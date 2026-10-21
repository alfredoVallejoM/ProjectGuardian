"""B01 G00-07 foundation; no false multi-axis certification."""
import pytest
from guardian.domain.outcomes import (
    StatusAxis, SourceStatus, DecisionStatus, ImplementationStatus,
    AuditStatus, MaterialStatus, QualificationStatus, TypedStatus,
    parse_status, render_status_vector, check_illegal_promotion, Result, Diagnostic,
)

@pytest.mark.parametrize('axis,value', [
    (StatusAxis.SOURCE,'identified'), (StatusAxis.DECISION,'proposed'),
    (StatusAxis.IMPLEMENTATION,'development_complete'), (StatusAxis.AUDIT,'pass'),
    (StatusAxis.MATERIAL,'not_run'), (StatusAxis.QUALIFICATION,'unqualified'),
    (StatusAxis.COMMITMENT,'draft'), (StatusAxis.SUPPORT,'unknown'),
    (StatusAxis.MIGRATION,'not_started'),
])
def test_all_status_axes_are_nominal(axis,value):
    res = parse_status(axis, value)
    assert res.ok and res.value.axis is axis and res.value.value.value == value
    with pytest.raises(TypeError):
        TypedStatus(axis, DecisionStatus.PROPOSED if axis != StatusAxis.DECISION else AuditStatus.PASS)


def test_untrusted_status_cannot_convert_to_material():
    assert parse_status(StatusAxis.MATERIAL, 'development_complete').diagnostics[0].code == 'UNSUPPORTED_VARIANT'
    assert parse_status('material', 'pass').diagnostics[0].code == 'WRONG_STATUS_AXIS'
    x = TypedStatus(StatusAxis.IMPLEMENTATION, ImplementationStatus.DEVELOPMENT_COMPLETE)
    y = TypedStatus(StatusAxis.MATERIAL, MaterialStatus.PASS)
    assert check_illegal_promotion(x, y).diagnostics[0].code == 'ILLEGAL_STATUS_PROMOTION'


def test_pass_audit_not_same_as_qualified():
    x = TypedStatus(StatusAxis.AUDIT, AuditStatus.PASS)
    y = TypedStatus(StatusAxis.QUALIFICATION, QualificationStatus.QUALIFIED)
    assert check_illegal_promotion(x, y).diagnostics[0].code == 'ILLEGAL_STATUS_PROMOTION'


def test_no_not_run_promotion():
    x = TypedStatus(StatusAxis.MATERIAL, MaterialStatus.NOT_RUN)
    y = TypedStatus(StatusAxis.MATERIAL, MaterialStatus.PASS)
    assert check_illegal_promotion(x, y).diagnostics[0].code == 'TRANSITION_NOT_AUTHORIZED'


def test_vector_is_typed_sorted_and_non_duplicated():
    items = (TypedStatus(StatusAxis.MATERIAL, MaterialStatus.NOT_RUN), TypedStatus(StatusAxis.DECISION, DecisionStatus.PROPOSED))
    assert render_status_vector(items).value['decision']=='proposed'
    assert render_status_vector(items).value['material']=='not_run'
    assert render_status_vector(items).value['qualification']=='unobserved'
    assert len(render_status_vector(items).value)==9
    assert render_status_vector(items + (items[0],)).diagnostics[0].code == 'DUPLICATE_STATUS_AXIS'


def test_diagnostic_and_result_are_frozen_and_invariant():
    with pytest.raises(ValueError):
        Diagnostic('', '$', 'status', 'str', 'error')
    with pytest.raises(ValueError):
        Result(123,(Diagnostic('X', '$','str','int','invalid'),))
