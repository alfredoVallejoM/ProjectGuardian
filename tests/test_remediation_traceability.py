"""No test/canonical clause can vanish just by editing the progress projection."""
import copy
import importlib.util
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('contract_gate',ROOT/'tools/check_remediation_contracts.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
BASE=json.loads((ROOT/'verification/ae8561f_remediation_baseline.json').read_bytes())
MANIFEST=json.loads((ROOT/'verification/remediation_manifest.json').read_bytes())


def test_all_fifteen_findings_have_real_code_and_non_skipped_falsification_links():
    assert gate.validate(ROOT,BASE,MANIFEST)==[]
    assert len(BASE['original_clause_ids'])==120
    assert len(BASE['original_api_ids'])==58
    assert len(BASE['original_adversaries'])==36
    assert len(BASE['original_verticals'])==7


@pytest.mark.parametrize('attack',['delete','reassign','missing_test','invented_symbol','drop_clause'])
def test_traceability_mutations_are_not_silent(attack):
    changed=copy.deepcopy(MANIFEST)
    if attack=='delete':changed['findings'].pop()
    elif attack=='reassign':changed['findings'][0]['obligations']=['G00-03-F02']
    elif attack=='missing_test':changed['findings'][0]['falsification']='tests/missing.py::test_x'
    elif attack=='invented_symbol':changed['findings'][0]['symbols']=['src/guardian/domain/outcomes.py::absent_function']
    else:changed['original_clause_ids'].pop()
    assert gate.validate(ROOT,BASE,changed)


def test_baseline_is_checked_against_supplied_external_digest_before_using_claims():
    result=gate.check(ROOT,ROOT/'verification/ae8561f_remediation_baseline.json',
                      ROOT/'verification/remediation_manifest.json','0'*64)
    assert result==['UNTRUSTED_BASELINE_DIGEST']
