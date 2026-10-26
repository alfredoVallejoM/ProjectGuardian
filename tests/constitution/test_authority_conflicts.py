"""G00-11 and ADV12/33..35: scoped, pinned, non-temporal precedence."""
from dataclasses import replace
from itertools import permutations
import pytest
from foundation_completion import scenario
from foundation_b02 import entity
from completion_support import body,changed
from guardian.domain.identity import EntityKind as K,RevisionId
from guardian.domain.scope import ScopeRevision,Atom,Operator,DimensionValue,ValueKind,StepBudget
from guardian.domain.authority import (DecisionRevision,ActionKind,NormativeAction,ApprovalRef,ApprovalRecord,
    ApprovalPolicyRequirement,AuthorityGrant,validate_decision)
from guardian.domain.outcomes import DecisionStatus
from guardian.constitution.precedence import (Assertion,AssertionDomain,ConflictPolicies,PrecedenceStatus,
    detect_conflicts,resolve_precedence,DependencyView,localize_conflicts)
from guardian.constitution.evaluator import evaluate_constitution,RuleVerdict,EvaluationBudget


def conflict_case():
    req,registry,ids=scenario();left,right=req.constitution.rule_refs[:2];scope=ids['scope-main'];s=req.view.sources[0].ref
    # The operator pins the full claims, not just their identifiers.
    a=Assertion(left,ids['property-main'],'required-representation','exact',AssertionDomain.NORMATIVE,scope,(s,),ids['decision-main'])
    b=replace(a,identity=right,value='floating')
    req=replace(req,authority=replace(req.authority,assertion_pins=(a,b)))
    return req,registry,ids,a,b


def policies(req,**kw):return ConflictPolicies(req.view,req.facts.scope,req.authority,**kw)


def approve_supersession(req,old,new,scope=None,name='replace-rule'):
    dec=body(req,req.constitution.decision_refs[0]);scope=scope or dec.scope_ref
    identity=entity(req.view.project_id,K.DECISION,name)
    approval=ApprovalRef(req.view.project_id,'approval-'+name,req.view.revision)
    replacement=replace(dec,identity=identity,scope_ref=scope,action=NormativeAction(ActionKind.SUPERSEDE,new,scope),
        approval_refs=(approval,),affected_contracts=(old,new),supersedes=(old,))
    req=changed(req,replacement)
    reviewer=req.authority.approvals[0].principal
    ctx=replace(req.authority,approvals=req.authority.approvals+(ApprovalRecord(approval,replacement,reviewer,req.profile.context),),
        grants=req.authority.grants+(AuthorityGrant(reviewer,frozenset({ActionKind.SUPERSEDE}),frozenset({scope}),frozenset({new})),),
        requirements=req.authority.requirements+(ApprovalPolicyRequirement(ActionKind.SUPERSEDE,frozenset({scope}),1,True),)
        if not any(r.action is ActionKind.SUPERSEDE and scope in r.scopes for r in req.authority.requirements) else req.authority.requirements)
    return replace(req,authority=ctx),replacement


def test_opposite_normative_claims_retain_both_sources_and_conflict_without_supersession():
    req,_,ids,a,b=conflict_case();result=detect_conflicts((a,b),req.profile,policies(req))
    assert result.complete and not result.diagnostics and len(result.conflicts)==1
    conflict=result.conflicts[0]
    assert conflict.confirmed and set(conflict.witnesses)>={a.identity,b.identity,*a.source_refs,*b.source_refs}
    assert 'MISSING_APPROVED_SUPERSESSION' in conflict.reasons
    before=hash(req.view)
    for order in permutations((a,b)):
        assert detect_conflicts(order,req.profile,policies(req))==result
    assert hash(req.view)==before


def test_source_date_or_larger_revision_never_creates_precedence():
    req,_,ids,a,b=conflict_case()
    result=resolve_precedence(a,b,(),req.authority)
    assert result.status is PrecedenceStatus.CONFLICT and result.reasons==('MISSING_APPROVED_SUPERSESSION',)
    assert resolve_precedence(b,a,(),req.authority).status is PrecedenceStatus.CONFLICT


