"""GSL0-LC03 CST/AST preservation, no false compilation/admission."""
from dataclasses import replace
from random import Random
import pytest

from guardian.spec_lang.contract import CompileStatus,CompilationStage
from guardian.spec_lang.text import (FrontendError,TokenKind,extract_normative_units,lex_gsl)
from guardian.spec_lang.syntax import build_cst,parse_gsl,analyze_source,MAX_NESTING
from foundation_b02 import project,cut,bundle_context

BASE=(b'gsl "0.1";\nproject "project-alpha";\n'
      b'scope "s" { project: project("project-alpha"); }\n'
      b'obligation "o" { from: source_item("s", "F01"); kind: behavior; '
      b'scope: scope("s"); when: not (a and b) or c; }\n')


def given(raw=BASE,name='project-alpha'):
    p=project(name); s=cut(p); return bundle_context(p,s,raw)


def test_lc03_gslt02_hierarchical_cst_yields_original_with_trivia():
    raw=BASE.replace(b'when: not (a and b) or c;',b'when: not (a and b) or c; /* } no closure */')
    b,_=given(raw)
    stream=lex_gsl(extract_normative_units(b,source_format='gsl').units[0])
    cst=build_cst(stream)
    assert cst.yield_bytes()==raw
    groups=[x for x in cst.children if hasattr(x,'children')]
    assert len(groups)==2
    assert any(g.opener.text=='{' and g.closer.text=='}' for g in groups)


def test_lc03_gslt03_ast_contains_every_decl_and_field_without_loss():
    b,_=given()
    stream=lex_gsl(extract_normative_units(b,source_format='gsl').units[0])
    ast=parse_gsl(stream)
    assert [d.kind for d in ast.declarations]==['scope','obligation']
    assert [d.name for d in ast.declarations]==['s','o']
    assert [f.name for f in ast.declarations[1].fields]==['from','kind','scope','when']
    for d in ast.declarations:
        assert b.source_bytes[d.span.start:d.span.end].startswith(d.kind.encode())
        for f in d.fields:
            assert b.source_bytes[f.span.start:f.span.end].startswith(f.name.encode())


def test_lc03_expression_operator_precedence_and_source_grounding():
    b,_=given()
    ast=parse_gsl(lex_gsl(extract_normative_units(b,source_format='gsl').units[0]))
    when=ast.declarations[-1].fields[-1].expr
    assert when.tag=='or' and when.args[0].tag=='not' and when.args[1].tag=='name'
    assert when.args[0].args[0].tag=='and'
    assert b.source_bytes[when.span.start:when.span.end]==b'not (a and b) or c'


def test_lc03_analyze_returns_analyzed_not_compiled_no_certificate():
    b,context=given()
    result=analyze_source(b,context,source_format='gsl')
    assert result.ok
    assert result.status is CompileStatus.ANALYZED
    assert result.stage is CompilationStage.ABSTRACT
    assert result.units[0].cst.yield_bytes()==b.source_bytes
    assert not hasattr(result,'ratified') and not hasattr(result,'qualified')


def test_lc03_analyze_rejects_wrong_project_even_correct_grammar():
    b,ctx=given(BASE.replace(b'project "project-alpha"',b'project "project-beta"'))
    out=analyze_source(b,ctx,source_format='gsl')
    assert out.status is CompileStatus.REJECTED
    assert 'GSL_FOREIGN_PROJECT' in {d.code for d in out.diagnostics}


@pytest.mark.parametrize('bad,expected',[
    (BASE.replace(b'gsl "0.1";',b'gsl "9.9";'),'GSL_VERSION_UNSUPPORTED'),
    (BASE.replace(b'when: not (a and b) or c;',b'when not (a and b) or c;'),'GSL_PARSE_EXPECTED_TOKEN'),
    (BASE.replace(b'obligation "o"',b'unsupported "o"'),'GSL_UNKNOWN_DECLARATION'),
    (BASE.replace(b'when: not (a and b) or c;',b'when: not (a and b or c;'),'GSL_UNBALANCED_DELIMITER'),
    (BASE.replace(b'scope "s" {',b'scope "s" }'),'GSL_UNBALANCED_DELIMITER'),
])
def test_lc03_malformed_source_rejected_fail_closed(bad,expected):
    b,context=given(bad)
    out=analyze_source(b,context,source_format='gsl')
    assert out.status is CompileStatus.REJECTED
    assert expected in {d.code for d in out.diagnostics}


def test_lc03_disallow_trivia_only_from_becoming_compiled():
    b,c=given(b' // nothing\n')
    result=analyze_source(b,c,source_format='gsl')
    assert result.status is CompileStatus.REJECTED
    assert result.diagnostics[0].code=='GSL_PARSE_UNEXPECTED_EOF'


