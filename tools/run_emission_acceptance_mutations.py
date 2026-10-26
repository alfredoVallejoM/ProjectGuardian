"""Directed C14/T08/B08 falsations; invalid executions never count as kills."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

E = 'src/guardian/spec_lang/emission.py'
R = 'src/guardian/spec_lang/rebuild.py'
G = 'tools/g00_acceptance.py'
TE = 'tests/spec_lang/test_emission_rebuild.py::'
TG = 'tests/acceptance/test_execution_bindings.py::'
MUTATIONS = (
    ('EMIT-PIN', E, 'if _digest(raw) != expected_digest:', 'if False:', TE+'test_external_pin_is_checked_before_decoding_unverified_bundle'),
    ('EMIT-FORGED-IR', E, 'if output is not None and (type(output) is not ElaboratedProgram or output != fresh.value):', 'if False:', TE+'test_self_consistent_elaborated_object_cannot_replace_original_source'),
    ('EMIT-RECHECK', E, 'if rebuilt.value.wire_bytes != raw:', 'if False:', TE+'test_rehashed_formula_change_is_detected_by_rebuilding_source'),
    ('EMIT-COMPILER', E, "'implementation': context.compiler.implementation,", "'implementation': 'ignored-build',", TE+'test_changed_context_cannot_validate_an_earlier_emission[compiler]'),
    ('REBUILD-OLD-PIN', R, 'if old.expected_digest != change.before_digest:', 'if False:', TE+'test_invalid_update_never_returns_stale_ir[old-digest]'),
    ('REBUILD-HISTORY', R, 'and change.after.source_bytes != old.source_bytes):', 'and False):', TE+'test_invalid_update_never_returns_stale_ir[same-revision]'),
    ('GATE-ORIGINAL', G, 'if actual != pins[name]:', 'if False:', TG+'test_pinned_original_blob_cannot_be_replaced_by_current_author_claim'),
    ('GATE-COLLECTION', G, 'if len(set(expected)) != len(expected) or len(set(collected)) != len(collected) or set(expected) != set(collected):', 'if False:', TG+'test_unlinked_collected_population_cannot_drop_an_expected_regression'),
    ('GATE-PHASE', G, "or any(phases.get(phase) != 'passed' for phase in ('setup', 'call', 'teardown'))", 'or False', TG+'test_a_green_count_cannot_hide_failed_or_unexecuted_cases[failed-call]'),
    ('GATE-FILES', G, 'if digest(safe_file(root, name).read_bytes()) != checksum:', 'if False:', TG+'test_external_pins_and_actual_files_must_match_the_execution[source-changed]'),
    ('GATE-CLAUSE', G, "if original is None or digest(canonical(original)) != row.get('original_sha256'):", 'if original is None:', TG+'test_contract_and_test_links_cannot_be_reduced_or_reassigned[requirement]'),
    ('GATE-FALSIFICATION', G, "errors.append('TEST_LINKS_MISSING_OR_DUPLICATE:' + label)", 'pass  # deliberately discard missing falsification', TG+'test_contract_and_test_links_cannot_be_reduced_or_reassigned[negative]'),
)


def pytest_runtest_makereport(item, call):
    # Pytest invokes this hook before constructing each report. Record the real
    # exception class; parsing a traceback string is not reliable evidence.
    if call.excinfo is not None:
        item.user_properties.append(('mutation.exception_type', call.excinfo.type.__name__))


def run(root: Path) -> dict:
    rows = []
    for identity, filename, before, after, target in MUTATIONS:
        with tempfile.TemporaryDirectory(prefix='guardian-mutation-') as directory:
            work = Path(directory) / 'candidate'
            shutil.copytree(root, work, ignore=shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache', '*.egg-info', 'build', 'dist'))
            path = work / filename
            original = path.read_text(encoding='utf-8')
            if original.count(before) != 1:
                rows.append({'id': identity, 'status': 'INVALID_PATCH', 'matches': original.count(before)})
                continue
            path.write_text(original.replace(before, after, 1), encoding='utf-8')
            junit = Path(directory) / 'run.xml'
            command = [sys.executable, '-m', 'pytest', '-q', '-p', 'tools.run_emission_acceptance_mutations', target, '--tb=short', '--junitxml='+str(junit)]
            try:
                completed = subprocess.run(command, cwd=work, text=True, stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT, timeout=35)
                cases = list(ET.parse(junit).getroot().iter('testcase')) if junit.exists() else []
                invalid = not cases or any(case.find(tag) is not None for case in cases for tag in ('error', 'skipped'))
                failures = [case for case in cases if case.find('failure') is not None]
                assertion = bool(failures) and all(any(p.get('name') == 'mutation.exception_type'
                    and p.get('value') == 'AssertionError' for p in case.iter('property')) for case in failures)
                status = ('KILLED_BY_ASSERTION' if completed.returncode == 1 and assertion and not invalid
                          else 'SURVIVED' if completed.returncode == 0 and not invalid else 'INVALID_EXECUTION')
                rows.append({'id': identity, 'path': filename, 'test': target, 'status': status,
                             'returncode': completed.returncode, 'executed_cases': len(cases)})
            except (subprocess.TimeoutExpired, ET.ParseError, OSError) as exc:
                rows.append({'id': identity, 'status': 'INVALID_EXECUTION', 'reason': type(exc).__name__})
    return {'schema': 'guardian/emission-acceptance-mutations/v1', 'scope': 'DIRECTED_NOT_EXHAUSTIVE',
            'independent_review': False, 'killed': sum(r['status']=='KILLED_BY_ASSERTION' for r in rows),
            'survived': sum(r['status']=='SURVIVED' for r in rows),
            'invalid': sum(r['status'].startswith('INVALID') for r in rows), 'cases': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.root)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps({key:value for key,value in result.items() if key!='cases'}, sort_keys=True))
    return int(result['survived'] != 0 or result['invalid'] != 0)


if __name__ == '__main__':
    raise SystemExit(main())
