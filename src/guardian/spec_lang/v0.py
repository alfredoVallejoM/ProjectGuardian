"""GSL0-LC02: finite V4 source-semantics oracle and independent IR VM.

The V4 verification fragment follows the declared LC03 lexical profile but
uses a separate byte lexer and source interpreter, independent of productive
parser/lowering code. Formula checks and contract correspondence are distinct.
No Python eval, callbacks, publication or normative admission capabilities.
"""
from __future__ import annotations

import itertools
import re
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Mapping

from guardian.domain.evidence_logic import FourValued, UNKNOWN, YES, NO, CONFLICT
from guardian.domain.identity import EntityRef
from guardian.spec_lang.contract import ProofObligation, SourceBundle, CompileContext, verify_source_context
from guardian.spec_lang.ir import ContractIR, FormulaIR, IRType, SourceOrigin
from .source_inventory import (independent_tokens, CheckStatus, SourceCorrespondence,
                              check_source_correspondence)

_KEYWORDS = {'not','and','or','yes','no','unknown','conflict','true','false'}
_MAX_PARSE_DEPTH = 64
_MAX_SOURCE_TOKENS = 10000
_MAX_FORMULA_NODES = 10000


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

    def __post_init__(self) -> None:
        if not isinstance(self.inner, SourceFormula):
            raise TypeError('source NOT requires a source formula')


@dataclass(frozen=True, slots=True)
class SourceAnd(SourceFormula):
    left: SourceFormula
    right: SourceFormula

    def __post_init__(self) -> None:
        if not isinstance(self.left, SourceFormula) or not isinstance(self.right, SourceFormula):
            raise TypeError('source AND requires source formulas')


@dataclass(frozen=True, slots=True)
class SourceOr(SourceFormula):
    left: SourceFormula
    right: SourceFormula

    def __post_init__(self) -> None:
        if not isinstance(self.left, SourceFormula) or not isinstance(self.right, SourceFormula):
            raise TypeError('source OR requires source formulas')


class _SourceParser:
    def __init__(self,raw:str):
        self.tokens=[t.text for t in independent_tokens(raw.encode('utf-8'))]
        if len(self.tokens)>_MAX_SOURCE_TOKENS:
            raise ValueError('GSL_V0_SOURCE_RESOURCE_LIMIT')
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
        if value in ('yes','no','unknown','conflict','true','false'):
            return SourceConstant({'true':'yes','false':'no'}.get(value,value))
        if value in _KEYWORDS or re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',value) is None:
            raise ValueError('GSL_V0_UNEXPECTED_TOKEN')
        return SourceAtom(value)


def parse_source_formula(raw:bytes)->SourceFormula:
    if not isinstance(raw,bytes):
        raise TypeError('source formula requires raw UTF-8 bytes')
    source=_SourceParser(raw.decode('utf-8','strict')).parse()
    _validate_source_tree(source)
    return source


def _validate_source_tree(root:SourceFormula)->None:
    """Bound left-associated formulas as well as recursive parentheses/NOTs.

    The source parser is not a credentialed verifier and must never turn a
    hostile input into an uncaught RecursionError or a vacuous PASS.
    """
    pending=[(root,0)]
    nodes=0
    while pending:
        node,depth=pending.pop()
        nodes+=1
        if nodes>_MAX_FORMULA_NODES or depth>_MAX_PARSE_DEPTH:
            raise ValueError('GSL_V0_SOURCE_RESOURCE_LIMIT')
        if isinstance(node,SourceNot):
            pending.append((node.inner,depth+1))
        elif isinstance(node,(SourceAnd,SourceOr)):
            pending.extend(((node.left,depth+1),(node.right,depth+1)))
        elif not isinstance(node,(SourceAtom,SourceConstant)):
            raise TypeError('invalid source formula node')


def lower_formula(source:SourceFormula)->FormulaIR:
    """Candidate translator; oracle must NOT derive expected results from this."""
    _validate_source_tree(source)
    return _lower_validated(source)


