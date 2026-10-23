"""R1/R2/R5/R7: cross-product nominal tests and real snapshot consumers."""
from dataclasses import replace
from itertools import permutations
import ast
from pathlib import Path
import pytest

from guardian.domain.identity import EntityKind, RevisionId, ContentDigest, DigestAlgorithm
from guardian.domain.outcomes import (
    StatusAxis, SourceStatus, DecisionStatus, CommitmentStatus, ImplementationStatus,
    AuditStatus, MaterialStatus, SupportStatus, QualificationStatus, MigrationStatus,
    TypedStatus, parse_status, encode_status, decode_status, check_illegal_promotion,
    StatusObservation, validate_status_observation,
)
from guardian.domain.project import RepositoryId, StorageMode
from guardian.domain.source import (
    DocumentSourceCut, SourceEntry, HistoryRole, MissingSource, validate_source_universe,
    describe_source_coverage, check_source_membership,
)
from guardian.application.project_service import build_readonly_project_view, inspect_project_definition
from guardian.spec_lang.contract import CompilationResult, CompilationStage, CompileStatus
from foundation_b02 import project, cut, universe, entity, bundle_context

# Explicit test-side oracle, not imported from production's dispatch dictionary.
AXES = (
    (StatusAxis.SOURCE, SourceStatus), (StatusAxis.DECISION, DecisionStatus),
    (StatusAxis.COMMITMENT, CommitmentStatus), (StatusAxis.IMPLEMENTATION, ImplementationStatus),
    (StatusAxis.AUDIT, AuditStatus), (StatusAxis.MATERIAL, MaterialStatus),
    (StatusAxis.SUPPORT, SupportStatus), (StatusAxis.QUALIFICATION, QualificationStatus),
    (StatusAxis.MIGRATION, MigrationStatus),
)
CASES = [(axis, other_axis, value) for axis, _ in AXES
         for other_axis, enum in AXES for value in enum]


@pytest.mark.parametrize('axis,source_axis,value', CASES)
def test_status_parser_nominal_cross_product(axis, source_axis, value):
    result = parse_status(axis, value)
    assert result.ok == (axis is source_axis)
    if axis is source_axis:
        assert type(result.value.value) is type(value)
        assert decode_status(encode_status(result.value)).value == result.value
    else:
        assert result.diagnostics[0].code == 'WRONG_STATUS_AXIS'


@pytest.mark.parametrize('axis,enum', AXES)
def test_status_plain_strings_roundtrip_and_cross_axis_promotions(axis, enum):
    for value in enum:
        parsed = parse_status(axis, value.value)
        assert parsed.value == TypedStatus(axis, value)
        for other_axis, other in AXES:
            if other_axis is not axis:
                target = TypedStatus(other_axis, next(iter(other)))
                assert check_illegal_promotion(parsed.value, target).diagnostics[0].code == 'ILLEGAL_STATUS_PROMOTION'


def test_status_decoder_is_not_a_coercing_authority():
    valid = encode_status(TypedStatus(StatusAxis.MATERIAL, MaterialStatus.NOT_RUN))
    for bad in (dict(valid, certificate=True), dict(valid, value=AuditStatus.PASS),
                dict(valid, schema='future'), dict(valid, axis='unknown')):
        assert not decode_status(bad).ok
    class Hostile(str):
        def __eq__(self, other):
            raise AssertionError('user equality executed')
    assert not parse_status(StatusAxis.MATERIAL, Hostile('pass')).ok


@pytest.mark.parametrize('mode', tuple(StorageMode))
def test_managed_and_designated_authority_sources_are_allowed_but_not_arbitrary_repos(mode):
    p = project(mode=mode)
    allowed = set(p.storage.repositories) | {p.storage.authority_repository}
    for repository in allowed:
        assert check_source_membership(p, cut(p, repo=repository)).allowed
    assert not check_source_membership(p, cut(p, repo=RepositoryId('github', 'alien/repo'))).allowed


def test_sidecar_authority_runs_through_the_real_source_analysis_service():
    from guardian.application.project_service import analyze_project_source
    p = project(mode=StorageMode.SIDECAR)
    s = cut(p, repo=p.storage.authority_repository)
    b, c = bundle_context(p, s, b'gsl "0.1"; project "project-alpha";')
    view = build_readonly_project_view(p, universe(p, (s,)), {s.ref: s}).value
    assert analyze_project_source(view, b, c, source_format='gsl').ok


@pytest.mark.parametrize('path_a,path_b,disjoint', [
    ('a/spec.gsl','b/spec.gsl',True), ('a/spec.gsl','a/spec.gsl',False),
    ('docs','docs/main.gsl',False), ('docs','docs-other/main.gsl',True),
])
def test_source_disjointness_is_path_material_not_lineage_labels(path_a,path_b,disjoint):
    p = project()
    a = cut(p, name='source-one', path=path_a)
    b = cut(p, name='source-two', path=path_b, commit='d'*40)
    for pair in permutations((a, b)):
        descriptor = describe_source_coverage(universe(p, pair))
        assert descriptor.source_population_disjoint is disjoint
        assert not descriptor.coverage_qualified


