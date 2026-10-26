"""Whole-unit omission/injection against the actual LC03->LC05->LC06 path.
No compiler/lexer/parser/evaluator mocks. Altered public objects retain exact
pinned bytes, valid spans and lossless partitions; tests demand re-extraction.
"""
from dataclasses import replace
import pytest
from foundation_b02 import project,cut,bundle_context
from guardian.spec_lang.text import Extraction,NormativeUnit,TextSpan,lex_gsl
from guardian.spec_lang.syntax import analyze_source,AnalyzedUnit,build_cst,parse_gsl
from guardian.spec_lang.typecheck import typecheck_analyses
from guardian.spec_lang.elaboration import elaborate_program


def fixture(second_info):
    p=project();s=cut(p)
    unit1=b'gsl "0.1"; project "project-alpha"; scope "scope-one" { project: project("project-alpha"); }\n'
    unit2=b'gsl "0.1"; project "project-alpha"; scope "scope-two" { project: project("project-alpha"); }\n'
    raw=b'# Specification\n```gsl normative\n'+unit1+b'```\n```gsl '+second_info+b'\n'+unit2+b'```\n'
    source,context=bundle_context(p,s,raw)
    analysis=analyze_source(source,context,source_format='markdown')
    assert analysis.ok,analysis.diagnostics
    return source,context,analysis,unit2


def gaps(source,units):
    result=[];position=0
    for u in units:
        if position<u.span.start:result.append(TextSpan(position,u.span.start))
        position=u.span.end
    if position<len(source.source_bytes):result.append(TextSpan(position,len(source.source_bytes)))
    return tuple(result)


def test_control_real_extraction_preserves_both_normative_units():
    _,context,analysis,_=fixture(b'normative')
    typed=typecheck_analyses((analysis,),context)
    assert typed.ok,typed.diagnostics
    result=elaborate_program(typed.value)
    assert result.ok and len(result.value.contracts[0].declarations)==2


def test_review_G02_extraction_cannot_erase_a_normative_fence():
    source,context,analysis,_=fixture(b'normative')
    kept=analysis.units[:1]
    units=tuple(u.token_stream.unit for u in kept)
    extraction=Extraction(source,units,gaps(source,units))
    forged=replace(analysis,units=kept,extraction=extraction)
    typed=typecheck_analyses((forged,),context)
    if not typed.ok:return
    result=elaborate_program(typed.value)
    assert not result.ok,'Original source has TWO normative fences but an altered extraction yields one accepted IR declaration'


def test_control_example_fence_is_not_normative():
    _,context,analysis,_=fixture(b'example')
    assert len(analysis.units)==1
    typed=typecheck_analyses((analysis,),context)
    assert typed.ok
    assert len(elaborate_program(typed.value).value.contracts[0].declarations)==1


def test_review_G02_extraction_cannot_promote_an_example_fence():
    source,context,analysis,example=fixture(b'example')
    start=source.source_bytes.index(example)
    added=NormativeUnit(source,TextSpan(start,start+len(example)),example,'markdown-fence')
    stream=lex_gsl(added)
    analyzed=AnalyzedUnit(stream,build_cst(stream),parse_gsl(stream))
    included=analysis.extraction.units+(added,)
    forged=replace(analysis,units=analysis.units+(analyzed,),
        extraction=Extraction(source,included,gaps(source,included)))
    typed=typecheck_analyses((forged,),context)
    if not typed.ok:return
    result=elaborate_program(typed.value)
    assert not result.ok,'An EXAMPLE fence was promoted to a normative declaration by supplying a structurally valid extraction'


@pytest.mark.parametrize('mode',['omit-normative','promote-example'])
def test_review_G02_emitter_and_reconstruction_must_rederive_unit_membership(mode):
    from guardian.spec_lang.emission import emit_program, read_emission, verify_emission
    source,context,analysis,example=fixture(b'normative' if mode=='omit-normative' else b'example')
    # Positive control: ordinary frontend output is emitted and reconstructed.
    original=typecheck_analyses((analysis,),context)
    emitted=emit_program(original.value)
    assert emitted.ok,emitted.diagnostics
    assert verify_emission(emitted.value.wire_bytes,original.value,emitted.value.compilation_digest).ok
    if mode=='omit-normative':
        kept=analysis.units[:1]
        included=tuple(u.token_stream.unit for u in kept)
    else:
        start=source.source_bytes.index(example)
        added=NormativeUnit(source,TextSpan(start,start+len(example)),example,'markdown-fence')
        stream=lex_gsl(added)
        kept=analysis.units+(AnalyzedUnit(stream,build_cst(stream),parse_gsl(stream)),)
        included=analysis.extraction.units+(added,)
    forged=replace(analysis,units=kept,extraction=Extraction(source,included,gaps(source,included)))
    typed=typecheck_analyses((forged,),context)
    if not typed.ok:return
    emitted=emit_program(typed.value)
    if not emitted.ok:return
    transport=read_emission(emitted.value.wire_bytes,emitted.value.compilation_digest)
    assert transport.ok,transport.diagnostics  # Integrity is not correspondence.
    rebuilt=verify_emission(emitted.value.wire_bytes,typed.value,emitted.value.compilation_digest)
    assert not rebuilt.ok,'Source-pinned emission and source reconstruction both accept altered normative-unit membership'
