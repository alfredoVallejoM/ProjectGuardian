"""LC06/LC07/LC08 slice: source-grounded elaboration, maps and pending proofs.

This produces ContractIR, not a complete C00-C14 compilation certificate.
The independent V0 is a consumer of this result, never its constructor.
"""
from __future__ import annotations
from dataclasses import dataclass

from guardian.domain.identity import EntityRef, ContentDigest
from guardian.domain.outcomes import Diagnostic, Result
from .contract import ProofObligation, ProofState
from .ir import (ContractIR, DeclarationIR, IRField, IRValue, IRType, FormulaIR,
                 RelationKind, SourceOrigin, canonical_bytes, decode_ir, contract_digest)
from .typecheck import TypedProgram, TypedFormula, typecheck_analyses


def _ref_key(ref: EntityRef) -> tuple[str, ...]:
    return ref.project.value, ref.kind.value, ref.entity.value, ref.revision.value


@dataclass(frozen=True, slots=True)
class SourceMapEntry:
    declaration: EntityRef
    path: str
    origin: SourceOrigin

    def __post_init__(self) -> None:
        if type(self.declaration) is not EntityRef or type(self.origin) is not SourceOrigin:
            raise TypeError('GSL_SOURCE_MAP_NOMINAL_CONTEXT')
        if type(self.path) is not str or not self.path.startswith('$'):
            raise ValueError('GSL_SOURCE_MAP_PATH')
        if self.declaration.project != self.origin.source.project:
            raise ValueError('GSL_SOURCE_MAP_PROJECT')


@dataclass(frozen=True, slots=True)
class ElaboratedProgram:
    contracts: tuple[ContractIR, ...]
    source_map: tuple[SourceMapEntry, ...]
    canonical_contracts: tuple[bytes, ...]
    contract_digests: tuple[ContentDigest, ...]
    unchecked_source_items: tuple[tuple[EntityRef, str], ...]

    def __post_init__(self) -> None:
        for sequence, typ in ((self.contracts,ContractIR),(self.source_map,SourceMapEntry),
                              (self.canonical_contracts,bytes),(self.contract_digests,ContentDigest)):
            if type(sequence) is not tuple or any(type(x) is not typ for x in sequence):
                raise TypeError('GSL_ELABORATION_RESULT_IMMUTABLE')
        if not self.contracts or len(self.canonical_contracts)!=len(self.contracts) or len(self.contract_digests)!=len(self.contracts):
            raise ValueError('GSL_ELABORATION_POPULATION')
        if len({c.source for c in self.contracts})!=len(self.contracts):
            raise ValueError('GSL_ELABORATION_DUPLICATE_SOURCE')
        expected=set(); declarations={}
        for ir, raw, digest in zip(self.contracts,self.canonical_contracts,self.contract_digests):
            ContractIR.__post_init__(ir)
            if canonical_bytes(ir)!=raw or contract_digest(ir)!=digest or decode_ir(raw)!=ir:
                raise ValueError('GSL_ELABORATION_CANONICAL_MISMATCH')
            for declaration in ir.declarations:
                if declaration.identity in declarations:
                    raise ValueError('GSL_ELABORATION_DUPLICATE_DECLARATION')
                declarations[declaration.identity]=declaration
                expected.add((declaration.identity,'$'))
                for index, field in enumerate(declaration.fields):
                    path=f'$.fields[{index}]';expected.add((declaration.identity,path))
                    if field.typed_value.kind is IRType.V4:
                        stack=[(field.typed_value.value,path+'.value')]
                        while stack:
                            formula, fp=stack.pop();expected.add((declaration.identity,fp))
                            stack.extend((arg,fp+f'.args[{i}]') for i,arg in enumerate(formula.args))
        actual=[(entry.declaration,entry.path) for entry in self.source_map]
        if len(actual)!=len(set(actual)) or set(actual)!=expected:
            raise ValueError('GSL_SOURCE_MAP_POPULATION_MISMATCH')
        for entry in self.source_map:
            SourceMapEntry.__post_init__(entry)
            parent=declarations[entry.declaration].origin
            if (entry.origin.source!=parent.source or entry.origin.source_digest!=parent.source_digest
                    or entry.origin.byte_start<parent.byte_start or entry.origin.byte_end>parent.byte_end
                    or (entry.path=='$' and entry.origin!=parent)):
                raise ValueError('GSL_SOURCE_MAP_ORIGIN_MISMATCH')
        if type(self.unchecked_source_items) is not tuple or any(type(p) is not tuple or len(p)!=2
                or type(p[0]) is not EntityRef or type(p[1]) is not str or not p[1] for p in self.unchecked_source_items):
            raise TypeError('GSL_SOURCE_ITEM_COVERAGE_REQUIRED')

    @property
    def status(self) -> str:
        return 'ELABORATED'

    @property
    def compiled(self) -> bool:
        # C12 diff / C14 emission and campaign qualification are not performed.
        return False

    @property
    def normatively_admitted(self) -> bool:
        return False

    @property
    def proofs(self) -> tuple[ProofObligation, ...]:
        return tuple(p for ir in self.contracts for p in ir.proofs)

    @property
    def source_coverage(self) -> str:
        return 'SOURCE_ITEMS_NOT_RECONCILED'


