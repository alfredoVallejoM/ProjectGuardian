"""Pure proposals: constructing an amendment never changes a policy."""
from dataclasses import dataclass
from guardian.domain.constitution import RuleRevision
from guardian.domain.identity import EntityRef
from guardian.domain.outcomes import Result
from guardian.domain.authority import diagnostic, exact_tuple
from guardian.domain.record_base import text


@dataclass(frozen=True, slots=True)
class AmendmentRationale:
    explanation: str
    affected_contracts: tuple[EntityRef, ...]

    def __post_init__(self):
        text(self.explanation,'AMENDMENT_RATIONALE_REQUIRED')
        exact_tuple(self.affected_contracts,EntityRef,'AMENDMENT_IMPACT',nonempty=True)


@dataclass(frozen=True, slots=True)
class AmendmentRequest:
    prior: RuleRevision
    proposal: RuleRevision
    rationale: AmendmentRationale

    @property
    def status(self):
        return 'PROPOSED_ONLY'


def make_amendment_request(prior: RuleRevision, proposal: RuleRevision,
                           rationale: AmendmentRationale) -> Result[AmendmentRequest]:
    try:
        if type(prior) is not RuleRevision or type(proposal) is not RuleRevision or type(rationale) is not AmendmentRationale:
            raise TypeError('INVALID_AMENDMENT')
        RuleRevision.__post_init__(prior); RuleRevision.__post_init__(proposal)
        AmendmentRationale.__post_init__(rationale)
        if prior.identity.entity != proposal.identity.entity or prior.identity.revision == proposal.identity.revision:
            raise ValueError('INVALID_LINEAGE')
        if any(r.project != prior.identity.project for r in rationale.affected_contracts):
            raise ValueError('AMENDMENT_IMPACT_PROJECT_MISMATCH')
        return Result(AmendmentRequest(prior,proposal,rationale))
    except (TypeError,ValueError,AttributeError) as exc:
        return Result(diagnostics=(diagnostic(str(exc),'$.amendment','no policy mutation performed'),))
