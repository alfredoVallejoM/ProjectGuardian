"""G00-09 and V06: real typed record roundtrips, not opaque payload acceptance."""
from dataclasses import replace
import copy
import json
import pytest
from foundation_completion import scenario
from foundation_b02 import entity
from guardian.domain.identity import EntityKind as K,RevisionId
from guardian.domain.outcomes import StatusObservation,TypedStatus,StatusAxis,MaterialStatus
from guardian.domain.foundation_records import ProjectRevision
from guardian.domain.scope import evaluate_scope
from guardian.persistence.schema_registry import (foundation_schema_registry,encode_record,decode_record,
    lookup_schema_descriptor,check_reader_compatibility,Compatibility,validate_schema_refs,ENVELOPE)


def examples():
    r,_,ids=scenario();s=r.view.sources[0].ref
    chosen={type(x).__name__:x for x in r.view.records}
    chosen['ProjectRevision']=ProjectRevision(identity=entity(r.view.project_id,K.PROJECT,'project-record'),source_refs=(s,),scope_ref=ids['scope-main'],definition=r.project)
    chosen['ProjectDefinition']=r.project
    chosen['SourceUniverseRevision']=r.universe
    chosen['SupportProfile']=r.profile
    chosen['StatusObservation']=StatusObservation(ids['obligation-now'],TypedStatus(StatusAxis.MATERIAL,MaterialStatus.NOT_RUN),s,ids['scope-main'],ids['obligation-now'].revision,'test-observer')
    chosen['ApplicabilityResult']=evaluate_scope(r.view._by_ref[ids['scope-main']].expression,r.profile,r.facts.scope).result
    return r,chosen


def encoded(name):
    request,values=examples();registry=foundation_schema_registry(request.view.revision)
    value=values[name]
    # Values without an intrinsic record identity require explicit envelope metadata.
    kwargs={}
    if name in ('ProjectDefinition','SupportProfile','ApplicabilityResult'):
        kwargs['envelope_ref']=entity(request.view.project_id,K.PROJECT,'transport-record')
        kwargs['source_refs']=(request.view.sources[0].ref,)
    if name=='SourceUniverseRevision':kwargs['source_refs']=(request.view.sources[0].ref,)
    result=encode_record(value,registry,**kwargs)
    assert result.ok,result.diagnostics
    return value,registry,result.value


NAMES=tuple(examples()[1])
assert len(NAMES)==19


@pytest.mark.parametrize('name',NAMES)
def test_every_admitted_foundational_record_roundtrips_with_exact_nominal_type(name):
    value,registry,wire=encoded(name)
    decoded=decode_record(json.dumps(wire,ensure_ascii=True).encode(),registry)
    assert decoded.ok,decoded.diagnostics
    assert type(decoded.value.record) is type(value) and decoded.value.record==value
    assert not decoded.value.normatively_admitted
    assert wire['schema']==ENVELOPE
    assert wire['project_id']['type']=='project_id' and wire['logical_id']['type']=='entity_id'
    assert wire['revision_id']['type']=='revision_id' and wire['source_refs']


@pytest.mark.parametrize('name',NAMES)
@pytest.mark.parametrize('attack',['missing','extra','wrong-variant','wrong-type'])
def test_each_record_contract_rejects_omission_extra_fields_and_nominal_type_changes(name,attack):
    value,registry,wire=encoded(name);payload=wire['payload'];fields=payload['fields']
    if attack=='missing':del fields[next(iter(fields))]
    if attack=='extra':fields['completed']=True
    if attack=='wrong-variant':payload['$type']='arbitrary.Executable'
    if attack=='wrong-type':fields[next(iter(fields))]=42
    result=decode_record(wire,registry)
    assert not result.ok
    assert result.diagnostics


@pytest.mark.parametrize('name',NAMES)
def test_codec_keeps_all_constructor_fields_including_explicit_null_and_empty(name):
    from dataclasses import fields
    value,_,wire=encoded(name)
    assert set(wire['payload']['fields'])=={f.name for f in fields(value) if f.init}


@pytest.mark.parametrize('attack',['schema','revision','payload-version','discriminant','unknown-feature','reader-feature','identity','source'])
def test_adversarial_envelope_cannot_change_contract_or_namespace(attack):
    _,registry,wire=encoded('ObligationRevision')
    if attack=='schema':wire['schema']='guardian/normative-envelope/v1'
    if attack=='revision':wire['registry_revision']='rev-'+'c'*32
    if attack=='payload-version':wire['payload_version']='v999'
    if attack=='discriminant':wire['record_type']='CapabilityRevision'
    if attack=='unknown-feature':wire['required_normative_features'].append('silent.new.law')
    if attack=='reader-feature':registry=replace(registry,reader_features=frozenset())
    if attack=='identity':wire['logical_id']['value']='wrong-entity'
    if attack=='source':wire['source_refs'][0]['entity']='wrong-source'
    assert not decode_record(wire,registry).ok


