"""Structural projection only: presence is not semantic completeness."""
import ast,csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]


def test_api_projection_preserves_58_original_ids_and_actual_signatures():
    rows=list(csv.DictReader((ROOT/'verification/b00/apis.tsv').open(),delimiter='\t'))
    assert len(rows)==58 and {r['id'] for r in rows}=={f'G00-API-{i:03}' for i in range(1,59)}
    for r in rows:
        module=ast.parse((ROOT/r['owner']).read_text())
        fn=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name==r['operation'])
        actual='('+ast.unparse(fn.args)+')->'+(ast.unparse(fn.returns) if fn.returns else '?')
        assert actual==r['runtime_signature'],r['id']


def test_projection_keeps_canonical_pins_and_original_adversarial_tests():
    m=json.loads((ROOT/'verification/b00/reconciliation_manifest.json').read_bytes())
    assert m['artifacts']['verification/b00/apis.tsv']==hashlib.sha256((ROOT/'verification/b00/apis.tsv').read_bytes()).hexdigest()
    assert m['original_blob_pins']['architecture/g00_functional_refinement.json']=='b5e2d1d90578dd942647720314047e5d2e4caac2'
    assert len(m['acceptance_tests'])==16 and len(set(m['acceptance_tests']))==16
    assert not m['ratified'] and not m['campaign_closed']
