"""The seven original G00-V01..V07 use actual source, record and evaluator paths.

These tests are not independent review and do not themselves close all 120
clause obligations. Every vertical includes a positive and a relevant falsation.
"""
from dataclasses import replace
from hashlib import sha256
import json
import pytest
from foundation_completion import scenario
from foundation_b02 import entity,cut,universe
from completion_support import body,changed
from guardian.domain.identity import EntityKind as K,Alias,AliasIndex,bind_alias,resolve_alias,RevisionId
from guardian.domain.outcomes import SourceStatus,MaterialStatus
from guardian.domain.references import resolve_entity,validate_references,EntityImport,TrustedEntityImports
from guardian.domain.source import (ApprovedSourceImport,SourceEntry,SourceExclusion,MissingSource,HistoryRole,
    validate_source_universe,describe_source_coverage)
from guardian.domain.authority import validate_decision
from guardian.domain.scope import (FactSet,ScopeWitness,DimensionObservation,DimensionValue,ValueKind,
    Atom,Operator,All,Any,Not,StepBudget,evaluate_scope)
from guardian.domain.evidence_logic import YES,NO,UNKNOWN,CONFLICT
from guardian.domain.scope_codec import encode_applicability_result,decode_applicability_result
from guardian.constitution.evaluator import evaluate_constitution,RuleVerdict,EvaluationBudget
from guardian.application.project_service import build_readonly_project_view
from guardian.application.contract_service import inspect_contract
from guardian.application.constitution_service import evaluate_project_constitution
from guardian.persistence.schema_registry import foundation_schema_registry,encode_record,decode_record


def product(req,registry):
    view=build_readonly_project_view(req.project,req.universe,{s.ref:s for s in req.view.sources},
        entities=tuple(r.identity for r in req.view.records))
    assert view.ok,view.diagnostics
    return evaluate_project_constitution(view.value,req.view,req.facts,req.profile,req.authority,
        registry,req.candidate_ref,budget=req.budget,dependencies=req.dependencies)


def test_G00_V01_two_isolated_projects_with_overlapping_aliases_and_scoped_import():
    a,reg,ai=scenario();b,_,bi=scenario('project-beta')
    alias=Alias('Contrato compartido')
    for req,ids in ((a,ai),(b,bi)):
        index=bind_alias(AliasIndex(),ids['obligation-now'],alias,req.view.sources[0].ref).index
        exact=resolve_alias(index,req.view.project_id,K.OBLIGATION,alias)
        assert exact.ok
        assert resolve_entity(exact.value,req.view,K.OBLIGATION).value.record==body(req,ids['obligation-now'])
    assert not resolve_entity(bi['obligation-now'],a.view,K.OBLIGATION).ok
    assert validate_decision(body(b,bi['decision-main']),a.authority).diagnostics[0].code=='AUTHORITY_POLICY_OR_PROJECT_MISMATCH'
    s=b.view.sources[0];grant=ApprovedSourceImport(a.view.project_id,s.ref,s.repository,s.path,ai['decision-main'],s)
    permitted=TrustedEntityImports((EntityImport(grant,frozenset({bi['property-main']}),b.view),))
    found=resolve_entity(bi['property-main'],a.view,K.PROPERTY,permitted)
    assert found.ok and found.value.imported
    assert not resolve_entity(bi['capability-one'],a.view,K.CAPABILITY,permitted).ok
    assert product(a,reg).value.aggregate_verdict is RuleVerdict.PASS


