"""B02→B03→content resolution→inspection→LC03/LC04, no mock semantics."""
from dataclasses import replace
from foundation_b03 import scenario
from foundation_b02 import entity, bundle_context
from guardian.domain.identity import EntityKind as K
from guardian.domain.references import EntityImport, TrustedEntityImports
from guardian.domain.source import ApprovedSourceImport
from guardian.application.contract_service import inspect_contract
from guardian.spec_lang.contract import SymbolBinding
from guardian.spec_lang.syntax import analyze_source
from guardian.spec_lang.resolution import resolve_analyses


def test_productive_contract_is_inspected_and_referenced_by_gsl_without_typecheck_promotion():
    p, s, records, snapshot, ids = scenario()
    original = hash(snapshot)
    inspected = inspect_contract(ids['obligation-now'], snapshot)
    assert inspected.ok and inspected.value.record is records[5]
    assert inspected.value.qualification == 'NOT_CHECKED'
    assert inspected.value.scope_evaluation == 'NOT_EVALUATED'
    assert {d.code for d in inspected.value.reference_validation.diagnostics} == {'REFERENCED_CONTENT_UNAVAILABLE'}
    raw = b'gsl "0.1"; project "project-alpha"; obligation "obligation-authored" { requires: property("shared_property"); }'
    bundle, context = bundle_context(p, s, raw)
    context = replace(context, symbols=(SymbolBinding('shared_property', ids['property-shared'], s.ref),))
    parsed = analyze_source(bundle, context, source_format='gsl')
    linked = resolve_analyses((parsed,), context, snapshot=snapshot)
    assert linked.ok, linked.diagnostics
    assert linked.references[0].target == ids['property-shared']
    assert linked.references[0].basis == 'SNAPSHOT_RECORD'
    assert not linked.compiled and not linked.typechecked and hash(snapshot) == original
    incomplete = replace(snapshot, records=tuple(r for r in snapshot.records if r.identity != ids['property-shared']))
    rejected = resolve_analyses((parsed,), context, snapshot=incomplete)
    assert not rejected.ok and rejected.diagnostics[0].code == 'ORPHAN_REFERENCE'


def test_import_inspection_does_not_turn_a_record_grant_into_graph_traversal_permission():
    a, b = scenario(), scenario('project-beta')
    target=b[4]['property-shared'];s=b[1]
    source_grant=ApprovedSourceImport(a[0].project_id,s.ref,s.repository,s.path,
        entity(a[0].project_id,K.DECISION,'approve-import'),s)
    grants=TrustedEntityImports((EntityImport(source_grant,frozenset({target}),b[3]),))
    inspected=inspect_contract(target,a[3],grants)
    assert inspected.ok and inspected.value.record is b[2][4]
    assert inspected.value.import_boundary=='RECORD_ONLY_NO_TRANSITIVE_GRANT'
    assert inspected.value.reference_validation is None
    assert not inspect_contract(b[4]['capability-one'],a[3],grants).ok


def test_foreign_property_validation_needs_explicit_cut_and_entity_grants():
    from guardian.domain.capability import validate_capability
    a,b=scenario(),scenario('project-beta');target=b[4]['property-shared'];s=b[1]
    cap=replace(a[2][2],property_refs=(target,))
    assert not validate_capability(cap,a[3]).ok
    grant=ApprovedSourceImport(a[0].project_id,s.ref,s.repository,s.path,
        entity(a[0].project_id,K.DECISION,'approve-import'),s)
    imports=TrustedEntityImports((EntityImport(grant,frozenset({target}),b[3]),))
    assert validate_capability(cap,a[3],grants=imports).ok


def test_canonical_identity_facades_use_the_same_content_resolver():
    from guardian.domain.identity import resolve_entity, validate_references
    from guardian.domain.references import resolve_entity as engine
    _,_,records,snapshot,ids=scenario()
    actual=resolve_entity(ids['property-shared'],snapshot,K.PROPERTY)
    assert actual==engine(ids['property-shared'],snapshot,K.PROPERTY)
    assert actual.value.record is records[4]
    report=validate_references(records,snapshot)
    assert not report.ok and {d.code for d in report.diagnostics}=={'REFERENCED_CONTENT_UNAVAILABLE'}
