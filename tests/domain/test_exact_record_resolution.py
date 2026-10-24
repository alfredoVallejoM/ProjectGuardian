"""G00-08 exact content, history and finite cut-scoped imports."""
from dataclasses import replace
import pytest
from foundation_b03 import scenario
from foundation_b02 import entity
from guardian.domain.identity import EntityKind as K, RevisionId
from guardian.domain.references import (RecordSnapshot, EntityImport, TrustedEntityImports,
    resolve_entity, validate_references)
from guardian.domain.source import ApprovedSourceImport


def imported(local, foreign, ids=None):
    p, s, records, snap, names = foreign
    approval = entity(local[0].project_id, K.DECISION, 'approve-import')
    grant = ApprovedSourceImport(local[0].project_id, s.ref, s.repository, s.path, approval, s)
    return TrustedEntityImports((EntityImport(grant, frozenset(ids or (names['property-shared'],)), snap),))


def test_exact_body_is_returned_not_a_matching_name_or_placeholder():
    p, s, records, snap, ids = scenario()
    outcome = resolve_entity(ids['property-shared'], snap, K.PROPERTY)
    assert outcome.ok and outcome.value.record is records[4]
    assert not outcome.value.historical and not outcome.value.imported and not outcome.value.normatively_admitted
    mismatch = resolve_entity(ids['property-shared'], snap, K.CAPABILITY)
    assert mismatch.diagnostics[0].code == 'WRONG_ID_KIND'
    assert resolve_entity(s.ref, snap, K.SOURCE).diagnostics[0].code == 'SOURCE_RESOLVER_REQUIRED'


def test_anchor_presence_does_not_claim_that_content_is_implemented():
    _, _, records, snap, _ = scenario()
    assert snap.contains_entity(records[0].scope_ref)
    outcome = resolve_entity(records[0].scope_ref, snap, K.SCOPE)
    assert not outcome.ok and outcome.diagnostics[0].code == 'REFERENCED_CONTENT_UNAVAILABLE'


def test_no_latest_fallback_and_historical_never_promoted_to_current():
    _, _, records, snap, ids = scenario()
    old = records[4]
    new_ref = replace(old.identity, revision=RevisionId('rev-'+'b'*32))
    new = replace(old, identity=new_ref, statement='A new declared revision')
    with pytest.raises(ValueError, match='MULTIPLE_CURRENT_REVISIONS'):
        replace(snap, records=snap.records+(new,))
    revised = replace(snap, records=snap.records+(new,), historical=frozenset({old.identity}))
    assert resolve_entity(old.identity, revised, K.PROPERTY).value.record is old
    assert resolve_entity(new.identity, revised, K.PROPERTY).value.record is new
    assert resolve_entity(old.identity, revised, K.PROPERTY, require_current=True).diagnostics[0].code == 'HISTORICAL_REFERENCE_NOT_CURRENT'
    absent = replace(old.identity, revision=RevisionId('rev-'+'c'*32))
    assert resolve_entity(absent, revised, K.PROPERTY).diagnostics[0].code == 'UNKNOWN_REVISION'


def test_duplicate_revision_rejects_overwrite_and_input_is_not_mutated():
    _, _, records, snap, ids = scenario()
    before = hash(snap)
    with pytest.raises(ValueError, match='DUPLICATE_LOGICAL_ID'):
        replace(snap, records=snap.records+(records[4],))
    for _ in range(4):
        assert resolve_entity(ids['property-shared'], snap, K.PROPERTY).value.record == records[4]
    assert hash(snap) == before


def test_scoped_import_requires_exact_entity_and_material_source_cut():
    a, b = scenario(), scenario('project-beta')
    target = b[4]['property-shared']
    assert resolve_entity(target, a[3], K.PROPERTY).diagnostics[0].code == 'FORBIDDEN_CROSS_PROJECT_REF'
    grants = imported(a, b)
    ok = resolve_entity(target, a[3], K.PROPERTY, grants)
    assert ok.ok and ok.value.record is b[2][4] and ok.value.imported
    other = b[4]['capability-one']
    assert resolve_entity(other, a[3], K.CAPABILITY, grants).diagnostics[0].code == 'UNAPPROVED_IMPORT_SCOPE'
    drifted = replace(b[1], commit='d'*40)
    drifted_snapshot = replace(b[3], sources=(drifted,))
    with pytest.raises(ValueError, match='IMPORT_MATERIAL_CUT_MISMATCH'):
        replace(grants.entries[0], snapshot=drifted_snapshot)


