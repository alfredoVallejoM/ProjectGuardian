"""G00-10 pure constitutional evaluator with a conserved rule denominator.

PASS is conditional, structural evaluation of the explicit snapshot. It is not
scientific certification, normative admission, authentication or publication.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from enum import Enum
from guardian.domain.identity import EntityKind, EntityRef
from guardian.domain.authority import (AuthorityContext, DecisionRevision, ActionKind,
    validate_decision, exact_tuple, diagnostic)
from guardian.domain.constitution import (ConstitutionRevision, RuleRevision,
    CONSTITUTION_FEATURES)
from guardian.domain.references import (RecordSnapshot, TrustedEntityImports,
    resolve_entity, validate_references)
from guardian.domain.scope import (SupportProfile, FactSet, StepBudget, ScopeRevision,
    ScopeEvaluation, EvaluationStatus, evaluate_scope)
from guardian.domain.evidence_logic import YES, NO, UNKNOWN, CONFLICT
from guardian.domain.outcomes import (Diagnostic, TypedStatus, SourceStatus,
    check_illegal_promotion)
from guardian.domain.project import ProjectDefinition
from guardian.domain.source import (SourceUniverseRevision, TrustedImportGrants,
    validate_source_universe, SourceCut)
from guardian.domain.architecture import ArchitectureRevision
from guardian.domain.foundation_records import ProjectRevision, SourcePolicyRevision, SourceUniverseRecord
from .authority_resolution import required_approvals
from .invariants import TrustedRuleEvaluatorRegistry, validate_rule_registry
from .precedence import (Assertion, AssertionDomain, ConflictPolicies, ConflictRecord,
    DependencyView, LocalizedConflict, detect_conflicts, localize_conflicts, ref_key)


@dataclass(frozen=True, slots=True)
class StatusPairObservation:
    source: TypedStatus
    target: TypedStatus
    witness: EntityRef

    def __post_init__(self):
        if type(self.source) is not TypedStatus or type(self.target) is not TypedStatus:
            raise TypeError('STATUS_PAIR_REQUIRED')
        TypedStatus.__post_init__(self.source); TypedStatus.__post_init__(self.target)
        if type(self.witness) is not EntityRef or self.witness.kind is not EntityKind.SOURCE:
            raise TypeError('FACT_SOURCE_REQUIRED')


@dataclass(frozen=True, slots=True)
class ArchitectureObservation:
    architecture: EntityRef
    dependencies: tuple[tuple[str,str], ...]
    complete: bool
    witness: EntityRef

    def __post_init__(self):
        if type(self.architecture) is not EntityRef or self.architecture.kind is not EntityKind.ARCHITECTURE:
            raise TypeError('ARCHITECTURE_REF_REQUIRED')
        if type(self.dependencies) is not tuple or type(self.complete) is not bool:
            raise TypeError('ARCHITECTURE_FACT_REQUIRED')
        if len(self.dependencies)>10000 or any(type(p) is not tuple or len(p)!=2 or any(type(v) is not str or not v for v in p) for p in self.dependencies):
            raise TypeError('DEPENDENCY_FACT_REQUIRED')
        if len(set(self.dependencies))!=len(self.dependencies):raise ValueError('DUPLICATE_OBSERVED_EDGE')
        if type(self.witness) is not EntityRef or self.witness.kind is not EntityKind.SOURCE:
            raise TypeError('FACT_SOURCE_REQUIRED')


@dataclass(frozen=True, slots=True)
class ReferenceSetObservation:
    before: frozenset[EntityRef]
    after: frozenset[EntityRef]
    witness: EntityRef

    def __post_init__(self):
        for seq in (self.before,self.after):
            if type(seq) is not frozenset or len(seq)>25000 or any(type(v) is not EntityRef for v in seq):
                raise TypeError('EXPLICIT_REFERENCE_SETS_REQUIRED')
        if type(self.witness) is not EntityRef or self.witness.kind is not EntityKind.SOURCE:
            raise TypeError('FACT_SOURCE_REQUIRED')


@dataclass(frozen=True, slots=True)
class ConstitutionFacts:
    scope: FactSet
    status_pairs: tuple[StatusPairObservation,...] = ()
    architectures: tuple[ArchitectureObservation,...] = ()
    reference_sets: tuple[ReferenceSetObservation,...] = ()
    assertions: tuple[Assertion,...] = ()
    assertions_complete: bool = False

    def __post_init__(self):
        if type(self.scope) is not FactSet or type(self.assertions_complete) is not bool:
            raise TypeError('CONSTITUTION_FACTS_REQUIRED')
        FactSet.__post_init__(self.scope)
        for seq,typ in ((self.status_pairs,StatusPairObservation),(self.architectures,ArchitectureObservation),
                        (self.reference_sets,ReferenceSetObservation),(self.assertions,Assertion)):
            exact_tuple(seq,typ,'CONSTITUTION_FACTS')
        refs=[x.witness for x in self.status_pairs+self.architectures+self.reference_sets]
        refs.extend(s for a in self.assertions for s in a.source_refs)
        if any(r not in self.scope.source_refs for r in refs):
            raise ValueError('FACT_SOURCE_OUTSIDE_CONTEXT')
        if any(a.architecture.project!=self.scope.context.project_id for a in self.architectures):
            raise ValueError('FACT_PROJECT_MISMATCH')
        if any(r.project!=self.scope.context.project_id for item in self.reference_sets for r in item.before|item.after):
            raise ValueError('FACT_PROJECT_MISMATCH')


@dataclass(frozen=True, slots=True)
class EvaluationBudget:
    max_rules: int = 4096
    max_steps: int = 1000000
    scope: StepBudget = StepBudget()
    max_conflict_pairs: int = 10000

    def __post_init__(self):
        for v,limit in ((self.max_rules,25000),(self.max_steps,10000000),(self.max_conflict_pairs,100000)):
            if type(v) is not int or not 0<=v<=limit:raise ValueError('INVALID_EVALUATION_BUDGET')
        if type(self.scope) is not StepBudget:raise TypeError('SCOPE_BUDGET_REQUIRED')
        StepBudget.__post_init__(self.scope)


@dataclass(frozen=True, slots=True)
class EvaluationRequest:
    constitution: ConstitutionRevision
    view: RecordSnapshot
    project: ProjectDefinition
    universe: SourceUniverseRevision
    facts: ConstitutionFacts
    profile: SupportProfile
    authority: AuthorityContext
    candidate_ref: EntityRef
    budget: EvaluationBudget = EvaluationBudget()
    imports: TrustedEntityImports | None = None
    source_imports: TrustedImportGrants | None = None
    dependencies: DependencyView | None = None


class RuleVerdict(str,Enum):
    PASS='PASS'
    FAIL='FAIL'
    UNKNOWN='UNKNOWN'
    CONFLICT='CONFLICT'
    NOT_APPLICABLE='NOT_APPLICABLE'
    SUPERSEDED='SUPERSEDED'
    RESOURCE_LIMITED='RESOURCE_LIMITED'
    INVALID_INPUT='INVALID_INPUT'


@dataclass(frozen=True, slots=True)
class RuleEvaluation:
    rule_ref: EntityRef
    verdict: RuleVerdict
    applicability: ScopeEvaluation | None
    positive_witnesses: tuple[EntityRef,...]
    negative_witnesses: tuple[EntityRef,...]
    diagnostics: tuple[Diagnostic,...]
    conflicts: tuple[ConflictRecord,...] = ()
    evaluator_id: str | None = None
    examined: bool = True
    requirement_evaluation: ScopeEvaluation | None = None
    supersession_decisions: tuple[EntityRef, ...] = ()

    def __post_init__(self):
        if type(self.rule_ref) is not EntityRef or self.rule_ref.kind is not EntityKind.RULE or type(self.verdict) is not RuleVerdict or type(self.examined) is not bool:
            raise TypeError('RULE_EVALUATION_REQUIRED')
        for seq,typ in ((self.positive_witnesses,EntityRef),(self.negative_witnesses,EntityRef),
                        (self.diagnostics,Diagnostic),(self.conflicts,ConflictRecord)):
            if type(seq) is not tuple or any(type(x) is not typ for x in seq):raise TypeError('RULE_REPORT_NOT_IMMUTABLE')
        for evaluation in (self.applicability, self.requirement_evaluation):
            if evaluation is not None:
                if type(evaluation) is not ScopeEvaluation:raise TypeError('SCOPE_EVALUATION_REQUIRED')
                ScopeEvaluation.__post_init__(evaluation)
        if type(self.supersession_decisions) is not tuple or any(type(x) is not EntityRef or x.kind is not EntityKind.DECISION for x in self.supersession_decisions):
            raise TypeError('SUPERSESSION_EVIDENCE_REQUIRED')
        if self.verdict is RuleVerdict.SUPERSEDED and (not self.examined or not self.positive_witnesses or not self.supersession_decisions):
            raise ValueError('UNWITNESSED_SUPERSESSION')
        if self.verdict is RuleVerdict.PASS and (not self.examined or not self.positive_witnesses or self.conflicts):
            raise ValueError('UNSUPPORTED_RULE_PASS')
        if self.verdict is RuleVerdict.NOT_APPLICABLE and (self.applicability is None or not self.applicability.ok
                or self.applicability.result.value!=NO or self.applicability.result.conflicts):
            raise ValueError('UNWITNESSED_EXCLUSION')
        if self.verdict is RuleVerdict.FAIL and not self.negative_witnesses:raise ValueError('UNWITNESSED_FAILURE')


@dataclass(frozen=True, slots=True)
class ConstitutionEvaluationReport:
    constitution_ref: EntityRef
    policy_ref: EntityRef
    candidate_ref: EntityRef
    rule_results: tuple[RuleEvaluation,...]
    expected_rule_refs: tuple[EntityRef,...]
    aggregate_verdict: RuleVerdict
    diagnostics: tuple[Diagnostic,...]
    localized_conflicts: tuple[LocalizedConflict,...]
    steps: int

    def __post_init__(self):
        if (type(self.constitution_ref) is not EntityRef or self.constitution_ref.kind is not EntityKind.CONSTITUTION
                or type(self.policy_ref) is not EntityRef or type(self.candidate_ref) is not EntityRef
                or self.candidate_ref.kind is not EntityKind.IMPLEMENTATION
                or type(self.aggregate_verdict) is not RuleVerdict
                or type(self.steps) is not int or self.steps < 0):
            raise TypeError('CONSTITUTION_REPORT_REQUIRED')
        if any(r.project != self.constitution_ref.project for r in (self.policy_ref, self.candidate_ref)):
            raise ValueError('REPORT_PROJECT_MISMATCH')
        for seq, typ in ((self.rule_results, RuleEvaluation), (self.diagnostics, Diagnostic),
                         (self.expected_rule_refs, EntityRef), (self.localized_conflicts, LocalizedConflict)):
            if type(seq) is not tuple or any(type(x) is not typ for x in seq):
                raise TypeError('CONSTITUTION_REPORT_NOT_IMMUTABLE')
        for row in self.rule_results:RuleEvaluation.__post_init__(row)
        if len(set(self.expected_rule_refs)) != len(self.expected_rule_refs) or any(r.kind is not EntityKind.RULE for r in self.expected_rule_refs):
            raise ValueError('INVALID_RULE_DENOMINATOR')
        if tuple(r.rule_ref for r in self.rule_results)!=self.expected_rule_refs:
            raise ValueError('RULE_SET_INCOMPLETE')
        if self.aggregate_verdict is RuleVerdict.PASS and (not self.expected_rule_refs
                or self.diagnostics or self.localized_conflicts or any(not r.examined or r.verdict not in
                (RuleVerdict.PASS,RuleVerdict.NOT_APPLICABLE,RuleVerdict.SUPERSEDED) for r in self.rule_results)):
            raise ValueError('PREMATURE_CONSTITUTION_PASS')

    @property
    def examined_rule_ids(self):
        return tuple(r.rule_ref for r in self.rule_results if r.examined)

    @property
    def unexamined_rule_ids(self):
        return tuple(r.rule_ref for r in self.rule_results if not r.examined)

    @property
    def verdicts_present(self):
        return tuple(sorted({r.verdict.value for r in self.rule_results}))

    @property
    def normatively_admitted(self):
        return False

    @property
    def coverage_scope(self):
        return 'EXPLICIT_IN_MEMORY_CONSTITUTION_ONLY'


def _diagnostics(items):
    return tuple(sorted(set(items),key=lambda d:(d.path,d.code,d.reason)))


def _row(target, verdict, code, reason, *, applicability=None, positive=(),negative=(),conflicts=(),examined=True,evaluator=None):
    ds=() if code is None else (diagnostic(code,f'$.rules[{target.entity.value}@{target.revision.value}]',reason),)
    return RuleEvaluation(target,verdict,applicability,tuple(sorted(set(positive),key=ref_key)),
                          tuple(sorted(set(negative),key=ref_key)),ds,tuple(conflicts),evaluator,examined)


def collect_constitution_report(expected: tuple[EntityRef,...], results: tuple[RuleEvaluation,...],
                                constitution_ref: EntityRef, policy_ref: EntityRef, candidate_ref: EntityRef,
                                *, diagnostics: tuple[Diagnostic,...]=(), localized_conflicts=(), steps: int=0) -> ConstitutionEvaluationReport:
    if type(expected) is not tuple or len(set(expected))!=len(expected) or any(type(x) is not EntityRef or x.kind is not EntityKind.RULE for x in expected):
        raise ValueError('INVALID_RULE_DENOMINATOR')
    if type(results) is not tuple or any(type(x) is not RuleEvaluation for x in results):raise TypeError('RULE_RESULTS_REQUIRED')
    expected=tuple(sorted(expected,key=ref_key));errors=list(diagnostics);table={}
    for result in results:
        RuleEvaluation.__post_init__(result)
        if result.rule_ref in table or result.rule_ref not in expected:
            errors.append(diagnostic('RULE_SET_INCOMPLETE','$.results','extra or duplicate rule result'))
        else:table[result.rule_ref]=result
    for target in expected:
        if target not in table:
            errors.append(diagnostic('RULE_SET_INCOMPLETE','$.results','missing rule retained as unexamined'))
            table[target]=_row(target,RuleVerdict.UNKNOWN,'RULE_SET_INCOMPLETE','rule not evaluated',examined=False)
    rows=tuple(table[x] for x in expected);verdicts={r.verdict for r in rows}
    if RuleVerdict.RESOURCE_LIMITED in verdicts:aggregate=RuleVerdict.RESOURCE_LIMITED
    elif errors or RuleVerdict.INVALID_INPUT in verdicts:aggregate=RuleVerdict.INVALID_INPUT
    elif RuleVerdict.CONFLICT in verdicts or localized_conflicts:aggregate=RuleVerdict.CONFLICT
    elif RuleVerdict.FAIL in verdicts:aggregate=RuleVerdict.FAIL
    elif not rows or RuleVerdict.UNKNOWN in verdicts or any(not r.examined for r in rows):aggregate=RuleVerdict.UNKNOWN
    else:aggregate=RuleVerdict.PASS
    return ConstitutionEvaluationReport(constitution_ref,policy_ref,candidate_ref,rows,expected,aggregate,
                                          _diagnostics(errors),tuple(localized_conflicts),steps)


def _scope(target,request,budget):
    found=resolve_entity(target,request.view,EntityKind.SCOPE,request.imports)
    if not found.ok:return None,found.diagnostics
    body=found.value.record
    pinned=next((r for r in request.authority.normative_records if r.identity==body.identity),None)
    if pinned != body:
        return None,(diagnostic('NORMATIVE_BODY_MISMATCH','$.scope','dependent scope body is not the externally fixed norm'),)
    if type(body) is not ScopeRevision or body.registry!=request.profile.registry:
        return None,(diagnostic('SCOPE_REGISTRY_MISMATCH','$.scope','exact registry required'),)
    result=evaluate_scope(body.expression,request.profile,request.facts.scope,budget)
    return result,() if result.ok else result.diagnostics


def _decision_authorized(target,request,meter=None):
    found=resolve_entity(target,request.view,EntityKind.DECISION,request.imports)
    if not found.ok:return False,found.diagnostics
    decision=found.value.record
    scope, errors = _metered_scope(decision.scope_ref, request, meter)
    if errors or scope.result.value != YES or scope.result.conflicts:
        return False, errors or (diagnostic('APPROVAL_SCOPE_NOT_ESTABLISHED','$.decision.scope','approval is not applicable to this profile'),)
    requirements=required_approvals(decision.action,request.profile,request.constitution)
    if not requirements.ok:return False,requirements.diagnostics
    validated=validate_decision(decision,request.authority,minimum_approvals=requirements.value.minimum,
                                independent_author=requirements.value.independent_author)
    if not validated.ok:return False,validated.diagnostics
    return validated.value.authorized,()



def _assertion_population(request):
    """Validate coverage of externally fixed norms, never a candidate boolean alone."""
    pinned = {a.identity: a for a in request.authority.assertion_pins}
    actual = {a.identity: a for a in request.facts.assertions if a.domain is AssertionDomain.NORMATIVE}
    if len(actual) != sum(a.domain is AssertionDomain.NORMATIVE for a in request.facts.assertions):
        return (diagnostic('DUPLICATE_ASSERTION', '$.facts.assertions', 'duplicate normative identity'),)
    if pinned.keys() - actual.keys():
        return (diagnostic('ASSERTION_SET_INCOMPLETE', '$.facts.assertions',
            'externally pinned assertions must not disappear from the examined population'),)
    if actual.keys() - pinned.keys() or any(actual[k] != a for k, a in pinned.items()):
        return (diagnostic('NORMATIVE_ASSERTION_BODY_MISMATCH', '$.facts.assertions',
            'supplied normative assertions differ from their external pins'),)
    return ()


def _validate_project_bodies(request, bound):
    """One exact source for duplicated project/policy/universe arguments."""
    universe = bound.get(request.universe.identity)
    if (type(universe) is not SourceUniverseRecord or universe.universe != request.universe
            or request.view._by_ref.get(universe.identity) != universe):
        raise ValueError('NORMATIVE_UNIVERSE_BODY_MISMATCH')
    policy = bound.get(request.project.source_policy_ref)
    if (type(policy) is not SourcePolicyRevision or policy.policy != request.project.source_policy
            or request.view._by_ref.get(policy.identity) != policy):
        raise ValueError('NORMATIVE_POLICY_BODY_MISMATCH')
    projects = [x for x in bound.values() if type(x) is ProjectRevision
                and x.identity.project == request.project.project_id
                and x.identity not in request.view.historical]
    if (len(projects) != 1 or projects[0].definition != request.project
            or request.view._by_ref.get(projects[0].identity) != projects[0]):
        raise ValueError('NORMATIVE_PROJECT_BODY_MISMATCH')


def _approved_exclusions(request, meter):
    """Derive a decision allowlist only after checking every exact exclusion use.

    The lower-level source validator accepts a set of trusted DecisionRefs. One
    valid use must never authorize another use of the same decision implicitly.
    All source/universe bodies have already been compared with the external pins.
    """
    allowed, errors = set(), []
    for exclusion in sorted(request.universe.excluded, key=lambda x: (ref_key(x.approval_ref), ref_key(x.cut))):
        found = resolve_entity(exclusion.approval_ref, request.view, EntityKind.DECISION, request.imports)
        if not found.ok:
            errors.extend(found.diagnostics)
            continue
        decision = found.value.record
        if (type(decision) is not DecisionRevision or decision.action.kind is not ActionKind.EXCLUDE_SOURCE
                or decision.action.target != request.universe.identity
                or exclusion.cut not in decision.affected_contracts
                or request.universe.identity not in decision.affected_contracts):
            errors.append(diagnostic('EXCLUSION_AUTHORIZATION_MISMATCH',
                '$.universe.excluded[' + exclusion.cut.entity.value + ']',
                'approval must explicitly exclude this pinned source from this universe'))
            continue
        authorized, issues = _decision_authorized(decision.identity, request, meter)
        if not authorized:
            errors.extend(issues or (diagnostic('EXCLUSION_AUTHORITY_UNVERIFIED', '$.universe.excluded',
                                               'exclusion approval is not effective in this profile'),))
        else:
            allowed.add(decision.identity)
    return frozenset(allowed) if not errors else frozenset(), _diagnostics(errors)


def _merge_rule_evaluations(rows, rule, applicability):
    """Aggregate one predicate's unordered observations without first-wins loss."""
    priority = (RuleVerdict.INVALID_INPUT, RuleVerdict.CONFLICT, RuleVerdict.FAIL, RuleVerdict.UNKNOWN, RuleVerdict.PASS)
    verdict = next(v for v in priority if any(r.verdict is v for r in rows))
    return RuleEvaluation(rule.identity, verdict, applicability,
        tuple(sorted({w for r in rows for w in r.positive_witnesses}, key=ref_key)),
        tuple(sorted({w for r in rows for w in r.negative_witnesses}, key=ref_key)),
        _diagnostics(d for r in rows for d in r.diagnostics),
        tuple(sorted({c for r in rows for c in r.conflicts}, key=lambda c: (ref_key(c.left.identity), ref_key(c.right.identity)))),
        rule.rule_kind)

