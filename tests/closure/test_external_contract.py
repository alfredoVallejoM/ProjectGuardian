"""Independent external verification of complete supported declarations/fields.

Expected source text is fixed separately from candidate construction. Mutation
cases alter candidate, source, authority expectation and transport independently.
"""
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
from guardian.domain.identity import (ProjectId, EntityId, EntityKind, EntityRef,
    RevisionId, ContentDigest, DigestAlgorithm, encode_identity)
from guardian.spec_lang.contract import ProofObligation
from guardian.spec_lang.ir import (ContractIR, DeclarationIR, SourceOrigin, SourceItem,
    IRField, IRValue, IRType, FormulaIR, CommitmentKind, RelationKind, ir_to_data, decode_ir)

ROOT = Path(__file__).resolve().parents[2]
WORKER = ROOT / 'verification/external_v0/contract_worker.py'
RUNNER = ROOT / 'tools/run_external_v0.py'
spec = importlib.util.spec_from_file_location('contract_worker_test', WORKER)
worker = importlib.util.module_from_spec(spec); spec.loader.exec_module(worker)
SHA = lambda raw: hashlib.sha256(raw).hexdigest()
SOURCE = b'''gsl "0.1"; project "project-alpha";
// External reference to clause-main is a reference, NOT proof of existence.
source "source-main" { locator: "spec.gsl"; source_cut: context; }
scope "scope-main" { project: project("project-alpha"); campaign: "G-00"; }
objective "objective-main" { from: source_item("source-main", "G00-05-F01"); scope: scope("scope-main"); }
capability "capability-main" { from: source_item("source-main", "G00-05-F02"); scope: scope("scope-main"); }
property "property-main" { from: source_item("source-main", "G00-05-F03"); kind: constitution; subject: project("project-alpha"); holds: true /* } holds: no; */ and alpha; }
obligation "obligation-main" { from: source_item("source-main", "G00-05-F04"); kind: constitution; scope: scope("scope-main"); when: not (alpha or beta); requires: property("property-main"); verification: verification_ref("verification-main"); }
verification "verification-main" { from: source_item("source-main", "G00-12-F01"); target: obligation("obligation-main"); property: property("property-main"); method: property_and_negative; }
relation "relation-main" { kind: references; parent: obligation("obligation-main"); child: clause("clause-main"); }
'''


def case(raw=SOURCE, source_format='gsl'):
    project = ProjectId('project-alpha'); revision = RevisionId('rev-'+'1'*32)
    def ref(kind, name):
        k = EntityKind(kind)
        return EntityRef(project, k, EntityId(project, k, name), revision)
    source = ref('source', 'source-main')
    digest = ContentDigest(DigestAlgorithm.SHA256, SHA(raw))
    def value(tag, x): return IRValue(IRType(tag), x)
    def r(kind, name): return value('ref', ref(kind, name))
    def item(name): return value('source_item', SourceItem(source, name))
    kind = value('kind', CommitmentKind.CONSTITUTION)
    formulas = FormulaIR('not', (FormulaIR('or', (FormulaIR('atom', name='alpha'), FormulaIR('atom', name='beta'))),))
    rows = [
      ('source','source-main',[('locator',value('text','spec.gsl')),('source_cut',r('source','source-main'))]),
      ('scope','scope-main',[('project',r('project','project-alpha')),('campaign',value('text','G-00'))]),
      ('objective','objective-main',[('from',item('G00-05-F01')),('scope',r('scope','scope-main'))]),
      ('capability','capability-main',[('from',item('G00-05-F02')),('scope',r('scope','scope-main'))]),
      ('property','property-main',[('from',item('G00-05-F03')),('kind',kind),('subject',r('project','project-alpha')),
          ('holds',value('v4',FormulaIR('and',(FormulaIR('yes'),FormulaIR('atom',name='alpha')))))]),
      ('obligation','obligation-main',[('from',item('G00-05-F04')),('kind',kind),('scope',r('scope','scope-main')),
          ('when',value('v4',formulas)),('requires',r('property','property-main')),('verification',r('verification','verification-main'))]),
      ('verification','verification-main',[('from',item('G00-12-F01')),('target',r('obligation','obligation-main')),
          ('property',r('property','property-main')),('method',value('text','property_and_negative'))]),
      ('relation','relation-main',[('kind',value('kind',RelationKind.REFERENCES)),('parent',r('obligation','obligation-main')),
          ('child',r('clause','clause-main'))]),
    ]
    decls=[]
    for typ,name,fields in rows:
        start=raw.index(f'{typ} "{name}" {{'.encode())
        # Fixture lines deliberately put braces inside comments; declaration closes at EOL.
        end=raw.index(b' }\n', start)+2
        decls.append(DeclarationIR(ref(typ,name),SourceOrigin(source,digest,start,end),
                     tuple(IRField(n,v) for n,v in fields)))
    ir=ContractIR(project,source,digest,tuple(decls))
    expected=dict(schema='guardian.external-contract-expectation/v1',profile='gsl0/correspondence-0.1',
        source_sha256=SHA(raw),source_format=source_format,project='project-alpha',revision=revision.value,
        source=encode_identity(source),declarations=[encode_identity(d.identity) for d in decls],
        bindings=[],proofs=[],limits=dict(max_atoms=8,max_valuations=65536,max_total_valuations=262144))
    return raw,expected,ir_to_data(ir)


