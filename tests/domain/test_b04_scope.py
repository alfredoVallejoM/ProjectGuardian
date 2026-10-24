"""Original G00-06 F01..F10, APIs 031..038 and ADV-16..20.

Expected tables are independently enumerated; tests do not derive expectations
by calling the scalar algebra used by the implementation.
"""
from dataclasses import FrozenInstanceError, replace
import itertools
import json
import pytest
from foundation_b04 import fixture, witness, observation, contains, scoped_fixture
from foundation_b02 import entity
from guardian.domain.identity import EntityKind as K, RevisionId, ContentDigest, DigestAlgorithm
from guardian.domain.evidence_logic import UNKNOWN, YES, NO, CONFLICT
from guardian.domain.scope import *
from guardian.domain.scope_codec import encode_applicability_result, decode_applicability_result

VALUES=(UNKNOWN,YES,NO,CONFLICT)
AND=((0,0,2,2),(0,1,2,3),(2,2,2,2),(2,3,2,3))
OR=((0,1,0,1),(1,1,1,1),(0,1,2,3),(1,1,3,3))


def evidence(i, profile, source, label):
    w=witness(profile,source,label)
    ds=() if i!=3 else (Diagnostic('APPLICABILITY_CONFLICT','$.'+label,'consistent evidence','both','opposing evidence'),)
    return ApplicabilityResult(profile.context, VALUES[i], (w,) if VALUES[i].positive else (),
        (w,) if VALUES[i].negative else (), ds)


def run(expr, observations=(), profile=None, facts=None, budget=StepBudget()):
    _,s,_,_,_,_,p,f=fixture()
    p=profile or p; f=facts or replace(f, dimensions=observations)
    return evaluate_scope(expr,p,f,budget)


def test_f01_profile_is_typed_versioned_and_unknown_dimensions_are_explicit():
    *_,profile,facts=fixture()
    assert validate_support_profile(profile).ok
    assert 'features' in profile.unknown_dimensions and 'platform' in profile.unknown_dimensions
    assert evaluate_scope(contains(),profile,facts).result.value==UNKNOWN
    with pytest.raises(ValueError,match='UNKNOWN_NORMATIVE_DIMENSION'):
        replace(profile,required_dimensions=('future.normative-law',))
    assert replace(profile,informational=(('info.label',DimensionValue(ValueKind.TEXT,'note')),))
    with pytest.raises(TypeError,match='INVALID_INFORMATIONAL'):
        replace(profile,informational=(('normative.new-law',DimensionValue(ValueKind.TEXT,'note')),))
    with pytest.raises(ValueError,match='REGISTRY_REVISION'):
        replace(profile,registry=replace(profile.registry,revision=RevisionId('rev-'+'1'*32)))


@pytest.mark.parametrize('kind,value',[(ValueKind.INTEGER,True),(ValueKind.INTEGER,1.0),(ValueKind.TEXT_SET,{'x'}),
    (ValueKind.BOOLEAN,1),(ValueKind.TEXT,False),(ValueKind.TEXT_SET,frozenset({3}))])
def test_f01_dimension_types_do_not_coerce_values(kind,value):
    with pytest.raises((TypeError,ValueError)):
        DimensionValue(kind,value)


def test_f02_ast_arity_types_and_registered_operators():
    for constructor in (All,Any):
        with pytest.raises(ValueError,match='INVALID_SCOPE_ARITY'):
            constructor(())
        with pytest.raises(ValueError):
            constructor([contains()])
    with pytest.raises(TypeError,match='UNSAFE_SCOPE_PREDICATE'):
        Atom('features','eval','__import__("os")')
    *_,profile,facts=fixture()
    bad=Atom('features',Operator.EQUALS,DimensionValue(ValueKind.TEXT,'wrong type'))
    result=evaluate_scope(bad,profile,facts)
    assert result.status is EvaluationStatus.INVALID_INPUT and result.result is None
    assert result.diagnostics[0].code=='INVALID_PREDICATE_TYPE'
    unknown=Atom('future.dimension',Operator.PRESENT)
    assert validate_scope_expression(unknown,profile.registry).diagnostics[0].code=='UNKNOWN_NORMATIVE_DIMENSION'


