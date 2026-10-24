"""Audit-only falsifications against ae8561f; no production edits.
Tests assert the specification, not the observed faulty behavior.
"""
from pathlib import Path
import ast
from dataclasses import replace
from hashlib import sha256
import pytest
from foundation_b02 import project,cut,universe,bundle_context,entity
from guardian.domain.identity import *
from guardian.domain.outcomes import *
from guardian.domain.project import *
from guardian.domain.source import *
from guardian.application.project_service import *
from guardian.spec_lang.contract import *
from guardian.spec_lang.ir import *
from guardian.spec_lang.syntax import analyze_source, AnalyzedUnit
from guardian.spec_lang.text import NormativeUnit, TextSpan
from guardian.spec_lang.v0 import *


def fixture(raw=b'gsl "0.1"; project "project-alpha"; obligation "obl-main" { when: true; }'):
    p=project();s=cut(p);b,c=bundle_context(p,s,raw)
    return p,s,b,c


def test_Q01_status_parser_rejects_an_enum_from_another_axis():
    result=parse_status(StatusAxis.MATERIAL, AuditStatus.PASS)
    assert not result.ok, 'AuditStatus.PASS was converted to MaterialStatus.PASS'


def test_Q02_sidcar_governance_repository_is_a_valid_project_source():
    p=project(mode=StorageMode.SIDECAR);s=cut(p,repo=p.storage.authority_repository)
    r=check_source_membership(p,s)
    assert r.allowed, (r.code,'sidecar governance documents cannot be loaded')


def test_Q03_same_material_cut_cannot_be_called_disjoint_by_changing_lineage():
    p=project();a=cut(p,name='source-one');b=replace(a,ref=entity(p.project_id,EntityKind.SOURCE,'source-two'))
    u=universe(p,(a,b));v=validate_source_universe(u,p,{a.ref:a,b.ref:b});d=describe_source_coverage(u)
    assert not(v.ok and d.source_population_disjoint), 'two aliases of same material cut are declared disjoint'


def test_Q04_document_baseline_cycles_are_diagnosed():
    p=project();a=DocumentSourceCut(entity(p.project_id,EntityKind.SOURCE,'document-one'),'https://example.org/spec','v1')
    b=replace(a,ref=entity(p.project_id,EntityKind.SOURCE,'document-two'),document_version='v2')
    entries=(SourceEntry(a,HistoryRole.DELTA,SourceStatus.CONTENT_OBSERVED,'one-history',b.ref),
             SourceEntry(b,HistoryRole.DELTA,SourceStatus.CONTENT_OBSERVED,'one-history',a.ref))
    u=universe(p,(a,b),entries=entries);r=validate_source_universe(u,p,{a.ref:a,b.ref:b})
    assert any(x.code in ('HISTORICAL_CYCLE','HISTORICAL_BASE_MISSING') for x in r.diagnostics), r


def test_Q05_missing_source_entry_is_visible_in_coverage_description():
    p=project();s=cut(p);u=universe(p,(s,),entries=(SourceEntry(s,HistoryRole.BASE,SourceStatus.MISSING,'history'),))
    d=describe_source_coverage(u)
    assert d.known_missing or any('missing' in x.lower() for x in d.limitations), d


def test_Q06_compile_context_cannot_hold_mutable_source_pins():
    _,_,b,c=fixture();item=[b.source_ref,b.expected_digest]
    try:
        ctx=replace(c,expected_sources=(item,))
    except (TypeError,ValueError):
        return
    initial=verify_source_context(b,ctx).ok
    item[1]=ContentDigest(DigestAlgorithm.SHA256,'0'*64)
    assert verify_source_context(b,ctx).ok==initial, 'same frozen context changes trust through mutable nested list'


def test_Q07_compiled_result_rejects_an_untyped_digest():
    with pytest.raises((TypeError,ValueError)):
        CompilationResult(CompileStatus.COMPILED,CompilationStage.EMIT,(),artifact_digest='fake-digest')


@pytest.mark.parametrize('start,end,raw',[(0,20,b'\xc3\xa9'),(1,2,b'\xa9')])
def test_Q08_normative_unit_rejects_invalid_byte_boundaries(start,end,raw):
    _,_,b,_=fixture('é'.encode())
    with pytest.raises((TypeError,ValueError)):
        NormativeUnit(b,TextSpan(start,end),raw,'gsl')


def test_Q09_domain_does_not_import_application():
    from guardian.domain import outcomes
    root=Path(outcomes.__file__).parent
    violations=[]
    for p in root.glob('*.py'):
        for n in ast.walk(ast.parse(p.read_text())):
            if isinstance(n,ast.ImportFrom) and n.module and n.module.startswith('guardian.application'):
                violations.append((p.name,n.lineno,n.module))
    assert not violations, violations


def test_Q10_status_validator_rejects_orphan_entity_and_scope():
    p,s,_,_=fixture();u=universe(p,(s,));v=build_readonly_project_view(p,u,{s.ref:s}).value
    target=entity(p.project_id,EntityKind.OBLIGATION,'absent-obligation');scope=entity(p.project_id,EntityKind.SCOPE,'absent-scope')
    obs=StatusObservation(target,TypedStatus(StatusAxis.MATERIAL,MaterialStatus.PASS),s.ref,scope,target.revision,'reviewer')
    assert not validate_status_observation(obs,v).ok, 'entity/scope absent from supplied snapshot are accepted'