def test_document_dag_is_valid_and_cycle_and_foreign_baseline_are_not():
    p = project()
    a = DocumentSourceCut(entity(p.project_id,EntityKind.SOURCE,'document-one'),'https://example.org/spec','v1')
    b = replace(a,ref=entity(p.project_id,EntityKind.SOURCE,'document-two'),document_version='v2')
    first = SourceEntry(a,HistoryRole.BASE,SourceStatus.CONTENT_OBSERVED,'history')
    second = SourceEntry(b,HistoryRole.DELTA,SourceStatus.CONTENT_OBSERVED,'history',a.ref)
    catalog = {a.ref:a,b.ref:b}
    for entries in permutations((first, second)):
        assert validate_source_universe(universe(p,(a,b),entries=entries),p,catalog).ok
    cycle = (replace(first,role=HistoryRole.DELTA,baseline_ref=b.ref), second)
    diagnostics = validate_source_universe(universe(p,(a,b),entries=cycle),p,catalog).diagnostics
    assert 'HISTORICAL_CYCLE' in {d.code for d in diagnostics}
    foreign = replace(b,locator='https://example.org/unrelated')
    bad = universe(p,(a,foreign),entries=(first,replace(second,cut=foreign)))
    assert 'INVALID_HISTORICAL_BASELINE' in {d.code for d in validate_source_universe(bad,p,{a.ref:a,b.ref:foreign}).diagnostics}


def test_missing_channels_are_both_visible_without_qualifying_or_losing_limits():
    p = project(); s = cut(p)
    e = SourceEntry(s, HistoryRole.BASE, SourceStatus.MISSING, 'history')
    u = universe(p,(s,),entries=(e,),missing=(MissingSource('never-acquired','historical gap'),),limits=('scope limited',))
    descriptor = describe_source_coverage(u)
    assert len(descriptor.known_missing) == 2
    assert descriptor.limitations[0] == 'scope limited'
    assert not descriptor.coverage_qualified
    assert {'SOURCE_MISSING','SOURCE_COVERAGE_UNKNOWN'} <= {d.code for d in validate_source_universe(u,p,{s.ref:s}).diagnostics}


def test_status_all_references_are_exact_and_evidence_is_not_automatically_created():
    p = project(); s = cut(p)
    target = entity(p.project_id,EntityKind.OBLIGATION,'target-one')
    scope = entity(p.project_id,EntityKind.SCOPE,'scope-one')
    proof = entity(p.project_id,EntityKind.VERIFICATION,'proof-one')
    obs = StatusObservation(target,TypedStatus(StatusAxis.MATERIAL,MaterialStatus.PASS),s.ref,scope,target.revision,'reviewer',(proof,))
    entries = (target,scope,proof)
    for omitted in entries:
        v = build_readonly_project_view(p,universe(p,(s,)),{s.ref:s},entities=tuple(e for e in entries if e!=omitted)).value
        assert validate_status_observation(obs,v).diagnostics[0].code == 'ORPHAN_REFERENCE'
    v = build_readonly_project_view(p,universe(p,(s,)),{s.ref:s},entities=entries).value
    assert validate_status_observation(obs,v).ok
    wrong_scope = replace(scope,revision=RevisionId('rev-'+'e'*32))
    assert not validate_status_observation(replace(obs,scope_ref=wrong_scope),v).ok
    assert v.entities == entries


def test_project_inspection_reports_policy_pins_and_missing_sources_without_qualification():
    p = project(); s = cut(p)
    u = universe(p,(s,),missing=(MissingSource('not-found','recorded gap'),))
    v = build_readonly_project_view(p,u,{s.ref:s}).value
    inspection = inspect_project_definition(p,v)
    assert inspection.ok and not inspection.value.qualified
    assert inspection.value.definition.source_policy_ref == p.source_policy_ref
    assert inspection.value.missing_references == (p.constitution_ref,)
    assert inspection.value.source_coverage.known_missing == u.known_missing
    assert {d.code for d in inspection.value.diagnostics} == {'ORPHAN_REFERENCE','SOURCE_MISSING'}
    assert not inspect_project_definition(p).ok


def test_domain_has_no_application_spec_lang_adapters_or_persistence_imports():
    import guardian.domain
    root = Path(guardian.domain.__file__).parent
    forbidden = ('guardian.application','guardian.spec_lang','guardian.adapters','guardian.persistence','guardian.interfaces')
    for path in root.glob('*.py'):
        for node in ast.walk(ast.parse(path.read_text())):
            names = ([node.module or ''] if isinstance(node,ast.ImportFrom)
                     else [alias.name for alias in node.names] if isinstance(node,ast.Import) else [])
            assert not any(n.startswith(forbidden) for n in names), (path.name,node.lineno,names)
