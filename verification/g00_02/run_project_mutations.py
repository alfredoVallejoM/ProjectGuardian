"""Directed mutations of G00-02 descriptors; do not edit the working tree."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
PATH='src/guardian/domain/project.py'
TEST='tests/g00_02/test_project_contract_boundaries.py'
MUTATIONS=(
 ('P01','        ProjectDefinition.__post_init__(definition)\n','        pass  # deliberately omitted\n','test_project_revalidation_rejects_invalid_nested_contract'),
 ('P02','        StorageDescriptor.__post_init__(descriptor)\n','        pass  # deliberately omitted\n','test_federated_descriptor_revalidates_all_nested_metadata'),
 ('P03','or self.source_policy.revision!=self.source_policy_ref.revision','or False','test_policy_revision_change_is_explicit_and_old_definition_is_preserved'),
 ('P04',' or not any(self.mode is mode for mode in StorageMode)','','test_federated_descriptor_revalidates_all_nested_metadata[fabricated-mode]'),
 ('P05','        EntityRef.__post_init__(ref)\n','        pass  # deliberately omitted\n','test_membership_revalidates_reference_before_namespace_result'),
 ('P06',"'ProjectDefinition' if type(definition) is ProjectDefinition else 'non-ProjectDefinition'","type(definition).__name__",'test_rejected_external_objects_do_not_execute_metaclass_or_validation_hooks[project]'),
 ('P07',' or type(item[0]) is not str','','test_malformed_authority_key_cannot_invoke_hash_or_equality'),
 ('P08','    if ref.project!=project.project_id:\n','    if False:\n','test_alternating_projects_with_equal_human_names_cannot_share_authority'),
 ('P09','        ProjectDefinition.__post_init__(self)\n        managed =','        managed =','test_project_revalidation_rejects_invalid_nested_contract'),
)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();original=(ROOT/PATH).read_bytes();text=original.decode();rows=[]
    for label,old,new,test in MUTATIONS:
        if text.count(old)!=1:
            raise ValueError('mutation point changed: '+label)
        with tempfile.TemporaryDirectory(prefix='guardian-g00-02-') as name:
            root=Path(name);shutil.copytree(ROOT/'src',root/'src',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            (root/'tests/g00_02').mkdir(parents=True);shutil.copyfile(ROOT/TEST,root/TEST)
            (root/PATH).write_text(text.replace(old,new,1))
            output=root/'mutation.xml'
            env=dict(os.environ,PYTHONPATH=str(root/'src'),PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
            cmd=[sys.executable,'-m','pytest','-q',TEST+'::'+test,'--junitxml='+str(output)]
            try:
                proc=subprocess.run(cmd,cwd=root,env=env,capture_output=True,text=True,timeout=30)
                cases=list(ET.parse(output).getroot().iter('testcase'))
                failures=[f for c in cases for f in c.findall('failure')]
                errors=sum(len(c.findall('error')) for c in cases);skips=sum(len(c.findall('skipped')) for c in cases)
                pertinent=any('AssertionError' in (f.text or '') or 'DID NOT RAISE' in (f.text or '') for f in failures)
                detected=proc.returncode==1 and bool(failures) and not errors and not skips and pertinent
                rows.append(dict(id=label,status='DETECTED' if detected else 'NOT_DETECTED',test=TEST+'::'+test,
                    returncode=proc.returncode,failures=len(failures),errors=errors,skips=skips,
                    output_sha256=hashlib.sha256((proc.stdout+proc.stderr).encode()).hexdigest()))
            except (subprocess.TimeoutExpired,ET.ParseError,FileNotFoundError) as exc:
                rows.append(dict(id=label,status='INVALID_RUN',reason=type(exc).__name__))
    assert (ROOT/PATH).read_bytes()==original
    record=dict(schema='guardian/g00-02-directed-mutations/v1',source_sha256=hashlib.sha256(original).hexdigest(),
                mutations=rows,independent_review=False,obligation_closed=False)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
    print(json.dumps({r['id']:r['status'] for r in rows},sort_keys=True))
    return 0 if all(r['status']=='DETECTED' for r in rows) else 1


if __name__=='__main__':raise SystemExit(main())
