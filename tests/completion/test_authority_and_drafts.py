"""G00-04/F01..F10 and the remaining B03 incomplete-draft boundary."""
from dataclasses import fields,replace
import pytest
from foundation_completion import scenario
from foundation_b02 import entity
from completion_support import body,changed
from guardian.domain.identity import EntityKind as K,RevisionId
from guardian.domain.outcomes import DecisionStatus
from guardian.domain.authority import (ApprovalRef,ApprovalRecord,PrincipalRef,AuthorityGrant,AuthorityContext,
    ActionKind,NormativeAction,AuthorityVerdict,evaluate_authority,validate_decision)
from guardian.domain.constitution import validate_constitution,RuleRevision
from guardian.domain.drafts import RecordDraft,inspect_draft,revise_draft,complete_draft
from guardian.constitution.amendments import AmendmentRationale,make_amendment_request
from guardian.constitution.evaluator import evaluate_constitution,RuleVerdict


def test_explicit_approval_passes_conditional_check_without_ratification_event():
    req,_,ids=scenario();dec=body(req,ids['decision-main'])
    result=validate_decision(dec,req.authority)
    assert result.ok and result.value.authorized
    assert not result.value.authenticated_by_this_function and not dec.normatively_admitted
    assert result.value.approvals==(dec.approval_refs[0],)


@pytest.mark.parametrize('attack',['no-context','plain-json','no-approvals','no-grants','no-requirements','denial','wrong-target'])
def test_adv10_textual_approval_never_substitutes_for_the_external_context(attack):
    req,_,ids=scenario();dec=body(req,ids['decision-main']);ctx=req.authority
    if attack=='no-context':ctx=None
    if attack=='plain-json':ctx={'approved':True,'role':'admin'}
    if attack=='no-approvals':ctx=replace(ctx,approvals=())
    if attack=='no-grants':ctx=replace(ctx,grants=())
    if attack=='no-requirements':ctx=replace(ctx,requirements=())
    if attack=='denial':ctx=replace(ctx,denied_actions=frozenset({(ctx.approvals[0].principal,dec.action)}))
    if attack=='wrong-target':ctx=replace(ctx,grants=tuple(replace(g,targets=frozenset({ids['obligation-now']})) for g in ctx.grants))
    result=validate_decision(dec,ctx)
    assert not result.ok
    assert result.diagnostics[0].code in {'UNTRUSTED_RATIFICATION','MISSING_APPROVAL','UNKNOWN_AUTHORITY_RULE'}


@pytest.mark.parametrize('field,value',[('statement','I authorize everything now'),('rationale','different rationale'),('alternatives',('new option',))])
def test_reusing_approval_for_different_decision_body_at_same_revision_fails(field,value):
    req,_,ids=scenario();dec=body(req,ids['decision-main'])
    assert validate_decision(dec,req.authority).ok
    result=validate_decision(replace(dec,**{field:value}),req.authority)
    assert not result.ok and result.diagnostics[0].code=='MISSING_APPROVAL'


@pytest.mark.parametrize('state',[DecisionStatus.PROPOSED,DecisionStatus.REJECTED,DecisionStatus.SUPERSEDED])
def test_nonapproved_decisions_remain_descriptive_without_becoming_authorized(state):
    req,_,ids=scenario();dec=replace(body(req,ids['decision-main']),declared_status=state)
    result=validate_decision(dec,None)
    assert result.ok and not result.value.authorized and not result.value.approvals


def test_external_quorum_cannot_be_weakened_by_candidate_constitution_or_parameter():
    req,reg,ids=scenario();dec=body(req,ids['decision-main'])
    ctx=replace(req.authority,requirements=tuple(replace(r,minimum=2) for r in req.authority.requirements))
    assert not validate_decision(dec,ctx,minimum_approvals=1).ok
    result=evaluate_constitution(replace(req,authority=ctx),reg)
    assert result.aggregate_verdict is not RuleVerdict.PASS
    assert any(d.code=='MISSING_APPROVAL' for row in result.rule_results for d in row.diagnostics)


def test_quorum_counts_distinct_principals_not_multiple_signatures_by_one_actor():
    req,_,ids=scenario();dec=body(req,ids['decision-main']);first=req.authority.approvals[0]
    second_ref=replace(first.reference,identifier='second-approval')
    d=replace(dec,approval_refs=(first.reference,second_ref))
    ctx=replace(req.authority,approvals=(replace(first,decision=d),ApprovalRecord(second_ref,d,first.principal,first.context)),
        requirements=tuple(replace(r,minimum=2) for r in req.authority.requirements))
    assert not validate_decision(d,ctx).ok
    reviewer=PrincipalRef(req.view.project_id,'second-independent-reviewer')
    ctx=replace(ctx,principals=ctx.principals|{reviewer},grants=ctx.grants+(replace(ctx.grants[0],principal=reviewer),),
        approvals=(ctx.approvals[0],replace(ctx.approvals[1],principal=reviewer)))
    assert validate_decision(d,ctx).value.authorized


def test_independent_author_policy_rejects_self_approval_even_with_capability_grant():
    req,_,ids=scenario();dec=body(req,ids['decision-main']);a=req.authority.approvals[0]
    ctx=replace(req.authority,approvals=(replace(a,principal=dec.actor),),grants=(replace(req.authority.grants[0],principal=dec.actor),))
    assert evaluate_authority(dec.actor,dec.action,ctx).verdict is AuthorityVerdict.AUTHORIZED
    assert not validate_decision(dec,ctx,independent_author=False).ok


