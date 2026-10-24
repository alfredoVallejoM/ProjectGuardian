"""G00-B04: pure, evidence-scoped four-valued applicability.

A result describes supplied information, not authenticated truth or admission.
Missing data stays UNKNOWN. Resource exhaustion has no applicability value.
No project callback, clock, I/O, or implicit current project is used here.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import ClassVar

from .evidence_logic import FourValued, UNKNOWN, YES, NO, CONFLICT
from .identity import ContentDigest, EntityKind, EntityRef, ProjectId, RevisionId
from .outcomes import Diagnostic, Result
from .record_base import RecordRevision, ReferenceUse, ref

_NAME = re.compile(r'[a-z][a-z0-9_.-]*\Z', re.ASCII)
_MAX_ITEMS = 4096
_MAX_DEPTH = 64


def _name(value: object, code: str = 'INVALID_DIMENSION_NAME') -> None:
    if type(value) is not str or len(value) > 128 or not _NAME.fullmatch(value):
        raise ValueError(code)


def _tuple(value: object, kind: type, code: str, *, nonempty: bool = False) -> None:
    if type(value) is not tuple or len(value) > _MAX_ITEMS or (nonempty and not value):
        raise ValueError(code)
    if any(type(x) is not kind for x in value):
        raise TypeError(code)


def _diag(code: str, path: str, reason: str) -> Diagnostic:
    return Diagnostic(code, path, 'typed scoped evidence', 'scope input', reason)


class ValueKind(str, Enum):
    TEXT = 'text'
    INTEGER = 'integer'
    BOOLEAN = 'boolean'
    TEXT_SET = 'text_set'


class Operator(str, Enum):
    EQUALS = 'equals'
    CONTAINS = 'contains'
    IN_RANGE = 'in_range'
    PRESENT = 'present'


@dataclass(frozen=True, slots=True)
class DimensionValue:
    kind: ValueKind
    value: str | int | bool | frozenset[str]

    def __post_init__(self) -> None:
        if type(self.kind) is not ValueKind:
            raise TypeError('INVALID_DIMENSION_TYPE')
        typ = {ValueKind.TEXT: str, ValueKind.INTEGER: int,
               ValueKind.BOOLEAN: bool, ValueKind.TEXT_SET: frozenset}[self.kind]
        if type(self.value) is not typ:
            raise TypeError('INVALID_DIMENSION_VALUE')
        if self.kind is ValueKind.TEXT_SET and (len(self.value) > _MAX_ITEMS or any(type(x) is not str for x in self.value)):
            raise TypeError('INVALID_DIMENSION_VALUE')


@dataclass(frozen=True, slots=True)
class IntegerRange:
    minimum: int
    maximum: int

    def __post_init__(self) -> None:
        if type(self.minimum) is not int or type(self.maximum) is not int or self.minimum > self.maximum:
            raise ValueError('INVALID_INTEGER_RANGE')


@dataclass(frozen=True, slots=True)
class ProfileDimensionSchema:
    name: str
    version: str
    kind: ValueKind
    operators: frozenset[Operator]

    def __post_init__(self) -> None:
        _name(self.name)
        _name(self.version, 'DIMENSION_VERSION_REQUIRED')
        if type(self.kind) is not ValueKind or type(self.operators) is not frozenset or not self.operators:
            raise TypeError('INVALID_DIMENSION_SCHEMA')
        allowed = {Operator.PRESENT, Operator.EQUALS}
        if self.kind is ValueKind.TEXT_SET:
            allowed.add(Operator.CONTAINS)
        if self.kind is ValueKind.INTEGER:
            allowed.add(Operator.IN_RANGE)
        if any(type(op) is not Operator or op not in allowed for op in self.operators):
            raise ValueError('INVALID_DIMENSION_OPERATOR')


@dataclass(frozen=True, slots=True)
class DimensionRegistry:
    revision: RevisionId
    schemas: tuple[ProfileDimensionSchema, ...]

    def __post_init__(self) -> None:
        if type(self.revision) is not RevisionId:
            raise TypeError('REGISTRY_REVISION_REQUIRED')
        _tuple(self.schemas, ProfileDimensionSchema, 'INVALID_DIMENSION_REGISTRY', nonempty=True)
        for schema in self.schemas:
            ProfileDimensionSchema.__post_init__(schema)
        if len({s.name for s in self.schemas}) != len(self.schemas):
            raise ValueError('DUPLICATE_DIMENSION_SCHEMA')


def foundation_dimension_registry(revision: RevisionId) -> DimensionRegistry:
    """Explicit local registry; callers pin its revision rather than use latest."""
    def schema(name: str, kind: ValueKind) -> ProfileDimensionSchema:
        ops = {Operator.EQUALS, Operator.PRESENT}
        if kind is ValueKind.TEXT_SET:
            ops.add(Operator.CONTAINS)
        if kind is ValueKind.INTEGER:
            ops.add(Operator.IN_RANGE)
        return ProfileDimensionSchema(name, 'v1', kind, frozenset(ops))
    return DimensionRegistry(revision, tuple(schema(name, kind) for name, kind in (
        ('features', ValueKind.TEXT_SET), ('platform', ValueKind.TEXT),
        ('toolchain', ValueKind.TEXT), ('domain', ValueKind.TEXT),
        ('representation', ValueKind.TEXT), ('consumers', ValueKind.TEXT_SET),
        ('resources.memory_bytes', ValueKind.INTEGER), ('resources.cpu_count', ValueKind.INTEGER),
    )))


@dataclass(frozen=True, slots=True)
class ScopeContext:
    project_id: ProjectId
    project_revision: RevisionId
    profile_revision: RevisionId
    registry_revision: RevisionId
    source_universe_ref: EntityRef
    verification_policy_ref: EntityRef
    milestone: str
    candidate_ref: EntityRef | None = None

    def __post_init__(self) -> None:
        if type(self.project_id) is not ProjectId or any(type(r) is not RevisionId for r in (
                self.project_revision, self.profile_revision, self.registry_revision)):
            raise TypeError('INVALID_PROFILE_IDENTITY')
        ref(self.source_universe_ref, EntityKind.SOURCE_UNIVERSE, 'INVALID_PROFILE_UNIVERSE')
        ref(self.verification_policy_ref, (EntityKind.SOURCE_POLICY, EntityKind.CONSTITUTION), 'INVALID_PROFILE_POLICY')
        _name(self.milestone, 'INVALID_PROFILE_MILESTONE')
        if self.candidate_ref is not None:
            ref(self.candidate_ref, EntityKind.IMPLEMENTATION, 'INVALID_PROFILE_CANDIDATE')
        if any(r.project != self.project_id for r in (self.source_universe_ref, self.verification_policy_ref)
               + ((self.candidate_ref,) if self.candidate_ref is not None else ())):
            raise ValueError('PROFILE_CROSS_PROJECT_REF')


@dataclass(frozen=True, slots=True)
class ScopeWitness:
    context: ScopeContext
    source_ref: EntityRef
    identifier: str
    description: str

    def __post_init__(self) -> None:
        if type(self.context) is not ScopeContext:
            raise TypeError('WITNESS_CONTEXT_REQUIRED')
        ref(self.source_ref, EntityKind.SOURCE, 'WITNESS_SOURCE_REQUIRED')
        _name(self.identifier, 'WITNESS_ID_REQUIRED')
        if type(self.description) is not str or not self.description.strip():
            raise ValueError('WITNESS_DESCRIPTION_REQUIRED')
        if self.source_ref.project != self.context.project_id:
            raise ValueError('WITNESS_PROJECT_MISMATCH')


def _witnesses(value: object, *, required: bool = False) -> None:
    _tuple(value, ScopeWitness, 'INVALID_SCOPE_WITNESSES', nonempty=required)
    for witness in value:
        ScopeWitness.__post_init__(witness)


def _witness_key(w: ScopeWitness) -> tuple[str, ...]:
    return (w.source_ref.project.value, w.source_ref.entity.value,
            w.source_ref.revision.value, w.identifier, w.description)


def _canonical_witnesses(witnesses: tuple[ScopeWitness, ...]) -> tuple[ScopeWitness, ...]:
    return tuple(sorted(set(witnesses), key=_witness_key))


@dataclass(frozen=True, slots=True)
class DimensionObservation:
    dimension: str
    version: str
    value: DimensionValue | None
    witnesses: tuple[ScopeWitness, ...]
    complete: bool = False
    completeness_witnesses: tuple[ScopeWitness, ...] = ()

    def __post_init__(self) -> None:
        _name(self.dimension)
        _name(self.version, 'DIMENSION_VERSION_REQUIRED')
        if self.value is not None:
            if type(self.value) is not DimensionValue:
                raise TypeError('INVALID_DIMENSION_VALUE')
            DimensionValue.__post_init__(self.value)
        if type(self.complete) is not bool:
            raise TypeError('INVALID_COMPLETENESS_FLAG')
        _witnesses(self.witnesses, required=self.value is not None)
        _witnesses(self.completeness_witnesses, required=self.complete)
        if not self.complete and self.completeness_witnesses:
            raise ValueError('UNDECLARED_COMPLETENESS_EVIDENCE')


@dataclass(frozen=True, slots=True)
class SupportProfile:
    context: ScopeContext
    registry: DimensionRegistry
    dimensions: tuple[DimensionObservation, ...] = ()
    required_dimensions: tuple[str, ...] = ()
    informational: tuple[tuple[str, DimensionValue], ...] = ()

    @property
    def project_id(self) -> ProjectId:
        return self.context.project_id

    @property
    def project_revision(self) -> RevisionId:
        return self.context.project_revision

    @property
    def unknown_dimensions(self) -> tuple[str, ...]:
        observed = {x.dimension for x in self.dimensions if x.value is not None or x.complete}
        return tuple(sorted(s.name for s in self.registry.schemas if s.name not in observed))

    def __post_init__(self) -> None:
        if type(self.context) is not ScopeContext or type(self.registry) is not DimensionRegistry:
            raise TypeError('INVALID_SUPPORT_PROFILE')
        ScopeContext.__post_init__(self.context)
        DimensionRegistry.__post_init__(self.registry)
        if self.context.registry_revision != self.registry.revision:
            raise ValueError('PROFILE_REGISTRY_REVISION_MISMATCH')
        _tuple(self.dimensions, DimensionObservation, 'INVALID_PROFILE_DIMENSIONS')
        _tuple(self.required_dimensions, str, 'INVALID_REQUIRED_DIMENSIONS')
        schemas = {x.name: x for x in self.registry.schemas}
        if len(set(self.required_dimensions)) != len(self.required_dimensions):
            raise ValueError('DUPLICATE_REQUIRED_DIMENSION')
        if any(n not in schemas for n in self.required_dimensions):
            raise ValueError('UNKNOWN_NORMATIVE_DIMENSION')
        for observation in self.dimensions:
            _validate_observation(observation, self.context, schemas)
        if type(self.informational) is not tuple or len(self.informational) > _MAX_ITEMS:
            raise TypeError('INVALID_INFORMATIONAL_EXTENSIONS')
        names = []
        for pair in self.informational:
            if type(pair) is not tuple or len(pair) != 2 or type(pair[0]) is not str or not pair[0].startswith('info.') or type(pair[1]) is not DimensionValue:
                raise TypeError('INVALID_INFORMATIONAL_EXTENSIONS')
            _name(pair[0]); DimensionValue.__post_init__(pair[1]); names.append(pair[0])
        if len(names) != len(set(names)):
            raise ValueError('DUPLICATE_INFORMATIONAL_EXTENSION')


def _validate_observation(observation: DimensionObservation, context: ScopeContext,
                          schemas: dict[str, ProfileDimensionSchema]) -> None:
    DimensionObservation.__post_init__(observation)
    schema = schemas.get(observation.dimension)
    if schema is None:
        raise ValueError('UNKNOWN_NORMATIVE_DIMENSION')
    if schema.version != observation.version:
        raise ValueError('DIMENSION_VERSION_MISMATCH')
    if observation.value is not None and observation.value.kind is not schema.kind:
        raise TypeError('INVALID_PREDICATE_TYPE')
    if any(w.context != context for w in observation.witnesses + observation.completeness_witnesses):
        raise ValueError('EVIDENCE_CONTEXT_MISMATCH')


@dataclass(frozen=True, slots=True)
class Atom:
    dimension: str
    operator: Operator
    operand: DimensionValue | IntegerRange | None = None
    evidence_ref: EntityRef | None = None

    def __post_init__(self) -> None:
        _name(self.dimension)
        if type(self.operator) is not Operator:
            raise TypeError('UNSAFE_SCOPE_PREDICATE')
        if self.evidence_ref is not None:
            ref(self.evidence_ref, EntityKind.SOURCE, 'ATOM_EVIDENCE_SOURCE_REQUIRED')
        if self.operator is Operator.PRESENT:
            if self.operand is not None:
                raise ValueError('INVALID_SCOPE_ARITY')
        elif self.operator is Operator.IN_RANGE:
            if type(self.operand) is not IntegerRange:
                raise TypeError('INVALID_PREDICATE_TYPE')
            IntegerRange.__post_init__(self.operand)
        elif type(self.operand) is not DimensionValue:
            raise TypeError('INVALID_PREDICATE_TYPE')
        else:
            DimensionValue.__post_init__(self.operand)


@dataclass(frozen=True, slots=True)
class All:
    expressions: tuple[ScopeExpression, ...]

    def __post_init__(self) -> None:
        _children(self.expressions)


@dataclass(frozen=True, slots=True)
class Any:
    expressions: tuple[ScopeExpression, ...]

    def __post_init__(self) -> None:
        _children(self.expressions)


@dataclass(frozen=True, slots=True)
class Not:
    expression: ScopeExpression

    def __post_init__(self) -> None:
        if type(self.expression) not in _NODE_TYPES:
            raise TypeError('UNSAFE_SCOPE_PREDICATE')


@dataclass(frozen=True, slots=True)
class TrueConst:
    authorization_ref: EntityRef

    def __post_init__(self) -> None:
        ref(self.authorization_ref, EntityKind.DECISION, 'CONSTANT_AUTHORIZATION_REQUIRED')


@dataclass(frozen=True, slots=True)
class FalseConst:
    authorization_ref: EntityRef

    def __post_init__(self) -> None:
        ref(self.authorization_ref, EntityKind.DECISION, 'CONSTANT_AUTHORIZATION_REQUIRED')


@dataclass(frozen=True, slots=True)
class VerifierPredicate:
    verifier_ref: EntityRef
    input_contract: ContentDigest
    version: str

    def __post_init__(self) -> None:
        ref(self.verifier_ref, EntityKind.VERIFICATION, 'VERIFIER_REFERENCE_REQUIRED')
        if type(self.input_contract) is not ContentDigest:
            raise TypeError('VERIFIER_INPUT_DIGEST_REQUIRED')
        _name(self.version, 'VERIFIER_VERSION_REQUIRED')


ScopeExpression = Atom | All | Any | Not | TrueConst | FalseConst | VerifierPredicate
_NODE_TYPES = (Atom, All, Any, Not, TrueConst, FalseConst, VerifierPredicate)


def _children(children: object) -> None:
    if type(children) is not tuple or not children or len(children) > _MAX_ITEMS:
        raise ValueError('INVALID_SCOPE_ARITY')
    if any(type(x) not in _NODE_TYPES for x in children):
        raise TypeError('UNSAFE_SCOPE_PREDICATE')


@dataclass(frozen=True, slots=True)
class VerifiedPredicateObservation:
    """Trusted observation supplied by caller; no plugin is ever executed."""
    predicate: VerifierPredicate
    context: ScopeContext
    positive_witnesses: tuple[ScopeWitness, ...] = ()
    negative_witnesses: tuple[ScopeWitness, ...] = ()

    def __post_init__(self) -> None:
        if type(self.predicate) is not VerifierPredicate or type(self.context) is not ScopeContext:
            raise TypeError('INVALID_VERIFIER_OBSERVATION')
        VerifierPredicate.__post_init__(self.predicate)
        _witnesses(self.positive_witnesses); _witnesses(self.negative_witnesses)
        if self.predicate.verifier_ref.project != self.context.project_id or any(
                w.context != self.context for w in self.positive_witnesses + self.negative_witnesses):
            raise ValueError('EVIDENCE_CONTEXT_MISMATCH')


@dataclass(frozen=True, slots=True)
class ConstantAuthorization:
    decision_ref: EntityRef
    witness: ScopeWitness
    allow_true: bool
    allow_false: bool

    def __post_init__(self) -> None:
        ref(self.decision_ref, EntityKind.DECISION, 'CONSTANT_AUTHORIZATION_REQUIRED')
        if type(self.witness) is not ScopeWitness or type(self.allow_true) is not bool or type(self.allow_false) is not bool:
            raise TypeError('INVALID_CONSTANT_AUTHORIZATION')
        if self.decision_ref.project != self.witness.context.project_id:
            raise ValueError('CONSTANT_AUTHORIZATION_PROJECT_MISMATCH')


@dataclass(frozen=True, slots=True)
class FactSet:
    context: ScopeContext
    source_refs: frozenset[EntityRef]
    dimensions: tuple[DimensionObservation, ...] = ()
    verified_predicates: tuple[VerifiedPredicateObservation, ...] = ()
    constant_authorizations: tuple[ConstantAuthorization, ...] = ()

    def __post_init__(self) -> None:
        if type(self.context) is not ScopeContext:
            raise TypeError('FACT_CONTEXT_REQUIRED')
        if type(self.source_refs) is not frozenset or len(self.source_refs) > _MAX_ITEMS or any(
                type(x) is not EntityRef or x.kind is not EntityKind.SOURCE or x.project != self.context.project_id for x in self.source_refs):
            raise TypeError('FACT_SOURCE_CATALOG_REQUIRED')
        _tuple(self.dimensions, DimensionObservation, 'INVALID_FACT_DIMENSIONS')
        _tuple(self.verified_predicates, VerifiedPredicateObservation, 'INVALID_VERIFIER_OBSERVATIONS')
        _tuple(self.constant_authorizations, ConstantAuthorization, 'INVALID_CONSTANT_AUTHORIZATIONS')
        ws = []
        for observation in self.dimensions:
            DimensionObservation.__post_init__(observation)
            ws.extend(observation.witnesses + observation.completeness_witnesses)
        for observation in self.verified_predicates:
            VerifiedPredicateObservation.__post_init__(observation)
            if observation.context != self.context:
                raise ValueError('EVIDENCE_CONTEXT_MISMATCH')
            ws.extend(observation.positive_witnesses + observation.negative_witnesses)
        for authorization in self.constant_authorizations:
            ConstantAuthorization.__post_init__(authorization)
            ws.append(authorization.witness)
        if len(ws) > _MAX_ITEMS:
            raise ValueError('FACT_WITNESS_LIMIT')
        if any(w.context != self.context or w.source_ref not in self.source_refs for w in ws):
            raise ValueError('EVIDENCE_CONTEXT_OR_SOURCE_MISMATCH')


@dataclass(frozen=True, slots=True)
class StepBudget:
    max_steps: int = 100000
    max_nodes: int = 4096
    max_depth: int = 64
    max_facts: int = 4096
    max_witnesses: int = 4096

    def __post_init__(self) -> None:
        for value, limit in ((self.max_steps, 1_000_000), (self.max_nodes, _MAX_ITEMS),
                             (self.max_depth, _MAX_DEPTH), (self.max_facts, _MAX_ITEMS),
                             (self.max_witnesses, _MAX_ITEMS)):
            if type(value) is not int or not 1 <= value <= limit:
                raise ValueError('INVALID_EVALUATION_BUDGET')


@dataclass(frozen=True, slots=True)
class ScopeConflict:
    """Both sides of an internal conflict survive a decisive outer value."""
    context: ScopeContext
    positive_witnesses: tuple[ScopeWitness, ...]
    negative_witnesses: tuple[ScopeWitness, ...]

    def __post_init__(self) -> None:
        if type(self.context) is not ScopeContext:
            raise TypeError('CONFLICT_CONTEXT_REQUIRED')
        ScopeContext.__post_init__(self.context)
        _witnesses(self.positive_witnesses, required=True)
        _witnesses(self.negative_witnesses, required=True)
        if any(w.context != self.context for w in self.positive_witnesses + self.negative_witnesses):
            raise ValueError('EVIDENCE_CONTEXT_MISMATCH')


def _conflict_key(conflict: ScopeConflict):
    return (tuple(_witness_key(w) for w in conflict.positive_witnesses),
            tuple(_witness_key(w) for w in conflict.negative_witnesses))


@dataclass(frozen=True, slots=True)
class ApplicabilityResult:
    context: ScopeContext
    value: FourValued
    positive_witnesses: tuple[ScopeWitness, ...] = ()
    negative_witnesses: tuple[ScopeWitness, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()
    retained_conflicts: tuple[ScopeConflict, ...] = ()

    def __post_init__(self) -> None:
        if type(self.context) is not ScopeContext or type(self.value) is not FourValued:
            raise TypeError('INVALID_APPLICABILITY_RESULT')
        ScopeContext.__post_init__(self.context)
        _tuple(self.retained_conflicts, ScopeConflict, 'INVALID_RETAINED_CONFLICTS')
        for conflict in self.retained_conflicts:
            ScopeConflict.__post_init__(conflict)
            if conflict.context != self.context:
                raise ValueError('EVIDENCE_CONTEXT_MISMATCH')
        _witnesses(self.positive_witnesses); _witnesses(self.negative_witnesses)
        _tuple(self.diagnostics, Diagnostic, 'INVALID_SCOPE_DIAGNOSTICS')
        if self.value.positive != bool(self.positive_witnesses) or self.value.negative != bool(self.negative_witnesses):
            raise ValueError('UNWITNESSED_APPLICABILITY')
        if any(w.context != self.context for w in self.positive_witnesses + self.negative_witnesses):
            raise ValueError('EVIDENCE_CONTEXT_MISMATCH')

    @property
    def conflicts(self) -> tuple[ScopeConflict, ...]:
        own = ((ScopeConflict(self.context, _canonical_witnesses(self.positive_witnesses),
                              _canonical_witnesses(self.negative_witnesses)),)
               if self.value == CONFLICT else ())
        return tuple(sorted(set(self.retained_conflicts + own), key=_conflict_key))

    @property
    def profile_revision(self) -> RevisionId:
        return self.context.profile_revision

    @property
    def policy_revision(self) -> RevisionId:
        return self.context.verification_policy_ref.revision


def _diagnostics(*items: tuple[Diagnostic, ...]) -> tuple[Diagnostic, ...]:
    return tuple(sorted(set(d for group in items for d in group), key=lambda d: (d.path, d.code, d.reason)))


def _combine(left: ApplicabilityResult, right: ApplicabilityResult, conjunction: bool) -> ApplicabilityResult:
    if type(left) is not ApplicabilityResult or type(right) is not ApplicabilityResult or left.context != right.context:
        raise ValueError('EVIDENCE_CONTEXT_MISMATCH')
    ApplicabilityResult.__post_init__(left); ApplicabilityResult.__post_init__(right)
    value = left.value.conjunction(right.value) if conjunction else left.value.disjunction(right.value)
    positive = _canonical_witnesses(left.positive_witnesses + right.positive_witnesses) if value.positive else ()
    negative = _canonical_witnesses(left.negative_witnesses + right.negative_witnesses) if value.negative else ()
    conflicts = tuple(sorted(set(left.conflicts + right.conflicts), key=_conflict_key))
    extra = ((_diag('APPLICABILITY_CONFLICT', '$', 'internal conflict retained with both witnesses'),)
             if conflicts else ())
    return ApplicabilityResult(left.context, value, positive, negative,
                               _diagnostics(left.diagnostics, right.diagnostics, extra), conflicts)


def and_evidence(left: ApplicabilityResult, right: ApplicabilityResult) -> ApplicabilityResult:
    return _combine(left, right, True)


def or_evidence(left: ApplicabilityResult, right: ApplicabilityResult) -> ApplicabilityResult:
    return _combine(left, right, False)


def negate_evidence(value: ApplicabilityResult) -> ApplicabilityResult:
    if type(value) is not ApplicabilityResult:
        raise TypeError('INVALID_APPLICABILITY_RESULT')
    ApplicabilityResult.__post_init__(value)
    conflicts = value.conflicts
    extra = ((_diag('APPLICABILITY_CONFLICT', '$', 'internal conflict retained with both witnesses'),)
             if conflicts else ())
    return ApplicabilityResult(value.context, value.value.negate(), value.negative_witnesses,
                               value.positive_witnesses, _diagnostics(value.diagnostics, extra), conflicts)


class EvaluationStatus(str, Enum):
    COMPLETE = 'COMPLETE'
    INVALID_INPUT = 'INVALID_INPUT'
    RESOURCE_LIMITED = 'RESOURCE_LIMITED'


@dataclass(frozen=True, slots=True)
class ScopeTrace:
    path: str
    operator: str
    result: ApplicabilityResult

    def __post_init__(self) -> None:
        if type(self.path) is not str or not self.path.startswith('$') or type(self.operator) is not str:
            raise ValueError('INVALID_SCOPE_TRACE')
        if self.operator not in {t.__name__ for t in _NODE_TYPES} or type(self.result) is not ApplicabilityResult:
            raise ValueError('INVALID_SCOPE_TRACE')
        ApplicabilityResult.__post_init__(self.result)


@dataclass(frozen=True, slots=True)
class ScopeEvaluation:
    status: EvaluationStatus
    result: ApplicabilityResult | None
    diagnostics: tuple[Diagnostic, ...]
    trace: tuple[ScopeTrace, ...]
    steps: int
    nodes: int
    unexamined: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.status) is not EvaluationStatus or (self.status is EvaluationStatus.COMPLETE) != (type(self.result) is ApplicabilityResult):
            raise ValueError('INVALID_SCOPE_EVALUATION_STATUS')
        _tuple(self.diagnostics, Diagnostic, 'INVALID_SCOPE_DIAGNOSTICS')
        _tuple(self.trace, ScopeTrace, 'INVALID_SCOPE_TRACE')
        _tuple(self.unexamined, str, 'INVALID_UNEXAMINED_NODES')
        if type(self.steps) is not int or type(self.nodes) is not int or min(self.steps, self.nodes) < 0:
            raise ValueError('INVALID_SCOPE_EVALUATION_COUNTER')
        if self.status is not EvaluationStatus.COMPLETE and not self.diagnostics:
            raise ValueError('EVALUATION_FAILURE_WITHOUT_DIAGNOSTIC')
        for entry in self.trace:
            ScopeTrace.__post_init__(entry)
        if self.status is EvaluationStatus.COMPLETE:
            ApplicabilityResult.__post_init__(self.result)
            if self.unexamined or not self.trace or self.trace[-1].path != '$' or self.trace[-1].result != self.result:
                raise ValueError('INCOMPLETE_SCOPE_REPORT')
            if len(self.trace) != self.nodes or len({t.path for t in self.trace}) != len(self.trace):
                raise ValueError('INCOMPLETE_SCOPE_REPORT')
            if any(t.result.context != self.result.context for t in self.trace):
                raise ValueError('EVIDENCE_CONTEXT_MISMATCH')
            if self.diagnostics != self.result.diagnostics:
                raise ValueError('SCOPE_DIAGNOSTIC_LOSS')

    @property
    def ok(self) -> bool:
        """Evaluation completed, even for UNKNOWN/CONFLICT; NOT a compliance PASS."""
        return self.status is EvaluationStatus.COMPLETE


class _Limited(Exception):
    pass


class _Meter:
    def __init__(self, budget: StepBudget):
        self.budget, self.steps, self.nodes = budget, 0, 0
        self.path = '$'

    def spend(self, amount: int = 1) -> None:
        if self.steps + amount > self.budget.max_steps:
            raise _Limited('EVALUATION_RESOURCE_LIMITED')
        self.steps += amount


def validate_support_profile(profile: object) -> Result[SupportProfile]:
    try:
        if type(profile) is not SupportProfile:
            raise TypeError('INVALID_SUPPORT_PROFILE')
        SupportProfile.__post_init__(profile)
        return Result(profile)
    except (TypeError, ValueError, AttributeError) as exc:
        return Result(diagnostics=(_diag(str(exc), '$.profile', 'profile or versioned dimension contract is invalid'),))


def _validate_node(node: object, registry: DimensionRegistry) -> None:
    if type(node) not in _NODE_TYPES:
        raise TypeError('UNSAFE_SCOPE_PREDICATE')
    type(node).__post_init__(node)
    if type(node) is Atom:
        schema = next((s for s in registry.schemas if s.name == node.dimension), None)
        if schema is None:
            raise ValueError('UNKNOWN_NORMATIVE_DIMENSION')
        if node.operator not in schema.operators:
            raise ValueError('INVALID_DIMENSION_OPERATOR')
        if node.operator is Operator.EQUALS and node.operand.kind is not schema.kind:
            raise TypeError('INVALID_PREDICATE_TYPE')
        if node.operator is Operator.CONTAINS and node.operand.kind is not ValueKind.TEXT:
            raise TypeError('INVALID_PREDICATE_TYPE')


def _walk(expr: object, registry: DimensionRegistry, meter: _Meter):
    # A bounded postorder; shared subexpressions are legal, ancestor cycles are not.
    stack, active, ordered = [(expr, '$', 1, False)], set(), []
    while stack:
        node, path, depth, leaving = stack.pop(); meter.path = path
        if leaving:
            active.remove(id(node)); ordered.append((node, path)); continue
        meter.spend()
        if depth > meter.budget.max_depth or meter.nodes >= meter.budget.max_nodes:
            raise _Limited('EVALUATION_RESOURCE_LIMITED')
        meter.nodes += 1
        if id(node) in active:
            raise ValueError('CYCLIC_SCOPE_EXPRESSION')
        _validate_node(node, registry)
        active.add(id(node)); stack.append((node, path, depth, True))
        children = node.expressions if type(node) in (All, Any) else (node.expression,) if type(node) is Not else ()
        if len(children) > meter.budget.max_nodes - meter.nodes:
            raise _Limited('EVALUATION_RESOURCE_LIMITED')
        stack.extend((child, f'{path}.{i}', depth+1, False) for i, child in reversed(tuple(enumerate(children))))
    return ordered


def validate_scope_expression(expr: object, registry: DimensionRegistry,
                              budget: StepBudget = StepBudget()) -> Result[ScopeExpression]:
    try:
        if type(registry) is not DimensionRegistry or type(budget) is not StepBudget:
            raise TypeError('INVALID_SCOPE_VALIDATION_CONTEXT')
        DimensionRegistry.__post_init__(registry); StepBudget.__post_init__(budget)
        _walk(expr, registry, _Meter(budget))
        return Result(expr)
    except (TypeError, ValueError, AttributeError, _Limited) as exc:
        return Result(diagnostics=(_diag(str(exc), '$.expression', 'expression rejected without executing project code'),))


def _atomic(atom: Atom, profile: SupportProfile, facts: FactSet, meter: _Meter, path: str) -> ApplicabilityResult:
    positive, negative = [], []
    for observation in profile.dimensions + facts.dimensions:
        meter.spend()
        if observation.dimension != atom.dimension:
            continue
        ws = observation.witnesses
        cs = observation.completeness_witnesses
        if atom.evidence_ref is not None:
            ws = tuple(w for w in ws if w.source_ref == atom.evidence_ref)
            cs = tuple(w for w in cs if w.source_ref == atom.evidence_ref)
        meter.spend(len(ws) + len(cs))
        value = observation.value
        if value is None:
            if observation.complete and cs:
                negative.extend(cs)
            continue
        if not ws:
            continue
        if atom.operator is Operator.PRESENT:
            positive.extend(ws)
        elif atom.operator is Operator.EQUALS:
            # Incomplete sets can prove positive membership but not set equality.
            if value.kind is ValueKind.TEXT_SET and not (observation.complete and cs):
                if not value.value <= atom.operand.value:
                    negative.extend(ws)
            elif value.value == atom.operand.value:
                positive.extend(ws + (cs if value.kind is ValueKind.TEXT_SET else ()))
            else:
                negative.extend(ws + (cs if value.kind is ValueKind.TEXT_SET else ()))
        elif atom.operator is Operator.CONTAINS:
            if atom.operand.value in value.value:
                positive.extend(ws)
            elif observation.complete and cs:
                negative.extend(cs)
        elif atom.operator is Operator.IN_RANGE:
            (positive if atom.operand.minimum <= value.value <= atom.operand.maximum else negative).extend(ws)
    return _atom_result(profile.context, positive, negative, path, 'APPLICABILITY_UNKNOWN')


def _atom_result(context: ScopeContext, positive, negative, path: str, missing_code: str) -> ApplicabilityResult:
    p, n = _canonical_witnesses(tuple(positive)), _canonical_witnesses(tuple(negative))
    value = FourValued(bool(p), bool(n))
    ds = ((_diag('APPLICABILITY_CONFLICT', path, 'positive and negative witnesses coexist'),) if value == CONFLICT
          else (_diag(missing_code, path, 'no sufficient supplied evidence'),) if value == UNKNOWN else ())
    return ApplicabilityResult(context, value, p, n, ds)


def evaluate_scope(expr: object, profile: SupportProfile, facts: FactSet,
                   budget: StepBudget = StepBudget()) -> ScopeEvaluation:
    meter, trace, results, order = None, [], {}, []
    try:
        if type(profile) is not SupportProfile or type(facts) is not FactSet or type(budget) is not StepBudget:
            raise TypeError('INVALID_SCOPE_EVALUATION_CONTEXT')
        StepBudget.__post_init__(budget); meter = _Meter(budget)
        population = len(profile.dimensions) + len(facts.dimensions) + len(facts.verified_predicates) + len(facts.constant_authorizations)
        if population > budget.max_facts:
            raise _Limited('EVALUATION_RESOURCE_LIMITED')
        SupportProfile.__post_init__(profile); FactSet.__post_init__(facts)
        if profile.context != facts.context:
            raise ValueError('EVIDENCE_CONTEXT_MISMATCH')
        schemas = {s.name: s for s in profile.registry.schemas}
        ws = []
        for observation in profile.dimensions + facts.dimensions:
            meter.spend(); _validate_observation(observation, profile.context, schemas)
            ws.extend(observation.witnesses + observation.completeness_witnesses)
        for observation in facts.verified_predicates:
            ws.extend(observation.positive_witnesses + observation.negative_witnesses)
        ws.extend(a.witness for a in facts.constant_authorizations)
        if len(ws) > budget.max_witnesses:
            raise _Limited('EVALUATION_RESOURCE_LIMITED')
        meter.spend(len(ws))
        if any(w.source_ref not in facts.source_refs for w in ws):
            raise ValueError('EVIDENCE_SOURCE_OUTSIDE_CATALOG')
        order = _walk(expr, profile.registry, meter)
        for node, path in order:
            meter.path = path; meter.spend()
            if type(node) is Atom:
                if node.evidence_ref is not None and node.evidence_ref.project != profile.project_id:
                    raise ValueError('EVIDENCE_CONTEXT_MISMATCH')
                result = _atomic(node, profile, facts, meter, path)
            elif type(node) is VerifierPredicate:
                if node.verifier_ref.project != profile.project_id:
                    raise ValueError('EVIDENCE_CONTEXT_MISMATCH')
                positive, negative = [], []
                for observation in facts.verified_predicates:
                    meter.spend()
                    if observation.predicate == node:
                        positive.extend(observation.positive_witnesses); negative.extend(observation.negative_witnesses)
                result = _atom_result(profile.context, positive, negative, path, 'MISSING_VERIFIED_OBSERVATION')
            elif type(node) in (TrueConst, FalseConst):
                witnesses = []
                for authorization in facts.constant_authorizations:
                    meter.spend()
                    allowed = authorization.allow_true if type(node) is TrueConst else authorization.allow_false
                    if authorization.decision_ref == node.authorization_ref and allowed:
                        witnesses.append(authorization.witness)
                if not witnesses:
                    raise ValueError('CONSTANT_NOT_AUTHORIZED')
                result = _atom_result(profile.context, witnesses if type(node) is TrueConst else (),
                                      witnesses if type(node) is FalseConst else (), path, 'CONSTANT_NOT_AUTHORIZED')
            elif type(node) is Not:
                result = negate_evidence(results[path + '.0'])
            else:
                result = results[path + '.0']
                for i in range(1, len(node.expressions)):
                    meter.spend()
                    right = results[f'{path}.{i}']
                    meter.spend(len(result.positive_witnesses) + len(result.negative_witnesses)
                                + len(right.positive_witnesses) + len(right.negative_witnesses))
                    result = and_evidence(result, right) if type(node) is All else or_evidence(result, right)
            results[path] = result; trace.append(ScopeTrace(path, type(node).__name__, result))
        result = results['$']
        return ScopeEvaluation(EvaluationStatus.COMPLETE, result, result.diagnostics, tuple(trace), meter.steps, meter.nodes)
    except _Limited as exc:
        path = meter.path if meter else '$'
        pending = tuple(p for _, p in order if p not in results) or (path,)
        return ScopeEvaluation(EvaluationStatus.RESOURCE_LIMITED, None,
            (_diag('EVALUATION_RESOURCE_LIMITED', path, str(exc)),), tuple(trace),
            meter.steps if meter else 0, meter.nodes if meter else 0, pending)
    except (TypeError, ValueError, AttributeError) as exc:
        return ScopeEvaluation(EvaluationStatus.INVALID_INPUT, None,
            (_diag(str(exc), meter.path if meter else '$', 'invalid scope contract or evidence context'),),
            tuple(trace), meter.steps if meter else 0, meter.nodes if meter else 0)


def evaluate_atom(atom: Atom, profile: SupportProfile, facts: FactSet,
                  budget: StepBudget = StepBudget()) -> ScopeEvaluation:
    if type(atom) is not Atom:
        return ScopeEvaluation(EvaluationStatus.INVALID_INPUT, None,
            (_diag('INVALID_ATOM', '$', 'Atom required'),), (), 0, 0)
    return evaluate_scope(atom, profile, facts, budget)


@dataclass(frozen=True, slots=True, kw_only=True)
class ScopeRevision(RecordRevision):
    """Actual scope body resolvable by B06; its label never admits a policy."""
    KIND: ClassVar[EntityKind] = EntityKind.SCOPE
    registry: DimensionRegistry
    expression: ScopeExpression

    def __post_init__(self) -> None:
        RecordRevision.__post_init__(self)
        validated = validate_scope_expression(self.expression, self.registry)
        if not validated.ok:
            raise ValueError(validated.diagnostics[0].code)

    def references(self) -> tuple[ReferenceUse, ...]:
        result = list(RecordRevision.references(self))
        order = _walk(self.expression, self.registry, _Meter(StepBudget()))
        for node, path in order:
            target = (node.evidence_ref if type(node) is Atom else
                      node.verifier_ref if type(node) is VerifierPredicate else
                      node.authorization_ref if type(node) in (TrueConst, FalseConst) else None)
            if target is not None:
                result.append(ReferenceUse('$.expression' + path[1:], target, target.kind))
        return tuple(result)
