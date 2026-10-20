"""GSL0-LC02: finite V4 source-semantics oracle and independent IR VM.

The minimal source grammar here is a *verification fragment*, not the future
GSL grammar (LC03). Its lexer sees source bytes independently of any candidate
IR or its self-computed hashes. No Python eval, callbacks or project I/O.
"""
from __future__ import annotations

import itertools
import re
from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from guardian.domain.evidence_logic import FourValued, UNKNOWN, YES, NO, CONFLICT
from guardian.domain.identity import EntityRef
from guardian.spec_lang.contract import SourceBundle, CompileContext, verify_source_context
from guardian.spec_lang.ir import FormulaIR, SourceOrigin

_SOURCE_TOKEN = re.compile(r'[A-Za-z_][A-Za-z_0-9]*|\(|\)|\S')
_KEYWORDS = {'not','and','or','yes','no','unknown','conflict'}
_MAX_PARSE_DEPTH = 64


class SourceFormula:
    """Typed source-language formula node; deliberately distinct from FormulaIR."""


@dataclass(frozen=True, slots=True)
class SourceConstant(SourceFormula):
    value: str
    def __post_init__(self):
        if self.value not in ('yes','no','unknown','conflict'):
            raise ValueError('invalid V4 source constant')


@dataclass(frozen=True, slots=True)
class SourceAtom(SourceFormula):
    name: str
    def __post_init__(self):
        if not isinstance(self.name,str) or not self.name or self.name in _KEYWORDS or self.name[0].isdigit():
            raise ValueError('invalid source atom')


@dataclass(frozen=True, slots=True)
class SourceNot(SourceFormula):
    inner: SourceFormula


@dataclass(frozen=True, slots=True)
class SourceAnd(SourceFormula):
    left: SourceFormula
    right: SourceFormula


@dataclass(frozen=True, slots=True)
class SourceOr(SourceFormula):
    left: SourceFormula
    right: SourceFormula


class _SourceParser:
    def __init__(self,raw:str):
        self.tokens=[m.group(0) for m in _SOURCE_TOKEN.finditer(raw)]
        self.i=0
        if not self.tokens:
            raise ValueError('GSL_V0_EMPTY_SOURCE_FORMULA')

    def take(self,expected:str|None=None)->str:
        if self.i >= len(self.tokens):
            raise ValueError('GSL_V0_UNEXPECTED_END')
        token=self.tokens[self.i]
        if expected is not None and token!=expected:
            raise ValueError(f'GSL_V0_EXPECTED_{expected}')
        self.i+=1
        return token

    def peek(self)->str|None:
        return self.tokens[self.i] if self.i<len(self.tokens) else None

    def parse(self)->SourceFormula:
        f=self.disj(0)
        if self.i != len(self.tokens):
            raise ValueError('GSL_V0_TRAILING_TOKENS')
        return f

    def disj(self,depth:int)->SourceFormula:
        lhs=self.conj(depth+1)
        while self.peek()=='or':
            self.take('or')
            lhs=SourceOr(lhs,self.conj(depth+1))
        return lhs

    def conj(self,depth:int)->SourceFormula:
        lhs=self.neg(depth+1)
        while self.peek()=='and':
            self.take('and')
            lhs=SourceAnd(lhs,self.neg(depth+1))
        return lhs

    def neg(self,depth:int)->SourceFormula:
        if depth>_MAX_PARSE_DEPTH:
            raise ValueError('GSL_V0_MAX_DEPTH')
        tok=self.peek()
        if tok=='not':
            self.take('not')
            return SourceNot(self.neg(depth+1))
        if tok=='(':
            self.take('(')
            node=self.disj(depth+1)
            self.take(')')
            return node
        value=self.take()
        if value in ('yes','no','unknown','conflict'):
            return SourceConstant(value)
        if value in _KEYWORDS or re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',value) is None:
            raise ValueError('GSL_V0_UNEXPECTED_TOKEN')
        return SourceAtom(value)


def parse_source_formula(raw:bytes)->SourceFormula:
    if not isinstance(raw,bytes):
        raise TypeError('source formula requires raw UTF-8 bytes')
    return _SourceParser(raw.decode('utf-8','strict')).parse()


