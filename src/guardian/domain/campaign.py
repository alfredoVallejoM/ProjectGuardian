"""G00-B03 immutable campaign membership, without admission or mutable completion."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, TYPE_CHECKING
from .project_view import ReadOnlyEntityView
if TYPE_CHECKING:
    from .references import TrustedEntityImports
from .identity import EntityKind, EntityRef
from .outcomes import DueStatus, Diagnostic, Result
from .obligation import ObligationRevision
from .record_base import RecordRevision, ReferenceUse, text, texts, ref, validate_record


class MembershipMode(str, Enum):
    REQUIRED='required'
    CONDITIONAL='conditional'
    ALTERNATIVE='alternative'


@dataclass(frozen=True, slots=True)
class Membership:
    obligation: EntityRef
    scope: EntityRef
    milestone: str
    mode: MembershipMode = MembershipMode.REQUIRED
    alternative_group: str | None = None

    def __post_init__(self) -> None:
        ref(self.obligation, EntityKind.OBLIGATION, 'INVALID_MEMBER')
        ref(self.scope, EntityKind.SCOPE, 'INVALID_MEMBERSHIP_SCOPE')
        text(self.milestone, 'MILESTONE_REQUIRED')
        if type(self.mode) is not MembershipMode:
            raise TypeError('MEMBERSHIP_MODE_REQUIRED')
        if self.mode is MembershipMode.ALTERNATIVE:
            text(self.alternative_group, 'ALTERNATIVE_POLICY_REQUIRED')
        elif self.alternative_group is not None:
            raise ValueError('UNEXPECTED_ALTERNATIVE_GROUP')


@dataclass(frozen=True, slots=True, kw_only=True)
class CampaignRevision(RecordRevision):
    KIND: ClassVar[EntityKind] = EntityKind.CAMPAIGN
    title: str
    membership: tuple[Membership, ...]
    closure_policy: tuple[str, ...]

    def __post_init__(self) -> None:
        RecordRevision.__post_init__(self)
        text(self.title, 'CAMPAIGN_TITLE_REQUIRED')
        if type(self.membership) is not tuple or not self.membership or any(type(x) is not Membership for x in self.membership):
            raise TypeError('CAMPAIGN_MEMBERSHIP_REQUIRED')
        keys = [(m.obligation, m.scope, m.milestone) for m in self.membership]
        if len(set(keys)) != len(keys):
            raise ValueError('AMBIGUOUS_MEMBERSHIP')
        texts(self.closure_policy, 'CLOSURE_POLICY_REQUIRED', nonempty=True)

    def references(self) -> tuple[ReferenceUse, ...]:
        result = RecordRevision.references(self)
        for i, member in enumerate(self.membership):
            result += (ReferenceUse(f'$.membership[{i}].obligation', member.obligation, EntityKind.OBLIGATION),
                       ReferenceUse(f'$.membership[{i}].scope', member.scope, EntityKind.SCOPE))
        return result


@dataclass(frozen=True, slots=True)
class DueDescription:
    declared_due: DueStatus
    at_declared_milestone: bool
    applicability: str = 'NOT_EVALUATED'
    admission: str = 'NOT_CHECKED'


def inspect_due(obligation: object, milestone: str) -> Result[DueDescription]:
    if type(obligation) is not ObligationRevision or type(milestone) is not str or not milestone:
        return Result(diagnostics=(Diagnostic('INVALID_DUE_QUERY', '$', 'obligation and milestone', 'invalid', 'untyped query'),))
    return Result(DueDescription(obligation.due, obligation.milestone == milestone))


def validate_campaign(campaign: object, view: ReadOnlyEntityView, *, grants: TrustedEntityImports | None = None) -> Result[CampaignRevision]:
    return validate_record(campaign, CampaignRevision, view, grants=grants)
