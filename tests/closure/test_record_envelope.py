"""Versioned envelopes: wire shape is never normative or domain validity."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest
from test_external_contract import case
from guardian.domain.identity import EntityKind, EntityId, ProjectId, encode_identity
from guardian.domain.outcomes import StatusAxis, parse_status, encode_status

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('envelope_validator',ROOT/'tools/validate_record_envelope.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
SCHEMAS=ROOT/'schemas/guardian'
PINS={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in SCHEMAS.glob('*.schema.json')}
FEATURES=['identity.nominal.v1','status.axes.v1','gsl0.ir.v0.1']


def envelope(kind='CONTRACT_IR'):
    _,e,c=case()
    logical=encode_identity(EntityId(ProjectId(e['project']),EntityKind.SOURCE,'source-main'))
    payload,schema,feature=c,'guardian/gsl0/typed-ir/v0.1',FEATURES[2]
    if kind=='IDENTITY_RECORD':payload,schema,feature=e['source'],'guardian.identity/v1',FEATURES[0]
    elif kind=='STATUS_RECORD':payload,schema,feature=encode_status(parse_status(StatusAxis.MATERIAL,'not_run').value),'guardian.status/v1',FEATURES[1]
    return dict(schema='guardian/normative-envelope/v1',record_type=kind,project_id=c['project'],logical_id=logical,
        revision_id=dict(schema='guardian.identity/v1',type='revision_id',value=e['revision']),
        required_normative_features=[feature],source_refs=[e['source']],payload_schema=schema,payload=payload)


def check(value,features=FEATURES,pins=PINS):return mod.validate(value,SCHEMAS,pins,features)


@pytest.mark.parametrize('kind',['IDENTITY_RECORD','STATUS_RECORD','CONTRACT_IR'])
def test_existing_wire_kinds_roundtrip_without_semantic_promotion(kind):
    value=envelope(kind);roundtrip=mod.load(json.dumps(value).encode())
    assert roundtrip==value
    r=check(roundtrip);assert r['status']=='WIRE_FORMAT_CHECKED' and r['normative_admission']=='NOT_CHECKED'


@pytest.mark.parametrize('key',list(envelope()))
@pytest.mark.parametrize('attack',['missing','null'])
def test_required_fields_never_default_missing_or_null(key,attack):
    value=envelope()
    if attack=='missing':del value[key]
    else:value[key]=None
    assert check(value)['status']=='REJECTED'


def test_unknown_feature_and_unimplemented_record_kind_fail_closed():
    value=envelope();value['required_normative_features'].append('unapproved.law.v9')
    assert 'UNSUPPORTED_NORMATIVE_FEATURE' in check(value)['errors'][0]
    value=envelope();value['record_type']='OBLIGATION_REVISION'
    assert check(value)['status']=='REJECTED'


@pytest.mark.parametrize('features',[[],['unapproved.law.v9']])
def test_reader_support_is_explicit_not_read_from_candidate(features):
    assert check(envelope(),features=features)['status']=='REJECTED'


def test_unknown_field_cannot_change_normative_result():
    value=envelope();value['completed']=True
    assert check(value)['status']=='REJECTED'
    value=envelope();value['informational_extensions']={'normative.approved':True}
    assert check(value)['status']=='REJECTED'


def test_large_integers_are_tagged_and_exact_not_rounded():
    value=envelope();number=10**80+7
    value['informational_extensions']={'info.bounds':{'$type':'exact_integer','decimal':str(number)}}
    decoded=mod.load(json.dumps(value).encode())
    assert check(decoded)['status']=='WIRE_FORMAT_CHECKED'
    assert int(decoded['informational_extensions']['info.bounds']['decimal'])==number
    value['informational_extensions']['info.bounds']=number
    with pytest.raises(ValueError,match='EXACT_INTEGER_TAG_REQUIRED'):mod.load(json.dumps(value).encode())


@pytest.mark.parametrize('raw',[b'{"x":NaN}',b'{"x":Infinity}',b'{"x":1,"x":2}',b'{"x":0.3}'])
def test_json_rejects_ambiguous_or_inexact_numbers(raw):
    with pytest.raises(ValueError):mod.load(raw)


def test_exact_integer_string_is_canonical():
    for value in ('00','-0','+1','1e20','0.5'):
        e=envelope();e['informational_extensions']={'info.bound':{'$type':'exact_integer','decimal':value}}
        assert check(e)['status']=='REJECTED'


def test_unknown_schema_and_enum_reject_without_mapping_to_unknown_state():
    value=envelope('STATUS_RECORD');value['payload']['value']='DONE'
    assert check(value)['status']=='REJECTED'
    value=envelope('IDENTITY_RECORD');value['payload']['schema']='guardian.identity/v9'
    assert check(value)['status']=='REJECTED'


def test_extra_ir_fields_missing_property_semantics_and_duplicate_fields_reject():
    for attack in ('extra','duplicate','missing'):
        value=envelope();p=value['payload']['declarations'][4]
        if attack=='extra':p['fields'].append({'name':'approved','value':{'tag':'bool','value':True}})
        elif attack=='duplicate':p['fields'].append(copy.deepcopy(p['fields'][0]))
        else:p['fields'].pop()
        assert check(value)['status']=='REJECTED'


def test_false_schema_pins_fail_before_untrusted_schema_interpretation():
    pins=copy.deepcopy(PINS);pins['normative-envelope-v1.schema.json']='0'*64
    with pytest.raises(ValueError,match='SCHEMA_PIN_MISMATCH'):check(envelope(),pins=pins)


def test_cross_project_envelope_is_not_accepted_as_transport_identity():
    value=envelope();value['project_id']['value']='foreign-project'
    assert check(value)['status']=='REJECTED'
