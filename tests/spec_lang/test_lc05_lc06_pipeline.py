"""Actual source-to-IR tests; independent checker never builds the product IR."""
from dataclasses import replace
import copy
import importlib.util
import itertools
from pathlib import Path
import json
import hashlib
import subprocess
import sys
import pytest

from foundation_b02 import project, cut, bundle_context, entity
from foundation_completion import scenario
from guardian.domain.identity import EntityKind as K, RevisionId, encode_identity
from guardian.domain.clause import ClauseRevision
from guardian.domain.references import RecordSnapshot
from guardian.domain.outcomes import Result
from guardian.spec_lang.contract import SymbolBinding, ProofState
from guardian.spec_lang.syntax import analyze_source
from guardian.spec_lang.ir import IRType, ir_to_data, canonical_bytes, decode_ir
from guardian.spec_lang.typecheck import TypecheckBudget, typecheck_analyses, TypedFormula
from guardian.spec_lang.elaboration import elaborate_program
from guardian.application.specification_service import elaborate_sources

ROOT=Path(__file__).resolve().parents[2]
ORACLE=ROOT/'verification/external_v0/contract_worker.py'
spec=importlib.util.spec_from_file_location('independent_lc05_contract_oracle',ORACLE)
oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
RAW=b'''gsl "0.1"; project "project-alpha";
source "source-main" { locator: "spec/main.gsl"; source_cut: context; }
scope "scope-main" { project: project("project-alpha"); campaign: "G-00"; }
objective "objective-main" { from: source_item("source-main","G00-05-F01"); scope: scope("scope-main"); }
capability "capability-one" { from: source_item("source-main","G00-05-F02"); scope: scope("scope-main"); }
property "property-main" { from: source_item("source-main","G00-05-F03"); kind: behavior; subject: project("project-alpha"); holds: true /* } */ and alpha; }
obligation "obligation-now" { from: source_item("source-main","G00-05-F04"); kind: behavior; scope: scope("scope-main"); when: not (alpha or beta); requires: property("property-main"); verification: verification_ref("verification-main"); }
verification "verification-main" { from: source_item("source-main","G00-12-F01"); target: obligation("obligation-now"); property: property("property-main"); method: property_and_negative; }
relation "relation-main" { kind: proposed_detail; parent: obligation("obligation-now"); child: clause("clause-main"); }
'''
DECLARATIONS=(('source','source-main'),('scope','scope-main'),('objective','objective-main'),
 ('capability','capability-one'),('property','property-main'),('obligation','obligation-now'),
 ('verification','verification-main'),('relation','relation-main'))


def inputs(raw=RAW,source_format='gsl'):
    req,_,ids=scenario();p=req.project;s=req.view.sources[0]
    b,c=bundle_context(p,s,raw)
    clause=ClauseRevision(identity=entity(p.project_id,K.CLAUSE,'clause-main'),source_refs=(s.ref,),
        scope_ref=ids['scope-main'],parent_ref=ids['obligation-now'],source_item='G00-05-F04',
        statement='Keep the original obligation contract',acceptance=('Acceptance is preserved',),
        falsification=('Removing acceptance fails',),verification_spec_refs=(ids['verification-main'],))
    snapshot=replace(req.view,records=req.view.records+(clause,))
    c=replace(c,symbols=(SymbolBinding('clause_main',clause.identity,s.ref),),
              supported_features=c.supported_features|{'deferred-property'})
    parsed=analyze_source(b,c,source_format=source_format)
    assert parsed.ok,parsed.diagnostics
    return b,c,parsed,snapshot,clause


