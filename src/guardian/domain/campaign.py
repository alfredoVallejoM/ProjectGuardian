"""G00-B03 immutable campaign membership, without admission or mutable completion."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, TYPE_CHECKING
from .project_view import ReadOnlyEntityView
if TYPE_CHECKING:
    from .references import TrustedEntityImports
    from .scope import SupportProfile, FactSet, ScopeRevision, StepBudget, ScopeEvaluation
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
    scope_evaluation: ScopeEvaluation | None = None

    @property
    def normatively_due(self) -> None:
        # Scope and scheduling do not authenticate constitutional approval.
        return None


def inspect_due(obligation: object, milestone: str, profile: SupportProfile | None = None,
                *, facts: FactSet | None = None, scope_record: ScopeRevision | None = None,
                budget: StepBudget | None = None) -> Result[DueDescription]:
    """Describe scheduling and, with a resolved scope, compute applicability.

    Approval is deliberately NOT inferred. FUTURE remains FUTURE even when
    the scope returns YES and the named milestone is the queried milestone.
    """
    from .scope import SupportProfile, ScopeRevision, StepBudget, evaluate_scope
    if type(obligation) is not ObligationRevision or type(milestone) is not str or not milestone:
        return Result(diagnostics=(Diagnostic('INVALID_DUE_QUERY', '$', 'obligation and milestone', 'invalid', 'untyped query'),))
    if profile is None:
        return Result(DueDescription(obligation.due, obligation.milestone == milestone))
    if (type(profile) is not SupportProfile or type(scope_record) is not ScopeRevision
            or scope_record.identity != obligation.applicability_ref
            or profile.project_id != obligation.identity.project
            or profile.context.milestone != milestone
            or profile.registry != scope_record.registry):
        return Result(diagnostics=(Diagnostic('DUE_SCOPE_CONTEXT_MISMATCH', '$.profile',
            'matching profile, exact scope and registry', 'mismatch', 'no implicit scope or milestone substitution'),))
    evaluation = evaluate_scope(scope_record.expression, profile, facts, budget if budget is not None else StepBudget())
    if not evaluation.ok:
        return Result(diagnostics=evaluation.diagnostics)
    bits = evaluation.result.value
    name = {(False,False):'UNKNOWN', (True,False):'YES', (False,True):'NO', (True,True):'CONFLICT'}[(bits.positive,bits.negative)]
    return Result(DueDescription(obligation.due, obligation.milestone == milestone,
                                name, 'NOT_CHECKED', evaluation))


def validate_campaign(campaign: object, view: ReadOnlyEntityView, *, grants: TrustedEntityImports | None = None) -> Result[CampaignRevision]:
    return validate_record(campaign, CampaignRevision, view, grants=grants)
