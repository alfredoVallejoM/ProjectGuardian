"""Directed B04 mutations in temporary copies; not an independent audit.

Only pytest assertion failures (including missing expected rejection) count as
kills. Collection errors, exception-only failures, timeouts and skips do not.
No network, Actions, repository writes or automatic qualification.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

SCOPE = 'src/guardian/domain/scope.py'
UNIT = 'tests/domain/test_b04_scope.py::'
PROP = 'tests/domain/test_b04_composition_properties.py::'
ADV = 'tests/domain/test_b04_adversarial.py::'
INT = 'tests/integration/test_b04_applicability_product_path.py::'
MUTATIONS = (
    ('B04-M01', SCOPE,
     'elif observation.complete and cs:\n                negative.extend(cs)',
     'elif ws:\n                negative.extend(ws)',
     UNIT+'test_f06_complete_sets_not_missing_data_can_supply_negative_witness'),
    ('B04-M02', SCOPE,
     'if profile.context != facts.context:', 'if False:',
     UNIT+'test_f10_evidence_from_another_profile_context_is_rejected'),
    ('B04-M03', SCOPE,
     'value = left.value.conjunction(right.value) if conjunction else left.value.disjunction(right.value)',
     'value = left.value.disjunction(right.value)',
     UNIT+'test_f04_f05_exact_support_tables_and_contributing_witnesses'),
    ('B04-M04', SCOPE,
     "result = negate_evidence(results[path + '.0'])", "result = results[path + '.0']",
     PROP+'test_all_64_scoped_valuations_match_independent_nested_tables'),
    ('B04-M05', SCOPE,
     "if not witnesses:\n                    raise ValueError('CONSTANT_NOT_AUTHORIZED')",
     "if False:\n                    raise ValueError('CONSTANT_NOT_AUTHORIZED')",
     UNIT+'test_explicit_constants_require_scoped_authorization_not_empty_all'),
    ('B04-M06', SCOPE,
     'if self.steps + amount > self.budget.max_steps:', 'if False:',
     PROP+'test_exact_budget_boundary_and_unexamined_failure_are_not_boolean_values'),
    ('B04-M07', SCOPE,
     'conflicts = tuple(sorted(set(left.conflicts + right.conflicts), key=_conflict_key))',
     'conflicts = ()',
     ADV+'test_direct_composition_preserves_conflict_witnesses_when_final_value_is_decisive'),
    ('B04-M08', 'src/guardian/domain/scope_codec.py',
     "if type(raw['schema']) is not str or raw['schema'] != SCHEMA:",
     "if raw['schema'] != SCHEMA or type(raw['schema']) is not str:",
     ADV+'test_scope_codec_does_not_invoke_candidate_schema_equality'),
    ('B04-M09', SCOPE,
     'if atom.evidence_ref is not None:', 'if False:',
     PROP+'test_source_selector_does_not_take_another_sources_negative_witness'),
    ('B04-M10', 'src/guardian/domain/campaign.py',
     'return Result(DueDescription(obligation.due, obligation.milestone == milestone,\n                                name, \'NOT_CHECKED\', evaluation))',
     'return Result(DueDescription(DueStatus.CURRENT, obligation.milestone == milestone,\n                                name, \'NOT_CHECKED\', evaluation))',
     UNIT+'test_f07_applicability_does_not_promote_future_to_current_or_approve'),
    ('B04-M11', 'src/guardian/application/contract_service.py',
     'if entry is None or entry.acquisition not in (SourceStatus.CONTENT_OBSERVED, SourceStatus.SEMANTIC_RECONCILED):',
     'if entry is None:',
     INT+'test_unobserved_sources_cannot_supply_applicability_witnesses'),
    ('B04-M12', SCOPE,
     "if self.unexamined or not self.trace or self.trace[-1].path != '$' or self.trace[-1].result != self.result:",
     "if not self.trace or self.trace[-1].path != '$' or self.trace[-1].result != self.result:",
     ADV+'test_complete_report_cannot_hide_unexamined_nodes'),
)


def run(root: Path, selected: set[str] | None = None) -> dict:
    records = []
    for identifier, relative, before, after, test in MUTATIONS:
        if selected is not None and identifier not in selected:
            continue
        original = (root/relative).read_text(encoding='utf-8')
        if original.count(before) != 1:
            records.append(dict(id=identifier, status='INVALID_MUTATION', reason='replacement not unique'))
            continue
        with tempfile.TemporaryDirectory(prefix='guardian-b04-mutation-') as temporary:
            work = Path(temporary)
            for name in ('src', 'tests', 'tools', 'verification', 'schemas'):
                if (root/name).is_dir():
                    shutil.copytree(root/name, work/name,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.egg-info', '.pytest_cache'))
            shutil.copyfile(root/'pyproject.toml', work/'pyproject.toml')
            (work/relative).write_text(original.replace(before, after, 1), encoding='utf-8')
            report = work/'result.xml'
            command = [sys.executable, '-m', 'pytest', '-q', test, '--junitxml='+str(report)]
            try:
                proc = subprocess.run(command, cwd=work, capture_output=True, text=True, timeout=60)
                cases = list(ET.parse(report).getroot().iter('testcase')) if report.is_file() else []
                failures = [t.find('failure') for t in cases if t.find('failure') is not None]
                invalid = (not cases or proc.returncode not in (0,1) or
                           any(t.find(tag) is not None for t in cases for tag in ('error','skipped')))
                assertion_failures = bool(failures) and all(
                    'AssertionError' in f.get('message','') or 'DID NOT RAISE' in f.get('message','')
                    or (f.text is not None and 'AssertionError' in f.text)
                    for f in failures)
                status = ('INVALID_RUN' if invalid or (failures and not assertion_failures)
                          else 'KILLED' if proc.returncode == 1 and assertion_failures else 'SURVIVED')
                records.append(dict(id=identifier, status=status, target=relative, test=test,
                    cases=len(cases), assertion_failures=len(failures), returncode=proc.returncode,
                    tail=proc.stdout[-1800:]))
            except (OSError, subprocess.TimeoutExpired, ET.ParseError) as exc:
                records.append(dict(id=identifier, status='INVALID_RUN', reason=str(exc)))
    return dict(schema='guardian.directed-b04-mutations/v1', scope='DIRECTED_NOT_EXHAUSTIVE',
        independent_audit=False, mutations=records,
        killed=sum(r['status']=='KILLED' for r in records),
        survived=sum(r['status']=='SURVIVED' for r in records),
        invalid=sum(r['status'] not in ('KILLED','SURVIVED') for r in records))


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--only', action='append')
    p.add_argument('--output', type=Path)
    args=p.parse_args()
    valid={r[0] for r in MUTATIONS}
    if args.only and not set(args.only)<=valid:
        p.error('unknown mutation ID')
    result=run(args.root.resolve(), set(args.only) if args.only else None)
    raw=json.dumps(result, ensure_ascii=False, indent=2)+'\n'
    if args.output:args.output.write_text(raw,encoding='utf-8')
    print(raw)
    return 0 if result['killed']==len(result['mutations']) and result['mutations'] else 1


if __name__=='__main__':
    sys.exit(main())