def expected(bundle, *, source_format='gsl', deferred=False, relation=True):
    """Operator inventory written from the fixed input spec, not candidate output."""
    source=bundle.source_ref;project=source.project
    def identity(kind,name):return encode_identity(entity(project,K(kind),name,bundle.revision))
    rows=DECLARATIONS if relation else DECLARATIONS[:-1]
    proofs=[]
    if deferred:
        proofs.append(dict(identifier='interpret:property-main',origin=identity('property','property-main'),state='UNPROVEN'))
    if relation:
        proofs.append(dict(identifier='refinement:relation-main',origin=identity('relation','relation-main'),state='UNPROVEN'))
    return dict(schema='guardian.external-contract-expectation/v1',profile='gsl0/correspondence-0.1',
        source_sha256=hashlib.sha256(bundle.source_bytes).hexdigest(),source_format=source_format,
        project=project.value,revision=bundle.revision.value,source=encode_identity(source),
        declarations=[identity(k,n) for k,n in rows],bindings=[identity('clause','clause-main')],proofs=proofs,
        limits=dict(max_atoms=8,max_valuations=65536,max_total_valuations=262144))


def product(raw=RAW,fmt='gsl'):
    b,c,a,s,_=inputs(raw,fmt)
    result=elaborate_sources((b,),c,formats=(fmt,),snapshot=s)
    return result,b,c,a,s


def test_all_eight_declarations_are_resolved_typed_elaborated_and_externally_compared():
    r,b,c,a,s=product();assert r.ok,r.diagnostics
    out=r.value;ir=out.contracts[0]
    assert [(d.identity.kind.value,d.identity.entity.value) for d in ir.declarations]==list(DECLARATIONS)
    assert out.status=='ELABORATED' and not out.compiled and not out.normatively_admitted
    assert decode_ir(out.canonical_contracts[0])==ir
    report=oracle.verify_contract(b.source_bytes,expected(b),ir_to_data(ir))
    assert report['status']=='SOURCE_IR_CORRESPONDENT' and report['declarations_checked']==8
    assert report['fields_checked']==25 and report['proofs_preserved']==1
    assert report['semantic_obligations_pending'] and not report['full_contract_equivalent']
    assert out.proofs[0].state is ProofState.UNPROVEN
    assert out.unchecked_source_items and out.source_coverage=='SOURCE_ITEMS_NOT_RECONCILED'


@pytest.mark.parametrize('source_format',['gsl','markdown'])
@pytest.mark.parametrize('newline',['\n','\r\n','\r'])
def test_utf8_comments_physical_maps_and_newlines_are_preserved(source_format,newline):
    text=RAW.decode().replace('spec/main.gsl','especificación/β.gsl')
    if source_format=='markdown':
        text='# Fuentes β\n```gsl\nexample is not a normative declaration\n```\n```gsl normative\n'+text+'```\n'
    raw=text.replace('\n',newline).encode()
    r,b,*_=product(raw,source_format);assert r.ok,r.diagnostics
    report=oracle.verify_contract(raw,expected(b,source_format=source_format),ir_to_data(r.value.contracts[0]))
    assert report['status']=='SOURCE_IR_CORRESPONDENT'
    for entry in r.value.source_map:
        entry.origin.verify_against(b)
        assert raw[entry.origin.byte_start:entry.origin.byte_end].decode('utf-8')


@pytest.mark.parametrize('field', ['source_cut','locator','project','scope','from','kind','when','target','property','method'])
def test_required_fields_are_not_defaulted(field):
    # Remove exactly one field in a specified declaration, retaining syntax.
    start={'source_cut':RAW.index(b'source "'),'locator':RAW.index(b'source "'),
           'project':RAW.index(b'scope "'),'scope':RAW.index(b'objective "'),
           'from':RAW.index(b'objective "'),'kind':RAW.index(b'obligation "'),
           'when':RAW.index(b'obligation "'),'target':RAW.index(b'verification "'),
           'property':RAW.index(b'verification "'),'method':RAW.index(b'verification "')}[field]
    i=RAW.index((field+':').encode(),start);j=RAW.index(b';',i)+1
    r,*_=product(RAW[:i]+RAW[j:])
    assert not r.ok and 'GSL_MISSING_NORMATIVE_FIELD' in {d.code for d in r.diagnostics}