def lower_formula(source:SourceFormula)->FormulaIR:
    """Candidate translator; oracle must NOT derive expected results from this."""
    if isinstance(source,SourceAtom):
        return FormulaIR('atom',name=source.name)
    if isinstance(source,SourceConstant):
        return FormulaIR(source.value)
    if isinstance(source,SourceNot):
        return FormulaIR('not',(lower_formula(source.inner),))
    if isinstance(source,SourceAnd):
        return FormulaIR('and',(lower_formula(source.left),lower_formula(source.right)))
    if isinstance(source,SourceOr):
        return FormulaIR('or',(lower_formula(source.left),lower_formula(source.right)))
    raise TypeError('unknown source formula type')


def _source_eval(f:SourceFormula,valuation:Mapping[str,tuple[bool,bool]])->tuple[bool,bool]:
    """Independent source interpreter using primitive tuple bits."""
    if isinstance(f,SourceConstant):
        return {'yes':(True,False),'no':(False,True),'unknown':(False,False),'conflict':(True,True)}[f.value]
    if isinstance(f,SourceAtom):
        if f.name not in valuation:
            raise ValueError('GSL_V0_MISSING_ATOM')
        return valuation[f.name]
    if isinstance(f,SourceNot):
        a,b=_source_eval(f.inner,valuation)
        return (b,a)
    if isinstance(f,SourceAnd):
        a,b=_source_eval(f.left,valuation)
        c,d=_source_eval(f.right,valuation)
        return (a and c,b or d)
    if isinstance(f,SourceOr):
        a,b=_source_eval(f.left,valuation)
        c,d=_source_eval(f.right,valuation)
        return (a or c,b and d)
    raise TypeError('unknown source formula')


def _ir_instructions(ir:FormulaIR)->list[tuple[str,str|None]]:
    """Build a postfix VM program without consulting source evaluator."""
    instructions=[]
    def walk(f:FormulaIR,depth:int=0):
        if depth>_MAX_PARSE_DEPTH:
            raise ValueError('GSL_IR_MAX_DEPTH')
        for arg in f.args:
            walk(arg,depth+1)
        instructions.append((f.op,f.name if f.op=='atom' else str(len(f.args)) if f.op in ('and','or') else None))
    walk(ir)
    return instructions


def evaluate_ir(ir:FormulaIR,valuation:Mapping[str,FourValued])->FourValued:
    if not isinstance(ir,FormulaIR):
        raise TypeError('typed FormulaIR required')
    stack:list[FourValued]=[]
    constants={'yes':YES,'no':NO,'unknown':UNKNOWN,'conflict':CONFLICT}
    for opcode,arg in _ir_instructions(ir):
        if opcode in constants:
            stack.append(constants[opcode])
        elif opcode=='atom':
            if arg not in valuation or not isinstance(valuation[arg],FourValued):
                raise ValueError('GSL_IR_MISSING_OR_UNTYPED_ATOM')
            stack.append(valuation[arg])
        elif opcode=='not':
            stack.append(stack.pop().negate())
        elif opcode in ('and','or'):
            n=int(arg)
            if len(stack)<n:
                raise ValueError('GSL_IR_STACK_UNDERFLOW')
            values=stack[-n:]
            del stack[-n:]
            result=values[0]
            for value in values[1:]:
                result=(result.conjunction(value) if opcode=='and' else result.disjunction(value))
            stack.append(result)
        else:
            raise ValueError('GSL_IR_UNKNOWN_OPERATOR')
    if len(stack)!=1:
        raise ValueError('GSL_IR_INVALID_STACK')
    return stack[0]


def _atoms_source(s:SourceFormula)->set[str]:
    if isinstance(s,SourceAtom):return {s.name}
    if isinstance(s,SourceConstant):return set()
    if isinstance(s,SourceNot):return _atoms_source(s.inner)
    if isinstance(s,(SourceAnd,SourceOr)):return _atoms_source(s.left)|_atoms_source(s.right)
    raise TypeError('unknown source atom type')


def _atoms_ir(s:FormulaIR)->set[str]:
    result:set[str]=set()
    pending=[s]
    while pending:
        x=pending.pop()
        if x.op=='atom':result.add(x.name)
        pending.extend(x.args)
    return result


def _used_ops_source(s:SourceFormula)->set[str]:
    if isinstance(s,SourceConstant):return set()
    if isinstance(s,SourceAtom):return {'v4-atom'}
    if isinstance(s,SourceNot):return {'v4-not'}|_used_ops_source(s.inner)
    if isinstance(s,SourceAnd):return {'v4-and'}|_used_ops_source(s.left)|_used_ops_source(s.right)
    if isinstance(s,SourceOr):return {'v4-or'}|_used_ops_source(s.left)|_used_ops_source(s.right)
    raise TypeError('unknown source expression')


