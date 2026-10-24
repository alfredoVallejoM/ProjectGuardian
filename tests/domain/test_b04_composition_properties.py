"""Independent table oracle versus real scoped observations, not product bits."""
from dataclasses import replace
import itertools
from pathlib import Path
import ast
import pytest
from foundation_b02 import entity
from foundation_b04 import fixture, observation, contains, witness
from guardian.domain.identity import EntityKind as K, RevisionId
from guardian.domain.evidence_logic import UNKNOWN, YES, NO, CONFLICT
from guardian.domain.scope import (All, Any, Not, ScopeWitness, ApplicabilityResult,
    DimensionValue, ValueKind, Operator, Atom, DimensionObservation,
    ProfileDimensionSchema, DimensionRegistry, SupportProfile, StepBudget,
    EvaluationStatus, evaluate_scope, validate_support_profile, validate_scope_expression)
from guardian.domain.scope_codec import encode_applicability_result, decode_applicability_result

# Truth tables stated independently of the runtime's bit operations.
AND=((0,0,2,2),(0,1,2,3),(2,2,2,2),(2,3,2,3))
OR=((0,1,0,1),(1,1,1,1),(0,1,2,3),(1,1,3,3))
NEG=(0,2,1,3)
VALUES=(UNKNOWN,YES,NO,CONFLICT)


def observed(profile,source,states):
    rows=[]
    for key,state in zip(('alpha','beta','gamma'),states):
        if state in (1,3):
            rows.append(DimensionObservation(key,'v1',DimensionValue(ValueKind.BOOLEAN,True),
                                             (witness(profile,source,key+'-positive'),)))
        if state in (2,3):
            rows.append(DimensionObservation(key,'v1',DimensionValue(ValueKind.BOOLEAN,False),
                                             (witness(profile,source,key+'-negative'),)))
    return tuple(rows)


@pytest.mark.parametrize('states',itertools.product(range(4),repeat=3))
def test_all_64_scoped_valuations_match_independent_nested_tables(states):
    _,source,_,_,_,_,p,f=fixture()
    registry=DimensionRegistry(p.registry.revision,tuple(ProfileDimensionSchema(n,'v1',ValueKind.BOOLEAN,
                              frozenset({Operator.EQUALS,Operator.PRESENT})) for n in ('alpha','beta','gamma')))
    p=replace(p,registry=registry)
    f=replace(f,dimensions=observed(p,source,states))
    a,b,c=(Atom(n,Operator.EQUALS,DimensionValue(ValueKind.BOOLEAN,True)) for n in ('alpha','beta','gamma'))
    x,y,z=states
    expressions=(
      (Not(All((a,Any((b,c))))),NEG[AND[x][OR[y][z]]]),
      (Any((All((a,b)),Not(c))),OR[AND[x][y]][NEG[z]]),
      (Not(Not(a)),x),
      (All((a,b,c)),AND[AND[x][y]][z]),
      (Any((a,b,c)),OR[OR[x][y]][z]),
    )
    before=hash(p),hash(f)
    for expr,expected in expressions:
        report=evaluate_scope(expr,p,f)
        assert report.ok and report.result.value==VALUES[expected]
        assert len(report.trace)==report.nodes and report.trace[-1].result==report.result
        assert all(w.context==p.context for w in report.result.positive_witnesses+report.result.negative_witnesses)
        assert decode_applicability_result(encode_applicability_result(report.result)).value==report.result
        if 3 in states and expr is not expressions[2][0]:
            assert report.result.conflicts
        permuted=evaluate_scope(expr,p,replace(f,dimensions=tuple(reversed(f.dimensions))))
        assert permuted==report
    assert before==(hash(p),hash(f))


def test_registered_extension_works_without_a_second_evaluator_or_plugins():
    _,source,_,_,_,_,p,f=fixture()
    schema=ProfileDimensionSchema('enterprise.batch','v2',ValueKind.INTEGER,
                                   frozenset({Operator.EQUALS,Operator.PRESENT}))
    registry=DimensionRegistry(p.registry.revision,p.registry.schemas+(schema,))
    p=replace(p,registry=registry,required_dimensions=('enterprise.batch',))
    observed=DimensionObservation(schema.name,'v2',DimensionValue(ValueKind.INTEGER,17),(witness(p,source),))
    expr=Atom(schema.name,Operator.EQUALS,DimensionValue(ValueKind.INTEGER,17))
    assert evaluate_scope(expr,p,replace(f,dimensions=(observed,))).result.value==YES
    wrong=replace(observed,version='v1')
    result=evaluate_scope(expr,p,replace(f,dimensions=(wrong,)))
    assert not result.ok and result.diagnostics[0].code=='DIMENSION_VERSION_MISMATCH'
    missing=replace(expr,dimension='unregistered.norm')
    result=evaluate_scope(missing,p,f)
    assert not result.ok and result.diagnostics[0].code=='UNKNOWN_NORMATIVE_DIMENSION'


def test_informational_extensions_never_supply_normative_facts():
    _,_,_,_,_,_,p,f=fixture()
    p=replace(p,informational=(('info.features',DimensionValue(ValueKind.TEXT_SET,frozenset({'feature-x'}))),))
    r=evaluate_scope(contains(),p,f)
    assert r.ok and r.result.value==UNKNOWN
    assert not validate_scope_expression(Atom('info.features',Operator.PRESENT),p.registry).ok


def test_exact_budget_boundary_and_unexamined_failure_are_not_boolean_values():
    _,s,_,_,_,_,p,f=fixture();f=replace(f,dimensions=(observation(p,s),))
    expr=Not(contains());reference=evaluate_scope(expr,p,f)
    exact=replace(StepBudget(),max_steps=reference.steps,max_nodes=reference.nodes,max_depth=2)
    assert evaluate_scope(expr,p,f,exact)==reference
    smaller=replace(exact,max_steps=reference.steps-1)
    failed=evaluate_scope(expr,p,f,smaller)
    assert failed.status is EvaluationStatus.RESOURCE_LIMITED and failed.result is None
    assert failed.unexamined and not failed.ok


def test_source_selector_does_not_take_another_sources_negative_witness():
    _,s,_,_,_,_,p,f=fixture()
    other=entity(p.project_id,K.SOURCE,'other-source')
    positive=observation(p,s)
    negative=replace(observation(p,s,(),True),
       witnesses=(replace(witness(p,s,'negative'),source_ref=other),),
       completeness_witnesses=(replace(witness(p,s,'complete'),source_ref=other),))
    f=replace(f,source_refs=frozenset({s.ref,other}),dimensions=(positive,negative))
    assert evaluate_scope(contains(),p,f).result.value==CONFLICT
    selected=evaluate_scope(replace(contains(),evidence_ref=s.ref),p,f)
    assert selected.result.value==YES and not selected.result.negative_witnesses


@pytest.mark.parametrize('raw',[None,[],True,{'schema':'unknown'}])
def test_untrusted_result_encoding_is_rejected_not_defaulted(raw):
    result=decode_applicability_result(raw)
    assert not result.ok and result.value is None


def test_applicability_entrypoints_do_not_import_io_or_application():
    root=Path(__file__).parents[2]/'src/guardian/domain'
    forbidden=('guardian.application','pathlib','os','time','random','uuid','subprocess','socket','requests')
    for name in ('scope.py','scope_codec.py'):
        tree=ast.parse((root/name).read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):assert not any((node.module or '').startswith(x) for x in forbidden)
            if isinstance(node,ast.Import):assert not any(a.name.startswith(forbidden) for a in node.names)
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):assert node.func.id not in ('eval','exec','open','__import__')
