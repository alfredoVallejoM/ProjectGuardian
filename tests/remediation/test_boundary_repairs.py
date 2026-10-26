"""Non-vacuous regression controls for A01/A02/A03/D01/G01/G02.

Synthetic gate authorities test only execution binding, not all 120 contracts.
Product tests exercise original source bytes and real compiler operations.
"""
from dataclasses import replace
from hashlib import sha1, sha256
import importlib.util
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

from foundation_b02 import project, cut, universe, bundle_context
from guardian.domain.identity import ContentDigest, DigestAlgorithm, RevisionId
from guardian.domain.source import (GitSourceCut, DocumentSourceCut, validate_git_source_cut,
    validate_document_source, validate_source_universe, check_source_membership)
from guardian.spec_lang.contract import SourceBundle
from guardian.spec_lang.syntax import analyze_source, AnalyzedUnit, build_cst, parse_gsl
from guardian.spec_lang.text import Extraction, NormativeUnit, TextSpan, lex_gsl
from guardian.spec_lang.resolution import resolve_analyses
from guardian.spec_lang.typecheck import typecheck_analyses
from guardian.spec_lang.elaboration import elaborate_program
from guardian.spec_lang.emission import emit_program, verify_emission
from guardian.spec_lang.rebuild import rebuild_program, SourceChange
from guardian.application.specification_service import elaborate_sources, emit_sources

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('boundary_gate_fixture',ROOT/'tests/acceptance/test_execution_bindings.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)


def evaluate(root, plan, receipt, adapter_pin=None):
    p,r=f.gate.canonical(plan),f.gate.canonical(receipt)
    return f.gate.check(root,p,r,expected_plan_sha256=f.gate.digest(p),
        expected_receipt_sha256=f.gate.digest(r),expected_api_adapters_sha256=adapter_pin)


def refresh(root, plan, receipt):
    paths=plan['expected_input_files']
    for path in paths:
        paths[path]=f.gate.digest((root/path).read_bytes())
    receipt['files_before']=dict(paths);receipt['files_after']=dict(paths)
    for name,row in plan['expected_runtime_modules'].items():
        row['sha256']=paths[row['source_path']]
        receipt['loaded_guardian_modules'][name]['sha256']=row['sha256']


@pytest.mark.parametrize('field', ['owner','operation'])
def test_api_substitution_rejected_even_when_code_and_runtime_pins_match(tmp_path,field):
    p,r=f.fixture(tmp_path)
    assert evaluate(tmp_path,p,r)['status']=='STRUCTURAL_EXECUTION_BINDINGS_CHECKED'
    (tmp_path/'src/component.py').write_text('def behavior(): return 1\ndef unrelated(): return 1\n')
    (tmp_path/'src/other.py').write_text('def behavior(): return 1\n')
    p['expected_input_files']['src/other.py']='pending';refresh(tmp_path,p,r)
    assert evaluate(tmp_path,p,r)['status']=='STRUCTURAL_EXECUTION_BINDINGS_CHECKED'
    if field=='operation':p['apis'][0]['operation']='unrelated'
    else:p['apis'][0].update(owner='src/other.py',code_paths=['src/other.py'])
    errors=evaluate(tmp_path,p,r)['errors']
    assert errors==['API_CONTRACT_ENDPOINT_MISMATCH:G00-API-001'],errors


def adapted(root):
    p,r=f.fixture(root)
    (root/'src/component.py').write_text('def behavior(): return 1\ndef adapted(): return 1\n')
    (root/'verification').mkdir()
    (root/'verification/adapter.md').write_text('Synthetic adapter review, not normative approval.')
    p['expected_input_files']['verification/adapter.md']='pending';refresh(root,p,r)
    p['apis'][0]['operation']='adapted'
    p['api_adapters']=[dict(id=p['apis'][0]['id'],original_sha256=p['apis'][0]['original_sha256'],
        original_owner='src/component.py',original_operation='behavior',
        target_owner='src/component.py',target_operation='adapted',
        preconditions_review='Preserves the explicit input contract.',
        postconditions_review='Returns the same nominal value.',
        errors_review='Preserves rejection and diagnostic conditions.',review_path='verification/adapter.md')]
    return p,r


def test_explicit_adapter_needs_separate_operator_pin_and_bound_review(tmp_path):
    p,r=adapted(tmp_path)
    assert 'EXTERNAL_API_ADAPTER_PIN_MISMATCH' in evaluate(tmp_path,p,r)['errors']
    pin=f.gate.digest(f.gate.canonical(p['api_adapters']))
    out=evaluate(tmp_path,p,r,pin)
    assert out['status']=='STRUCTURAL_EXECUTION_BINDINGS_CHECKED',out
    assert not out['campaign_closed'] and out['semantic_sufficiency']=='NOT_ESTABLISHED_BY_LINK_CHECK'
    p['api_adapters'][0]['postconditions_review']='changed after the pin'
    assert 'EXTERNAL_API_ADAPTER_PIN_MISMATCH' in evaluate(tmp_path,p,r,pin)['errors']


@pytest.mark.parametrize('field', ['original_operation','original_owner','original_sha256','review_path',
    'preconditions_review','postconditions_review','errors_review'])
def test_adapter_cannot_hide_wrong_origin_or_missing_preservation_review(tmp_path,field):
    p,r=adapted(tmp_path)
    p['api_adapters'][0][field]='' if field.endswith('_review') else 'wrong'
    pin=f.gate.digest(f.gate.canonical(p['api_adapters']))
    out=evaluate(tmp_path,p,r,pin)
    assert out['status']=='HOLD_INCOMPLETE_EVIDENCE',out


@pytest.mark.parametrize('value', ['PREFIX_SYNTHETIC_REJECT_SUFFIX', None, {}, [17], [False], [['SYNTHETIC_REJECT']]])
def test_diagnostic_properties_require_exact_typed_lists(tmp_path,value):
    p,r=f.fixture(tmp_path)
    assert evaluate(tmp_path,p,r)['status']=='STRUCTURAL_EXECUTION_BINDINGS_CHECKED'
    r['cases'][1]['properties']['guardian.diagnostic']=value
    out=evaluate(tmp_path,p,r)
    assert any(e.startswith('INVALID_TEST_PROPERTIES:') for e in out['errors'])
    assert any(e.startswith('ADVERSARY_DIAGNOSTIC_NOT_RECORDED:') for e in out['errors'])


def test_similar_but_not_equal_diagnostic_does_not_count(tmp_path):
    p,r=f.fixture(tmp_path)
    r['cases'][1]['properties']['guardian.diagnostic']=['SYNTHETIC_REJECT_EXTRA','NOT_'+ 'SYNTHETIC_REJECT']
    out=evaluate(tmp_path,p,r)
    assert 'ADVERSARY_DIAGNOSTIC_NOT_RECORDED:ADV-01' in out['errors']


@pytest.mark.parametrize('attack',['plan-missing','observed-missing','population','wrong-bytes','path','source-pin','shape'])
def test_runtime_binding_valid_positive_then_one_isolated_violation(tmp_path,attack):
    p,r=f.fixture(tmp_path)
    assert evaluate(tmp_path,p,r)['status']=='STRUCTURAL_EXECUTION_BINDINGS_CHECKED'
    if attack=='plan-missing':p.pop('expected_runtime_modules')
    if attack=='observed-missing':r.pop('loaded_guardian_modules')
    if attack=='population':r['loaded_guardian_modules']['guardian.extra']=r['loaded_guardian_modules']['guardian.component']
    if attack=='wrong-bytes':r['loaded_guardian_modules']['guardian.component']['sha256']='0'*64
    if attack=='path':r['loaded_guardian_modules']['guardian.component']['path']='/elsewhere/component.py'
    if attack=='source-pin':p['expected_runtime_modules']['guardian.component']['sha256']='0'*64
    if attack=='shape':r['loaded_guardian_modules']['guardian.component']['extra']='unknown'
    out=evaluate(tmp_path,p,r)
    assert out['status']=='HOLD_INCOMPLETE_EVIDENCE',out
    assert any('RUNTIME_MODULE' in e for e in out['errors'])


@pytest.mark.parametrize('same_bytes',[False,True])
def test_actual_isolated_import_allows_identical_copy_and_rejects_other_code(tmp_path,same_bytes):
    root=tmp_path/'candidate';root.mkdir();p,_=f.fixture(root)
    local=root/'src/guardian';local.mkdir()
    (local/'__init__.py').write_text('')
    (local/'component.py').write_text('def behavior():\n    return 0\n')
    installed=tmp_path/'install/guardian';installed.mkdir(parents=True)
    (installed/'__init__.py').write_bytes((local/'__init__.py').read_bytes())
    (installed/'component.py').write_text('def behavior():\n    return '+('0' if same_bytes else '1')+'\n')
    api_path=root/'architecture/g00_api_contracts.json'
    original=json.loads(api_path.read_bytes())
    for row in original['functions']:row['owner_path']='src/guardian/component.py'
    raw=f.gate.canonical(original);api_path.write_bytes(raw)
    p['original_git_blobs']['architecture/g00_api_contracts.json']=sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    for row in p['apis']:
        row['owner']='src/guardian/component.py'
        row['original_sha256']=f.gate.digest(f.gate.canonical(next(x for x in original['functions'] if x['id']==row['id'])))
    for label in ('clauses','apis','attacks','verticals'):
        for row in p[label]:row['code_paths']=['src/guardian/component.py']
    (root/'tests/test_component.py').write_text('from guardian.component import behavior\n'
        +'def test_yes(): assert behavior() == '+('0' if same_bytes else '1')+'\n'
        +'def test_no(record_property):\n    assert behavior() != 2\n    record_property("guardian.diagnostic", "SYNTHETIC_REJECT")\n')
    path=tmp_path/'receipt.json'
    env=dict(os.environ,PYTHONPATH=os.pathsep.join((str(installed.parent),str(ROOT))))
    proc=subprocess.run([sys.executable,'-m','pytest','-q','-p','tools.pytest_g00_receipt',
        '--g00-receipt='+str(path)],cwd=root,env=env,capture_output=True,text=True,timeout=30)
    assert proc.returncode==0,proc.stdout+proc.stderr
    r=json.loads(path.read_bytes())
    p['expected_collection']=r['collected'];p['expected_input_files']=dict(r['files_before'])
    p['expected_runtime_modules']={name:dict(source_path='src/guardian/'+filename,
        sha256=f.gate.digest((local/filename).read_bytes()),allowed_paths=[str(installed/filename)])
        for name,filename in (('guardian','__init__.py'),('guardian.component','component.py'))}
    out=evaluate(root,p,r)
    if same_bytes:assert out['status']=='STRUCTURAL_EXECUTION_BINDINGS_CHECKED',out
    else:assert out['errors']==['RUNTIME_MODULE_BYTES_MISMATCH:guardian.component'],out


@pytest.mark.parametrize('kind',['git','document'])
def test_exact_nominal_object_reconstructed_with_invalid_payload_is_revalidated(kind):
    p=project();source=cut(p)
    if kind=='document':source=DocumentSourceCut(source.ref,'https://example.invalid/doc','v1')
    bad=object.__new__(type(source))
    for field in source.__dataclass_fields__:object.__setattr__(bad,field,getattr(source,field))
    object.__setattr__(bad,'commit' if kind=='git' else 'document_version','main' if kind=='git' else '')
    validator=validate_git_source_cut if kind=='git' else validate_document_source
    assert validator(source).ok
    assert not validator(bad).ok
    out=validate_source_universe(universe(p,(bad,)),p,{bad.ref:bad})
    assert not out.ok and out.diagnostics[0].path=='$.entries[0].cut'
    assert not check_source_membership(p,bad).allowed


def test_source_subclass_hook_is_never_called_by_validator():
    p=project();s=cut(p)
    class Hostile(GitSourceCut):
        def __post_init__(self):raise AssertionError('project callback')
    bad=object.__new__(Hostile)
    for name in s.__dataclass_fields__:object.__setattr__(bad,name,getattr(s,name))
    assert not validate_git_source_cut(bad).ok


def source_program(raw=None,fmt='gsl'):
    p=project();s=cut(p)
    if raw is None:raw=b'gsl "0.1"; project "project-alpha"; scope "scope-main" { project: project("project-alpha"); }'
    b,c=bundle_context(p,s,raw)
    if fmt!='gsl':c=replace(c,source_formats=((b.source_ref,fmt),))
    a=analyze_source(b,c,source_format=fmt)
    t=typecheck_analyses((a,),c);assert t.ok,t.diagnostics
    return b,c,a,t.value


@pytest.mark.parametrize('reverse',[False,True])
def test_split_identical_remove_and_add_is_a_legitimate_noop(reverse):
    b,c,a,p=source_program()
    changes=(SourceChange(b.source_ref,b.expected_digest,None,None),SourceChange(None,None,b,'gsl'))
    if reverse:changes=tuple(reversed(changes))
    out=rebuild_program(p,changes,c)
    assert out.ok,out.diagnostics
    assert out.value.output==elaborate_program(p).value


@pytest.mark.parametrize('fmt',['gsl','markdown'])
def test_declared_format_is_fixed_in_context_not_chosen_by_supplied_analysis(fmt):
    b,c,a,p=source_program()
    if fmt=='markdown':
        # The identical bytes form a valid raw program and a Markdown document
        # containing a fence inside a raw-language block comment.
        raw=(b.source_bytes+b'\n/*\n```gsl normative\n'+b.source_bytes.replace(b'scope-main',b'scope-other')+b'\n```\n*/')
        b,c,a,p=source_program(raw)
    mismatched=analyze_source(b,c,source_format='markdown') if fmt=='markdown' else replace(a,source_format=None)
    if fmt=='markdown':assert mismatched.ok
    r=typecheck_analyses((mismatched,),c)
    assert not r.ok
    assert r.diagnostics[0].code in ('GSL_SOURCE_FORMAT_PIN_MISMATCH','GSL_DECLARED_SOURCE_FORMAT_REQUIRED')


@pytest.mark.parametrize('newline',[b'\n',b'\r',b'\r\n'])
def test_markdown_reextract_preserves_all_norms_examples_and_unicode(newline):
    unit=b'gsl "0.1"; project "project-alpha"; scope "scope-one" { project: project("project-alpha"); }'
    raw=('# áβ🙂\n'.encode()+b'```gsl example\n'+unit+b'\n```\n'
        +b'```gsl normative\n'+unit+b'\n```\n'
        +b'~~~gsl normative\n'+unit.replace(b'scope-one',b'scope-two')+b'\n~~~\n').replace(b'\n',newline)
    b,c,a,p=source_program(raw,'markdown')
    assert len(elaborate_program(p).value.contracts[0].declarations)==2
    emitted=emit_program(p);assert emitted.ok,emitted.diagnostics
    assert verify_emission(emitted.value.wire_bytes,p,emitted.value.compilation_digest).ok
    assert emit_sources((b,),c,formats=('markdown',)).value==emitted.value
    assert not emit_sources((b,),c,formats=('gsl',)).ok


@pytest.mark.parametrize('boundary',['resolve','typecheck','elaborate','emit','verify','rebuild'])
def test_each_public_consumer_rejects_a_lost_normative_unit(boundary):
    unit=b'gsl "0.1"; project "project-alpha"; scope "scope-one" { project: project("project-alpha"); }'
    raw=b'```gsl normative\n'+unit+b'\n```\n```gsl normative\n'+unit.replace(b'scope-one',b'scope-two')+b'\n```\n'
    b,c,a,p=source_program(raw,'markdown')
    good=emit_program(p);assert good.ok
    kept=a.units[:1];u=kept[0].token_stream.unit
    extraction=Extraction(b,(u,),(TextSpan(0,u.span.start),TextSpan(u.span.end,len(raw))))
    bad=replace(a,units=kept,extraction=extraction)
    if boundary=='resolve':r=resolve_analyses((bad,),c)
    elif boundary=='typecheck':r=typecheck_analyses((bad,),c)
    else:
        tampered=replace(p,analyses=(bad,))
        if boundary=='elaborate':r=elaborate_program(tampered)
        elif boundary=='emit':r=emit_program(tampered)
        elif boundary=='verify':r=verify_emission(good.value.wire_bytes,tampered,good.value.compilation_digest)
        else:r=rebuild_program(tampered,(),c)
    assert not r.ok
    assert 'GSL_ANALYSIS_SOURCE_RECONSTRUCTION_MISMATCH' in {d.code for d in r.diagnostics},r.diagnostics


@pytest.mark.parametrize('split',[False,True])
def test_markdown_update_with_new_revision_and_format_pin_is_legitimate(split):
    unit=b'gsl "0.1"; project "project-alpha"; scope "scope-main" { project: project("project-alpha"); campaign: "old"; }'
    raw=b'```gsl normative\n'+unit+b'\n```\n'
    b,c,a,p=source_program(raw,'markdown')
    changed=raw.replace(b'"old"',b'"new"')
    reference=replace(b.source_ref,revision=RevisionId('rev-'+'e'*32))
    new=SourceBundle(reference,changed,ContentDigest(DigestAlgorithm.SHA256,sha256(changed).hexdigest()))
    context=replace(c,expected_sources=((reference,new.expected_digest),),source_formats=((reference,'markdown'),))
    edits=((SourceChange(b.source_ref,b.expected_digest,None,None),SourceChange(None,None,new,'markdown'))
        if split else (SourceChange(b.source_ref,b.expected_digest,new,'markdown'),))
    rebuilt=rebuild_program(p,edits,context)
    assert rebuilt.ok,rebuilt.diagnostics
    direct=typecheck_analyses((analyze_source(new,context,source_format='markdown'),),context)
    assert direct.ok and emit_program(rebuilt.value.program).value==emit_program(direct.value).value


@pytest.mark.parametrize('variant',['list','mutable-pair','duplicate','missing','unknown'])
def test_source_format_pin_map_is_explicit_immutable_and_population_exact(variant):
    b,c,a,p=source_program()
    pins=((b.source_ref,'gsl'),)
    if variant=='list':pins=list(pins)
    if variant=='mutable-pair':pins=([b.source_ref,'gsl'],)
    if variant=='duplicate':pins=pins+pins
    if variant=='missing':pins=((replace(b.source_ref,revision=RevisionId('rev-'+'e'*32)),'gsl'),)
    if variant=='unknown':pins=((b.source_ref,'guess'),)
    with pytest.raises((TypeError,ValueError)):
        replace(c,source_formats=pins)


def test_acceptance_cli_runs_outside_checkout_without_pythonpath(tmp_path):
    environment=dict(os.environ);environment.pop('PYTHONPATH',None)
    proc=subprocess.run([sys.executable,str(ROOT/'tools/g00_acceptance.py'),'--help'],
        cwd=tmp_path,env=environment,capture_output=True,text=True,timeout=20)
    assert proc.returncode==0,proc.stdout+proc.stderr
    assert '--api-adapters-sha256' in proc.stdout