def _lower_formula(value: TypedFormula, declaration: EntityRef, source: SourceOrigin,
                   path: str, maps: list[SourceMapEntry]) -> FormulaIR:
    origin=SourceOrigin(source.source,source.source_digest,value.span.start,value.span.end)
    maps.append(SourceMapEntry(declaration,path,origin))
    args=tuple(_lower_formula(a,declaration,source,path+f'.args[{i}]',maps)
               for i,a in enumerate(value.arguments))
    return FormulaIR(value.operator,args,value.atom)


def elaborate_program(program: TypedProgram) -> Result[ElaboratedProgram]:
    """Recheck original source typing before accepting any public typed object.

    Re-running typing is deliberate fail-closed validation, not incremental
    compilation. A modified TypedProgram never chooses its own source meaning.
    """
    try:
        if type(program) is not TypedProgram:
            raise TypeError('GSL_TYPED_PROGRAM_REQUIRED')
        TypedProgram.__post_init__(program)
        checked=typecheck_analyses(program.analyses,program.context,snapshot=program.snapshot,
            imports=program.imports,external_symbols=program.external_symbols,budget=program.budget)
        if not checked.ok:
            return Result(diagnostics=checked.diagnostics)
        if checked.value.declarations!=program.declarations or checked.value.resolution!=program.resolution:
            raise ValueError('GSL_TYPED_PROGRAM_SOURCE_MISMATCH')
        bundles={a.extraction.source.source_ref:a.extraction.source for a in program.analyses}
        contracts=[];maps=[]
        for source_ref in sorted(bundles,key=_ref_key):
            bundle=bundles[source_ref];declarations=[];proofs=[]
            for declaration in program.declarations:
                if declaration.origin.source!=source_ref:
                    continue
                declaration.origin.verify_against(bundle)
                maps.append(SourceMapEntry(declaration.identity,'$',declaration.origin))
                fields=[]
                for index,field in enumerate(declaration.fields):
                    field.origin.verify_against(bundle)
                    path=f'$.fields[{index}]'
                    maps.append(SourceMapEntry(declaration.identity,path,field.origin))
                    value=(_lower_formula(field.value,declaration.identity,declaration.origin,path+'.value',maps)
                           if field.kind is IRType.V4 else field.value)
                    fields.append(IRField(field.name,IRValue(field.kind,value)))
                    if field.kind is IRType.DEFERRED:
                        proofs.append(ProofObligation('interpret:'+declaration.identity.entity.value,
                                                      declaration.identity,ProofState.UNPROVEN))
                    elif field.kind is IRType.KIND and value is RelationKind.PROPOSED_DETAIL:
                        proofs.append(ProofObligation('refinement:'+declaration.identity.entity.value,
                                                      declaration.identity,ProofState.UNPROVEN))
                declarations.append(DeclarationIR(declaration.identity,declaration.origin,tuple(fields)))
            ir=ContractIR(program.context.project,source_ref,bundle.expected_digest,tuple(declarations),tuple(proofs))
            ir.verify_sources(bundle);contracts.append(ir)
        for entry in maps:
            entry.origin.verify_against(bundles[entry.origin.source])
        result=ElaboratedProgram(tuple(contracts),tuple(maps),tuple(canonical_bytes(ir) for ir in contracts),
            tuple(contract_digest(ir) for ir in contracts),program.resolution.unchecked_source_items)
        mapped=validate_source_map(program,result)
        return Result(result) if mapped.ok else Result(diagnostics=mapped.diagnostics)
    except (TypeError,ValueError,AttributeError,KeyError,RecursionError) as exc:
        return Result(diagnostics=(Diagnostic('GSL_ELABORATION_REJECTED','$','source-grounded typed program',
                                              type(exc).__name__,str(exc) or 'invalid elaboration'),))


