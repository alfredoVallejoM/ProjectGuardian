"""Check a pinned initial technical profile and its executed acceptance cases.

This is an internal conformance gate, not the external trust root. It imports
candidate types to compare them with an operator-pinned specification snapshot.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


def runtime_profile():
    from guardian.domain.identity import EntityKind, DigestAlgorithm
    from guardian.domain.outcomes import StatusAxis
    from guardian.spec_lang import contract, ir
    return {
        'language_version': contract.LANGUAGE_VERSION,
        'semantic_version': contract.SEMANTIC_VERSION,
        'ir_schema': contract.TYPED_IR_SCHEMA,
        'stages': [stage.value for stage in contract.CompilationStage],
        'compile_statuses': [status.value for status in contract.CompileStatus],
        'proof_states': [status.value for status in contract.ProofState],
        'entity_kinds': [kind.value for kind in EntityKind],
        'digest_algorithms': [item.value for item in DigestAlgorithm],
        'status_axes': [item.value for item in StatusAxis],
        'ir_value_tags': [item.value for item in ir.IRType],
        'commitment_kinds': [item.value for item in ir.CommitmentKind],
        'relation_kinds': [item.value for item in ir.RelationKind],
        'fields': {kind.value: {name: value.value for name, value in fields.items()}
                   for kind, fields in ir._FIELDS.items()},
        'required': {kind.value: sorted(names) for kind, names in ir._REQUIRED.items()},
        'reference_kinds': {kind.value + '.' + field: value.value
                            for (kind, field), value in ir._REFERENCE_KIND.items()},
    }


def check(root, profile_path, expected_hash, junit_path):
    raw = profile_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_hash:
        return {'status': 'FAIL', 'errors': ['PROFILE_PIN_MISMATCH']}
    profile = json.loads(raw)
    errors = []
    if profile.get('schema') != 'guardian.initial-milestone-profile/v1':
        errors.append('PROFILE_SCHEMA')
    if profile.get('runtime') != runtime_profile():
        errors.append('RUNTIME_PROFILE_DRIFT')
    if profile.get('ratified') is not False or profile.get('campaign_closed') is not False:
        errors.append('UNAUTHORIZED_PROFILE_PROMOTION')
    suite = ET.parse(junit_path).getroot()
    cases = list(suite.iter('testcase'))
    if not cases:
        errors.append('NO_EXECUTED_TESTS')
    if any(case.find(tag) is not None for case in cases for tag in ('failure', 'error', 'skipped')):
        errors.append('TEST_SUITE_NOT_ALL_PASS')
    required = profile.get('acceptance', [])
    if not required or len({row['id'] for row in required}) != len(required):
        errors.append('ACCEPTANCE_POPULATION')
    bindings = set()
    for row in required:
        if not row.get('original_basis') or not row.get('test_nodes'):
            errors.append('EMPTY_ACCEPTANCE_BINDING:' + row['id'])
        for node in row['test_nodes']:
            bindings.add(node)
            filename, function = node.split('::')
            path = root / filename
            if not path.is_file():
                errors.append('MISSING_TEST_FILE:' + node)
                continue
            module = ast.parse(path.read_text())
            if not any(isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == function for item in module.body):
                errors.append('MISSING_TEST_FUNCTION:' + node)
            classname = filename[:-3].replace('/', '.')
            matches = [case for case in cases if case.get('classname') == classname
                       and case.get('name', '').split('[', 1)[0] == function]
            if not matches:
                errors.append('TEST_NOT_EXECUTED:' + node)
    return dict(status='PASS' if not errors else 'FAIL', errors=errors,
                acceptance_rows=len(required), distinct_test_functions=len(bindings),
                executed_cases=len(cases), ratified=False, campaign_closed=False,
                gate_scope='PROFILE_AND_EXECUTION_BINDINGS_NOT_SEMANTIC_SUFFICIENCY')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--expected-profile-sha256', required=True)
    parser.add_argument('--junit', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.root / 'src'))
    try:
        result = check(args.root, args.profile, args.expected_profile_sha256, args.junit)
    except (ValueError, KeyError, TypeError, OSError, ET.ParseError, SyntaxError) as exc:
        result = {'status': 'FAIL', 'errors': [str(exc)]}
    print(json.dumps(result, sort_keys=True))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