def evaluate_registered_rule(rule: RuleRevision, request: EvaluationRequest,
                             registry: TrustedRuleEvaluatorRegistry, applicability: ScopeEvaluation,
                             conflicts: tuple[LocalizedConflict,...]=(), *, _meter=None) -> RuleEvaluation:
    """Dispatch only builtin semantics. The public evaluator prevalidates contexts."""
    if (type(rule) is not RuleRevision or type(request) is not EvaluationRequest
            or type(registry) is not TrustedRuleEvaluatorRegistry or type(applicability) is not ScopeEvaluation):
        raise TypeError('TYPED_RULE_EVALUATION_INPUT_REQUIRED')
    RuleRevision.__post_init__(rule); TrustedRuleEvaluatorRegistry.__post_init__(registry)
    ScopeEvaluation.__post_init__(applicability)
    if not applicability.ok or applicability.result.context != request.profile.context or applicability.result.value != YES or applicability.result.conflicts:
        return _row(rule.identity,RuleVerdict.UNKNOWN,'APPLICABILITY_NOT_ESTABLISHED','dispatch requires positive consistent applicability',applicability=applicability)
    if _meter is not None:
        # Work units include each input record/reference and each observation;
        # this is a deterministic logical budget, not a wall-clock estimate.
        _meter.spend(1 + len(request.view.records) + sum(len(r.references()) for r in request.view.records)
                     + len(request.facts.status_pairs) + len(request.facts.architectures)
                     + sum(len(a.dependencies) for a in request.facts.architectures)
                     + sum(len(x.before) + len(x.after) for x in request.facts.reference_sets))
    key=rule.rule_kind;target=rule.identity;positive=rule.source_refs;negative=rule.source_refs
    if key not in registry.identifiers or rule.semantic_version!=registry.semantic_version:
        return _row(target,RuleVerdict.UNKNOWN,'UNKNOWN_RULE_KIND','required rule has no registered semantics',applicability=applicability,evaluator=None)
    def out(verdict,code=None,reason='structural predicate checked',pos=positive,neg=()):
        return _row(target,verdict,code,reason,applicability=applicability,positive=pos if verdict is RuleVerdict.PASS else (),
                    negative=neg,evaluator=key)
    subjects=[]
    for reference in rule.predicate.subjects:
        found=resolve_entity(reference,request.view,reference.kind,request.imports)
        if not found.ok:return out(RuleVerdict.UNKNOWN,found.diagnostics[0].code,'subject body unavailable')
        body=found.value.record
        if body not in request.authority.normative_records:
            return out(RuleVerdict.UNKNOWN,'NORMATIVE_BODY_MISMATCH','subject body differs from the fixed normative snapshot')
        subjects.append(body)
    if key=='identity.kind_separation.v1':
        for record in subjects or request.view.records:
            if record.identity.kind is not record.KIND:
                return out(RuleVerdict.FAIL,'WRONG_ID_KIND','record identity mismatch',neg=negative)
        return out(RuleVerdict.PASS)
    if key=='reference.project_isolation.v1':
        report=validate_references(tuple(subjects or request.view.records),request.view,request.imports)
        if report.diagnostics:
            return out(RuleVerdict.UNKNOWN,report.diagnostics[0].code,'exact reference integrity not established')
        return out(RuleVerdict.PASS)
    if key=='source.cut_immutability.v1':
        approvals, issues = _approved_exclusions(request, _meter)
        if issues:
            row = out(RuleVerdict.UNKNOWN, issues[0].code, 'source exclusion is not authorized')
            return replace(row, diagnostics=issues)
        report=validate_source_universe(request.universe,request.project,{s.ref:s for s in request.view.sources},
                     request.source_imports,trusted_exclusion_decisions=approvals)
        if report.diagnostics:return out(RuleVerdict.UNKNOWN,report.diagnostics[0].code,'source policy/cut uncertainty')
        return out(RuleVerdict.PASS)
    if key=='normative.ratification_required.v1':
        if not subjects:return out(RuleVerdict.UNKNOWN,'MISSING_DECISION_SUBJECT','no implicit ratification')
        for body in subjects:
            if type(body) is not DecisionRevision:return out(RuleVerdict.INVALID_INPUT,'WRONG_ID_KIND','decision required')
            allowed,errors=_decision_authorized(body.identity,request,_meter)
            if not allowed:return out(RuleVerdict.UNKNOWN,errors[0].code if errors else 'UNTRUSTED_RATIFICATION','approval absent')
        return out(RuleVerdict.PASS)
    if key=='scope.four_valued.v1':
        if rule.predicate.expression_ref is None:return out(RuleVerdict.UNKNOWN,'MISSING_PREDICATE_SCOPE','requirement expression absent')
        evaluation,errors=_metered_scope(rule.predicate.expression_ref,request,_meter)
        if errors:return out(RuleVerdict.RESOURCE_LIMITED if evaluation and evaluation.status is EvaluationStatus.RESOURCE_LIMITED else RuleVerdict.UNKNOWN,errors[0].code,'requirement not evaluated')
        value=evaluation.result
        if value.conflicts or value.value==CONFLICT:
            row=_row(target,RuleVerdict.CONFLICT,'APPLICABILITY_CONFLICT','requirement has conflicting support',applicability=applicability,
                positive=tuple(w.source_ref for w in value.positive_witnesses),negative=tuple(w.source_ref for w in value.negative_witnesses),evaluator=key)
            return replace(row, requirement_evaluation=evaluation)
        if value.value==UNKNOWN:return replace(out(RuleVerdict.UNKNOWN,'MISSING_FACT','requirement unknown'),requirement_evaluation=evaluation)
        if value.value==NO:return replace(out(RuleVerdict.FAIL,'REQUIREMENT_FALSE','negative requirement witness',neg=tuple(w.source_ref for w in value.negative_witnesses)),requirement_evaluation=evaluation)
        return replace(out(RuleVerdict.PASS,pos=tuple(w.source_ref for w in value.positive_witnesses)),requirement_evaluation=evaluation)
    if key=='status.axis_separation.v1':
        if not request.facts.status_pairs:return out(RuleVerdict.UNKNOWN,'MISSING_FACT','no observed status pairs')
        rows = []
        for item in request.facts.status_pairs:
            check=check_illegal_promotion(item.source,item.target)
            if not check.ok:
                rows.append(out(RuleVerdict.FAIL,check.diagnostics[0].code,'observed illegal promotion',neg=(item.witness,)))
            else:
                rows.append(out(RuleVerdict.PASS,pos=(item.witness,)))
        return _merge_rule_evaluations(rows, rule, applicability)
    if key=='architecture.dependencies_declared.v1':
        if not subjects:return out(RuleVerdict.UNKNOWN,'MISSING_ARCHITECTURE','no architecture contract')
        rows = []
        for body in sorted(subjects, key=lambda x: ref_key(x.identity)):
            body_start = len(rows)
            if type(body) is not ArchitectureRevision:
                rows.append(out(RuleVerdict.INVALID_INPUT,'WRONG_ID_KIND','architecture required'))
                continue
            observed=[x for x in request.facts.architectures if x.architecture==body.identity]
            if not observed:
                rows.append(out(RuleVerdict.UNKNOWN,'MISSING_FACT','no observed architecture'))
                continue
            complete={frozenset(x.dependencies) for x in observed if x.complete}
            if len(complete)>1 or (complete and any(not set(x.dependencies) <= next(iter(complete)) for x in observed)):
                rows.append(_row(target,RuleVerdict.CONFLICT,'CONFLICTING_ARCHITECTURE_FACTS','complete and observed dependencies disagree',
                    applicability=applicability,positive=tuple(x.witness for x in observed if x.complete),
                    negative=tuple(x.witness for x in observed),evaluator=key))
            for fact in observed:
                actual=set(fact.dependencies)
                violation=(actual-set(body.allowed_dependencies)) | (actual & set(body.forbidden_dependencies))
                if fact.complete:violation |= set(body.required_dependencies)-actual
                if violation:
                    rows.append(out(RuleVerdict.FAIL,'ARCHITECTURE_CONSTRAINT_VIOLATION','observed dependencies violate contract',neg=(fact.witness,)))
            if not complete:
                rows.append(out(RuleVerdict.UNKNOWN,'INCOMPLETE_ARCHITECTURE_OBSERVATION','absence is not proof'))
            elif not any(r.verdict in (RuleVerdict.FAIL,RuleVerdict.CONFLICT) for r in rows[body_start:]):
                rows.append(out(RuleVerdict.PASS,pos=tuple(x.witness for x in observed)))
        return _merge_rule_evaluations(rows, rule, applicability)
    if key=='authority.conflict_localization.v1':
        if not request.facts.assertions_complete:return out(RuleVerdict.UNKNOWN,'ASSERTION_SET_INCOMPLETE','expected assertion universe not closed')
        relevant=[x.conflict for x in conflicts if target in x.blocked or any(s in x.blocked for s in rule.predicate.subjects)]
        if relevant:return _row(target,RuleVerdict.CONFLICT,'UNRESOLVED_NORMATIVE_CONFLICT','localized conflict retained',applicability=applicability,conflicts=relevant,evaluator=key)
        return out(RuleVerdict.PASS)
    if key=='normative.non_erasure_precheck.v1':
        if not request.facts.reference_sets:return out(RuleVerdict.UNKNOWN,'MISSING_FACT','both reference sets must be explicit')
        rows = [out(RuleVerdict.FAIL,'NORMATIVE_REFERENCE_ERASURE','required references lost',neg=(item.witness,))
                if not item.before <= item.after else out(RuleVerdict.PASS,pos=(item.witness,))
                for item in request.facts.reference_sets]
        return _merge_rule_evaluations(rows, rule, applicability)
    return out(RuleVerdict.UNKNOWN,'UNKNOWN_REQUIRED_VERIFIER','no registered interpreter')