def run(tmp_path, source, expected, candidate, *, worker_path=WORKER, worker_pin=None,
        expectation_pin=None, mode='contract', env=None):
    paths=[tmp_path/n for n in ('source.gsl','expectation.json','candidate.json')]
    paths[0].write_bytes(source);paths[1].write_text(json.dumps(expected));paths[2].write_text(json.dumps(candidate))
    command=[sys.executable,'-I','-S',str(RUNNER),'--mode',mode,'--worker',str(worker_path),
      '--expected-worker-sha256',worker_pin or SHA(worker_path.read_bytes()),'--source',str(paths[0]),
      '--expectation',str(paths[1]),'--expected-expectation-sha256',expectation_pin or SHA(paths[1].read_bytes()),
      '--candidate',str(paths[2])]
    process=subprocess.run(command,cwd=tmp_path,env=env,capture_output=True,text=True,timeout=15)
    return process.returncode,json.loads(process.stdout)


def fields(candidate):
    return [(d['identity']['entity_kind'],f['name'],f) for d in candidate['declarations'] for f in d['fields']]


def test_all_eight_product_declarations_pass_complete_external_correspondence():
    source,expected,candidate=case()
    assert decode_ir(json.dumps(candidate).encode())
    r=worker.verify_contract(source,expected,candidate)
    assert r['status']=='SOURCE_IR_CORRESPONDENT' and r['declarations_checked']==8
    assert r['fields_checked']==25 and r['formulas_checked']==2 and r['valuations_checked']==20
    assert r['reference_correspondence']=='CHECKED' and r['reference_integrity']=='NOT_CHECKED'
    assert r['normative_admission']=='NOT_CHECKED' and not r['full_contract_equivalent']


@pytest.mark.parametrize('index',range(8))
@pytest.mark.parametrize('attack',['remove','extra','identity','revision','foreign','origin','swap'])
def test_each_declaration_population_identity_origin_and_order_is_bound(index,attack):
    source,e,c=case();d=c['declarations'][index]
    if attack=='remove':del c['declarations'][index]
    elif attack=='extra':c['declarations'].append(copy.deepcopy(d))
    elif attack=='identity':d['identity']['entity']='forged-entity'
    elif attack=='revision':d['identity']['revision']='rev-'+'2'*32
    elif attack=='foreign':d['identity']['project']='foreign-project'
    elif attack=='origin':d['origin']=copy.deepcopy(c['declarations'][(index+1)%8]['origin'])
    else:c['declarations'][index],c['declarations'][(index+1)%8]=c['declarations'][(index+1)%8],c['declarations'][index]
    with pytest.raises(worker.Invalid):worker.verify_contract(source,e,c)


