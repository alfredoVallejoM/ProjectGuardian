"""Checks artifact integrity, not independent approval of the authored review."""
import copy
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[2]
MP=ROOT/'verification/b00/reconciliation_manifest.json'

def tool(name):
    s=importlib.util.spec_from_file_location(name,ROOT/'tools'/f'{name}.py')
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

gate=tool('check_b00_reconciliation')
deployment=tool('check_external_verifier_installation')


def test_120_clause_dispositions_and_12_parent_judgments_preserve_all_original_ids():
    raw=MP.read_bytes()
    r=gate.check(ROOT,MP,hashlib.sha256(raw).hexdigest(),authority_mode='external-readback')
    assert r['status']=='TECHNICAL_DISPOSITION_RECORDS_CHECKED',r
    assert (r['clauses'],r['parents'],r['apis'],r['decisions'])==(120,12,58,24)
    assert r['implementation_completeness']=='NOT_CLAIMED' and not r['campaign_closed']
    assert r['ratification']=='HOLD_EXTERNAL'


def test_removing_or_reassigning_any_clause_or_api_is_detectable():
    for name,label in [('clauses','CLAUSES'),('apis','APIS')]:
        rows=gate.table(ROOT/f'verification/b00/{name}.tsv');expected={r['id'] for r in rows}
        for i in range(len(rows)):
            errors=[];gate.population(rows[:i]+rows[i+1:],expected,label,errors)
            assert errors==[label+'_POPULATION_MISMATCH']
        changed=copy.deepcopy(rows);changed[0]['id']=changed[1]['id'];errors=[]
        gate.population(changed,expected,label,errors);assert errors


def test_operator_manifest_pin_cannot_be_replaced_by_candidate():
    r=gate.check(ROOT,MP,'0'*64,authority_mode='external-readback')
    assert r['status']=='FAIL' and r['errors']==['MANIFEST_PIN_MISMATCH']


def test_artifact_change_fails_without_changing_external_manifest_pin(tmp_path):
    m=json.loads(MP.read_bytes());name='verification/b00/clauses.tsv'
    # A modified artifact under the same trusted manifest is never accepted.
    m['artifacts'][name]='0'*64
    p=tmp_path/'manifest.json';p.write_text(json.dumps(m))
    r=gate.check(ROOT,p,hashlib.sha256(p.read_bytes()).hexdigest(),authority_mode='external-readback')
    assert r['status']=='FAIL' and 'ARTIFACT_PIN_MISMATCH:'+name in r['errors']


def test_missing_canonical_bytes_never_report_local_source_verification_pass():
    raw=MP.read_bytes();r=gate.check(ROOT,MP,hashlib.sha256(raw).hexdigest(),authority_mode='required')
    if r['missing_authority_files']:
        assert r['status']=='FAIL' and 'ORIGINAL_BYTES_MISSING' in r['errors']
    else:
        assert r['original_source_bytes']=='CHECKED'


def test_future_apis_and_payloads_are_not_promoted_by_listing_them():
    rows=gate.table(ROOT/'verification/b00/apis.tsv')
    for r in rows:
        if r['runtime_signature']=='-':assert r['disposition'] in ('PLANNED','SCALAR_PRIMITIVE_ONLY')
    catalog=json.loads((ROOT/'verification/b00/format_catalog.json').read_bytes())
    assert not catalog['generic_domain_decoder_implemented']
    assert next(x for x in catalog['formats'] if x['record_type']=='OBLIGATION_REVISION')['runtime_domain_decoder']=='NOT_IMPLEMENTED'


def test_junit_gate_rejects_missing_failed_or_skipped_required_tests(tmp_path):
    import xml.etree.ElementTree as ET
    manifest=json.loads(MP.read_bytes())
    cases=[]
    for node in manifest['acceptance_tests']:
        filename,name=node.split('::');cases.append((filename[:-3].replace('/','.'),name))
    for attack in ('missing','failed','skipped'):
        suite=ET.Element('testsuite')
        for i,(cls,name) in enumerate(cases):
            if i==0 and attack=='missing':continue
            c=ET.SubElement(suite,'testcase',classname=cls,name=name)
            if i==0 and attack in ('failed','skipped'):ET.SubElement(c,'failure' if attack=='failed' else 'skipped')
        file=tmp_path/'run.xml';ET.ElementTree(suite).write(file)
        r=gate.check(ROOT,MP,hashlib.sha256(MP.read_bytes()).hexdigest(),junit=file,authority_mode='external-readback')
        assert r['status']=='FAIL'


def test_verifier_owned_by_candidate_cannot_be_called_protected():
    observations=[dict(role=r,owner_uid=1000,pin_matches=True,writable_by_candidate=True,writable_ancestor=True,symlink=False) for r in ('worker','launcher')]
    r=deployment.assess(observations,1000,1000,1000)
    assert r['status']=='HOLD' and 'IDENTITIES_NOT_SEPARATED' in r['errors']
    assert r['independent_review']=='NOT_CHECKED'


@pytest.mark.parametrize('field',['pin_matches','writable_by_candidate','writable_ancestor','symlink'])
def test_permission_checker_fails_closed_on_each_deployment_failure(field):
    observations=[dict(role=r,owner_uid=2000,pin_matches=True,writable_by_candidate=False,writable_ancestor=False,symlink=False) for r in ('worker','launcher')]
    observations[0][field]=field!='pin_matches'
    assert deployment.assess(observations,1000,2000,1000)['status']=='HOLD'


def test_successful_permission_policy_still_does_not_approve_or_attest():
    # This is a unit test of the policy, not a claim of an actual protected deployment.
    observations=[dict(role=r,owner_uid=2000,pin_matches=True,writable_by_candidate=False,writable_ancestor=False,symlink=False) for r in ('worker','launcher')]
    r=deployment.assess(observations,1000,2000,1000)
    assert r['status']=='FILESYSTEM_SEPARATION_CHECKED' and not r['signed_attestation']
    assert r['normative_approval']=='NOT_CHECKED'
    assert deployment.assess(observations,1000,2000,0)['status']=='HOLD'