def test_G00_V02_foundational_specification_shares_properties_without_material_completion():
    req,_,ids=scenario();prop=body(req,ids['property-main'])
    for key in ('capability-one','capability-two'):
        cap=body(req,ids[key]);assert cap.property_refs==(prop.identity,)
        assert resolve_entity(cap.property_refs[0],req.view,K.PROPERTY).value.record is prop
    obligations=[body(req,ids[n]) for n in ('obligation-now','obligation-future','obligation-research')]
    assert len({o.identity for o in obligations})==3 and len({o.due for o in obligations})==3
    assert body(req,ids['verification-main']).material_status=='NOT_RUN'
    inspected=inspect_contract(ids['obligation-now'],req.view)
    assert inspected.ok and inspected.value.reference_validation.ok
    assert inspected.value.qualification=='NOT_CHECKED'
    assert not any(o.normatively_admitted for o in obligations)
    missing=replace(req.view,records=tuple(r for r in req.view.records if r.identity!=prop.identity))
    rejected=inspect_contract(ids['obligation-now'],missing)
    assert rejected.ok and not rejected.value.reference_validation.ok
    assert 'ORPHAN_REFERENCE' in {d.code for d in rejected.value.reference_validation.diagnostics}


def test_G00_V03_historical_overlaps_missing_sources_and_exclusions_do_not_certify_coverage():
    req,_,ids=scenario();p=req.project
    base=cut(p,'history-base',commit='1'*40);delta=cut(p,'history-delta',commit='2'*40);excluded=cut(p,'excluded-file',path='ignored.gsl')
    entries=(SourceEntry(base,HistoryRole.BASE,SourceStatus.CONTENT_OBSERVED,'lineage'),
        SourceEntry(delta,HistoryRole.DELTA,SourceStatus.IDENTIFIED,'lineage',base.ref),
        SourceEntry(excluded,HistoryRole.REFERENCE,SourceStatus.IDENTITY_VERIFIED,'excluded-lineage'))
    omission=SourceExclusion(excluded.ref,'documented not in contracted scope',ids['decision-main'])
    u=universe(p,(base,delta,excluded),entries=entries,included=(base.ref,delta.ref),excluded=(omission,),missing=(MissingSource('historic report','unavailable'),))
    catalog={x.ref:x for x in (base,delta,excluded)}
    result=validate_source_universe(u,p,catalog,trusted_exclusion_decisions=frozenset({ids['decision-main']}))
    assert not result.eligible_for_complete_claim and 'SOURCE_COVERAGE_UNKNOWN' in {d.code for d in result.diagnostics}
    description=describe_source_coverage(u)
    assert not description.source_population_disjoint and not description.coverage_qualified and description.known_missing
    # An unapproved deletion of the same source is an additional authority fault.
    untrusted=validate_source_universe(u,p,catalog)
    assert 'EXCLUSION_AUTHORITY_UNVERIFIED' in {d.code for d in untrusted.diagnostics}
    positive=universe(p,(base,),entries=(entries[0],))
    assert validate_source_universe(positive,p,{base.ref:base}).ok
    assert not describe_source_coverage(positive).coverage_qualified


def test_G00_V04_proposal_vs_external_approval_and_localized_normative_conflict():
    from guardian.domain.claims import Assertion,AssertionDomain
    from guardian.constitution.precedence import ConflictPolicies,detect_conflicts,DependencyView,localize_conflicts
    from guardian.domain.outcomes import DecisionStatus
    req,registry,ids=scenario();decision=body(req,ids['decision-main']);proposed=replace(decision,declared_status=DecisionStatus.PROPOSED)
    assert not validate_decision(proposed,None).value.authorized
    assert validate_decision(decision,req.authority).value.authorized
    a=Assertion(req.constitution.rule_refs[0],ids['property-main'],'requirement','exact',AssertionDomain.NORMATIVE,
        ids['scope-main'],(req.view.sources[0].ref,),decision.identity)
    b=replace(a,identity=req.constitution.rule_refs[1],value='inexact')
    req=replace(req,authority=replace(req.authority,assertion_pins=(a,b)))
    conflicts=detect_conflicts((a,b),req.profile,ConflictPolicies(req.view,req.facts.scope,req.authority))
    assert len(conflicts.conflicts)==1 and conflicts.conflicts[0].confirmed
    localized=localize_conflicts(conflicts.conflicts,DependencyView(req.view.project_id,((a.identity,ids['obligation-now']),)))
    assert ids['obligation-now'] in localized[0].blocked and ids['obligation-future'] not in localized[0].blocked
    assert set(conflicts.conflicts[0].witnesses)>={a.identity,b.identity}
    spoof=replace(req.authority,approvals=())
    assert not validate_decision(decision,spoof).ok