def _lower_validated(source:SourceFormula)->FormulaIR:
    if isinstance(source,SourceAtom):
        return FormulaIR('atom',name=source.name)
    if isinstance(source,SourceConstant):
        return FormulaIR(source.value)
    if isinstance(source,SourceNot):
        return FormulaIR('not',(_lower_validated(source.inner),))
    if isinstance(source,SourceAnd):
        return FormulaIR('and',(_lower_validated(source.left),_lower_validated(source.right)))
    if isinstance(source,SourceOr):
        return FormulaIR('or',(_lower_validated(source.left),_lower_validated(source.right)))
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
    seen_nodes=0
    def walk(f:FormulaIR,depth:int=0):
        nonlocal seen_nodes
        seen_nodes+=1
        if seen_nodes>_MAX_FORMULA_NODES:
            raise ValueError('GSL_IR_RESOURCE_LIMIT')
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
    MISSING_BINDING = 'MISSING_BINDING'
    INCONCLUSIVE_NO_INTERPRETED_FORMULAS = 'INCONCLUSIVE_NO_INTERPRETED_FORMULAS'
    INCONCLUSIVE_EXPECTED_COVERAGE = 'INCONCLUSIVE_EXPECTED_COVERAGE'


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
    except (ValueError,UnicodeDecodeError,TypeError,RecursionError) as exc:
        return OracleResult(OracleStatus.INVALID_SOURCE,(),0,reason=str(exc))
    try:
        _validate_source_tree(src)
        source_features=_used_ops_source(src)
        candidate_features=_used_ops_ir(candidate)
        # Pre-validate VM depth even on a zero-valuation or constant formula.
        _ir_instructions(candidate)
    except (ValueError,RecursionError,TypeError) as exc:
        return OracleResult(OracleStatus.INVALID_IR,(),0,reason=str(exc))
    if not (source_features|candidate_features) <= context.supported_features:
        return OracleResult(OracleStatus.UNSUPPORTED_FEATURE,(),0,reason='operator not supported by pinned semantic profile')
    if 'finite-v4-oracle' not in context.supported_features:
        return OracleResult(OracleStatus.UNSUPPORTED_FEATURE,(),0,reason='finite oracle not enabled in semantic profile')
    names=tuple(sorted(_atoms_source(src)|_atoms_ir(candidate)))
    if type(max_atoms) is not int or type(max_valuations) is not int or max_atoms<0 or max_valuations<=0 or len(names)>max_atoms or 4**len(names)>max_valuations:
        return OracleResult(OracleStatus.INCONCLUSIVE_RESOURCE_LIMIT,names,0,reason='exhaustive source/IR valuation budget exceeded')
    for n,assignment in enumerate(itertools.product(((False,False),(True,False),(False,True),(True,True)),repeat=len(names)),1):
        v=dict(zip(names,assignment))
        try:
            source_value=_source_eval(src,v)
        except (ValueError,TypeError,RecursionError) as exc:
            return OracleResult(OracleStatus.INVALID_SOURCE,names,n-1,reason=str(exc))
        try:
            ir_value=evaluate_ir(candidate,{k:FourValued(*x) for k,x in v.items()})
        except (ValueError,TypeError,RecursionError,IndexError) as exc:
            return OracleResult(OracleStatus.INVALID_IR,names,n-1,reason=str(exc))
        current=(ir_value.positive,ir_value.negative)
        if source_value!=current:
            return OracleResult(OracleStatus.COUNTEREXAMPLE,names,n,tuple(zip(names,assignment)),source_value,current,'semantic mismatch under pinned original source')
    return OracleResult(OracleStatus.FINITE_EQUIVALENT,names,4**len(names))


@dataclass(frozen=True, slots=True)
class FormulaGrounding:
    """Independently supplied source location for ONE interpreted IR field.

    It is not a source map attestation: the verifier checks its source byte
    content and its placement in the declaration against an independent pin.
    It cannot infer the human meaning of an arbitrary textual specification.
    """
    declaration: EntityRef
    field_name: str
    field_occurrence: int
    origin: SourceOrigin

    def __post_init__(self) -> None:
        if not isinstance(self.declaration, EntityRef) or not isinstance(self.origin, SourceOrigin):
            raise TypeError('formula binding needs a pinned declaration and source')
        if type(self.field_name) is not str or not self.field_name.isidentifier():
            raise ValueError('formula binding needs exact field name')
        if type(self.field_occurrence) is not int or self.field_occurrence < 0:
            raise ValueError('formula binding occurrence must be a nonnegative integer')


