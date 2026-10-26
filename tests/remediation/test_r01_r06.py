"""Original-contract falsations R01-R06, independent of the happy-path counts."""
from dataclasses import replace
from itertools import permutations
import copy
import pytest
from foundation_completion import scenario
from foundation_b02 import cut, entity
from guardian.domain.identity import EntityKind as K, RevisionId, encode_identity
from guardian.domain.claims import Assertion, AssertionDomain
from guardian.domain.authority import ActionKind
from guardian.domain.foundation_records import SourceUniverseRecord, SourcePolicyRevision
from guardian.domain.source import SourceEntry, SourceExclusion, HistoryRole, MissingSource
from guardian.domain.outcomes import (SourceStatus, StatusAxis, TypedStatus,
    ImplementationStatus, MaterialStatus, AuditStatus, QualificationStatus)
from guardian.domain.references import validate_references
from guardian.domain.scope import evaluate_scope
from guardian.constitution.evaluator import evaluate_constitution, RuleVerdict
from guardian.persistence.schema_registry import foundation_schema_registry, encode_record, decode_record


def recontextualize(req, universe, cuts):
    """Test operator explicitly pins a legitimate new universe body."""
    records=tuple(replace(r, universe=universe) if type(r) is SourceUniverseRecord else r
                  for r in req.view.records)
    pins=tuple(replace(r, universe=universe) if type(r) is SourceUniverseRecord else r
               for r in req.authority.normative_records)
    return replace(req, universe=universe, view=replace(req.view, records=records, sources=cuts),
                   authority=replace(req.authority, normative_records=pins))


def with_second_source(req, excluded=False):
    extra=cut(req.project, name='source-extra', path='spec/extra.gsl', commit='f'*40)
    entry=SourceEntry(extra, HistoryRole.REFERENCE, SourceStatus.CONTENT_OBSERVED, 'extra-lineage')
    exclusion=(SourceExclusion(extra.ref,'not in this corpus',req.constitution.decision_refs[0]),) if excluded else ()
    universe=replace(req.universe, entries=req.universe.entries+(entry,),
        included=req.universe.included if excluded else req.universe.included+(extra.ref,),excluded=exclusion)
    return recontextualize(req,universe,req.view.sources+(extra,)),extra


def assertions(req, ids):
    refs=req.constitution.rule_refs[:2]
    base=Assertion(refs[0],ids['property-main'],'representation','exact',AssertionDomain.NORMATIVE,
                   ids['scope-main'],(req.view.sources[0].ref,),ids['decision-main'])
    return base,replace(base,identity=refs[1],value='floating')


@pytest.mark.parametrize('remaining',[0,1])
def test_R01_pinned_normative_assertions_cannot_be_removed_to_claim_completeness(remaining):
    req,registry,ids=scenario();claims=assertions(req,ids)
    req=replace(req,authority=replace(req.authority,assertion_pins=claims),
                facts=replace(req.facts,assertions=claims[:remaining],assertions_complete=True))
    report=evaluate_constitution(req,registry)
    codes={d.code for d in report.diagnostics}|{d.code for r in report.rule_results for d in r.diagnostics}
    assert report.aggregate_verdict is not RuleVerdict.PASS
    assert 'ASSERTION_SET_INCOMPLETE' in codes
    assert len(report.rule_results)==len(req.constitution.rule_refs)


def test_R02_unrelated_rule_adoption_cannot_authorize_a_source_exclusion():
    req,registry,_=scenario();req,_=with_second_source(req,excluded=True)
    report=evaluate_constitution(req,registry)
    rule=next(r for r in req.view.records if getattr(r,'rule_kind',None)=='source.cut_immutability.v1')
    row=next(r for r in report.rule_results if r.rule_ref==rule.identity)
    assert row.verdict is not RuleVerdict.PASS
    assert 'EXCLUSION_AUTHORIZATION_MISMATCH' in {d.code for d in row.diagnostics}


