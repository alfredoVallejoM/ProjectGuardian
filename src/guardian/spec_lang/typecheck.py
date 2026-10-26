"""LC05: strict source-grounded typing for the fixed GSL0/IR 0.1 profile.

The existing LC04 resolver owns identities. This module validates field meaning,
arity and nominal domains; it neither interprets project callbacks nor confers
admission. Import/module syntax and a general term calculus remain outside 0.1.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from guardian.domain.identity import EntityId, EntityKind, EntityRef, ProjectId
from guardian.domain.outcomes import Diagnostic, Result
from guardian.domain.references import RecordSnapshot, TrustedEntityImports
from .contract import CompileContext, SourceBundle, SymbolBinding
from .ir import (IRType, CommitmentKind, RelationKind, SourceItem, SourceOrigin,
                 _FIELDS, _REQUIRED, _REFERENCE_KIND)
from .resolution import ResolutionReport, resolve_analyses
from .syntax import Expr, FrontendAnalysis
from .text import TextSpan


@dataclass(frozen=True, slots=True)
class TypecheckBudget:
    max_nodes: int = 10000
    max_depth: int = 64
    max_sources: int = 128
    max_bytes: int = 8_000_000

    def __post_init__(self) -> None:
        for value, cap in ((self.max_nodes, 100000), (self.max_depth, 64),
                           (self.max_sources, 1024), (self.max_bytes, 8_000_000)):
            if type(value) is not int or not 1 <= value <= cap:
                raise ValueError('GSL_INVALID_TYPECHECK_BUDGET')


@dataclass(frozen=True, slots=True)
class TypedFormula:
    """Typed source term; not FormulaIR and not the independent V0 AST."""
    operator: str
    span: TextSpan
    arguments: tuple[TypedFormula, ...] = ()
    atom: str | None = None

    def __post_init__(self) -> None:
        if type(self.span) is not TextSpan or type(self.arguments) is not tuple:
            raise TypeError('GSL_TYPED_FORMULA_REQUIRED')
        if any(type(a) is not TypedFormula for a in self.arguments):
            raise TypeError('GSL_TYPED_FORMULA_REQUIRED')
        if self.operator == 'atom':
            if type(self.atom) is not str or not self.atom.isidentifier() or self.arguments:
                raise ValueError('GSL_INVALID_TYPED_ATOM')
            if self.atom in ('true','false','yes','no','unknown','conflict','and','or','not'):
                raise ValueError('GSL_LITERAL_IS_NOT_ATOM')
        elif self.operator in ('yes','no','unknown','conflict'):
            if self.atom is not None or self.arguments:
                raise ValueError('GSL_INVALID_TYPED_CONSTANT')
        elif self.operator in ('not','and','or'):
            if self.atom is not None or (len(self.arguments) != 1 if self.operator == 'not' else len(self.arguments) < 2):
                raise ValueError('GSL_INVALID_TYPED_ARITY')
        else:
            raise ValueError('GSL_UNKNOWN_TYPED_OPERATOR')
        if any(a.span.start < self.span.start or a.span.end > self.span.end for a in self.arguments):
            raise ValueError('GSL_TYPED_ORIGIN_MISMATCH')


@dataclass(frozen=True, slots=True)
class TypedField:
    name: str
    kind: IRType
    value: str | EntityRef | SourceItem | CommitmentKind | RelationKind | TypedFormula
    origin: SourceOrigin

    def __post_init__(self) -> None:
        if type(self.name) is not str or type(self.kind) is not IRType or type(self.origin) is not SourceOrigin:
            raise TypeError('GSL_TYPED_FIELD_REQUIRED')
        expected = {IRType.TEXT:(str,), IRType.DEFERRED:(str,), IRType.REF:(EntityRef,),
                    IRType.SOURCE_ITEM:(SourceItem,), IRType.KIND:(CommitmentKind,RelationKind),
                    IRType.V4:(TypedFormula,)}
        if self.kind not in expected or type(self.value) not in expected[self.kind]:
            raise TypeError('GSL_TYPED_FIELD_TYPE_MISMATCH')


@dataclass(frozen=True, slots=True)
class TypedDeclaration:
    identity: EntityRef
    origin: SourceOrigin
    fields: tuple[TypedField, ...]

    def __post_init__(self) -> None:
        if type(self.identity) is not EntityRef or type(self.origin) is not SourceOrigin:
            raise TypeError('GSL_TYPED_DECLARATION_REQUIRED')
        if type(self.fields) is not tuple or any(type(f) is not TypedField for f in self.fields):
            raise TypeError('GSL_TYPED_FIELDS_REQUIRED')
        if self.identity.project != self.origin.source.project:
            raise ValueError('GSL_TYPED_PROJECT_MISMATCH')
        if any(f.origin.source != self.origin.source or f.origin.source_digest != self.origin.source_digest
               or f.origin.byte_start < self.origin.byte_start or f.origin.byte_end > self.origin.byte_end
               for f in self.fields):
            raise ValueError('GSL_TYPED_ORIGIN_MISMATCH')


@dataclass(frozen=True, slots=True)
class TypedProgram:
    analyses: tuple[FrontendAnalysis, ...]
    context: CompileContext
    resolution: ResolutionReport
    declarations: tuple[TypedDeclaration, ...]
    budget: TypecheckBudget
    snapshot: RecordSnapshot | None = None
    imports: TrustedEntityImports | None = None
    external_symbols: tuple[SymbolBinding, ...] = ()

    def __post_init__(self) -> None:
        if (type(self.analyses) is not tuple or not self.analyses
                or any(type(a) is not FrontendAnalysis or not a.ok for a in self.analyses)
                or type(self.context) is not CompileContext or type(self.resolution) is not ResolutionReport
                or not self.resolution.ok or type(self.budget) is not TypecheckBudget
                or type(self.declarations) is not tuple
                or any(type(d) is not TypedDeclaration for d in self.declarations)):
            raise TypeError('GSL_TYPED_PROGRAM_REQUIRED')
        if tuple(d.identity for d in self.declarations) != tuple(d.identity for d in self.resolution.declarations):
            raise ValueError('GSL_TYPED_DECLARATION_POPULATION')
        if self.snapshot is not None and type(self.snapshot) is not RecordSnapshot:
            raise TypeError('GSL_TYPED_SNAPSHOT_REQUIRED')
        if self.imports is not None and type(self.imports) is not TrustedEntityImports:
            raise TypeError('GSL_TYPED_IMPORTS_REQUIRED')
        if type(self.external_symbols) is not tuple or any(type(x) is not SymbolBinding for x in self.external_symbols):
            raise TypeError('GSL_TYPED_SYMBOLS_REQUIRED')

    @property
    def compiled(self) -> bool:
        return False

    @property
    def normatively_admitted(self) -> bool:
        return False


class _TypingFailure(ValueError):
    def __init__(self, code: str, path: str, reason: str):
        super().__init__(reason)
        self.diagnostic = Diagnostic(code, path, 'fixed GSL0 typed field', 'source expression', reason)


class _Meter:
    def __init__(self, budget: TypecheckBudget):
        self.budget, self.nodes = budget, 0

    def spend(self, path: str, depth: int = 0) -> None:
        self.nodes += 1
        if self.nodes > self.budget.max_nodes or depth > self.budget.max_depth:
            raise _TypingFailure('GSL_TYPECHECK_RESOURCE_LIMIT', path, 'bounded source typing exhausted')


def _formula(expr: Expr, context: CompileContext, meter: _Meter, path: str, depth: int = 0) -> TypedFormula:
    meter.spend(path, depth)
    if expr.tag == 'bool' and type(expr.value) is bool:
        return TypedFormula('yes' if expr.value else 'no', expr.span)
    if expr.tag == 'name' and type(expr.value) is str:
        if expr.value in ('yes','no','unknown','conflict'):
            return TypedFormula(expr.value, expr.span)
        if 'v4-atom' not in context.supported_features:
            raise _TypingFailure('GSL_UNSUPPORTED_NORMATIVE_FEATURE', path, 'v4-atom required')
        return TypedFormula('atom', expr.span, atom=expr.value)
    if expr.tag in ('not','and','or'):
        if 'v4-' + expr.tag not in context.supported_features:
            raise _TypingFailure('GSL_UNSUPPORTED_NORMATIVE_FEATURE', path, 'operator not in pinned features')
        args = tuple(_formula(a, context, meter, path + f'.{i}', depth+1) for i,a in enumerate(expr.args))
        return TypedFormula(expr.tag, expr.span, args)
    raise _TypingFailure('GSL_EXPRESSION_TYPE_MISMATCH', path, 'only V4 constants, atoms and boolean connectives are interpreted')


def typecheck_analyses(analyses: tuple[FrontendAnalysis, ...], context: CompileContext, *,
                      snapshot: RecordSnapshot | None = None, imports: TrustedEntityImports | None = None,
                      external_symbols: tuple[SymbolBinding, ...] = (),
                      budget: TypecheckBudget = TypecheckBudget()) -> Result[TypedProgram]:
    """Resolve and type every source declaration or return errors without partial IR.

    Resolver bindings are never accepted as proof of external record existence.
    The 0.1 single-source IR forbids cross-project refs and cross-source items;
    accepted LC04 imports beyond that encoding profile fail explicitly here.
    """
    errors: list[Diagnostic] = []
    try:
        if type(budget) is not TypecheckBudget or type(context) is not CompileContext:
            raise TypeError('GSL_INVALID_TYPECHECK_CONTEXT')
        TypecheckBudget.__post_init__(budget); CompileContext.__post_init__(context)
        if type(analyses) is not tuple or not analyses or any(type(a) is not FrontendAnalysis or not a.ok for a in analyses):
            raise TypeError('GSL_COMPLETE_ANALYSES_REQUIRED')
        if len(analyses) > budget.max_sources or sum(len(a.extraction.source.source_bytes) for a in analyses) > budget.max_bytes:
            raise _TypingFailure('GSL_TYPECHECK_RESOURCE_LIMIT', '$.sources', 'source population/byte limit')
        for registry in (context.type_registry, context.predicate_registry):
            if registry is not None and registry.entries:
                raise _TypingFailure('GSL_UNSUPPORTED_REGISTRY_SEMANTICS', '$.context', 'arbitrary registered term semantics are not implemented in profile 0.1')
        # The declared batch has a fixed source population. No missing pinned file
        # can disappear by requesting strict typing of only its happy subset.
        bundles = {a.extraction.source.source_ref:a.extraction.source for a in analyses}
        if set(bundles) != {p[0] for p in context.expected_sources} or len(bundles) != len(analyses):
            raise _TypingFailure('GSL_SOURCE_SET_INCOMPLETE', '$.sources', 'all context source pins must occur exactly once')
        resolved = resolve_analyses(analyses, context, snapshot=snapshot, imports=imports,
                                    external_symbols=external_symbols, max_nodes=budget.max_nodes)
        if not resolved.ok:
            return Result(diagnostics=resolved.diagnostics)
        meter = _Meter(budget); declarations = []
        for declaration in resolved.declarations:
            bundle = bundles[declaration.source]
            kind = declaration.identity.kind
            path = f'$.{bundle.source_ref.entity.value}.{declaration.identity.entity.value}'
            meter.spend(path)
            allowed = _FIELDS.get(kind)
            if allowed is None:
                raise _TypingFailure('GSL_UNSUPPORTED_DECLARATION', path, 'declaration has no IR profile')
            names = [f.name for f in declaration.syntax.fields]
            for name in sorted(_REQUIRED[kind] - set(names)):
                errors.append(Diagnostic('GSL_MISSING_NORMATIVE_FIELD', path+'.'+name, 'required field', 'absent', 'no implicit normative default'))
            if kind is EntityKind.PROPERTY and (('holds' in names) == ('deferred_semantics' in names)):
                errors.append(Diagnostic('GSL_PROPERTY_SEMANTICS_REQUIRED', path, 'exactly one semantics field', 'source fields', 'interpreted or explicitly deferred'))
            seen = set(); fields = []
            for field in declaration.syntax.fields:
                field_path = path + '.' + field.name + '@' + str(field.expr.span.start)
                meter.spend(field_path)
                try:
                    if field.name not in allowed:
                        raise _TypingFailure('GSL_UNKNOWN_NORMATIVE_FIELD', field_path, 'unregistered field cannot be ignored')
                    if field.name in seen and field.name not in ('requires','verification'):
                        raise _TypingFailure('GSL_DUPLICATE_NORMATIVE_FIELD', field_path, 'singleton field repeated')
                    seen.add(field.name); typ = allowed[field.name]; expr = field.expr
                    origin = SourceOrigin(bundle.source_ref, bundle.expected_digest, expr.span.start, expr.span.end)
                    origin.verify_against(bundle)
                    if typ is IRType.V4:
                        value = _formula(expr, context, meter, field_path)
                    elif typ in (IRType.TEXT, IRType.DEFERRED):
                        if expr.tag != 'string' and not (field.name == 'method' and expr.tag == 'name'):
                            raise _TypingFailure('GSL_EXPRESSION_TYPE_MISMATCH', field_path, 'text literal required')
                        if type(expr.value) is not str or (typ is IRType.DEFERRED and not expr.value):
                            raise _TypingFailure('GSL_EMPTY_DEFERRED_SEMANTICS', field_path, 'nonempty deferred text required')
                        if typ is IRType.DEFERRED and 'deferred-property' not in context.supported_features:
                            raise _TypingFailure('GSL_UNSUPPORTED_NORMATIVE_FEATURE', field_path, 'deferred-property feature required')
                        value = expr.value
                    elif typ is IRType.KIND:
                        if expr.tag != 'name':
                            raise _TypingFailure('GSL_EXPRESSION_TYPE_MISMATCH', field_path, 'nominal enum name required')
                        enum = RelationKind if kind is EntityKind.RELATION else CommitmentKind
                        try:
                            value = enum(expr.value)
                        except (ValueError, TypeError):
                            raise _TypingFailure('GSL_UNKNOWN_ENUM_VARIANT', field_path, 'enum variant not admitted') from None
                    else:
                        links = [r for r in resolved.references if r.declaration == declaration.identity
                                 and r.field == field.name and r.span == expr.span]
                        if len(links) != 1:
                            raise _TypingFailure('GSL_TYPED_REFERENCE_UNRESOLVED', field_path, 'exact whole-field reference required')
                        target = links[0].target
                        if type(target) is ProjectId:
                            target = EntityRef(target, EntityKind.PROJECT, EntityId(target,EntityKind.PROJECT,target.value), bundle.revision)
                        if target.project != context.project:
                            raise _TypingFailure('GSL_IR_PROFILE_FOREIGN_REFERENCE', field_path, 'IR 0.1 cannot encode foreign reference')
                        if typ is IRType.REF:
                            if target.kind is not _REFERENCE_KIND[(kind,field.name)]:
                                raise _TypingFailure('GSL_REFERENCE_KIND_MISMATCH', field_path, 'wrong nominal reference kind')
                            if field.name == 'source_cut' and target != bundle.source_ref:
                                raise _TypingFailure('GSL_IR_PROFILE_FOREIGN_SOURCE', field_path, 'source_cut must match its source bundle')
                            value = target
                        elif typ is IRType.SOURCE_ITEM:
                            if expr.tag != 'call' or expr.value != 'source_item' or len(expr.args) != 2 or target != bundle.source_ref:
                                raise _TypingFailure('GSL_IR_PROFILE_FOREIGN_SOURCE', field_path, 'source item must belong to this IR source')
                            value = SourceItem(target, expr.args[1].value)
                        else:
                            raise _TypingFailure('GSL_UNSUPPORTED_FIELD_TYPE', field_path, 'field not interpreted')
                    fields.append(TypedField(field.name,typ,value,origin))
                except _TypingFailure as exc:
                    if exc.diagnostic.code == 'GSL_TYPECHECK_RESOURCE_LIMIT':
                        raise
                    errors.append(exc.diagnostic)
            if kind is EntityKind.RELATION:
                by_name = {field.name:field for field in fields}
                if 'parent' in by_name and 'child' in by_name:
                    from guardian.domain.clause import ClauseRevision
                    from guardian.domain.references import resolve_entity
                    child = resolve_entity(by_name['child'].value, snapshot, EntityKind.CLAUSE, imports)
                    if (not child.ok or type(child.value.record) is not ClauseRevision
                            or child.value.record.parent_ref != by_name['parent'].value):
                        errors.append(Diagnostic('GSL_RELATION_PARENT_MISMATCH', path,
                            'source-backed clause with exact parent', 'relation',
                            'a relation cannot reassign the parent of an existing clause'))
            origin = SourceOrigin(bundle.source_ref,bundle.expected_digest,
                                  declaration.syntax.span.start,declaration.syntax.span.end)
            declarations.append(TypedDeclaration(declaration.identity, origin, tuple(fields)))
        if errors:
            return Result(diagnostics=tuple(sorted(errors,key=lambda d:(d.path,d.code))))
        return Result(TypedProgram(analyses,context,resolved,tuple(declarations),budget,snapshot,imports,external_symbols))
    except _TypingFailure as exc:
        return Result(diagnostics=tuple(errors)+(exc.diagnostic,))
    except (TypeError,ValueError,AttributeError,RecursionError) as exc:
        return Result(diagnostics=tuple(errors)+(Diagnostic('GSL_TYPECHECK_INVALID_INPUT','$','bounded typed source profile',type(exc).__name__,str(exc) or 'invalid input'),))
