"""External-process conformance. No positive result is a contract certificate."""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from guardian.spec_lang.ir import FormulaIR, _formula_to_data
from guardian.spec_lang.v0 import parse_source_formula, lower_formula

ROOT = Path(__file__).resolve().parents[2]
WORKER = ROOT / 'verification/external_v0/worker.py'
RUNNER = ROOT / 'tools/run_external_v0.py'
SHA = lambda raw: hashlib.sha256(raw).hexdigest()
spec = importlib.util.spec_from_file_location('external_worker_test', WORKER)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


def case(raw=b'not (alpha and beta)', formula=None):
    if formula is None:
        formula = _formula_to_data(lower_formula(parse_source_formula(raw)))
    expected = dict(schema='guardian.external-v0-expectation/v1', profile='gsl0/v4-0.1',
        source_sha256=SHA(raw), expressions=[dict(id='obligation:example/when/0', start=0, end=len(raw))],
        limits=dict(max_atoms=8, max_valuations=65536, max_total_valuations=262144))
    candidate = dict(schema='guardian.external-v0-candidate/v1', formulas=[dict(id='obligation:example/when/0', formula=formula)])
    return raw, expected, candidate


def launch(tmp_path, source, expected, candidate, worker_path=WORKER, worker_pin=None, expectation_pin=None, env=None):
    s, e, c = [tmp_path / name for name in ('source.gsl', 'expected.json', 'candidate.json')]
    s.write_bytes(source)
    e.write_text(json.dumps(expected))
    c.write_text(json.dumps(candidate))
    command = [sys.executable, '-I', '-S', str(RUNNER), '--worker', str(worker_path),
        '--expected-worker-sha256', worker_pin or SHA(worker_path.read_bytes()), '--source', str(s),
        '--expectation', str(e), '--expected-expectation-sha256', expectation_pin or SHA(e.read_bytes()),
        '--candidate', str(c)]
    completed = subprocess.run(command, cwd=tmp_path, env=env, capture_output=True, text=True, timeout=10)
    return completed.returncode, json.loads(completed.stdout)


@pytest.mark.parametrize('raw', [b'true', b'false', b'unknown', b'conflict', b'not unknown', b'not conflict',
    b'alpha and beta', b'alpha or beta', b'not (alpha and beta)', b'not alpha or beta and gamma',
    b'yes /* } when: no; */ and no', b'yes // comment\r\nand no'])
def test_external_profile_matches_real_product_formula_ir(raw):
    source, expected, candidate = case(raw)
    result = worker.verify(source, expected, candidate)
    assert result['status'] == 'FINITE_EQUIVALENT'
    assert result['claim'] == 'PINNED_FORMULAS_ONLY' and not result['full_contract_equivalent']
    assert result['declaration_correspondence'] == 'NOT_CHECKED'


@pytest.mark.parametrize('left', ['unknown', 'yes', 'no', 'conflict'])
@pytest.mark.parametrize('right', ['unknown', 'yes', 'no', 'conflict'])
@pytest.mark.parametrize('op', ['and', 'or'])
def test_external_truth_tables_against_product(left, right, op):
    source, expected, candidate = case(f'{left} {op} {right}'.encode())
    assert worker.verify(source, expected, candidate)['status'] == 'FINITE_EQUIVALENT'