@pytest.mark.parametrize('attribute,value', [
    ('declared_limits',('silently weakened universe',)),
    ('known_missing',(MissingSource('missing://norm','not available'),)),
])
def test_R03_same_universe_identity_does_not_authorize_another_body(attribute,value):
    req,registry,_=scenario()
    report=evaluate_constitution(replace(req,universe=replace(req.universe,**{attribute:value})),registry)
    assert report.aggregate_verdict is RuleVerdict.INVALID_INPUT
    assert 'NORMATIVE_UNIVERSE_BODY_MISMATCH' in {d.code for d in report.diagnostics}


def test_R03_source_policy_body_in_snapshot_cannot_disagree_with_request():
    from guardian.domain.project import RepositoryId
    req,registry,_=scenario()
    old=next(r for r in req.view.records if type(r) is SourcePolicyRevision)
    bad=replace(old,policy=replace(old.policy,allow_repositories=(RepositoryId('github','untrusted/other'),)))
    view=replace(req.view,records=tuple(bad if r.identity==bad.identity else r for r in req.view.records))
    report=evaluate_constitution(replace(req,view=view),registry)
    assert report.aggregate_verdict is RuleVerdict.INVALID_INPUT
    assert 'NORMATIVE_POLICY_BODY_MISMATCH' in {d.code for d in report.diagnostics}


def test_R04_nested_exclusion_approval_is_part_of_reference_integrity():
    req,_,_=scenario();req,extra=with_second_source(req,excluded=True)
    phantom=entity(req.view.project_id,K.DECISION,'absent-exclusion-approval')
    record=next(r for r in req.view.records if type(r) is SourceUniverseRecord)
    record=replace(record,universe=replace(record.universe,excluded=(SourceExclusion(extra.ref,'excluded',phantom),)))
    report=validate_references((record,),req.view)
    assert any(d.code=='ORPHAN_REFERENCE' and '.excluded[0].approval_ref' in d.path for d in report.diagnostics)


def test_R04_baseline_is_a_field_specific_reference_not_hidden_inside_payload():
    req,_,_=scenario();record=next(r for r in req.view.records if type(r) is SourceUniverseRecord)
    original=record.universe.entries[0]
    baseline=entity(req.view.project_id,K.SOURCE,'source-unavailable')
    record=replace(record,universe=replace(record.universe,entries=(replace(original,role=HistoryRole.DELTA,baseline_ref=baseline),)))
    report=validate_references((record,),req.view)
    assert any(d.code=='UNKNOWN_SOURCE' and '.entries[0].baseline_ref' in d.path for d in report.diagnostics)


def applicability(req,ids):
    scope=req.view._by_ref[ids['scope-main']]
    return evaluate_scope(scope.expression,req.profile,req.facts.scope).result


def test_R05_applicability_cannot_be_encoded_with_foreign_envelope_context():
    req,_,ids=scenario();other,_,_=scenario('project-beta')
    record=applicability(req,ids);registry=foundation_schema_registry(req.view.revision)
    result=encode_record(record,registry,
        envelope_ref=entity(other.view.project_id,K.PROJECT,'transport-record'),
        source_refs=(other.view.sources[0].ref,))
    assert not result.ok
    assert 'ENVELOPE_PAYLOAD_PROJECT_MISMATCH' in result.diagnostics[0].reason


def test_R05_applicability_decoding_checks_context_not_only_envelope_consistency():
    req,_,ids=scenario();other,_,_=scenario('project-beta')
    registry=foundation_schema_registry(req.view.revision)
    wire=encode_record(applicability(req,ids),registry,
        envelope_ref=entity(req.view.project_id,K.PROJECT,'transport-record'),
        source_refs=(req.view.sources[0].ref,)).value
    wire=copy.deepcopy(wire)
    wire['project_id']=encode_identity(other.view.project_id)
    wire['logical_id']['project']=other.view.project_id.value
    wire['source_refs']=[encode_identity(other.view.sources[0].ref)]
    result=decode_record(wire,registry)
    assert not result.ok
    assert 'ENVELOPE_PAYLOAD_PROJECT_MISMATCH' in result.diagnostics[0].reason


