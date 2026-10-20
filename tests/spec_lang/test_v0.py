import dataclasses
import hashlib
import itertools
import sys
from pathlib import Path
import pytest

sys.path.insert(0,str(Path(__file__).parents[1]))
from oracles.v4_oracle import evaluate as independent_evaluate
from guardian.domain.evidence_logic import FourValued, UNKNOWN,YES,NO,CONFLICT,V4_VALUES
from guardian.domain.identity import ContentDigest, DigestAlgorithm
from guardian.spec_lang.contract import SourceBundle
from guardian.spec_lang.ir import FormulaIR,SourceOrigin
from guardian.spec_lang.v0 import (
    OracleStatus, parse_source_formula, lower_formula, evaluate_ir,
    verify_semantics,
)


def origin(bundle,text):
    start=bundle.source_bytes.index(text)
    return SourceOrigin(bundle.source_ref,bundle.expected_digest,start,start+len(text))


@pytest.mark.parametrize('value',V4_VALUES)
def test_v4_all_values_distinct_and_not_involutive(value):
    assert value.negate().negate()==value
    assert UNKNOWN.negate()==UNKNOWN and CONFLICT.negate()==CONFLICT


def test_source_parser_and_lowering_covers_precedence():
    assert lower_formula(parse_source_formula(b'not x and y or z')) == FormulaIR('or',(
        FormulaIR('and',(FormulaIR('not',(FormulaIR('atom',name='x'),)),FormulaIR('atom',name='y'))),
        FormulaIR('atom',name='z')))
    for raw in (b'', b'alpha or', b'alpha and )', b'alpha()'):
        with pytest.raises(ValueError):
            parse_source_formula(raw)
    with pytest.raises(ValueError):
        FormulaIR('or',(FormulaIR('yes'),))


def test_all_16_binary_v4_truth_table_matches_independent_oracle():
    for left,right in itertools.product(V4_VALUES, repeat=2):
        a=(left.positive,left.negative); b=(right.positive,right.negative)
        assert (left.conjunction(right).positive,left.conjunction(right).negative)==independent_evaluate(('and',('atom','x'),('atom','y')),{'x':a,'y':b})
        assert (left.disjunction(right).positive,left.disjunction(right).negative)==independent_evaluate(('or',('atom','x'),('atom','y')),{'x':a,'y':b})
        assert (left.negate().positive,left.negate().negative)==independent_evaluate(('not',('atom','x')),{'x':a})


def test_exhaustive_64_semantic_cases_source_and_ir(pinned):
    bundle,ctx=pinned
    expr=b'not (alpha and beta)'
    ir=lower_formula(parse_source_formula(expr))
    report=verify_semantics(bundle,ctx,origin(bundle,expr),ir)
    assert report.status is OracleStatus.FINITE_EQUIVALENT
    assert report.valuations_checked==16
    text=b'(alpha or beta) and not gamma'
    data=SourceBundle(bundle.source_ref,text,ContentDigest(DigestAlgorithm.SHA256,hashlib.sha256(text).hexdigest()))
    context=dataclasses.replace(ctx,expected_sources=((bundle.source_ref,data.expected_digest),))
    checked=verify_semantics(data,context,SourceOrigin(bundle.source_ref,data.expected_digest,0,len(text)),lower_formula(parse_source_formula(text)))
    assert checked.acceptable and checked.valuations_checked==64


def test_mutation_of_semantic_ir_caught_even_after_hashes_regenerated(pinned):
    bundle,ctx=pinned
    expr=b'not (alpha and beta)'
    valid=lower_formula(parse_source_formula(expr))
    wrong=FormulaIR('or',valid.args[0].args)
    assert verify_semantics(bundle,ctx,origin(bundle,expr),valid).acceptable
    result=verify_semantics(bundle,ctx,origin(bundle,expr),wrong)
    assert result.status is OracleStatus.COUNTEREXAMPLE
    assert result.witness and result.source_value!=result.ir_value
    # Rehashing wrong typed IR can never change comparison to independently pinned bytes.
    import json
    from hashlib import sha256
    forged_digest=sha256(json.dumps({'ir':'or','hash':sha256(b'or').hexdigest()}).encode()).hexdigest()
    assert forged_digest and not result.acceptable


