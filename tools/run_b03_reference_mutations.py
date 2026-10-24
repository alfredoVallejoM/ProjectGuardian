"""Directed regression attacks on B03/B06/LC04. No timeout/error counts as a kill."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

D='src/guardian/domain/'
S='src/guardian/spec_lang/'
MUTATIONS=(
 ('B03_ACCEPTANCE',D+'obligation.py',"texts(self.acceptance_contract, 'REQUIRED_ACCEPTANCE_MISSING', nonempty=True)","texts(self.acceptance_contract, 'REQUIRED_ACCEPTANCE_MISSING')",'tests/domain/test_b03_commitments.py::test_f04_f05_required_obligation_contracts_cannot_be_missing_null_or_empty'),
 ('REF_KIND',D+'references.py','if reference.kind is not expected_kind:','if False:','tests/domain/test_exact_record_resolution.py::test_exact_body_is_returned_not_a_matching_name_or_placeholder'),
 ('REF_SCOPE',D+'references.py','and reference in e.entities]','and reference.project == e.snapshot.project_id]','tests/domain/test_exact_record_resolution.py::test_scoped_import_requires_exact_entity_and_material_source_cut'),
 ('REF_CUT',D+'references.py','if not any(c == grant.pinned_cut for c in self.snapshot.sources):','if False:','tests/domain/test_exact_record_resolution.py::test_scoped_import_requires_exact_entity_and_material_source_cut'),
 ('REF_REVISION',D+'references.py','record = selected._by_ref.get(reference)','record = next((r for r in selected.records if r.identity.entity == reference.entity), None)','tests/domain/test_exact_record_resolution.py::test_no_latest_fallback_and_historical_never_promoted_to_current'),
 ('NO_COMPILED',S+'resolution.py','def compiled(self) -> bool:\n        return False','def compiled(self) -> bool:\n        return True','tests/spec_lang/test_lc04_reference_linking.py::test_two_pass_forward_references_cycles_sources_and_project_share_nominal_ids'),
 ('SYMBOL_ORIGIN',S+'resolution.py','if any(b.declared_source not in resolved.value.record.source_refs for b in matching_bindings):','if False:','tests/spec_lang/test_lc04_adversarial_boundaries.py::test_named_binding_must_match_record_source_provenance'),
 ('SOURCE_PIN',S+'resolution.py','if kind is EntityKind.SOURCE and identity not in pins:','if False:','tests/spec_lang/test_lc04_adversarial_boundaries.py::test_explicit_source_symbol_does_not_invent_a_material_source_pin'),
 ('MEMBERSHIP',D+'campaign.py','if len(set(keys)) != len(keys):','if False:','tests/domain/test_b03_commitments.py::test_f08_membership_is_reference_not_a_copy_and_no_auto_closure'),
 ('BUDGET',S+'resolution.py','if nodes > max_nodes:','if False:','tests/spec_lang/test_lc04_adversarial_boundaries.py::test_expression_budget_is_counted_after_declaration_budget'),
 ('AUTHORITY',D+'record_base.py','if self.declared_status is DecisionStatus.APPROVED and self.authority_ref is None:','if False:','tests/domain/test_b03_commitments.py::test_proposal_approved_label_is_never_authenticated_by_constructor'),
 ('NO_ADMISSION',D+'references.py','def normatively_admitted(self) -> bool:\n        return False','def normatively_admitted(self) -> bool:\n        return True','tests/domain/test_exact_record_resolution.py::test_exact_body_is_returned_not_a_matching_name_or_placeholder'),
)


def run(root: Path, output: Path):
    results=[]
    for name,path,before,after,test in MUTATIONS:
        with tempfile.TemporaryDirectory(prefix='guardian-b03-mutant-') as tmp:
            dst=Path(tmp)
            for directory in ('src','tests'):
                shutil.copytree(root/directory,dst/directory,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
            shutil.copyfile(root/'pyproject.toml',dst/'pyproject.toml')
            target=dst/path;raw=target.read_text()
            if raw.count(before)!=1:
                raise ValueError(f'{name}: expected one mutation anchor, got {raw.count(before)}')
            target.write_text(raw.replace(before,after))
            try:
                p=subprocess.run([sys.executable,'-m','pytest','-q',test,'--junitxml=mutant.xml'],cwd=dst,
                    env={**os.environ,'PYTHONPATH':str(dst/'src')+os.pathsep+str(dst/'tests')},
                    capture_output=True,text=True,timeout=30)
                suites=list(ET.parse(dst/'mutant.xml').getroot().iter('testsuite'))
                failures=sum(int(s.get('failures',0)) for s in suites)
                errors=sum(int(s.get('errors',0)) for s in suites)
                skipped=sum(int(s.get('skipped',0)) for s in suites)
                status='KILLED' if p.returncode==1 and failures and not errors and not skipped else 'SURVIVED' if p.returncode==0 else 'INVALID_RUN'
                result=dict(id=name,status=status,test=test,failures=failures,errors=errors,skipped=skipped,returncode=p.returncode)
            except (subprocess.TimeoutExpired,OSError,ET.ParseError) as exc:
                result=dict(id=name,status='INVALID_RUN',reason=type(exc).__name__)
            results.append(result);print(name,result['status'],flush=True)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(dict(scope='DIRECTED_B03_REFERENCE_LINKING_NOT_EXHAUSTIVE',results=results),indent=2)+'\n')
    return results


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    raise SystemExit(0 if all(x['status']=='KILLED' for x in run(args.root,args.output)) else 1)
