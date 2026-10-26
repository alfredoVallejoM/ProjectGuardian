"""G00-10/F01..F10: complete denominator, pure execution and exact authority."""
from dataclasses import replace
import ast
from pathlib import Path
import random
import pytest
from foundation_completion import scenario
from foundation_b02 import entity
from completion_support import body,changed
from guardian.domain.identity import EntityKind as K,RevisionId
from guardian.domain.scope import Atom,Operator,DimensionValue,ValueKind
from guardian.domain.constitution import RulePredicate,KNOWN_RULES
from guardian.constitution.evaluator import (evaluate_constitution,collect_constitution_report,
    evaluate_registered_rule,EvaluationBudget,RuleVerdict)
from guardian.constitution.invariants import TrustedRuleEvaluatorRegistry


def test_all_nine_structural_evaluators_are_exercised_in_real_valid_snapshot():
    req,reg,_=scenario();report=evaluate_constitution(req,reg)
    assert report.aggregate_verdict is RuleVerdict.PASS
    assert {r.evaluator_id for r in report.rule_results}==KNOWN_RULES
    assert all(r.examined and r.positive_witnesses for r in report.rule_results)
    assert set(report.examined_rule_ids)==set(req.constitution.rule_refs)
    assert not report.unexamined_rule_ids and not report.normatively_admitted


@pytest.mark.parametrize('index',range(9))
def test_each_required_rule_missing_body_stays_in_denominator(index):
    req,reg,_=scenario();ref=req.constitution.rule_refs[index]
    req=replace(req,view=replace(req.view,records=tuple(r for r in req.view.records if r.identity!=ref)))
    report=evaluate_constitution(req,reg)
    assert len(report.rule_results)==9 and report.aggregate_verdict is not RuleVerdict.PASS
    row=next(x for x in report.rule_results if x.rule_ref==ref)
    assert not row.examined and row.diagnostics[0].code=='ORPHAN_REFERENCE'


@pytest.mark.parametrize('index',range(9))
def test_unknown_kind_never_disappears_even_if_other_rules_pass(index):
    req,reg,_=scenario();r=body(req,req.constitution.rule_refs[index])
    new=replace(r,rule_kind='future.unknown.v9',predicate=RulePredicate('future.unknown.v9'))
    req=changed(req,new,operator_repin=True)
    report=evaluate_constitution(req,reg)
    assert len(report.rule_results)==9
    row=next(x for x in report.rule_results if x.rule_ref==new.identity)
    assert row.verdict is RuleVerdict.UNKNOWN and row.diagnostics[0].code=='UNKNOWN_RULE_KIND'
    assert report.aggregate_verdict is not RuleVerdict.PASS


@pytest.mark.parametrize('field',['rule','constitution','policy'])
def test_candidate_cannot_weaken_fixed_normative_bodies_at_same_revision(field):
    req,reg,_=scenario()
    if field=='rule':
        old=body(req,req.constitution.rule_refs[0]);req=changed(req,replace(old,rationale='silent edit'))
    elif field=='constitution':req=changed(req,replace(req.constitution,rule_refs=req.constitution.rule_refs[:-1]))
    else:reg=replace(reg,policy_ref=entity(req.view.project_id,K.SOURCE_POLICY,'other-policy'))
    result=evaluate_constitution(req,reg)
    assert result.aggregate_verdict is not RuleVerdict.PASS
    assert any(d.code in {'NORMATIVE_BODY_MISMATCH','EVALUATION_CONTEXT_MISMATCH'}
               for d in result.diagnostics+tuple(d for r in result.rule_results for d in r.diagnostics))


@pytest.mark.parametrize('max_rules',[0,1,4,8])
def test_rule_budget_keeps_every_unexamined_rule_without_false_pass(max_rules):
    req,reg,_=scenario();report=evaluate_constitution(replace(req,budget=EvaluationBudget(max_rules=max_rules)),reg)
    assert report.aggregate_verdict is RuleVerdict.RESOURCE_LIMITED
    assert len(report.rule_results)==9 and len(report.unexamined_rule_ids)==9-max_rules
    assert all(r.verdict is RuleVerdict.RESOURCE_LIMITED for r in report.rule_results[max_rules:])


