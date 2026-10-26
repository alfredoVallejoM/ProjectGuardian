"""Pytest plugin recording phases and before/after input bytes, not signatures.

Use: pytest -p tools.pytest_g00_receipt --g00-receipt=/outside/root/receipt.json
The receipt is an unsigned observation. An operator must separately pin it and
an acceptance plan; it cannot authenticate its own producer.
"""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys


def pytest_addoption(parser):
    parser.addoption('--g00-receipt', action='store', default=None,
                     help='Write an unsigned phase/file-bound execution record')


def snapshot(root):
    result = {}
    for prefix in ('src', 'tests', 'tools', 'schemas', 'verification', 'architecture'):
        directory = root / prefix
        if not directory.exists():
            continue
        for path in sorted(directory.rglob('*')):
            if '__pycache__' in path.parts or path.suffix == '.pyc':
                continue
            if path.is_symlink():
                raise ValueError('RECEIPT_SYMLINK_INPUT')
            if path.is_file():
                result[path.relative_to(root).as_posix()] = sha256(path.read_bytes()).hexdigest()
    for name in ('pyproject.toml', 'pytest.ini', 'setup.cfg', 'conftest.py'):
        path = root / name
        if path.exists():
            if path.is_symlink():
                raise ValueError('RECEIPT_SYMLINK_INPUT')
            result[name] = sha256(path.read_bytes()).hexdigest()
    return result


class Recorder:
    def __init__(self, config, path):
        self.root = Path(config.rootpath)
        self.path = Path(path).absolute()
        relative = self.path.relative_to(self.root) if self.path.is_relative_to(self.root) else None
        if relative is not None and relative.parts[0] in ('src', 'tests', 'tools', 'schemas', 'verification', 'architecture'):
            raise ValueError('RECEIPT_MUST_NOT_BE_ITS_OWN_INPUT')
        self.data = {'schema': 'guardian/pytest-execution/v1', 'python': platform.python_version(),
                     'invocation': list(config.invocation_params.args), 'collected': [], 'deselected': [],
                     'collection_errors': [], 'files_before': snapshot(self.root), 'cases': [],
                     'signed': False, 'independent_review': False}
        self.cases = {}

    def pytest_collection_finish(self, session):
        self.data['collected'] = sorted(item.nodeid for item in session.items)

    def pytest_deselected(self, items):
        self.data['deselected'].extend(item.nodeid for item in items)

    def pytest_collectreport(self, report):
        if report.failed:
            self.data['collection_errors'].append(report.nodeid)

    def pytest_runtest_logreport(self, report):
        item = self.cases.setdefault(report.nodeid, {'id': report.nodeid, 'phases': {},
                                                    'wasxfail': False, 'properties': {}})
        if report.when in item['phases']:
            # A rerun is not silently collapsed into a final successful attempt.
            item['phases'][report.when] = 'duplicate-attempt'
        else:
            item['phases'][report.when] = report.outcome
        item['wasxfail'] |= hasattr(report, 'wasxfail')
        for name, value in report.user_properties:
            item['properties'].setdefault(str(name), [])
            text = str(value)
            if text not in item['properties'][str(name)]:
                item['properties'][str(name)].append(text)

    def pytest_sessionfinish(self, session, exitstatus):
        self.data['exit_status'] = int(exitstatus)
        self.data['cases'] = [self.cases[key] for key in sorted(self.cases)]
        self.data['deselected'].sort()
        self.data['files_after'] = snapshot(self.root)
        loaded = {}
        for name, module in sorted(sys.modules.items()):
            if name == 'guardian' or name.startswith('guardian.'):
                filename = getattr(module, '__file__', None)
                if filename and Path(filename).is_file():
                    path = Path(filename).resolve()
                    relative = path.relative_to(self.root).as_posix() if path.is_relative_to(self.root) else str(path)
                    loaded[name] = {'path': relative, 'sha256': sha256(path.read_bytes()).hexdigest()}
        self.data['loaded_guardian_modules'] = loaded
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, sort_keys=True, indent=2) + '\n', encoding='utf-8')


def pytest_configure(config):
    path = config.getoption('--g00-receipt')
    if path:
        config.pluginmanager.register(Recorder(config, path), 'g00-file-bound-receipt')