def test_G00_V05_four_values_nested_expressions_codec_and_resource_limit():
    req,_,ids=scenario();context=req.profile.context;s=req.view.sources[0].ref
    profile=replace(req.profile,dimensions=())
    expression=Atom('features',Operator.CONTAINS,DimensionValue(ValueKind.TEXT,'ready'))
    pos=ScopeWitness(context,s,'yes','ready observed');neg=ScopeWitness(context,s,'no','exhaustive empty set')
    yes=DimensionObservation('features','v1',DimensionValue(ValueKind.TEXT_SET,frozenset({'ready'})),(pos,))
    no=DimensionObservation('features','v1',DimensionValue(ValueKind.TEXT_SET,frozenset()),(neg,),True,(neg,))
    for observations,expected in (((),UNKNOWN),((yes,),YES),((no,),NO),((yes,no),CONFLICT)):
        facts=FactSet(context,frozenset({s}),observations)
        evaluation=evaluate_scope(expression,profile,facts)
        assert evaluation.ok and evaluation.result.value==expected
        assert decode_applicability_result(encode_applicability_result(evaluation.result)).value==evaluation.result
        double=evaluate_scope(Not(Not(expression)),profile,facts)
        assert double.result.value==expected
    contradictory=FactSet(context,frozenset({s}),(yes,no))
    nested=evaluate_scope(All((expression,Any((expression,Not(expression))))),profile,contradictory)
    assert nested.result.conflicts
    exhausted=evaluate_scope(expression,profile,contradictory,StepBudget(max_steps=1))
    assert not exhausted.ok and exhausted.result is None and exhausted.unexamined


def test_G00_V06_old_reader_rejects_unknown_meaning_but_preserves_informational_extension():
    req,_,ids=scenario();registry=foundation_schema_registry(req.view.revision)
    for key in ('objective-main','capability-one','property-main','obligation-now'):
        original=body(req,ids[key]);wire=encode_record(original,registry,informational_extensions=(('info.note','context only'),)).value
        returned=decode_record(json.dumps(wire).encode(),registry)
        assert returned.ok and type(returned.value.record) is type(original) and returned.value.record==original
        assert returned.value.informational_extensions==( ('info.note','context only'), )
        reader=replace(registry,reader_features=registry.reader_features-{'record.typed.v1'})
        assert not decode_record(wire,reader).ok
        wire['required_normative_features'].append('new.normative.feature')
        assert not decode_record(wire,registry).ok


def test_G00_V07_deterministic_end_to_end_complete_snapshot_and_rule_omission_attack():
    req,registry,ids=scenario();before=hash(req.view);positive=product(req,registry)
    assert positive.ok and positive.value.aggregate_verdict is RuleVerdict.PASS
    permuted=replace(req,view=replace(req.view,records=tuple(reversed(req.view.records))))
    assert product(permuted,registry).value==positive.value and hash(req.view)==before
    shortened=changed(req,replace(req.constitution,rule_refs=req.constitution.rule_refs[:-1]))
    attack=product(shortened,registry)
    assert attack.ok and attack.value.aggregate_verdict is not RuleVerdict.PASS
    assert 'NORMATIVE_BODY_MISMATCH' in {d.code for d in attack.value.diagnostics}
    limited=product(replace(req,budget=EvaluationBudget(max_rules=1)),registry)
    assert limited.ok and limited.value.aggregate_verdict is RuleVerdict.RESOURCE_LIMITED
    assert len(limited.value.rule_results)==9 and len(limited.value.unexamined_rule_ids)==8