@dataclass(frozen=True, slots=True)
class CoverageExpectation:
    """Immutable independent inventory; must NOT be inferred from candidate IR.

    GSL-0 does not acquire or ratify this inventory. LC09 must establish its
    completeness against the original authoritative G-00 corpus.
    """
    declarations: frozenset[EntityRef]
    interpreted_fields: frozenset[tuple[EntityRef,str,int]]

    def __post_init__(self) -> None:
        if (type(self.declarations) is not frozenset or
                any(not isinstance(d, EntityRef) for d in self.declarations)):
            raise TypeError('expected declaration identities must be nominal')
        if type(self.interpreted_fields) is not frozenset:
            raise TypeError('expected formula identifiers must be immutable')
        for field in self.interpreted_fields:
            if (type(field) is not tuple or len(field) != 3 or not isinstance(field[0], EntityRef)
                    or type(field[1]) is not str or not field[1].isidentifier()
                    or type(field[2]) is not int or field[2] < 0
                    or field[0] not in self.declarations):
                raise ValueError('expected formula must belong to a declared typed entity')


@dataclass(frozen=True, slots=True)
class ContractSemanticResult:
    """Full coverage of the *interpreted V4 subset*, never product qualification."""
    status: OracleStatus
    interpreted_fields: int
    checked_fields: int
    valuations_checked: int
    counterexample: FormulaGrounding | None = None
    oracle_result: OracleResult | None = None
    deferred_properties: tuple[EntityRef, ...] = ()
    pending_proofs: tuple[ProofObligation, ...] = ()
    reason: str = ''

    correspondence: SourceCorrespondence = field(default_factory=SourceCorrespondence)

    def __post_init__(self) -> None:
        if (not isinstance(self.status, OracleStatus) or not isinstance(self.correspondence, SourceCorrespondence)
                or any(type(n) is not int or n < 0 for n in
                       (self.interpreted_fields, self.checked_fields, self.valuations_checked))
                or self.checked_fields > self.interpreted_fields):
            raise ValueError('INVALID_SEMANTIC_REPORT')
        if (self.status is OracleStatus.FINITE_EQUIVALENT
                and (not self.checked_fields or self.checked_fields != self.interpreted_fields)):
            raise ValueError('INCOMPLETE_FINITE_REPORT')
        if type(self.deferred_properties) is not tuple or type(self.pending_proofs) is not tuple:
            raise TypeError('semantic obligations must be immutable')

    @property
    def formula_equivalent(self) -> bool:
        """Only the enumerated, grounded V4 fields, under the recorded budget."""
        return self.status is OracleStatus.FINITE_EQUIVALENT

    @property
    def acceptable(self) -> bool:
        """Source correspondence only; NOT admission or full contract validity.

        Legacy boolean narrowed to prevent finite formulas certifying unchecked
        declarations/fields. See each dimension for guarantees not checked.
        """
        return (self.formula_equivalent and not self.deferred_properties and not self.pending_proofs
                and self.correspondence.declarations is CheckStatus.CHECKED
                and self.correspondence.fields is CheckStatus.CHECKED)

    @property
    def full_contract_equivalent(self) -> bool:
        return (self.acceptable and self.correspondence.reference_integrity is CheckStatus.CHECKED
                and self.correspondence.historical_coverage is CheckStatus.CHECKED)



def _independent_field_value_spans(raw: bytes, *, base_offset: int) -> dict[str, tuple[tuple[int, int], ...]]:
    """Locate actual `field: expression;` value bytes, excluding strings/comments.

    This verifier lexer is intentionally separate from the productive GSL
    frontend. It binds a V4 formula origin to its FIELD rather than accepting
    any formula-looking substring anywhere within the declaration, including
    comments, strings, or a different field. It is a bounded LC02 contract
    check, not the full LC03/LC04 declaration-origin proof.
    """
    tokens = [(t.kind, t.text, t.start, t.end)
              for t in independent_tokens(raw, base_offset)]
    result: dict[str, list[tuple[int, int]]] = {}
    for idx in range(len(tokens) - 2):
        head = tokens[idx]
        if head[0] != 'name' or tokens[idx+1][1] != ':':
            continue
        paren = 0
        last = None
        for j in range(idx+2, len(tokens)):
            current=tokens[j]
            punctuation = current[1]
            if punctuation == '(':
                paren += 1
            elif punctuation == ')':
                paren -= 1
            if paren < 0:
                break
            if punctuation == ';' and paren == 0:
                if last is not None:
                    result.setdefault(head[1], []).append((tokens[idx+2][2], last[3]))
                break
            if punctuation in ('{', '}') and paren == 0:
                break
            last = current
    return {name: tuple(spans) for name, spans in result.items()}


