"""G00-04: explicit, revision-bound authority inputs and decision validation.

AuthorityContext is an input from a trusted boundary, NOT a way of authenticating
JSON. Approval binds the entire immutable decision, its policy and exact profile.
No constructor or validator ratifies or publishes a decision.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar
from .identity import EntityKind, EntityRef, ProjectId, RevisionId
from .outcomes import DecisionStatus, Diagnostic, Result
from .record_base import RecordRevision, ReferenceUse, ref, refs, text, texts, uses
from .scope import ScopeContext
from .claims import Assertion, AssertionDomain

MAX_AUTHORITY_ITEMS = 4096


def diagnostic(code: str, path: str, reason: str) -> Diagnostic:
    return Diagnostic(code, path, 'explicit scoped authority', 'authority input', reason)


def exact_tuple(value: object, typ: type, code: str, *, nonempty: bool = False) -> None:
    if type(value) is not tuple or len(value) > MAX_AUTHORITY_ITEMS or (nonempty and not value):
        raise TypeError(code)
    if any(type(x) is not typ for x in value):
        raise TypeError(code)
    for x in value:
        if hasattr(typ, '__post_init__'):
            typ.__post_init__(x)
    if len(set(value)) != len(value):
        raise ValueError('DUPLICATE_' + code)


@dataclass(frozen=True, slots=True)
class PrincipalRef:
    project: ProjectId
    identifier: str

    def __post_init__(self) -> None:
        if type(self.project) is not ProjectId:
            raise TypeError('PRINCIPAL_PROJECT_REQUIRED')
        text(self.identifier, 'PRINCIPAL_ID_REQUIRED')


@dataclass(frozen=True, slots=True)
class ApprovalRef:
    project: ProjectId
    identifier: str
    revision: RevisionId

    def __post_init__(self) -> None:
        if type(self.project) is not ProjectId or type(self.revision) is not RevisionId:
            raise TypeError('APPROVAL_IDENTITY_REQUIRED')
        text(self.identifier, 'APPROVAL_ID_REQUIRED')


class ActionKind(str, Enum):
    RATIFY = 'ratify'
    ADOPT = 'adopt'
    SUPERSEDE = 'supersede'
    AMEND = 'amend'
    IMPORT = 'import'
    EXCLUDE_SOURCE = 'exclude_source'


@dataclass(frozen=True, slots=True)
class NormativeAction:
    kind: ActionKind
    target: EntityRef
    scope_ref: EntityRef

    def __post_init__(self) -> None:
        if type(self.kind) is not ActionKind or type(self.target) is not EntityRef:
            raise TypeError('NORMATIVE_ACTION_REQUIRED')
        ref(self.scope_ref, EntityKind.SCOPE, 'ACTION_SCOPE_REQUIRED')
        if self.target.project != self.scope_ref.project:
            raise ValueError('ACTION_PROJECT_MISMATCH')


@dataclass(frozen=True, slots=True)
class AuthorityGrant:
    principal: PrincipalRef
    actions: frozenset[ActionKind]
    scope_refs: frozenset[EntityRef]
    targets: frozenset[EntityRef]

    def __post_init__(self) -> None:
        if type(self.principal) is not PrincipalRef:
            raise TypeError('PRINCIPAL_REQUIRED')
        PrincipalRef.__post_init__(self.principal)
        for seq, typ in ((self.actions, ActionKind), (self.scope_refs, EntityRef), (self.targets, EntityRef)):
            if type(seq) is not frozenset or not seq or len(seq) > MAX_AUTHORITY_ITEMS or any(type(x) is not typ for x in seq):
                raise TypeError('EXACT_AUTHORITY_GRANT_REQUIRED')
        if any(s.kind is not EntityKind.SCOPE for s in self.scope_refs):
            raise TypeError('GRANT_SCOPE_KIND')
        if any(r.project != self.principal.project for r in self.scope_refs | self.targets):
            raise ValueError('GRANT_PROJECT_MISMATCH')


@dataclass(frozen=True, slots=True, kw_only=True)
class DecisionRevision(RecordRevision):
    KIND: ClassVar[EntityKind] = EntityKind.DECISION
    statement: str
    actor: PrincipalRef
    policy_ref: EntityRef
    action: NormativeAction
    approval_refs: tuple[ApprovalRef, ...] = ()
    affected_contracts: tuple[EntityRef, ...] = ()
    rationale: str = ''
    alternatives: tuple[str, ...] = ()
    supersedes: tuple[EntityRef, ...] = ()

    def __post_init__(self) -> None:
        RecordRevision.__post_init__(self)
        text(self.statement, 'DECISION_STATEMENT_REQUIRED')
        text(self.rationale, 'DECISION_RATIONALE_REQUIRED')
        if type(self.actor) is not PrincipalRef or self.actor.project != self.identity.project:
            raise ValueError('DECISION_ACTOR_PROJECT')
        PrincipalRef.__post_init__(self.actor)
        ref(self.policy_ref, (EntityKind.CONSTITUTION, EntityKind.SOURCE_POLICY), 'DECISION_POLICY_REQUIRED')
        if type(self.action) is not NormativeAction:
            raise TypeError('NORMATIVE_ACTION_REQUIRED')
        NormativeAction.__post_init__(self.action)
        exact_tuple(self.approval_refs, ApprovalRef, 'APPROVAL_REFS')
        exact_tuple(self.affected_contracts, EntityRef, 'AFFECTED_CONTRACTS', nonempty=True)
        exact_tuple(self.supersedes, EntityRef, 'SUPERSESSION_REFS')
        texts(self.alternatives, 'INVALID_ALTERNATIVES')
        if (self.policy_ref.project != self.identity.project or self.action.scope_ref != self.scope_ref
                or self.action.target not in self.affected_contracts
                or any(x.project != self.identity.project for x in self.affected_contracts + self.supersedes)
                or any(x.project != self.identity.project for x in self.approval_refs)):
            raise ValueError('DECISION_SCOPE_OR_PROJECT_MISMATCH')
        if self.supersedes and (self.action.kind is not ActionKind.SUPERSEDE
                                or self.action.target in self.supersedes):
            raise ValueError('INVALID_SUPERSESSION')

    def references(self) -> tuple[ReferenceUse, ...]:
        return (RecordRevision.references(self)
                + (ReferenceUse('$.policy_ref', self.policy_ref, self.policy_ref.kind),)
                + uses('$.affected_contracts', self.affected_contracts)
                + uses('$.supersedes', self.supersedes))


@dataclass(frozen=True, slots=True)
class ApprovalRecord:
    reference: ApprovalRef
    decision: DecisionRevision
    principal: PrincipalRef
    context: ScopeContext

    def __post_init__(self) -> None:
        if (type(self.reference) is not ApprovalRef or type(self.decision) is not DecisionRevision
                or type(self.principal) is not PrincipalRef or type(self.context) is not ScopeContext):
            raise TypeError('TYPED_APPROVAL_REQUIRED')
        ApprovalRef.__post_init__(self.reference)
        DecisionRevision.__post_init__(self.decision)
        PrincipalRef.__post_init__(self.principal)
        ScopeContext.__post_init__(self.context)
        if (self.reference not in self.decision.approval_refs
                or self.context.project_id != self.decision.identity.project
                or self.reference.project != self.context.project_id
                or self.principal.project != self.context.project_id
                or self.decision.policy_ref != self.context.verification_policy_ref):
            raise ValueError('APPROVAL_CONTEXT_MISMATCH')
        if self.decision.declared_status is not DecisionStatus.APPROVED:
            raise ValueError('APPROVAL_REQUIRES_APPROVED_CANDIDATE')


@dataclass(frozen=True, slots=True)
class ApprovalPolicyRequirement:
    action: ActionKind
    scopes: frozenset[EntityRef]
    minimum: int = 1
    independent_author: bool = False

    def __post_init__(self):
        if type(self.action) is not ActionKind or type(self.scopes) is not frozenset or not self.scopes:
            raise TypeError('APPROVAL_REQUIREMENT_REQUIRED')
        if any(type(x) is not EntityRef or x.kind is not EntityKind.SCOPE for x in self.scopes):
            raise TypeError('APPROVAL_SCOPE_REQUIRED')
        if type(self.minimum) is not int or not 1 <= self.minimum <= MAX_AUTHORITY_ITEMS or type(self.independent_author) is not bool:
            raise ValueError('INVALID_APPROVAL_REQUIREMENT')


@dataclass(frozen=True, slots=True)
class AuthorityContext:
    context: ScopeContext
    principals: frozenset[PrincipalRef]
    grants: tuple[AuthorityGrant, ...] = ()
    approvals: tuple[ApprovalRecord, ...] = ()
    denied_actions: frozenset[tuple[PrincipalRef, NormativeAction]] = frozenset()
    requirements: tuple[ApprovalPolicyRequirement, ...] = ()
    normative_records: tuple[RecordRevision, ...] = ()
    assertion_pins: tuple[Assertion,...] = ()

    def __post_init__(self) -> None:
        if type(self.context) is not ScopeContext:
            raise TypeError('AUTHORITY_CONTEXT_REQUIRED')
        ScopeContext.__post_init__(self.context)
        if type(self.principals) is not frozenset or len(self.principals) > MAX_AUTHORITY_ITEMS:
            raise TypeError('TRUSTED_PRINCIPALS_REQUIRED')
        if any(type(p) is not PrincipalRef or p.project != self.context.project_id for p in self.principals):
            raise ValueError('PRINCIPAL_PROJECT_MISMATCH')
        exact_tuple(self.grants, AuthorityGrant, 'AUTHORITY_GRANTS')
        exact_tuple(self.approvals, ApprovalRecord, 'AUTHORITY_APPROVALS')
        if any(g.principal not in self.principals for g in self.grants):
            raise ValueError('UNTRUSTED_PRINCIPAL')
        if any(a.context != self.context or a.principal not in self.principals for a in self.approvals):
            raise ValueError('APPROVAL_CONTEXT_MISMATCH')
        exact_tuple(self.assertion_pins, Assertion, 'PINNED_ASSERTIONS')
        if any(a.identity.project != self.context.project_id or a.domain is not AssertionDomain.NORMATIVE for a in self.assertion_pins):
            raise ValueError('NORMATIVE_ASSERTION_CONTEXT_MISMATCH')
        if len({a.identity for a in self.assertion_pins}) != len(self.assertion_pins):
            raise ValueError('DUPLICATE_ASSERTION_PIN')
        exact_tuple(self.requirements, ApprovalPolicyRequirement, 'TRUSTED_APPROVAL_REQUIREMENTS')
        if any(s.project != self.context.project_id for r in self.requirements for s in r.scopes):
            raise ValueError('TRUSTED_APPROVAL_POLICY_PROJECT')
        if type(self.normative_records) is not tuple or len(self.normative_records) > MAX_AUTHORITY_ITEMS:
            raise TypeError('PINNED_NORMATIVE_RECORDS_REQUIRED')
        if any(not isinstance(r, RecordRevision) or r.identity.project != self.context.project_id for r in self.normative_records):
            raise TypeError('PINNED_NORMATIVE_RECORDS_REQUIRED')
        if len({r.identity for r in self.normative_records}) != len(self.normative_records):
            raise ValueError('DUPLICATE_NORMATIVE_BODY')
        if len({a.reference for a in self.approvals}) != len(self.approvals):
            raise ValueError('DUPLICATE_APPROVAL_ID')
        if type(self.denied_actions) is not frozenset or len(self.denied_actions) > MAX_AUTHORITY_ITEMS:
            raise TypeError('INVALID_AUTHORITY_DENIALS')
        for item in self.denied_actions:
            if (type(item) is not tuple or len(item) != 2 or type(item[0]) is not PrincipalRef
                    or type(item[1]) is not NormativeAction or item[0] not in self.principals):
                raise TypeError('INVALID_AUTHORITY_DENIALS')
            NormativeAction.__post_init__(item[1])
            if item[1].target.project != self.context.project_id:
                raise ValueError('DENIAL_PROJECT_MISMATCH')


class AuthorityVerdict(str, Enum):
    AUTHORIZED = 'AUTHORIZED'
    REQUIRES_APPROVAL = 'REQUIRES_APPROVAL'
    DENIED = 'DENIED'
    UNKNOWN = 'UNKNOWN'


@dataclass(frozen=True, slots=True)
class AuthorityEvaluation:
    verdict: AuthorityVerdict
    reasons: tuple[str, ...]
    policy_ref: EntityRef | None
    authenticated_by_this_function: bool = False


def evaluate_authority(actor: object, action: object, context: object) -> AuthorityEvaluation:
    if type(context) is not AuthorityContext:
        return AuthorityEvaluation(AuthorityVerdict.UNKNOWN, ('MISSING_AUTHORITY_CONTEXT',), None)
    try:
        AuthorityContext.__post_init__(context)
        if type(actor) is not PrincipalRef or type(action) is not NormativeAction:
            raise TypeError('INVALID_AUTHORITY_QUERY')
        PrincipalRef.__post_init__(actor); NormativeAction.__post_init__(action)
    except (TypeError, ValueError, AttributeError) as exc:
        return AuthorityEvaluation(AuthorityVerdict.UNKNOWN, (str(exc),), None)
    policy = context.context.verification_policy_ref
    if actor not in context.principals or action.target.project != context.context.project_id:
        return AuthorityEvaluation(AuthorityVerdict.DENIED, ('UNTRUSTED_PRINCIPAL_OR_PROJECT',), policy)
    if (actor, action) in context.denied_actions:
        return AuthorityEvaluation(AuthorityVerdict.DENIED, ('EXPLICIT_AUTHORITY_DENIAL',), policy)
    allowed = any(g.principal == actor and action.kind in g.actions
                  and action.scope_ref in g.scope_refs and action.target in g.targets for g in context.grants)
    verdict = AuthorityVerdict.AUTHORIZED if allowed else AuthorityVerdict.REQUIRES_APPROVAL
    return AuthorityEvaluation(verdict, ('EXACT_SCOPED_GRANT' if allowed else 'REQUIRES_APPROVAL',), policy)


@dataclass(frozen=True, slots=True)
class DecisionValidation:
    decision: EntityRef
    declared_status: DecisionStatus
    authorized: bool
    approvals: tuple[ApprovalRef, ...]
    policy_ref: EntityRef
    authenticated_by_this_function: bool = False


def validate_decision(decision: object, context: object, *, minimum_approvals: int = 1,
                      independent_author: bool = False) -> Result[DecisionValidation]:
    try:
        if type(decision) is not DecisionRevision:
            raise TypeError('DECISION_REQUIRED')
        DecisionRevision.__post_init__(decision)
        if type(minimum_approvals) is not int or not 1 <= minimum_approvals <= MAX_AUTHORITY_ITEMS or type(independent_author) is not bool:
            raise ValueError('INVALID_APPROVAL_POLICY')
        if decision.declared_status is not DecisionStatus.APPROVED:
            return Result(DecisionValidation(decision.identity, decision.declared_status, False, (), decision.policy_ref))
        if type(context) is not AuthorityContext:
            raise ValueError('UNTRUSTED_RATIFICATION')
        AuthorityContext.__post_init__(context)
        if (context.context.project_id != decision.identity.project
                or context.context.verification_policy_ref != decision.policy_ref):
            raise ValueError('AUTHORITY_POLICY_OR_PROJECT_MISMATCH')
        requirements = [r for r in context.requirements
            if r.action is decision.action.kind and decision.scope_ref in r.scopes]
        if not requirements:
            raise ValueError('UNKNOWN_AUTHORITY_RULE')
        minimum_approvals = max(minimum_approvals, *(r.minimum for r in requirements))
        independent_author = independent_author or any(r.independent_author for r in requirements)
        accepted = tuple(a for a in context.approvals
            if a.decision == decision and a.reference in decision.approval_refs
            and (not independent_author or a.principal != decision.actor)
            and evaluate_authority(a.principal, decision.action, context).verdict is AuthorityVerdict.AUTHORIZED)
        if len({a.principal for a in accepted}) < minimum_approvals:
            raise ValueError('MISSING_APPROVAL')
        return Result(DecisionValidation(decision.identity, decision.declared_status, True,
            tuple(sorted((a.reference for a in accepted), key=lambda x:(x.identifier,x.revision.value))), decision.policy_ref))
    except (TypeError, ValueError, AttributeError) as exc:
        return Result(diagnostics=(diagnostic(str(exc), '$.decision', 'decision is not authorized by the exact supplied policy'),))
