"""Directed C12 mutations; collection failures/timeouts never count as kills.

Runs only the diff contract suite in temporary source copies. This is a local
constructor check, not independent review or an exhaustive mutation campaign.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

TARGET = 'src/guardian/spec_lang/contract_diff.py'
TEST = 'tests/spec_lang/test_contract_diff.py'
MUTATIONS = (
 ('hide_removed_declaration',
  "emit(ChangeKind.DECLARATION_REMOVED, location, old[key], None)",
  "pass  # mutant: removed declaration silently omitted",
  'test_each_declaration_removal_is_visible_even_when_remaining_rows_are_valid'),
 ('hide_declaration_order',
  "emit(ChangeKind.DECLARATION_ORDER_CHANGED, '$.declarations.order', old_order, new_order)",
  "pass  # mutant: normative order ignored",
  'test_declaration_reordering_is_not_normalized_as_a_set'),
 ('hide_removed_proof',
  "emit(kind, '$.proofs[' + _json(key).decode('utf-8') + ']', ap.get(key), bp.get(key))",
  "None if kind is ChangeKind.PROOF_REMOVED else emit(kind, '$.proofs[' + _json(key).decode('utf-8') + ']', ap.get(key), bp.get(key))",
  'test_removing_proof_or_replacing_interpretation_with_deferred_is_not_hidden'),
 ('cross_project_matching',
  "if left['project'] != right['project']:",
  'if False:  # mutant: namespaces merged',
  'test_two_projects_with_identical_names_are_incomparable'),
 ('ambiguous_lineage_last_wins',
  'if key in result:\n            raise _Incomparable',
  'if False:\n            raise _Incomparable',
  'test_revision_changes_are_pins_not_deletion_or_latest_selection'),
 ('ignore_node_budget',
  'if self.nodes >= self.budget.max_nodes:',
  'if False:  # mutant: aggregate node budget ignored',
  'test_exact_node_budget_and_determinism_do_not_depend_on_json_key_order'),
)


def run(root: Path) -> dict:
    source = (root / TARGET).read_text(encoding='utf-8')
    rows = []
    with tempfile.TemporaryDirectory(prefix='guardian-diff-mutants-') as folder:
        work = Path(folder)
        shutil.copytree(root / 'src', work / 'src', ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        shutil.copyfile(root / TEST, work / 'test_contract_diff.py')
        env = dict(os.environ, PYTHONPATH=str(work / 'src'), PYTHONDONTWRITEBYTECODE='1',
                   PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')

        def execute(node: str, name: str):
            junit = work / (name + '.xml')
            command = [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
                       node, '--junitxml=' + str(junit)]
            try:
                result = subprocess.run(command, cwd=work, env=env, capture_output=True,
                                        text=True, timeout=45, check=False)
            except subprocess.TimeoutExpired:
                return {'verdict':'INVALID', 'reason':'TIMEOUT'}
            if not junit.is_file():
                return {'verdict':'INVALID', 'reason':'NO_JUNIT', 'returncode':result.returncode}
            document = ET.parse(junit).getroot()
            cases = document.findall('.//testcase')
            failures = [(c.attrib.get('name'), f.attrib.get('message',''))
                        for c in cases for f in c.findall('failure')]
            errors = document.findall('.//error')
            skips = document.findall('.//skipped')
            invalid = (not cases or errors or skips or result.returncode not in (0,1)
                       or any('AssertionError' not in message and not message.startswith('assert ')
                              for _,message in failures))
            verdict = 'INVALID' if invalid else 'KILLED' if failures else 'SURVIVED'
            return {'verdict':verdict, 'returncode':result.returncode,
                    'cases':len(cases), 'failures':len(failures), 'errors':len(errors),
                    'skipped':len(skips), 'failing_cases':[n for n,_ in failures],
                    'stdout_sha256':hashlib.sha256(result.stdout.encode()).hexdigest()}

        baseline = execute('test_contract_diff.py', 'baseline')
        if baseline['verdict'] != 'SURVIVED':
            return {'status':'INVALID_BASELINE', 'baseline':baseline, 'mutations':[]}
        for name, old, new, test in MUTATIONS:
            if source.count(old) != 1:
                rows.append({'id':name, 'verdict':'INVALID', 'reason':'MUTATION_LOCATION_NOT_UNIQUE'})
                continue
            (work / TARGET).write_text(source.replace(old,new,1), encoding='utf-8')
            for cache in (work / 'src').rglob('__pycache__'):
                shutil.rmtree(cache)
            result = execute('test_contract_diff.py::' + test, name)
            rows.append({'id':name, 'test':TEST+'::'+test, **result})
    return {'schema':'guardian.contract-diff-mutations/v1',
            'status':'PASS' if all(r['verdict']=='KILLED' for r in rows) else 'FAIL',
            'python':sys.version.split()[0], 'scope':'DIRECTED_C12_ONLY',
            'independent_review':False, 'baseline':baseline,
            'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
            'test_sha256':hashlib.sha256((root/TEST).read_bytes()).hexdigest(),
            'killed':sum(r['verdict']=='KILLED' for r in rows),
            'survived':sum(r['verdict']=='SURVIVED' for r in rows),
            'invalid':sum(r['verdict']=='INVALID' for r in rows), 'mutations':rows}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args()
    result=run(args.root.resolve())
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':
    sys.exit(main())