def validate_source_map(program: TypedProgram, output: ElaboratedProgram) -> Result[bool]:
    """Check exact parsed-source positions, not only containment in a declaration.

    This checker walks the parsed source and does not call the formula lowerer.
    It is an internal integrity check, not the independent external V0 oracle.
    Semantic correspondence and trust in source pins are separate guarantees.
    """
    try:
        if type(program) is not TypedProgram or type(output) is not ElaboratedProgram:
            raise TypeError('GSL_SOURCE_MAP_INPUT')
        TypedProgram.__post_init__(program); ElaboratedProgram.__post_init__(output)
        fresh=typecheck_analyses(program.analyses,program.context,snapshot=program.snapshot,
            imports=program.imports,external_symbols=program.external_symbols,budget=program.budget)
        if not fresh.ok:
            return Result(diagnostics=fresh.diagnostics)
        if fresh.value.declarations!=program.declarations or fresh.value.resolution!=program.resolution:
            raise ValueError('GSL_TYPED_PROGRAM_SOURCE_MISMATCH')
        expected={}
        bundles={a.extraction.source.source_ref:a.extraction.source for a in program.analyses}
        if {c.source for c in output.contracts}!=set(bundles):
            raise ValueError('GSL_SOURCE_MAP_SOURCE_POPULATION')
        for declaration in fresh.value.resolution.declarations:
            bundle=bundles[declaration.source]
            def put(path,span):
                expected[declaration.identity,path]=SourceOrigin(bundle.source_ref,bundle.expected_digest,span.start,span.end)
            put('$',declaration.syntax.span)
            typed=next(d for d in fresh.value.declarations if d.identity==declaration.identity)
            for i,(parsed,field) in enumerate(zip(declaration.syntax.fields,typed.fields)):
                path=f'$.fields[{i}]';put(path,parsed.expr.span)
                if field.kind is IRType.V4:
                    stack=[(parsed.expr,path+'.value')]
                    while stack:
                        expr,fp=stack.pop();put(fp,expr.span)
                        stack.extend((arg,fp+f'.args[{n}]') for n,arg in enumerate(expr.args))
        actual={(m.declaration,m.path):m.origin for m in output.source_map}
        if actual!=expected:
            raise ValueError('GSL_SOURCE_MAP_EXACT_SPAN_MISMATCH')
        return Result(True)
    except (TypeError,ValueError,AttributeError,KeyError,RecursionError) as exc:
        return Result(diagnostics=(Diagnostic('GSL_SOURCE_MAP_REJECTED','$','exact original AST spans',
            type(exc).__name__,str(exc) or 'invalid source map'),))