@pytest.mark.parametrize('old,new,code',[
 (b'locator: "spec/main.gsl"',b'locator: 34','GSL_EXPRESSION_TYPE_MISMATCH'),
 (b'locator: "spec/main.gsl"',b'locator: true','GSL_EXPRESSION_TYPE_MISMATCH'),
 (b'kind: behavior',b'kind: "behavior"','GSL_EXPRESSION_TYPE_MISMATCH'),
 (b'kind: behavior',b'kind: certified','GSL_UNKNOWN_ENUM_VARIANT'),
 (b'holds: true /* } */ and alpha',b'holds: execute_project("secret")','GSL_EXPRESSION_TYPE_MISMATCH'),
 (b'holds: true /* } */ and alpha',b'holds: 1','GSL_EXPRESSION_TYPE_MISMATCH'),
 (b'campaign: "G-00";',b'campaign: "G-00"; approved: true;','GSL_UNKNOWN_NORMATIVE_FIELD'),
 (b'campaign: "G-00";',b'campaign: "G-00"; campaign: "G-01";','GSL_DUPLICATE_NORMATIVE_FIELD'),
 (b'holds: true /* } */ and alpha;',b'holds: true; deferred_semantics: "behavior";','GSL_PROPERTY_SEMANTICS_REQUIRED'),
 (b'holds: true /* } */ and alpha;',b'deferred_semantics: "";','GSL_EMPTY_DEFERRED_SEMANTICS'),
])
def test_semantic_errors_prevent_partial_elaboration(old,new,code):
    r,*_=product(RAW.replace(old,new,1))
    assert not r.ok and code in {d.code for d in r.diagnostics}


def test_deferred_property_generates_unproven_obligation_preserved_by_oracle():
    raw=RAW.replace(b'holds: true /* } */ and alpha;',b'deferred_semantics: "uninterpreted program behavior";')
    r,b,*_=product(raw);assert r.ok,r.diagnostics
    assert [p.identifier for p in r.value.proofs]==['interpret:property-main','refinement:relation-main']
    assert all(p.state is ProofState.UNPROVEN for p in r.value.proofs)
    assert oracle.verify_contract(raw,expected(b,deferred=True),ir_to_data(r.value.contracts[0]))['proofs_preserved']==2


@pytest.mark.parametrize('feature',['v4-atom','v4-and','v4-not','v4-or','deferred-property'])
def test_semantic_feature_must_be_enabled_in_the_pinned_context(feature):
    raw=RAW if feature!='deferred-property' else RAW.replace(b'holds: true /* } */ and alpha;',b'deferred_semantics: "unknown";')
    b,c,a,s,_=inputs(raw)
    c=replace(c,supported_features=c.supported_features-{feature})
    r=typecheck_analyses((a,),c,snapshot=s)
    assert not r.ok and 'GSL_UNSUPPORTED_NORMATIVE_FEATURE' in {d.code for d in r.diagnostics}


def test_repeated_reference_fields_preserve_order_and_multiplicity():
    raw=RAW.replace(b'requires: property("property-main");',b'requires: property("property-main"); requires: property("property-main");')
    r,b,*_=product(raw);assert r.ok
    fields=r.value.contracts[0].declarations[5].fields
    assert sum(f.name=='requires' for f in fields)==2
    assert oracle.verify_contract(raw,expected(b),ir_to_data(r.value.contracts[0]))['fields_checked']==26


def test_relation_requires_a_real_clause_and_does_not_prove_refinement():
    b,c,a,s,clause=inputs()
    absent=replace(s,records=tuple(x for x in s.records if x.identity!=clause.identity))
    result=typecheck_analyses((a,),c,snapshot=absent)
    assert not result.ok and 'ORPHAN_REFERENCE' in {d.code for d in result.diagnostics}
    wrong=replace(clause,parent_ref=entity(s.project_id,K.OBLIGATION,'another-parent'))
    changed=replace(s,records=tuple(wrong if x.identity==clause.identity else x for x in s.records))
    result=typecheck_analyses((a,),c,snapshot=changed)
    assert not result.ok and 'GSL_RELATION_PARENT_MISMATCH' in {d.code for d in result.diagnostics}
    assert clause.refinement_sufficiency=='NOT_PROVEN' and not clause.normatively_admitted