def test_R05_applicability_witnesses_cannot_be_relabelled_as_another_source():
    req,_,ids=scenario();req,extra=with_second_source(req)
    registry=foundation_schema_registry(req.view.revision)
    result=encode_record(applicability(req,ids),registry,
        envelope_ref=entity(req.view.project_id,K.PROJECT,'transport-record'),source_refs=(extra.ref,))
    assert not result.ok
    assert 'ENVELOPE_PAYLOAD_SOURCE_MISMATCH' in result.diagnostics[0].reason


def test_R06_illegal_status_facts_preserve_all_witnesses_and_permutation_invariance():
    req,registry,_=scenario();req,extra=with_second_source(req)
    facts=replace(req.facts,scope=replace(req.facts.scope,source_refs=req.facts.scope.source_refs|{extra.ref}))
    sample=req.facts.status_pairs[0]
    left=replace(sample,source=TypedStatus(StatusAxis.IMPLEMENTATION,ImplementationStatus.DEVELOPMENT_COMPLETE),
                 target=TypedStatus(StatusAxis.MATERIAL,MaterialStatus.PASS))
    right=replace(left,witness=extra.ref)
    reports=[evaluate_constitution(replace(req,facts=replace(facts,status_pairs=order)),registry) for order in permutations((left,right))]
    assert reports[0]==reports[1]
    row=next(r for r in reports[0].rule_results if r.evaluator_id=='status.axis_separation.v1')
    assert set(row.negative_witnesses)=={sample.witness,extra.ref}


def test_R01_complete_pinned_assertions_preserve_both_sides_of_the_conflict():
    req,registry,ids=scenario();claims=assertions(req,ids)
    req=replace(req,authority=replace(req.authority,assertion_pins=claims),
                facts=replace(req.facts,assertions=claims,assertions_complete=True))
    result=evaluate_constitution(req,registry)
    assert result.aggregate_verdict is RuleVerdict.CONFLICT
    assert result.localized_conflicts
    assert {result.localized_conflicts[0].conflict.left,result.localized_conflicts[0].conflict.right}==set(claims)


def test_R01_same_assertion_id_with_another_body_is_not_a_complete_original_set():
    req,registry,ids=scenario();claims=assertions(req,ids)
    req=replace(req,authority=replace(req.authority,assertion_pins=claims),
                facts=replace(req.facts,assertions=(claims[0],replace(claims[1],value=claims[0].value)),assertions_complete=True))
    result=evaluate_constitution(req,registry)
    assert result.aggregate_verdict is RuleVerdict.INVALID_INPUT
    assert 'NORMATIVE_ASSERTION_BODY_MISMATCH' in {d.code for d in result.diagnostics}


def authorized_exclusion():
    from guardian.domain.authority import (ApprovalRef,ApprovalRecord,NormativeAction)
    req,registry,ids=scenario();req,extra=with_second_source(req,excluded=True)
    original=req.authority.approvals[0]
    identity=entity(req.view.project_id,K.DECISION,'decision-exclude')
    approval=ApprovalRef(req.view.project_id,'approval-exclude',req.view.revision)
    decision=replace(original.decision,identity=identity,
        action=NormativeAction(ActionKind.EXCLUDE_SOURCE,req.universe.identity,ids['scope-main']),
        statement='Exclude exactly this source from the fixed universe',approval_refs=(approval,),
        affected_contracts=(req.universe.identity,extra.ref))
    universe=replace(req.universe,excluded=(replace(req.universe.excluded[0],approval_ref=identity),))
    req=recontextualize(req,universe,req.view.sources)
    grant=replace(req.authority.grants[0],targets=req.authority.grants[0].targets|{req.universe.identity})
    req=replace(req,view=replace(req.view,records=req.view.records+(decision,)),
        authority=replace(req.authority,grants=(grant,),normative_records=req.authority.normative_records+(decision,),
            approvals=req.authority.approvals+(ApprovalRecord(approval,decision,original.principal,req.profile.context),)))
    return req,registry,ids,extra,decision


def test_R02_legitimate_exact_source_exclusion_remains_valid():
    req,registry,_,_,_=authorized_exclusion()
    result=evaluate_constitution(req,registry)
    row=next(r for r in result.rule_results if r.evaluator_id=='source.cut_immutability.v1')
    assert row.verdict is RuleVerdict.PASS, row
    assert result.aggregate_verdict is RuleVerdict.PASS,result


