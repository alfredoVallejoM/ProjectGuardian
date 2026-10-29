"""Adversarial tests of retained evidence; not extra product acceptance cases."""
import copy
import importlib.util
import json
from pathlib import Path
import pytest

HERE = Path(__file__).resolve().parent
s = importlib.util.spec_from_file_location('audit_g00_01_receipts', HERE/'audit_receipts.py')
v = importlib.util.module_from_spec(s); s.loader.exec_module(v)
PINS = json.loads((HERE/'PINS.json').read_bytes())
PACKAGE = v.unpack(v.read_encoded(HERE/'PAIRED_RECEIPTS.json.xz.b64'), PINS['package_sha256'])
ACCEPTANCE = json.loads((HERE.parent/'ACCEPTANCE.json').read_bytes())


def inputs():
    return copy.deepcopy(PACKAGE), copy.deepcopy(ACCEPTANCE), copy.deepcopy(PINS)


def repin_receipts(package, pins):
    # Test structural defenses even under explicitly changed simulated operator
    # pins. This is not permission to replace actual production evidence pins.
    pins['receipt_sha256'] = {k:v.sha(v.raw_json(r)) for k,r in v.reconstruct(package).items()}


def test_retained_pair_is_exactly_reconstructed_and_has_no_closure_authority():
    p,a,pins = inputs()
    out = v.audit(p,a,pins)
    assert out['status'] == 'RETAINED_EVIDENCE_CHECKED', out
    assert not out['new_product_test_execution'] and not out['campaign_closed']
    assert not out['signed_attestation'] and not out['independent_review']
    assert {k:v.sha(v.raw_json(r)) for k,r in v.reconstruct(p).items()} == pins['receipt_sha256']


@pytest.mark.parametrize('attack', [
    'drop-case','duplicate-case','skip-call','failed-setup','failed-teardown',
    'missing-phase','xfail','collection-error','deselected','exit-bool',
    'test-file-missing','wrong-runtime-digest','foreign-runtime-path','missing-module',
    'selected-invocation','drop-clause','duplicate-clause','drop-api','drop-adversary',
    'same-positive-negative','absent-falsification','unexecuted-link','missing-parent-bridge',
    'mutant-timeout','mutant-collection-error','mutant-omitted','mutant-duplicated',
    'normative-pin-change','claimed-signed','claimed-independent','properties-scalar',
])
def test_malformed_or_weakened_dossier_does_not_close(attack):
    p,a,pins = inputs(); run=p['runs']['full_suite']; template=p['shared']['case_template']
    if attack=='drop-case': p['shared']['collected'].pop()
    elif attack=='duplicate-case': p['shared']['collected'][-1]=p['shared']['collected'][0]
    elif attack=='skip-call': template['phases']['call']='skipped'
    elif attack=='failed-setup': template['phases']['setup']='failed'
    elif attack=='failed-teardown': template['phases']['teardown']='failed'
    elif attack=='missing-phase': template['phases'].pop('teardown')
    elif attack=='xfail': template['wasxfail']=True
    elif attack=='collection-error': run['collection_errors']=['broken.py']
    elif attack=='deselected': run['deselected']=['missing']
    elif attack=='exit-bool': run['exit_status']=False
    elif attack=='test-file-missing': p['shared']['files_before'].pop('tests/g00_01/test_contracts.py')
    elif attack=='wrong-runtime-digest': run['loaded_guardian_modules']['guardian.domain.identity']['sha256']='0'*64
    elif attack=='foreign-runtime-path': run['loaded_guardian_modules']['guardian.domain.identity']['path']='/other/identity.py'
    elif attack=='missing-module': run['loaded_guardian_modules'].pop('guardian.domain.identity')
    elif attack=='selected-invocation': run['invocation'] += ['-k','happy']
    elif attack=='drop-clause': a['clauses'].pop()
    elif attack=='duplicate-clause': a['clauses'][-1]=a['clauses'][0]
    elif attack=='drop-api': a['apis'].pop()
    elif attack=='drop-adversary': a['original_adversaries'].pop()
    elif attack=='same-positive-negative': a['apis'][4]['negative']=a['apis'][4]['positive']
    elif attack=='absent-falsification': a['clauses'][0]['negative']=[]
    elif attack=='unexecuted-link': a['clauses'][0]['negative']=['tests/unexecuted.py::test_no']
    elif attack=='missing-parent-bridge': a['parent_bridge']['test']='not-executed'
    elif attack=='mutant-timeout': p['mutations_batches'][0]['mutations'][0]['returncode']=124
    elif attack=='mutant-collection-error': p['mutations_batches'][0]['mutations'][0]['errors']=1
    elif attack=='mutant-omitted': p['mutations_batches'][0]['mutations'].pop()
    elif attack=='mutant-duplicated': p['mutations_batches'][0]['mutations'][-1]=p['mutations_batches'][0]['mutations'][0]
    elif attack=='normative-pin-change': a['normative_sources']['architecture/campaigns.json']='0'*40
    elif attack=='claimed-signed': run['signed']=True
    elif attack=='claimed-independent': run['independent_review']=True
    elif attack=='properties-scalar': template['properties']={'guardian.diagnostic':'NOT_THE_OBSERVED_CODE'}
    repin_receipts(p,pins)
    result=v.audit(p,a,pins)
    assert result['status']=='HOLD' and result['errors'], (attack,result)


def test_original_operator_pin_cannot_be_replaced_inside_package():
    p,a,pins=inputs()
    p['runs']['full_suite']['exit_status']=1
    p['original_receipt_sha256']['full_suite']=v.sha(v.raw_json(v.reconstruct(p)['full_suite']))
    assert 'RECEIPT_PIN:full_suite' in v.audit(p,a,pins)['errors']


def test_bad_outer_pin_fails_before_semantic_processing():
    with pytest.raises(ValueError, match='EVIDENCE_PACKAGE_PIN_MISMATCH'):
        v.unpack(v.read_encoded(HERE/'PAIRED_RECEIPTS.json.xz.b64'), '0'*64)
