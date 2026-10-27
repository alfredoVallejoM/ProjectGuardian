"""Directed G00-03 metadata mutations; only real call AssertionErrors are kills."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TARGET = 'src/guardian/domain/source.py'
MUTATIONS = (
    ('entry-metadata', '            SourceEntry.__post_init__(entry)\n', '            pass  # mutant\n',
     'tests/acceptance/test_g00_03_descriptor_boundaries.py::test_entry_metadata_is_revalidated_before_history_or_acquisition[lineage-]'),
    ('exclusion-reason', '            SourceExclusion.__post_init__(exclusion)\n', '            pass  # mutant\n',
     'tests/acceptance/test_g00_03_descriptor_boundaries.py::test_unjustified_exclusion_is_rejected_at_public_boundary[reason-]'),
    ('include-kind', '            _source_reference(reference, EntityKind.SOURCE)\n',
     '            _source_reference(reference, reference.kind)\n',
     'tests/acceptance/test_g00_03_descriptor_boundaries.py::test_unrelated_entity_kind_cannot_be_a_source_include'),
    ('missing-reason', '            MissingSource.__post_init__(missing)\n', '            pass  # mutant\n',
     'tests/acceptance/test_g00_03_descriptor_boundaries.py::test_missing_source_descriptor_keeps_a_real_reason'),
    ('membership-boundary', '    return invalid if invalid else _membership_diagnostics(universe)\n',
     '    return _membership_diagnostics(universe)\n',
     'tests/acceptance/test_g00_03_descriptor_boundaries.py::test_unjustified_exclusion_is_rejected_at_public_boundary[reason-]'),
)
HOOK = '''import json, os
from pathlib import Path
import pytest
EVENTS = {"assertions": [], "other_failures": [], "collection_errors": [], "skipped": []}
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.skipped or hasattr(report, "wasxfail"):
        EVENTS["skipped"].append(item.nodeid)
    if report.failed:
        key = "assertions" if call.when == "call" and call.excinfo is not None and isinstance(call.excinfo.value, AssertionError) else "other_failures"
        EVENTS[key].append(item.nodeid)
def pytest_collectreport(report):
    if report.failed: EVENTS["collection_errors"].append(report.nodeid)
def pytest_sessionfinish(session, exitstatus):
    EVENTS["collected"] = [item.nodeid for item in session.items]
    EVENTS["exit_status"] = int(exitstatus)
    Path(os.environ["G00_MUTATION_RECORD"]).write_text(json.dumps(EVENTS))
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    original = (ROOT / TARGET).read_text(encoding='utf-8')
    rows = []
    for name, before, after, node in MUTATIONS:
        row = {'id': name, 'test': node, 'status': 'INVALID'}
        if original.count(before) != 1:
            row['reason'] = 'MUTATION_ANCHOR_NOT_UNIQUE'; rows.append(row); continue
        with tempfile.TemporaryDirectory(prefix='g00-source-mutant-') as directory:
            tmp = Path(directory)
            shutil.copytree(ROOT / 'src', tmp / 'src', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            (tmp / 'tests/acceptance').mkdir(parents=True)
            for item in ('tests/foundation_b02.py', 'tests/acceptance/test_g00_03_descriptor_boundaries.py'):
                shutil.copy2(ROOT / item, tmp / item)
            (tmp / TARGET).write_text(original.replace(before, after), encoding='utf-8')
            (tmp / 'tests/conftest.py').write_text(HOOK, encoding='utf-8')
            receipt = tmp / 'events.json'
            env = dict(os.environ, PYTHONPATH=os.pathsep.join((str(tmp / 'src'), str(tmp / 'tests'))),
                       G00_MUTATION_RECORD=str(receipt), PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
            try:
                proc = subprocess.run([sys.executable, '-c',
                    'import os,sys,pytest; status=pytest.main(sys.argv[1:]); '
                    'sys.stdout.flush(); sys.stderr.flush(); os._exit(int(status))', '-q', node], cwd=tmp,
                    env=env, capture_output=True, text=True, timeout=30)
                event = json.loads(receipt.read_text()) if receipt.exists() else {}
                row['exit_status'] = proc.returncode
                row['events'] = event
                if (event.get('collected') == [node] and not event.get('other_failures')
                        and not event.get('collection_errors') and not event.get('skipped')):
                    if proc.returncode == 1 and event.get('assertions') == [node]: row['status'] = 'DETECTED'
                    elif proc.returncode == 0 and not event.get('assertions'): row['status'] = 'SURVIVED'
                row['output'] = (proc.stdout + proc.stderr)[-5000:]
            except subprocess.TimeoutExpired:
                row['reason'] = 'TIMEOUT_NOT_A_KILL'
        rows.append(row)
    result = {'schema': 'guardian/g00-03-directed-mutations/v1', 'independent_review': False,
              'cases': rows, 'detected': sum(r['status'] == 'DETECTED' for r in rows),
              'survived': sum(r['status'] == 'SURVIVED' for r in rows),
              'invalid': sum(r['status'] == 'INVALID' for r in rows)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('detected', 'survived', 'invalid')}))
    return 0 if result['detected'] == len(MUTATIONS) else 1


if __name__ == '__main__':
    raise SystemExit(main())
