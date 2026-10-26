"""B08 evidence gate: byte pins, full populations and actual test phases.

This checks traceability/execution bindings, not semantic sufficiency, trust in
an author, or authenticity of a receipt. Pins must come from the operator, not
from a field inside the candidate. No gate result closes a campaign.
"""
from __future__ import annotations

import argparse
import ast
from hashlib import sha1, sha256
import json
from pathlib import Path, PurePosixPath

PLAN_SCHEMA = 'guardian/g00/acceptance-plan/v1'
RECEIPT_SCHEMA = 'guardian/pytest-execution/v1'
MAX_BYTES = 32_000_000
CLAUSES = frozenset(f'G00-{parent:02d}-F{clause:02d}' for parent in range(1, 13) for clause in range(1, 11))
PARENTS = frozenset(f'G00-{n:02d}' for n in range(1, 13))
APIS = frozenset(f'G00-API-{n:03d}' for n in range(1, 59))
ATTACKS = frozenset(f'ADV-{n:02d}' for n in range(1, 37))
VERTICALS = frozenset(f'G00-V{n:02d}' for n in range(1, 8))


def digest(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def load(raw: bytes):
    if type(raw) is not bytes or len(raw) > MAX_BYTES:
        raise ValueError('EVIDENCE_BYTE_LIMIT')
    return json.loads(raw, object_pairs_hook=_pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError('NONFINITE_EVIDENCE')))


def safe_file(root: Path, name: str) -> Path:
    if type(name) is not str or '\\' in name or not name or '\x00' in name:
        raise ValueError('UNSAFE_EVIDENCE_PATH')
    relative = PurePosixPath(name)
    if relative.is_absolute() or str(relative) != name or '..' in relative.parts:
        raise ValueError('UNSAFE_EVIDENCE_PATH')
    path = root
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('SYMLINK_EVIDENCE_REJECTED')
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError('EVIDENCE_FILE_MISSING_OR_OVERSIZED')
    return path


def _population(rows, expected, label, errors):
    if type(rows) is not list or any(type(row) is not dict or type(row.get('id')) is not str for row in rows):
        errors.append(label + '_INVALID_ROWS')
        return {}
    result = {row['id']: row for row in rows}
    if len(result) != len(rows) or set(result) != expected:
        errors.append(label + '_POPULATION_MISMATCH')
    return result


def _originals(root, pins, errors):
    specifications = (
        ('clauses', 'architecture/g00_functional_refinement.json', 'clauses', CLAUSES),
        ('apis', 'architecture/g00_api_contracts.json', 'functions', APIS),
        ('attacks', 'architecture/g00_validation_plan.json', 'attacks', ATTACKS),
        ('verticals', 'architecture/g00_validation_plan.json', 'verticals', VERTICALS),
    )
    result, cache = {}, {}
    if type(pins) is not dict or set(pins) != {spec[1] for spec in specifications}:
        errors.append('ORIGINAL_PIN_POPULATION_MISMATCH')
        return result
    for label, name, key, expected in specifications:
        try:
            if name not in cache:
                raw = safe_file(root, name).read_bytes()
                actual = sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
                if actual != pins[name]:
                    raise ValueError('ORIGINAL_BLOB_MISMATCH')
                cache[name] = load(raw)
            result[label] = _population(cache[name][key], expected, 'ORIGINAL_' + label.upper(), errors)
        except (ValueError, KeyError, TypeError, OSError) as exc:
            errors.append(str(exc) + ':' + name)
    clauses = result.get('clauses', {})
    for identity, row in clauses.items():
        if row.get('parent_obligation') != identity[:6]:
            errors.append('ORIGINAL_PARENT_MISMATCH:' + identity)
    return result


def _executed(cases, collected, links, label, errors):
    if type(links) is not list or not links or len(set(links)) != len(links):
        errors.append('TEST_LINKS_MISSING_OR_DUPLICATE:' + label)
        return
    for nodeid in links:
        item = cases.get(nodeid)
        if nodeid not in collected or not item:
            errors.append('REQUIRED_TEST_NOT_EXECUTED:' + str(nodeid))
            continue
        phases = item.get('phases', {})
        if (item.get('wasxfail') is not False or set(phases) != {'setup', 'call', 'teardown'}
                or any(phases.get(phase) != 'passed' for phase in ('setup', 'call', 'teardown'))):
            errors.append('REQUIRED_TEST_NOT_PASSED:' + nodeid)


