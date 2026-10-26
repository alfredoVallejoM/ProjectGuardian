"""The emitted schema is a real independent wire-shape check, not a codec alias."""
import json
from pathlib import Path
from dataclasses import replace
import pytest
from jsonschema import Draft202012Validator
from test_domain_record_codec import encoded,NAMES
from guardian.persistence.schema_registry import schema_document,decode_record


@pytest.mark.parametrize('name',NAMES)
def test_schema_accepts_each_wire_record_and_rejects_missing_and_unknown_fields(name):
    _,registry,wire=encoded(name);schema=schema_document(registry)
    Draft202012Validator.check_schema(schema);validator=Draft202012Validator(schema)
    assert not list(validator.iter_errors(wire))
    del wire['payload']['fields'][next(iter(wire['payload']['fields']))]
    assert list(validator.iter_errors(wire))


def test_generated_schema_matches_frozen_candidate_bytes_and_uses_only_local_refs():
    _,registry,_=encoded('ObjectiveRevision')
    root=Path(__file__).resolve().parents[2]
    generated=schema_document(registry)
    expected=json.loads((root/'schemas/guardian/domain/v2/domain-record.schema.json').read_bytes())
    assert generated==expected
    todo=[generated]
    while todo:
        x=todo.pop()
        if type(x) is dict:
            if '$ref' in x:assert x['$ref'].startswith('#/')
            todo.extend(x.values())
        elif type(x) is list:todo.extend(x)


def test_future_envelope_version_and_unknown_required_feature_rejected_not_ignored():
    _,registry,wire=encoded('ObligationRevision');validator=Draft202012Validator(schema_document(registry))
    wire['schema']='guardian/normative-envelope/v3'
    assert list(validator.iter_errors(wire)) and not decode_record(wire,registry).ok
    wire['schema']='guardian/normative-envelope/v2';wire['required_normative_features'].append('new.meaning.v99')
    assert list(validator.iter_errors(wire)) and not decode_record(wire,registry).ok