@pytest.mark.parametrize('attack',['cut','universe','scope','grant'])
def test_R02_legitimate_approval_cannot_be_reused_outside_its_exact_contract(attack):
    req,registry,ids,extra,decision=authorized_exclusion()
    if attack=='grant':
        req=replace(req,authority=replace(req.authority,grants=tuple(replace(g,targets=g.targets-{req.universe.identity}) for g in req.authority.grants)))
    else:
        from guardian.domain.authority import ApprovalRecord
        if attack=='cut':bad=replace(decision,affected_contracts=(req.universe.identity,req.view.sources[0].ref))
        elif attack=='universe':
            other=entity(req.view.project_id,K.SOURCE_UNIVERSE,'other-universe')
            bad=replace(decision,action=replace(decision.action,target=other),affected_contracts=(other,extra.ref))
        else:
            # Unknown scope is not silently interpreted as universally applicable.
            target=entity(req.view.project_id,K.SCOPE,'unknown-scope')
            bad=replace(decision,scope_ref=target,action=replace(decision.action,scope_ref=target))
        req=replace(req,view=replace(req.view,records=tuple(bad if r.identity==decision.identity else r for r in req.view.records)))
    result=evaluate_constitution(req,registry)
    assert result.aggregate_verdict is not RuleVerdict.PASS
    row=next(r for r in result.rule_results if r.evaluator_id=='source.cut_immutability.v1')
    assert row.verdict is not RuleVerdict.PASS


def test_R03_project_body_is_fixed_not_just_its_identifier():
    req,registry,_=scenario()
    changed=replace(req.project,display_name='Renamed without the pinned project revision')
    result=evaluate_constitution(replace(req,project=changed),registry)
    assert result.aggregate_verdict is RuleVerdict.INVALID_INPUT
    assert 'NORMATIVE_PROJECT_BODY_MISMATCH' in {d.code for d in result.diagnostics}


def test_R04_all_nested_references_in_authorized_universe_are_valid():
    req,_,_,_,_=authorized_exclusion()
    record=next(r for r in req.view.records if type(r) is SourceUniverseRecord)
    report=validate_references((record,),req.view)
    assert report.ok,report.diagnostics
    assert any('.excluded[0].approval_ref' in u.path for u in record.references())


def test_R05_profile_and_result_roundtrip_preserve_internal_context_and_witnesses():
    req,_,ids=scenario();registry=foundation_schema_registry(req.view.revision)
    reference=entity(req.view.project_id,K.PROJECT,'transport-record')
    for value in (req.profile,applicability(req,ids)):
        encoded=encode_record(value,registry,envelope_ref=reference,source_refs=(req.view.sources[0].ref,))
        assert encoded.ok,encoded.diagnostics
        decoded=decode_record(encoded.value,registry)
        assert decoded.ok and decoded.value.record==value


def test_R06_architecture_and_erasure_reports_are_permutation_invariant():
    from guardian.constitution.evaluator import ArchitectureObservation,ReferenceSetObservation
    req,registry,ids=scenario();req,extra=with_second_source(req)
    facts=replace(req.facts,scope=replace(req.facts.scope,source_refs=req.facts.scope.source_refs|{extra.ref}))
    observed=facts.architectures[0]
    arch=(replace(observed,dependencies=(('domain','application'),)),replace(observed,dependencies=(),witness=extra.ref))
    first=facts.reference_sets[0]
    erased=(replace(first,after=frozenset()),replace(first,after=frozenset({ids['obligation-now']}),witness=extra.ref))
    a=evaluate_constitution(replace(req,facts=replace(facts,architectures=arch,reference_sets=erased)),registry)
    b=evaluate_constitution(replace(req,facts=replace(facts,architectures=tuple(reversed(arch)),reference_sets=tuple(reversed(erased)))),registry)
    assert a==b
    for name in ('architecture.dependencies_declared.v1','normative.non_erasure_precheck.v1'):
        row=next(r for r in a.rule_results if r.evaluator_id==name)
        assert {observed.witness,extra.ref}<=set(row.negative_witnesses)