@pytest.mark.parametrize('steps',[0,1,30,135,300])
def test_global_steps_are_an_upper_bound_not_a_partial_success_counter(steps):
    req,reg,_=scenario();report=evaluate_constitution(replace(req,budget=EvaluationBudget(max_steps=steps)),reg)
    assert report.aggregate_verdict is RuleVerdict.RESOURCE_LIMITED
    assert report.steps<=steps and len(report.rule_results)==9 and report.unexamined_rule_ids


def test_exact_measured_budget_succeeds_and_one_less_never_does():
    req,reg,_=scenario();baseline=evaluate_constitution(req,reg)
    exact=evaluate_constitution(replace(req,budget=EvaluationBudget(max_steps=baseline.steps)),reg)
    assert exact.aggregate_verdict is RuleVerdict.PASS and exact.steps==baseline.steps
    short=evaluate_constitution(replace(req,budget=EvaluationBudget(max_steps=baseline.steps-1)),reg)
    assert short.aggregate_verdict is RuleVerdict.RESOURCE_LIMITED


@pytest.mark.parametrize('attack',['missing','duplicate','extra'])
def test_collector_rejects_rule_omission_even_when_all_supplied_results_are_pass(attack):
    req,reg,_=scenario();good=evaluate_constitution(req,reg);rows=good.rule_results
    if attack=='missing':rows=rows[:-1]
    if attack=='duplicate':rows=rows+(rows[0],)
    if attack=='extra':rows=rows+(replace(rows[0],rule_ref=entity(req.view.project_id,K.RULE,'extra-rule')),)
    report=collect_constitution_report(req.constitution.rule_refs,rows,req.constitution.identity,req.constitution.policy_ref,req.candidate_ref)
    assert report.aggregate_verdict is not RuleVerdict.PASS
    assert 'RULE_SET_INCOMPLETE' in {d.code for d in report.diagnostics}
    assert len(report.rule_results)==9


def test_unknown_applicability_does_not_exclude_a_required_rule():
    req,reg,ids=scenario();old=body(req,ids['scope-main'])
    scope=replace(old,identity=entity(req.view.project_id,K.SCOPE,'unknown-applicability'),
        expression=Atom('platform',Operator.EQUALS,DimensionValue(ValueKind.TEXT,'linux')))
    rule=replace(body(req,req.constitution.rule_refs[0]),applicability_ref=scope.identity)
    report=evaluate_constitution(changed(req,scope,rule,operator_repin=True),reg)
    row=next(x for x in report.rule_results if x.rule_ref==rule.identity)
    assert row.verdict is RuleVerdict.UNKNOWN and row.diagnostics[0].code=='APPLICABILITY_UNKNOWN'
    assert len(report.rule_results)==9


def test_not_applicable_requires_negative_scope_witness():
    req,reg,ids=scenario();old=body(req,ids['scope-main'])
    scope=replace(old,identity=entity(req.view.project_id,K.SCOPE,'negative-applicability'),
        expression=Atom('features',Operator.CONTAINS,DimensionValue(ValueKind.TEXT,'absent-feature')))
    rule=replace(body(req,req.constitution.rule_refs[0]),applicability_ref=scope.identity)
    report=evaluate_constitution(changed(req,scope,rule,operator_repin=True),reg)
    row=next(x for x in report.rule_results if x.rule_ref==rule.identity)
    assert row.verdict is RuleVerdict.NOT_APPLICABLE and row.applicability.result.negative_witnesses
    assert report.aggregate_verdict is RuleVerdict.PASS


def test_constitution_precondition_is_preserved_and_no_rule_removed_when_unknown():
    req,reg,ids=scenario();scope=replace(body(req,ids['scope-main']),identity=entity(req.view.project_id,K.SCOPE,'unknown-precondition'),
        expression=Atom('platform',Operator.PRESENT))
    constitution=replace(req.constitution,precondition_refs=(scope.identity,))
    req=changed(req,scope,constitution,operator_repin=True)
    result=evaluate_constitution(req,reg)
    assert result.aggregate_verdict is RuleVerdict.UNKNOWN and len(result.unexamined_rule_ids)==9
    assert len(result.rule_results)==9


