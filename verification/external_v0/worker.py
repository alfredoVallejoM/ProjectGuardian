"""Stdlib-only external finite V4 checker; never imports candidate Python code.

An operator-pinned expectation, NOT the candidate, selects source byte spans.
The only positive claim is equivalence of those formulas on a finite domain.
Declaration correspondence, references and admission are explicitly NOT_CHECKED.
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


def report(status, reason='', **details):
    return dict(status=status, reason=reason, claim='PINNED_FORMULAS_ONLY',
                full_contract_equivalent=False, normative_admission='NOT_CHECKED',
                declaration_correspondence='NOT_CHECKED', reference_integrity='NOT_CHECKED',
                historical_coverage='NOT_CHECKED', profile=PROFILE, **details)


def verify(source, expectation, candidate):
    exact(expectation, ('schema', 'profile', 'source_sha256', 'expressions', 'limits'))
    exact(candidate, ('schema', 'formulas'))
    if expectation['schema'] != 'guardian.external-v0-expectation/v1' or expectation['profile'] != PROFILE:
        raise Invalid('EXPECTATION_VERSION')
    if candidate['schema'] != 'guardian.external-v0-candidate/v1':
        raise Invalid('CANDIDATE_VERSION')
    checked_hash(source, expectation['source_sha256'])
    source.decode('utf-8')
    limits = exact(expectation['limits'], ('max_atoms', 'max_valuations', 'max_total_valuations'))
    for key, maximum in (('max_atoms', 8), ('max_valuations', 65536), ('max_total_valuations', 262144)):
        if type(limits[key]) is not int or not 1 <= limits[key] <= maximum:
            raise Limited('LIMIT_POLICY')
    expressions, formulas = expectation['expressions'], candidate['formulas']
    if type(expressions) is not list or not 1 <= len(expressions) <= 256 or type(formulas) is not list or len(formulas) > 256:
        raise Invalid('EXPRESSION_POPULATION')
    expected, actual = {}, {}
    for entry in expressions:
        exact(entry, ('id', 'start', 'end'))
        identifier, start, end = entry['id'], entry['start'], entry['end']
        if type(identifier) is not str or not identifier or identifier in expected:
            raise Invalid('DUPLICATE_EXPECTATION_OR_ID')
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(source):
            raise Invalid('SOURCE_SPAN')
        # Decode both prefixes: source and span must agree on UTF-8 boundaries.
        source[:start].decode('utf-8'); source[:end].decode('utf-8')
        expected[identifier] = source[start:end]
    for entry in formulas:
        exact(entry, ('id', 'formula'))
        identifier = entry['id']
        if type(identifier) is not str or not identifier or identifier in actual:
            raise Invalid('DUPLICATE_CANDIDATE_OR_ID')
        actual[identifier] = entry['formula']
    if set(expected) != set(actual):
        raise Invalid('FORMULA_POPULATION_MISMATCH')
    checked = total = 0
    for identifier in sorted(expected):
        source_tree = parse(expected[identifier])
        ir = actual[identifier]
        variables = validate_ir(ir)
        pending = [source_tree]
        while pending:
            node = pending.pop()
            if node[0] == 'variable':
                variables.add(node[1])
            elif node[0] != 'constant':
                pending.extend(node[1:])
        names = sorted(variables)
        size = 4 ** len(names)
        if len(names) > limits['max_atoms'] or size > limits['max_valuations'] or total + size > limits['max_total_valuations']:
            return report('INCONCLUSIVE_RESOURCE_LIMIT', checked_formulas=checked, valuations_checked=total)
        for values in itertools.product(range(4), repeat=len(names)):
            assignment = dict(zip(names, values))
            left, right = source_value(source_tree, assignment), ir_value(ir, assignment)
            total += 1
            if left != right:
                return report('COUNTEREXAMPLE', formula=identifier, witness=assignment,
                              source_value=left, ir_value=right, valuations_checked=total)
        checked += 1
    return report('FINITE_EQUIVALENT', checked_formulas=checked, valuations_checked=total)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--expectation', required=True)
    parser.add_argument('--expected-expectation-sha256', required=True)
    parser.add_argument('--candidate', required=True)
    args = parser.parse_args()
    try:
        raw = read_bytes(args.expectation)
        checked_hash(raw, args.expected_expectation_sha256)
        result = verify(read_bytes(args.source), load(raw), load(read_bytes(args.candidate)))
    except Limited as exc:
        result = report('INCONCLUSIVE_RESOURCE_LIMIT', str(exc))
    except (ValueError, TypeError, KeyError, UnicodeError, OSError, RecursionError) as exc:
        result = report('INVALID_INPUT', str(exc))
    print(json.dumps(result, sort_keys=True, ensure_ascii=True, allow_nan=False))
    return 0 if result['status'] == 'FINITE_EQUIVALENT' else 1


if __name__ == '__main__':
    sys.exit(main())