def _verify_interpreted_fields(
    ir: ContractIR,
    bundle: SourceBundle,
    context: CompileContext,
    groundings: tuple[FormulaGrounding, ...],
    *,
    expectation: CoverageExpectation | None = None,
    max_atoms: int = 6,
    max_valuations: int = 4096,
    max_total_valuations: int = 65536,
) -> ContractSemanticResult:
    """Fail closed on every interpreted field missing independent grounding.

    A syntactically valid IR with hashes recalculated but a dropped/rewired
    formula cannot be called semantically equivalent. This is LC02 V0 only:
    LC03–LC08 must prove that GSL elaboration supplies complete groundings.
    """
    if (not isinstance(ir, ContractIR) or not isinstance(bundle, SourceBundle)
            or not isinstance(context, CompileContext) or type(groundings) is not tuple
            or any(not isinstance(g, FormulaGrounding) for g in groundings)):
        return ContractSemanticResult(OracleStatus.INVALID_IR, 0, 0, 0, reason='typed contract inputs required')
    if (type(max_atoms) is not int or max_atoms < 0 or type(max_valuations) is not int
            or max_valuations <= 0 or type(max_total_valuations) is not int or max_total_valuations <= 0):
        return ContractSemanticResult(OracleStatus.INCONCLUSIVE_RESOURCE_LIMIT, 0, 0, 0,
                                      reason='invalid finite evaluation budget')
    if not verify_source_context(bundle, context).ok:
        return ContractSemanticResult(OracleStatus.UNTRUSTED_PIN, 0, 0, 0, reason='source pin is not trusted')
    if expectation is None:
        return ContractSemanticResult(OracleStatus.INCONCLUSIVE_EXPECTED_COVERAGE, 0, 0, 0,
                                      reason='no independent source declaration/field inventory supplied')
    if not isinstance(expectation, CoverageExpectation):
        return ContractSemanticResult(OracleStatus.INVALID_SOURCE, 0, 0, 0,
                                      reason='expected source inventory is not typed')
    try:
        ir.verify_sources(bundle)
    except (ValueError, TypeError) as exc:
        return ContractSemanticResult(OracleStatus.INVALID_IR, 0, 0, 0, reason=str(exc))

    interpretations: dict[tuple[EntityRef, str, int], tuple[FormulaIR, SourceOrigin]] = {}
    deferred: list[EntityRef] = []
    for declaration in ir.declarations:
        counts: dict[str, int] = {}
        for field in declaration.fields:
            nth = counts.get(field.name, 0)
            counts[field.name] = nth + 1
            if field.typed_value.kind is IRType.V4:
                interpretations[(declaration.identity, field.name, nth)] = (
                    field.typed_value.value, declaration.origin
                )
            elif field.typed_value.kind is IRType.DEFERRED:
                deferred.append(declaration.identity)

    if ({d.identity for d in ir.declarations} != expectation.declarations or
            set(interpretations) != expectation.interpreted_fields):
        return ContractSemanticResult(OracleStatus.MISSING_BINDING, len(interpretations), 0, 0,
                                      deferred_properties=tuple(deferred),
                                      reason='candidate declaration/field inventory differs from independent source inventory')

    bound: dict[tuple[EntityRef, str, int], FormulaGrounding] = {}
    for grounding in groundings:
        key = (grounding.declaration, grounding.field_name, grounding.field_occurrence)
        if key in bound:
            return ContractSemanticResult(OracleStatus.MISSING_BINDING, len(interpretations), 0, 0,
                                          deferred_properties=tuple(deferred), reason='duplicate formula grounding')
        bound[key] = grounding
    if set(bound) != set(interpretations):
        missing = sorted(str(k[0].entity.value) + '.' + k[1] + ':' + str(k[2]) for k in set(interpretations)-set(bound))
        extra = sorted(str(k[0].entity.value) + '.' + k[1] + ':' + str(k[2]) for k in set(bound)-set(interpretations))
        return ContractSemanticResult(OracleStatus.MISSING_BINDING, len(interpretations), 0, 0,
                                      deferred_properties=tuple(deferred),
                                      reason=f'grounding coverage mismatch: missing={missing}, extra={extra}')
    if not interpretations:
        return ContractSemanticResult(OracleStatus.INCONCLUSIVE_NO_INTERPRETED_FORMULAS, 0, 0, 0,
                                      deferred_properties=tuple(deferred), reason='no interpreted formulas to compare')

    # A caller-supplied source map alone cannot prove the selected bytes are
    # the semantic value of the claimed field. Recompute field anchors from
    # pinned source bytes with a separate small lexer, ignoring comments and
    # strings; compare exact occurrence and complete expression range.
    field_ranges: dict[tuple[int, int], dict[str, tuple[tuple[int, int], ...]]] = {}
    checked = 0
    valuations = 0
    for key, (candidate, declaration_origin) in interpretations.items():
        grounding = bound[key]
        src = grounding.origin
        if (src.source != declaration_origin.source or src.source_digest != declaration_origin.source_digest
                or not (declaration_origin.byte_start <= src.byte_start < src.byte_end <= declaration_origin.byte_end)):
            return ContractSemanticResult(OracleStatus.MISSING_BINDING, len(interpretations), checked, valuations,
                                          grounding, deferred_properties=tuple(deferred),
                                          reason='field source location not contained within declaration origin')
        span_key = (declaration_origin.byte_start, declaration_origin.byte_end)
        if span_key not in field_ranges:
            try:
                field_ranges[span_key] = _independent_field_value_spans(
                    bundle.source_bytes[span_key[0]:span_key[1]],base_offset=span_key[0])
            except (ValueError, UnicodeDecodeError) as exc:
                return ContractSemanticResult(OracleStatus.INVALID_SOURCE, len(interpretations), checked, valuations,
                                              counterexample=grounding,deferred_properties=tuple(deferred),
                                              reason=str(exc))
        spans = field_ranges[span_key].get(key[1], ())
        expected_occurrences=sum(1 for k in expectation.interpreted_fields if k[0]==key[0] and k[1]==key[1])
        if len(spans)!=expected_occurrences or key[2] >= len(spans) or spans[key[2]] != (src.byte_start, src.byte_end):
            return ContractSemanticResult(OracleStatus.MISSING_BINDING, len(interpretations), checked, valuations,
                                          counterexample=grounding,deferred_properties=tuple(deferred),
                                          reason='formula grounding is not the complete value of the named source field')
        if type(max_total_valuations) is not int or max_total_valuations <= valuations:
            return ContractSemanticResult(OracleStatus.INCONCLUSIVE_RESOURCE_LIMIT,
                len(interpretations), checked, valuations, reason='aggregate valuation budget exhausted')
        outcome = verify_semantics(bundle, context, src, candidate,
                                   max_atoms=max_atoms,
                                   max_valuations=min(max_valuations, max_total_valuations - valuations))
        valuations += outcome.valuations_checked
        if not outcome.acceptable:
            return ContractSemanticResult(outcome.status, len(interpretations), checked, valuations,
                                          counterexample=grounding, oracle_result=outcome,
                                          deferred_properties=tuple(deferred), pending_proofs=ir.proofs,
                                          reason=outcome.reason)
        checked += 1
    return ContractSemanticResult(OracleStatus.FINITE_EQUIVALENT, len(interpretations), checked, valuations,
                                  deferred_properties=tuple(deferred), pending_proofs=ir.proofs,
                                  reason='all interpreted V4 fields checked; deferred properties and POs do not qualify')


