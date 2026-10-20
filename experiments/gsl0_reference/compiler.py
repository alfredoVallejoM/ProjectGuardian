"""An executable *candidate reference slice* of GSL-0; not Guardian's normative compiler.

The compiler is deliberately pure and produces no approvals, implementation verdicts,
or material evidence. It is an experiment for validating the proposed language contract.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping
import json

from lark import Lark, Token, Transformer, UnexpectedInput, v_args

GRAMMAR = (Path(__file__).with_name("grammar.lark")).read_text(encoding="utf-8")
_PARSER = Lark(GRAMMAR, parser="lalr", propagate_positions=True)
KINDS = {"existence", "behavior", "constitution", "execution", "development", "integration", "migration"}
SCHEMAS = {
    "source": ({"locator", "source_cut"}, {"locator", "source_cut"}),
    "scope": ({"project", "campaign"}, {"project"}),
    "objective": ({"from", "scope"}, {"from", "scope"}),
    "capability": ({"from", "scope"}, {"from", "scope"}),
    "property": ({"from", "kind", "subject", "holds", "deferred_semantics"}, {"kind", "subject"}),
    "obligation": ({"from", "kind", "scope", "when", "requires", "verification"}, {"from", "kind", "scope", "when", "requires"}),
    "verification": ({"from", "target", "property", "method"}, {"from", "target", "property", "method"}),
    "relation": ({"kind", "parent", "child"}, {"kind", "parent", "child"}),
}
REPEATED_FIELDS = {"requires", "verification"}
REF_TYPES = {"project":"project", "scope":"scope", "property":"property", "obligation":"obligation", "objective":"objective", "capability":"capability", "verification_ref":"verification", "clause":"clause"}
PREDICATES = {"nominal_distinct": ("IdentityKind", "IdentityKind")}
VERIFICATION_METHODS = {"property_and_negative", "structural_negative", "finite_exhaustive"}
RELATION_SIGNATURES = {"proposed_detail": ("obligation", "clause")}


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    line: int
    column: int


@dataclass(frozen=True)
class Expr:
    tag: str
    value: Any
    span: Span


@dataclass(frozen=True)
class Decl:
    kind: str
    id: str
    fields: tuple[tuple[str, Expr], ...]
    span: Span


@dataclass(frozen=True)
class Module:
    version: str
    project: str
    declarations: tuple[Decl, ...]


@dataclass(frozen=True)
class Diagnostic:
    code: str
    subject: str
    explanation: str


@dataclass(frozen=True)
class SourceRecord:
    locator: str
    logical_items: frozenset[str]


@dataclass(frozen=True)
class CompileContext:
    project: str
    source_cut: str
    sources: Mapping[str, SourceRecord]
    required_source_items: Mapping[str, frozenset[str]] | None = None
    required_relation_ids: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Compilation:
    status: str
    diagnostics: tuple[Diagnostic, ...]
    ir: dict[str, Any] | None
    source_map: dict[str, Any] | None
    manifest: dict[str, Any] | None
    proof_obligations: tuple[dict[str, Any], ...] = ()


def _json_string(value: Token) -> str:
    return json.loads(str(value))


class _ASTBuilder(Transformer):
    def __init__(self, source: str):
        super().__init__()
        self._prefix = [0]
        for c in source:
            self._prefix.append(self._prefix[-1] + len(c.encode("utf-8")))

    def _span(self, meta) -> Span:
        return Span(self._prefix[meta.start_pos],self._prefix[meta.end_pos],meta.line,meta.column)

    def version(self, x):
        return _json_string(x[0])

    def project_decl(self,x):
        return _json_string(x[0])

    def start(self,x):
        return Module(x[0],x[1],tuple(x[2:]))

    @v_args(meta=True)
    def field(self,meta,x):
        return (str(x[0]), x[1])

    def _decl(self,kind,meta,x):
        return Decl(kind,_json_string(x[0]),tuple(x[1:]),self._span(meta))

    @v_args(meta=True)
    def source_decl(self,meta,x):return self._decl("source",meta,x)
    @v_args(meta=True)
    def scope_decl(self,meta,x):return self._decl("scope",meta,x)
    @v_args(meta=True)
    def objective_decl(self,meta,x):return self._decl("objective",meta,x)
    @v_args(meta=True)
    def capability_decl(self,meta,x):return self._decl("capability",meta,x)
    @v_args(meta=True)
    def property_decl(self,meta,x):return self._decl("property",meta,x)
    @v_args(meta=True)
    def obligation_decl(self,meta,x):return self._decl("obligation",meta,x)
    @v_args(meta=True)
    def verification_decl(self,meta,x):return self._decl("verification",meta,x)
    @v_args(meta=True)
    def relation_decl(self,meta,x):return self._decl("relation",meta,x)

    @v_args(meta=True)
    def string(self,meta,x):return Expr("string",_json_string(x[0]),self._span(meta))
    @v_args(meta=True)
    def number(self,meta,x):return Expr("number",str(x[0]),self._span(meta))
    @v_args(meta=True)
    def name(self,meta,x):return Expr("name",str(x[0]),self._span(meta))
    @v_args(meta=True)
    def true(self,meta,x):return Expr("boolean",True,self._span(meta))
    @v_args(meta=True)
    def false(self,meta,x):return Expr("boolean",False,self._span(meta))
    @v_args(meta=True)
    def call(self,meta,x):return Expr("call",(str(x[0]),tuple(x[1:])),self._span(meta))
    @v_args(meta=True)
    def negative(self,meta,x):return Expr("not",x[0],self._span(meta))
    @v_args(meta=True)
    def conjunction(self,meta,x):return x[0] if len(x)==1 else Expr("and",tuple(x),self._span(meta))
    @v_args(meta=True)
    def disjunction(self,meta,x):return x[0] if len(x)==1 else Expr("or",tuple(x),self._span(meta))


def parse(text:str) -> Module:
    return _ASTBuilder(text).transform(_PARSER.parse(text))


def _field(d:Decl,key:str) -> Expr:
    for k,e in d.fields:
        if k==key:return e
    raise KeyError(key)


def _issue(out:list[Diagnostic],code:str,d:Decl,explanation:str) -> None:
    out.append(Diagnostic(code,f"{d.kind}:{d.id}",explanation))


def _check_schema(d:Decl,out:list[Diagnostic]) -> None:
    allowed,required=SCHEMAS[d.kind]
    counts=Counter(k for k,_ in d.fields)
    for key in counts:
        if key not in allowed:_issue(out,"GSL-FIELD-UNKNOWN",d,key)
        if counts[key]>1 and key not in REPEATED_FIELDS:_issue(out,"GSL-FIELD-DUPLICATE",d,key)
    for key in sorted(required-counts.keys()):_issue(out,"GSL-FIELD-MISSING",d,key)
    if d.kind=="property":
        has_holds="holds" in counts
        has_deferred="deferred_semantics" in counts
        if has_holds==has_deferred:_issue(out,"GSL-PROPERTY-SEMANTICS",d,"exactly one of holds/deferred_semantics is required")


def _is_call(e:Expr,name:str | None=None,arity:int | None=None) -> bool:
    if e.tag!="call":return False
    n,args=e.value
    return (name is None or n==name) and (arity is None or len(args)==arity)


def _is_atom(e:Expr,tag:str) -> bool:return e.tag==tag


def _validate_expr(e:Expr, symbols:set[tuple[str,str]], source_items:Mapping[str,SourceRecord], d:Decl, errors:list[Diagnostic], expected:str) -> None:
    """Small typed subset; unsupported predicates and terms are rejected, not guessed."""
    if expected=="string":
        if e.tag!="string":_issue(errors,"GSL-TYPE",d,"expected string")
    elif expected=="name":
        if e.tag!="name":_issue(errors,"GSL-TYPE",d,"expected enum name")
    elif expected=="application":
        _validate_expr(e,symbols,source_items,d,errors,"formula")
    elif expected=="formula":
        if e.tag=="boolean":return
        if e.tag=="not":return _validate_expr(e.value,symbols,source_items,d,errors,"formula")
        if e.tag in ("and","or"):
            for x in e.value:_validate_expr(x,symbols,source_items,d,errors,"formula")
            return
        if e.tag=="call" and e.value[0] in PREDICATES:
            name,args=e.value
            specs=PREDICATES[name]
            if len(args)!=len(specs):_issue(errors,"GSL-PRED-ARITY",d,name)
            for x,t in zip(args,specs):
                if not _is_call(x,"kind",1) or x.value[1][0].tag!="string":_issue(errors,"GSL-PRED-TYPE",d,f"{name} expects IdentityKind")
            return
        _issue(errors,"GSL-PRED-UNSUPPORTED",d,f"unsupported predicate: {e.value if e.tag=='call' else e.tag}")
    elif expected.startswith("ref:"):
        kind=expected.split(":",1)[1]
        allowed_names=[name for name, v in REF_TYPES.items() if v==kind]
        if not e.tag=="call" or e.value[0] not in allowed_names or len(e.value[1])!=1 or e.value[1][0].tag!="string":
            _issue(errors,"GSL-TYPE",d,f"expected Ref<{kind}>")
        elif kind=="project" and (kind, e.value[1][0].value) not in symbols:
            _issue(errors,"GSL-FOREIGN-PROJECT",d,e.value[1][0].value)
        elif kind!="project" and (kind, e.value[1][0].value) not in symbols:
            if kind=="clause" and any(e.value[1][0].value in source.logical_items for source in source_items.values()):return
            _issue(errors,"GSL-REF-MISSING",d,f"{kind}:{e.value[1][0].value}")
    elif expected=="source_item":
        if not _is_call(e,"source_item",2) or any(a.tag!="string" for a in e.value[1]):
            _issue(errors,"GSL-TYPE",d,"source_item requires two strings")
        else:
            source,item=(a.value for a in e.value[1])
            if source not in source_items or item not in source_items[source].logical_items:
                _issue(errors,"GSL-SOURCE-ITEM-MISSING",d,f"{source}#{item}")


def _value_to_ir(e:Expr,project:str) -> Any:
    if e.tag in ("boolean","number","string","name"):
        return {"op":e.tag,"value":e.value}
    if e.tag=="call":
        name,args=e.value
        if name in REF_TYPES and len(args)==1 and args[0].tag=="string":
            return {"op":"resolved_ref","project":project,"kind":REF_TYPES[name],"id":args[0].value}
        if name=="source_item" and len(args)==2 and all(a.tag=="string" for a in args):
            return {"op":"source_item_ref","source":args[0].value,"item":args[1].value}
        if name=="kind" and len(args)==1 and args[0].tag=="string":
            return {"op":"identity_kind","id":args[0].value}
        if name in PREDICATES:
            return {"op":"interpreted_predicate","name":name,"signature":"candidate-0.1","args":[_value_to_ir(x,project) for x in args]}
        raise ValueError(f"cannot lower unknown semantic call {name}")
    if e.tag=="not":return {"op":"not","arg":_value_to_ir(e.value,project)}
    if e.tag in ("and","or"):
        return {"op":e.tag,"args":[_value_to_ir(x,project) for x in e.value]}
    raise ValueError(e.tag)


def canonical_bytes(value:Any) -> bytes:
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode("utf-8")


def compile_strict(text:str,ctx:CompileContext) -> Compilation:
    try:
        module=parse(text)
    except UnexpectedInput as exc:
        return Compilation("REJECTED",(Diagnostic("GSL-PARSE","document",f"line {exc.line}, column {exc.column}"),),None,None,None)
    if module.version!="0.1":
        return Compilation("REJECTED",(Diagnostic("GSL-VERSION","document",module.version),),None,None,None)
    if not ctx.source_cut or not ctx.project:
        return Compilation("REJECTED",(Diagnostic("GSL-CONTEXT","document","project/source cut must be pinned"),),None,None,None)
    if module.project!=ctx.project:
        return Compilation("REJECTED",(Diagnostic("GSL-PROJECT","document",module.project),),None,None,None)
    errors:list[Diagnostic]=[]
    symbols:set[tuple[str,str]]={(d.kind,d.id) for d in module.declarations}
    symbols.add(("project",ctx.project))
    counts=Counter((d.kind,d.id) for d in module.declarations)
    for d in module.declarations:
        if counts[(d.kind,d.id)]>1:_issue(errors,"GSL-ID-DUPLICATE",d,d.id)
        _check_schema(d,errors)
    declared_sources={d.id:ctx.sources[d.id] for d in module.declarations if d.kind=="source" and d.id in ctx.sources}
    for d in module.declarations:
        fs=dict(d.fields)
        if any(f not in fs for f in SCHEMAS[d.kind][1]):continue
        if d.kind=="source":
            _validate_expr(fs["locator"],symbols,declared_sources,d,errors,"string")
            if d.id not in ctx.sources:_issue(errors,"GSL-SOURCE-UNKNOWN",d,d.id)
            elif fs["locator"].tag=="string" and fs["locator"].value!=ctx.sources[d.id].locator:_issue(errors,"GSL-SOURCE-LOCATOR",d,d.id)
            if not (fs["source_cut"].tag=="name" and fs["source_cut"].value=="context"):_issue(errors,"GSL-SOURCE-CUT",d,"use pinned context")
        elif d.kind=="scope":
            _validate_expr(fs["project"],symbols,declared_sources,d,errors,"ref:project")
            if _is_call(fs["project"],"project",1) and fs["project"].value[1][0].tag=="string" and fs["project"].value[1][0].value!=ctx.project:_issue(errors,"GSL-FOREIGN-PROJECT",d,"cross-project scope not admitted")
            if "campaign" in fs:_validate_expr(fs["campaign"],symbols,declared_sources,d,errors,"string")
        elif d.kind in ("objective","capability"):
            _validate_expr(fs["from"],symbols,declared_sources,d,errors,"source_item")
            _validate_expr(fs["scope"],symbols,declared_sources,d,errors,"ref:scope")
        elif d.kind=="property":
            if "from" in fs: _validate_expr(fs["from"],symbols,declared_sources,d,errors,"source_item")
            _validate_expr(fs["kind"],symbols,declared_sources,d,errors,"name")
            if fs["kind"].tag=="name" and fs["kind"].value not in KINDS:_issue(errors,"GSL-KIND",d,fs["kind"].value)
            _validate_expr(fs["subject"],symbols,declared_sources,d,errors,"ref:project")
            if "holds" in fs:_validate_expr(fs["holds"],symbols,declared_sources,d,errors,"formula")
            if "deferred_semantics" in fs:_validate_expr(fs["deferred_semantics"],symbols,declared_sources,d,errors,"string")
        elif d.kind=="obligation":
            _validate_expr(fs["from"],symbols,declared_sources,d,errors,"source_item")
            _validate_expr(fs["kind"],symbols,declared_sources,d,errors,"name")
            if fs["kind"].tag=="name" and fs["kind"].value not in KINDS:_issue(errors,"GSL-KIND",d,fs["kind"].value)
            _validate_expr(fs["scope"],symbols,declared_sources,d,errors,"ref:scope")
            _validate_expr(fs["when"],symbols,declared_sources,d,errors,"application")
            for key,value in d.fields:
                if key=="requires":_validate_expr(value,symbols,declared_sources,d,errors,"ref:property")
                if key=="verification":_validate_expr(value,symbols,declared_sources,d,errors,"ref:verification")
        elif d.kind=="verification":
            _validate_expr(fs["from"],symbols,declared_sources,d,errors,"source_item")
            _validate_expr(fs["target"],symbols,declared_sources,d,errors,"ref:obligation")
            _validate_expr(fs["property"],symbols,declared_sources,d,errors,"ref:property")
            _validate_expr(fs["method"],symbols,declared_sources,d,errors,"name")
            if fs["method"].tag=="name" and fs["method"].value not in VERIFICATION_METHODS:
                _issue(errors,"GSL-METHOD-UNKNOWN",d,fs["method"].value)
        elif d.kind=="relation":
            _validate_expr(fs["kind"],symbols,declared_sources,d,errors,"name")
            if fs["kind"].tag=="name" and fs["kind"].value not in RELATION_SIGNATURES:
                _issue(errors,"GSL-RELATION-UNKNOWN",d,fs["kind"].value)
            _validate_expr(fs["parent"],symbols,declared_sources,d,errors,"ref:obligation")
            _validate_expr(fs["child"],symbols,declared_sources,d,errors,"ref:clause")
    if ctx.required_source_items is not None:
        represented: set[tuple[str,str]] = set()
        for d in module.declarations:
            for field,value in d.fields:
                if field=="from" and _is_call(value,"source_item",2) and all(a.tag=="string" for a in value.value[1]):
                    represented.add(tuple(a.value for a in value.value[1]))
        for source, required_items in ctx.required_source_items.items():
            for item in sorted(required_items):
                if (source,item) not in represented:
                    errors.append(Diagnostic("GSL-COVERAGE-MISSING",source,item))
    for required_id in sorted(ctx.required_relation_ids):
        if ("relation",required_id) not in symbols:
            errors.append(Diagnostic("GSL-RELATION-COVERAGE-MISSING","relation",required_id))
    if errors:return Compilation("REJECTED",tuple(errors),None,None,None)
    declarations=[{"node_type":d.kind,"id":d.id,"fields":[{"name":k,"value":_value_to_ir(v,ctx.project)} for k,v in d.fields]} for d in module.declarations]
    ir={"schema":"guardian/gsl0/reference-0.1","project":ctx.project,"declarations":declarations}
    source_map={f"{d.kind}:{d.id}":{"byte_start":d.span.start,"byte_end":d.span.end,"line":d.span.line,"column":d.span.column} for d in module.declarations}
    contract_digest=sha256(canonical_bytes(ir)).hexdigest()
    manifest={"source_cut":ctx.source_cut,"source_digest":sha256(text.encode("utf-8")).hexdigest(),"contract_digest":contract_digest,"language":"0.1","status":"PROPOSED_NOT_RATIFIED"}
    proof_obligations=[]
    for d in module.declarations:
        if d.kind=="property" and any(k=="deferred_semantics" for k,_ in d.fields):
            proof_obligations.append({"kind":"PROPERTY_INTERPRETATION_PENDING","property_id":d.id,"status":"UNPROVEN"})
        if d.kind=="relation" and _field(d,"kind").tag=="name" and _field(d,"kind").value=="proposed_detail":
            proof_obligations.append({"kind":"REFINEMENT_SUFFICIENCY_PENDING","relation_id":d.id,"status":"UNPROVEN"})
    return Compilation("COMPILED",(),ir,source_map,manifest,tuple(proof_obligations))