def _used_ops_ir(s:FormulaIR,max_nodes:int=10000)->set[str]:
    used:set[str]=set()
    pending=[(s,0)]
    processed=0
    while pending:
        node,depth=pending.pop()
        processed+=1
        if processed>max_nodes or depth>_MAX_PARSE_DEPTH:
            raise ValueError('GSL_IR_RESOURCE_LIMIT')
        op={'atom':'v4-atom','not':'v4-not','and':'v4-and','or':'v4-or'}.get(node.op)
        if op is not None:used.add(op)
        pending.extend((a,depth+1) for a in node.args)
    return used


class OracleStatus(str,Enum):
    FINITE_EQUIVALENT = 'FINITE_EQUIVALENT'
    COUNTEREXAMPLE = 'COUNTEREXAMPLE'
    INCONCLUSIVE_RESOURCE_LIMIT = 'INCONCLUSIVE_RESOURCE_LIMIT'
    UNSUPPORTED_FEATURE = 'UNSUPPORTED_FEATURE'
    INVALID_IR = 'INVALID_IR'
    INVALID_SOURCE = 'INVALID_SOURCE'
    UNTRUSTED_PIN = 'UNTRUSTED_PIN'


@dataclass(frozen=True,slots=True)
class OracleResult:
    status:OracleStatus
    atoms:tuple[str,...]
    valuations_checked:int
    witness:tuple[tuple[str,tuple[bool,bool]],...] = ()
    source_value:tuple[bool,bool] | None = None
    ir_value:tuple[bool,bool] | None = None
    reason:str = ''

    @property
    def acceptable(self)->bool:
        return self.status is OracleStatus.FINITE_EQUIVALENT


def verify_semantics(
    bundle:SourceBundle, context:CompileContext, origin:SourceOrigin, candidate:FormulaIR,
    *,max_atoms:int=6,max_valuations:int=4096,
)->OracleResult:
    """Check actual pinned bytes → source evaluator vs candidate IR VM.

    The candidate's own digest is NOT an oracle; source and its expected digest
    must come from an external pinned context. For >budget, refuse PASS.
    """
    if not isinstance(bundle,SourceBundle) or not isinstance(context,CompileContext) or not isinstance(origin,SourceOrigin) or not isinstance(candidate,FormulaIR):
        return OracleResult(OracleStatus.INVALID_SOURCE,(),0,reason='typed inputs required')
    if not verify_source_context(bundle,context).ok:
        return OracleResult(OracleStatus.UNTRUSTED_PIN,(),0,reason='external source pin not accepted')
    try:
        origin.verify_against(bundle)
        src=parse_source_formula(bundle.source_bytes[origin.byte_start:origin.byte_end])
    except (ValueError,UnicodeDecodeError,TypeError) as exc:
        return OracleResult(OracleStatus.INVALID_SOURCE,(),0,reason=str(exc))
    try:
        source_features=_used_ops_source(src)
        candidate_features=_used_ops_ir(candidate)
        # Pre-validate VM depth even on a zero-valuation or constant formula.
        _ir_instructions(candidate)
    except (ValueError,RecursionError,TypeError) as exc:
        return OracleResult(OracleStatus.INVALID_IR,(),0,reason=str(exc))
    if not (source_features|candidate_features) <= context.supported_features:
        return OracleResult(OracleStatus.UNSUPPORTED_FEATURE,(),0,reason='operator not supported by pinned semantic profile')
    names=tuple(sorted(_atoms_source(src)|_atoms_ir(candidate)))
    if type(max_atoms) is not int or type(max_valuations) is not int or max_atoms<0 or max_valuations<=0 or len(names)>max_atoms or 4**len(names)>max_valuations:
        return OracleResult(OracleStatus.INCONCLUSIVE_RESOURCE_LIMIT,names,0,reason='exhaustive source/IR valuation budget exceeded')
    for n,assignment in enumerate(itertools.product(((False,False),(True,False),(False,True),(True,True)),repeat=len(names)),1):
        v=dict(zip(names,assignment))
        source_value=_source_eval(src,v)
        ir_value=evaluate_ir(candidate,{k:FourValued(*x) for k,x in v.items()})
        current=(ir_value.positive,ir_value.negative)
        if source_value!=current:
            return OracleResult(OracleStatus.COUNTEREXAMPLE,names,n,tuple(zip(names,assignment)),source_value,current,'semantic mismatch under pinned original source')
    return OracleResult(OracleStatus.FINITE_EQUIVALENT,names,4**len(names))
