"""B08 gate falsations using deliberately synthetic authority and evidence.

These tests validate the gate, NOT the 120 product contracts. A two-test
synthetic plan must never be advertised as semantic campaign coverage.
"""
from copy import deepcopy
from hashlib import sha1
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('g00_acceptance', ROOT / 'tools/g00_acceptance.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def fixture(tmp_path):
    rows = {
        'clauses': [{'id': name, 'parent_obligation': name[:6], 'acceptance': 'synthetic acceptance ' + name}
                    for name in sorted(gate.CLAUSES)],
        'apis': [{'id': name, 'function_name': 'behavior', 'owner_path': 'src/component.py'} for name in sorted(gate.APIS)],
        'attacks': [{'id': name, 'expected_diagnostic': 'SYNTHETIC_REJECT'} for name in sorted(gate.ATTACKS)],
        'verticals': [{'id': name, 'purpose': 'synthetic vertical'} for name in sorted(gate.VERTICALS)],
    }
    paths = {
        'architecture/g00_functional_refinement.json': {'clauses': rows['clauses']},
        'architecture/g00_api_contracts.json': {'functions': rows['apis']},
        'architecture/g00_validation_plan.json': {'attacks': rows['attacks'], 'verticals': rows['verticals']},
    }
    pins = {}
    for name, value in paths.items():
        raw = gate.canonical(value)
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        pins[name] = sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    for name, raw in [('src/component.py', b'def behavior():\n    return 1\n'),
                      ('tests/test_component.py', b'def test_yes(): assert True\ndef test_no(): assert True\n')]:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    nodeids = ['tests/test_component.py::test_yes', 'tests/test_component.py::test_no']
    manifest = {p.relative_to(tmp_path).as_posix(): gate.digest(p.read_bytes()) for p in tmp_path.rglob('*') if p.is_file()}
    receipt = {'schema': gate.RECEIPT_SCHEMA, 'collected': nodeids, 'deselected': [], 'collection_errors': [],
               'exit_status': 0, 'files_before': manifest, 'files_after': dict(manifest),
               'cases': [{'id': node, 'phases': {'setup': 'passed', 'call': 'passed', 'teardown': 'passed'},
                          'wasxfail': False, 'properties': {'guardian.diagnostic': ['SYNTHETIC_REJECT']}}
                         for node in nodeids]}
    plan = {'schema': gate.PLAN_SCHEMA, 'campaign': 'G-00', 'original_git_blobs': pins,
            'expected_collection': nodeids, 'expected_input_files': dict(manifest),
            'parents': [{'id': name, 'bridge_review': 'Synthetic fixture, no product judgment'} for name in sorted(gate.PARENTS)]}
    for label, values in rows.items():
        plan[label] = []
        for row in values:
            item = {'id': row['id'], 'original_sha256': gate.digest(gate.canonical(row)),
                    'positive': nodeids[:1], 'negative': nodeids[1:], 'code_paths': ['src/component.py'],
                    'contract_review': 'Synthetic fixture; not evidence of the real implementation'}
            if label == 'clauses': item['parent'] = row['parent_obligation']
            if label == 'apis': item.update(owner='src/component.py', operation='behavior')
            if label == 'attacks': item['expected_diagnostic'] = 'SYNTHETIC_REJECT'
            plan[label].append(item)
    plan['expected_runtime_modules'] = {'guardian.component': {
        'source_path': 'src/component.py', 'sha256': manifest['src/component.py'],
        'allowed_paths': ['src/component.py']}}
    receipt['loaded_guardian_modules'] = {'guardian.component': {
        'path': 'src/component.py', 'sha256': manifest['src/component.py']}}
    return plan, receipt


def check(tmp_path, plan, receipt, **pins):
    p, r = gate.canonical(plan), gate.canonical(receipt)
    return gate.check(tmp_path, p, r, expected_plan_sha256=pins.get('plan_pin', gate.digest(p)),
                      expected_receipt_sha256=pins.get('receipt_pin', gate.digest(r)))


def test_structural_success_never_promotes_semantic_sufficiency_or_closure(tmp_path):
    plan, receipt = fixture(tmp_path)
    result = check(tmp_path, plan, receipt)
    assert result['status'] == 'STRUCTURAL_EXECUTION_BINDINGS_CHECKED', result
    assert result['semantic_sufficiency'] == 'NOT_ESTABLISHED_BY_LINK_CHECK'
    assert not result['campaign_closed'] and not result['normatively_admitted']
    assert result['independent_review'] == result['receipt_authenticity'] == 'NOT_CHECKED'


@pytest.mark.parametrize('label', ['parents', 'clauses', 'apis', 'attacks', 'verticals'])
def test_every_canonical_population_is_mandatory_not_just_a_count(tmp_path, label):
    plan, receipt = fixture(tmp_path)
    del plan[label][0]
    result = check(tmp_path, plan, receipt)
    assert label.upper() + '_POPULATION_MISMATCH' in result['errors']


@pytest.mark.parametrize('attack', ['duplicate', 'reassign', 'requirement', 'positive', 'negative', 'same-test', 'review', 'owner', 'symbol', 'diagnostic'])
def test_contract_and_test_links_cannot_be_reduced_or_reassigned(tmp_path, attack):
    plan, receipt = fixture(tmp_path)
    if attack == 'duplicate': plan['clauses'][0] = deepcopy(plan['clauses'][1])
    if attack == 'reassign': plan['clauses'][0]['parent'] = 'G00-12'
    if attack == 'requirement': plan['clauses'][0]['original_sha256'] = '0' * 64
    if attack in ('positive', 'negative'): plan['clauses'][0][attack] = []
    if attack == 'same-test': plan['clauses'][0]['negative'] = plan['clauses'][0]['positive']
    if attack == 'review': plan['parents'][0]['bridge_review'] = ''
    if attack == 'owner': plan['apis'][0]['owner'] = 'src/other.py'
    if attack == 'symbol': plan['apis'][0]['operation'] = 'missing'
    if attack == 'diagnostic': plan['attacks'][0]['expected_diagnostic'] = 'WRONG_DIAGNOSIS'
    assert check(tmp_path, plan, receipt)['status'] == 'HOLD_INCOMPLETE_EVIDENCE'


@pytest.mark.parametrize('attack', ['missing', 'duplicate', 'failed-setup', 'failed-call', 'failed-teardown', 'skip', 'xfail', 'xpass', 'deselected', 'collection-error', 'exit', 'partial-phases'])
def test_a_green_count_cannot_hide_failed_or_unexecuted_cases(tmp_path, attack):
    plan, receipt = fixture(tmp_path)
    if attack == 'missing': receipt['cases'].pop()
    if attack == 'duplicate': receipt['cases'][0] = deepcopy(receipt['cases'][1])
    if attack.startswith('failed-'): receipt['cases'][0]['phases'][attack.split('-')[1]] = 'failed'
    if attack == 'skip': receipt['cases'][0]['phases']['call'] = 'skipped'
    if attack in ('xfail', 'xpass'): receipt['cases'][0]['wasxfail'] = True
    if attack == 'deselected': receipt['deselected'] = ['tests/test_important.py::test_law']
    if attack == 'collection-error': receipt['collection_errors'] = ['tests/test_important.py']
    if attack == 'exit': receipt['exit_status'] = 1
    if attack == 'partial-phases': receipt['cases'][0]['phases'].pop('teardown')
    receipt['passed'] = 10_000
    assert check(tmp_path, plan, receipt)['status'] == 'HOLD_INCOMPLETE_EVIDENCE'


@pytest.mark.parametrize('attack', ['plan-pin', 'receipt-pin', 'source-changed', 'during-run', 'original-changed', 'original-missing', 'dependency-omitted'])
def test_external_pins_and_actual_files_must_match_the_execution(tmp_path, attack):
    plan, receipt = fixture(tmp_path)
    pins = {}
    if attack == 'plan-pin': pins['plan_pin'] = '0' * 64
    if attack == 'receipt-pin': pins['receipt_pin'] = '0' * 64
    if attack == 'source-changed': (tmp_path / 'src/component.py').write_text('def behavior(): return 0\n')
    if attack == 'during-run': receipt['files_after']['src/component.py'] = '0' * 64
    if attack == 'original-changed': (tmp_path / 'architecture/g00_api_contracts.json').write_text('{}')
    if attack == 'original-missing': (tmp_path / 'architecture/g00_api_contracts.json').unlink()
    if attack == 'dependency-omitted':
        receipt['files_before'].pop('architecture/g00_api_contracts.json')
        receipt['files_after'].pop('architecture/g00_api_contracts.json')
    assert check(tmp_path, plan, receipt, **pins)['status'] == 'HOLD_INCOMPLETE_EVIDENCE'


@pytest.mark.parametrize('path', ['../escape', '/tmp/escape', 'src/../component.py', 'src//component.py', 'src\\component.py'])
def test_paths_cannot_escape_the_candidate(tmp_path, path):
    with pytest.raises(ValueError): gate.safe_file(tmp_path, path)


def test_symlink_and_duplicate_json_keys_are_rejected(tmp_path):
    (tmp_path / 'real.py').write_text('pass')
    (tmp_path / 'link.py').symlink_to(tmp_path / 'real.py')
    with pytest.raises(ValueError, match='SYMLINK'): gate.safe_file(tmp_path, 'link.py')
    with pytest.raises(ValueError, match='DUPLICATE'): gate.load(b'{"schema":1,"schema":2}')


def test_actual_pytest_plugin_captures_call_failure_skip_and_diagnostic(tmp_path):
    (tmp_path / 'test_cases.py').write_text('''import pytest

def test_pass(record_property):
    record_property("guardian.diagnostic", "EXPECTED_REJECTION")
    assert 2 == 2

def test_failure():
    assert False, "real failing behavior"

@pytest.mark.skip(reason="not executed")
def test_skip():
    assert False
''')
    receipt_path = tmp_path / 'record.json'
    env = dict(__import__('os').environ, PYTHONPATH=str(ROOT))
    proc = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'tools.pytest_g00_receipt',
                           '--g00-receipt=' + str(receipt_path)], cwd=tmp_path, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30)
    assert proc.returncode == 1, proc.stdout
    data = json.loads(receipt_path.read_text())
    cases = {x['id']: x for x in data['cases']}
    assert cases['test_cases.py::test_pass']['phases'] == {'setup': 'passed', 'call': 'passed', 'teardown': 'passed'}
    assert cases['test_cases.py::test_pass']['properties']['guardian.diagnostic'] == ['EXPECTED_REJECTION']
    assert cases['test_cases.py::test_failure']['phases']['call'] == 'failed'
    assert cases['test_cases.py::test_skip']['phases']['setup'] == 'skipped'
    assert data['exit_status'] == 1 and not data['signed'] and not data['independent_review']


def test_unlinked_collected_population_cannot_drop_an_expected_regression(tmp_path):
    plan, receipt = fixture(tmp_path)
    plan['expected_collection'] = plan['expected_collection'] + ['tests/test_component.py::test_regression']
    assert 'TEST_COLLECTION_MISMATCH' in check(tmp_path, plan, receipt)['errors']


def test_pinned_original_blob_cannot_be_replaced_by_current_author_claim(tmp_path):
    plan, receipt = fixture(tmp_path)
    plan['original_git_blobs']['architecture/g00_functional_refinement.json'] = '0' * 40
    assert any('ORIGINAL_BLOB_MISMATCH' in error for error in check(tmp_path, plan, receipt)['errors'])
