"""G00-03: ten clauses and ADV-07..09, positive+negative evidence."""
from dataclasses import replace
import pytest

from guardian.domain.identity import EntityKind,ContentDigest,DigestAlgorithm
from guardian.domain.project import RepositoryId,StorageMode
from guardian.domain.outcomes import SourceStatus
from guardian.domain.source import (DocumentSourceCut, GitSourceCut,GitObjectKind,
    HistoryRole,SourceEntry,SourceExclusion,MissingSource,CoverageScope,
    validate_source_path,validate_git_source_cut,validate_document_source,
    validate_inclusion_exclusion,validate_source_universe,describe_source_coverage)
from foundation_b02 import project,cut,entity,universe


def test_g00_03_f01_pinned_git_sha_object_and_relative_path():
    p=project();s=cut(p)
    assert validate_git_source_cut(s).ok and len(s.commit)==40
    with pytest.raises(ValueError,match='SOURCE_CUT_NOT_PINNED'):
        replace(s,commit='main')
    with pytest.raises(ValueError,match='SOURCE_CUT_NOT_PINNED'):
        replace(s,commit='0'*7)


def test_g00_03_f02_document_has_revision_and_capture_identity():
    p=project()
    d=DocumentSourceCut(entity(p.project_id,EntityKind.SOURCE,'doc'), 'https://example.org/report','edition-2')
    assert validate_document_source(d).ok
    with pytest.raises(ValueError,match='SOURCE_REVISION_REQUIRED'):
        replace(d,document_version='')


def test_g00_03_f03_inclusion_set_is_explicit_versioned_and_not_world():
    p=project();one=cut(p);two=cut(p,name='unused')
    u=universe(p,(one,two),included=(one.ref,))
    assert one.ref in u.included and two.ref not in u.included
    assert replace(u,included=(one.ref,two.ref))!=u


def test_g00_03_f04_exclusion_requires_reason_and_approval_ref():
    p=project();s=cut(p)
    with pytest.raises(ValueError,match='EXCLUSION_UNJUSTIFIED'):
        SourceExclusion(s.ref,'',entity(p.project_id,EntityKind.DECISION,'approval'))
    exc=SourceExclusion(s.ref,'out of scope',entity(p.project_id,EntityKind.DECISION,'approval'))
    u=universe(p,(s,),included=(),excluded=(exc,),missing=(MissingSource('source gap','not acquired'),))
    assert exc in u.excluded


def test_g00_03_f05_known_missing_preserved_and_no_complete_claim():
    p=project();s=cut(p)
    u=universe(p,(s,),missing=(MissingSource('older release','not accessible'),))
    validation=validate_source_universe(u,p,{s.ref:s})
    assert not validation.ok and not validation.eligible_for_complete_claim
    assert any(d.code=='SOURCE_COVERAGE_UNKNOWN' for d in validation.diagnostics)
    assert describe_source_coverage(u).known_missing==u.known_missing


def test_g00_03_f06_history_delta_not_double_counted_as_disjoint():
    p=project()
    one=cut(p,name='base',commit='1'*40)
    two=cut(p,name='delta',commit='2'*40)
    entries=(SourceEntry(one,HistoryRole.BASE,SourceStatus.CONTENT_OBSERVED,'history-x'),
             SourceEntry(two,HistoryRole.DELTA,SourceStatus.IDENTIFIED,'history-x',one.ref))
    u=universe(p,(one,two),entries=entries)
    assert validate_source_universe(u,p,{one.ref:one,two.ref:two}).ok
    assert not describe_source_coverage(u).source_population_disjoint
    assert not describe_source_coverage(u).coverage_qualified


def test_g00_03_f07_observation_states_are_not_certification():
    p=project(); s=cut(p)
    entry=SourceEntry(s,HistoryRole.BASE,SourceStatus.IDENTITY_VERIFIED,'history')
    u=universe(p,(s,),entries=(entry,))
    v=validate_source_universe(u,p,{s.ref:s})
    assert s.ref in v.unresolved_sources
    assert not v.eligible_for_complete_claim


