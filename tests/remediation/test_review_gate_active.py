"""New adversarial expectations; intended RED on 55fe58a2. No synthetic row is
claimed as product-clause coverage. Uses the unchanged published gate fixture.
"""
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('published_gate_tests',ROOT/'tests/acceptance/test_execution_bindings.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)


def repin_file(root, plan, receipt, name):
    value=f.gate.digest((root/name).read_bytes())
    for target in (plan['expected_input_files'],receipt['files_before'],receipt['files_after']):
        target[name]=value
    for module, binding in plan.get('expected_runtime_modules', {}).items():
        if binding['source_path'] == name:
            binding['sha256'] = value
            receipt['loaded_guardian_modules'][module]['sha256'] = value


def test_review_A01_api_operation_must_match_original_or_explicit_adapter(tmp_path):
    plan,receipt=f.fixture(tmp_path)
    path=tmp_path/'src/component.py'
    path.write_text(path.read_text()+'\ndef unrelated():\n    return 17\n')
    repin_file(tmp_path,plan,receipt,'src/component.py')
    plan['apis'][0]['operation']='unrelated'
    result=f.check(tmp_path,plan,receipt)
    assert result['status']=='HOLD_INCOMPLETE_EVIDENCE', result
    assert 'API_CONTRACT_ENDPOINT_MISMATCH:G00-API-001' in result['errors']


def test_review_A02_diagnostic_property_is_not_substring_match(tmp_path):
    plan,receipt=f.fixture(tmp_path)
    for row in receipt['cases']:
        row['properties']['guardian.diagnostic']='NOT_OBSERVED:SYNTHETIC_REJECT:UNRELATED'
    result=f.check(tmp_path,plan,receipt)
    assert result['status']=='HOLD_INCOMPLETE_EVIDENCE', result


@pytest.mark.parametrize('module_state',['omitted','foreign','wrong_digest','empty'])
def test_review_A03_loaded_module_provenance_is_bound(tmp_path,module_state):
    plan,receipt=f.fixture(tmp_path)
    if module_state=='omitted':receipt.pop('loaded_guardian_modules')
    if module_state=='foreign':
        receipt['loaded_guardian_modules']={'guardian.component':{'path':'/different/install/guardian/component.py','sha256':'0'*64}}
    elif module_state=='wrong_digest':
        receipt['loaded_guardian_modules']={'guardian.component':{'path':'src/component.py','sha256':'0'*64}}
    elif module_state=='empty':receipt['loaded_guardian_modules']={}
    result=f.check(tmp_path,plan,receipt)
    assert result['status']=='HOLD_INCOMPLETE_EVIDENCE', result


def test_review_A04_real_runner_imports_other_code_but_gate_accepts(tmp_path):
    root=tmp_path/'candidate';root.mkdir()
    plan,_=f.fixture(root)
    local=root/'src/guardian';local.mkdir()
    (local/'__init__.py').write_text('')
    (local/'component.py').write_text('def behavior():\n    return 0\n')
    foreign=tmp_path/'foreign/guardian';foreign.mkdir(parents=True)
    (foreign/'__init__.py').write_text('')
    (foreign/'component.py').write_text('def behavior():\n    return 1\n')
    (root/'tests/test_component.py').write_text('''from guardian.component import behavior

def test_yes():
    assert behavior() == 1

def test_no(record_property):
    assert behavior() != 0
    record_property("guardian.diagnostic", "SYNTHETIC_REJECT")
''')
    receipt_path=tmp_path/'actual-receipt.json'
    env=dict(os.environ,PYTHONPATH=os.pathsep.join((str(foreign.parent),str(ROOT))))
    run=subprocess.run([sys.executable,'-m','pytest','-q','-p','tools.pytest_g00_receipt',
        '--g00-receipt='+str(receipt_path)],cwd=root,env=env,capture_output=True,text=True,timeout=30)
    assert run.returncode==0,run.stdout+run.stderr
    receipt=json.loads(receipt_path.read_text())
    assert receipt['loaded_guardian_modules']['guardian.component']['path']==str(foreign/'component.py')
    plan['expected_collection']=receipt['collected']
    plan['expected_input_files']=dict(receipt['files_before'])
    for label in ('clauses','apis','attacks','verticals'):
        for row in plan[label]:
            row['code_paths']=['src/guardian/component.py']
            if label=='apis':row['owner']='src/guardian/component.py'
    result=f.check(root,plan,receipt)
    assert result['status']=='HOLD_INCOMPLETE_EVIDENCE',result
