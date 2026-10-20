"""Run a bounded G00-01 source-accounting demonstration, NOT normative validation."""
from pathlib import Path
from dataclasses import asdict
import json
from compiler import CompileContext, SourceRecord, compile_strict

ROOT=Path(__file__).parent
CAT=json.loads((ROOT/'g00_01_source_catalog_candidate.json').read_text(encoding='utf8'))
CTX=CompileContext('ProjectGuardian','historical-corpus-pin-required',{
    key:SourceRecord(v['locator'],frozenset(v['logical_items'])) for key,v in CAT.items()
},{key:frozenset(v['logical_items']) for key,v in CAT.items()},frozenset(f'G00-01-F{i:02}-DETAIL' for i in range(1,11)))
result=compile_strict((ROOT/'g00_01_candidate.gsl').read_text(encoding='utf8'),CTX)
print(json.dumps({
    'status':result.status,
    'declarations':len(result.ir['declarations']) if result.ir else 0,
    'proof_obligations':len(result.proof_obligations),
    'unproven':sum(x['status']=='UNPROVEN' for x in result.proof_obligations),
    'diagnostics':[asdict(x) for x in result.diagnostics],
    'ratification':'NONE',
    'development':'REFERENCE_EXPERIMENT_ONLY',
},indent=2))
