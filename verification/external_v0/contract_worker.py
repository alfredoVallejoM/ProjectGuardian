"""Standalone source-to-IR correspondence checker for the pinned GSL0 profile.

Stdlib only. Does not import Guardian, its source inventory, parser, types or VM.
The operator pins original bytes, nominal context, declaration inventory and POs.
Complete correspondence of the supported fields is NOT normative admission,
reference existence, historical coverage, or realization of a specification.
The finite V4 kernel is reused from the separately maintained external checker.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import re
import sys

PROFILE = 'gsl0/v4-0.1'
MAX_BYTES = 2_000_000
MAX_NODES = 4096
MAX_DEPTH = 64
NAME = re.compile(r'[A-Za-z_][A-Za-z_0-9]*\Z', re.ASCII)
CONSTANTS = {'unknown': 0, 'yes': 1, 'true': 1, 'no': 2, 'false': 2, 'conflict': 3}
AND_TABLE = ((0, 0, 2, 2), (0, 1, 2, 3), (2, 2, 2, 2), (2, 3, 2, 3))
OR_TABLE = ((0, 1, 0, 1), (1, 1, 1, 1), (0, 1, 2, 3), (1, 1, 3, 3))
NOT_TABLE = (0, 2, 1, 3)


class Invalid(ValueError):
    pass


class Limited(Invalid):
    pass


def exact(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise Invalid('SCHEMA_FIELDS')
    return value


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Invalid('DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def read_bytes(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise Limited('BYTE_LIMIT')
    return raw


def load(raw):
    return json.loads(raw.decode('utf-8'), object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(Invalid('NONFINITE_JSON')))


def checked_hash(raw, expected):
    if type(expected) is not str or re.fullmatch('[0-9a-f]{64}', expected) is None:
        raise Invalid('HASH_FORMAT')
    if hashlib.sha256(raw).hexdigest() != expected:
        raise Invalid('PIN_MISMATCH')


def lex(raw):
    text = raw.decode('utf-8')
    out, i = [], 0
    while i < len(text):
        if text[i].isspace():
            i += 1
            continue
        if text.startswith('//', i):
            i += 2
            while i < len(text) and text[i] not in '\r\n':
                i += 1
            continue
        if text.startswith('/*', i):
            j = text.find('*/', i + 2)
            if j < 0:
                raise Invalid('UNTERMINATED_COMMENT')
            i = j + 2
            continue
        match = re.match(r'[A-Za-z_][A-Za-z_0-9]*|[()]', text[i:], re.ASCII)
        if not match:
            raise Invalid('UNSUPPORTED_SOURCE_TOKEN')
        out.append(match[0])
        i += len(match[0])
        if len(out) > MAX_NODES:
            raise Limited('TOKEN_LIMIT')
    return out


def parse(raw):
    tokens = lex(raw)
    pos, nodes = 0, 0

    def expression(minimum=0, depth=0):
        nonlocal pos, nodes
        nodes += 1
        if depth > MAX_DEPTH or nodes > MAX_NODES:
            raise Limited('SOURCE_DEPTH_OR_NODE_LIMIT')
        if pos >= len(tokens):
            raise Invalid('MISSING_OPERAND')
        word = tokens[pos]
        pos += 1
        if word == 'not':
            left = ('not', expression(3, depth + 1))
        elif word == '(':
            left = expression(0, depth + 1)
            if pos >= len(tokens) or tokens[pos] != ')':
                raise Invalid('UNBALANCED_SOURCE')
            pos += 1
        elif word in CONSTANTS:
            left = ('constant', CONSTANTS[word])
        elif NAME.fullmatch(word) and word not in ('and', 'or'):
            left = ('variable', word)
        else:
            raise Invalid('INVALID_OPERAND')
        while pos < len(tokens):
            op = tokens[pos]
            precedence = {'or': 1, 'and': 2}.get(op, -1)
            if precedence < minimum:
                break
            pos += 1
            left = (op, left, expression(precedence + 1, depth + 1))
        return left

    result = expression()
    if pos != len(tokens):
        raise Invalid('TRAILING_SOURCE')
    return result


def source_value(tree, values):
    op = tree[0]
    if op == 'constant':
        return tree[1]
    if op == 'variable':
        return values[tree[1]]
    if op == 'not':
        return NOT_TABLE[source_value(tree[1], values)]
    table = AND_TABLE if op == 'and' else OR_TABLE
    return table[source_value(tree[1], values)][source_value(tree[2], values)]


def validate_ir(root):
    variables, stack, count = set(), [(root, 0)], 0
    while stack:
        node, depth = stack.pop()
        count += 1
        if depth > MAX_DEPTH or count > MAX_NODES:
            raise Limited('IR_DEPTH_OR_NODE_LIMIT')
        exact(node, ('op', 'name', 'args'))
        op, name, args = node['op'], node['name'], node['args']
        if type(op) is not str or type(args) is not list:
            raise Invalid('UNTYPED_FORMULA')
        if op == 'atom':
            if type(name) is not str or not NAME.fullmatch(name) or name in (*CONSTANTS, 'and', 'or', 'not') or args:
                raise Invalid('INVALID_ATOM')
            variables.add(name)
        elif op in ('yes', 'no', 'unknown', 'conflict'):
            if name is not None or args:
                raise Invalid('INVALID_CONSTANT')
        elif op in ('not', 'and', 'or'):
            if name is not None or (len(args) != 1 if op == 'not' else len(args) < 2):
                raise Invalid('INVALID_ARITY')
            stack.extend((arg, depth + 1) for arg in args)
        else:
            raise Invalid('UNSUPPORTED_IR_OPERATOR')
    return variables


def ir_value(node, values):
    op = node['op']
    if op == 'atom':
        return values[node['name']]
    if op in CONSTANTS:
        return CONSTANTS[op]
    if op == 'not':
        value = ir_value(node['args'][0], values)
        return ((value & 1) << 1) | ((value & 2) >> 1)
    result = 1 if op == 'and' else 2
    for arg in node['args']:
        value = ir_value(arg, values)
        if op == 'and':
            result = ((result & value) & 1) | ((result | value) & 2)
        else:
            result = ((result | value) & 1) | ((result & value) & 2)
    return result



CORRESPONDENCE_PROFILE = 'gsl0/correspondence-0.1'
IDENTITY_SCHEMA = 'guardian.identity/v1'
IR_SCHEMA = 'guardian/gsl0/typed-ir/v0.1'
KINDS = frozenset(('objective capability property obligation campaign architecture '
                   'constitution decision rule source source_policy source_universe '
                   'scope clause relation verification implementation project').split())
COMMITMENTS = frozenset('existence behavior constitution execution development integration migration'.split())
FIELDS = {
    'source': {'locator': 'text', 'source_cut': 'ref:source'},
    'scope': {'project': 'ref:project', 'campaign': 'text'},
    'objective': {'from': 'source_item', 'scope': 'ref:scope'},
    'capability': {'from': 'source_item', 'scope': 'ref:scope'},
    'property': {'from': 'source_item', 'kind': 'kind:commitment', 'subject': 'ref:project',
                 'holds': 'v4', 'deferred_semantics': 'deferred'},
    'obligation': {'from': 'source_item', 'kind': 'kind:commitment', 'scope': 'ref:scope',
                   'when': 'v4', 'requires': 'ref:property', 'verification': 'ref:verification'},
    'verification': {'from': 'source_item', 'target': 'ref:obligation',
                     'property': 'ref:property', 'method': 'text'},
    'relation': {'kind': 'kind:relation', 'parent': 'ref:obligation', 'child': 'ref:clause'},
}
REQUIRED = {
    'source': {'locator', 'source_cut'}, 'scope': {'project'},
    'objective': {'from', 'scope'}, 'capability': {'from', 'scope'},
    'property': {'kind', 'subject'}, 'obligation': {'from', 'kind', 'scope', 'when'},
    'verification': {'from', 'target', 'property', 'method'},
    'relation': {'kind', 'parent', 'child'},
}
MAX_DECLARATIONS = 2500
MAX_FIELDS = 1000
MAX_TOKENS = 100000


def require(condition, reason):
    if not condition:
        raise Invalid(reason)


def token(value):
    require(type(value) is str and 3 <= len(value) <= 96
            and re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', value, re.ASCII),
            'INVALID_NOMINAL_TOKEN')
    return value


def nominal_ref(value):
    exact(value, ('schema', 'type', 'project', 'entity_kind', 'entity', 'revision'))
    require(value['schema'] == IDENTITY_SCHEMA and value['type'] == 'entity_ref', 'REFERENCE_SCHEMA')
    token(value['project']); token(value['entity'])
    require(type(value['entity_kind']) is str and value['entity_kind'] in KINDS, 'REFERENCE_KIND')
    require(type(value['revision']) is str and re.fullmatch(r'rev-[0-9a-f]{32}', value['revision']), 'REFERENCE_REVISION')
    return value


def ref_key(value):
    nominal_ref(value)
    return value['entity_kind'], value['entity']


def nominal_digest(value, raw):
    exact(value, ('schema', 'type', 'algorithm', 'hex'))
    require(value['schema'] == IDENTITY_SCHEMA and value['type'] == 'content_digest', 'DIGEST_SCHEMA')
    require(type(value['algorithm']) is str and value['algorithm'] in ('sha256', 'sha512'), 'DIGEST_ALGORITHM')
    expected = hashlib.new(value['algorithm'], raw).hexdigest()
    require(type(value['hex']) is str and value['hex'] == expected, 'SOURCE_DIGEST_MISMATCH')


def bounded_list(value, maximum, reason):
    require(type(value) is list, reason + '_TYPE')
    if len(value) > maximum:
        raise Limited(reason + '_LIMIT')
    return value


def lexical_inventory(raw, base):
    """Independent tokenization, with physical UTF-8 offsets and no callbacks."""
    text = raw.decode('utf-8')
    offsets = [base]
    for char in text:
        offsets.append(offsets[-1] + len(char.encode('utf-8')))
    result, i = [], 0
    while i < len(text):
        if text[i].isspace():
            i += 1; continue
        if text.startswith('//', i):
            i += 2
            while i < len(text) and text[i] not in '\r\n':
                i += 1
            continue
        if text.startswith('/*', i):
            end = text.find('*/', i + 2)
            require(end >= 0, 'UNTERMINATED_COMMENT')
            i = end + 2; continue
        start = i
        if text[i] == '"':
            i += 1
            while i < len(text):
                if text[i] == '\\':
                    i += 2
                elif text[i] == '"':
                    i += 1; break
                else:
                    i += 1
            else:
                raise Invalid('UNTERMINATED_STRING')
            value = json.loads(text[start:i]); value.encode('utf-8')
            kind = 'string'
        else:
            match = re.match(r'[A-Za-z_][A-Za-z_0-9]*|[+-]?[0-9]+|[{}():;,]', text[i:], re.ASCII)
            require(match is not None, 'UNSUPPORTED_SOURCE_TOKEN')
            value = match[0]; i += len(value)
            kind = 'name' if NAME.fullmatch(value) else 'other'
        result.append((kind, value, offsets[start], offsets[i]))
        if len(result) > MAX_TOKENS:
            raise Limited('SOURCE_TOKEN_LIMIT')
    return result


def normative_regions(raw, source_format):
    require(source_format in ('gsl', 'markdown'), 'SOURCE_FORMAT')
    if source_format == 'gsl':
        return [(0, len(raw))]
    offset, opened, html, regions = 0, None, False, []
    for line in raw.splitlines(keepends=True):
        text = line.decode('utf-8').rstrip('\r\n')
        if opened is None:
            if html or '<!--' in text:
                html = '-->' not in text
            elif (match := re.fullmatch(r' {0,3}(`{3,}|~{3,})([^\r\n]*)', text)):
                marker, info = match.groups(); words = info.split()
                normative = bool(words) and words[0] in ('gsl', 'gsl0') and 'normative' in words[1:]
                if normative:
                    require(words[1:] in (['normative'], ['normative', 'version=0.1']), 'NORMATIVE_FENCE_PROFILE')
                opened = marker, offset + len(line), normative
        elif (match := re.fullmatch(r' {0,3}(`{3,}|~{3,})[ \t]*', text)):
            marker, start, normative = opened
            if match[1][0] == marker[0] and len(match[1]) >= len(marker):
                if normative:
                    regions.append((start, offset))
                opened = None
        offset += len(line)
    require(opened is None and regions, 'INCOMPLETE_NORMATIVE_DOCUMENT')
    return regions


def inventory(raw, expectation):
    declarations, seen = [], set()
    total_tokens = 0
    for start, end in normative_regions(raw, expectation['source_format']):
        items = lexical_inventory(raw[start:end], start)
        total_tokens += len(items)
        if total_tokens > MAX_TOKENS:
            raise Limited('SOURCE_TOKEN_LIMIT')
        pos = 0

        def take(value=None, kind=None):
            nonlocal pos
            require(pos < len(items), 'INCOMPLETE_DECLARATION')
            item = items[pos]; pos += 1
            if value is not None:
                expected_kind = 'name' if NAME.fullmatch(value) else 'other'
                require(item[1] == value and item[0] == expected_kind, 'SOURCE_GRAMMAR')
            require(kind is None or item[0] == kind, 'SOURCE_GRAMMAR')
            return item

        take('gsl'); version = take(kind='string')[1]; take(';')
        take('project'); project = take(kind='string')[1]; take(';')
        require(version == '0.1' and project == expectation['project'], 'HEADER_CONTEXT_MISMATCH')
        while pos < len(items):
            opening = take(kind='name'); kind = opening[1]
            require(kind in FIELDS, 'UNSUPPORTED_DECLARATION')
            name = token(take(kind='string')[1]); key = kind, name
            require(key not in seen, 'DUPLICATE_SOURCE_DECLARATION'); seen.add(key)
            take('{'); fields, counts = [], {}
            while pos < len(items) and not (items[pos][0] == 'other' and items[pos][1] == '}'):
                field = take(kind='name')[1]; take(':')
                require(field in FIELDS[kind], 'UNKNOWN_SOURCE_FIELD')
                counts[field] = counts.get(field, 0) + 1
                require(counts[field] == 1 or field in ('requires', 'verification'), 'DUPLICATE_SOURCE_FIELD')
                values, depth = [], 0
                while pos < len(items):
                    item = items[pos]
                    if item[0] != 'string':
                        if item[1] == ';' and depth == 0:
                            break
                        depth += (item[1] == '(') - (item[1] == ')')
                        require(item[1] not in ('{', '}') and depth >= 0, 'SOURCE_FIELD_STRUCTURE')
                        if depth > MAX_DEPTH:
                            raise Limited('SOURCE_FIELD_DEPTH_LIMIT')
                    values.append(take())
                take(';'); require(values and depth == 0, 'INCOMPLETE_FIELD')
                fields.append((field, values))
                if len(fields) > MAX_FIELDS:
                    raise Limited('FIELD_COUNT_LIMIT')
            close = take('}')
            require(REQUIRED[kind] <= counts.keys(), 'MISSING_SOURCE_FIELD')
            if kind == 'property':
                require(('holds' in counts) != ('deferred_semantics' in counts), 'PROPERTY_SEMANTICS_REQUIRED')
            declarations.append((key, opening[2], close[3], fields))
            if len(declarations) > MAX_DECLARATIONS:
                raise Limited('DECLARATION_LIMIT')
    return declarations


def reference_from_source(values, expected_kind, expectation, bindings):
    if len(values) == 1 and values[0][0] == 'name' and values[0][1] == 'context':
        require(expected_kind == 'source', 'WRONG_CONTEXT_REFERENCE_TYPE')
        return expectation['source']
    require(len(values) == 4 and values[0][0] == 'name' and values[1][1] == '('
            and values[1][0] == 'other' and values[2][0] == 'string'
            and values[3][0] == 'other' and values[3][1] == ')', 'REFERENCE_SYNTAX')
    call_kind = {'verification_ref': 'verification'}.get(values[0][1], values[0][1])
    require(call_kind == expected_kind, 'REFERENCE_KIND_MISMATCH')
    name = token(values[2][1])
    key = expected_kind, name
    if key in bindings:
        return bindings[key]
    return dict(schema=IDENTITY_SCHEMA, type='entity_ref', project=expectation['project'],
                entity_kind=expected_kind, entity=name, revision=expectation['revision'])


def ordinary_value(field, values, tag, expectation, bindings):
    if tag.startswith('ref:'):
        return reference_from_source(values, tag.split(':')[1], expectation, bindings)
    if tag == 'source_item':
        require(len(values) == 6 and values[0][:2] == ('name', 'source_item')
                and values[1][:2] == ('other', '(') and values[2][0] == 'string'
                and values[3][:2] == ('other', ',') and values[4][0] == 'string'
                and values[5][:2] == ('other', ')'), 'SOURCE_ITEM_SYNTAX')
        require(values[2][1] == expectation['source']['entity'] and values[4][1], 'SOURCE_ITEM_BINDING')
        return dict(source=expectation['source'], logical_item=values[4][1])
    if tag.startswith('kind:'):
        enum = tag.split(':')[1]
        require(len(values) == 1 and values[0][0] == 'name', 'KIND_SYNTAX')
        allowed = COMMITMENTS if enum == 'commitment' else {'proposed_detail', 'references'}
        require(values[0][1] in allowed, 'UNKNOWN_ENUM_VARIANT')
        return dict(enum=enum, value=values[0][1])
    require(tag in ('text', 'deferred') and len(values) == 1, 'VALUE_SYNTAX')
    require(values[0][0] == 'string' or (field == 'method' and values[0][0] == 'name'), 'VALUE_TYPE')
    require(tag != 'deferred' or bool(values[0][1]), 'EMPTY_DEFERRED_SEMANTICS')
    return values[0][1]


def contract_report(status, reason='', **details):
    return dict(status=status, reason=reason, profile=CORRESPONDENCE_PROFILE,
                claim='SOURCE_IR_CORRESPONDENCE_ONLY', full_contract_equivalent=False,
                reference_integrity='NOT_CHECKED', historical_coverage='NOT_CHECKED',
                normative_admission='NOT_CHECKED', implementation_realization='NOT_CHECKED',
                **details)


def verify_contract(source, expectation, candidate):
    exact(expectation, ('schema', 'profile', 'source_sha256', 'source_format', 'project',
                        'revision', 'source', 'declarations', 'bindings', 'proofs', 'limits'))
    require(expectation['schema'] == 'guardian.external-contract-expectation/v1'
            and expectation['profile'] == CORRESPONDENCE_PROFILE, 'EXPECTATION_VERSION')
    checked_hash(source, expectation['source_sha256']); source.decode('utf-8')
    token(expectation['project']); nominal_ref(expectation['source'])
    require(expectation['source']['project'] == expectation['project']
            and expectation['source']['revision'] == expectation['revision']
            and expectation['source']['entity_kind'] == 'source', 'EXPECTED_SOURCE_CONTEXT')
    limits = exact(expectation['limits'], ('max_atoms', 'max_valuations', 'max_total_valuations'))
    for key, maximum in (('max_atoms', 8), ('max_valuations', 65536), ('max_total_valuations', 262144)):
        if type(limits[key]) is not int or not 1 <= limits[key] <= maximum:
            raise Limited('LIMIT_POLICY')
    refs = bounded_list(expectation['declarations'], MAX_DECLARATIONS, 'EXPECTED_DECLARATIONS')
    keys = [ref_key(r) for r in refs]
    require(len(set(keys)) == len(keys), 'DUPLICATE_EXPECTED_DECLARATION')
    for ref in refs:
        require(ref['project'] == expectation['project'] and ref['entity_kind'] in FIELDS,
                'FOREIGN_OR_UNSUPPORTED_EXPECTED_DECLARATION')
    bindings = {}
    for ref in bounded_list(expectation['bindings'], MAX_DECLARATIONS, 'EXPECTED_BINDINGS'):
        key = ref_key(ref)
        require(ref['project'] == expectation['project'] and key not in bindings, 'AMBIGUOUS_OR_FOREIGN_BINDING')
        bindings[key] = ref
    for ref in refs:
        key = ref_key(ref)
        require(key not in bindings or bindings[key] == ref, 'DECLARATION_BINDING_CONFLICT')
        bindings[key] = ref
    records = inventory(source, expectation)
    require([r[0] for r in records] == keys, 'SOURCE_EXPECTATION_POPULATION_OR_ORDER_MISMATCH')
    exact(candidate, ('schema', 'semantic_version', 'project', 'source', 'source_digest', 'declarations', 'proofs'))
    require(candidate['schema'] == IR_SCHEMA and candidate['semantic_version'] == PROFILE, 'IR_VERSION')
    exact(candidate['project'], ('schema', 'type', 'value'))
    require(candidate['project'] == dict(schema=IDENTITY_SCHEMA, type='project_id', value=expectation['project']), 'IR_PROJECT')
    nominal_ref(candidate['source']); require(candidate['source'] == expectation['source'], 'IR_SOURCE')
    nominal_digest(candidate['source_digest'], source)
    actual = bounded_list(candidate['declarations'], MAX_DECLARATIONS, 'DECLARATIONS')
    require(len(actual) == len(records), 'DECLARATION_POPULATION_MISMATCH')
    formulas, pending_origins, checked_fields = [], [], 0
    for original, expected_ref, declaration in zip(records, refs, actual):
        (kind, name), start, end, source_fields = original
        exact(declaration, ('identity', 'origin', 'fields')); nominal_ref(declaration['identity'])
        require(declaration['identity'] == expected_ref, 'DECLARATION_IDENTITY_OR_ORDER_MISMATCH')
        origin = exact(declaration['origin'], ('source', 'digest', 'byte_start', 'byte_end'))
        require(type(origin['byte_start']) is int and type(origin['byte_end']) is int,
                'ORIGIN_OFFSET_TYPE')
        require(origin == dict(source=expectation['source'], digest=candidate['source_digest'],
                               byte_start=start, byte_end=end), 'DECLARATION_ORIGIN_MISMATCH')
        fields = bounded_list(declaration['fields'], MAX_FIELDS, 'FIELDS')
        require(len(fields) == len(source_fields), 'FIELD_POPULATION_MISMATCH')
        for (field, values), emitted in zip(source_fields, fields):
            exact(emitted, ('name', 'value'))
            require(type(emitted['name']) is str and emitted['name'] == field, 'FIELD_ORDER_OR_NAME_MISMATCH')
            payload = exact(emitted['value'], ('tag', 'value'))
            tag = FIELDS[kind][field]
            require(payload['tag'] == tag.split(':')[0], 'FIELD_TYPE_MISMATCH')
            if tag == 'v4':
                raw = source[values[0][2]:values[-1][3]]
                tree = parse(raw); variables = validate_ir(payload['value'])
                stack = [tree]; count = 0
                while stack:
                    node = stack.pop(); count += 1
                    if count > MAX_NODES:
                        raise Limited('SOURCE_FORMULA_NODE_LIMIT')
                    if node[0] == 'variable':
                        variables.add(node[1])
                    elif node[0] != 'constant':
                        stack.extend(node[1:])
                formulas.append((name + '.' + field, tree, payload['value'], sorted(variables)))
            else:
                expected_value = ordinary_value(field, values, tag, expectation, bindings)
                # Compare exact JSON type as well as value; bool must never alias integer.
                require(type(payload['value']) is type(expected_value) and payload['value'] == expected_value,
                        'NORMATIVE_FIELD_MISMATCH:' + name + '.' + field)
                if tag == 'deferred' or (kind == 'relation' and field == 'kind'
                                        and expected_value['value'] == 'proposed_detail'):
                    pending_origins.append(expected_ref)
            checked_fields += 1
    proofs = bounded_list(expectation['proofs'], MAX_DECLARATIONS * 2, 'EXPECTED_PROOFS')
    seen_proofs = set()
    for proof in proofs:
        exact(proof, ('identifier', 'origin', 'state')); nominal_ref(proof['origin'])
        require(type(proof['identifier']) is str and 1 <= len(proof['identifier']) <= 512,
                'PROOF_IDENTIFIER')
        require(proof['state'] == 'UNPROVEN', 'PROOF_PROMOTION_FORBIDDEN')
        require(proof['origin'] in refs, 'ORPHAN_EXPECTED_PROOF')
        key = proof['identifier'], json.dumps(proof['origin'], sort_keys=True)
        require(key not in seen_proofs, 'DUPLICATE_PROOF'); seen_proofs.add(key)
    require(all(any(p['origin'] == ref for p in proofs) for ref in pending_origins), 'DEFERRED_PROOF_REQUIRED')
    bounded_list(candidate['proofs'], MAX_DECLARATIONS * 2, 'PROOFS')
    require(candidate['proofs'] == proofs, 'PROOF_OBLIGATION_MISMATCH')
    total = checked = 0
    for name, tree, formula, variables in formulas:
        size = 4 ** len(variables)
        if (len(variables) > limits['max_atoms'] or size > limits['max_valuations']
                or total + size > limits['max_total_valuations']):
            return contract_report('INCONCLUSIVE_RESOURCE_LIMIT', 'VALUATION_BUDGET',
                                   checked_formulas=checked, valuations_checked=total)
        for values in itertools.product(range(4), repeat=len(variables)):
            assignment = dict(zip(variables, values)); total += 1
            left, right = source_value(tree, assignment), ir_value(formula, assignment)
            if left != right:
                return contract_report('COUNTEREXAMPLE', name, witness=assignment,
                                       source_value=left, ir_value=right, valuations_checked=total)
        checked += 1
    return contract_report('SOURCE_IR_CORRESPONDENT', declarations_checked=len(actual),
                           fields_checked=checked_fields, formulas_checked=checked,
                           valuations_checked=total, proofs_preserved=len(proofs),
                           deferred_properties=len(pending_origins),
                           semantic_obligations_pending=bool(pending_origins or proofs),
                           declaration_correspondence='CHECKED', field_correspondence='CHECKED',
                           reference_correspondence='CHECKED', formula_equivalence='CHECKED_FINITE_DOMAIN',
                           source_sha256=hashlib.sha256(source).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--expectation', required=True)
    parser.add_argument('--expected-expectation-sha256', required=True)
    parser.add_argument('--candidate', required=True)
    args = parser.parse_args()
    try:
        raw = read_bytes(args.expectation); checked_hash(raw, args.expected_expectation_sha256)
        source = read_bytes(args.source); candidate_bytes = read_bytes(args.candidate)
        result = verify_contract(source, load(raw), load(candidate_bytes))
        result.update(expectation_sha256=hashlib.sha256(raw).hexdigest(),
                      candidate_sha256=hashlib.sha256(candidate_bytes).hexdigest())
    except Limited as exc:
        result = contract_report('INCONCLUSIVE_RESOURCE_LIMIT', str(exc))
    except (ValueError, TypeError, KeyError, UnicodeError, OSError, RecursionError) as exc:
        result = contract_report('REJECTED', str(exc))
    print(json.dumps(result, sort_keys=True, ensure_ascii=True, allow_nan=False))
    return 0 if result['status'] == 'SOURCE_IR_CORRESPONDENT' else 1


if __name__ == '__main__':
    sys.exit(main())
