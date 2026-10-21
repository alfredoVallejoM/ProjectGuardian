"""GSL0-LC03: hierarchical lossless CST and source-grounded syntactic AST.

AST is intentionally UNTYPED and NON-NORMATIVE. LC04/LC05 resolve and check;
LC06 elaborates. No parser outcome is Compiled/ratified/qualified.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, replace
from typing import TypeAlias

from guardian.domain.outcomes import Diagnostic
from guardian.spec_lang.contract import (CompileContext, CompileStatus,
    CompilationStage, SourceBundle, verify_source_context)
from .text import (Extraction, FrontendError, NormativeUnit, TextSpan,
    Token, TokenKind, TokenStream, extract_normative_units, lex_gsl)

MAX_NESTING=64
DECLARATIONS=frozenset({'source','scope','objective','capability','property','obligation','verification','relation'})
_OPEN={'{':'}','(' :')','[':']'}
_CLOSE={v:k for k,v in _OPEN.items()}


@dataclass(frozen=True,slots=True)
class CSTGroup:
    """Opening/closing delimiters owned by this node; all trivia retained."""
    opener:Token|None
    children:tuple['CSTItem',...]
    closer:Token|None
    span:TextSpan

    def __post_init__(self)->None:
        if type(self.children) is not tuple or not isinstance(self.span,TextSpan):
            raise TypeError('INVALID_CST_GROUP')
        if (self.opener is None)!=(self.closer is None):
            raise ValueError('UNBALANCED_CST_NODE')
        if self.opener is not None and (self.opener.kind is not TokenKind.PUNCT
                or self.closer.kind is not TokenKind.PUNCT
                or _OPEN.get(self.opener.text)!=self.closer.text):
            raise ValueError('CST_DELIMITER_KIND_MISMATCH')
        parts=[self.opener] if self.opener is not None else []
        parts.extend(self.children)
        if self.closer is not None:parts.append(self.closer)
        offset=self.span.start
        for part in parts:
            if not isinstance(part,(Token,CSTGroup)) or part.span.start!=offset:
                raise ValueError('CST_CHILD_SPAN_GAP_OR_WRONG_TYPE')
            offset=part.span.end
        if offset!=self.span.end:
            raise ValueError('CST_GROUP_SPAN_MISMATCH')

    def yield_bytes(self)->bytes:
        parts=[]
        if self.opener is not None: parts.append(self.opener.text)
        for item in self.children:
            parts.append(item.text if isinstance(item,Token) else item.yield_bytes().decode('utf-8'))
        if self.closer is not None:parts.append(self.closer.text)
        return ''.join(parts).encode('utf-8')


CSTItem:TypeAlias=Token|CSTGroup


def build_cst(stream:TokenStream,*,max_nesting:int=MAX_NESTING)->CSTGroup:
    if not isinstance(stream,TokenStream) or type(max_nesting) is not int or max_nesting<1:
        raise TypeError('CST requires typed stream and positive budget')
    # Builder is stack-driven, so malicious nesting does not trigger Python recursion.
    frames:list[tuple[Token|None,list[CSTItem]]]=[(None,[])]
    for token in stream.tokens:
        if token.kind is TokenKind.PUNCT and token.text in _OPEN:
            if len(frames)>max_nesting:
                raise FrontendError('GSL_CST_DEPTH_LIMIT',token.span.start,'group nesting over budget')
            frames.append((token,[]))
        elif token.kind is TokenKind.PUNCT and token.text in _CLOSE:
            if len(frames)==1 or _OPEN[frames[-1][0].text]!=token.text:
                raise FrontendError('GSL_UNBALANCED_DELIMITER',token.span.start,'unexpected closing delimiter')
            opening,children=frames.pop()
            frames[-1][1].append(CSTGroup(opening,tuple(children),token,TextSpan(opening.span.start,token.span.end)))
        else:
            frames[-1][1].append(token)
    if len(frames)>1:
        opening=frames[-1][0]
        raise FrontendError('GSL_UNBALANCED_DELIMITER',opening.span.start,'unclosed group')
    root=CSTGroup(None,tuple(frames[0][1]),None,stream.unit.span)
    if root.yield_bytes()!=stream.unit.raw:
        raise FrontendError('GSL_CST_NOT_LOSSLESS',stream.unit.span.start,'CST yield differs from source')
    return root


@dataclass(frozen=True,slots=True)
class Expr:
    tag:str
    span:TextSpan
    value:str|int|bool|None=None
    args:tuple['Expr',...]=()

    def __post_init__(self)->None:
        if self.tag not in ('name','string','number','bool','call','not','and','or'):
            raise ValueError('UNKNOWN_SYNTAX_EXPR')
        if not isinstance(self.span,TextSpan) or type(self.args) is not tuple:
            raise TypeError('invalid expression AST')


@dataclass(frozen=True,slots=True)
class ParsedField:
    name:str
    expr:Expr
    span:TextSpan

    def __post_init__(self)->None:
        if type(self.name) is not str or not self.name.isidentifier() or not isinstance(self.expr,Expr) or not isinstance(self.span,TextSpan):
            raise TypeError('INVALID_PARSED_FIELD')
        if self.expr.span.start<self.span.start or self.expr.span.end>self.span.end:
            raise ValueError('PARSED_FIELD_ORIGIN_MISMATCH')


@dataclass(frozen=True,slots=True)
class ParsedDeclaration:
    kind:str
    name:str
    fields:tuple[ParsedField,...]
    span:TextSpan

    def __post_init__(self)->None:
        if self.kind not in DECLARATIONS or type(self.name) is not str or not isinstance(self.fields,tuple) or not isinstance(self.span,TextSpan):
            raise ValueError('INVALID_PARSED_DECLARATION')
        if any(not isinstance(f,ParsedField) or f.span.start<self.span.start or f.span.end>self.span.end for f in self.fields):
            raise ValueError('PARSED_DECLARATION_FIELD_ORIGIN_MISMATCH')


@dataclass(frozen=True,slots=True)
class ParsedModule:
    version:str
    project:str
    declarations:tuple[ParsedDeclaration,...]
    span:TextSpan
    source:NormativeUnit

    def __post_init__(self)->None:
        if self.version!='0.1' or type(self.project) is not str or not self.project or not isinstance(self.source,NormativeUnit):
            raise ValueError('INVALID_PARSED_MODULE_HEADER')
        if self.span!=self.source.span or type(self.declarations) is not tuple:
            raise ValueError('INVALID_PARSED_MODULE_ORIGIN')
        if any(not isinstance(d,ParsedDeclaration) or d.span.start<self.span.start or d.span.end>self.span.end for d in self.declarations):
            raise ValueError('PARSED_MODULE_DECLARATION_ORIGIN_MISMATCH')


class _Parser:
    def __init__(self,stream:TokenStream):
        self.stream=stream
        self.tokens=[token for token in stream.tokens if token.kind not in (TokenKind.WHITESPACE,TokenKind.COMMENT)]
        self.idx=0

    def at(self,raw:str)->bool:
        return self.idx<len(self.tokens) and self.tokens[self.idx].text==raw

    def _token(self)->Token:
        if self.idx>=len(self.tokens):
            raise FrontendError('GSL_PARSE_UNEXPECTED_EOF',self.stream.unit.span.end,'unexpected end of GSL source')
        return self.tokens[self.idx]

    def take(self,raw:str|None=None,kind:TokenKind|None=None)->Token:
        tok=self._token()
        if (raw is not None and tok.text!=raw) or (kind is not None and tok.kind is not kind):
            raise FrontendError('GSL_PARSE_EXPECTED_TOKEN',tok.span.start,f'expected {raw or kind.value}; saw {tok.text!r}')
        self.idx+=1
        return tok

    def expression(self,depth:int=0)->Expr:
        if depth>MAX_NESTING:
            raise FrontendError('GSL_AST_DEPTH_LIMIT',self._token().span.start,'AST expression exceeds depth budget')
        return self._or(depth)

    def _or(self,depth:int)->Expr:
        items=[self._and(depth)]
        while self.at('or'):
            self.take('or')
            items.append(self._and(depth))
        return (Expr('or',TextSpan(items[0].span.start,items[-1].span.end),args=tuple(items))
                if len(items)>1 else items[0])

    def _and(self,depth:int)->Expr:
        items=[self._not(depth)]
        while self.at('and'):
            self.take('and')
            items.append(self._not(depth))
        return (Expr('and',TextSpan(items[0].span.start,items[-1].span.end),args=tuple(items))
                if len(items)>1 else items[0])

    def _not(self,depth:int)->Expr:
        if depth>MAX_NESTING:
            raise FrontendError('GSL_AST_DEPTH_LIMIT',self._token().span.start,'AST expression exceeds depth budget')
        if self.at('not'):
            start=self.take('not')
            child=self._not(depth+1)
            return Expr('not',TextSpan(start.span.start,child.span.end),args=(child,))
        return self._atom(depth)

    def _atom(self,depth:int)->Expr:
        if depth>MAX_NESTING:
            raise FrontendError('GSL_AST_DEPTH_LIMIT',self._token().span.start,'AST expression exceeds depth budget')
        tok=self._token()
        if self.at('('):
            opening=self.take('(');value=self.expression(depth+1);closing=self.take(')')
            return replace(value,span=TextSpan(opening.span.start,closing.span.end))
        if tok.kind is TokenKind.STRING:
            self.idx+=1
            return Expr('string',tok.span,json.loads(tok.text))
        if tok.kind is TokenKind.NUMBER:
            self.idx+=1
            # Preserve signed/exponential decimal lexeme; LC05 owns numeric typing.
            return Expr('number',tok.span,tok.text)
        if tok.kind is TokenKind.NAME:
            self.idx+=1
            if tok.text in ('true','false'):
                return Expr('bool',tok.span,tok.text=='true')
            if self.at('('):
                self.take('(');args=[]
                if not self.at(')'):
                    while True:
                        args.append(self.expression(depth+1))
                        if not self.at(','):break
                        self.take(',')
                end=self.take(')')
                return Expr('call',TextSpan(tok.span.start,end.span.end),tok.text,tuple(args))
            if tok.text in ('and','or','not'):
                raise FrontendError('GSL_RESERVED_EXPRESSION',tok.span.start,'operator is not standalone expression')
            return Expr('name',tok.span,tok.text)
        raise FrontendError('GSL_PARSE_INVALID_EXPRESSION',tok.span.start,'expected literal, reference, call or grouped expression')

    def parse(self)->ParsedModule:
        start=self.take('gsl')
        version=json.loads(self.take(kind=TokenKind.STRING).text)
        self.take(';');self.take('project')
        project=json.loads(self.take(kind=TokenKind.STRING).text)
        self.take(';')
        declarations=[]
        while self.idx<len(self.tokens):
            kind=self.take(kind=TokenKind.NAME)
            if kind.text not in DECLARATIONS:
                raise FrontendError('GSL_UNKNOWN_DECLARATION',kind.span.start,f'unsupported declaration {kind.text}')
            name=json.loads(self.take(kind=TokenKind.STRING).text)
            self.take('{')
            fields=[]
            while not self.at('}'):
                key=self.take(kind=TokenKind.NAME)
                self.take(':')
                value=self.expression()
                end=self.take(';')
                fields.append(ParsedField(key.text,value,TextSpan(key.span.start,end.span.end)))
            end=self.take('}')
            declarations.append(ParsedDeclaration(kind.text,name,tuple(fields),TextSpan(kind.span.start,end.span.end)))
        if version!='0.1':
            raise FrontendError('GSL_VERSION_UNSUPPORTED',start.span.start,'unrecognized source language version')
        if type(project) is not str or not project:
            raise FrontendError('GSL_PROJECT_MISSING',start.span.start,'project header needs name')
        return ParsedModule(version,project,tuple(declarations),self.stream.unit.span,self.stream.unit)


def parse_gsl(stream:TokenStream)->ParsedModule:
    if not isinstance(stream,TokenStream):
        raise TypeError('parser accepts lossless TokenStream only')
    return _Parser(stream).parse()


@dataclass(frozen=True,slots=True)
class AnalyzedUnit:
    token_stream:TokenStream
    cst:CSTGroup
    ast:ParsedModule


@dataclass(frozen=True,slots=True)
class FrontendAnalysis:
    status:CompileStatus
    stage:CompilationStage
    units:tuple[AnalyzedUnit,...]
    diagnostics:tuple[Diagnostic,...]
    extraction:Extraction|None=None

    def __post_init__(self)->None:
        if self.status not in (CompileStatus.ANALYZED,CompileStatus.REJECTED):
            raise ValueError('LC03_FRONTEND_CANNOT_COMPILE')
        if not isinstance(self.stage,CompilationStage) or type(self.units) is not tuple or type(self.diagnostics) is not tuple:
            raise TypeError('LC03_FRONTEND_UNTYPED_RESULT')
        if any(not isinstance(u,AnalyzedUnit) for u in self.units) or any(not isinstance(d,Diagnostic) for d in self.diagnostics):
            raise TypeError('LC03_FRONTEND_UNTYPED_CONTENT')
        if self.status is CompileStatus.ANALYZED and (self.stage is not CompilationStage.ABSTRACT or self.diagnostics or not self.units or not isinstance(self.extraction,Extraction)):
            raise ValueError('LC03_ANALYZED_REQUIRES_FULL_SYNTAX')
        if self.status is CompileStatus.REJECTED and not self.diagnostics:
            raise ValueError('LC03_REJECTION_REQUIRES_DIAGNOSTICS')

    @property
    def ok(self)->bool:
        return self.status is CompileStatus.ANALYZED and not self.diagnostics


def analyze_source(bundle:SourceBundle,context:CompileContext,*,source_format:str)->FrontendAnalysis:
    """Strict C01..C05 pipeline. Never emits COMPILED before LC04–LC08."""
    pinned=verify_source_context(bundle,context)
    if not pinned.ok:
        return FrontendAnalysis(CompileStatus.REJECTED,CompilationStage.ACQUIRE,(),pinned.diagnostics)
    extraction=None
    analyzed=[]
    stage=CompilationStage.EXTRACT
    try:
        extraction=extract_normative_units(bundle,source_format=source_format)
        for unit in extraction.units:
            stage=CompilationStage.LEX
            stream=lex_gsl(unit)
            stage=CompilationStage.PARSE
            cst=build_cst(stream)
            stage=CompilationStage.ABSTRACT
            ast=parse_gsl(stream)
            if ast.project!=context.project.value:
                raise FrontendError('GSL_FOREIGN_PROJECT',ast.span.start,'source declares a different project')
            analyzed.append(AnalyzedUnit(stream,cst,ast))
        return FrontendAnalysis(CompileStatus.ANALYZED,CompilationStage.ABSTRACT,tuple(analyzed),(),extraction)
    except FrontendError as exc:
        return FrontendAnalysis(CompileStatus.REJECTED,stage,tuple(analyzed),
            (Diagnostic(exc.code,f'$.source.byte[{exc.byte_start}]','valid GSL syntax','invalid',exc.message),),extraction)