def test_approved_exact_supersession_resolves_without_erasing_history():
    req,_,ids,a,b=conflict_case();req,d=approve_supersession(req,a.identity,b.identity)
    assert validate_decision(d,req.authority).value.authorized
    result=detect_conflicts((a,b),req.profile,policies(req))
    assert not result.conflicts and len(result.resolutions)==1
    assert result.resolutions[0].status is PrecedenceStatus.RIGHT_PRECEDES
    assert a.identity in req.view._by_ref and b.identity in req.view._by_ref
    assert result.resolutions[0].decisions==(d.identity,)


@pytest.mark.parametrize('attack',['missing-approval','proposed','body-change','wrong-scope'])
def test_supersession_proposal_cannot_override_an_existing_rule(attack):
    req,_,ids,a,b=conflict_case();req,d=approve_supersession(req,a.identity,b.identity)
    candidates=(d,)
    if attack=='missing-approval':req=replace(req,authority=replace(req.authority,approvals=req.authority.approvals[:-1]))
    if attack=='proposed':candidates=(replace(d,declared_status=DecisionStatus.PROPOSED),)
    if attack=='body-change':candidates=(replace(d,rationale='unapproved replacement'),)
    if attack=='wrong-scope':
        scope=entity(req.view.project_id,K.SCOPE,'scope-other')
        candidates=(replace(d,scope_ref=scope,action=replace(d.action,scope_ref=scope)),)
    assert resolve_precedence(a,b,candidates,req.authority).status is PrecedenceStatus.CONFLICT


def test_supersession_cycle_is_a_conflict_not_first_registered_wins():
    req,_,ids,a,b=conflict_case();req,ab=approve_supersession(req,a.identity,b.identity)
    req,ba=approve_supersession(req,b.identity,a.identity,name='reverse-replacement')
    for order in ((ab,ba),(ba,ab)):
        result=resolve_precedence(a,b,order,req.authority)
        assert result.status is PrecedenceStatus.CONFLICT and 'PRECEDENCE_CYCLE' in result.reasons


def test_known_disjoint_scopes_do_not_generate_a_normative_conflict():
    req,_,ids,a,b=conflict_case();original=body(req,ids['scope-main'])
    absent=replace(original,identity=entity(req.view.project_id,K.SCOPE,'scope-absent'),
        expression=Atom('features',Operator.CONTAINS,DimensionValue(ValueKind.TEXT,'absent')))
    req=changed(req,absent,operator_repin=True);b=replace(b,scope_ref=absent.identity)
    req=replace(req,authority=replace(req.authority,assertion_pins=(a,b)))
    result=detect_conflicts((a,b),req.profile,policies(req))
    assert result.complete and not result.conflicts


def test_unknown_intersection_is_visible_not_asserted_to_be_disjoint():
    req,_,ids,a,b=conflict_case();unknown=replace(body(req,ids['scope-main']),identity=entity(req.view.project_id,K.SCOPE,'scope-unknown'),
        expression=Atom('platform',Operator.EQUALS,DimensionValue(ValueKind.TEXT,'linux')))
    req=changed(req,unknown,operator_repin=True);b=replace(b,scope_ref=unknown.identity)
    req=replace(req,authority=replace(req.authority,assertion_pins=(a,b)))
    result=detect_conflicts((a,b),req.profile,policies(req))
    assert len(result.conflicts)==1 and not result.conflicts[0].confirmed
    assert result.conflicts[0].reasons[0]=='SCOPE_INTERSECTION_UNKNOWN_OR_CONFLICT'


def test_facts_proposals_and_norms_are_separate_authority_domains():
    req,_,ids,a,b=conflict_case()
    observed=replace(b,domain=AssertionDomain.OBSERVED,observation_revision=req.view.revision,authority_ref=None)
    assert not detect_conflicts((a,observed),req.profile,policies(req)).conflicts
    proposed=replace(b,domain=AssertionDomain.PROPOSED,authority_ref=None)
    report=detect_conflicts((a,proposed),req.profile,policies(req))
    assert not report.conflicts and report.nonbinding==(b.identity,)
    older=replace(a,domain=AssertionDomain.OBSERVED,observation_revision=RevisionId('rev-'+'1'*32),authority_ref=None)
    assert not detect_conflicts((older,observed),req.profile,policies(req)).conflicts