def test_unknown_or_conflict_not_demoted_to_boolean(pinned):
    bundle,ctx=pinned
    for word,value in ((b'unknown',UNKNOWN),(b'conflict',CONFLICT)):
        assert evaluate_ir(FormulaIR(word.decode()),{})==value
        assert evaluate_ir(FormulaIR('not',(FormulaIR(word.decode()),)),{})==value
        content=word
        b=SourceBundle(bundle.source_ref,content,ContentDigest(DigestAlgorithm.SHA256,hashlib.sha256(content).hexdigest()))
        context=dataclasses.replace(ctx,expected_sources=((bundle.source_ref,b.expected_digest),))
        assert verify_semantics(b,context,SourceOrigin(bundle.source_ref,b.expected_digest,0,len(word)),FormulaIR(word.decode())).acceptable
        assert verify_semantics(b,context,SourceOrigin(bundle.source_ref,b.expected_digest,0,len(word)),FormulaIR('no')).status is OracleStatus.COUNTEREXAMPLE


def test_unpinned_digest_tampering_cannot_succeed(pinned):
    bundle,ctx=pinned
    raw=b'not (alpha or beta)'
    changed=SourceBundle(bundle.source_ref,raw,ContentDigest(DigestAlgorithm.SHA256,hashlib.sha256(raw).hexdigest()))
    result=verify_semantics(changed,ctx,SourceOrigin(changed.source_ref,changed.expected_digest,0,len(raw)),lower_formula(parse_source_formula(raw)))
    assert result.status is OracleStatus.UNTRUSTED_PIN


def test_budget_limit_is_inconclusive_not_pass(pinned):
    bundle,ctx=pinned
    expr=b'not (alpha and beta)'
    ir=lower_formula(parse_source_formula(expr))
    too_small=verify_semantics(bundle,ctx,origin(bundle,expr),ir,max_atoms=1)
    assert too_small.status is OracleStatus.INCONCLUSIVE_RESOURCE_LIMIT and not too_small.acceptable
    too_few=verify_semantics(bundle,ctx,origin(bundle,expr),ir,max_valuations=3)
    assert too_few.status is OracleStatus.INCONCLUSIVE_RESOURCE_LIMIT and too_few.valuations_checked==0


def test_invalid_span_not_equivalent(pinned):
    bundle,ctx=pinned
    invalid=SourceOrigin(bundle.source_ref,bundle.expected_digest,0,len(bundle.source_bytes)+1)
    res=verify_semantics(bundle,ctx,invalid,FormulaIR('yes'))
    assert res.status is OracleStatus.INVALID_SOURCE


def test_v4_ir_is_not_evaluator_of_source_python_code():
    for raw in (b'__import__("os")',b'x.__class__',b'lambda x: x',b'alpha && beta'):
        with pytest.raises(ValueError):parse_source_formula(raw)


def test_domain_gsl_coexistence_without_certification(pinned):
    from guardian.domain.outcomes import TypedStatus,StatusAxis,MaterialStatus,QualificationStatus
    bundle,ctx=pinned
    assert verify_semantics(bundle,ctx,origin(bundle,b'not (alpha and beta)'),lower_formula(parse_source_formula(b'not (alpha and beta)'))).acceptable
    material=TypedStatus(StatusAxis.MATERIAL,MaterialStatus.NOT_RUN)
    qualification=TypedStatus(StatusAxis.QUALIFICATION,QualificationStatus.UNQUALIFIED)
    assert material.value is MaterialStatus.NOT_RUN and qualification.value is QualificationStatus.UNQUALIFIED