@pytest.mark.parametrize('i',range(4))
def test_f03_all_four_values_preserve_typed_context_and_witnesses_in_roundtrip(i):
    _,source,_,_,_,_,profile,_=fixture()
    result=evidence(i,profile,source,'witness-main')
    wire=json.loads(json.dumps(encode_applicability_result(result)))
    recovered=decode_applicability_result(wire)
    assert recovered.ok and recovered.value==result
    assert recovered.value.profile_revision==profile.context.profile_revision
    assert recovered.value.policy_revision==profile.context.verification_policy_ref.revision
    assert bool(recovered.value.positive_witnesses)==VALUES[i].positive
    assert bool(recovered.value.negative_witnesses)==VALUES[i].negative
    wire['unexpected_normative_field']=True
    assert not decode_applicability_result(wire).ok


@pytest.mark.parametrize('left,right',itertools.product(range(4),repeat=2))
def test_f04_f05_exact_support_tables_and_contributing_witnesses(left,right):
    _,source,_,_,_,_,profile,_=fixture()
    a,b=evidence(left,profile,source,'left'),evidence(right,profile,source,'right')
    conjunction=and_evidence(a,b); disjunction=or_evidence(a,b)
    assert conjunction.value==VALUES[AND[left][right]]
    assert disjunction.value==VALUES[OR[left][right]]
    assert bool(conjunction.positive_witnesses)==conjunction.value.positive
    assert bool(conjunction.negative_witnesses)==conjunction.value.negative
    if left==3 or right==3:
        assert any(d.code=='APPLICABILITY_CONFLICT' for d in conjunction.diagnostics)
        assert any(d.code=='APPLICABILITY_CONFLICT' for d in disjunction.diagnostics)
    assert negate_evidence(a).value==VALUES[(0,2,1,3)[left]]
    assert negate_evidence(a).positive_witnesses==a.negative_witnesses
    assert negate_evidence(a).negative_witnesses==a.positive_witnesses


@pytest.mark.parametrize('present,complete,expected',[(True,False,YES),(True,True,YES),(False,False,UNKNOWN),(False,True,NO)])
def test_f06_complete_sets_not_missing_data_can_supply_negative_witness(present,complete,expected):
    _,s,_,_,_,_,p,f=fixture()
    obs=observation(p,s,('feature-x',) if present else ('other-feature',),complete)
    result=evaluate_scope(contains(),p,replace(f,dimensions=(obs,)))
    assert result.ok and result.result.value==expected
    assert bool(result.result.negative_witnesses)==expected.negative


def test_f06_completeness_needs_its_own_witness_and_is_not_a_boolean_claim():
    _,s,_,_,_,_,p,f=fixture();obs=observation(p,s,())
    with pytest.raises(ValueError,match='INVALID_SCOPE_WITNESSES'):
        replace(obs,complete=True)
    empty_known=replace(obs,complete=True,completeness_witnesses=obs.witnesses)
    assert evaluate_scope(contains(),p,replace(f,dimensions=(empty_known,))).result.value==NO
    missing=DimensionObservation('features','v1',None,())
    assert evaluate_scope(contains(),p,replace(f,dimensions=(missing,))).result.value==UNKNOWN


def test_f06_incomplete_set_equality_is_not_promoted_to_yes():
    _,s,_,_,_,_,p,f=fixture();obs=observation(p,s)
    equal=Atom('features',Operator.EQUALS,DimensionValue(ValueKind.TEXT_SET,frozenset({'feature-x'})))
    assert evaluate_scope(equal,p,replace(f,dimensions=(obs,))).result.value==UNKNOWN
    other=replace(equal,operand=DimensionValue(ValueKind.TEXT_SET,frozenset({'other'})))
    assert evaluate_scope(other,p,replace(f,dimensions=(obs,))).result.value==NO
    assert evaluate_scope(equal,p,replace(f,dimensions=(replace(obs,complete=True,completeness_witnesses=obs.witnesses),))).result.value==YES