def test_g00_03_f08_source_claim_does_not_modify_constitution():
    p=project();s=cut(p);u=universe(p,(s,))
    original=p.constitution_ref
    validate_source_universe(u,p,{s.ref:s})
    assert p.constitution_ref==original


def test_g00_03_f09_scope_coverage_has_denominator_missing_and_limits():
    p=project();s=cut(p)
    u=universe(p,(s,),missing=(MissingSource('lost','old corpus'),),limits=('excluded release 2020',))
    coverage=describe_source_coverage(u)
    assert coverage.scope.corpus==('gsl-foundation',)
    assert coverage.limitations==('excluded release 2020',)
    assert not coverage.coverage_qualified


def test_g00_03_f10_corporal_feature_platform_time_scope_not_optional():
    p=project();s=cut(p)
    with pytest.raises(ValueError,match='COVERAGE_SCOPE_INCOMPLETE'):
        CoverageScope((),('specs',),('linux',),'2026')
    assert universe(p,(s,)).scope.temporal_boundary=='2026-10-21'


def test_adv07_mutable_HEAD_never_valid_git_cut():
    p=project()
    with pytest.raises(ValueError,match='SOURCE_CUT_NOT_PINNED'):
        GitSourceCut(entity(p.project_id,EntityKind.SOURCE,'bad'),p.storage.repositories[0],
                     'HEAD',GitObjectKind.BLOB,'spec/main.gsl')


def test_adv08_missing_source_does_not_issue_coverage_pass():
    p=project();s=cut(p)
    u=universe(p,(s,),missing=(MissingSource('baseline','unavailable'),))
    assert not describe_source_coverage(u).coverage_qualified
    assert not validate_source_universe(u,p,{s.ref:s}).eligible_for_complete_claim


def test_adv09_two_BASE_cuts_same_history_detect_double_population():
    p=project();a=cut(p,name='base',commit='1'*40);b=cut(p,name='base-two',commit='2'*40)
    entries=(SourceEntry(a,HistoryRole.BASE,SourceStatus.CONTENT_OBSERVED,'same-lineage'),
             SourceEntry(b,HistoryRole.BASE,SourceStatus.CONTENT_OBSERVED,'same-lineage'))
    v=validate_source_universe(universe(p,(a,b),entries=entries),p,{a.ref:a,b.ref:b})
    assert 'SOURCE_POPULATION_DOUBLE_COUNT' in {d.code for d in v.diagnostics}


@pytest.mark.parametrize('bad_path',['../escape','/absolute','foo/../../etc','C:\\evil','foo//bar','foo/./bar','foo/','foo\x00bar','foo\\bar'])
def test_g00_03_source_path_rejects_traversal_controls_and_absolute(bad_path):
    assert not validate_source_path(bad_path).ok


def test_g00_03_include_exclude_conflict_blocks_universe():
    p=project();s=cut(p)
    x=SourceExclusion(s.ref,'not relevant',entity(p.project_id,EntityKind.DECISION,'approved-exclusion'))
    u=universe(p,(s,),excluded=(x,))
    assert 'SOURCE_SCOPE_CONFLICT' in {d.code for d in validate_inclusion_exclusion(u)}


def test_g00_03_catalog_difference_is_not_silently_accepted():
    p=project();s=cut(p);u=universe(p,(s,))
    mismatch=replace(s,commit='d'*40)
    v=validate_source_universe(u,p,{s.ref:mismatch})
    assert 'SOURCE_CATALOG_MISMATCH' in {d.code for d in v.diagnostics}


def test_g00_03_universe_rejects_omitted_limits():
    p=project();s=cut(p)
    v=validate_source_universe(universe(p,(s,),limits=()),p,{s.ref:s})
    assert 'COVERAGE_LIMITS_NOT_DECLARED' in {d.code for d in v.diagnostics}


def test_g00_03_universe_identity_is_distinct_from_observed_source():
    p=project();s=cut(p);u=universe(p,(s,))
    assert u.identity.kind is EntityKind.SOURCE_UNIVERSE
    assert s.ref.kind is EntityKind.SOURCE


