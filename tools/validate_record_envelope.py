"""Validate the pinned wire envelope, NOT domain semantics or normative admission.

JSON Schema files are operator-pinned. Decoders of future domain entities are
not supplied by this tool. An opaque payload is never promoted to a typed record.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

MAX_BYTES = 2_000_000


def unique(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError('DUPLICATE_JSON_KEY')
        out[k] = v
    return out


def load(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError('BYTE_LIMIT')
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('NONFINITE_JSON')))
    stack = [(value, 0)]
    while stack:
        item, depth = stack.pop()
        if depth > 64:
            raise ValueError('DEPTH_LIMIT')
        if type(item) is float:
            raise ValueError('EXACT_NUMBER_ENCODING_REQUIRED')
        if type(item) is int and abs(item) > 9007199254740991:
            raise ValueError('EXACT_INTEGER_TAG_REQUIRED')
        if type(item) is str:
            item.encode('utf-8')
        if type(item) is dict:
            stack.extend((x, depth+1) for x in item.values())
        elif type(item) is list:
            stack.extend((x, depth+1) for x in item)
    return value


def validate(data, schema_root, pins, reader_features):
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    required = {'identity-v1.schema.json', 'status-v1.schema.json',
                'contract-ir-v0.1.schema.json', 'normative-envelope-v1.schema.json'}
    if type(pins) is not dict or set(pins) != required:
        raise ValueError('SCHEMA_PIN_POPULATION')
    resources = []; schemas = {}
    for filename in sorted(required):
        raw = (schema_root / filename).read_bytes()
        if hashlib.sha256(raw).hexdigest() != pins[filename]:
            raise ValueError('SCHEMA_PIN_MISMATCH:' + filename)
        schema = load(raw); Draft202012Validator.check_schema(schema)
        schemas[filename] = schema
        resources.append((schema['$id'], Resource.from_contents(schema)))
    def unavailable(uri):
        from referencing.exceptions import NoSuchResource
        raise NoSuchResource(ref=uri)
    registry = Registry(retrieve=unavailable).with_resources(resources)
    errors = sorted(Draft202012Validator(schemas['normative-envelope-v1.schema.json'],
                    registry=registry).iter_errors(data), key=lambda e: str(e.json_path))
    if errors:
        return {'status': 'REJECTED', 'errors': [e.json_path + ':' + e.message for e in errors]}
    unknown = set(data['required_normative_features']) - set(reader_features)
    if unknown:
        return {'status': 'REJECTED', 'errors': ['UNSUPPORTED_NORMATIVE_FEATURE:' + x for x in sorted(unknown)]}
    project = data['project_id']['value']
    if data['logical_id']['project'] != project or any(r['project'] != project or r['entity_kind'] != 'source' for r in data['source_refs']):
        return {'status': 'REJECTED', 'errors': ['ENVELOPE_PROJECT_OR_SOURCE_MISMATCH']}
    if data['record_type'] == 'CONTRACT_IR' and data['payload']['project']['value'] != project:
        return {'status': 'REJECTED', 'errors': ['ENVELOPE_PAYLOAD_PROJECT_MISMATCH']}
    # Transport acceptance is deliberately not a domain decoder or certificate.
    return dict(status='WIRE_FORMAT_CHECKED', domain_validation='NOT_CHECKED',
                reference_integrity='NOT_CHECKED', normative_admission='NOT_CHECKED')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', type=Path, required=True)
    parser.add_argument('--schema-root', type=Path, required=True)
    parser.add_argument('--pins', type=Path, required=True)
    parser.add_argument('--expected-pins-sha256', required=True)
    parser.add_argument('--reader-feature', action='append', default=[])
    args = parser.parse_args()
    try:
        raw = args.pins.read_bytes()
        if hashlib.sha256(raw).hexdigest() != args.expected_pins_sha256:
            raise ValueError('EXTERNAL_PINS_MISMATCH')
        result = validate(load(args.record.read_bytes()), args.schema_root, load(raw), args.reader_feature)
    except (ValueError, TypeError, KeyError, OSError, RecursionError) as exc:
        result = {'status': 'REJECTED', 'errors': [str(exc)]}
    print(json.dumps(result, sort_keys=True, ensure_ascii=True))
    return 0 if result['status'] == 'WIRE_FORMAT_CHECKED' else 1


if __name__ == '__main__':
    sys.exit(main())