def test_two_projects_same_id_text_do_not_collide_and_conflicting_imports_fail():
    a, b = scenario(), scenario('project-beta')
    target = b[4]['property-shared']; grants = imported(a, b)
    assert a[4]['property-shared'].entity.value == target.entity.value
    changed = replace(b[2][4], guarantee='Different content at same revision')
    alternate = replace(b[3], records=tuple(changed if r.identity == target else r for r in b[3].records))
    second = replace(grants.entries[0], snapshot=alternate)
    for entries in ((grants.entries[0], second), (second, grants.entries[0])):
        result = resolve_entity(target, a[3], K.PROPERTY, TrustedEntityImports(entries))
        assert not result.ok and result.diagnostics[0].code == 'CONFLICTING_IMPORT_CONTENT'


def test_local_reference_cycles_are_not_mistaken_for_execution_dags():
    _, _, records, snapshot, _ = scenario()
    report = validate_references(records, snapshot)
    assert report.checked > 40
    # Objective↔Capability cycles are resolved. Scope/verification/constitution
    # bodies are still absent and must remain explicit, not fabricated.
    assert report.diagnostics
    assert {x.code for x in report.diagnostics} == {'REFERENCED_CONTENT_UNAVAILABLE'}
    assert report.diagnostics == validate_references(tuple(reversed(records)), snapshot).diagnostics


@pytest.mark.parametrize('bad', [None, (), 'latest', 0, True])
def test_invalid_reference_inputs_fail_closed(bad):
    s = scenario()
    assert resolve_entity(bad, s[3], K.PROPERTY).diagnostics[0].code == 'INVALID_REFERENCE_INPUT'
    assert resolve_entity(s[4]['property-shared'], bad, K.PROPERTY).diagnostics[0].code == 'INVALID_REFERENCE_INPUT'


def test_import_descriptors_are_not_authority_if_context_is_not_passed():
    a, b = scenario(), scenario('project-beta')
    grants = imported(a, b)
    assert resolve_entity(b[4]['property-shared'], a[3], K.PROPERTY, grants.entries[0]).diagnostics[0].code == 'FORBIDDEN_CROSS_PROJECT_REF'


def test_same_record_bytes_at_two_conflicting_material_cuts_are_not_first_wins():
    a,b=scenario(),scenario('project-beta');first=imported(a,b).entries[0]
    changed_cut=replace(b[1],commit='e'*40)
    second=replace(first, source_grant=replace(first.source_grant,pinned_cut=changed_cut),
                   snapshot=replace(b[3],sources=(changed_cut,)))
    for order in ((first,second),(second,first)):
        result=resolve_entity(b[4]['property-shared'],a[3],K.PROPERTY,TrustedEntityImports(order))
        assert result.diagnostics[0].code=='CONFLICTING_IMPORT_CONTENT'


def test_reference_index_is_immutable_and_contains_actual_bodies():
    _,_,records,snapshot,ids=scenario()
    with pytest.raises(TypeError):
        snapshot._by_ref[ids['property-shared']]=records[0]
    assert snapshot._by_ref[ids['property-shared']] is records[4]
    with pytest.raises(ValueError,match='RECORD_SOURCE_OUTSIDE_SNAPSHOT'):
        replace(snapshot,sources=())


def test_alias_resolution_composes_with_exact_content_without_losing_revision():
    from guardian.domain.identity import Alias,AliasIndex,bind_alias,resolve_alias
    _,source,records,snapshot,ids=scenario()
    outcome=bind_alias(AliasIndex(),ids['property-shared'],Alias('Propiedad compartida'),source.ref)
    resolved=resolve_alias(outcome.index,snapshot.project_id,K.PROPERTY,Alias('Propiedad compartida'))
    assert resolved.ok
    result=resolve_entity(resolved.value,snapshot,K.PROPERTY)
    assert result.ok and result.value.record is records[4]
