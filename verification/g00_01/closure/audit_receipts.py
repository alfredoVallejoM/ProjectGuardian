"""Audit retained execution receipts; not authentication or an independent review.

The compact representation reconstructs the two original JSON byte streams.
Acceptance is conditional on separately selected candidate, receipt and package
pins. This verifier does not rerun pytest and does not close G-00 or grant trust.
"""
from __future__ import annotations
import argparse
import base64
import copy
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath


def raw_json(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode('utf-8')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_encoded(path):
    """Read the fixed three text parts; no candidate-controlled path lookup."""
    path = Path(path)
    return b"".join(path.with_name(path.name + f".part{i:02}").read_bytes().strip()
                    for i in range(1, 4))


def unpack(raw, expected_sha256):
    if type(raw) is not bytes or len(raw) > 100000:
        raise ValueError('ENCODED_EVIDENCE_LIMIT')
    compressed = base64.b64decode(raw.strip(), validate=True)
    decoder = lzma.LZMADecompressor(memlimit=96 * 1024 * 1024)
    decoded = decoder.decompress(compressed, max_length=4_000_001)
    if len(decoded) > 4_000_000 or not decoder.eof or decoder.unused_data:
        raise ValueError('DECODED_EVIDENCE_LIMIT_OR_TRAILING_DATA')
    if sha(decoded) != expected_sha256:
        raise ValueError('EVIDENCE_PACKAGE_PIN_MISMATCH')
    def pairs(rows):
        result = {}
        for k, v in rows:
            if k in result:
                raise ValueError('DUPLICATE_JSON_KEY')
            result[k] = v
        return result
    return json.loads(decoded, object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('NONFINITE_JSON')))


def reconstruct(package):
    if package['schema'] != 'guardian/paired-pytest-receipts/lossless-v1':
        raise ValueError('UNSUPPORTED_EVIDENCE_ENCODING')
    shared = package['shared']
    result = {}
    for label, metadata in package['runs'].items():
        receipt = copy.deepcopy(metadata)
        receipt['collected'] = copy.deepcopy(shared['collected'])
        receipt['files_before'] = copy.deepcopy(shared['files_before'])
        receipt['files_after'] = copy.deepcopy(shared['files_before'])
        receipt['cases'] = []
        if not set(shared['case_exceptions']) <= set(shared['collected']):
            raise ValueError('UNBOUND_CASE_EXCEPTION')
        for node in shared['collected']:
            case = copy.deepcopy(shared['case_template'])
            case['id'] = node
            case.update(copy.deepcopy(shared['case_exceptions'].get(node, {})))
            receipt['cases'].append(case)
        result[label] = receipt
    return result


