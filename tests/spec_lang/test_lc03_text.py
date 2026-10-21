"""GSL0-LC03 source byte laws, explicit normative fences and adversarial lexing."""
from hashlib import sha256
import random
import pytest

from guardian.spec_lang.contract import SourceBundle
from guardian.spec_lang.text import (FrontendError,TextSpan,TokenKind,
    lossless_scan,extract_normative_units,lex_gsl)
from foundation_b02 import project,cut,bundle_context


def bundle(raw):
    p=project();s=cut(p)
    return bundle_context(p,s,raw)[0]


def test_lc03_gslt01_scanner_reconstructs_utf8_crlf_bom_comment_and_unicode():
    for raw in (b'', b'\r\n\n',b'hello  world\t\r\n',
                'é µ漢字 🌍  \r\n// source\n'.encode(), '\ufeffcafé\r\n'.encode()):
        segments=lossless_scan(bundle(raw))
        assert b''.join(seg.raw for seg in segments)==raw
        last=0
        for seg in segments:
            assert seg.span.start==last
            last=seg.span.end
            raw[:last].decode('utf-8')
        assert last==len(raw)


def test_lc03_gslt01_random_unicode_lossless_property():
    rng=random.Random(42)
    alphabet=['a','1',' ','\r','\n','\t','é','漢','🌍','}']
    for _ in range(100):
        raw=''.join(rng.choice(alphabet) for _ in range(rng.randrange(90))).encode('utf-8')
        assert b''.join(s.raw for s in lossless_scan(bundle(raw)))==raw


def test_lc03_markdown_extract_only_explicit_normative_fences():
    text=('Intro 🌍\r\n```gsl example\r\n'+
          'gsl "0.1"; project "wrong";\r\n```\r\n'+
          '```gsl normative version=0.1\r\n'+
          'gsl "0.1";\r\nproject "project-alpha";\r\n'+
          'source "s" { locator: "é"; source_cut: context; }\r\n'+
          '```\r\nEnd\r\n').encode()
    e=extract_normative_units(bundle(text),source_format='markdown')
    assert len(e.units)==1
    assert b'project "wrong"' not in e.units[0].raw
    assert b'locator: "\xc3\xa9"' in e.units[0].raw
    assert e.units[0].raw==text[e.units[0].span.start:e.units[0].span.end]
    spans=sorted([x.span for x in e.units]+list(e.excluded_spans),key=lambda x:x.start)
    assert b''.join(text[s.start:s.end] for s in spans)==text


def test_lc03_markdown_two_normative_fences_have_independent_spans():
    raw=(b'Hello\n```gsl normative\n'+b'gsl "0.1"; project "project-alpha";\n'+
         b'```\nOther\n~~~gsl normative version=0.1\n'+
         b'gsl "0.1"; project "project-alpha";\n'+b'~~~\n')
    result=extract_normative_units(bundle(raw),source_format='markdown')
    assert len(result.units)==2
    assert result.units[0].span.end<result.units[1].span.start


@pytest.mark.parametrize('text,code',[
    (b'```gsl example\na\n```\n','GSL_NO_NORMATIVE_UNITS'),
    (b'```gsl\ngsl "0.1";\n```','GSL_NO_NORMATIVE_UNITS'),
    (b'```gsl normative version=9.9\na\n```','GSL_INVALID_NORMATIVE_FENCE'),
    (b'```gsl normative\na','GSL_UNTERMINATED_MARKDOWN_FENCE'),
    (b'```gsl normative\n```','GSL_EMPTY_UNIT'),
])
def test_lc03_markdown_fence_is_fail_closed(text,code):
    with pytest.raises(FrontendError) as caught:
        extract_normative_units(bundle(text),source_format='markdown')
    assert caught.value.code==code


def test_lc03_lexer_preserves_comments_trivia_escaped_quotes_and_nested_braces_in_string():
    source=(b'gsl "0.1"; // } ) \r\nproject "project-alpha";\n'
            b'source "s" { locator: "\\\"}\\\""; /* ) } */ source_cut: context; }\n')
    b=bundle(source)
    stream=lex_gsl(extract_normative_units(b,source_format='gsl').units[0])
    assert stream.yield_bytes()==source
    assert sum(t.kind is TokenKind.COMMENT for t in stream.tokens)==2
    assert any(t.kind is TokenKind.STRING and '}' in t.text for t in stream.tokens)
    assert any(t.kind is TokenKind.WHITESPACE for t in stream.tokens)


@pytest.mark.parametrize('raw,code',[
    (b'gsl "0.1"; @bad','GSL_UNKNOWN_TOKEN'),
    (b'gsl "0.1"; /* unterminated','GSL_UNTERMINATED_COMMENT'),
    (b'gsl "0.1"; "unterminated','GSL_UNTERMINATED_STRING'),
    (b'gsl "0.1"; "bad\\xescape"','GSL_INVALID_STRING_ESCAPE'),
    (b'gsl "0.1"; 1.2.3','GSL_INVALID_NUMBER'),
    (b'gsl "0.1"; 42suffix','GSL_INVALID_NUMBER'),
])
def test_lc03_lexer_negative_tokens_rejected_with_code(raw,code):
    with pytest.raises(FrontendError) as caught:
        lex_gsl(extract_normative_units(bundle(raw),source_format='gsl').units[0])
    assert caught.value.code==code


def test_lc03_lexer_budget_limit_detects_resource_exhaustion():
    b=bundle(b'gsl "0.1"; project "project-alpha";')
    with pytest.raises(FrontendError,match='GSL_TOKEN_RESOURCE_LIMIT'):
        lex_gsl(extract_normative_units(b,source_format='gsl').units[0],max_tokens=2)


def test_lc03_lexer_utf8_spans_exact_absolute_offsets_in_markdown():
    raw=('## Éxample\n```gsl normative\ngsl "0.1"; project "project-alpha";\n'+
         'property "élément" { holds: not (a and b); }\n```\n').encode()
    unit=extract_normative_units(bundle(raw),source_format='markdown').units[0]
    stream=lex_gsl(unit)
    assert stream.yield_bytes()==unit.raw
    for t in stream.tokens:
        assert raw[t.span.start:t.span.end].decode('utf-8')==t.text


def test_lc03_lexer_true_number_string_escape_labels():
    b=bundle(b'gsl "0.1"; project "project-alpha"; scope "s" { value: -1.4e+3; flag: true; }')
    stream=lex_gsl(extract_normative_units(b,source_format='gsl').units[0])
    assert any(t.text=='-1.4e+3' and t.kind is TokenKind.NUMBER for t in stream.tokens)
    assert stream.yield_bytes()==b.source_bytes


def test_lc03_markdown_comment_does_not_create_normative_contract():
    md=(b'<!--\n```gsl normative\ngsl "0.1"; project "project-alpha";\n```\n-->\n'+
        b'```gsl normative\ngsl "0.1"; project "project-alpha";\n```\n')
    e=extract_normative_units(bundle(md),source_format='markdown')
    assert len(e.units)==1
    assert e.units[0].raw==b'gsl "0.1"; project "project-alpha";\n'


def test_lc03_markdown_mixed_character_fence_cannot_close_normative_block():
    raw=b'```gsl normative\ngsl "0.1"; project "project-alpha";\n```~~~\n'
    with pytest.raises(FrontendError,match='GSL_UNTERMINATED_MARKDOWN_FENCE'):
        extract_normative_units(bundle(raw),source_format='markdown')
