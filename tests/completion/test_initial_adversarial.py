"""Falsations authored before correcting the integrated implementation."""
from dataclasses import replace
import pytest
from foundation_completion import scenario
from completion_support import body,changed
from guardian.domain.authority import DecisionRevision,ApprovalPolicyRequirement,ActionKind
from guardian.domain.scope import FactSet
from guardian.constitution.evaluator import evaluate_constitution,EvaluationBudget,RuleVerdict,RuleEvaluation,collect_constitution_report


def test_total_budget_counts_decision_and_requirement_scope_evaluations():
    req,registry,_=scenario()
    # Exactly the previously reported steps fit only because authorization and
    # requirement evaluations were omitted from accounting.
    r=evaluate_constitution(replace(req,budget=EvaluationBudget(max_steps=135)),registry)
    assert r.aggregate_verdict is RuleVerdict.RESOURCE_LIMITED
    assert r.steps<=135
    assert len(r.rule_results)==9


def test_no_rule_can_manufacture_superseded_without_evidence():
    req,registry,_=scenario();good=evaluate_constitution(req,registry)
    with pytest.raises(ValueError):
        replace(good.rule_results[0],verdict=RuleVerdict.SUPERSEDED,positive_witnesses=(),examined=False)


def test_typed_report_cannot_store_mutable_diagnostics_or_wrong_verdict():
    req,registry,_=scenario();good=evaluate_constitution(req,registry)
    with pytest.raises(TypeError):replace(good,diagnostics=[])
    with pytest.raises(TypeError):replace(good,aggregate_verdict='PASS')


def test_atomic_facts_preserve_conflicting_requirement_witnesses():
    from guardian.domain.scope import DimensionObservation,DimensionValue,ValueKind,ScopeWitness
    req,registry,_=scenario();s=req.view.sources[0].ref
    negative=ScopeWitness(req.profile.context,s,'negative','complete inventory excludes ready')
    fact=DimensionObservation('features','v1',DimensionValue(ValueKind.TEXT_SET,frozenset()),(negative,),True,(negative,))
    # Use another scope for the applicability, so the conflict is in the rule's
    # requirement, not its applicability expression.
    from guardian.domain.scope import ScopeRevision,Atom,Operator
    from foundation_b02 import entity
    from guardian.domain.identity import EntityKind as K
    always=replace(req.view._by_ref[req.constitution.scope_ref],identity=entity(req.view.project_id,K.SCOPE,'scope-known'),
        expression=Atom('features',Operator.PRESENT))
    rules=[replace(r,applicability_ref=always.identity) for r in req.view.records if r.identity.kind is K.RULE]
    req=changed(req,always,*rules,operator_repin=True)
    # Approval scope is also moved to the uncontested presence expression.
    dec=body(req,req.constitution.decision_refs[0]);dec=replace(dec,scope_ref=always.identity,action=replace(dec.action,scope_ref=always.identity))
    req=changed(req,dec,operator_repin=True)
    req=replace(req,constitution=replace(req.constitution,approval_requirements=tuple(replace(r,scopes=frozenset({always.identity})) for r in req.constitution.approval_requirements)))
    req=changed(req,req.constitution,operator_repin=True)
    req=replace(req,authority=replace(req.authority,requirements=tuple(replace(r,scopes=frozenset({always.identity})) for r in req.authority.requirements),
        grants=tuple(replace(g,scope_refs=frozenset({always.identity})) for g in req.authority.grants)),
        facts=replace(req.facts,scope=replace(req.facts.scope,dimensions=(fact,))))
    result=evaluate_constitution(req,registry)
    row=next(r for r in result.rule_results if r.evaluator_id=='scope.four_valued.v1')
    assert row.verdict is RuleVerdict.CONFLICT
    assert row.positive_witnesses and row.negative_witnesses


def test_pinned_rule_cannot_be_weakened_by_replacing_its_scope_body_at_same_revision():
    from guardian.domain.scope import Atom,Operator,DimensionValue,ValueKind
    req,registry,ids=scenario();scope=body(req,ids['scope-main'])
    # Keep all IDs/revisions and external expectations unchanged while rewriting
    # the dependent norm. The changed input must not earn structural PASS.
    changed_scope=replace(scope,expression=Atom('features',Operator.PRESENT))
    report=evaluate_constitution(changed(req,changed_scope),registry)
    assert report.aggregate_verdict is not RuleVerdict.PASS
    assert any(d.code=='NORMATIVE_BODY_MISMATCH' for row in report.rule_results for d in row.diagnostics)