def audit(package, acceptance, pins):
    errors = []
    def demand(condition, code):
        if not condition:
            errors.append(code)
    try:
        runs = reconstruct(package)
        demand(set(runs) == {'full_suite', 'installed_package'}, 'RUN_POPULATION')
        source = runs['full_suite']; installed = runs['installed_package']
        collection = source['collected']
        demand(len(collection) == pins['expected_cases'] and len(set(collection)) == len(collection), 'CASE_POPULATION')
        demand(collection == sorted(collection) == installed['collected'], 'COLLECTION_ORDER_OR_MISMATCH')
        demand(source['files_before'] == installed['files_before'], 'RUN_INPUT_MISMATCH')
        files = source['files_before']
        for name in files:
            path = PurePosixPath(name)
            demand(not path.is_absolute() and '..' not in path.parts and str(path) == name, 'UNSAFE_INPUT_PATH')
        for prefix, count in pins['file_counts'].items():
            demand(sum(n.startswith(prefix + '/') for n in files) == count, 'FILE_POPULATION:' + prefix)
        test_files = {n for n in files if n.startswith('tests/') and PurePosixPath(n).name.startswith('test_') and n.endswith('.py')}
        collected_files = {n.split('::', 1)[0] for n in collection}
        demand(collected_files == test_files, 'TEST_FILE_COVERAGE')
        for label, r in runs.items():
            demand(sha(raw_json(r)) == pins['receipt_sha256'][label], 'RECEIPT_PIN:' + label)
            demand(r['schema'] == 'guardian/pytest-execution/v1', 'RECEIPT_SCHEMA')
            demand(type(r['exit_status']) is int and r['exit_status'] == 0, 'RUN_EXIT:' + label)
            demand(r['collection_errors'] == r['deselected'] == [], 'INCOMPLETE_RUN:' + label)
            demand(r['signed'] is False and r['independent_review'] is False, 'TRUST_PROMOTION:' + label)
            demand(r['python'] == pins['python'], 'PYTHON_PROFILE:' + label)
            demand(r['files_before'] == r['files_after'], 'CHANGED_INPUTS:' + label)
            ids = [c['id'] for c in r['cases']]
            demand(ids == collection, 'CASE_ID_MISMATCH:' + label)
            for case in r['cases']:
                demand(case['phases'] == {'setup':'passed','call':'passed','teardown':'passed'}
                       and case['wasxfail'] is False, 'CASE_NOT_FULL_PASS:' + case['id'])
                demand(type(case['properties']) is dict and all(type(v) is list and all(type(x) is str for x in v)
                       for v in case['properties'].values()), 'INVALID_PROPERTIES:' + case['id'])
            command = r['invocation']
            demand(command == pins['invocations'][label], 'SELECTED_OR_ALTERED_INVOCATION:' + label)
            modules = r['loaded_guardian_modules']
            demand(len(modules) == pins['expected_modules'], 'MODULE_POPULATION:' + label)
            for name, observed in modules.items():
                relative = name.replace('.', '/')
                candidates = ['src/' + relative + '.py', 'src/' + relative + '/__init__.py']
                expected = [n for n in candidates if n in files]
                demand(len(expected) == 1, 'MODULE_SOURCE_AMBIGUITY:' + name)
                if len(expected) != 1:
                    continue
                file = expected[0]
                path = file if label == 'full_suite' else pins['installed_root'] + '/' + file[4:]
                demand(observed == {'path':path,'sha256':files[file]}, 'RUNTIME_MODULE_MISMATCH:' + label + ':' + name)
            demand(set(modules) == set(source['loaded_guardian_modules']), 'MODULE_SET_MISMATCH:' + label)
        demand(acceptance['base_commit'] == pins['implementation_base'], 'ACCEPTANCE_BASE')
        demand({x['id'] for x in acceptance['clauses']} == {f'G00-01-F{i:02}' for i in range(1,11)}
               and len(acceptance['clauses']) == 10, 'CLAUSE_POPULATION')
        demand({x['id'] for x in acceptance['apis']} == {f'G00-API-{i:03}' for i in range(1,9)}
               and len(acceptance['apis']) == 8, 'API_POPULATION')
        demand({x['id'] for x in acceptance['original_adversaries']} == {'ADV-01','ADV-02','ADV-03'}
               and len(acceptance['original_adversaries']) == 3, 'ADVERSARY_POPULATION')
        demand(acceptance['normative_sources'] == pins['normative_sources'], 'ORIGINAL_SOURCE_PIN_MISMATCH')
        def executed(selector):
            return type(selector) is str and any(n == selector or n.startswith(selector + '[') for n in collection)
        for row in acceptance['clauses'] + acceptance['apis']:
            demand(bool(row['positive']) and bool(row['negative']), 'MISSING_FALSIFICATION:' + row['id'])
            demand(not set(row['positive']) & set(row['negative']), 'REUSED_POSITIVE_NEGATIVE:' + row['id'])
            demand(all(executed(n) for n in row['positive'] + row['negative']), 'UNEXECUTED_LINK:' + row['id'])
        for row in acceptance['original_adversaries']:
            demand(bool(row['tests']) and all(executed(n) for n in row['tests']), 'UNEXECUTED_ADVERSARY:' + row['id'])
        demand(executed(acceptance['parent_bridge']['test']) and bool(acceptance['parent_bridge']['argument'])
               and bool(acceptance['parent_bridge']['counterexample']), 'PARENT_BRIDGE')
        demand(sum(n.startswith('tests/g00_01/') for n in collection) == 94, 'DIRECT_G00_01_POPULATION')
        mutations = [m for b in package['mutations_batches'] for m in b['mutations']]
        demand(len(mutations) == 20 and {m['id'] for m in mutations} == {f'M{i:02}' for i in range(1,21)}, 'MUTATION_POPULATION')
        for mutation in mutations:
            demand(mutation['status'] == 'DETECTED' and mutation['returncode'] == 1
                   and mutation['failures'] > 0 and mutation['errors'] == mutation['skips'] == 0
                   and executed(mutation['nodeid']), 'INVALID_MUTATION:' + mutation['id'])
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        errors.append('MALFORMED_EVIDENCE:' + str(exc))
    return {'status':'RETAINED_EVIDENCE_CHECKED' if not errors else 'HOLD',
            'errors':sorted(set(errors)), 'independent_review':False, 'signed_attestation':False,
            'new_product_test_execution':False, 'campaign_closed':False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package', type=Path, required=True)
    p.add_argument('--acceptance', type=Path, required=True)
    p.add_argument('--pins', type=Path, required=True)
    a = p.parse_args(); pins = json.loads(a.pins.read_bytes())
    package = unpack(read_encoded(a.package), pins['package_sha256'])
    result = audit(package, json.loads(a.acceptance.read_bytes()), pins)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['status'] == 'RETAINED_EVIDENCE_CHECKED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