@pytest.mark.parametrize('change',['value','origin','formula','population'])
def test_elaborator_rejects_forged_public_typed_objects_against_original_source(change):
    b,c,a,s,_=inputs();typed=typecheck_analyses((a,),c,snapshot=s).value
    decl=typed.declarations[4 if change=='formula' else 0];fields=list(decl.fields)
    if change=='value':fields[0]=replace(fields[0],value='changed.gsl')
    elif change=='origin':fields[0]=replace(fields[0],origin=decl.origin)
    elif change=='formula':fields[-1]=replace(fields[-1],value=TypedFormula('no',fields[-1].value.span))
    else:
        with pytest.raises(ValueError,match='POPULATION'):
            replace(typed,declarations=typed.declarations[:-1])
        return
    changed=replace(decl,fields=tuple(fields))
    tampered=replace(typed,declarations=tuple(changed if d.identity==decl.identity else d for d in typed.declarations))
    result=elaborate_program(tampered)
    assert not result.ok and 'GSL_TYPED_PROGRAM_SOURCE_MISMATCH' in result.diagnostics[0].reason


@pytest.mark.parametrize('change',['missing','duplicate','foreign','canonical','digest'])
def test_elaborated_result_rejects_map_population_or_transport_incoherence(change):
    result=product()[0].value
    with pytest.raises((TypeError,ValueError)):
        if change=='missing':replace(result,source_map=result.source_map[:-1])
        elif change=='duplicate':replace(result,source_map=result.source_map+(result.source_map[0],))
        elif change=='foreign':
            other=scenario('project-beta')[0]
            replace(result,source_map=(replace(result.source_map[0],origin=replace(result.source_map[0].origin,source=other.view.sources[0].ref)),)+result.source_map[1:])
        elif change=='canonical':replace(result,canonical_contracts=(b'{}',))
        else:replace(result,contract_digests=(replace(result.contract_digests[0],hex='0'*64),))


@pytest.mark.parametrize('field,value',[('max_nodes',2),('max_depth',1),('max_bytes',10)])
def test_compilation_budget_is_not_an_elaboration_success(field,value):
    b,c,a,s,_=inputs()
    r=elaborate_sources((b,),c,snapshot=s,budget=replace(TypecheckBudget(),**{field:value}))
    assert not r.ok
    assert any('RESOURCE_LIMIT' in d.code for d in r.diagnostics)


def test_omitted_pinned_source_is_not_a_successful_subset_compilation():
    b,c,a,s,_=inputs();other=cut(project(),name='source-second',path='spec/other.gsl')
    second,_=bundle_context(project(),other,b'gsl "0.1"; project "project-alpha"; scope "scope-second" { project:project("project-alpha"); }')
    context=replace(c,expected_sources=c.expected_sources+((second.source_ref,second.expected_digest),))
    r=typecheck_analyses((a,),context,snapshot=s)
    assert not r.ok and r.diagnostics[0].code=='GSL_SOURCE_SET_INCOMPLETE'


def test_multi_source_batch_order_does_not_change_canonical_artifacts():
    p=project();left=cut(p);right=cut(p,name='source-second',path='spec/right.gsl')
    b,c=bundle_context(p,left,b'gsl "0.1"; project "project-alpha"; scope "scope-left" {project:project("project-alpha");}')
    other,_=bundle_context(p,right,b'gsl "0.1"; project "project-alpha"; scope "scope-right" {project:project("project-alpha");}')
    c=replace(c,expected_sources=c.expected_sources+((other.source_ref,other.expected_digest),))
    outputs=[elaborate_sources(items,c) for items in ((b,other),(other,b))]
    assert all(r.ok for r in outputs)
    assert outputs[0].value==outputs[1].value