def test_lc03_markdown_prose_examples_and_normative_are_disjoint():
    raw=(b'Explanation\n```gsl example\n'+BASE+b'```\n'+
         b'```gsl normative version=0.1\n'+BASE+b'```\n')
    b,c=given(raw)
    outcome=analyze_source(b,c,source_format='markdown')
    assert outcome.ok,outcome.diagnostics
    assert len(outcome.units)==1
    assert outcome.units[0].cst.yield_bytes()==BASE
    assert outcome.extraction.excluded_spans


def test_lc03_ast_and_cst_not_confused_with_source_digest_identity():
    source,context=given(BASE)
    outcome=analyze_source(source,context,source_format='gsl')
    assert outcome.ok
    assert outcome.units[0].ast.source.source.source_ref==source.source_ref
    assert outcome.units[0].ast.source.source.expected_digest==source.expected_digest


def test_lc03_semantic_test_mutations_remain_ast_not_proof():
    b,c=given(BASE.replace(b'when: not (a and b) or c;',b'when: not (a and b) or false;'))
    out=analyze_source(b,c,source_format='gsl')
    assert out.ok
    assert out.units[0].ast.declarations[1].fields[-1].expr.args[1].value is False
    assert out.status is CompileStatus.ANALYZED


def test_lc03_unknown_feature_source_fails_closed_with_context():
    b,c=given()
    other=project('project-beta');sb=cut(other)
    _,c2=bundle_context(other,sb,BASE)
    res=analyze_source(b,c2,source_format='gsl')
    assert res.status is CompileStatus.REJECTED
    assert res.stage is CompilationStage.ACQUIRE


def test_lc03_unbalanced_nesting_limit_rejects_even_valid_brackets():
    raw=b'gsl "0.1"; project "project-alpha"; scope "s" { p: '+(b'('*70)+b'a'+(b')'*70)+b'; }'
    b,c=given(raw)
    r=analyze_source(b,c,source_format='gsl')
    assert r.status is CompileStatus.REJECTED
    assert r.diagnostics[0].code in ('GSL_CST_DEPTH_LIMIT','GSL_AST_DEPTH_LIMIT')


def test_lc03_lossless_parser_random_whitespace_and_comments():
    rng=Random(1)
    for _ in range(35):
        whitespace=rng.choice([' ','  ','\n','\r\n',' /* ignored } */ ','\t'])
        raw=('gsl'+whitespace+'"0.1";\nproject'+whitespace+'"project-alpha";\n'+
             'source'+whitespace+'"s"'+whitespace+'{\nlocator:'+whitespace+'"literal }";\nsource_cut: context;\n}\n').encode()
        b,c=given(raw)
        out=analyze_source(b,c,source_format='gsl')
        assert out.ok,out.diagnostics
        assert out.units[0].cst.yield_bytes()==raw
        assert out.units[0].ast.declarations[0].kind=='source'


def test_lc03_expression_span_never_splits_unicode_utf8_bytes():
    raw=(b'gsl "0.1"; project "project-alpha";\n'+
         'property "é" { from: source_item("src", "漢字"); holds: a or b; }'.encode())
    b,c=given(raw)
    out=analyze_source(b,c,source_format='gsl')
    assert out.ok,out.diagnostics
    for d in out.units[0].ast.declarations:
        assert b.source_bytes[d.span.start:d.span.end].decode('utf-8')
        for f in d.fields:
            assert b.source_bytes[f.span.start:f.span.end].decode('utf-8')


def test_lc03_direct_forged_compiled_frontend_result_rejected():
    from guardian.spec_lang.syntax import FrontendAnalysis
    with pytest.raises(ValueError,match='LC03_FRONTEND_CANNOT_COMPILE'):
        FrontendAnalysis(CompileStatus.COMPILED,CompilationStage.EMIT,(),())


def test_lc03_direct_forged_cst_with_gapped_tokens_rejected():
    from guardian.spec_lang.syntax import CSTGroup
    from guardian.spec_lang.text import Token,TextSpan
    tok=Token(TokenKind.NAME,'hello',TextSpan(1,6))
    with pytest.raises(ValueError,match='CST_CHILD_SPAN_GAP'):
        CSTGroup(None,(tok,),None,TextSpan(0,6))


def test_lc03_legal_expression_nested_precedence_limit_is_consistent():
    src=b'gsl "0.1"; project "project-alpha"; obligation "o" { when: '+b'('*32+b'a'+b')'*32+b'; }'
    b,c=given(src)
    result=analyze_source(b,c,source_format='gsl')
    assert result.ok,result.diagnostics
    assert result.units[0].cst.yield_bytes()==src


def test_lc03_many_sibling_and_terms_flatten_to_bounded_ast():
    src=b'gsl "0.1"; project "project-alpha"; obligation "o" { when: '+b' and '.join(b'a' for _ in range(200))+b'; }'
    b,c=given(src)
    result=analyze_source(b,c,source_format='gsl')
    assert result.ok,result.diagnostics
    expr=result.units[0].ast.declarations[0].fields[0].expr
    assert expr.tag=='and' and len(expr.args)==200
    assert result.units[0].cst.yield_bytes()==src