def verify_contract_semantics(
    ir: ContractIR, bundle: SourceBundle, context: CompileContext,
    groundings: tuple[FormulaGrounding, ...], *,
    expectation: CoverageExpectation | None = None,
    max_atoms: int = 6, max_valuations: int = 4096, max_total_valuations: int = 65536,
    source_format: str = 'gsl',
) -> ContractSemanticResult:
    """Compose distinct checks; no single finite result is a global certificate.

    Original bytes, not the candidate map, establish declaration and field
    origins. Reference *existence*, historical import completeness, admission,
    and implementation behavior remain explicit NOT_CHECKED dimensions.
    """
    report = _verify_interpreted_fields(ir, bundle, context, groundings,
        expectation=expectation, max_atoms=max_atoms, max_valuations=max_valuations,
        max_total_valuations=max_total_valuations)
    if not report.formula_equivalent:
        return report
    correspondence = check_source_correspondence(ir, bundle, context, source_format=source_format)
    if correspondence.declarations is CheckStatus.MISMATCH:
        return replace(report, status=OracleStatus.MISSING_BINDING,
                       correspondence=correspondence, reason=correspondence.reason)
    return replace(report, correspondence=correspondence,
                   reason='V4 fields checked; source correspondence and unchecked dimensions are reported separately')