def test_product_ir_is_verified_in_an_external_process_and_scope_mutation_is_rejected(tmp_path):
    result,b,*_=product();assert result.ok
    source=tmp_path/'source.gsl';expectation=tmp_path/'expectation.json';candidate=tmp_path/'candidate.json'
    source.write_bytes(b.source_bytes);expectation.write_text(json.dumps(expected(b)))
    candidate.write_bytes(result.value.canonical_contracts[0])
    command=[sys.executable,'-I','-S',str(ROOT/'tools/run_external_v0.py'),'--mode','contract',
      '--worker',str(ORACLE),'--expected-worker-sha256',hashlib.sha256(ORACLE.read_bytes()).hexdigest(),
      '--source',str(source),'--expectation',str(expectation),'--expected-expectation-sha256',
      hashlib.sha256(expectation.read_bytes()).hexdigest(),'--candidate',str(candidate)]
    good=subprocess.run(command,capture_output=True,text=True,timeout=30)
    assert good.returncode==0 and json.loads(good.stdout)['status']=='SOURCE_IR_CORRESPONDENT'
    data=json.loads(candidate.read_bytes());data['declarations'][5]['fields'][2]['value']['value']['entity']='forged-scope'
    candidate.write_text(json.dumps(data,sort_keys=True))
    bad=subprocess.run(command,capture_output=True,text=True,timeout=30)
    assert bad.returncode==1 and 'NORMATIVE_FIELD_MISMATCH' in json.loads(bad.stdout)['reason']


@pytest.mark.parametrize('expression',[
    'yes','no','unknown','conflict','true','false','alpha','not alpha',
    'alpha and beta','alpha or beta','not (alpha and beta)','not (alpha or beta)',
    '(alpha or beta) and not gamma','(alpha and beta) or gamma',
    'alpha and (beta or (gamma and conflict))','alpha /* comment */ or unknown',
])
def test_formula_lowering_matches_independent_source_interpretation(expression):
    raw=RAW.replace(b'true /* } */ and alpha',expression.encode())
    r,b,*_=product(raw);assert r.ok,r.diagnostics
    report=oracle.verify_contract(raw,expected(b),ir_to_data(r.value.contracts[0]))
    assert report['status']=='SOURCE_IR_CORRESPONDENT'
    assert report['formula_equivalence']=='CHECKED_FINITE_DOMAIN'


@pytest.mark.parametrize('path_kind',['field','formula'])
def test_exact_source_map_rejects_in_declaration_but_wrong_subspan(path_kind):
    from guardian.spec_lang.elaboration import validate_source_map
    b,c,a,s,_=inputs();typed=typecheck_analyses((a,),c,snapshot=s).value
    output=elaborate_program(typed).value
    maps=list(output.source_map)
    index=next(i for i,m in enumerate(maps) if ('.value' in m.path if path_kind=='formula' else m.path=='$.fields[0]'))
    old=maps[index]
    parent=next(d for ir in output.contracts for d in ir.declarations if d.identity==old.declaration).origin
    maps[index]=replace(old,origin=parent)
    changed=replace(output,source_map=tuple(maps))
    checked=validate_source_map(typed,changed)
    assert not checked.ok and 'GSL_SOURCE_MAP_EXACT_SPAN_MISMATCH' in checked.diagnostics[0].reason
    assert validate_source_map(typed,output).value is True


def test_real_clause_body_roundtrips_without_refinement_or_admission_promotion():
    from guardian.persistence.schema_registry import foundation_schema_registry,encode_record,decode_record,schema_document
    from jsonschema import Draft202012Validator
    _,_,_,snapshot,clause=inputs();registry=foundation_schema_registry(snapshot.revision)
    wire=encode_record(clause,registry)
    assert wire.ok
    assert not list(Draft202012Validator(schema_document(registry)).iter_errors(wire.value))
    decoded=decode_record(wire.value,registry)
    assert decoded.ok and decoded.value.record==clause
    assert decoded.value.record.refinement_sufficiency=='NOT_PROVEN'
    assert not decoded.value.record.normatively_admitted
    wrong=copy.deepcopy(wire.value);wrong['payload']['fields']['parent_ref']['fields']['kind']['value']='property'
    assert not decode_record(wrong,registry).ok
