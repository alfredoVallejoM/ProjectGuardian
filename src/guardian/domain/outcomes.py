"""G00-B01: typed outcomes, diagnostics and separate lifecycle axes.

A status is an observation, never an authority to certify other status axes.
State transition/admission policies are deliberately owned by later campaigns.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Generic, Mapping, TypeVar, TYPE_CHECKING

T = TypeVar('T')


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    path: str
    expected: str
    actual_type: str
    reason: str

    def __post_init__(self) -> None:
        if not all(isinstance(s, str) and s for s in (
            self.code, self.path, self.expected, self.actual_type, self.reason
        )):
            raise ValueError('diagnostic fields must be non-empty strings')


@dataclass(frozen=True, slots=True)
class Result(Generic[T]):
    value: T | None = None
    diagnostics: tuple[Diagnostic, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.diagnostics, tuple) or not all(isinstance(d, Diagnostic) for d in self.diagnostics):
            raise TypeError('diagnostics must be a tuple of Diagnostic')
        if self.value is not None and self.diagnostics:
            raise ValueError('value and errors must not coexist')

    @property
    def ok(self) -> bool:
        return self.value is not None and not self.diagnostics


class StatusAxis(str, Enum):
    SOURCE = 'source'
    DECISION = 'decision'
    COMMITMENT = 'commitment'
    IMPLEMENTATION = 'implementation'
    AUDIT = 'audit'
    MATERIAL = 'material'
    SUPPORT = 'support'
    QUALIFICATION = 'qualification'
    MIGRATION = 'migration'


class SourceStatus(str, Enum):
    UNIDENTIFIED = 'unidentified'
    IDENTIFIED = 'identified'
    IDENTITY_VERIFIED = 'identity_verified'
    CONTENT_OBSERVED = 'content_observed'
    SEMANTIC_RECONCILED = 'semantic_reconciled'
    MISSING = 'missing'


class DecisionStatus(str, Enum):
    PROPOSED = 'proposed'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    SUPERSEDED = 'superseded'


class CommitmentStatus(str, Enum):
    DRAFT = 'draft'
    ADMITTED = 'admitted'
    SUSPENDED = 'suspended'
    SUPERSEDED = 'superseded'


class ImplementationStatus(str, Enum):
    NOT_IMPLEMENTED = 'not_implemented'
    IN_PROGRESS = 'in_progress'
    DEVELOPED_CANDIDATE = 'developed_candidate'
    DEVELOPMENT_COMPLETE = 'development_complete'


class AuditStatus(str, Enum):
    NOT_REVIEWED = 'not_reviewed'
    FINDINGS = 'findings'
    PASS = 'pass'
    HOLD = 'hold'


class MaterialStatus(str, Enum):
    NOT_RUN = 'not_run'
    PASS = 'pass'
    FAIL = 'fail'
    SKIPPED = 'skipped'
    INCONCLUSIVE = 'inconclusive'


class SupportStatus(str, Enum):
    UNKNOWN = 'unknown'
    SUPPORTED = 'supported'
    UNSUPPORTED = 'unsupported'
    CONFLICT = 'conflict'


class QualificationStatus(str, Enum):
    UNQUALIFIED = 'unqualified'
    CANDIDATE = 'candidate'
    QUALIFIED = 'qualified'
    REVOKED = 'revoked'


class MigrationStatus(str, Enum):
    NOT_STARTED = 'not_started'
    IN_PROGRESS = 'in_progress'
    PRESERVATION_PENDING = 'preservation_pending'
    QUALIFIED = 'qualified'
    HOLD = 'hold'


StatusValue = (
    SourceStatus | DecisionStatus | CommitmentStatus | ImplementationStatus |
    AuditStatus | MaterialStatus | SupportStatus | QualificationStatus | MigrationStatus
)
_STATUS_TYPES: Mapping[StatusAxis, type[Enum]] = {
    StatusAxis.SOURCE: SourceStatus,
    StatusAxis.DECISION: DecisionStatus,
    StatusAxis.COMMITMENT: CommitmentStatus,
    StatusAxis.IMPLEMENTATION: ImplementationStatus,
    StatusAxis.AUDIT: AuditStatus,
    StatusAxis.MATERIAL: MaterialStatus,
    StatusAxis.SUPPORT: SupportStatus,
    StatusAxis.QUALIFICATION: QualificationStatus,
    StatusAxis.MIGRATION: MigrationStatus,
}


@dataclass(frozen=True, slots=True)
class TypedStatus:
    axis: StatusAxis
    value: StatusValue

    def __post_init__(self) -> None:
        if not isinstance(self.axis, StatusAxis) or not isinstance(self.value, _STATUS_TYPES[self.axis]):
            raise TypeError('status value belongs to a different axis')


def parse_status(axis: object, value: object, path: str = '$.status') -> Result[TypedStatus]:
    if not isinstance(axis, StatusAxis):
        return Result(diagnostics=(Diagnostic('WRONG_STATUS_AXIS', path, 'StatusAxis', type(axis).__name__, 'unknown status axis'),))
    if type(value) is _STATUS_TYPES[axis]:
        return Result(TypedStatus(axis, value))
    if isinstance(value, Enum):
        return Result(diagnostics=(Diagnostic('WRONG_STATUS_AXIS', path, _STATUS_TYPES[axis].__name__, type(value).__name__, 'enum belongs to another axis'),))
    if type(value) is not str:
        return Result(diagnostics=(Diagnostic('UNSUPPORTED_VARIANT', path, _STATUS_TYPES[axis].__name__, type(value).__name__, 'not a string'),))
    try:
        return Result(TypedStatus(axis, _STATUS_TYPES[axis](value)))
    except (ValueError, TypeError):
        return Result(diagnostics=(Diagnostic('UNSUPPORTED_VARIANT', path, _STATUS_TYPES[axis].__name__, type(value).__name__, 'value unsupported on this axis'),))


def render_status_vector(items: tuple[TypedStatus, ...]) -> Result[dict[str, str]]:
    if not isinstance(items, tuple) or any(not isinstance(i, TypedStatus) for i in items):
        return Result(diagnostics=(Diagnostic('WRONG_STATUS_AXIS', '$.statuses', 'tuple[TypedStatus]', type(items).__name__, 'invalid status vector'),))
    axes = [i.axis for i in items]
    if len(set(axes)) != len(axes):
        return Result(diagnostics=(Diagnostic('DUPLICATE_STATUS_AXIS', '$.statuses', 'unique axes', 'tuple', 'axis was specified multiple times'),))
    # Display all nine axes, including those with no observation. Absence of
    # evidence is not an inferred status (especially not PASS or QUALIFIED).
    observed={i.axis:i.value.value for i in items}
    return Result({axis.value:observed.get(axis,'unobserved') for axis in sorted(StatusAxis,key=lambda x:x.value)})


def check_illegal_promotion(source: TypedStatus, target: TypedStatus) -> Result[bool]:
    """Basic anti-promotion invariant; transition validation belongs to G01/G06/G09."""
    if not isinstance(source, TypedStatus) or not isinstance(target, TypedStatus):
        return Result(diagnostics=(Diagnostic('WRONG_STATUS_AXIS', '$.promotion', 'TypedStatus pair', 'unknown', 'untyped promotion'),))
    if source.axis != target.axis:
        return Result(diagnostics=(Diagnostic('ILLEGAL_STATUS_PROMOTION', '$.promotion', source.axis.value, target.axis.value, 'cross-axis promotion forbidden'),))
    if source == target:
        return Result(True)
    return Result(diagnostics=(Diagnostic('TRANSITION_NOT_AUTHORIZED', '$.promotion', 'authorized G01/G09 transition', target.value.value, 'pure domain cannot promote lifecycle state'),))


class DueStatus(str, Enum):
    """Orthogonal scheduling classification; not a decision or admission status."""
    CURRENT='current'
    FUTURE='future'
    CONDITIONAL='conditional'
    OPTIONAL='optional'
    RESEARCH='research'


@dataclass(frozen=True,slots=True)
class StatusObservation:
    """Untrusted, descriptive status assertion with pinned provenance.

    Future G01/G06/G09 may project authorized states from verified events;
    merely constructing this value never issues a certificate or transition.
    """
    entity: object
    status: TypedStatus
    source_ref: object
    scope_ref: object
    revision: object
    observer: str
    evidence_refs: tuple[object,...]=()
    due: DueStatus|None=None

    def __post_init__(self)->None:
        # Local import avoids domain identity↔outcomes import cycle.
        from guardian.domain.identity import EntityRef,EntityKind,RevisionId
        if not isinstance(self.entity,EntityRef) or not isinstance(self.status,TypedStatus):
            raise TypeError('INVALID_STATUS_OBSERVATION')
        if not isinstance(self.source_ref,EntityRef) or self.source_ref.kind is not EntityKind.SOURCE:
            raise TypeError('STATUS_SOURCE_REF_REQUIRED')
        if not isinstance(self.scope_ref,EntityRef) or self.scope_ref.kind is not EntityKind.SCOPE:
            raise TypeError('STATUS_SCOPE_REF_REQUIRED')
        if not isinstance(self.revision,RevisionId):
            raise TypeError('STATUS_REVISION_REQUIRED')
        if type(self.observer) is not str or not self.observer.strip():
            raise ValueError('STATUS_OBSERVER_REQUIRED')
        if (type(self.evidence_refs) is not tuple
                or any(not isinstance(x,EntityRef) for x in self.evidence_refs)):
            raise TypeError('STATUS_EVIDENCE_REFS_INVALID')
        if self.due is not None and not isinstance(self.due,DueStatus):
            raise TypeError('STATUS_DUE_INVALID')
        if any(x.project != self.entity.project for x in
               (self.source_ref,self.scope_ref,*self.evidence_refs)):
            raise ValueError('STATUS_CROSS_PROJECT_PROVENANCE')


def validate_status_observation(observation: object, project_view: object) -> Result[StatusObservation]:
    """Structural and source-membership validation, NO authority promotion."""
    from guardian.domain.project_view import ReadOnlyEntityView
    if not isinstance(observation,StatusObservation) or not isinstance(project_view,ReadOnlyEntityView):
        return Result(diagnostics=(Diagnostic('INVALID_STATUS_OBSERVATION','$.status',
            'StatusObservation+ReadOnlyProjectView','untyped','status observation must be scoped'),))
    if observation.entity.project!=project_view.project_id:
        return Result(diagnostics=(Diagnostic('STATUS_WRONG_PROJECT','$.entity',
            'local project','foreign','status observation belongs to another project'),))
    if not project_view.contains_source(observation.source_ref):
        return Result(diagnostics=(Diagnostic('STATUS_SOURCE_OUTSIDE_UNIVERSE','$.source',
            'included source cut','unknown','status provenance absent from source universe'),))
    if observation.revision != observation.entity.revision:
        return Result(diagnostics=(Diagnostic('STATUS_REVISION_MISMATCH','$.revision',
            'entity revision','different revision','status observation revision is not pinned to entity'),))
    for label, ref in (('entity', observation.entity), ('scope', observation.scope_ref),
                       *((f'evidence[{i}]', ref) for i, ref in enumerate(observation.evidence_refs))):
        if not project_view.contains_entity(ref):
            return Result(diagnostics=(Diagnostic('ORPHAN_REFERENCE', '$.'+label,
                'exact reference in snapshot', 'missing', 'no implicit revision or placeholder permitted'),))
    return Result(observation)


def encode_status(status: TypedStatus) -> dict[str, str]:
    """Versioned nominal codec; encoding is not lifecycle authorization."""
    if type(status) is not TypedStatus:
        raise TypeError('TypedStatus required')
    return {'schema': 'guardian.status/v1', 'axis': status.axis.value, 'value': status.value.value}


def decode_status(envelope: object) -> Result[TypedStatus]:
    if (type(envelope) is not dict or set(envelope) != {'schema', 'axis', 'value'}
            or any(type(v) is not str for v in envelope.values())
            or envelope['schema'] != 'guardian.status/v1'):
        return Result(diagnostics=(Diagnostic('INVALID_STATUS_SCHEMA', '$.status',
            'guardian.status/v1', type(envelope).__name__, 'strict nominal envelope required'),))
    try:
        axis = StatusAxis(envelope['axis'])
    except ValueError:
        return Result(diagnostics=(Diagnostic('WRONG_STATUS_AXIS', '$.status.axis',
            'known status axis', 'str', 'unknown axis'),))
    return parse_status(axis, envelope['value'])