def test_empty_observations_never_prove_architecture_status_or_non_erasure():
    req,reg,_=scenario()
    empty=replace(req.facts,architectures=(),status_pairs=(),reference_sets=(),assertions_complete=False)
    result=evaluate_constitution(replace(req,facts=empty),reg)
    assert result.aggregate_verdict is RuleVerdict.UNKNOWN
    assert {r.evaluator_id for r in result.rule_results if r.verdict is RuleVerdict.UNKNOWN}>={
        'status.axis_separation.v1','architecture.dependencies_declared.v1','normative.non_erasure_precheck.v1','authority.conflict_localization.v1'}


def test_contradictory_complete_and_partial_architecture_observations_are_conflict():
    req,reg,_=scenario();a=req.facts.architectures[0]
    bad=replace(a,dependencies=(('domain','application'),),complete=False)
    report=evaluate_constitution(replace(req,facts=replace(req.facts,architectures=(a,bad))),reg)
    row=next(x for x in report.rule_results if x.evaluator_id=='architecture.dependencies_declared.v1')
    assert row.verdict is RuleVerdict.CONFLICT and row.positive_witnesses and row.negative_witnesses


def test_erasure_precheck_reports_loss_without_rewriting_obligation_universe():
    req,reg,ids=scenario();fact=req.facts.reference_sets[0]
    result=evaluate_constitution(replace(req,facts=replace(req.facts,reference_sets=(replace(fact,after=fact.after-{ids['obligation-now']}),))),reg)
    row=next(r for r in result.rule_results if r.evaluator_id=='normative.non_erasure_precheck.v1')
    assert row.verdict is RuleVerdict.FAIL and row.diagnostics[0].code=='NORMATIVE_REFERENCE_ERASURE'
    assert result.aggregate_verdict is RuleVerdict.FAIL
    assert ids['obligation-now'] in req.view._by_ref


def test_canonical_determinism_under_map_and_record_permutation_without_input_mutation():
    req,reg,_=scenario();before=hash(req.view);expected=evaluate_constitution(req,reg)
    for seed in range(10):
        records=list(req.view.records);random.Random(seed).shuffle(records)
        shuffled=replace(req,view=replace(req.view,records=tuple(records)))
        actual=evaluate_constitution(shuffled,reg)
        assert actual==expected
    assert hash(req.view)==before


def test_pure_evaluator_never_uses_wallclock_filesystem_environment_or_network(monkeypatch):
    req,reg,_=scenario()
    import builtins,time,os,socket
    def forbidden(*args,**kwargs):raise AssertionError('IMPURE_EVALUATION')
    # All input construction and module loading occur before trapping effects.
    expected=evaluate_constitution(req,reg)
    for module,name in ((builtins,'open'),(time,'time'),(time,'monotonic'),(os,'getenv'),(socket,'socket')):
        monkeypatch.setattr(module,name,forbidden)
    assert evaluate_constitution(req,reg)==expected


def test_trusted_registry_cannot_receive_a_project_callback():
    req,reg,_=scenario();called=[]
    def callback():called.append(True);return True
    with pytest.raises((TypeError,ValueError)):replace(reg,identifiers=frozenset({callback}))
    with pytest.raises((TypeError,ValueError)):RulePredicate(callback)
    assert not called
    report=evaluate_constitution(req,{'callback':callback})
    assert report.aggregate_verdict is RuleVerdict.INVALID_INPUT
    assert not called


def test_domain_and_constitution_layers_do_not_import_shell_or_persistence():
    root=Path(__file__).resolve().parents[2]/'src/guardian';bad=[]
    forbidden=('guardian.application','guardian.persistence','guardian.adapters')
    for folder in ('domain','constitution'):
        for path in (root/folder).glob('*.py'):
            for node in ast.walk(ast.parse(path.read_text())):
                names=([node.module] if isinstance(node,ast.ImportFrom) and node.module else
                       [alias.name for alias in node.names] if isinstance(node,ast.Import) else [])
                if any(n.startswith(forbidden) for n in names):bad.append((str(path),node.lineno))
    assert not bad,bad
