"""Executable positive/falsifying contracts for G00-03-F01..F10.

These exercise the real source domain. They are not tests of the acceptance
checker and do not authenticate approvals or close the parent campaign.
"""
from dataclasses import FrozenInstanceError, fields, replace
import pytest
from foundation_b02 import project, cut, universe, entity
from guardian.domain.identity import EntityKind as K, RevisionId
from guardian.domain.outcomes import SourceStatus
from guardian.domain.source import (
    CoverageScope, DocumentSourceCut, GitObjectKind, GitSourceCut, HistoryRole,
    MissingSource, SourceEntry, SourceExclusion, validate_document_source,
    validate_git_source_cut, validate_inclusion_exclusion, validate_source_universe,
    describe_source_coverage,
)


def forge(value, **changes):
    obj = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(obj, field.name, changes.get(field.name, getattr(value, field.name)))
    return obj


def validate(p, u, **kwargs):
    return validate_source_universe(u, p, {e.cut.ref: e.cut for e in u.entries}, **kwargs)


def codes(result):
    return {d.code for d in result.diagnostics}


def test_G00_03_F01_positive_fixed_git_objects():
    p = project(); s = cut(p)
    for length in (40, 64):
        for kind, path in ((GitObjectKind.COMMIT, None), (GitObjectKind.TREE, 'spec'),
                           (GitObjectKind.BLOB, 'spec/source.gsl')):
            fixed = replace(s, commit='a' * length, object_kind=kind, path=path)
            assert validate_git_source_cut(fixed).value == fixed
            assert validate(p, universe(p, (fixed,))).ok


def test_G00_03_F01_negative_mutable_or_partial_git_cut(record_property):
    p = project(); s = cut(p)
    for value in ('main', 'HEAD', 'abc1234', ''):
        result = validate_git_source_cut(forge(s, commit=value))
        assert not result.ok and result.value is None
        assert result.diagnostics[0].code == 'SOURCE_CUT_NOT_PINNED'
    record_property('guardian.diagnostic', result.diagnostics[0].code)


def test_G00_03_F02_positive_versioned_document_captures():
    p = project()
    first = DocumentSourceCut(entity(p.project_id, K.SOURCE, 'document-main'),
                              'https://example.invalid/report', 'edition-1')
    second = replace(first, ref=replace(first.ref, revision=RevisionId('rev-' + 'b' * 32)),
                     document_version='edition-2')
    assert first.ref != second.ref
    assert validate_document_source(first).value == first
    assert validate_document_source(second).value == second
    assert first.document_version == 'edition-1'


def test_G00_03_F02_negative_title_or_missing_version():
    p = project()
    valid = DocumentSourceCut(entity(p.project_id, K.SOURCE, 'document-main'),
                              'urn:spec:report', 'edition-1')
    for altered in (forge(valid, locator='A report title'), forge(valid, document_version='')):
        result = validate_document_source(altered)
        assert not result.ok and result.diagnostics[0].code == 'SOURCE_REVISION_REQUIRED'


def test_G00_03_F03_positive_explicit_include_set_and_new_revision():
    p = project(); a = cut(p); b = cut(p, name='source-other', path='spec/other.gsl')
    old = universe(p, (a, b), included=(a.ref,))
    new = replace(old, identity=replace(old.identity, revision=RevisionId('rev-' + 'd' * 32)),
                  included=(a.ref, b.ref))
    assert validate(p, old).ok and validate(p, new).ok
    assert old.included == (a.ref,) and b.ref not in old.included
    assert old.identity != new.identity
    assert describe_source_coverage(old).counted_source_cuts == 1
    assert describe_source_coverage(new).counted_source_cuts == 2
    with pytest.raises(FrozenInstanceError):
        old.included = new.included


def test_G00_03_F03_negative_unknown_source_is_not_included_by_default():
    p = project(); s = cut(p); absent = cut(p, name='source-absent', path='absent.gsl')
    u = universe(p, (s,), included=(s.ref, absent.ref))
    result = validate(p, u)
    assert not result.ok and 'UNKNOWN_SOURCE' in codes(result)
    assert not result.eligible_for_complete_claim


def test_G00_03_F04_positive_reason_and_external_exact_approval_reference():
    p = project(); a = cut(p); b = cut(p, name='source-other', path='spec/other.gsl')
    decision = entity(p.project_id, K.DECISION, 'decision-exclude')
    exclusion = SourceExclusion(b.ref, 'Outside the explicitly selected corpus', decision)
    u = universe(p, (a, b), included=(a.ref,), excluded=(exclusion,))
    result = validate(p, u, trusted_exclusion_decisions=frozenset({decision}))
    assert result.ok and u.excluded == (exclusion,)
    assert not result.eligible_for_complete_claim  # trust input is not authentication


def test_G00_03_F04_negative_reference_alone_does_not_authorize_exclusion(record_property):
    p = project(); a = cut(p); b = cut(p, name='source-other', path='spec/other.gsl')
    decision = entity(p.project_id, K.DECISION, 'decision-exclude')
    exclusion = SourceExclusion(b.ref, 'Explicitly requested but not authorized', decision)
    u = universe(p, (a, b), included=(a.ref,), excluded=(exclusion,))
    result = validate(p, u)
    assert not result.ok and 'EXCLUSION_AUTHORITY_UNVERIFIED' in codes(result)
    record_property('guardian.diagnostic', 'EXCLUSION_AUTHORITY_UNVERIFIED')


def test_G00_03_F05_positive_known_missing_is_preserved_in_reports():
    p = project(); s = cut(p); missing = MissingSource('urn:source:missing', 'Not retrieved')
    u = universe(p, (s,), missing=(missing,))
    report = describe_source_coverage(u)
    result = validate(p, u)
    assert report.known_missing == (missing,) and report.scope == u.scope
    assert 'SOURCE_COVERAGE_UNKNOWN' in codes(result)
    assert not report.coverage_qualified and not result.eligible_for_complete_claim