@pytest.mark.parametrize('field',['acceptance_contract','falsification_contract','verification_spec_refs','required_property_refs'])
@pytest.mark.parametrize('value',[None,{'$tuple':[]},''])
def test_acceptance_null_and_empty_never_become_default_normative_contract(field,value):
    _,registry,wire=encoded('ObligationRevision');wire['payload']['fields'][field]=value
    assert not decode_record(wire,registry).ok


@pytest.mark.parametrize('raw',[b'{"x":1,"x":2}',b'{"n":NaN}',b'{"n":Infinity}',b'{"n":-Infinity}',b'\xff'])
def test_hostile_JSON_is_rejected_without_normalization(raw):
    _,registry,_=encoded('ObjectiveRevision');assert not decode_record(raw,registry).ok


def test_unknown_enum_is_not_coerced_to_first_state_or_unknown():
    _,registry,wire=encoded('StatusObservation')
    wire['payload']['fields']['status']['fields']['value']['value']='universal-pass'
    result=decode_record(wire,registry)
    assert not result.ok and 'UNSUPPORTED_VARIANT' in result.diagnostics[0].reason


def test_large_integer_and_informational_extensions_are_exact_and_non_authoritative():
    request,values=examples();registry=foundation_schema_registry(request.view.revision);n=10**200+17
    result=encode_record(values['ObligationRevision'],registry,informational_extensions=(('info.resource_bound',n),('info.label','ámbito ∀')))
    assert result.ok
    wire=result.value
    assert wire['informational_extensions']['info.resource_bound']=={'$integer':str(n)}
    decoded=decode_record(json.dumps(wire).encode(),registry)
    assert decoded.ok and dict(decoded.value.informational_extensions)['info.resource_bound']==n
    assert not decoded.value.normatively_admitted
    wire['informational_extensions']['approved']=True
    assert not decode_record(wire,registry).ok


@pytest.mark.parametrize('raw',['-0','+1','01','1e99','0.5','1'])
def test_exact_integer_tag_is_canonical_and_cannot_smuggle_small_or_fractional_values(raw):
    _,registry,wire=encoded('ObjectiveRevision');wire['informational_extensions']['info.number']={'$integer':raw}
    assert not decode_record(wire,registry).ok


def test_reader_version_compatibility_is_explicit_and_never_migrates():
    _,registry,wire=encoded('ObjectiveRevision')
    descriptor=lookup_schema_descriptor(wire['payload_schema'],wire['payload_version'],registry).value
    assert check_reader_compatibility(descriptor,descriptor,registry.reader_features) is Compatibility.COMPATIBLE
    changed=replace(descriptor,semantic_version='different-meaning-v2')
    assert check_reader_compatibility(descriptor,changed,registry.reader_features) is Compatibility.REQUIRES_MIGRATION
    assert check_reader_compatibility(descriptor,descriptor,frozenset()) is Compatibility.UNSUPPORTED
    assert not lookup_schema_descriptor(descriptor.schema_id,'latest',registry).ok


def test_authority_runtime_is_not_a_deserializable_self_authenticating_record():
    req,_,_=scenario();registry=foundation_schema_registry(req.view.revision)
    assert not encode_record(req.authority,registry).ok
    _,_,wire=encoded('DecisionRevision');wire['payload']['$type']='authority.AuthorityContext'
    assert not decode_record(wire,registry).ok


def test_decoded_APPROVED_label_still_needs_original_external_approval_context():
    from guardian.domain.authority import validate_decision
    value,registry,wire=encoded('DecisionRevision')
    result=decode_record(wire,registry);assert result.ok
    assert not result.value.normatively_admitted
    assert not validate_decision(result.value.record,None).ok


def test_real_decoded_records_resolve_in_same_snapshot_and_orphans_do_not():
    request,_,ids=scenario();record=request.view._by_ref[ids['obligation-now']]
    registry=foundation_schema_registry(request.view.revision)
    decoded=decode_record(encode_record(record,registry).value,registry).value.record
    assert validate_schema_refs(decoded,request.view).ok
    view=replace(request.view,records=tuple(r for r in request.view.records if r.identity!=ids['property-main']))
    assert not validate_schema_refs(decoded,view).ok


def test_recursive_and_oversized_payloads_fail_closed():
    _,registry,wire=encoded('ObjectiveRevision');loop={'$tuple':[]};loop['$tuple'].append(loop)
    wire['informational_extensions']['info.loop']=loop
    assert not decode_record(wire,registry).ok
    assert not decode_record(b' '*4_000_001,registry).ok


def test_omitted_optional_constructor_field_is_not_silently_defaulted_by_decoder():
    _,registry,wire=encoded('ObjectiveRevision')
    assert 'exclusions' in wire['payload']['fields']
    del wire['payload']['fields']['exclusions']
    assert not decode_record(wire,registry).ok
