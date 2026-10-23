"""GSL0-LC03: lossless UTF-8 text, explicit normative Markdown fences and lexer.

No text is declared normative merely because it looks like a program. The
caller supplies an immutable SourceBundle and must select the source format.
This module has no filesystem, clock, Git, LLM, admission or policy effects.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum

from guardian.spec_lang.contract import SourceBundle

MAX_BYTES=2_000_000
MAX_TOKENS=100_000
_IDENT=re.compile(r'[A-Za-z_][A-Za-z_0-9]*\Z', re.ASCII)
_NUMBER=re.compile(r'[+-]?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?')
_FENCE=re.compile(r'^( {0,3})(`{3,}|~{3,})([^\r\n]*)$')
_CLOSER=re.compile(r'^ {0,3}(`{3,}|~{3,})[ \t]*$')
_PUNCT=frozenset('{}()[]:;,')


class FrontendError(ValueError):
    def __init__(self, code:str, start:int, message:str):
        super().__init__(f'{code} at byte {start}: {message}')
        self.code=code
        self.byte_start=start
        self.message=message


@dataclass(frozen=True,slots=True)
class TextSpan:
    start:int
    end:int

    def __post_init__(self)->None:
        if type(self.start) is not int or type(self.end) is not int or self.start<0 or self.end<self.start:
            raise ValueError('INVALID_TEXT_SPAN')


@dataclass(frozen=True,slots=True)
class TextSegment:
    span:TextSpan
    category:str
    raw:bytes

    def __post_init__(self)->None:
        if not isinstance(self.span,TextSpan) or type(self.raw) is not bytes or len(self.raw)!=self.span.end-self.span.start:
            raise ValueError('INVALID_TEXT_SEGMENT')
        if self.category not in ('content','whitespace','newline'):
            raise ValueError('INVALID_SEGMENT_KIND')


def lossless_scan(bundle:SourceBundle)->tuple[TextSegment,...]:
    """Lossless document segmentation; every byte occurs exactly once."""
    if not isinstance(bundle,SourceBundle):
        raise TypeError('expected pinned SourceBundle')
    data=bundle.source_bytes
    if len(data)>MAX_BYTES:
        raise FrontendError('GSL_TEXT_RESOURCE_LIMIT',0,'source exceeds byte budget')
    chars=data.decode('utf-8')
    segments:list[TextSegment]=[]
    start=0
    byte_cursor=0
    previous=None
    for ch in chars:
        cat='newline' if ch in '\r\n' else 'whitespace' if ch.isspace() else 'content'
        if previous is not None and cat!=previous:
            segments.append(TextSegment(TextSpan(start,byte_cursor),previous,data[start:byte_cursor]))
            start=byte_cursor
        previous=cat
        byte_cursor+=len(ch.encode('utf-8'))
    if previous is not None:
        segments.append(TextSegment(TextSpan(start,byte_cursor),previous,data[start:byte_cursor]))
    if b''.join(segment.raw for segment in segments)!=data:
        raise AssertionError('LOSSLESS_DOCUMENT_RECONSTRUCTION_FAILURE')
    return tuple(segments)


@dataclass(frozen=True,slots=True)
class NormativeUnit:
    source:SourceBundle
    span:TextSpan
    raw:bytes
    format:str

    def __post_init__(self)->None:
        if not isinstance(self.source,SourceBundle) or not isinstance(self.span,TextSpan):
            raise TypeError('unit needs fixed source and span')
        data = self.source.source_bytes
        if self.span.end > len(data):
            raise ValueError('SOURCE_UNIT_OUT_OF_BOUNDS')
        for offset in (self.span.start, self.span.end):
            if offset < len(data) and data[offset] & 0xC0 == 0x80:
                raise ValueError('SOURCE_UNIT_SPLITS_UTF8')
        if type(self.raw) is not bytes or not self.raw or data[self.span.start:self.span.end]!=self.raw:
            raise ValueError('SOURCE_UNIT_BYTES_MISMATCH')
        if self.format not in ('gsl','markdown-fence'):
            raise ValueError('UNKNOWN_SOURCE_UNIT_FORMAT')


@dataclass(frozen=True,slots=True)
class Extraction:
    source:SourceBundle
    units:tuple[NormativeUnit,...]
    excluded_spans:tuple[TextSpan,...]

    def __post_init__(self)->None:
        if type(self.units) is not tuple or type(self.excluded_spans) is not tuple:
            raise TypeError('invalid extraction partitions')
        if not self.units:
            raise ValueError('NO_NORMATIVE_UNITS')
        last=-1
        for unit in self.units:
            if unit.source!=self.source or unit.span.start<last:
                raise ValueError('EXTRACTED_UNITS_OVERLAP')
            last=unit.span.end
        parts=sorted([*(x.span for x in self.units),*self.excluded_spans],key=lambda x:x.start)
        at=0
        for part in parts:
            if part.start!=at:
                raise ValueError('SOURCE_EXTRACTION_NOT_LOSSLESS')
            at=part.end
        if at!=len(self.source.source_bytes):
            raise ValueError('SOURCE_EXTRACTION_NOT_LOSSLESS')


def _non_normative_gaps(source:SourceBundle, units:tuple[NormativeUnit,...])->tuple[TextSpan,...]:
    cursor=0
    pieces=[]
    for unit in units:
        if cursor<unit.span.start:
            pieces.append(TextSpan(cursor,unit.span.start))
        cursor=unit.span.end
    if cursor<len(source.source_bytes):
        pieces.append(TextSpan(cursor,len(source.source_bytes)))
    return tuple(pieces)


def extract_normative_units(bundle:SourceBundle, *, source_format:str)->Extraction:
    """Only `gsl normative [version=0.1]` Markdown fences carry declarations.

    Other fences, prose and examples remain outside the compilation input,
    but appear in the excluded spans and are never discarded from the source.
    A fence not closed with the same marker and sufficient length is rejected.
    """
    if not isinstance(bundle,SourceBundle):
        raise TypeError('expected pinned SourceBundle')
    if len(bundle.source_bytes)>MAX_BYTES:
        raise FrontendError('GSL_TEXT_RESOURCE_LIMIT',0,'source exceeds byte budget')
    if source_format=='gsl':
        if not bundle.source_bytes:
            raise FrontendError('GSL_EMPTY_UNIT',0,'raw GSL must be nonempty')
        unit=NormativeUnit(bundle,TextSpan(0,len(bundle.source_bytes)),bundle.source_bytes,'gsl')
        return Extraction(bundle,(unit,),())
    if source_format!='markdown':
        raise FrontendError('GSL_UNKNOWN_SOURCE_FORMAT',0,source_format)
    lines=bundle.source_bytes.splitlines(keepends=True)
    if not lines and bundle.source_bytes:
        lines=[bundle.source_bytes]
    units=[]
    current=None
    html_comment=False
    offset=0
    for line in lines:
        core=line.decode('utf-8').rstrip('\r\n')
        if current is None:
            # Fences inside Markdown HTML comments are not normative code.
            if html_comment:
                if '-->' in core:
                    html_comment=False
                offset+=len(line)
                continue
            if '<!--' in core:
                if '-->' not in core.split('<!--',1)[1]:
                    html_comment=True
                offset+=len(line)
                continue
            match=_FENCE.fullmatch(core)
            if match:
                marker=match.group(2)
                info=match.group(3).strip()
                parts=info.split()
                is_gsl=bool(parts) and parts[0] in ('gsl','gsl0')
                is_normative=is_gsl and 'normative' in parts[1:]
                if is_normative:
                    if parts not in ([parts[0],'normative'],[parts[0],'normative','version=0.1']):
                        raise FrontendError('GSL_INVALID_NORMATIVE_FENCE',offset,'unknown fence directives/version')
                current=(marker,offset+len(line),is_normative)
        else:
            marker,start,normative=current
            close=_CLOSER.fullmatch(core)
            if close and close.group(1)[0]==marker[0] and len(close.group(1))>=len(marker):
                if normative:
                    if offset==start:
                        raise FrontendError('GSL_EMPTY_UNIT',start,'normative GSL code block is empty')
                    units.append(NormativeUnit(bundle,TextSpan(start,offset),bundle.source_bytes[start:offset],'markdown-fence'))
                current=None
        offset+=len(line)
    if current is not None:
        raise FrontendError('GSL_UNTERMINATED_MARKDOWN_FENCE',current[1],'unclosed fenced block')
    if not units:
        raise FrontendError('GSL_NO_NORMATIVE_UNITS',0,'Markdown contains no explicitly normative GSL fences')
    result=tuple(units)
    return Extraction(bundle,result,_non_normative_gaps(bundle,result))


class TokenKind(str,Enum):
    WHITESPACE='whitespace'
    COMMENT='comment'
    NAME='name'
    STRING='string'
    NUMBER='number'
    PUNCT='punct'


@dataclass(frozen=True,slots=True)
class Token:
    kind:TokenKind
    text:str
    span:TextSpan

    def __post_init__(self)->None:
        if not isinstance(self.kind,TokenKind) or type(self.text) is not str or not self.text:
            raise TypeError('INVALID_TOKEN')
        if self.span.end-self.span.start!=len(self.text.encode('utf-8')):
            raise ValueError('TOKEN_SPAN_NOT_BYTE_EXACT')


@dataclass(frozen=True,slots=True)
class TokenStream:
    unit:NormativeUnit
    tokens:tuple[Token,...]

    def __post_init__(self)->None:
        if not isinstance(self.unit,NormativeUnit) or type(self.tokens) is not tuple or any(not isinstance(t,Token) for t in self.tokens):
            raise TypeError('invalid token stream')
        pos=self.unit.span.start
        for token in self.tokens:
            if token.span.start!=pos:
                raise ValueError('TOKEN_STREAM_NOT_CONTIGUOUS')
            pos=token.span.end
        if pos!=self.unit.span.end or self.yield_bytes()!=self.unit.raw:
            raise ValueError('TOKEN_STREAM_NOT_LOSSLESS')

    def yield_bytes(self)->bytes:
        return ''.join(t.text for t in self.tokens).encode('utf-8')


def lex_gsl(unit:NormativeUnit, *, max_tokens:int=MAX_TOKENS)->TokenStream:
    if not isinstance(unit,NormativeUnit):
        raise TypeError('expected normative GSL unit')
    if type(max_tokens) is not int or max_tokens<1:
        raise ValueError('INVALID_LEX_BUDGET')
    value=unit.raw.decode('utf-8')
    n=len(value)
    positions=[unit.span.start]
    for ch in value:
        positions.append(positions[-1]+len(ch.encode('utf-8')))
    tokens=[]
    i=0
    def add(kind:TokenKind,end:int):
        nonlocal i
        tokens.append(Token(kind,value[i:end],TextSpan(positions[i],positions[end])))
        if len(tokens)>max_tokens:
            raise FrontendError('GSL_TOKEN_RESOURCE_LIMIT',positions[i],'token count budget exceeded')
        i=end
    while i<n:
        ch=value[i]
        if ch.isspace():
            j=i+1
            while j<n and value[j].isspace():j+=1
            add(TokenKind.WHITESPACE,j)
        elif value.startswith('//',i):
            j=i+2
            while j<n and value[j] not in '\r\n':j+=1
            add(TokenKind.COMMENT,j)
        elif value.startswith('/*',i):
            j=value.find('*/',i+2)
            if j<0:
                raise FrontendError('GSL_UNTERMINATED_COMMENT',positions[i],'block comment unclosed')
            add(TokenKind.COMMENT,j+2)
        elif ch=='"':
            j=i+1
            escaped=False
            while j<n:
                c=value[j]
                if not escaped and c=='"':
                    j+=1;break
                if c in '\r\n' and not escaped:
                    raise FrontendError('GSL_UNTERMINATED_STRING',positions[i],'raw newlines not allowed in quoted literal')
                if c=='\\' and not escaped: escaped=True
                else: escaped=False
                j+=1
            else:
                raise FrontendError('GSL_UNTERMINATED_STRING',positions[i],'quoted string not closed')
            raw=value[i:j]
            try:
                decoded=json.loads(raw)
                decoded.encode('utf-8')
            except (ValueError,UnicodeEncodeError) as exc:
                raise FrontendError('GSL_INVALID_STRING_ESCAPE',positions[i],'string is not valid JSON UTF-8 literal') from exc
            add(TokenKind.STRING,j)
        elif ch in _PUNCT:
            add(TokenKind.PUNCT,i+1)
        elif ch.isascii() and (ch.isalpha() or ch=='_'):
            j=i+1
            while j<n and (value[j].isascii() and (value[j].isalnum() or value[j]=='_')):j+=1
            add(TokenKind.NAME,j)
        elif ch in '+-' or ch.isdecimal() and ch.isascii():
            m=_NUMBER.match(value,i)
            if m is None:
                raise FrontendError('GSL_INVALID_NUMBER',positions[i],'unrecognized numeric token')
            j=m.end()
            if j<n and ((value[j].isascii() and (value[j].isalnum() or value[j]=='_')) or value[j]=='.'):
                raise FrontendError('GSL_INVALID_NUMBER',positions[i],'malformed numeric suffix')
            add(TokenKind.NUMBER,j)
        else:
            raise FrontendError('GSL_UNKNOWN_TOKEN',positions[i],f'invalid character U+{ord(ch):04X}')
    return TokenStream(unit,tuple(tokens))
