"""Check the pinned B00 disposition records and executed tests, not code sufficiency.

The semantic review is authored in the parent judgments and 120 clause rows.
This gate detects damaged/reassigned artifacts. It cannot replace independent
judgment, ratification, or proof that a future implementation meets its contract.
"""
from __future__ import annotations
import argparse
import ast
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


def unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('DUPLICATE_JSON_KEY')
        out[key] = value
    return out


def load(raw):
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('NONFINITE_JSON')))


def inside(root, name):
    if type(name) is not str or Path(name).is_absolute() or '..' in Path(name).parts:
        raise ValueError('UNSAFE_ARTIFACT_PATH')
    path = root / name
    if path.resolve() != path.absolute() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('ARTIFACT_SYMLINK_OR_ESCAPE')
    return path


def table(path):
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding='utf-8')), delimiter='\t'))
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError('MALFORMED_TSV')
    return rows


def population(rows, expected, label, errors):
    actual = [r.get('id') for r in rows]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        errors.append(label + '_POPULATION_MISMATCH')


def check(root, manifest_path, expected_hash, *, junit=None, authority_mode='required'):
    raw = manifest_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_hash:
        return {'status': 'FAIL', 'errors': ['MANIFEST_PIN_MISMATCH']}
    m = load(raw)
    errors = []
    if m.get('schema') != 'guardian.b00-technical-reconciliation/v1':
        errors.append('MANIFEST_VERSION')
    if m.get('ratified') is not False or m.get('campaign_closed') is not False:
        errors.append('UNAUTHORIZED_PROMOTION')
    required_artifacts = {
        'verification/b00/clauses.tsv','verification/b00/apis.tsv',
        'verification/b00/decisions.tsv','verification/b00/parents.json',
        'verification/b00/format_catalog.json',
        *(f'schemas/guardian/{name}.schema.json' for name in
          ('identity-v1','status-v1','contract-ir-v0.1','normative-envelope-v1')),
    }
    if set(m.get('artifacts', {})) != required_artifacts:
        errors.append('ARTIFACT_POPULATION')
    for path, digest in m.get('artifacts', {}).items():
        file = inside(root, path)
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != digest:
            errors.append('ARTIFACT_PIN_MISMATCH:' + path)
    if errors:
        return {'status': 'FAIL', 'errors': errors}
    clauses = table(root/'verification/b00/clauses.tsv')
    population(clauses, {f'G00-{i:02}-F{j:02}' for i in range(1,13) for j in range(1,11)}, 'CLAUSES', errors)
    for row in clauses:
        if row['relation'] not in ('REFINES','DESIGN_CHOICE','CROSS_CONTRACT','BOUNDARY'):
            errors.append('CLAUSE_RELATION:' + row['id'])
        if len(row['disposition']) < 40 or not row['bridge']:
            errors.append('CLAUSE_REASON_MISSING:' + row['id'])
    parents = load((root/'verification/b00/parents.json').read_bytes())
    population(parents['judgments'], {f'G00-{i:02}' for i in range(1,13)}, 'PARENTS', errors)
    if parents['ratified'] is not False or parents['code_completeness_claim'] is not False:
        errors.append('PARENT_REVIEW_PROMOTION')
    for row in parents['judgments']:
        numbers = [n for group in row['dimensions'].values() for n in group]
        if sorted(numbers) != list(range(1,11)) or not row['counterexample'] or not row['bridge']:
            errors.append('PARENT_DIMENSION_COVERAGE:' + row['id'])
    apis = table(root/'verification/b00/apis.tsv')
    population(apis, {f'G00-API-{i:03}' for i in range(1,59)}, 'APIS', errors)
    actual_signatures = 0
    for row in apis:
        path = inside(root, row['owner'])
        nodes = ast.parse(path.read_text()).body if path.is_file() else ()
        fn = next((n for n in nodes if isinstance(n, ast.FunctionDef) and n.name == row['operation']), None)
        signature = '('+ast.unparse(fn.args)+')->'+(ast.unparse(fn.returns) if fn.returns else '?') if fn else '-'
        if signature != row['runtime_signature']:
            errors.append('API_SIGNATURE_DRIFT:' + row['id'])
        if fn:
            actual_signatures += 1
        if not row['decision'] or not row['block']:
            errors.append('API_DISPOSITION_MISSING:' + row['id'])
    decisions = table(root/'verification/b00/decisions.tsv')
    population(decisions, {f'G00-DD-{i:03}' for i in range(1,25)}, 'DECISIONS', errors)
    if any(r['authority_state'] != 'AWAITING_EXTERNAL_RATIFICATION' for r in decisions):
        errors.append('DECISION_SELF_RATIFICATION')
    catalog = load((root/'verification/b00/format_catalog.json').read_bytes())
    if catalog['authority'] != 'CANDIDATE_NOT_RATIFIED' or catalog['generic_domain_decoder_implemented'] is not False:
        errors.append('FORMAT_AUTHORITY_PROMOTION')
    for item in catalog['formats']:
        if item['runtime_domain_decoder'] not in ('EXISTING_BOUNDED_CODEC', 'NOT_IMPLEMENTED'):
            errors.append('FORMAT_DECODER_CLAIM')
    missing_authority = []
    for name, blob in m['original_blob_pins'].items():
        path = inside(root, name)
        if not path.is_file():
            missing_authority.append(name)
            continue
        data = path.read_bytes()
        if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest() != blob:
            errors.append('ORIGINAL_SOURCE_CHANGED:' + name)
    if missing_authority and authority_mode == 'required':
        errors.append('ORIGINAL_BYTES_MISSING')
    executed_cases = None
    if junit is not None:
        tests = list(ET.parse(junit).getroot().iter('testcase')); executed_cases = len(tests)
        if not tests or any(t.find(tag) is not None for t in tests for tag in ('error','failure','skipped')):
            errors.append('EXECUTION_NOT_ALL_PASS')
        for node in m['acceptance_tests']:
            filename, function = node.split('::')
            source = inside(root, filename)
            if not source.is_file() or not any(isinstance(n,ast.FunctionDef) and n.name==function for n in ast.parse(source.read_text()).body):
                errors.append('TEST_BINDING_MISSING:' + node)
            matches = [t for t in tests if t.get('classname') == filename[:-3].replace('/','.')
                       and t.get('name','').split('[',1)[0] == function]
            if not matches:
                errors.append('REQUIRED_TEST_NOT_EXECUTED:' + node)
    return dict(status='TECHNICAL_DISPOSITION_RECORDS_CHECKED' if not errors else 'FAIL', errors=errors,
        clauses=len(clauses),parents=len(parents['judgments']),apis=len(apis),runtime_named_functions=actual_signatures,
        decisions=len(decisions),executed_cases=executed_cases,
        original_source_bytes='CHECKED' if not missing_authority else 'EXTERNAL_GIT_READBACK_REQUIRED',
        missing_authority_files=missing_authority,semantic_review='AUTHORED_NOT_INDEPENDENTLY_REVIEWED',
        implementation_completeness='NOT_CLAIMED',ratification='HOLD_EXTERNAL',campaign_closed=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--expected-manifest-sha256',required=True);p.add_argument('--junit',type=Path,required=True)
    p.add_argument('--authority-mode',choices=('required','external-readback'),default='required')
    a = p.parse_args()
    try:
        r=check(a.root.resolve(),a.manifest,a.expected_manifest_sha256,junit=a.junit,authority_mode=a.authority_mode)
    except (ValueError,TypeError,KeyError,OSError,SyntaxError,ET.ParseError) as e:
        r={'status':'FAIL','errors':[str(e)]}
    print(json.dumps(r,sort_keys=True,ensure_ascii=True))
    return 0 if r['status']=='TECHNICAL_DISPOSITION_RECORDS_CHECKED' else 1


if __name__=='__main__':
    sys.exit(main())
