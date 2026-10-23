"""Targeted behavioral mutations. Exit nonzero on survivors or invalid runs.

Runs in temporary copies; never modifies the working tree, uses no network or
GitHub Actions, and counts neither collection errors nor timeouts as a kill.
This is a bounded fault-injection campaign, not all possible program mutants.
"""
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

# ID, relative module, exact substitutions, exact falsification node ID.
P = 'src/guardian/'
D = P+'domain/'
S = P+'spec_lang/'
T = 'tests/test_audit_contract_gaps.py::'
MUTATIONS = (
 ('Q01', D+'outcomes.py', (("    if isinstance(value, Enum):", "    if False and isinstance(value, Enum):"),
                          ("    if type(value) is not str:", "    if not isinstance(value, str):")), T+'test_Q01_status_parser_rejects_an_enum_from_another_axis'),
 ('Q02', D+'source.py', (("source.repository not in project.permitted_source_repositories", "source.repository not in project.source_policy.allow_repositories"),),T+'test_Q02_sidcar_governance_repository_is_a_valid_project_source'),
 ('Q03', D+'source.py', (("if len(set(physical)) != len(physical):", "if False and len(set(physical)) != len(physical):"),),
    'tests/test_q_mutation_controls.py::test_physical_alias_reports_specific_diagnostic'),
 ('Q04', D+'source.py', (("groups.setdefault(history_source_key(entry.cut) + (entry.lineage,), []).append(entry)","\n        if isinstance(entry.cut, GitSourceCut):\n            groups.setdefault(history_source_key(entry.cut) + (entry.lineage,), []).append(entry)"),
                       ("        current = entry\n        path:", "        if isinstance(entry.cut, DocumentSourceCut):\n            continue\n        current = entry\n        path:")),T+'test_Q04_document_baseline_cycles_are_diagnosed'),
 ('Q05', D+'source.py', (("if entry.acquisition is SourceStatus.MISSING:", "if False and entry.acquisition is SourceStatus.MISSING:"),),T+'test_Q05_missing_source_entry_is_visible_in_coverage_description'),
 ('Q06', S+'contract.py', (("if type(pair) is not tuple or len(pair) != 2:", "if False and (type(pair) is not tuple or len(pair) != 2):"),),T+'test_Q06_compile_context_cannot_hold_mutable_source_pins'),
 ('Q07', S+'contract.py', (("if self.artifact_digest is not None and type(self.artifact_digest) is not ContentDigest:","if False and self.artifact_digest is not None and type(self.artifact_digest) is not ContentDigest:"),),T+'test_Q07_compiled_result_rejects_an_untyped_digest'),
 ('Q08', S+'text.py', (("if self.span.end > len(data):", "if False and self.span.end > len(data):"),
                      ("if offset < len(data) and data[offset] & 0xC0 == 0x80:","if False and offset < len(data) and data[offset] & 0xC0 == 0x80:")),T+'test_Q08_normative_unit_rejects_invalid_byte_boundaries'),
 ('Q09', D+'outcomes.py', (("    from guardian.domain.project_view import ReadOnlyEntityView", "    from guardian.application.project_service import ReadOnlyProjectView\n    from guardian.domain.project_view import ReadOnlyEntityView"),),T+'test_Q09_domain_does_not_import_application'),
 ('Q10', P+'application/project_service.py', (("and ref in self.entities)", "and True)"),),T+'test_Q10_status_validator_rejects_orphan_entity_and_scope'),
 ('Q11', S+'syntax.py', (("or self.ast.project != self.token_stream.unit.source.project.value", "or False"),
                        ("if self.cst != build_cst(self.token_stream) or self.ast != parse_gsl(self.token_stream):", "if False and (self.cst != build_cst(self.token_stream) or self.ast != parse_gsl(self.token_stream)):")),T+'test_Q11_frontend_result_cannot_pair_a_foreign_ast_with_local_source'),
 ('Q12', S+'v0.py', (("'unknown','conflict','true','false'", "'unknown','conflict'"),),T+'test_Q12_true_literal_is_not_accepted_as_an_uninterpreted_atom'),
 ('Q13', S+'source_inventory.py', (("if text.startswith('/*', i):", "if False and text.startswith('/*', i):"),),T+'test_Q13_v0_accepts_legal_block_comments_inside_formula'),
 ('Q14', S+'source_inventory.py', (("if (declaration.origin.byte_start, declaration.origin.byte_end) != (original.start, original.end):", "if False and (declaration.origin.byte_start, declaration.origin.byte_end) != (original.start, original.end):"),),T+'test_Q14_declaration_origin_swap_cannot_earn_source_to_ir_equivalence'),
 ('Q15', S+'source_inventory.py', (("    if kind is IRType.REF:\n", "    if kind is IRType.REF:\n        return True\n"),),T+'test_Q15_ir_reference_changes_are_not_full_contract_equivalence'),
 ('NO_PARTIAL_PASS', S+'v0.py', (("and self.correspondence.declarations is CheckStatus.CHECKED", "and True"),
                               ("and self.correspondence.fields is CheckStatus.CHECKED", "and True")),
    'tests/spec_lang/test_lc01_lc02_semantic_audit.py::test_entire_interpreted_contract_matches_pinned_source'),
)


def run(root: Path, output: Path) -> list[dict]:
    results = []
    for name, path, replacements, test in MUTATIONS:
        with tempfile.TemporaryDirectory(prefix='guardian-mutant-') as temp:
            dest = Path(temp)
            for directory in ('src','tests'):
                shutil.copytree(root/directory,dest/directory,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
            shutil.copyfile(root/'pyproject.toml',dest/'pyproject.toml')
            target = dest/path
            code = target.read_text()
            counts = []
            for before, after in replacements:
                count = code.count(before)
                if count == 0:
                    raise ValueError(f'{name}: mutation anchor absent: {before}')
                counts.append(count)
                code = code.replace(before,after)
            target.write_text(code)
            try:
                process = subprocess.run([sys.executable,'-m','pytest','-q',test,'--junitxml=mutation.xml'],
                    cwd=dest,env={**os.environ,'PYTHONPATH':str(dest/'src')+os.pathsep+str(dest/'tests')},
                    capture_output=True,text=True,timeout=30)
                xml = ET.parse(dest/'mutation.xml').getroot()
                errors = sum(int(x.attrib.get('errors','0')) for x in xml.iter('testsuite'))
                failures = sum(int(x.attrib.get('failures','0')) for x in xml.iter('testsuite'))
                skipped = sum(int(x.attrib.get('skipped','0')) for x in xml.iter('testsuite'))
                status = ('KILLED' if process.returncode==1 and failures>0 and errors==0 and skipped==0
                          else 'SURVIVED' if process.returncode==0 else 'INVALID_RUN')
                result = dict(id=name,status=status,test=test,substitutions=counts,
                              returncode=process.returncode,failures=failures,errors=errors,skipped=skipped,
                              output=process.stdout+process.stderr)
            except subprocess.TimeoutExpired:
                result = dict(id=name,status='TIMEOUT_NOT_A_KILL',test=test)
            results.append(result)
            print(name,result['status'],flush=True)
            output.parent.mkdir(parents=True,exist_ok=True)
            output.write_text(json.dumps({'profile':'targeted-semantic-mutations/v1','results':results},indent=2)+'\n')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({'profile':'targeted-semantic-mutations/v1','results':results},indent=2)+'\n')
    return results


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    results=run(args.root,args.output)
    raise SystemExit(0 if all(r['status']=='KILLED' for r in results) else 1)