class _ConstitutionLimit(Exception):
    pass


class _ConstitutionMeter:
    """Logical work units, shared by rule, authority and scope evaluations."""
    def __init__(self, limit):self.limit,self.steps=limit,0
    def spend(self, cost=1):
        if cost < 0 or self.steps + cost > self.limit:raise _ConstitutionLimit('EVALUATION_RESOURCE_LIMITED')
        self.steps += cost
    @property
    def remaining(self):return self.limit-self.steps


def _metered_scope(target,request,meter):
    if meter is None:return _scope(target,request,request.budget.scope)
    meter.spend()
    if meter.remaining < 1:raise _ConstitutionLimit('EVALUATION_RESOURCE_LIMITED')
    budget=replace(request.budget.scope,max_steps=min(request.budget.scope.max_steps,meter.remaining))
    result,errors=_scope(target,request,budget)
    if result is not None:
        meter.spend(result.steps)
        if result.status is EvaluationStatus.RESOURCE_LIMITED:raise _ConstitutionLimit('EVALUATION_RESOURCE_LIMITED')
    return result,errors


def evaluate_constitution(request: EvaluationRequest, trusted_registry: TrustedRuleEvaluatorRegistry) -> ConstitutionEvaluationReport:
    if type(request) is not EvaluationRequest or type(request.constitution) is not ConstitutionRevision:
        raise TypeError('EVALUATION_REQUEST_REQUIRED')
    constitution=request.constitution;expected=constitution.rule_refs;rows=[];errors=[];localized=();meter=None
    def finish():
        return collect_constitution_report(expected,tuple(rows),constitution.identity,constitution.policy_ref,request.candidate_ref,
            diagnostics=tuple(errors),localized_conflicts=localized,steps=meter.steps if meter else 0)
    def pending(verdict,code,reason):
        known={x.rule_ref for x in rows}
        rows.extend(_row(r,verdict,code,reason,examined=False) for r in sorted(expected,key=ref_key) if r not in known)
    try:
        ConstitutionRevision.__post_init__(constitution)
        if (type(request.view) is not RecordSnapshot or type(request.project) is not ProjectDefinition
                or type(request.universe) is not SourceUniverseRevision or type(request.facts) is not ConstitutionFacts
                or type(request.profile) is not SupportProfile or type(request.authority) is not AuthorityContext
                or type(request.budget) is not EvaluationBudget or type(request.candidate_ref) is not EntityRef):
            raise TypeError('INVALID_EVALUATION_INPUT')
        EvaluationBudget.__post_init__(request.budget)
        meter=_ConstitutionMeter(request.budget.max_steps)
        meter.spend(len(expected)+len(request.view.records)+len(request.universe.entries))
        RecordSnapshot.__post_init__(request.view); ConstitutionFacts.__post_init__(request.facts)
        SupportProfile.__post_init__(request.profile); AuthorityContext.__post_init__(request.authority)
        if not validate_rule_registry(trusted_registry).ok:raise ValueError('UNTRUSTED_RULE_EXECUTOR')
        if request.imports is not None and type(request.imports) is not TrustedEntityImports:raise TypeError('TRUSTED_IMPORT_CONTEXT_REQUIRED')
        if request.source_imports is not None and type(request.source_imports) is not TrustedImportGrants:raise TypeError('TRUSTED_IMPORT_CONTEXT_REQUIRED')
        context=request.profile.context
        if (request.authority.context!=context or request.facts.scope.context!=context
                or request.view.revision!=context.project_revision
                or request.view.project_id!=context.project_id or request.project.project_id!=context.project_id
                or constitution.identity.project!=context.project_id or request.candidate_ref.project!=context.project_id
                or constitution.identity!=request.project.constitution_ref
                or constitution.policy_ref not in (request.project.source_policy_ref,request.project.constitution_ref)
                or request.candidate_ref.kind is not EntityKind.IMPLEMENTATION
                or (context.candidate_ref is not None and context.candidate_ref!=request.candidate_ref)
                or constitution.policy_ref!=context.verification_policy_ref
                or trusted_registry.policy_ref!=context.verification_policy_ref
                or request.universe.identity!=context.source_universe_ref
                or constitution.source_universe_ref!=context.source_universe_ref):
            raise ValueError('EVALUATION_CONTEXT_MISMATCH')
        if constitution.semantic_version!='g00.constitution/v1':raise ValueError('UNSUPPORTED_CONSTITUTION_VERSION')
        if constitution.required_normative_features-CONSTITUTION_FEATURES:raise ValueError('UNSUPPORTED_NORMATIVE_FEATURE')
        bound={r.identity:r for r in request.authority.normative_records}
        if bound.get(constitution.identity)!=constitution:raise ValueError('NORMATIVE_BODY_MISMATCH')
        _validate_project_bodies(request, bound)
        assertion_errors = _assertion_population(request)
        if assertion_errors:
            errors.extend(assertion_errors)
            pending(RuleVerdict.INVALID_INPUT, assertion_errors[0].code, 'normative assertion population rejected')
            return finish()
        found=resolve_entity(constitution.identity,request.view,EntityKind.CONSTITUTION)
        if not found.ok or found.value.record!=constitution:raise ValueError('CONSTITUTION_BODY_MISMATCH')
        observed={e.cut.ref for e in request.universe.entries if e.cut.ref in request.universe.included
            and e.acquisition in (SourceStatus.CONTENT_OBSERVED,SourceStatus.SEMANTIC_RECONCILED)}
        if not request.facts.scope.source_refs<=observed:raise ValueError('EVIDENCE_SOURCE_NOT_OBSERVED')
        if any(not request.view.contains_source(s) for s in request.facts.scope.source_refs):raise ValueError('EVIDENCE_SOURCE_OUTSIDE_CATALOG')
        catalog={c.ref:c for c in request.view.sources}
        if any(catalog.get(e.cut.ref)!=e.cut for e in request.universe.entries):raise ValueError('SNAPSHOT_SOURCE_MISMATCH')
        if request.dependencies is not None and (type(request.dependencies) is not DependencyView or request.dependencies.project!=context.project_id):
            raise ValueError('CONFLICT_SCOPE_LEAK')
    except _ConstitutionLimit:
        pending(RuleVerdict.RESOURCE_LIMITED,'EVALUATION_RESOURCE_LIMITED','prevalidation budget exhausted');return finish()
    except (TypeError,ValueError,AttributeError) as exc:
        errors.append(diagnostic(str(exc),'$.request','invalid input is not a scientific failure'))
        pending(RuleVerdict.INVALID_INPUT,str(exc),'context rejected');return finish()
    try:
        for target in sorted(constitution.precondition_refs,key=ref_key):
            result,ds=_metered_scope(target,request,meter)
            if ds or result.result.value!=YES or result.result.conflicts:
                code=ds[0].code if ds else 'CONSTITUTION_PRECONDITION_UNDECIDED'
                pending(RuleVerdict.UNKNOWN,code,'precondition not established');return finish()
        if request.facts.assertions:
            # Reserve the pair and bounded scope work before conflict evaluation.
            # This deliberately overestimates worst-case work rather than let
            # conflicts bypass the shared budget.
            count=len(request.facts.assertions)
            pairs=count*(count-1)//2
            scope_count=len({a.scope_ref for a in request.facts.assertions}|{a.decision.scope_ref for a in request.authority.approvals})
            meter.spend(pairs+count+scope_count*request.budget.scope.max_steps)
            report=detect_conflicts(request.facts.assertions,request.profile,
                ConflictPolicies(request.view,request.facts.scope,request.authority,request.budget.scope,request.budget.max_conflict_pairs))
            if not report.complete and any(d.code=='EVALUATION_RESOURCE_LIMITED' for d in report.diagnostics):
                raise _ConstitutionLimit('EVALUATION_RESOURCE_LIMITED')
            errors.extend(report.diagnostics)
            localized=localize_conflicts(report.conflicts,request.dependencies or DependencyView(request.view.project_id,()))
        # Build only externally approved, applicable replacement edges. Both
        # old and new revisions remain in the expected denominator and report.
        supersessions={};decision_sources={}
        for target in sorted(constitution.decision_refs,key=ref_key):
            found=resolve_entity(target,request.view,EntityKind.DECISION)
            if not found.ok:continue
            d=found.value.record
            if d.action.kind is not ActionKind.SUPERSEDE:continue
            allowed,ds=_decision_authorized(target,request,meter)
            if not allowed:continue
            if d.action.target not in expected:continue
            for old in d.supersedes:
                if old in expected:
                    supersessions.setdefault(old,set()).add(d.action.target)
                    decision_sources.setdefault(old,[]).append(d)
        def cyclic(start):
            seen=set();todo=list(supersessions.get(start,()))
            while todo:
                meter.spend();item=todo.pop()
                if item==start:return True
                if item not in seen:seen.add(item);todo.extend(supersessions.get(item,()))
            return False
        for index,target in enumerate(sorted(expected,key=ref_key)):
            if index>=request.budget.max_rules:raise _ConstitutionLimit('EVALUATION_RESOURCE_LIMITED')
            meter.spend()
            found=resolve_entity(target,request.view,EntityKind.RULE,request.imports)
            if not found.ok:
                rows.append(_row(target,RuleVerdict.UNKNOWN,found.diagnostics[0].code,'required rule body missing',examined=False));continue
            rule=found.value.record
            if bound.get(target)!=rule:
                rows.append(_row(target,RuleVerdict.UNKNOWN,'NORMATIVE_BODY_MISMATCH','rule differs from external normative body'));continue
            if target in supersessions:
                if len(supersessions[target])!=1 or cyclic(target):
                    rows.append(_row(target,RuleVerdict.CONFLICT,'CONFLICTING_SUPERSESSION','replacement is not a partial order'));continue
                ds=decision_sources[target]
                row=RuleEvaluation(target,RuleVerdict.SUPERSEDED,None,
                    tuple(sorted({s for d in ds for s in d.source_refs},key=ref_key)),(),(),(),None,True,None,
                    tuple(sorted({d.identity for d in ds},key=ref_key)))
                rows.append(row);continue
            if rule.rule_kind not in trusted_registry.identifiers or rule.semantic_version!=trusted_registry.semantic_version:
                rows.append(_row(target,RuleVerdict.UNKNOWN,'UNKNOWN_RULE_KIND','rule kept in denominator'));continue
            if rule.authority_ref is None or rule.authority_ref.kind is not EntityKind.DECISION or rule.authority_ref not in constitution.decision_refs:
                rows.append(_row(target,RuleVerdict.UNKNOWN,'MISSING_AUTHORITY_CONTEXT','rule needs governing decision'));continue
            authorized,ds=_decision_authorized(rule.authority_ref,request,meter)
            if not authorized:
                rows.append(_row(target,RuleVerdict.UNKNOWN,ds[0].code if ds else 'UNTRUSTED_RATIFICATION','rule authority not established'));continue
            governing=resolve_entity(rule.authority_ref,request.view,EntityKind.DECISION).value.record
            if target not in governing.affected_contracts:
                rows.append(_row(target,RuleVerdict.UNKNOWN,'AUTHORITY_TARGET_MISMATCH','approval is for another rule'));continue
            applicability,ds=_metered_scope(rule.applicability_ref,request,meter)
            if ds:
                rows.append(_row(target,RuleVerdict.UNKNOWN,ds[0].code,'scope not evaluated'));continue
            result=applicability.result;relevant=tuple(x.conflict for x in localized if target in x.blocked)
            if result.conflicts or result.value==CONFLICT or relevant:
                rows.append(_row(target,RuleVerdict.CONFLICT,'UNRESOLVED_NORMATIVE_CONFLICT','conflicting scope or normative support',applicability=applicability,conflicts=relevant));continue
            if result.value==UNKNOWN:
                rows.append(_row(target,RuleVerdict.UNKNOWN,'APPLICABILITY_UNKNOWN','unknown does not remove rule',applicability=applicability));continue
            if result.value==NO:
                rows.append(_row(target,RuleVerdict.NOT_APPLICABLE,None,'witnessed exclusion',applicability=applicability));continue
            rows.append(evaluate_registered_rule(rule,request,trusted_registry,applicability,localized,_meter=meter))
    except _ConstitutionLimit:
        pending(RuleVerdict.RESOURCE_LIMITED,'EVALUATION_RESOURCE_LIMITED','shared deterministic work budget exhausted')
    except (TypeError,ValueError,AttributeError) as exc:
        errors.append(diagnostic('INVALID_EVALUATION_INPUT','$.evaluation',str(exc)))
        pending(RuleVerdict.INVALID_INPUT,'INVALID_EVALUATION_INPUT','malformed dependency did not produce a positive result')
    return finish()