def test_f07_applicability_does_not_promote_future_to_current_or_approve():
    from guardian.domain.campaign import inspect_due
    from guardian.domain.outcomes import DueStatus
    _,_,records,_,_,_,profile,facts,scope=scoped_fixture()
    future=records[6]
    result=inspect_due(future,'m1',profile,facts=facts,scope_record=scope)
    assert result.ok and result.value.applicability=='YES'
    assert result.value.declared_due is DueStatus.FUTURE
    assert result.value.admission=='NOT_CHECKED' and result.value.normatively_due is None
    assert future.due is DueStatus.FUTURE
    wrong=inspect_due(future,'m2',profile,facts=facts,scope_record=scope)
    assert not wrong.ok and wrong.diagnostics[0].code=='DUE_SCOPE_CONTEXT_MISMATCH'


def test_f08_external_predicate_is_not_executed_and_requires_matching_verified_input():
    _,s,_,_,_,_,p,f=fixture()
    predicate=VerifierPredicate(entity(p.project_id,K.VERIFICATION,'check-axiom'),
        ContentDigest(DigestAlgorithm.SHA256,'a'*64),'v1')
    result=evaluate_scope(predicate,p,f)
    assert result.ok and result.result.value==UNKNOWN
    assert result.diagnostics[0].code=='MISSING_VERIFIED_OBSERVATION'
    obs=VerifiedPredicateObservation(predicate,p.context,(witness(p,s),),())
    assert evaluate_scope(predicate,p,replace(f,verified_predicates=(obs,))).result.value==YES
    wrong=replace(predicate,input_contract=ContentDigest(DigestAlgorithm.SHA256,'b'*64))
    assert evaluate_scope(wrong,p,replace(f,verified_predicates=(obs,))).result.value==UNKNOWN
    obs2=VerifiedPredicateObservation(predicate,p.context,(),(witness(p,s,'opposite'),))
    both=evaluate_scope(predicate,p,replace(f,verified_predicates=(obs,obs2)))
    assert both.result.value==CONFLICT


@pytest.mark.parametrize('field,amount',[('max_steps',1),('max_nodes',1),('max_depth',1),('max_facts',1),('max_witnesses',1)])
def test_f09_budget_exhaustion_has_no_applicability_value(field,amount):
    _,s,_,_,_,_,p,f=fixture()
    f=replace(f,dimensions=(observation(p,s),observation(p,s,(),True,'other-source')))
    tree=All((contains(),Not(contains('other'))))
    result=evaluate_scope(tree,p,f,replace(StepBudget(),**{field:amount}))
    assert result.status is EvaluationStatus.RESOURCE_LIMITED and not result.ok
    assert result.result is None and result.unexamined
    assert result.diagnostics[0].code=='EVALUATION_RESOURCE_LIMITED'


@pytest.mark.parametrize('field,value',[('profile_revision',RevisionId('rev-'+'1'*32)),
    ('project_revision',RevisionId('rev-'+'2'*32)),('milestone','m2'),
    ('registry_revision',RevisionId('rev-'+'3'*32))])
def test_f10_evidence_from_another_profile_context_is_rejected(field,value):
    _,s,_,_,_,_,p,f=fixture()
    foreign_context=replace(p.context,**{field:value})
    other=replace(f,context=foreign_context)
    result=evaluate_scope(contains(),p,other)
    assert not result.ok and result.result is None
    assert result.diagnostics[0].code=='EVIDENCE_CONTEXT_MISMATCH'
    w=replace(witness(p,s),context=foreign_context)
    with pytest.raises(ValueError,match='EVIDENCE_CONTEXT_MISMATCH'):
        replace(p,dimensions=(replace(observation(p,s),witnesses=(w,)),))


def test_f10_foreign_source_and_unknown_catalog_are_not_silently_accepted():
    _,s,_,_,_,_,p,f=fixture();other=fixture('project-beta')
    with pytest.raises(ValueError,match='WITNESS_PROJECT_MISMATCH'):
        replace(witness(p,s),source_ref=other[1].ref)
    result=evaluate_scope(contains(),replace(p,dimensions=(observation(p,s),)),replace(f,source_refs=frozenset()))
    assert not result.ok and result.diagnostics[0].code=='EVIDENCE_SOURCE_OUTSIDE_CATALOG'