def test_grant_for_one_scope_or_target_does_not_expand_to_another():
    req,_,ids=scenario();actor=req.authority.approvals[0].principal;dec=body(req,ids['decision-main'])
    query=replace(dec.action,target=ids['obligation-now'])
    assert evaluate_authority(actor,query,req.authority).verdict is AuthorityVerdict.REQUIRES_APPROVAL
    query=replace(dec.action,scope_ref=entity(req.view.project_id,K.SCOPE,'other-scope'))
    assert evaluate_authority(actor,query,req.authority).verdict is AuthorityVerdict.REQUIRES_APPROVAL
    assert evaluate_authority(scenario('project-beta')[0].authority.approvals[0].principal,dec.action,req.authority).verdict is AuthorityVerdict.DENIED


def test_policy_or_candidate_revision_mismatch_is_not_inferred_away():
    req,reg,ids=scenario();foreign=scenario('project-beta')[0]
    assert not validate_decision(body(req,ids['decision-main']),foreign.authority).ok
    changed_context=replace(req.profile.context,profile_revision=RevisionId('rev-'+'1'*32))
    # Reconstitute the external test-harness context; using it against a different
    # request must still be rejected rather than choosing the latest profile.
    ctx=replace(req.authority,context=changed_context,approvals=())
    result=evaluate_constitution(replace(req,authority=ctx),reg)
    assert result.aggregate_verdict is RuleVerdict.INVALID_INPUT
    assert 'EVALUATION_CONTEXT_MISMATCH' in {d.code for d in result.diagnostics}


def test_adv11_foreign_rules_never_enter_local_constitution():
    req,_,_=scenario();foreign=scenario('project-beta')[0]
    with pytest.raises(ValueError,match='FOREIGN_CONSTITUTION_RULE'):
        replace(req.constitution,rule_refs=(foreign.constitution.rule_refs[0],))


def test_constitution_validation_resolves_actual_rules_not_anchors():
    req,_,_=scenario();assert validate_constitution(req.constitution,req.view).ok
    target=req.constitution.rule_refs[0]
    view=replace(req.view,records=tuple(r for r in req.view.records if r.identity!=target),anchors=(target,))
    result=validate_constitution(req.constitution,view)
    assert not result.ok and any(d.code=='REFERENCED_CONTENT_UNAVAILABLE' for d in result.diagnostics)


def test_amendment_is_a_new_proposal_with_explicit_lineage_not_policy_mutation():
    req,_,_=scenario();old=body(req,req.constitution.rule_refs[0]);before=hash(req.view)
    new=replace(old,identity=replace(old.identity,revision=RevisionId('rev-'+'9'*32)),rationale='proposed changed rationale',declared_status=DecisionStatus.PROPOSED)
    result=make_amendment_request(old,new,AmendmentRationale('review the rationale',(old.identity,)))
    assert result.ok and result.value.status=='PROPOSED_ONLY'
    assert hash(req.view)==before and body(req,old.identity) is old
    assert not make_amendment_request(old,old,AmendmentRationale('no new version',(old.identity,))).ok


@pytest.mark.parametrize('kind',[K.OBJECTIVE,K.CAPABILITY,K.PROPERTY,K.OBLIGATION,K.CAMPAIGN,K.ARCHITECTURE])
def test_each_business_record_can_begin_as_incomplete_draft_and_complete_as_proposed(kind):
    req,_,_=scenario();record=next(x for x in req.view.records if x.identity.kind is kind)
    draft=RecordDraft(record.identity)
    report=inspect_draft(draft)
    assert not report.contract_ready and report.missing_fields and not draft.normatively_admitted
    values=tuple((f.name,getattr(record,f.name)) for f in fields(record) if f.init and f.name!='identity')
    ready=RecordDraft(record.identity,values);result=complete_draft(ready)
    assert result.ok and result.value==record and not result.value.normatively_admitted
    assert result.value.declared_status is DecisionStatus.PROPOSED


@pytest.mark.parametrize('absent',[None,(),[]])
def test_draft_keeps_null_empty_and_absent_acceptance_distinct_without_defaults(absent):
    req,_,ids=scenario();record=body(req,ids['obligation-now'])
    values=tuple((f.name,getattr(record,f.name)) for f in fields(record) if f.init and f.name not in ('identity','acceptance_contract'))
    empty=RecordDraft(record.identity,values)
    assert 'acceptance_contract' in inspect_draft(empty).missing_fields
    if absent==[]:
        with pytest.raises(TypeError):RecordDraft(record.identity,values+(('acceptance_contract',absent),))
    else:
        report=inspect_draft(RecordDraft(record.identity,values+(('acceptance_contract',absent),)))
        assert not report.missing_fields and not report.contract_ready and report.diagnostics[0].code=='DRAFT_CONTRACT_INVALID'


def test_revising_draft_needs_new_revision_and_never_mutates_prior_or_admits_it():
    req,_,ids=scenario();draft=RecordDraft(ids['obligation-now'])
    identity=replace(draft.identity,revision=RevisionId('rev-'+'9'*32))
    new=revise_draft(draft,identity,(('statement','new draft text'),))
    assert new.prior==draft.identity and not draft.supplied_fields
    with pytest.raises(ValueError):revise_draft(draft,draft.identity,())
    with pytest.raises(ValueError,match='DRAFT_CANNOT_RATIFY'):RecordDraft(identity,(('declared_status',DecisionStatus.APPROVED),))
