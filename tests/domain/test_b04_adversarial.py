"""B04 self-review falsifications; no independent-auditor claim."""
from dataclasses import replace
import pytest
from foundation_b04 import fixture, witness, observation, contains
from guardian.domain.evidence_logic import YES, NO, CONFLICT
from guardian.domain.scope import (ApplicabilityResult, ScopeTrace, ScopeEvaluation,
    and_evidence, or_evidence, evaluate_scope)
from guardian.domain.scope_codec import encode_applicability_result, decode_applicability_result


@pytest.mark.parametrize('operation,other', [(and_evidence, NO), (or_evidence, YES)])
def test_direct_composition_preserves_conflict_witnesses_when_final_value_is_decisive(operation, other):
    _,s,_,_,_,_,p,_ = fixture()
    positive=witness(p,s,'positive'); negative=witness(p,s,'negative')
    conflict=ApplicabilityResult(p.context,CONFLICT,(positive,),(negative,))
    decided=ApplicabilityResult(p.context,other,(positive,) if other==YES else (),
                                (negative,) if other==NO else ())
    result=operation(conflict,decided)
    assert result.value==other
    assert any(d.code=='APPLICABILITY_CONFLICT' for d in result.diagnostics)
    assert any(positive in c.positive_witnesses and negative in c.negative_witnesses
               for c in result.conflicts)
    decoded=decode_applicability_result(encode_applicability_result(result))
    assert decoded.ok and decoded.value.conflicts==result.conflicts


def test_completed_report_cannot_replace_trace_with_foreign_context():
    _,s,_,_,_,_,p,f=fixture()
    report=evaluate_scope(contains(),p,replace(f,dimensions=(observation(p,s),)))
    _,t,_,_,_,_,q,_=fixture('project-beta')
    foreign=ApplicabilityResult(q.context,YES,(witness(q,t),),())
    with pytest.raises((ValueError,TypeError)):
        replace(report,trace=(ScopeTrace('$','Atom',foreign),))


def test_scope_codec_does_not_invoke_candidate_schema_equality():
    _,s,_,_,_,_,p,_=fixture()
    raw=encode_applicability_result(ApplicabilityResult(p.context,YES,(witness(p,s),),()))
    seen=[]
    class Hostile:
        def __eq__(self,other):
            seen.append(other); return True
    raw['schema']=Hostile()
    result=decode_applicability_result(raw)
    assert not result.ok and not seen


def test_complete_report_cannot_hide_unexamined_nodes():
    _,s,_,_,_,_,p,f=fixture()
    report=evaluate_scope(contains(),p,replace(f,dimensions=(observation(p,s),)))
    with pytest.raises((ValueError,TypeError)):
        replace(report,unexamined=('$.hidden',))
