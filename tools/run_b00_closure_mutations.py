"""Targeted post-authoring adversarial checks; not an independent actor review."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

WORKER='verification/external_v0/contract_worker.py'
TEST='tests/closure/test_external_contract.py'
MUTATIONS=[
 ('EX-ID',"require(declaration['identity'] == expected_ref, 'DECLARATION_IDENTITY_OR_ORDER_MISMATCH')","require(True, 'DECLARATION_IDENTITY_OR_ORDER_MISMATCH')",'test_each_declaration_population_identity_origin_and_order_is_bound'),
 ('EX-ORIGIN',"require(origin == dict(source=expectation['source'], digest=candidate['source_digest'],\n                               byte_start=start, byte_end=end), 'DECLARATION_ORIGIN_MISMATCH')","require(True, 'DECLARATION_ORIGIN_MISMATCH')",'test_each_declaration_population_identity_origin_and_order_is_bound'),
 ('EX-FIELD',"require(type(payload['value']) is type(expected_value) and payload['value'] == expected_value,","require(True,",'test_every_field_is_checked_not_only_interpreted_formulas'),
 ('EX-TYPE',"require(payload['tag'] == tag.split(':')[0], 'FIELD_TYPE_MISMATCH')","require(True, 'FIELD_TYPE_MISMATCH')",'test_every_field_discriminant_is_compared'),
 ('EX-V4','if left != right:','if False:', 'test_every_field_is_checked_not_only_interpreted_formulas'),
 ('EX-PROOF',"require(candidate['proofs'] == proofs, 'PROOF_OBLIGATION_MISMATCH')","require(True, 'PROOF_OBLIGATION_MISMATCH')",'test_all_remaining_deferred_field_and_proofs_preserved_without_promotion'),
 ('EX-SOURCE-PIN',"checked_hash(source, expectation['source_sha256']); source.decode('utf-8')","source.decode('utf-8')",'test_rewriting_source_and_all_candidate_digests_cannot_change_operator_pin'),
 ('EX-BUDGET',"or total + size > limits['max_total_valuations']",'or False','test_aggregate_budget_cannot_emit_partial_positive'),
 ('EX-PROMOTION',"normative_admission='NOT_CHECKED'","normative_admission='APPROVED'",'test_all_eight_product_declarations_pass_complete_external_correspondence'),
]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();results=[]
    for name,old,new,test in MUTATIONS:
        with tempfile.TemporaryDirectory(prefix='guardian-contract-mutation-') as tmp:
            target=Path(tmp)/'checkout'
            shutil.copytree(a.root,target,ignore=shutil.ignore_patterns('.git','__pycache__','.pytest_cache','*.pyc','*.xml','.coverage','build','dist'))
            path=target/WORKER;source=path.read_text()
            if source.count(old)!=1:
                results.append(dict(id=name,status='INVALID_MUTATION_TARGET'));continue
            path.write_text(source.replace(old,new,1));report=Path(tmp)/'result.xml'
            try:
                run=subprocess.run([sys.executable,'-m','pytest','-q',TEST+'::'+test,'--junitxml='+str(report)],
                    cwd=target,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30)
                suite=ET.parse(report).getroot();cases=list(suite.iter('testcase'))
                errors=list(suite.iter('error'));skips=list(suite.iter('skipped'));failures=list(suite.iter('failure'))
                status='KILLED' if run.returncode==1 and cases and failures and not errors and not skips else 'SURVIVED' if run.returncode==0 and cases else 'INVALID_RUN'
                results.append(dict(id=name,status=status,test=test,executed=len(cases),failures=len(failures)))
            except (OSError,subprocess.TimeoutExpired,ET.ParseError) as exc:
                results.append(dict(id=name,status='INVALID_RUN',reason=str(exc)))
    result=dict(scope='TARGETED_EXTERNAL_CONTRACT_PROTECTIONS',independent_actor_review=False,
        killed=sum(r['status']=='KILLED' for r in results),total=len(results),results=results)
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
    return 0 if result['killed']==result['total'] else 1


if __name__=='__main__':sys.exit(main())