@pytest.mark.parametrize('index',range(25))
def test_every_field_is_checked_not_only_interpreted_formulas(index):
    source,e,c=case();field=fields(c)[index][2];tag=field['value']['tag'];v=field['value']['value']
    if tag in ('text','deferred'):field['value']['value']='forged-value'
    elif tag=='ref':v['entity']='forged-ref'
    elif tag=='source_item':v['logical_item']='wrong-item'
    elif tag=='kind':v['value']='behavior' if v['enum']=='commitment' else 'proposed_detail'
    else:field['value']['value']={'op':'no','name':None,'args':[]}
    if tag=='v4':
        assert worker.verify_contract(source,e,c)['status']=='COUNTEREXAMPLE'
    else:
        with pytest.raises(worker.Invalid):worker.verify_contract(source,e,c)


@pytest.mark.parametrize('index',range(25))
def test_every_field_discriminant_is_compared(index):
    source,e,c=case();fields(c)[index][2]['value']['tag']='integer'
    with pytest.raises(worker.Invalid,match='FIELD_TYPE_MISMATCH'):worker.verify_contract(source,e,c)


@pytest.mark.parametrize('attack',['missing','extra','order','duplicate','unknown'])
def test_fields_cannot_be_omitted_reordered_or_relabelled(attack):
    source,e,c=case();f=c['declarations'][5]['fields']
    if attack=='missing':f.pop()
    elif attack=='extra':f.append(copy.deepcopy(f[-1]))
    elif attack=='order':f.reverse()
    elif attack=='duplicate':f[1]=copy.deepcopy(f[0])
    else:f[1]['name']='unregistered'
    with pytest.raises(worker.Invalid):worker.verify_contract(source,e,c)


@pytest.mark.parametrize('tag',['schema','semantic_version','project','source','source_digest','extra'])
def test_top_level_context_is_operator_pinned(tag):
    source,e,c=case()
    if tag=='project':c[tag]['value']='foreign-project'
    elif tag=='source':c[tag]['revision']='rev-'+'2'*32
    elif tag=='source_digest':c[tag]['hex']='0'*64
    else:c[tag]='unexpected'
    with pytest.raises(worker.Invalid):worker.verify_contract(source,e,c)


def test_declared_schema_is_compared_to_original_profile_not_candidate_code():
    from guardian.spec_lang.ir import _FIELDS,_REQUIRED,_REFERENCE_KIND
    expected={k.value:{n:tag.value for n,tag in fs.items()} for k,fs in _FIELDS.items()}
    actual={k:{n:tag.split(':')[0] for n,tag in fs.items()} for k,fs in worker.FIELDS.items()}
    assert actual==expected
    assert worker.REQUIRED=={k.value:set(v) for k,v in _REQUIRED.items()}
    assert {(k,n):t.split(':')[1] for k,fs in worker.FIELDS.items() for n,t in fs.items() if t.startswith('ref:')}=={(k.value,n):v.value for (k,n),v in _REFERENCE_KIND.items()}


def test_markdown_examples_and_comments_are_not_normative():
    # Example has altered content; normative copy alone must determine correspondence.
    raw=b'```gsl\n'+SOURCE.replace(b'not (alpha or beta)',b'yes')+b'```\n\n~~~gsl normative version=0.1\n'+SOURCE+b'~~~\n'
    source,e,c=case(raw,'markdown')
    # The fixture constructor finds the first copy; explicitly relocate to normative copy.
    offset=raw.index(b'~~~gsl normative version=0.1\n')+len(b'~~~gsl normative version=0.1\n')
    for d in c['declarations']:
        key=d['identity'];start=SOURCE.index(f'{key["entity_kind"]} "{key["entity"]}" {{'.encode())
        d['origin']['byte_start']=offset+start;d['origin']['byte_end']=offset+SOURCE.index(b'\n',start)
    assert worker.verify_contract(source,e,c)['status']=='SOURCE_IR_CORRESPONDENT'


