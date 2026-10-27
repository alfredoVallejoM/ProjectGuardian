"""G00-03 public-boundary falsifications, not a synthetic acceptance-gate test."""
from dataclasses import fields, replace
import pytest
from foundation_b02 import project, cut, universe, entity
from guardian.domain.identity import EntityKind as K
from guardian.domain.outcomes import SourceStatus
from guardian.domain.source import (
    SourceEntry, SourceExclusion, MissingSource, HistoryRole,
    validate_source_universe, validate_inclusion_exclusion,
)


def reconstructed(value, **changes):
    """Untrusted exact-type object: bypass construction, not the validator."""
    obj = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(obj, field.name, changes.get(field.name, getattr(value, field.name)))
    return obj


@pytest.mark.parametrize('field,value', [
    ('role', 'base'), ('acquisition', 'semantic_reconciled'), ('lineage', ''),
    ('baseline_ref', 'latest'),
])
def test_entry_metadata_is_revalidated_before_history_or_acquisition(field, value):
    p = project(); s = cut(p); u = universe(p, (s,))
    bad = reconstructed(u.entries[0], **{field: value})
    supplied = replace(u, entries=(bad,))
    result = validate_source_universe(supplied, p, {s.ref: s})
    assert not result.ok, (field, result)
    assert 'INVALID_SOURCE_ENTRY' in {d.code for d in result.diagnostics}
    assert not result.eligible_for_complete_claim


@pytest.mark.parametrize('field,value', [('reason', ''), ('approval_ref', 'approved')])
def test_unjustified_exclusion_is_rejected_at_public_boundary(field, value):
    p = project(); s = cut(p); other = cut(p, name='source-other', path='spec/other.gsl')
    decision = entity(p.project_id, K.DECISION, 'decision-exclude')
    exclusion = SourceExclusion(other.ref, 'outside selected corpus', decision)
    bad = reconstructed(exclusion, **{field: value})
    u = universe(p, (s, other), included=(s.ref,), excluded=(bad,))
    result = validate_inclusion_exclusion(u)
    assert 'EXCLUSION_UNJUSTIFIED' in {d.code for d in result}, result
    validation = validate_source_universe(u, p, {s.ref: s, other.ref: other},
        trusted_exclusion_decisions=frozenset({decision}))
    assert not validation.ok
    assert 'EXCLUSION_UNJUSTIFIED' in {d.code for d in validation.diagnostics}


def test_unrelated_entity_kind_cannot_be_a_source_include():
    p = project(); s = cut(p); wrong = entity(p.project_id, K.OBLIGATION, 'not-a-source')
    u = universe(p, (s,), included=(wrong,))
    diagnostics = validate_inclusion_exclusion(u)
    assert 'INVALID_SOURCE_MEMBERSHIP_REF' in {d.code for d in diagnostics}, diagnostics


def test_missing_source_descriptor_keeps_a_real_reason():
    p = project(); s = cut(p)
    missing = reconstructed(MissingSource('urn:missing:item', 'unavailable'), reason='')
    u = universe(p, (s,), missing=(missing,))
    result = validate_source_universe(u, p, {s.ref: s})
    assert 'INVALID_MISSING_SOURCE' in {d.code for d in result.diagnostics}, result


def test_valid_reconstructed_records_are_not_rejected_wholesale():
    p = project(); s = cut(p); u = universe(p, (s,))
    same = reconstructed(u, entries=(reconstructed(u.entries[0]),))
    result = validate_source_universe(same, p, {s.ref: s})
    assert result.ok and same == u
    assert validate_inclusion_exclusion(same) == ()


@pytest.mark.parametrize('descriptor', ['entry', 'exclusion', 'missing'])
def test_untrusted_subclass_hooks_are_not_called_by_metadata_validation(descriptor):
    p = project(); s = cut(p); u = universe(p, (s,))
    decision = entity(p.project_id, K.DECISION, 'decision-exclude')
    base = {'entry': u.entries[0],
            'exclusion': SourceExclusion(s.ref, 'explicit reason', decision),
            'missing': MissingSource('urn:missing:item', 'unavailable')}[descriptor]
    def forbidden(self):
        raise AssertionError('caller hook executed by the validator')
    hostile_type = type('UntrustedDescriptor', (type(base),), {'__post_init__': forbidden})
    supplied = object.__new__(hostile_type)
    for field in fields(base):
        object.__setattr__(supplied, field.name, getattr(base, field.name))
    if descriptor == 'entry': u = replace(u, entries=(supplied,))
    elif descriptor == 'exclusion': u = replace(u, excluded=(supplied,))
    else: u = replace(u, known_missing=(supplied,))
    result = validate_source_universe(u, p, {s.ref: s})
    assert not result.ok
    code = {'entry': 'INVALID_SOURCE_ENTRY', 'exclusion': 'EXCLUSION_UNJUSTIFIED',
            'missing': 'INVALID_MISSING_SOURCE'}[descriptor]
    assert code in {d.code for d in result.diagnostics}


def test_multiple_metadata_errors_are_located_without_mutating_universe():
    p = project(); s = cut(p); u = universe(p, (s,))
    missing = reconstructed(MissingSource('urn:missing:item', 'unavailable'), reason='')
    bad = replace(u, entries=(reconstructed(u.entries[0], acquisition='observed'),),
                  known_missing=(missing,))
    before = (bad.entries, bad.included, bad.excluded, bad.known_missing)
    result = validate_source_universe(bad, p, {s.ref: s})
    assert {(d.code, d.path) for d in result.diagnostics} == {
        ('INVALID_SOURCE_ENTRY', '$.entries[0]'),
        ('INVALID_MISSING_SOURCE', '$.known_missing[0]')}
    assert (bad.entries, bad.included, bad.excluded, bad.known_missing) == before
    assert not result.eligible_for_complete_claim


def test_missing_entry_cut_is_diagnosed_instead_of_crashing():
    p = project(); s = cut(p); u = universe(p, (s,))
    bad = reconstructed(u.entries[0]); object.__delattr__(bad, 'cut')
    result = validate_source_universe(replace(u, entries=(bad,)), p, {s.ref: s})
    assert not result.ok
    assert result.diagnostics[0].code == 'INVALID_SOURCE_ENTRY'
