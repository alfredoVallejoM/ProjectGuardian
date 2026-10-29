"""Repeat the explicit G00-01 selection and record byte provenance.

This unsigned local observer is not a trusted runner or an independent review.
The input manifest fixes the selected files; full-checkout acceptance is separate.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys
import pytest


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


class Observer:
    def __init__(self):
        self.collected = []
        self.phases = []
        self.collection_errors = []
        self.deselected = []

    def pytest_collection_finish(self, session):
        self.collected = [item.nodeid for item in session.items]

    def pytest_collectreport(self, report):
        if report.failed:
            self.collection_errors.append(str(report.longrepr))

    def pytest_deselected(self, items):
        self.deselected.extend(item.nodeid for item in items)

    def pytest_runtest_logreport(self, report):
        self.phases.append(dict(nodeid=report.nodeid, phase=report.when,
            outcome=report.outcome, xfail=getattr(report, 'wasxfail', None)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = json.loads(args.manifest.read_bytes())
    observed = {}
    for path, pin in manifest['files'].items():
        raw = (root / path).read_bytes()
        if sha(raw) != pin['sha256'] or git_blob(raw) != pin['git_blob']:
            raise SystemExit('INPUT_MISMATCH:' + path)
        observed[path] = sha(raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    os.chdir(root)
    sys.path.insert(0, str(root))
    observer = Observer()
    command = ['-q', *manifest['selected_test_files'],
               '--junitxml=' + str(args.output.with_suffix('.xml').resolve())]
    exitcode = int(pytest.main(command, plugins=[observer]))
    after = {p: sha((root / p).read_bytes()) for p in observed}
    modules = {}
    provenance_errors = []
    for name, module in sorted(sys.modules.items()):
        if name != 'guardian' and not name.startswith('guardian.'):
            continue
        filename = getattr(module, '__file__', None)
        if not filename:
            provenance_errors.append(name + ':NO_MODULE_FILE')
            continue
        path = Path(filename).resolve()
        raw = path.read_bytes()
        try:
            relative = str(path.relative_to(root))
        except ValueError:
            relative = str(path)
        modules[name] = dict(path=relative, git_blob=git_blob(raw), sha256=sha(raw))
        if relative not in manifest['files'] or sha(raw) != manifest['files'][relative]['sha256']:
            provenance_errors.append(name + ':UNPINNED_MODULE_BYTES')
    failures = [p for p in observer.phases if p['outcome'] != 'passed' or p['xfail'] is not None]
    counts = Counter(p['nodeid'] for p in observer.phases)
    phase_complete = all(counts[n] == 3 and
        {p['phase'] for p in observer.phases if p['nodeid'] == n} == {'setup', 'call', 'teardown'}
        for n in observer.collected)
    case_counts = Counter(n.split('::')[0] for n in observer.collected)
    good = (exitcode == 0 and not failures and not provenance_errors
        and not observer.collection_errors and not observer.deselected
        and observed == after and phase_complete)
    result = dict(schema='guardian/g00-01-selected-execution/v1',
        status='SELECTED_ACCEPTANCE_PASS' if good else 'HOLD',
        base_commit=manifest['base_commit'], python=sys.version, pytest=pytest.__version__,
        hash_seed=os.environ.get('PYTHONHASHSEED'), exitcode=exitcode,
        full_checkout_executed=False, independent_review=False, signed=False,
        command=command, manifest_sha256=sha(args.manifest.read_bytes()),
        collected=observer.collected, cases=len(observer.collected), per_file=dict(case_counts),
        phases=observer.phases, collection_errors=observer.collection_errors,
        deselected=observer.deselected, all_phases_pass=not failures,
        phases_complete=phase_complete, files_before=observed, files_after=after,
        files_stable=observed == after, loaded_modules=modules,
        provenance_errors=provenance_errors, loaded_module_count=len(modules),
        limitations=['not the entire repository', 'no current installed-package execution',
                     'not proof against dishonest runner or transient in-memory changes'])
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'cases', 'loaded_module_count', 'provenance_errors')}, ensure_ascii=False))
    return 0 if good else 1


if __name__ == '__main__':
    raise SystemExit(main())