@pytest.mark.parametrize('change',[b'yes // hidden\r\nand alpha',b'yes /* test */ and alpha',b'(yes and alpha)'])
def test_literal_comments_and_grouping_keep_finite_semantics(change):
    source=SOURCE.replace(b'true /* } holds: no; */ and alpha',change)
    s,e,c=case(source);assert worker.verify_contract(s,e,c)['status']=='SOURCE_IR_CORRESPONDENT'


def test_all_remaining_deferred_field_and_proofs_preserved_without_promotion():
    source=SOURCE.replace(b'holds: true /* } holds: no; */ and alpha;',b'deferred_semantics: "program behavior";')
    s,e,c=case(source);d=c['declarations'][4]
    d['fields'][-1]={'name':'deferred_semantics','value':{'tag':'deferred','value':'program behavior'}}
    proof={'identifier':'interpret-property','origin':d['identity'],'state':'UNPROVEN'}
    e['proofs']=[copy.deepcopy(proof)];c['proofs']=[proof]
    r=worker.verify_contract(s,e,c)
    assert r['semantic_obligations_pending'] and r['proofs_preserved']==1
    assert r['status']=='SOURCE_IR_CORRESPONDENT' and not r['full_contract_equivalent']
    c['proofs']=[]
    with pytest.raises(worker.Invalid,match='PROOF_OBLIGATION_MISMATCH'):worker.verify_contract(s,e,c)
    e['proofs']=[]
    with pytest.raises(worker.Invalid,match='DEFERRED_PROOF_REQUIRED'):worker.verify_contract(s,e,c)


def test_proofs_cannot_be_promoted_or_added_silently():
    s,e,c=case();proof={'identifier':'proof','origin':e['declarations'][0],'state':'CHECKED_FINITE_DOMAIN'}
    e['proofs']=[proof];c['proofs']=[proof]
    with pytest.raises(worker.Invalid,match='PROOF_PROMOTION'):worker.verify_contract(s,e,c)


def test_repeated_reference_fields_preserve_multiplicity_and_order():
    source=SOURCE.replace(b'requires: property("property-main");',b'requires: property("property-main"); requires: property("second-property");')
    s,e,c=case(source);f=c['declarations'][5]['fields'];new=copy.deepcopy(f[4]);new['value']['value']['entity']='second-property';f.insert(5,new)
    assert worker.verify_contract(s,e,c)['status']=='SOURCE_IR_CORRESPONDENT'
    f[4],f[5]=f[5],f[4]
    with pytest.raises(worker.Invalid,match='NORMATIVE_FIELD_MISMATCH'):worker.verify_contract(s,e,c)


@pytest.mark.parametrize('budget',[0,True,-1,1,19])
def test_aggregate_budget_cannot_emit_partial_positive(budget):
    s,e,c=case();e['limits']['max_total_valuations']=budget
    if type(budget) is not int or budget<1:
        with pytest.raises(worker.Limited):worker.verify_contract(s,e,c)
    else:
        assert worker.verify_contract(s,e,c)['status']=='INCONCLUSIVE_RESOURCE_LIMIT'


def test_references_respect_operator_version_bindings_but_not_claim_existence():
    s,e,c=case();binding=copy.deepcopy(c['declarations'][-1]['fields'][-1]['value']['value']);binding['revision']='rev-'+'3'*32
    e['bindings']=[binding];c['declarations'][-1]['fields'][-1]['value']['value']=copy.deepcopy(binding)
    r=worker.verify_contract(s,e,c);assert r['status']=='SOURCE_IR_CORRESPONDENT' and r['reference_integrity']=='NOT_CHECKED'
    e['bindings'].append(copy.deepcopy(binding))
    with pytest.raises(worker.Invalid,match='AMBIGUOUS'):worker.verify_contract(s,e,c)