def test_external_runs_without_guardian_or_candidate_imports(tmp_path):
    marker = tmp_path / 'EXECUTED'
    poison = tmp_path / 'guardian'
    poison.mkdir()
    (poison / '__init__.py').write_text(f'from pathlib import Path; Path({str(marker)!r}).touch(); raise RuntimeError("candidate imported")')
    env = dict(os.environ, PYTHONPATH=str(tmp_path))
    status, result = launch(tmp_path, *case(), env=env)
    assert status == 0 and result['valuations_checked'] == 16
    assert result['isolation_flags'] == ['-I', '-S'] and not marker.exists()
    assert not result['signed_attestation']
    imports = [node for node in ast.walk(ast.parse(WORKER.read_text())) if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert all('guardian' not in ast.unparse(node) for node in imports)


def test_worker_pin_is_verified_before_any_code_execution(tmp_path):
    evil = tmp_path / 'evil.py'
    marker = tmp_path / 'EXECUTED'
    evil.write_text(f'from pathlib import Path; Path({str(marker)!r}).touch()')
    status, result = launch(tmp_path, *case(), worker_path=evil, worker_pin=SHA(WORKER.read_bytes()))
    assert status == 1 and result['reason'] == 'EXTERNAL_WORKER_PIN_MISMATCH'
    assert not marker.exists()


def test_expectation_pin_and_source_pin_cannot_be_replaced_by_candidate(tmp_path):
    source, expected, candidate = case()
    status, result = launch(tmp_path, source, expected, candidate, expectation_pin='0' * 64)
    assert status == 1 and result['reason'] == 'PIN_MISMATCH'
    status, result = launch(tmp_path, b'no', expected, candidate)
    assert status == 1 and result['reason'] == 'PIN_MISMATCH'


def test_correct_pin_does_not_mask_a_semantic_mutation(tmp_path):
    raw, expected, candidate = case()
    candidate['formulas'][0]['formula'] = _formula_to_data(FormulaIR('yes'))
    status, result = launch(tmp_path, raw, expected, candidate)
    assert status == 1 and result['status'] == 'COUNTEREXAMPLE'
    assert result['source_value'] != result['ir_value'] and 'witness' in result


@pytest.mark.parametrize('attack', ['missing', 'extra', 'duplicate', 'unknown-field'])
def test_candidate_cannot_reduce_or_extend_operator_frozen_population(attack):
    raw, expected, candidate = case()
    if attack == 'missing': candidate['formulas'] = []
    if attack == 'extra': candidate['formulas'].append(dict(id='extra', formula=_formula_to_data(FormulaIR('yes'))))
    if attack == 'duplicate': candidate['formulas'] *= 2
    if attack == 'unknown-field': candidate['approved'] = True
    with pytest.raises(worker.Invalid): worker.verify(raw, expected, candidate)


@pytest.mark.parametrize('attack', ['duplicate', 'empty', 'bool-start', 'negative-start', 'overflow', 'utf8'])
def test_operator_manifest_is_also_validated_not_assumed_well_formed(attack):
    raw, expected, candidate = case()
    if attack == 'duplicate': expected['expressions'] *= 2
    if attack == 'empty': expected['expressions'] = []
    if attack == 'bool-start': expected['expressions'][0]['start'] = False
    if attack == 'negative-start': expected['expressions'][0]['start'] = -1
    if attack == 'overflow': expected['expressions'][0]['end'] += 1
    if attack == 'utf8':
        raw = 'é yes'.encode(); expected['source_sha256'] = SHA(raw)
        expected['expressions'][0].update(start=1, end=len(raw))
    with pytest.raises((ValueError, UnicodeError)): worker.verify(raw, expected, candidate)


@pytest.mark.parametrize('raw', [b'yes /* open', b'__import__("os")', b'x.__class__', b'yes && no', b'yes no', b''])
def test_unsupported_source_cannot_be_executed_or_silently_accepted(raw):
    _, expected, candidate = case(b'yes')
    expected.update(source_sha256=SHA(raw))
    expected['expressions'][0]['end'] = len(raw)
    with pytest.raises(worker.Invalid): worker.verify(raw, expected, candidate)


def test_candidate_cannot_select_a_different_formula_span():
    raw = b'yes /* no */'
    _, expected, candidate = case(b'yes')
    expected['source_sha256'] = SHA(raw)  # The operator selected the first three bytes.
    candidate['formulas'][0]['formula'] = _formula_to_data(FormulaIR('no'))
    assert worker.verify(raw, expected, candidate)['status'] == 'COUNTEREXAMPLE'
    candidate['formulas'][0]['start'] = 7
    with pytest.raises(worker.Invalid): worker.verify(raw, expected, candidate)


def test_aggregate_budget_does_not_allow_partial_pass():
    raw, expected, candidate = case(b'yes')
    expected['expressions'].append(dict(expected['expressions'][0], id='second'))
    candidate['formulas'].append(dict(candidate['formulas'][0], id='second'))
    expected['limits']['max_total_valuations'] = 1
    result = worker.verify(raw, expected, candidate)
    assert result['status'] == 'INCONCLUSIVE_RESOURCE_LIMIT' and result['checked_formulas'] == 1


@pytest.mark.parametrize('bad', [0, -1, True, '8', None, 1000000000])
def test_budget_has_hard_caps_and_rejects_wrong_types(bad):
    raw, expected, candidate = case()
    expected['limits']['max_atoms'] = bad
    with pytest.raises(worker.Limited): worker.verify(raw, expected, candidate)


def test_duplicate_json_and_unknown_ir_operators_fail_closed():
    with pytest.raises(worker.Invalid): worker.load(b'{"x":1,"x":2}')
    raw, expected, candidate = case(b'yes')
    candidate['formulas'][0]['formula']['op'] = 'execute_python'
    with pytest.raises(worker.Invalid): worker.verify(raw, expected, candidate)


def test_depth_resource_exhaustion_cannot_be_pass(tmp_path):
    raw, expected, candidate = case(b'yes')
    formula = candidate['formulas'][0]['formula']
    for _ in range(100): formula = dict(op='not', name=None, args=[formula])
    candidate['formulas'][0]['formula'] = formula
    status, result = launch(tmp_path, raw, expected, candidate)
    assert status == 1 and result['status'] == 'INCONCLUSIVE_RESOURCE_LIMIT'


def test_external_formula_result_never_replaces_internal_contract_correspondence(tmp_path):
    from dataclasses import replace
    from test_audit_contract_gaps import make_two_obligations
    from foundation_b02 import entity
    from guardian.domain.identity import EntityKind
    from guardian.spec_lang.ir import IRField, IRType, IRValue
    from guardian.spec_lang.v0 import verify_contract_semantics
    raw = (b'gsl "0.1"; project "project-alpha"; obligation "obl-one" { when: yes; '
           b'from: source_item("source-main", "obl-one"); kind: constitution; scope: scope("scope-main"); }')
    ir, bundle, context, grounding, coverage = make_two_obligations(raw)
    assert verify_contract_semantics(ir, bundle, context, grounding, expectation=coverage).acceptable
    _, expected, candidate = case(b'yes')
    expected['source_sha256'] = SHA(raw)
    # Operator-selected bytes, not a span imported from the candidate source map.
    start = raw.index(b'when: yes;') + len(b'when: ')
    expected['expressions'][0].update(start=start, end=start + 3)
    formula = next(field.typed_value.value for field in ir.declarations[0].fields if field.name == 'when')
    candidate['formulas'][0]['formula'] = _formula_to_data(formula)
    status, checked = launch(tmp_path, raw, expected, candidate)
    assert status == 0 and checked['checked_formulas'] == 1
    decl = ir.declarations[0]
    wrong = replace(decl, fields=tuple(
        IRField('scope', IRValue(IRType.REF, entity(ir.project, EntityKind.SCOPE, 'wrong-scope')))
        if field.name == 'scope' else field for field in decl.fields))
    internal = verify_contract_semantics(replace(ir, declarations=(wrong,)), bundle, context, grounding, expectation=coverage)
    assert not internal.acceptable
    assert checked['reference_integrity'] == 'NOT_CHECKED' and not checked['full_contract_equivalent']
