from dataclasses import replace
from guardian.domain.source import (SourceEntry,HistoryRole,SourceExclusion,MissingSource,
   validate_source_universe,GitSourceCut,GitObjectKind,ApprovedSourceImport,TrustedImportGrants,
   check_source_membership)
from guardian.domain.outcomes import SourceStatus
from guardian.domain.identity import EntityKind
from guardian.domain.project import StorageMode
from guardian.application.project_service import ReadOnlyProjectView, analyze_project_source
from foundation_b02 import project,cut,entity,universe,bundle_context

RAW=b'gsl "0.1";\nproject "project-alpha";\n'

def test_missing_entry_blocks_positive_universe_validation():
    p=project();s=cut(p)
    u=universe(p,(s,),entries=(SourceEntry(s,HistoryRole.BASE,SourceStatus.MISSING,'history'),))
    result=validate_source_universe(u,p,{s.ref:s})
    assert not result.ok and 'SOURCE_MISSING' in {x.code for x in result.diagnostics}

def test_direct_view_cannot_bypass_universe_conflict():
    p=project();s=cut(p); bundle,ctx=bundle_context(p,s,RAW)
    denial=SourceExclusion(s.ref,'exclude',entity(p.project_id,EntityKind.DECISION,'approval'))
    u=universe(p,(s,),excluded=(denial,))
    import pytest
    with pytest.raises(ValueError, match='INVALID_SOURCE_UNIVERSE_MEMBERSHIP'):
        ReadOnlyProjectView(p,u,(s,))

def test_cross_repository_delta_is_not_valid_history():
    p=project(mode=StorageMode.FEDERATED)
    a=cut(p,name='base',repo=p.storage.repositories[0]);b=cut(p,name='delta',repo=p.storage.repositories[1])
    entries=(SourceEntry(a,HistoryRole.BASE,SourceStatus.CONTENT_OBSERVED,'x'),SourceEntry(b,HistoryRole.DELTA,SourceStatus.CONTENT_OBSERVED,'x',a.ref))
    u=universe(p,(a,b),entries=entries)
    out=validate_source_universe(u,p,{a.ref:a,b.ref:b})
    assert 'INVALID_HISTORICAL_BASELINE' in {x.code for x in out.diagnostics}

def test_exact_import_grant_does_not_cover_different_commit():
    p=project();source_project=project('project-beta');s=cut(source_project)
    grant=TrustedImportGrants((ApprovedSourceImport(p.project_id,s.ref,s.repository,s.path,entity(p.project_id,EntityKind.DECISION,'approval'),s),))
    assert check_source_membership(p,s,grant).allowed
    mutated=replace(s,commit='1'*40)
    assert not check_source_membership(p,mutated,grant).allowed


def test_missing_source_is_not_silent_when_other_sources_are_observed():
    p=project();good=cut(p,name='good');lost=cut(p,name='lost')
    entries=(SourceEntry(good,HistoryRole.BASE,SourceStatus.CONTENT_OBSERVED,'one'),
             SourceEntry(lost,HistoryRole.BASE,SourceStatus.MISSING,'two'))
    validation=validate_source_universe(universe(p,(good,lost),entries=entries),p,{good.ref:good,lost.ref:lost})
    assert {d.code for d in validation.diagnostics}>={'SOURCE_MISSING','SOURCE_COVERAGE_UNKNOWN'}
    assert lost.ref in validation.unresolved_sources


def test_import_requires_original_cut_not_just_nominal_reference():
    import pytest
    p=project();source_project=project('project-beta');s=cut(source_project)
    approval=entity(p.project_id,EntityKind.DECISION,'approval')
    with pytest.raises(TypeError):
        ApprovedSourceImport(p.project_id,s.ref,s.repository,s.path,approval)
    with pytest.raises(ValueError,match='IMPORT_PINNED_CUT_REQUIRED'):
        ApprovedSourceImport(p.project_id,s.ref,s.repository,s.path,approval,cut(source_project,name='other'))
    with pytest.raises(ValueError,match='IMPORT_CUT_REPOSITORY_PATH_MISMATCH'):
        ApprovedSourceImport(p.project_id,s.ref,s.repository,'spec/other.gsl',approval,s)


def test_document_import_must_bind_exact_document_version_and_locator():
    from guardian.domain.source import DocumentSourceCut
    p=project();foreign=project('project-beta')
    d=DocumentSourceCut(entity(foreign.project_id,EntityKind.SOURCE,'document'),
                        'https://example.org/research','edition-1')
    approved=entity(p.project_id,EntityKind.DECISION,'approved')
    grants=TrustedImportGrants((ApprovedSourceImport(p.project_id,d.ref,None,None,approved,d),))
    assert check_source_membership(p,d,grants).allowed
    assert not check_source_membership(p,replace(d,document_version='edition-2'),grants).allowed
    assert not check_source_membership(p,replace(d,locator='https://other.example/research'),grants).allowed


def test_readonly_view_rejects_untyped_cut_and_mismatch_of_equal_ref():
    import pytest
    from types import SimpleNamespace
    p=project();s=cut(p);u=universe(p,(s,))
    with pytest.raises(TypeError,match='sources must be frozen typed cuts'):
        ReadOnlyProjectView(p,u,(SimpleNamespace(ref=s.ref),))
    with pytest.raises(ValueError,match='PROJECT_SOURCES_MISMATCH'):
        ReadOnlyProjectView(p,u,(replace(s,commit='1'*40),))


def test_id_parser_rejects_user_defined_equality_without_executing_it():
    from guardian.domain.identity import parse_project_id,parse_revision_id
    class Hostile:
        def __eq__(self,other):
            raise RuntimeError('hostile input attempted to execute equality')
    assert not parse_project_id(Hostile()).ok
    assert not parse_revision_id(Hostile()).ok
