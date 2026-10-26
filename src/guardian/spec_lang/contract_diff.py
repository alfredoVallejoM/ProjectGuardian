"""C12: conservative, typed differences between two fixed-profile ContractIRs.

This is structural comparison, NOT a proof of semantic equivalence, source
coverage, realization, or normative admission. It never silently drops a field,
a repeated reference, an ordering change, or an outstanding proof obligation.
Inputs are exact JSON bytes; no project callbacks, filesystem, or clock are used.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json

from guardian.domain.identity import ContentDigest, DigestAlgorithm, encode_identity
from .ir import canonical_bytes, decode_ir, ir_to_data


class DiffStatus(str, Enum):
    COMPLETE = 'COMPLETE'
    REJECTED = 'REJECTED'
    INCOMPARABLE = 'INCOMPARABLE'
    RESOURCE_LIMITED = 'RESOURCE_LIMITED'


class ChangeKind(str, Enum):
    SOURCE_PIN_CHANGED = 'SOURCE_PIN_CHANGED'
    SOURCE_DIGEST_CHANGED = 'SOURCE_DIGEST_CHANGED'
    DECLARATION_ADDED = 'DECLARATION_ADDED'
    DECLARATION_REMOVED = 'DECLARATION_REMOVED'
    DECLARATION_ORDER_CHANGED = 'DECLARATION_ORDER_CHANGED'
    DECLARATION_REVISION_CHANGED = 'DECLARATION_REVISION_CHANGED'
    DECLARATION_ORIGIN_CHANGED = 'DECLARATION_ORIGIN_CHANGED'
    FIELD_ADDED = 'FIELD_ADDED'
    FIELD_REMOVED = 'FIELD_REMOVED'
    FIELD_ORDER_CHANGED = 'FIELD_ORDER_CHANGED'
    FIELD_CHANGED = 'FIELD_CHANGED'
    PROOF_ADDED = 'PROOF_ADDED'
    PROOF_REMOVED = 'PROOF_REMOVED'
    PROOF_CHANGED = 'PROOF_CHANGED'
    PROOF_ORDER_CHANGED = 'PROOF_ORDER_CHANGED'


@dataclass(frozen=True, slots=True)
class DiffBudget:
    max_input_bytes: int = 8_000_000
    max_nodes: int = 500_000
    max_depth: int = 256
    max_changes: int = 25_000
    max_output_bytes: int = 32_000_000

    def __post_init__(self) -> None:
        for value, ceiling in ((self.max_input_bytes, 8_000_000),
                               (self.max_nodes, 1_000_000), (self.max_depth, 512),
                               (self.max_changes, 100_000),
                               (self.max_output_bytes, 64_000_000)):
            if type(value) is not int or not 1 <= value <= ceiling:
                raise ValueError('INVALID_DIFF_BUDGET')


@dataclass(frozen=True, slots=True)
class DiffDiagnostic:
    code: str
    path: str
    reason: str

    def __post_init__(self) -> None:
        if any(type(v) is not str or not v for v in (self.code, self.path, self.reason)):
            raise TypeError('INVALID_DIFF_DIAGNOSTIC')


@dataclass(frozen=True, slots=True)
class ContractChange:
    kind: ChangeKind
    path: str
    before: bytes | None
    after: bytes | None

    def __post_init__(self) -> None:
        if type(self.kind) is not ChangeKind or type(self.path) is not str or not self.path.startswith('$'):
            raise TypeError('INVALID_CONTRACT_CHANGE')
        if any(v is not None and type(v) is not bytes for v in (self.before, self.after)):
            raise TypeError('IMMUTABLE_DIFF_VALUES_REQUIRED')
        if self.before == self.after:
            raise ValueError('CHANGE_MUST_DIFFER')


@dataclass(frozen=True, slots=True)
class ContractDiff:
    status: DiffStatus
    before_digest: ContentDigest | None
    after_digest: ContentDigest | None
    changes: tuple[ContractChange, ...]
    diagnostics: tuple[DiffDiagnostic, ...]
    visited_nodes: int

    def __post_init__(self) -> None:
        if type(self.status) is not DiffStatus:
            raise TypeError('INVALID_DIFF_STATUS')
        for seq, cls in ((self.changes, ContractChange), (self.diagnostics, DiffDiagnostic)):
            if type(seq) is not tuple or any(type(x) is not cls for x in seq):
                raise TypeError('IMMUTABLE_DIFF_REPORT_REQUIRED')
            for item in seq:
                cls.__post_init__(item)
        if any(d is not None and type(d) is not ContentDigest for d in (self.before_digest, self.after_digest)):
            raise TypeError('NOMINAL_DIFF_DIGEST_REQUIRED')
        if type(self.visited_nodes) is not int or self.visited_nodes < 0:
            raise ValueError('INVALID_DIFF_COUNTER')
        if self.status is DiffStatus.COMPLETE:
            if self.diagnostics or self.before_digest is None or self.after_digest is None:
                raise ValueError('INCOMPLETE_DIFF_REPORT')
            if (self.before_digest == self.after_digest) != (not self.changes):
                raise ValueError('DIFF_IDENTITY_INCONSISTENT')
        elif not self.diagnostics:
            raise ValueError('DIFF_FAILURE_NEEDS_DIAGNOSTIC')

    @property
    def structurally_identical(self) -> bool:
        return self.status is DiffStatus.COMPLETE and not self.changes

    @property
    def requires_review(self) -> bool:
        return not self.structurally_identical

    @property
    def normatively_admitted(self) -> bool:
        return False

    @property
    def semantic_equivalence(self) -> str:
        return 'NOT_CHECKED'


class _Limited(ValueError):
    pass


class _Incomparable(ValueError):
    pass


def _json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def _nonfinite(value):
    raise ValueError('NONFINITE_JSON')


class _Meter:
    def __init__(self, budget: DiffBudget):
        self.budget, self.nodes, self.output = budget, 0, 0

    def spend(self):
        if self.nodes >= self.budget.max_nodes:
            raise _Limited('DIFF_NODE_LIMIT')
        self.nodes += 1

    def load(self, raw: bytes):
        if type(raw) is not bytes:
            raise TypeError('DIFF_REQUIRES_EXACT_BYTES')
        if len(raw) > self.budget.max_input_bytes:
            raise _Limited('DIFF_INPUT_BYTE_LIMIT')
        tree = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique, parse_constant=_nonfinite)
        stack = [(tree, 0)]
        while stack:
            value, depth = stack.pop()
            self.spend()
            if depth > self.budget.max_depth:
                raise _Limited('DIFF_DEPTH_LIMIT')
            if type(value) is dict:
                stack.extend((v, depth + 1) for v in value.values())
            elif type(value) is list:
                stack.extend((v, depth + 1) for v in value)
        # The product decoder owns schema, nominal-type, field and formula rules.
        ir = decode_ir(raw)
        encoded = canonical_bytes(ir)
        return ir_to_data(ir), ContentDigest(DigestAlgorithm.SHA256, sha256(encoded).hexdigest())


def _logical(identity):
    return identity['project'], identity['entity_kind'], identity['entity']


def _index(declarations):
    result = {}
    for declaration in declarations:
        key = _logical(declaration['identity'])
        if key in result:
            raise _Incomparable('AMBIGUOUS_DECLARATION_LINEAGE')
        result[key] = declaration
    return result


def _fields(fields):
    counts, rows = {}, {}
    for field in fields:
        name = field['name']
        occurrence = counts.get(name, 0)
        counts[name] = occurrence + 1
        rows[(name, occurrence)] = field
    return rows


def diff_contracts(before: bytes, after: bytes, budget: DiffBudget = DiffBudget()) -> ContractDiff:
    """Compare validated IR bytes without matching names across namespaces.

    A logical declaration is matched by project/kind/ID. Revision changes stay
    explicit; multiple revisions of that same logical ID are ambiguous and are
    never resolved by latest or insertion order. Every list's order is retained.
    Exhaustion returns a visibly incomplete result, even after some changes.
    """
    changes = []
    left_digest = right_digest = None
    meter = None
    path = '$.budget'

    def report(status, code=None, reason=None):
        diagnostics = () if code is None else (DiffDiagnostic(code, path, reason or code),)
        return ContractDiff(status, left_digest, right_digest, tuple(changes), diagnostics,
                            meter.nodes if meter else 0)

    def emit(kind, location, left, right):
        nonlocal path
        path = location
        meter.spend()
        old = None if left is None else _json(left)
        new = None if right is None else _json(right)
        if old == new:
            return
        size = len(old or b'') + len(new or b'')
        if len(changes) >= budget.max_changes or meter.output + size > budget.max_output_bytes:
            raise _Limited('DIFF_OUTPUT_LIMIT')
        meter.output += size
        changes.append(ContractChange(kind, location, old, new))

    try:
        if type(budget) is not DiffBudget:
            raise TypeError('INVALID_DIFF_BUDGET')
        DiffBudget.__post_init__(budget)
        meter = _Meter(budget)
        path = '$.before'
        left, left_digest = meter.load(before)
        path = '$.after'
        right, right_digest = meter.load(after)
        path = '$.project'
        if left['project'] != right['project']:
            raise _Incomparable('DIFFERENT_PROJECTS')
        path = '$.declarations'
        old, new = _index(left['declarations']), _index(right['declarations'])
        emit(ChangeKind.SOURCE_PIN_CHANGED, '$.source', left['source'], right['source'])
        emit(ChangeKind.SOURCE_DIGEST_CHANGED, '$.source_digest', left['source_digest'], right['source_digest'])
        old_order, new_order = list(old), list(new)
        if set(old) == set(new):
            emit(ChangeKind.DECLARATION_ORDER_CHANGED, '$.declarations.order', old_order, new_order)
        else:
            # Compare retained order as well: additions/removals must not hide swaps.
            emit(ChangeKind.DECLARATION_ORDER_CHANGED, '$.declarations.retained_order',
                 [k for k in old_order if k in new], [k for k in new_order if k in old])
        for key in sorted(set(old) | set(new)):
            meter.spend()
            location = '$.declarations[' + '/'.join(key) + ']'
            if key not in new:
                emit(ChangeKind.DECLARATION_REMOVED, location, old[key], None)
                continue
            if key not in old:
                emit(ChangeKind.DECLARATION_ADDED, location, None, new[key])
                continue
            a, b = old[key], new[key]
            emit(ChangeKind.DECLARATION_REVISION_CHANGED, location + '.identity', a['identity'], b['identity'])
            emit(ChangeKind.DECLARATION_ORIGIN_CHANGED, location + '.origin', a['origin'], b['origin'])
            af, bf = _fields(a['fields']), _fields(b['fields'])
            # Occurrence keys preserve multiplicity of requires/verification fields.
            emit(ChangeKind.FIELD_ORDER_CHANGED, location + '.fields.order', list(af), list(bf))
            for field in sorted(set(af) | set(bf)):
                target = location + f'.fields[{field[0]}#{field[1]}]'
                kind = (ChangeKind.FIELD_ADDED if field not in af else
                        ChangeKind.FIELD_REMOVED if field not in bf else ChangeKind.FIELD_CHANGED)
                emit(kind, target, af.get(field), bf.get(field))
        path = '$.proofs'
        # Exact origin (including revision) belongs to proof identity.
        def proof_key(proof):
            return proof['identifier'], _json(proof['origin']).decode('utf-8')
        ap = {proof_key(p): p for p in left['proofs']}
        bp = {proof_key(p): p for p in right['proofs']}
        emit(ChangeKind.PROOF_ORDER_CHANGED, '$.proofs.order', list(ap), list(bp))
        for key in sorted(set(ap) | set(bp)):
            kind = (ChangeKind.PROOF_ADDED if key not in ap else
                    ChangeKind.PROOF_REMOVED if key not in bp else ChangeKind.PROOF_CHANGED)
            emit(kind, '$.proofs[' + _json(key).decode('utf-8') + ']', ap.get(key), bp.get(key))
        return report(DiffStatus.COMPLETE)
    except _Limited as exc:
        return report(DiffStatus.RESOURCE_LIMITED, str(exc))
    except _Incomparable as exc:
        return report(DiffStatus.INCOMPARABLE, str(exc))
    except RecursionError:
        return report(DiffStatus.RESOURCE_LIMITED, 'DIFF_DEPTH_LIMIT')
    except (TypeError, ValueError, KeyError, UnicodeError, OverflowError) as exc:
        return report(DiffStatus.REJECTED, 'INVALID_DIFF_INPUT', str(exc))


def diff_to_data(report: ContractDiff) -> dict:
    """Serializable report; difference observations never grant permission."""
    if type(report) is not ContractDiff:
        raise TypeError('TYPED_CONTRACT_DIFF_REQUIRED')
    ContractDiff.__post_init__(report)
    return {
        'schema': 'guardian/gsl0/contract-diff/v1', 'status': report.status.value,
        'before_digest': None if report.before_digest is None else encode_identity(report.before_digest),
        'after_digest': None if report.after_digest is None else encode_identity(report.after_digest),
        'structurally_identical': report.structurally_identical,
        'semantic_equivalence': report.semantic_equivalence,
        'normatively_admitted': False, 'requires_review': report.requires_review,
        'visited_nodes': report.visited_nodes,
        'changes': [{'kind': c.kind.value, 'path': c.path,
                     'before': None if c.before is None else json.loads(c.before),
                     'after': None if c.after is None else json.loads(c.after)} for c in report.changes],
        'diagnostics': [{'code': d.code, 'path': d.path, 'reason': d.reason} for d in report.diagnostics],
    }