def test_external_process_accepts_real_product_IR_and_rejects_rehashed_scope_change(tmp_path):
    s,e,c=case();rc,r=run(tmp_path,s,e,c)
    assert rc==0 and r['declarations_checked']==8 and not r['signed_attestation']
    c['declarations'][5]['fields'][2]['value']['value']['entity']='wrong-scope'
    c=json.loads(json.dumps(c,sort_keys=True)) # serialization/hashing cannot repair semantics
    rc,r=run(tmp_path,s,e,c);assert rc==1 and 'NORMATIVE_FIELD_MISMATCH' in r['reason']


def test_external_worker_does_not_import_guardian_even_with_poisoned_path(tmp_path):
    poison=tmp_path/'guardian';poison.mkdir();marker=tmp_path/'EXECUTED'
    (poison/'__init__.py').write_text(f'open({str(marker)!r},"w").write("executed")')
    rc,r=run(tmp_path,*case(),env=dict(os.environ,PYTHONPATH=str(tmp_path)))
    assert rc==0 and not marker.exists()
    imports=[n for n in ast.walk(ast.parse(WORKER.read_text())) if isinstance(n,(ast.Import,ast.ImportFrom))]
    assert all('guardian' not in ast.unparse(n) for n in imports)


def test_external_pins_cannot_be_replaced_by_candidate(tmp_path):
    rc,r=run(tmp_path,*case(),worker_pin='0'*64);assert rc==1 and r['reason']=='EXTERNAL_WORKER_PIN_MISMATCH'
    rc,r=run(tmp_path,*case(),expectation_pin='0'*64);assert rc==1 and r['reason']=='PIN_MISMATCH'
    s,e,c=case();rc,r=run(tmp_path,s.replace(b'G-00',b'G-99'),e,c);assert rc==1 and r['reason']=='PIN_MISMATCH'


def test_launcher_never_accepts_contract_checker_under_formula_mode(tmp_path):
    rc,r=run(tmp_path,*case(),mode='formulas')
    assert rc==1 and r['reason']=='EXTERNAL_WORKER_PROTOCOL_MISMATCH'


@pytest.mark.parametrize('raw',[b'{"x":1,"x":2}',b'{"n":NaN}',b'{"n":Infinity}'])
def test_duplicate_or_nonfinite_JSON_is_rejected(raw):
    with pytest.raises(ValueError):worker.load(raw)


def test_rewriting_source_and_all_candidate_digests_cannot_change_operator_pin():
    source=SOURCE.replace(b'"G-00"',b'"G-99"')
    s,e,c=case(source);e['source_sha256']=SHA(SOURCE)
    c['declarations'][1]['fields'][1]['value']['value']='G-99'
    with pytest.raises(worker.Invalid,match='PIN_MISMATCH'):worker.verify_contract(s,e,c)


def test_recomputed_candidate_inventory_cannot_shrink_original_source():
    s,e,c=case();e['declarations'].pop();c['declarations'].pop()
    with pytest.raises(worker.Invalid,match='SOURCE_EXPECTATION_POPULATION'):worker.verify_contract(s,e,c)


@pytest.mark.parametrize('keyword',['true','false'])
def test_product_ir_cannot_encode_language_constants_as_free_atoms(keyword):
    with pytest.raises(ValueError,match='atom needs name'):
        FormulaIR('atom',name=keyword)


@pytest.mark.parametrize('old,new', [
    (b'gsl "0.1"', b'"gsl" "0.1"'),
    (b'project "project-alpha";', b'"project" "project-alpha";'),
    (b'source_cut: context;', b'source_cut: "context";'),
    (b'from: source_item(', b'from: "source_item"('),
    (b'source_cut: context;', b'source_cut ":" context;'),
])
def test_quoted_keywords_and_punctuation_never_become_grammar(old,new):
    raw=SOURCE.replace(old,new,1)
    source,e,c=case(raw)
    with pytest.raises(worker.Invalid):
        worker.verify_contract(source,e,c)