def check(root: Path, plan_bytes: bytes, receipt_bytes: bytes, *,
          expected_plan_sha256: str, expected_receipt_sha256: str) -> dict:
    """Conservative structural acceptance; missing originals/rows/tests are HOLD.

    Even a successful result is not an independent semantic review. The caller
    must pin both documents independently; self-reported hashes are insufficient.
    """
    errors = []
    result = {'status': 'HOLD_INCOMPLETE_EVIDENCE', 'errors': errors,
              'campaign_closed': False, 'normatively_admitted': False,
              'semantic_sufficiency': 'NOT_ESTABLISHED_BY_LINK_CHECK',
              'receipt_authenticity': 'NOT_CHECKED', 'independent_review': 'NOT_CHECKED',
              'original_denominator': {'parents': 12, 'clauses': 120, 'apis': 58, 'attacks': 36, 'verticals': 7}}
    try:
        if type(plan_bytes) is not bytes or type(receipt_bytes) is not bytes:
            raise TypeError('PINNED_EVIDENCE_BYTES_REQUIRED')
        if digest(plan_bytes) != expected_plan_sha256 or digest(receipt_bytes) != expected_receipt_sha256:
            raise ValueError('EXTERNAL_EVIDENCE_PIN_MISMATCH')
        plan, receipt = load(plan_bytes), load(receipt_bytes)
        if plan.get('schema') != PLAN_SCHEMA or receipt.get('schema') != RECEIPT_SCHEMA:
            raise ValueError('UNSUPPORTED_EVIDENCE_SCHEMA')
        if plan.get('campaign') != 'G-00':
            raise ValueError('WRONG_CAMPAIGN')
        originals = _originals(root, plan.get('original_git_blobs'), errors)
        expected = plan.get('expected_collection')
        collected = receipt.get('collected')
        if (type(expected) is not list or not expected or type(collected) is not list
                or any(type(x) is not str for x in expected + collected)):
            raise ValueError('EXPLICIT_TEST_COLLECTION_REQUIRED')
        if len(set(expected)) != len(expected) or len(set(collected)) != len(collected) or set(expected) != set(collected):
            errors.append('TEST_COLLECTION_MISMATCH')
        if (receipt.get('exit_status') != 0 or type(receipt.get('exit_status')) is not int
                or receipt.get('collection_errors') != [] or receipt.get('deselected') != []):
            errors.append('INCOMPLETE_OR_FAILED_TEST_RUN')
        cases = _population(receipt.get('cases'), set(collected), 'EXECUTED_CASES', errors)
        before, after = receipt.get('files_before'), receipt.get('files_after')
        expected_files = plan.get('expected_input_files')
        if type(expected_files) is not dict or not expected_files or before != expected_files:
            errors.append('EXPECTED_INPUT_FILE_POPULATION_MISMATCH')
        if type(before) is not dict or not before or before != after:
            errors.append('EXECUTION_INPUTS_CHANGED_OR_UNBOUND')
            before = before if type(before) is dict else {}
        for name, checksum in before.items():
            try:
                if digest(safe_file(root, name).read_bytes()) != checksum:
                    errors.append('EXECUTED_FILE_CHANGED:' + name)
            except (ValueError, OSError) as exc:
                errors.append(str(exc) + ':' + str(name))
        selected = set(collected)
        _executed(cases, selected, collected, 'ENTIRE_COLLECTION', errors)
        for label, ids in (('clauses', CLAUSES), ('apis', APIS), ('attacks', ATTACKS), ('verticals', VERTICALS)):
            rows = _population(plan.get(label), ids, label.upper(), errors)
            for identity, row in rows.items():
                original = originals.get(label, {}).get(identity)
                if original is None or digest(canonical(original)) != row.get('original_sha256'):
                    errors.append('REQUIREMENT_BINDING_MISMATCH:' + identity)
                if label == 'clauses' and row.get('parent') != identity[:6]:
                    errors.append('CLAUSE_PARENT_MISMATCH:' + identity)
                paths = row.get('code_paths')
                if type(paths) is not list or not paths or any(name not in before for name in paths):
                    errors.append('IMPLEMENTATION_NOT_BOUND:' + identity)
                positive, negative = row.get('positive'), row.get('negative')
                _executed(cases, selected, positive, identity + ':positive', errors)
                _executed(cases, selected, negative, identity + ':negative', errors)
                if type(positive) is list and type(negative) is list and set(positive) & set(negative):
                    errors.append('SAME_TEST_USED_AS_POSITIVE_AND_FALSIFICATION:' + identity)
                for nodeid in (positive or []) + (negative or []):
                    if type(nodeid) is not str or nodeid.split('::')[0] not in before:
                        errors.append('TEST_SOURCE_NOT_BOUND:' + identity)
                review = row.get('contract_review')
                if type(review) is not str or not review.strip():
                    errors.append('SEMANTIC_REVIEW_UNRECORDED:' + identity)
                if label == 'apis' and original is not None:
                    owner, operation = row.get('owner'), row.get('operation')
                    if type(owner) is not str or type(operation) is not str or owner not in (paths or []):
                        errors.append('API_OWNER_OR_OPERATION_MISSING:' + identity)
                    else:
                        module = ast.parse(safe_file(root, owner).read_text(encoding='utf-8'))
                        if not any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == operation for n in module.body):
                            errors.append('API_SYMBOL_NOT_FOUND:' + identity)
                if label == 'attacks':
                    diagnostic = row.get('expected_diagnostic')
                    if type(diagnostic) is not str or not diagnostic.strip():
                        errors.append('ADVERSARY_DIAGNOSTIC_NOT_RECONCILED:' + identity)
                    elif not any(diagnostic in cases.get(node, {}).get('properties', {}).get('guardian.diagnostic', [])
                                 for node in (negative or [])):
                        errors.append('ADVERSARY_DIAGNOSTIC_NOT_RECORDED:' + identity)
        parents = _population(plan.get('parents'), PARENTS, 'PARENTS', errors)
        for identity, row in parents.items():
            if type(row.get('bridge_review')) is not str or not row['bridge_review'].strip():
                errors.append('PARENT_SUFFICIENCY_REVIEW_MISSING:' + identity)
        result['executed_cases'] = len(cases)
        result['source_files_checked'] = len(before)
    except (ValueError, TypeError, KeyError, AttributeError, OSError, SyntaxError, RecursionError) as exc:
        errors.append(str(exc) or type(exc).__name__)
    result['errors'] = sorted(set(errors))
    if not result['errors']:
        result['status'] = 'STRUCTURAL_EXECUTION_BINDINGS_CHECKED'
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--receipt-sha256', required=True)
    args = parser.parse_args()
    result = check(args.root, args.plan.read_bytes(), args.receipt.read_bytes(),
                   expected_plan_sha256=args.plan_sha256, expected_receipt_sha256=args.receipt_sha256)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result['status'] == 'STRUCTURAL_EXECUTION_BINDINGS_CHECKED' else 2


if __name__ == '__main__':
    raise SystemExit(main())
