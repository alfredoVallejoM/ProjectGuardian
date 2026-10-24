"""Frozen candidate profile detects ABI drift without ratifying the milestone."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / 'verification/initial_milestone_profile.json'
spec = importlib.util.spec_from_file_location('initial_gate', ROOT/'tools/check_initial_milestone.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def fixture(tmp_path):
    profile=json.loads(PROFILE.read_bytes())
    path=tmp_path/'profile.json';path.write_bytes(PROFILE.read_bytes())
    suite=ET.Element('testsuite')
    for node in sorted({n for row in profile['acceptance'] for n in row['test_nodes']}):
        filename,function=node.split('::')
        ET.SubElement(suite,'testcase', classname=filename[:-3].replace('/','.'), name=function)
    xml=tmp_path/'synthetic-gate-input.xml';ET.ElementTree(suite).write(xml)
    # Synthetic input tests the checker only. Material acceptance uses actual pytest JUnit.
    return path,xml,profile


def test_frozen_profile_matches_runtime_and_has_no_claim_of_ratification(tmp_path):
    path,xml,profile=fixture(tmp_path)
    result=gate.check(ROOT,path,hashlib.sha256(path.read_bytes()).hexdigest(),xml)
    assert result['status']=='PASS' and result['acceptance_rows']==18
    assert not result['ratified'] and not result['campaign_closed']
    assert profile['runtime']==gate.runtime_profile()
    assert len(profile['runtime']['fields'])==8 and len(profile['runtime']['stages'])==15


def test_changing_frozen_profile_fails_against_operator_pin(tmp_path):
    path,xml,profile=fixture(tmp_path)
    pin=hashlib.sha256(path.read_bytes()).hexdigest()
    profile['acceptance'].pop();path.write_text(json.dumps(profile))
    assert gate.check(ROOT,path,pin,xml)['errors']==['PROFILE_PIN_MISMATCH']


@pytest.mark.parametrize('drift',['language_version','semantic_version','ir_schema','fields','required','reference_kinds'])
def test_runtime_contract_drift_is_not_hidden_by_rehashing_profile(tmp_path,drift):
    path,xml,profile=fixture(tmp_path)
    profile['runtime'][drift]='incorrect';path.write_text(json.dumps(profile))
    result=gate.check(ROOT,path,hashlib.sha256(path.read_bytes()).hexdigest(),xml)
    assert 'RUNTIME_PROFILE_DRIFT' in result['errors']


@pytest.mark.parametrize('bad',['failure','error','skipped','absent'])
def test_unexecuted_or_nonpassing_required_tests_block_gate(tmp_path,bad):
    path,xml,_=fixture(tmp_path)
    tree=ET.parse(xml);suite=tree.getroot();node=list(suite)[0]
    if bad=='absent':suite.remove(node)
    else: ET.SubElement(node,bad)
    tree.write(xml)
    result=gate.check(ROOT,path,hashlib.sha256(path.read_bytes()).hexdigest(),xml)
    assert result['status']=='FAIL'
    assert any('TEST_NOT_EXECUTED' in e or e=='TEST_SUITE_NOT_ALL_PASS' for e in result['errors'])


def test_partial_gate_cannot_promote_normative_state(tmp_path):
    path,xml,profile=fixture(tmp_path)
    profile['ratified']=True;path.write_text(json.dumps(profile))
    result=gate.check(ROOT,path,hashlib.sha256(path.read_bytes()).hexdigest(),xml)
    assert 'UNAUTHORIZED_PROFILE_PROMOTION' in result['errors']


def test_source_profile_sha_matches_published_operator_handoff_value():
    assert hashlib.sha256(PROFILE.read_bytes()).hexdigest()==(ROOT/'docs/closure/INITIAL_PROFILE_SHA256.txt').read_text().strip()
