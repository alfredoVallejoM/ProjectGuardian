"""Independent byte inventory for source-to-IR checks (not a compiler).

No imports from text/syntax/lowering, no candidate source-map trust. The
inventory is recomputed from externally pinned original bytes. This establishes
syntactic declaration/field correspondence, NOT reference existence, authority,
historical coverage, refinement sufficiency or behavior of implemented code.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum

from guardian.domain.identity import EntityKind
from .contract import SourceBundle, CompileContext, LANGUAGE_VERSION
from .ir import ContractIR, IRType

_MAX_BYTES = 2_000_000
_MAX_TOKENS = 100_000
_NAMES = re.compile(r'[A-Za-z_][A-Za-z_0-9]*')
_NUMBERS = re.compile(r'[+-]?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?')
_KINDS = frozenset(('source', 'scope', 'objective', 'capability', 'property',
                    'obligation', 'verification', 'relation'))


@dataclass(frozen=True, slots=True)
class InventoryToken:
    kind: str
    text: str
    start: int
    end: int


def independent_tokens(raw: bytes, base: int = 0) -> tuple[InventoryToken, ...]:
    """Separate verification lexer with the same declared lexical profile."""
    if type(raw) is not bytes or type(base) is not int or base < 0:
        raise TypeError('V0_BYTES_AND_OFFSET_REQUIRED')
    if len(raw) > _MAX_BYTES:
        raise ValueError('GSL_V0_SOURCE_RESOURCE_LIMIT')
    text = raw.decode('utf-8', 'strict')
    offsets = [base]
    for c in text:
        offsets.append(offsets[-1] + len(c.encode('utf-8')))
    tokens = []
    i = 0
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
            end = text.find('*/', i + 2)
            if end < 0:
                raise ValueError('GSL_V0_UNTERMINATED_COMMENT')
            i = end + 2
            continue
        start = i
        if text[i] == '"':
            i += 1
            while i < len(text):
                if text[i] == '\\':
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            else:
                raise ValueError('GSL_V0_UNTERMINATED_STRING')
            decoded = json.loads(text[start:i])
            # Reject lone JSON surrogates, as the productive UTF-8 lexer does.
            decoded.encode('utf-8', 'strict')
            kind = 'string'
        elif (match := _NAMES.match(text, i)) is not None:
            i = match.end()
            kind = 'name'
        elif (match := _NUMBERS.match(text, i)) is not None:
            i = match.end()
            kind = 'number'
        else:
            i += 1
            kind = 'punct'
        tokens.append(InventoryToken(kind, text[start:i], offsets[start], offsets[i]))
        if len(tokens) > _MAX_TOKENS:
            raise ValueError('GSL_V0_SOURCE_RESOURCE_LIMIT')
    return tuple(tokens)


@dataclass(frozen=True, slots=True)
class InventoryField:
    name: str
    occurrence: int
    tokens: tuple[InventoryToken, ...]

    @property
    def span(self) -> tuple[int, int]:
        return self.tokens[0].start, self.tokens[-1].end


@dataclass(frozen=True, slots=True)
class InventoryDeclaration:
    kind: str
    name: str
    start: int
    end: int
    fields: tuple[InventoryField, ...]


def _regions(raw: bytes, source_format: str) -> tuple[tuple[int, int], ...]:
    if source_format == 'gsl':
        return ((0, len(raw)),)
    if source_format != 'markdown':
        raise ValueError('V0_UNSUPPORTED_SOURCE_FORMAT')
    # Separate Markdown convention recognizer; no productive extractor import.
    units = []
    opened = None
    html = False
    offset = 0
    for line in raw.splitlines(keepends=True):
        text = line.decode('utf-8').rstrip('\r\n')
        if opened is None:
            if html or '<!--' in text:
                html = '-->' not in text
            else:
                m = re.fullmatch(r' {0,3}(`{3,}|~{3,})([^\r\n]*)', text)
                if m:
                    marker, info = m.groups()
                    words = info.split()
                    normative = (bool(words) and words[0] in ('gsl', 'gsl0')
                                 and 'normative' in words[1:])
                    if normative and words[1:] not in (['normative'], ['normative', 'version=0.1']):
                        raise ValueError('V0_INVALID_NORMATIVE_FENCE')
                    opened = (marker, offset + len(line), normative)
        else:
            marker, begin, normative = opened
            close = re.fullmatch(r' {0,3}(`{3,}|~{3,})[ \t]*', text)
            if close and close[1][0] == marker[0] and len(close[1]) >= len(marker):
                if normative:
                    units.append((begin, offset))
                opened = None
        offset += len(line)
    if opened is not None or not units:
        raise ValueError('V0_INCOMPLETE_NORMATIVE_DOCUMENT')
    return tuple(units)


def source_inventory(bundle: SourceBundle, *, source_format: str = 'gsl') -> tuple[InventoryDeclaration, ...]:
    """Inventory each complete declaration independently of its candidate ID/map."""
    if type(bundle) is not SourceBundle:
        raise TypeError('V0_SOURCE_BUNDLE_REQUIRED')
    if len(bundle.source_bytes) > _MAX_BYTES:
        raise ValueError('GSL_V0_SOURCE_RESOURCE_LIMIT')
    declarations = []
    seen = set()
    for start, end in _regions(bundle.source_bytes, source_format):
        tokens = independent_tokens(bundle.source_bytes[start:end], start)
        idx = 0

        def take(text=None, kind=None):
            nonlocal idx
            if idx >= len(tokens):
                raise ValueError('V0_INCOMPLETE_DECLARATION')
            token = tokens[idx]
            if ((text is not None and token.text != text)
                    or (kind is not None and token.kind != kind)):
                raise ValueError('V0_UNSUPPORTED_DOCUMENT_SYNTAX')
            idx += 1
            return token

        take('gsl')
        version = json.loads(take(kind='string').text)
        take(';'); take('project')
        project = json.loads(take(kind='string').text)
        take(';')
        if version != LANGUAGE_VERSION or project != bundle.project.value:
            raise ValueError('V0_HEADER_CONTEXT_MISMATCH')
        while idx < len(tokens):
            kind = take(kind='name')
            if kind.text not in _KINDS:
                raise ValueError('V0_UNSUPPORTED_DECLARATION_KIND')
            name = json.loads(take(kind='string').text)
            if (kind.text, name) in seen:
                raise ValueError('V0_DUPLICATE_SOURCE_DECLARATION')
            seen.add((kind.text, name))
            take('{')
            fields = []
            occurrences = {}
            while idx < len(tokens) and tokens[idx].text != '}':
                field = take(kind='name').text
                take(':')
                values = []
                depth = 0
                while idx < len(tokens):
                    token = tokens[idx]
                    if token.kind == 'punct':
                        if token.text == ';' and depth == 0:
                            break
                        if token.text == '(':
                            depth += 1
                        elif token.text == ')':
                            depth -= 1
                        elif token.text in '{}[]':
                            raise ValueError('V0_UNSUPPORTED_FIELD_STRUCTURE')
                    if depth < 0 or depth > 64:
                        raise ValueError('V0_FIELD_DEPTH_LIMIT')
                    values.append(take())
                take(';')
                if not values or depth:
                    raise ValueError('V0_INCOMPLETE_FIELD')
                occurrence = occurrences.get(field, 0)
                occurrences[field] = occurrence + 1
                fields.append(InventoryField(field, occurrence, tuple(values)))
            closing = take('}')
            declarations.append(InventoryDeclaration(kind.text, name, kind.start, closing.end, tuple(fields)))
    return tuple(declarations)


class CheckStatus(str, Enum):
    CHECKED = 'CHECKED'
    NOT_CHECKED = 'NOT_CHECKED'
    MISMATCH = 'MISMATCH'


@dataclass(frozen=True, slots=True)
class SourceCorrespondence:
    declarations: CheckStatus = CheckStatus.NOT_CHECKED
    fields: CheckStatus = CheckStatus.NOT_CHECKED
    reference_integrity: CheckStatus = CheckStatus.NOT_CHECKED
    historical_coverage: CheckStatus = CheckStatus.NOT_CHECKED
    normative_admission: CheckStatus = CheckStatus.NOT_CHECKED
    reason: str = ''


def _call(tokens: tuple[InventoryToken, ...]):
    """Read one reference call with literal arguments; never execute callbacks."""
    if (len(tokens) < 4 or tokens[0].kind != 'name' or tokens[1].text != '('
            or tokens[-1].text != ')'):
        return None
    args = []
    for i, token in enumerate(tokens[2:-1]):
        if i % 2:
            if token.text != ',':
                return None
        else:
            if token.kind != 'string':
                return None
            args.append(json.loads(token.text))
    if len(tokens[2:-1]) % 2 == 0:
        return None
    return tokens[0].text, tuple(args)


def _matches(value, tokens, bundle, context, field_name):
    kind, payload = value.kind, value.value
    texts = tuple(t.text for t in tokens)
    if kind in (IRType.TEXT, IRType.DEFERRED):
        return len(tokens) == 1 and (
            (tokens[0].kind == 'string' and json.loads(tokens[0].text) == payload)
            or (kind is IRType.TEXT and field_name == 'method'
                and tokens[0].kind == 'name' and tokens[0].text == payload))
    if kind is IRType.KIND:
        return texts == (payload.value,)
    if kind is IRType.BOOL:
        return texts == ('true' if payload else 'false',)
    if kind is IRType.INTEGER:
        return len(tokens) == 1 and re.fullmatch(r'[+-]?[0-9]+', texts[0]) is not None and int(texts[0]) == payload
    if kind is IRType.SOURCE_ITEM:
        call = _call(tokens)
        return (call == ('source_item', (payload.source.entity.value, payload.logical_item))
                and payload.source == bundle.source_ref)
    if kind is IRType.REF:
        if texts == ('context',):
            return payload == bundle.source_ref
        call = _call(tokens)
        if call is None or len(call[1]) != 1:
            return False
        name, (identifier,) = call
        expected = {'verification_ref': 'verification'}.get(name, name)
        if expected != payload.kind.value or identifier != payload.entity.value or payload.project != context.project:
            return False
        candidates = tuple(s.identity for s in context.symbols
                           if s.identity.kind == payload.kind and s.identity.entity.value == identifier)
        # Explicit revision binding wins; otherwise this shorthand is local to
        # the pinned source revision. It does NOT establish entity existence.
        return payload in candidates if candidates else payload.revision == bundle.revision
    return kind is IRType.V4  # V0's separate evaluator checks the denotation.


def check_source_correspondence(ir: ContractIR, bundle: SourceBundle, context: CompileContext,
                                *, source_format: str = 'gsl') -> SourceCorrespondence:
    try:
        inventory = source_inventory(bundle, source_format=source_format)
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        return SourceCorrespondence(reason=str(exc))
    by_id = {(d.kind, d.name): d for d in inventory}
    if set(by_id) != {(d.identity.kind.value, d.identity.entity.value) for d in ir.declarations}:
        return SourceCorrespondence(CheckStatus.MISMATCH, reason='SOURCE_DECLARATION_POPULATION_MISMATCH')
    fields_match = True
    for declaration in ir.declarations:
        original = by_id[declaration.identity.kind.value, declaration.identity.entity.value]
        if (declaration.origin.byte_start, declaration.origin.byte_end) != (original.start, original.end):
            return SourceCorrespondence(CheckStatus.MISMATCH, reason='SOURCE_DECLARATION_ID_ORIGIN_MISMATCH')
        if len(declaration.fields) != len(original.fields):
            fields_match = False
            continue
        counts = {}
        actual = {}
        for field in declaration.fields:
            n = counts.get(field.name, 0)
            counts[field.name] = n + 1
            actual[field.name, n] = field.typed_value
        expected = {(f.name, f.occurrence): f for f in original.fields}
        if set(expected) != set(actual):
            fields_match = False
            continue
        if any(not _matches(actual[k], f.tokens, bundle, context, f.name) for k, f in expected.items()):
            fields_match = False
    return SourceCorrespondence(CheckStatus.CHECKED,
                                CheckStatus.CHECKED if fields_match else CheckStatus.MISMATCH,
                                reason='' if fields_match else 'SOURCE_NORMATIVE_FIELD_MISMATCH')
