"""API-008/F06: snapshots are data, never authority for their own cached lookup."""
from dataclasses import fields, replace
from types import MappingProxyType
import pytest
from foundation_b03 import scenario
from guardian.domain.identity import EntityKind as K, RevisionId, resolve_entity
from guardian.domain.references import RecordSnapshot, resolve_entity as resolve_content


def forged(record, **changes):
    obj=object.__new__(type(record))
    for f in fields(record):
        object.__setattr__(obj,f.name,changes.get(f.name,getattr(record,f.name)))
    return obj


def test_F06_forged_cache_cannot_substitute_record_with_same_identity():
    _,_,records,view,ids=scenario();wanted=ids['property-shared']
    fake=replace(records[4],guarantee='Changed outside the snapshot record population')
    by_ref=dict(view._by_ref);by_ref[wanted]=fake
    changed=forged(view,_by_ref=MappingProxyType(by_ref))
    result=resolve_entity(wanted,changed,K.PROPERTY)
    assert not result.ok or result.value.record is records[4]
    assert changed._by_ref[wanted] is fake  # resolver must not mutate its input


def test_F06_corrupt_snapshot_revision_does_not_resolve():
    _,_,_,view,ids=scenario()
    changed=forged(view,revision=forged(view.revision,value='main'))
    result=resolve_entity(ids['property-shared'],changed,K.PROPERTY)
    assert not result.ok and result.diagnostics[0].code=='INVALID_REFERENCE_INPUT'


def test_F06_malformed_import_context_is_typed_rejection_not_stopiteration():
    from guardian.domain.source import ApprovedSourceImport
    from guardian.domain.references import EntityImport,TrustedEntityImports
    local=scenario();foreign=scenario('project-beta');wanted=foreign[4]['property-shared']
    from foundation_b02 import entity
    approval=entity(local[0].project_id,K.DECISION,'approve-import')
    cut=foreign[1];grant=ApprovedSourceImport(local[0].project_id,cut.ref,cut.repository,cut.path,approval,cut)
    entry=EntityImport(grant,frozenset({wanted}),foreign[3])
    removed=replace(foreign[3],records=tuple(x for x in foreign[3].records if x.identity!=wanted))
    forged_entry=forged(entry,snapshot=removed)
    imports=forged(TrustedEntityImports(),entries=(forged_entry,))
    result=resolve_entity(wanted,local[3],K.PROPERTY,imports)
    assert not result.ok
    assert result.diagnostics[0].code=='INVALID_IMPORT_CONTEXT'


@pytest.mark.parametrize('bad',[None,0,''])
def test_F06_invalid_reference_and_diagnostic_path_are_total(bad):
    view=scenario()[3]
    result=resolve_content(None,view,K.PROPERTY,path=bad)
    assert not result.ok and result.diagnostics[0].path=='$'
