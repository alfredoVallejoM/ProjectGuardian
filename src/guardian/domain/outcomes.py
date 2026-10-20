"""G00-B01: typed outcomes, diagnostics and separate lifecycle axes.

A status is an observation, never an authority to certify other status axes.
State transition/admission policies are deliberately owned by later campaigns.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Generic, Mapping, TypeVar

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
    if not isinstance(value, str):
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
    return Result({i.axis.value: i.value.value for i in sorted(items, key=lambda i: i.axis.value)})


def check_illegal_promotion(source: TypedStatus, target: TypedStatus) -> Result[bool]:
    """Basic anti-promotion invariant; transition validation belongs to G01/G06/G09."""
    if not isinstance(source, TypedStatus) or not isinstance(target, TypedStatus):
        return Result(diagnostics=(Diagnostic('WRONG_STATUS_AXIS', '$.promotion', 'TypedStatus pair', 'unknown', 'untyped promotion'),))
    if source.axis != target.axis:
        return Result(diagnostics=(Diagnostic('ILLEGAL_STATUS_PROMOTION', '$.promotion', source.axis.value, target.axis.value, 'cross-axis promotion forbidden'),))
    if source == target:
        return Result(True)
    return Result(diagnostics=(Diagnostic('TRANSITION_NOT_AUTHORIZED', '$.promotion', 'authorized G01/G09 transition', target.value.value, 'pure domain cannot promote lifecycle state'),))