def test_unauthorized_claim_body_is_not_made_normative_by_approved_identity():
    req,_,ids,a,b=conflict_case();forged=replace(a,value='attacker text')
    report=detect_conflicts((forged,b),req.profile,policies(req))
    assert a.identity in report.nonbinding
    assert 'UNTRUSTED_RATIFICATION' in {d.code for d in report.diagnostics}


def test_localization_preserves_both_witnesses_and_only_supplied_dependents():
    req,_,ids,a,b=conflict_case();conflicts=detect_conflicts((a,b),req.profile,policies(req)).conflicts
    deps=DependencyView(req.view.project_id,((a.identity,ids['obligation-now']),(ids['obligation-now'],ids['campaign-now']),
        (ids['campaign-now'],ids['obligation-now'])))
    result=localize_conflicts(conflicts,deps)
    assert len(result)==1 and result[0].conflict==conflicts[0]
    assert set(result[0].blocked)=={a.identity,b.identity,ids['obligation-now'],ids['campaign-now']}
    assert ids['obligation-future'] not in result[0].blocked
    foreign=scenario('project-beta')[0]
    with pytest.raises(ValueError,match='CONFLICT_SCOPE_LEAK'):localize_conflicts(conflicts,DependencyView(foreign.view.project_id,()))


def test_conflict_resource_limit_preserves_incomplete_outcome():
    req,_,ids,a,b=conflict_case();result=detect_conflicts((a,b),req.profile,policies(req,max_pairs=0))
    assert not result.complete and 'EVALUATION_RESOURCE_LIMITED' in {d.code for d in result.diagnostics}


def test_constitution_replacement_keeps_both_rules_in_report_without_evaluating_old_as_current():
    req,reg,ids,a,b=conflict_case();old=req.constitution.rule_refs[0];new=req.constitution.rule_refs[1]
    # Preserve the full pinned population in this positive supersession case.
    # R01 separately proves that omitting either assertion is rejected.
    req=replace(req,facts=replace(req.facts,assertions=(a,b)))
    req,d=approve_supersession(req,old,new)
    constitution=replace(req.constitution,decision_refs=req.constitution.decision_refs+(d.identity,))
    req=changed(req,constitution,operator_repin=True)
    report=evaluate_constitution(req,reg)
    assert report.aggregate_verdict is RuleVerdict.PASS,report
    row=next(x for x in report.rule_results if x.rule_ref==old)
    assert row.verdict is RuleVerdict.SUPERSEDED and row.supersession_decisions==(d.identity,)
    assert len(report.rule_results)==len(req.constitution.rule_refs)==9


def test_mixed_failure_and_conflict_are_both_retained_in_full_report():
    req,reg,ids,a,b=conflict_case()
    architecture=req.facts.architectures[0]
    # A forbidden dependency is a demonstrable failure; a separate conflict
    # remains visible instead of being discarded by aggregation.
    facts=replace(req.facts,assertions=(a,b),architectures=(replace(architecture,dependencies=(('domain','application'),)),))
    req=replace(req,facts=facts,dependencies=DependencyView(req.view.project_id,((a.identity,ids['obligation-now']),)))
    report=evaluate_constitution(req,reg)
    assert 'CONFLICT' in report.verdicts_present
    # Select a nonconflicted rule to violate, since a rule with conflicted
    # authority must not also be evaluated as if it were uncontested.
    status=next(r for r in req.view.records if getattr(r,'rule_kind',None)=='status.axis_separation.v1')
    from guardian.domain.outcomes import TypedStatus,StatusAxis,ImplementationStatus,MaterialStatus
    pair=req.facts.status_pairs[0]
    bad=replace(pair,source=TypedStatus(StatusAxis.IMPLEMENTATION,ImplementationStatus.DEVELOPMENT_COMPLETE),target=TypedStatus(StatusAxis.MATERIAL,MaterialStatus.PASS))
    report=evaluate_constitution(replace(req,facts=replace(facts,status_pairs=(bad,))),reg)
    assert {'FAIL','CONFLICT'}<=set(report.verdicts_present)
    assert report.localized_conflicts and len(report.rule_results)==9
