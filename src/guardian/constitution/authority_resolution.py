"""Pure authority policy queries. Authentication is outside G-00."""
from __future__ import annotations
from dataclasses import dataclass
from guardian.domain.authority import (AuthorityContext, AuthorityEvaluation, NormativeAction,
    PrincipalRef, evaluate_authority as _evaluate, diagnostic)
from guardian.domain.constitution import ConstitutionRevision
from guardian.domain.scope import SupportProfile
from guardian.domain.outcomes import Result


@dataclass(frozen=True, slots=True)
class ApprovalRequirements:
    minimum: int
    independent_author: bool
    policy_ref: object


def required_approvals(action: NormativeAction, scope: SupportProfile,
                       constitution: ConstitutionRevision) -> Result[ApprovalRequirements]:
    if (type(action) is not NormativeAction or type(scope) is not SupportProfile
            or type(constitution) is not ConstitutionRevision):
        return Result(diagnostics=(diagnostic('INVALID_APPROVAL_QUERY','$','typed request required'),))
    if (action.target.project != scope.project_id or constitution.identity.project != scope.project_id
            or constitution.policy_ref != scope.context.verification_policy_ref):
        return Result(diagnostics=(diagnostic('APPROVAL_POLICY_MISMATCH','$','fixed policy and project required'),))
    matches = [r for r in constitution.approval_requirements if r.action is action.kind and action.scope_ref in r.scopes]
    if not matches:
        return Result(diagnostics=(diagnostic('UNKNOWN_AUTHORITY_RULE','$','missing approval rule is not permission'),))
    return Result(ApprovalRequirements(max(r.minimum for r in matches), any(r.independent_author for r in matches), constitution.policy_ref))


def evaluate_authority(actor: PrincipalRef, action: NormativeAction,
                       context: AuthorityContext) -> AuthorityEvaluation:
    return _evaluate(actor, action, context)
