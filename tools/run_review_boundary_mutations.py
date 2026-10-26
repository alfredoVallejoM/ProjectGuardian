"""Directed falsification of A01/A02/A03/D01/G01/G02, not independent review.

Each mutant runs in a fresh temporary checkout copy. Only an AssertionError in
an executed test call counts as a kill; collection errors, skip and timeout do
not. No GitHub Actions, in-place mutation, or exhaustive-coverage claim.
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

TEST = 'tests/remediation/test_boundary_repairs.py::'
MUTANTS = (
    ('A01_ENDPOINT', 'tools/g00_acceptance.py',
     '                    check_api_endpoint(identity, row, original, adapters, errors)',
     '                    pass  # mutant: unrelated API accepted',
     TEST + 'test_api_substitution_rejected_even_when_code_and_runtime_pins_match'),
    ('A01_ADAPTER_PIN', 'tools/g00_evidence_bindings.py',
     "if not _hash(expected_pin) or digest(canonical(rows)) != expected_pin:",
     'if False:  # mutant: self-selected adapter',
     TEST + 'test_explicit_adapter_needs_separate_operator_pin_and_bound_review'),
    ('A02_EXACT_CODE', 'tools/g00_evidence_bindings.py',
     'and any(v == code for v in values)', 'and any(code in v for v in values)',
     TEST + 'test_similar_but_not_equal_diagnostic_does_not_count'),
    ('A02_PROPERTY_SCHEMA', 'tools/g00_acceptance.py',
     '        check_properties(cases, errors)', '        pass  # mutant: malformed properties',
     TEST + 'test_diagnostic_properties_require_exact_typed_lists'),
    ('A03_EXECUTED_BYTES', 'tools/g00_acceptance.py',
     '        check_runtime_modules(plan, receipt, before, errors)',
     '        pass  # mutant: ignores actual loaded modules',
     TEST + 'test_actual_isolated_import_allows_identical_copy_and_rejects_other_code'),
    ('D01_REVALIDATE_PAYLOAD', 'src/guardian/domain/source.py',
     "    \"\"\"Validate exact nominal data, never a caller-defined subclass hook.\"\"\"\n    try:",
     "    \"\"\"Mutant skips validation.\"\"\"\n    return Result(cut)\n    try:",
     TEST + 'test_exact_nominal_object_reconstructed_with_invalid_payload_is_revalidated'),
    ('G01_WHOLE_DELTA', 'src/guardian/spec_lang/rebuild.py',
     'if change.after is not None and change.after.source_ref in inputs:',
     'if False:  # mutant: split delete/add bypass',
     'tests/remediation/test_review_source_active.py::test_review_G01_split_delete_add_must_not_bypass_revision_immutability'),
    ('G02_REEXTRACT', 'src/guardian/spec_lang/syntax.py',
     "        if analysis != fresh:\n            raise ValueError('GSL_ANALYSIS_SOURCE_RECONSTRUCTION_MISMATCH')\n        return Result(fresh)",
     '        return Result(analysis)  # mutant: trusts supplied extraction',
     TEST + 'test_each_public_consumer_rejects_a_lost_normative_unit'),
    ('G02_FORMAT_PIN', 'src/guardian/spec_lang/syntax.py',
     'if analysis.source_format != expected_format:', 'if False:  # mutant: interpretation not pinned',
     TEST + 'test_declared_format_is_fixed_in_context_not_chosen_by_supplied_analysis'),
)

HOOK = '''import json, os
from pathlib import Path
import pytest
CALLS=[]
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome=yield
    report=outcome.get_result()
    if report.when == "call":
        CALLS.append({"nodeid":report.nodeid,"outcome":report.outcome,
            "assertion_failure":bool(call.excinfo and call.excinfo.errisinstance(AssertionError))})
def pytest_sessionfinish(session, exitstatus):
    Path(os.environ["MUTATION_RECORD"]).write_text(json.dumps({"exit_status":int(exitstatus),"calls":CALLS}))
'''


def run(root: Path, output: Path, names: list[str] | None = None) -> dict:
    rows = []
    for name, filename, old, new, node in MUTANTS:
        if names and name not in names:
            continue
        with tempfile.TemporaryDirectory(prefix='guardian-review-mutant-') as directory:
            candidate = Path(directory) / 'candidate'
            shutil.copytree(root, candidate, ignore=shutil.ignore_patterns(
                '.git', '__pycache__', '.pytest_cache', '*.pyc', 'execution-evidence', 'build', '*.egg-info'))
            target = candidate / filename
            text = target.read_text(encoding='utf-8')
            if text.count(old) != 1:
                rows.append({'id': name, 'status': 'INVALID', 'reason': 'mutation location not unique'})
                continue
            target.write_text(text.replace(old, new, 1), encoding='utf-8')
            (candidate / 'mutation_hook.py').write_text(HOOK, encoding='utf-8')
            observation = Path(directory) / 'calls.json'
            environment = dict(os.environ, PYTHONPATH=str(candidate), MUTATION_RECORD=str(observation),
                               PYTHONDONTWRITEBYTECODE='1')
            try:
                proc = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'mutation_hook', node],
                    cwd=candidate, env=environment, capture_output=True, text=True, timeout=60)
                calls = json.loads(observation.read_text()) if observation.exists() else {}
                failures = [c['nodeid'] for c in calls.get('calls', []) if c.get('assertion_failure')]
                status = ('KILLED' if proc.returncode == 1 and failures else
                          'SURVIVED' if proc.returncode == 0 else 'INVALID')
                rows.append({'id': name, 'file': filename, 'test': node, 'status': status,
                    'exit_code': proc.returncode, 'assertion_failures': failures,
                    'calls': calls.get('calls', []), 'output_tail': proc.stdout[-1200:]})
            except subprocess.TimeoutExpired:
                rows.append({'id': name, 'status': 'INVALID', 'reason': 'timeout'})
    result = {'schema': 'guardian/review-remediation-mutations/v1', 'python': sys.version.split()[0],
              'independent_review': False, 'exhaustive': False, 'mutants': rows,
              'killed': sum(r['status'] == 'KILLED' for r in rows),
              'survived': sum(r['status'] == 'SURVIVED' for r in rows),
              'invalid': sum(r['status'] == 'INVALID' for r in rows)}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--only', nargs='*')
    args = parser.parse_args()
    result = run(Path(__file__).resolve().parents[1], args.output, args.only)
    print(json.dumps({k: v for k, v in result.items() if k != 'mutants'}, indent=2))
    raise SystemExit(0 if not result['survived'] and not result['invalid'] and result['killed'] else 1)
