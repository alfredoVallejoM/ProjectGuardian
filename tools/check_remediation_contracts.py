"""Structural contract gate anchored to an externally supplied baseline hash.

Checks inventory preservation, exact finding/obligation bindings, real symbols,
non-skipped falsification functions and (optionally) canonical Git blob pins.
Link checks do NOT establish test sufficiency or authenticate their executor.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path


def validate(root: Path, baseline: dict, manifest: dict) -> list[str]:
    problems = []
    expected = {r['id']: r for r in baseline['findings']}
    rows = manifest.get('findings', [])
    observed = {r['id']: r for r in rows}
    if len(observed) != len(rows) or set(observed) != set(expected):
        problems.append('FINDING_POPULATION_DRIFT')
    if manifest.get('original_clause_ids') != baseline['original_clause_ids']:
        problems.append('CLAUSE_POPULATION_DRIFT')
    for identifier, row in observed.items():
        if identifier not in expected:
            continue
        wanted = expected[identifier]
        if row.get('obligations') != wanted['obligations']:
            problems.append(identifier+':OBLIGATION_BINDING_DRIFT')
        if row.get('falsification') != wanted['falsification']:
            problems.append(identifier+':FALSIFICATION_BINDING_DRIFT')
        for entry in [row.get('falsification', ''), *row.get('symbols', [])]:
            try:
                filename, symbol = entry.split('::')
                path = root/filename
                if not path.resolve().is_relative_to(root.resolve()):
                    raise ValueError('path escapes repository')
                tree = ast.parse(path.read_text())
                nodes = [n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and n.name == symbol]
                if len(nodes) != 1:
                    raise ValueError('symbol absent or ambiguous')
                if entry == row.get('falsification'):
                    if any(isinstance(n,ast.Attribute) and n.attr in ('skip','skipif','xfail','importorskip') for n in ast.walk(tree)):
                        raise ValueError('test module skips required checks')
                    assertions = [n for n in ast.walk(nodes[0]) if isinstance(n,ast.Assert)]
                    exceptions = [n for n in ast.walk(nodes[0]) if isinstance(n,ast.Attribute) and n.attr=='raises']
                    if not assertions and not exceptions:
                        raise ValueError('no falsification assertion')
                    if assertions and all(isinstance(n.test,ast.Constant) for n in assertions):
                        raise ValueError('only constant assertions')
            except (OSError,ValueError,SyntaxError) as exc:
                problems.append(identifier+':INVALID_LINK:'+entry+':'+str(exc))
    return problems


def check(root: Path, baseline_path: Path, manifest_path: Path, expected_hash: str,
          tree_readback: Path | None = None) -> list[str]:
    raw = baseline_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_hash:
        return ['UNTRUSTED_BASELINE_DIGEST']
    baseline = json.loads(raw)
    errors = validate(root, baseline, json.loads(manifest_path.read_bytes()))
    if tree_readback is not None:
        tree = json.loads(tree_readback.read_bytes())
        if tree.get('files') != baseline['canonical_blob_pins']:
            errors.append('CANONICAL_SOURCE_TREE_DRIFT')
    return errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--expected-baseline-sha256', required=True)
    parser.add_argument('--tree-readback', type=Path)
    args = parser.parse_args()
    issues = check(args.root,args.baseline,args.manifest,args.expected_baseline_sha256,args.tree_readback)
    print(json.dumps({'structural_contract_gate':'FAIL' if issues else 'PASS','findings':issues},indent=2))
    raise SystemExit(bool(issues))