def test_internal_conflicts_survive_and_no_short_circuit_hides_them():
    _,s,_,_,_,_,p,f=fixture()
    f=replace(f,dimensions=(observation(p,s),observation(p,s,(),True,'negative')))
    decision=entity(p.project_id,K.DECISION,'constant-policy')
    f=replace(f,constant_authorizations=(ConstantAuthorization(decision,witness(p,s,'policy'),True,True),))
    for tree,expected in ((All((contains(),FalseConst(decision))),NO), (Any((contains(),TrueConst(decision))),YES)):
        r=evaluate_scope(tree,p,f)
        assert r.ok and r.result.value==expected
        assert any(t.result.value==CONFLICT for t in r.trace)
        assert any(d.code=='APPLICABILITY_CONFLICT' for d in r.diagnostics)


def test_explicit_constants_require_scoped_authorization_not_empty_all():
    _,s,_,_,_,_,p,f=fixture();decision=entity(p.project_id,K.DECISION,'constant-policy')
    for expression in (TrueConst(decision),FalseConst(decision)):
        r=evaluate_scope(expression,p,f)
        assert not r.ok and r.result is None and r.diagnostics[0].code=='CONSTANT_NOT_AUTHORIZED'
    only_true=ConstantAuthorization(decision,witness(p,s,'policy'),True,False)
    f=replace(f,constant_authorizations=(only_true,))
    assert evaluate_scope(TrueConst(decision),p,f).result.value==YES
    assert not evaluate_scope(FalseConst(decision),p,f).ok


@pytest.mark.parametrize('value,lower,upper,expected',[(10,0,10,YES),(11,0,10,NO),(-3,-4,-2,YES),(2**120,0,2**119,NO)])
def test_exact_integer_range_and_presence_are_typed(value,lower,upper,expected):
    _,s,_,_,_,_,p,f=fixture()
    obs=DimensionObservation('resources.memory_bytes','v1',DimensionValue(ValueKind.INTEGER,value),(witness(p,s),))
    f=replace(f,dimensions=(obs,))
    expr=Atom('resources.memory_bytes',Operator.IN_RANGE,IntegerRange(lower,upper))
    assert evaluate_atom(expr,p,f).result.value==expected
    assert evaluate_scope(Atom('resources.memory_bytes',Operator.PRESENT),p,f).result.value==YES


def test_input_permutation_does_not_mutate_or_select_first_witness():
    _,s,_,_,_,_,p,f=fixture()
    observations=(observation(p,s),observation(p,s,(),True,'negative'))
    first=replace(f,dimensions=observations);second=replace(f,dimensions=tuple(reversed(observations)))
    before=(hash(p),hash(first),hash(second))
    a=evaluate_scope(Not(contains()),p,first);b=evaluate_scope(Not(contains()),p,second)
    assert a==b and a.result.value==CONFLICT
    assert before==(hash(p),hash(first),hash(second))
    with pytest.raises(FrozenInstanceError):
        first.dimensions=()


def test_deep_and_cyclic_scope_inputs_fail_closed_without_python_recursion():
    *_,p,f=fixture();expr=contains()
    for _ in range(1000):expr=Not(expr)
    r=evaluate_scope(expr,p,f)
    assert r.status is EvaluationStatus.RESOURCE_LIMITED and r.result is None
    cycle=Not(contains());object.__setattr__(cycle,'expression',cycle)
    r=evaluate_scope(cycle,p,f)
    assert r.status is EvaluationStatus.INVALID_INPUT and r.diagnostics[0].code=='CYCLIC_SCOPE_EXPRESSION'
    class Bomb:
        def __call__(self):raise AssertionError('project callback executed')
        def __eq__(self,other):raise AssertionError('project equality executed')
    r=evaluate_scope(Bomb(),p,f)
    assert r.status is EvaluationStatus.INVALID_INPUT and r.diagnostics[0].code=='UNSAFE_SCOPE_PREDICATE'


@pytest.mark.parametrize('patch',[{'max_steps':True},{'max_nodes':0},{'max_depth':65},{'max_facts':-1}])
def test_budget_policy_is_explicit_and_non_coercing(patch):
    with pytest.raises(ValueError,match='INVALID_EVALUATION_BUDGET'):
        StepBudget(**patch)