def test_G00_03_F05_negative_acquisition_missing_cannot_disappear(record_property):
    p = project(); s = cut(p)
    u = universe(p, (s,), entries=(SourceEntry(s, HistoryRole.BASE, SourceStatus.MISSING, 'history'),))
    result = validate(p, u); report = describe_source_coverage(u)
    assert 'SOURCE_MISSING' in codes(result) and s.ref in result.unresolved_sources
    assert report.known_missing and 'SOURCE_MISSING' in report.known_missing[0].reason
    assert not report.coverage_qualified and not report.source_population_disjoint
    record_property('guardian.diagnostic', 'SOURCE_MISSING')


def test_G00_03_F06_positive_history_retains_both_cuts_without_disjoint_claim():
    p = project(); first = cut(p); second = cut(p, name='source-delta', commit='d' * 40)
    entries = (SourceEntry(first, HistoryRole.BASE, SourceStatus.CONTENT_OBSERVED, 'history'),
               SourceEntry(second, HistoryRole.DELTA, SourceStatus.CONTENT_OBSERVED, 'history', first.ref))
    u = universe(p, (first, second), entries=entries)
    assert validate(p, u).ok and len(u.entries) == 2
    report = describe_source_coverage(u)
    assert report.counted_source_cuts == 2 and not report.source_population_disjoint
    assert not report.coverage_qualified


def test_G00_03_F06_negative_aliases_do_not_double_count_physical_population(record_property):
    p = project(); first = cut(p); alias = replace(first, ref=entity(p.project_id, K.SOURCE, 'another-label'))
    u = universe(p, (first, alias))
    result = validate(p, u)
    assert not result.ok and 'SOURCE_POPULATION_DOUBLE_COUNT' in codes(result)
    assert not describe_source_coverage(u).source_population_disjoint
    record_property('guardian.diagnostic', 'SOURCE_POPULATION_DOUBLE_COUNT')


def test_G00_03_F07_positive_acquisition_levels_remain_distinct():
    p = project(); s = cut(p)
    for status in SourceStatus:
        u = universe(p, (s,), entries=(SourceEntry(s, HistoryRole.BASE, status, 'history'),))
        result = validate(p, u)
        assert u.entries[0].acquisition is status
        assert (s.ref in result.unresolved_sources) == (status is not SourceStatus.SEMANTIC_RECONCILED)
        assert not result.eligible_for_complete_claim


def test_G00_03_F07_negative_plain_status_label_is_not_nominal_acquisition():
    p = project(); s = cut(p); u = universe(p, (s,))
    supplied = replace(u, entries=(forge(u.entries[0], acquisition='semantic_reconciled'),))
    result = validate(p, supplied)
    assert not result.ok and 'INVALID_SOURCE_ENTRY' in codes(result)
    with pytest.raises(ValueError, match='INVALID_SOURCE_COVERAGE_INPUT'):
        describe_source_coverage(supplied)


def test_G00_03_F08_positive_observed_readme_never_issues_authority():
    p = project(); observed = cut(p, path='README.md')
    u = universe(p, (observed,), entries=(SourceEntry(observed, HistoryRole.BASE,
        SourceStatus.SEMANTIC_RECONCILED, 'history'),))
    before = (p, u, observed)
    result = validate(p, u); report = describe_source_coverage(u)
    assert result.ok and not result.unresolved_sources
    assert not result.eligible_for_complete_claim and not report.coverage_qualified
    assert (p, u, observed) == before
    assert p.constitution_ref.kind is K.CONSTITUTION


def test_G00_03_F08_negative_decision_reference_cannot_masquerade_as_source():
    p = project(); source = cut(p)
    supplied = forge(source, ref=entity(p.project_id, K.DECISION, 'decision-approved'))
    result = validate_git_source_cut(supplied)
    assert not result.ok and result.diagnostics[0].code == 'SOURCE_CUT_NOT_PINNED'


def test_G00_03_F09_positive_bounded_description_is_not_a_certificate():
    p = project(); s = cut(p)
    limits = ('Selected corpus only', 'No runtime evidence inspected')
    u = universe(p, (s,), limits=limits)
    report = describe_source_coverage(u); result = validate(p, u)
    assert report.limitations == limits and report.scope == u.scope == result.covered_scope
    assert not report.coverage_qualified and not result.eligible_for_complete_claim


def test_G00_03_F09_negative_undeclared_limits_block_validation():
    p = project(); s = cut(p); u = universe(p, (s,), limits=())
    result = validate(p, u)
    assert not result.ok and 'COVERAGE_LIMITS_NOT_DECLARED' in codes(result)


def test_G00_03_F10_positive_all_scope_dimensions_are_reported():
    p = project(); s = cut(p)
    scope = CoverageScope(('source-contracts',), ('identity', 'history'), ('linux', 'windows'),
                          'release-candidate-2026-10-27')
    u = replace(universe(p, (s,)), scope=scope)
    assert validate(p, u).covered_scope == scope
    assert describe_source_coverage(u).scope == scope


def test_G00_03_F10_negative_missing_scope_dimension_is_not_invented():
    p = project(); s = cut(p); u = universe(p, (s,))
    bad = replace(u, scope=forge(u.scope, temporal_boundary=''))
    result = validate(p, bad)
    assert not result.ok and 'INVALID_SOURCE_UNIVERSE' in codes(result)
    with pytest.raises(ValueError, match='INVALID_SOURCE_COVERAGE_INPUT'):
        describe_source_coverage(bad)