def test_Q11_frontend_result_cannot_pair_a_foreign_ast_with_local_source():
    _,_,b,c=fixture();r=analyze_source(b,c,source_format='gsl');assert r.ok
    try:
        forged=replace(r,units=(replace(r.units[0],ast=replace(r.units[0].ast,project='foreign-project')),))
    except (TypeError,ValueError):
        return
    assert not forged.ok,'ANALYZED accepts mismatched AST and source'


def test_Q12_true_literal_is_not_accepted_as_an_uninterpreted_atom():
    _,_,b,c=fixture();r=analyze_source(b,c,source_format='gsl');assert r.ok
    e=r.units[0].ast.declarations[0].fields[0].expr
    assert e.tag=='bool' and e.value is True
    origin=SourceOrigin(b.source_ref,b.expected_digest,e.span.start,e.span.end)
    # Direct construction now rejects literal keywords. Keep the original
    # verifier attack too, using an explicitly forged object as untrusted input.
    forged = object.__new__(FormulaIR)
    object.__setattr__(forged, 'op', 'atom')
    object.__setattr__(forged, 'name', 'true')
    object.__setattr__(forged, 'args', ())
    report=verify_semantics(b,c,origin,forged)
    assert not report.acceptable, 'true is parsed as bool in LC03 but as free atom in LC02'


def test_Q13_v0_accepts_legal_block_comments_inside_formula():
    raw=b'gsl "0.1"; project "project-alpha"; obligation "obl-main" { when: yes /* comment */ and no; }'
    _,_,b,c=fixture(raw);r=analyze_source(b,c,source_format='gsl');assert r.ok
    e=r.units[0].ast.declarations[0].fields[0].expr
    report=verify_semantics(b,c,SourceOrigin(b.source_ref,b.expected_digest,e.span.start,e.span.end),FormulaIR('and',(FormulaIR('yes'),FormulaIR('no'))))
    assert report.acceptable, (report.status,report.reason)


def make_two_obligations(raw):
    p,s,b,c=fixture(raw);r=analyze_source(b,c,source_format='gsl');assert r.ok
    ds=[];gs=[]
    for decl in r.units[0].ast.declarations:
        ref=entity(p.project_id,EntityKind.OBLIGATION,decl.name);e=decl.fields[0].expr
        origin=SourceOrigin(b.source_ref,b.expected_digest,decl.span.start,decl.span.end)
        fields=(IRField('from',IRValue(IRType.SOURCE_ITEM,SourceItem(s.ref,decl.name))),
                IRField('kind',IRValue(IRType.KIND,CommitmentKind.CONSTITUTION)),
                IRField('scope',IRValue(IRType.REF,entity(p.project_id,EntityKind.SCOPE,'scope-main'))),
                IRField('when',IRValue(IRType.V4,FormulaIR(str(e.value)))))
        ds.append(DeclarationIR(ref,origin,fields));gs.append(FormulaGrounding(ref,'when',0,SourceOrigin(s.ref,b.expected_digest,e.span.start,e.span.end)))
    ir=ContractIR(p.project_id,s.ref,b.expected_digest,tuple(ds));exp=CoverageExpectation(frozenset(d.identity for d in ds),frozenset((d.identity,'when',0) for d in ds))
    return ir,b,c,tuple(gs),exp


def test_Q14_declaration_origin_swap_cannot_earn_source_to_ir_equivalence():
    raw=b'gsl "0.1"; project "project-alpha"; obligation "obl-one" { when: yes; from: source_item("source-main", "obl-one"); kind: constitution; scope: scope("scope-main"); } obligation "obl-two" { when: no; from: source_item("source-main", "obl-two"); kind: constitution; scope: scope("scope-main"); }'
    ir,b,c,g,exp=make_two_obligations(raw)
    assert verify_contract_semantics(ir,b,c,g,expectation=exp).acceptable
    first=replace(ir.declarations[0],origin=ir.declarations[1].origin,fields=ir.declarations[1].fields)
    wrong=replace(ir,declarations=(first,ir.declarations[1]))
    bindings=(replace(g[0],origin=g[1].origin),g[1])
    result=verify_contract_semantics(wrong,b,c,bindings,expectation=exp)
    assert result.correspondence.declarations.value == 'MISMATCH'
    assert not result.acceptable,(result.status,'obl-one:yes swapped to obl-two:no without changing expected IDs')


def test_Q15_ir_reference_changes_are_not_full_contract_equivalence():
    raw=b'gsl "0.1"; project "project-alpha"; obligation "obl-one" { when: yes; from: source_item("source-main", "obl-one"); kind: constitution; scope: scope("scope-main"); }'
    ir,b,c,g,exp=make_two_obligations(raw)
    assert verify_contract_semantics(ir,b,c,g,expectation=exp).acceptable
    d=ir.declarations[0]
    fields=tuple(IRField('scope',IRValue(IRType.REF,entity(ir.project,EntityKind.SCOPE,'wrong-scope'))) if f.name=='scope' else f for f in d.fields)
    wrong=replace(ir,declarations=(replace(d,fields=fields),))
    result=verify_contract_semantics(wrong,b,c,g,expectation=exp)
    assert result.correspondence.fields.value == 'MISMATCH'
    assert not result.acceptable, 'V4 equality does not establish reference equality (documented boundary)'