def test_g00_03_source_entries_are_immutable_on_validation():
    p=project();s=cut(p);u=universe(p,(s,))
    catalog={s.ref:s}; before=dict(catalog)
    validate_source_universe(u,p,catalog)
    assert catalog==before and u.entries[0].cut==s


def test_g00_03_unverified_exclusion_cannot_disappear_without_external_trust_context():
    p=project();s=cut(p)
    decision=entity(p.project_id,EntityKind.DECISION,'approval')
    ex=SourceExclusion(s.ref,'reason',decision)
    # Untrusted approval citation is not a ratified human action.
    u=universe(p,(s,),included=(),excluded=(ex,),missing=(MissingSource('scope gap','excluded'),))
    v=validate_source_universe(u,p,{s.ref:s})
    assert 'EXCLUSION_AUTHORITY_UNVERIFIED' in {d.code for d in v.diagnostics}
    accepted=validate_source_universe(u,p,{s.ref:s},trusted_exclusion_decisions=frozenset({decision}))
    assert 'EXCLUSION_AUTHORITY_UNVERIFIED' not in {d.code for d in accepted.diagnostics}
    assert not accepted.eligible_for_complete_claim


def test_g00_03_historical_baseline_cycles_rejected():
    p=project();a=cut(p,name='one');b=cut(p,name='two')
    entries=(SourceEntry(a,HistoryRole.DELTA,SourceStatus.IDENTIFIED,'shared',b.ref),
             SourceEntry(b,HistoryRole.DELTA,SourceStatus.IDENTIFIED,'shared',a.ref))
    u=universe(p,(a,b),entries=entries)
    codes={d.code for d in validate_source_universe(u,p,{a.ref:a,b.ref:b}).diagnostics}
    assert 'HISTORICAL_CYCLE' in codes and 'HISTORICAL_BASE_MISSING' in codes


def test_g00_03_document_rejects_untrusted_executable_locator_scheme():
    p=project()
    with pytest.raises(ValueError,match='DOCUMENT_SCHEME_UNSUPPORTED'):
        DocumentSourceCut(entity(p.project_id,EntityKind.SOURCE,'doc'), 'javascript:alert(1)','rev-12')


def test_g00_03_commit_object_does_not_accept_blob_path():
    p=project();s=cut(p)
    with pytest.raises(ValueError,match='COMMIT_OBJECT_HAS_NO_PATH'):
        replace(s,object_kind=GitObjectKind.COMMIT)


def test_g00_03_f04_foreign_source_exclusion_requires_target_project_decision():
    from guardian.domain.source import ApprovedSourceImport, TrustedImportGrants
    a=project();foreign=project('project-beta');s=cut(foreign)
    own_decision=entity(a.project_id,EntityKind.DECISION,'exclude-source')
    grant_decision=entity(a.project_id,EntityKind.DECISION,'grant-import')
    grant=TrustedImportGrants((ApprovedSourceImport(a.project_id,s.ref,s.repository,s.path,grant_decision,s),))
    excl=SourceExclusion(s.ref,'untrusted for this target',own_decision)
    u=universe(a,(s,),included=(),excluded=(excl,),missing=(MissingSource('missing','not acquired'),))
    v=validate_source_universe(u,a,{s.ref:s},grant,trusted_exclusion_decisions=frozenset({own_decision}))
    assert 'EXCLUSION_WRONG_PROJECT' not in {d.code for d in v.diagnostics}
    assert 'EXCLUSION_AUTHORITY_UNVERIFIED' not in {d.code for d in v.diagnostics}
    altered=replace(excl,approval_ref=entity(foreign.project_id,EntityKind.DECISION,'foreign-approval'))
    invalid=replace(u,excluded=(altered,))
    v2=validate_source_universe(invalid,a,{s.ref:s},grant,trusted_exclusion_decisions=frozenset({altered.approval_ref}))
    assert 'EXCLUSION_WRONG_PROJECT' in {d.code for d in v2.diagnostics}
