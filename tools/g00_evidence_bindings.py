"""Strict execution/API bindings for B08; no authentication or semantic proof.

Every module mapping is supplied in the externally pinned acceptance plan.
Installed copies are allowed only at explicit paths and with identical pinned
bytes. These checks do not attest to a hostile runner or transient file changes.
"""
from __future__ import annotations
import re
from pathlib import PurePosixPath

_SHA256 = re.compile(r'[0-9a-f]{64}\Z', re.ASCII)
_MODULE = re.compile(r'guardian(?:\.[A-Za-z_][A-Za-z_0-9]*)*\Z', re.ASCII)


def _hash(value):
    return type(value) is str and _SHA256.fullmatch(value) is not None


def _runtime_path(value):
    if type(value) is not str or not value or '\\' in value or '\x00' in value:
        return False
    path = PurePosixPath(value)
    return str(path) == value and '..' not in path.parts and path.suffix == '.py'


def check_runtime_modules(plan, receipt, before, errors):
    expected = plan.get('expected_runtime_modules')
    loaded = receipt.get('loaded_guardian_modules')
    if type(expected) is not dict or not expected:
        errors.append('RUNTIME_MODULE_PLAN_REQUIRED')
        return
    if type(loaded) is not dict or not loaded:
        errors.append('RUNTIME_MODULE_RECEIPT_REQUIRED')
        return
    if set(loaded) != set(expected):
        errors.append('RUNTIME_MODULE_POPULATION_MISMATCH')
    for name, row in expected.items():
        if type(name) is not str or _MODULE.fullmatch(name) is None:
            errors.append('INVALID_RUNTIME_MODULE_NAME')
            continue
        if type(row) is not dict or set(row) != {'source_path', 'sha256', 'allowed_paths'}:
            errors.append('INVALID_RUNTIME_MODULE_PLAN:' + name)
            continue
        source, checksum, allowed = row['source_path'], row['sha256'], row['allowed_paths']
        if (not _runtime_path(source) or PurePosixPath(source).is_absolute()
                or not source.startswith('src/') or not _hash(checksum)
                or type(allowed) is not list or not allowed
                or any(not _runtime_path(p) for p in allowed)
                or len(set(allowed)) != len(allowed)):
            errors.append('INVALID_RUNTIME_MODULE_PLAN:' + name)
            continue
        if before.get(source) != checksum:
            errors.append('RUNTIME_MODULE_SOURCE_NOT_BOUND:' + name)
        actual = loaded.get(name)
        if type(actual) is not dict or set(actual) != {'path', 'sha256'}:
            errors.append('INVALID_RUNTIME_MODULE_OBSERVATION:' + name)
            continue
        if not _runtime_path(actual['path']) or actual['path'] not in allowed:
            errors.append('RUNTIME_MODULE_PATH_MISMATCH:' + name)
        if not _hash(actual['sha256']) or actual['sha256'] != checksum:
            errors.append('RUNTIME_MODULE_BYTES_MISMATCH:' + name)


def check_properties(cases, errors):
    """Reject scalars before matching exact codes; never substring membership."""
    for nodeid, case in cases.items():
        properties = case.get('properties')
        if (type(properties) is not dict or any(type(k) is not str or not k for k in properties)
                or any(type(v) is not list or any(type(x) is not str or not x for x in v)
                       for v in properties.values())):
            errors.append('INVALID_TEST_PROPERTIES:' + nodeid)


def observed_code(case, code):
    properties = case.get('properties')
    if type(properties) is not dict:
        return False
    values = properties.get('guardian.diagnostic')
    return (type(values) is list and all(type(v) is str for v in values)
            and any(v == code for v in values))


def api_adapters(plan, expected_pin, originals, before, canonical, digest, errors):
    """Optional explicit endpoint adaptations, separately pinned by the operator.

    Reviews are evidence records, not machine-verified proofs of equivalence or
    authenticated ratifications. With no external adapter pin, drift is rejected.
    """
    rows = plan.get('api_adapters', [])
    if type(rows) is not list:
        errors.append('INVALID_API_ADAPTERS')
        return {}
    if not rows:
        if expected_pin is not None:
            errors.append('API_ADAPTER_PIN_WITHOUT_ADAPTERS')
        return {}
    if not _hash(expected_pin) or digest(canonical(rows)) != expected_pin:
        errors.append('EXTERNAL_API_ADAPTER_PIN_MISMATCH')
        return {}
    keys = {'id', 'original_sha256', 'original_owner', 'original_operation',
            'target_owner', 'target_operation', 'preconditions_review',
            'postconditions_review', 'errors_review', 'review_path'}
    result = {}
    for row in rows:
        if type(row) is not dict or set(row) != keys or any(type(v) is not str or not v.strip() for v in row.values()):
            errors.append('INVALID_API_ADAPTER_RECORD')
            continue
        identity = row['id']
        original = originals.get(identity)
        if (identity in result or original is None
                or row['original_sha256'] != digest(canonical(original))
                or row['original_owner'] != original.get('owner_path')
                or row['original_operation'] != original.get('function_name')
                or row['target_owner'] not in before or row['review_path'] not in before):
            errors.append('API_ADAPTER_ORIGINAL_OR_REVIEW_MISMATCH:' + identity)
            continue
        result[identity] = row
    return result


def check_api_endpoint(identity, row, original, adapters, errors):
    expected_owner, expected_name = original.get('owner_path'), original.get('function_name')
    if type(expected_owner) is not str or not expected_owner or type(expected_name) is not str or not expected_name:
        errors.append('ORIGINAL_API_ENDPOINT_MISSING:' + identity)
        return
    actual = row.get('owner'), row.get('operation')
    if actual == (expected_owner, expected_name):
        return
    adaptation = adapters.get(identity)
    if adaptation is None or actual != (adaptation['target_owner'], adaptation['target_operation']):
        errors.append('API_CONTRACT_ENDPOINT_MISMATCH:' + identity)
