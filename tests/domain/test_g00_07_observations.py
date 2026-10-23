"""Adversarial G00-07-F03/F08/F09/F10: no claim may promote itself."""
from dataclasses import replace
import pytest

from guardian.domain.identity import EntityKind, RevisionId
from guardian.domain.outcomes import (
    DueStatus, StatusObservation,StatusAxis,TypedStatus,ImplementationStatus,
    MaterialStatus,QualificationStatus,StatusAxis,render_status_vector,
    validate_status_observation,
)
from guardian.application.project_service import build_readonly_project_view
from foundation_b02 import project,cut,entity,universe


def _view():
    p=project();s=cut(p);u=universe(p,(s,))
    result=build_readonly_project_view(p,u,{s.ref:s},entities=(
        entity(p.project_id,EntityKind.OBLIGATION,'spec-identity'),
        entity(p.project_id,EntityKind.SCOPE,'scope'),
    ))
    assert result.ok
    return p,s,result.value


def test_g00_07_observation_is_descriptive_scoped_pinned_and_separate_from_authority():
    p,s,v=_view()
    target=entity(p.project_id,EntityKind.OBLIGATION,'spec-identity')
    observation=StatusObservation(target,TypedStatus(StatusAxis.IMPLEMENTATION,ImplementationStatus.DEVELOPMENT_COMPLETE),
        s.ref,entity(p.project_id,EntityKind.SCOPE,'scope'),target.revision,'builder',(),DueStatus.FUTURE)
    assert validate_status_observation(observation,v).ok
    assert observation.due is DueStatus.FUTURE
    assert not hasattr(observation,'certify') and not hasattr(observation,'ratify')


def test_g00_07_status_observation_cannot_gain_authority_from_unrelated_source_or_revision():
    p,s,v=_view();target=entity(p.project_id,EntityKind.OBLIGATION,'spec-identity')
    ob=StatusObservation(target,TypedStatus(StatusAxis.QUALIFICATION,QualificationStatus.QUALIFIED),
        s.ref,entity(p.project_id,EntityKind.SCOPE,'scope'),target.revision,'agent')
    assert validate_status_observation(ob,v).ok  # Descriptive only: NOT a certified projection.
    with pytest.raises(ValueError,match='STATUS_CROSS_PROJECT_PROVENANCE'):
        replace(ob,source_ref=cut(project('project-beta')).ref)
    assert not validate_status_observation(replace(ob,revision=RevisionId('rev-'+'d'*32)),v).ok
    assert not validate_status_observation(replace(ob,source_ref=entity(p.project_id,EntityKind.SOURCE,'unknown')),v).ok


def test_g00_07_renderer_never_hides_missing_material_or_qualification():
    observed=(TypedStatus(StatusAxis.IMPLEMENTATION,ImplementationStatus.DEVELOPMENT_COMPLETE),)
    report=render_status_vector(observed)
    assert report.ok
    assert len(report.value)==9
    assert report.value['implementation']=='development_complete'
    assert report.value['material']=='unobserved'
    assert report.value['audit']=='unobserved'
    assert report.value['qualification']=='unobserved'
    with_missing=render_status_vector(observed+(TypedStatus(StatusAxis.MATERIAL,MaterialStatus.NOT_RUN),))
    assert with_missing.value['material']=='not_run'
    assert with_missing.value['qualification']=='unobserved'


def test_g00_07_due_axis_is_orthogonal_to_status_observation():
    assert DueStatus.FUTURE is not DueStatus.CURRENT
    assert DueStatus.FUTURE.value!='admitted'
