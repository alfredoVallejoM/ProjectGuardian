"""G00-11: typed conflicts, scoped partial precedence and local impact.

No timestamps or ordering heuristics confer precedence. Normative and observed
assertions inhabit distinct authority domains. A missing overlap proof is kept
as a potential conflict, not silently treated as disjointness.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from guardian.domain.identity import EntityKind, EntityRef, RevisionId
from guardian.domain.authority import (AuthorityContext, DecisionRevision, ActionKind,
    validate_decision, exact_tuple, diagnostic)
from guardian.domain.record_base import ref, refs, text
from guardian.domain.outcomes import Diagnostic
from guardian.domain.references import RecordSnapshot, resolve_entity
from guardian.domain.scope import (SupportProfile, FactSet, StepBudget, ScopeRevision,
    ApplicabilityResult, evaluate_scope, and_evidence)
from guardian.domain.evidence_logic import YES, NO


def ref_key(value: EntityRef):
    return value.project.value, value.kind.value, value.entity.value, value.revision.value


from guardian.domain.claims import Assertion, AssertionDomain


@dataclass(frozen=True, slots=True)
class ConflictPolicies:
    snapshot: RecordSnapshot
    facts: FactSet
    authority: AuthorityContext
    budget: StepBudget = StepBudget()
    max_pairs: int = 10000

    def __post_init__(self):
        if (type(self.snapshot) is not RecordSnapshot or type(self.facts) is not FactSet
                or type(self.authority) is not AuthorityContext or type(self.budget) is not StepBudget):
            raise TypeError('CONFLICT_CONTEXT_REQUIRED')
        if self.authority.context != self.facts.context or self.snapshot.project_id != self.facts.context.project_id or self.snapshot.revision != self.facts.context.project_revision:
            raise ValueError('CONFLICT_CONTEXT_MISMATCH')
        if type(self.max_pairs) is not int or not 0 <= self.max_pairs <= 100000:
            raise ValueError('INVALID_CONFLICT_BUDGET')


class PrecedenceStatus(str, Enum):
    LEFT_PRECEDES = 'LEFT_PRECEDES'
    RIGHT_PRECEDES = 'RIGHT_PRECEDES'
    COEXISTS = 'COEXISTS'
    CONFLICT = 'CONFLICT'
    UNKNOWN = 'UNKNOWN'


@dataclass(frozen=True, slots=True)
class PrecedenceResolution:
    status: PrecedenceStatus
    decisions: tuple[EntityRef, ...]
    reasons: tuple[str, ...]


def resolve_precedence(assertion_a: Assertion, assertion_b: Assertion,
                       approved_supersession: tuple[DecisionRevision, ...],
                       context: AuthorityContext) -> PrecedenceResolution:
    """Only fully validated approvals passed by the contextual caller can win."""
    if type(assertion_a) is not Assertion or type(assertion_b) is not Assertion or type(context) is not AuthorityContext:
        return PrecedenceResolution(PrecedenceStatus.UNKNOWN,(),('INVALID_PRECEDENCE_INPUT',))
    a,b=assertion_a,assertion_b
    if (a.identity.project != b.identity.project or a.subject != b.subject
            or a.property_name != b.property_name or a.domain is not b.domain
            or (type(a.value) is type(b.value) and a.value == b.value)):
        return PrecedenceResolution(PrecedenceStatus.COEXISTS,(),('DISTINCT_DOMAIN_SUBJECT_OR_COMPATIBLE',))
    if a.domain is AssertionDomain.OBSERVED:
        status = PrecedenceStatus.COEXISTS if a.observation_revision != b.observation_revision else PrecedenceStatus.CONFLICT
        return PrecedenceResolution(status,(),('OBSERVATIONS_NEVER_REWRITE_NORMS',))
    if a.domain is not AssertionDomain.NORMATIVE:
        return PrecedenceResolution(PrecedenceStatus.COEXISTS,(),('NONBINDING_ASSERTIONS',))
    if type(approved_supersession) is not tuple or any(type(d) is not DecisionRevision for d in approved_supersession):
        return PrecedenceResolution(PrecedenceStatus.UNKNOWN,(),('INVALID_SUPERSESSION_CONTEXT',))
    if a not in context.assertion_pins or b not in context.assertion_pins:
        return PrecedenceResolution(PrecedenceStatus.UNKNOWN,(),('UNPINNED_NORMATIVE_ASSERTION',))
    edges={}; ids=[]
    for decision in approved_supersession:
        valid=validate_decision(decision,context)
        if (not valid.ok or not valid.value.authorized or decision.action.kind is not ActionKind.SUPERSEDE
                or decision.action.scope_ref not in (a.scope_ref,b.scope_ref)):
            continue
        for old in decision.supersedes:
            edges.setdefault(old,set()).add(decision.action.target)
        ids.append(decision.identity)
    def reaches(start,target):
        visited=set();pending=[start]
        while pending:
            node=pending.pop()
            if node in visited:continue
            visited.add(node)
            for successor in edges.get(node,()):
                if successor == target:return True
                pending.append(successor)
        return False
    ab,ba=reaches(a.identity,b.identity),reaches(b.identity,a.identity)
    if ab and ba:return PrecedenceResolution(PrecedenceStatus.CONFLICT,tuple(sorted(set(ids),key=ref_key)),('PRECEDENCE_CYCLE',))
    if ab:return PrecedenceResolution(PrecedenceStatus.RIGHT_PRECEDES,tuple(sorted(set(ids),key=ref_key)),('APPROVED_SCOPED_SUPERSESSION',))
    if ba:return PrecedenceResolution(PrecedenceStatus.LEFT_PRECEDES,tuple(sorted(set(ids),key=ref_key)),('APPROVED_SCOPED_SUPERSESSION',))
    return PrecedenceResolution(PrecedenceStatus.CONFLICT,(),('MISSING_APPROVED_SUPERSESSION',))


@dataclass(frozen=True, slots=True)
class ConflictRecord:
    left: Assertion
    right: Assertion
    intersection: ApplicabilityResult | None
    confirmed: bool
    reasons: tuple[str, ...]

    def __post_init__(self):
        if type(self.left) is not Assertion or type(self.right) is not Assertion or type(self.confirmed) is not bool:
            raise TypeError('INVALID_CONFLICT_RECORD')
        if self.left.identity.project != self.right.identity.project:
            raise ValueError('CONFLICT_SCOPE_LEAK')
        if self.intersection is not None and type(self.intersection) is not ApplicabilityResult:
            raise TypeError('INVALID_CONFLICT_INTERSECTION')
        if self.confirmed and (self.intersection is None or self.intersection.value != YES):
            raise ValueError('UNPROVEN_SCOPE_INTERSECTION')
        if not self.reasons:
            raise ValueError('CONFLICT_REASON_REQUIRED')

    @property
    def witnesses(self):
        return (self.left.identity,self.right.identity) + self.left.source_refs + self.right.source_refs


@dataclass(frozen=True, slots=True)
class ConflictReport:
    conflicts: tuple[ConflictRecord, ...]
    resolutions: tuple[PrecedenceResolution, ...]
    diagnostics: tuple[Diagnostic, ...]
    nonbinding: tuple[EntityRef, ...]
    examined_pairs: int
    complete: bool


def detect_conflicts(assertions: tuple[Assertion, ...], profile: SupportProfile,
                     policies: ConflictPolicies) -> ConflictReport:
    conflicts=[];resolutions=[];errors=[];nonbinding=[];pairs=0
    def report(complete=True):
        return ConflictReport(tuple(conflicts),tuple(resolutions),tuple(sorted(set(errors),key=lambda d:(d.path,d.code,d.reason))),
                              tuple(sorted(set(nonbinding),key=ref_key)),pairs,complete)
    try:
        exact_tuple(assertions,Assertion,'ASSERTIONS')
        if len({a.identity for a in assertions}) != len(assertions):
            raise ValueError('DUPLICATE_ASSERTION_ID')
        if type(profile) is not SupportProfile or type(policies) is not ConflictPolicies:
            raise TypeError('CONFLICT_CONTEXT_REQUIRED')
        ConflictPolicies.__post_init__(policies)
        if profile.context != policies.facts.context:
            raise ValueError('CONFLICT_CONTEXT_MISMATCH')
    except (TypeError,ValueError,AttributeError) as exc:
        errors.append(diagnostic(str(exc),'$.assertions','invalid conflict input'))
        return report(False)
    approved=[]
    for item in policies.authority.approvals:
        d=item.decision
        result=validate_decision(d,policies.authority)
        if result.ok and result.value.authorized and d not in approved:approved.append(d)
    scope_cache={}
    def applicability(scope_ref):
        if scope_ref in scope_cache:return scope_cache[scope_ref]
        found=resolve_entity(scope_ref,policies.snapshot,EntityKind.SCOPE)
        if not found.ok:
            errors.extend(found.diagnostics);scope_cache[scope_ref]=None;return None
        body=found.value.record
        if body not in policies.authority.normative_records:
            errors.append(diagnostic('NORMATIVE_BODY_MISMATCH','$.scope','conflict scope differs from pinned normative body'))
            scope_cache[scope_ref]=None;return None
        if type(body) is not ScopeRevision or body.registry != profile.registry:
            errors.append(diagnostic('CONFLICT_SCOPE_REGISTRY_MISMATCH','$.scope','scope version is not the profile registry'))
            scope_cache[scope_ref]=None;return None
        evaluation=evaluate_scope(body.expression,profile,policies.facts,policies.budget)
        if not evaluation.ok:errors.extend(evaluation.diagnostics)
        scope_cache[scope_ref]=evaluation.result
        return evaluation.result
    effective=[]
    for a in sorted(assertions,key=lambda x:ref_key(x.identity)):
        if a.identity.project != profile.project_id:
            errors.append(diagnostic('CONFLICT_SCOPE_LEAK','$.assertions','foreign assertion was not imported'))
            continue
        if any(not policies.snapshot.contains_source(s) for s in a.source_refs):
            errors.append(diagnostic('UNKNOWN_SOURCE','$.assertions','assertion source not in pinned snapshot'));continue
        if a.domain in (AssertionDomain.PROPOSED,AssertionDomain.INFERENCE):
            nonbinding.append(a.identity);continue
        if a.domain is AssertionDomain.NORMATIVE and (a not in policies.authority.assertion_pins or not any(d.identity==a.authority_ref and a.identity in d.affected_contracts for d in approved)):
            nonbinding.append(a.identity)
            errors.append(diagnostic('UNTRUSTED_RATIFICATION','$.assertions','normative assertion has no approved exact decision'));continue
        effective.append(a)
    for i,a in enumerate(effective):
        for b in effective[i+1:]:
            if (a.subject != b.subject or a.property_name != b.property_name or a.domain is not b.domain
                    or (type(a.value) is type(b.value) and a.value==b.value)
                    or (a.domain is AssertionDomain.OBSERVED and a.observation_revision != b.observation_revision)):
                continue
            if pairs >= policies.max_pairs:
                errors.append(diagnostic('EVALUATION_RESOURCE_LIMITED','$.conflicts','pair budget exhausted'))
                return report(False)
            pairs+=1
            left,right=applicability(a.scope_ref),applicability(b.scope_ref)
            intersection=and_evidence(left,right) if left is not None and right is not None else None
            if intersection is not None and intersection.value==NO and not intersection.conflicts:
                continue
            scoped_decisions=[]
            for d in approved:
                value=applicability(d.scope_ref)
                if value is not None and value.value==YES and not value.conflicts:scoped_decisions.append(d)
            precedence=resolve_precedence(a,b,tuple(scoped_decisions),policies.authority)
            if intersection is not None and intersection.value==YES and not intersection.conflicts and precedence.status in (
                    PrecedenceStatus.LEFT_PRECEDES,PrecedenceStatus.RIGHT_PRECEDES,PrecedenceStatus.COEXISTS):
                resolutions.append(precedence);continue
            confirmed=intersection is not None and intersection.value==YES and not intersection.conflicts
            reason='UNRESOLVED_NORMATIVE_CONFLICT' if confirmed else 'SCOPE_INTERSECTION_UNKNOWN_OR_CONFLICT'
            conflicts.append(ConflictRecord(a,b,intersection,confirmed,(reason,)+precedence.reasons))
    return report()


@dataclass(frozen=True, slots=True)
class DependencyView:
    project: object
    edges: tuple[tuple[EntityRef,EntityRef], ...]

    def __post_init__(self):
        from guardian.domain.identity import ProjectId
        if type(self.project) is not ProjectId or type(self.edges) is not tuple or len(self.edges)>10000:
            raise TypeError('LOCAL_DEPENDENCIES_REQUIRED')
        for pair in self.edges:
            if type(pair) is not tuple or len(pair)!=2 or any(type(x) is not EntityRef or x.project!=self.project for x in pair):
                raise ValueError('CONFLICT_SCOPE_LEAK')
        if len(set(self.edges))!=len(self.edges):raise ValueError('DUPLICATE_DEPENDENCY')


@dataclass(frozen=True, slots=True)
class LocalizedConflict:
    conflict: ConflictRecord
    blocked: tuple[EntityRef, ...]


def localize_conflicts(conflicts: tuple[ConflictRecord, ...], dependencies: DependencyView) -> tuple[LocalizedConflict, ...]:
    exact_tuple(conflicts,ConflictRecord,'CONFLICTS')
    if type(dependencies) is not DependencyView:raise TypeError('LOCAL_DEPENDENCIES_REQUIRED')
    DependencyView.__post_init__(dependencies)
    adjacency={}
    for requirement,dependent in dependencies.edges:adjacency.setdefault(requirement,set()).add(dependent)
    out=[]
    for conflict in conflicts:
        if conflict.left.identity.project!=dependencies.project:raise ValueError('CONFLICT_SCOPE_LEAK')
        pending=[conflict.left.identity,conflict.right.identity];seen=set()
        while pending:
            node=pending.pop()
            if node in seen:continue
            seen.add(node);pending.extend(adjacency.get(node,()))
        out.append(LocalizedConflict(conflict,tuple(sorted(seen,key=ref_key))))
    return tuple(sorted(out,key=lambda x:(ref_key(x.conflict.left.identity),ref_key(x.conflict.right.identity))))
