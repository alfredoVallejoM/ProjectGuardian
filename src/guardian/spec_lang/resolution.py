"""LC04 reference-linking slice, using Guardian's nominal identities.

Two passes over pinned LC03 outputs: declarations first, then reference uses.
This is not a typechecker/lowerer and never returns COMPILED. Imports of actual
B03 records reuse the domain resolver and exact material source grants. Import
syntax, arbitrary namespace modules and dependency-order compilation are not
implemented by pretending that externally supplied descriptors are a parser.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from guardian.domain.identity import EntityId, EntityKind, EntityRef, ProjectId, RevisionId
from guardian.domain.outcomes import Diagnostic
from guardian.domain.references import RecordSnapshot, TrustedEntityImports, resolve_entity
from .contract import CompileContext, SymbolBinding, verify_source_context
from .syntax import Expr, FrontendAnalysis, ParsedDeclaration, validate_analysis_source
from .text import TextSpan

REFERENCE_CALLS = MappingProxyType({
    'source': EntityKind.SOURCE, 'scope': EntityKind.SCOPE,
    'objective': EntityKind.OBJECTIVE, 'capability': EntityKind.CAPABILITY,
    'property': EntityKind.PROPERTY, 'obligation': EntityKind.OBLIGATION,
    'verification': EntityKind.VERIFICATION, 'verification_ref': EntityKind.VERIFICATION,
    'relation': EntityKind.RELATION, 'clause': EntityKind.CLAUSE,
    'campaign': EntityKind.CAMPAIGN, 'architecture': EntityKind.ARCHITECTURE,
})
# Field-specific reference kinds are the same versioned IR contract, not a
# second independently mutable normative registry. Other typing remains LC05.
from .ir import _REFERENCE_KIND


class ResolutionStatus(str, Enum):
    REFERENCES_RESOLVED = 'REFERENCES_RESOLVED'
    REJECTED = 'REJECTED'


@dataclass(frozen=True, slots=True)
class LinkedReference:
    source: EntityRef
    declaration: EntityRef
    field: str
    span: TextSpan
    target: EntityRef | ProjectId
    basis: str

    def __post_init__(self) -> None:
        if type(self.source) is not EntityRef or self.source.kind is not EntityKind.SOURCE:
            raise TypeError('LINKED_SOURCE_REQUIRED')
        if type(self.declaration) is not EntityRef or type(self.target) not in (EntityRef, ProjectId):
            raise TypeError('LINKED_NOMINAL_REFERENCE_REQUIRED')
        if self.declaration.project != self.source.project:
            raise ValueError('LINKED_DECLARATION_PROJECT_MISMATCH')
        if type(self.field) is not str or not self.field or type(self.span) is not TextSpan:
            raise TypeError('LINKED_FIELD_ORIGIN_REQUIRED')
        if self.basis not in ('PINNED_CONTEXT', 'PROJECT_CONTEXT', 'SOURCE_PIN_ONLY',
                              'LOCAL_DECLARATION', 'PINNED_SOURCE', 'IMPORTED_RECORD', 'SNAPSHOT_RECORD'):
            raise ValueError('UNKNOWN_REFERENCE_BASIS')


@dataclass(frozen=True, slots=True)
class LinkedDeclaration:
    identity: EntityRef
    source: EntityRef
    syntax: ParsedDeclaration

    def __post_init__(self) -> None:
        if type(self.identity) is not EntityRef or type(self.source) is not EntityRef or type(self.syntax) is not ParsedDeclaration:
            raise TypeError('LINKED_DECLARATION_REQUIRED')
        if (self.source.kind is not EntityKind.SOURCE or self.identity.project != self.source.project
                or self.identity.kind.value != self.syntax.kind):
            raise ValueError('LINKED_DECLARATION_IDENTITY_MISMATCH')


@dataclass(frozen=True, slots=True)
class ResolutionReport:
    status: ResolutionStatus
    declarations: tuple[LinkedDeclaration, ...]
    references: tuple[LinkedReference, ...]
    diagnostics: tuple[Diagnostic, ...]
    unchecked_source_items: tuple[tuple[EntityRef, str], ...] = ()

    def __post_init__(self) -> None:
        if type(self.status) is not ResolutionStatus:
            raise TypeError('RESOLUTION_STATUS_REQUIRED')
        for seq, typ in ((self.declarations, LinkedDeclaration), (self.references, LinkedReference), (self.diagnostics, Diagnostic)):
            if type(seq) is not tuple or any(type(x) is not typ for x in seq):
                raise TypeError('RESOLUTION_RESULT_NOT_IMMUTABLE')
        if (type(self.unchecked_source_items) is not tuple or any(type(pair) is not tuple or len(pair) != 2
                or type(pair[0]) is not EntityRef or pair[0].kind is not EntityKind.SOURCE
                or type(pair[1]) is not str or not pair[1] for pair in self.unchecked_source_items)):
            raise TypeError('SOURCE_ITEM_RESULT_NOT_IMMUTABLE')
        owners = {d.identity: d for d in self.declarations}
        if len(owners) != len(self.declarations):
            raise ValueError('RESOLUTION_DUPLICATE_IDENTITY')
        for link in self.references:
            owner = owners.get(link.declaration)
            if (owner is None or link.source != owner.source or link.span.start < owner.syntax.span.start
                    or link.span.end > owner.syntax.span.end):
                raise ValueError('RESOLUTION_REFERENCE_ORIGIN_MISMATCH')
        if (self.status is ResolutionStatus.REJECTED) != bool(self.diagnostics):
            raise ValueError('RESOLUTION_STATUS_DIAGNOSTIC_MISMATCH')

    @property
    def ok(self) -> bool:
        return self.status is ResolutionStatus.REFERENCES_RESOLVED

    @property
    def compiled(self) -> bool:
        return False

    @property
    def typechecked(self) -> bool:
        return False


def resolve_analyses(analyses: tuple[FrontendAnalysis, ...], context: CompileContext,
                     *, snapshot: RecordSnapshot | None = None,
                     imports: TrustedEntityImports | None = None,
                     external_symbols: tuple[SymbolBinding, ...] = (),
                     max_nodes: int = 10000) -> ResolutionReport:
    errors: list[Diagnostic] = []
    declarations: list[LinkedDeclaration] = []
    linked: list[LinkedReference] = []
    unchecked: list[tuple[EntityRef, str]] = []

    def error(code: str, path: str, reason: str) -> None:
        errors.append(Diagnostic(code, path, 'pinned unambiguous typed reference', 'syntax', reason))

    def done() -> ResolutionReport:
        return ResolutionReport(ResolutionStatus.REJECTED if errors else ResolutionStatus.REFERENCES_RESOLVED,
            tuple(declarations), tuple(linked), tuple(sorted(errors, key=lambda d: (d.path, d.code, d.reason))), tuple(unchecked))

    if (type(analyses) is not tuple or not analyses or any(type(a) is not FrontendAnalysis or not a.ok for a in analyses)
            or type(context) is not CompileContext or type(max_nodes) is not int or max_nodes < 1):
        error('GSL_RESOLUTION_INPUT_INVALID', '$', 'complete LC03 analyses and explicit context required')
        return done()
    if snapshot is not None and (type(snapshot) is not RecordSnapshot or snapshot.project_id != context.project):
        error('GSL_SNAPSHOT_PROJECT_MISMATCH', '$.snapshot', 'snapshot is not local')
        return done()
    if imports is not None and type(imports) is not TrustedEntityImports:
        error('GSL_IMPORT_CONTEXT_INVALID', '$.imports', 'untrusted import descriptor type')
        return done()
    if (type(external_symbols) is not tuple or any(type(b) is not SymbolBinding or b.identity.project == context.project for b in external_symbols)
            or len(set(external_symbols)) != len(external_symbols)):
        error('GSL_EXTERNAL_BINDINGS_INVALID', '$.external_symbols', 'unique foreign pinned bindings required')
        return done()
    all_bindings = context.symbols + external_symbols
    if len(analyses) + sum(len(u.ast.declarations) for a in analyses for u in a.units) + len(all_bindings) > max_nodes:
        error('GSL_RESOLUTION_RESOURCE_LIMIT', '$', 'declaration/source/symbol budget exhausted')
        return done()
    pins = dict(context.expected_sources)
    table: dict[tuple[EntityKind, str], set[EntityRef]] = {}
    origins: dict[EntityRef, EntityRef] = {}
    for binding in all_bindings:
        table.setdefault((binding.identity.kind, binding.name), set()).add(binding.identity)
        table.setdefault((binding.identity.kind, binding.identity.entity.value), set()).add(binding.identity)
    seen_sources = set()
    seen_labels = set()
    for analysis in analyses:
        try:
            source_check = validate_analysis_source(analysis, context)
            if not source_check.ok:
                errors.extend(source_check.diagnostics)
                continue
            analysis = source_check.value
            FrontendAnalysis.__post_init__(analysis)
            for unit in analysis.units:
                type(unit).__post_init__(unit)
            source = analysis.extraction.source
            if source.source_ref in seen_sources:
                error('GSL_DUPLICATE_SOURCE_INPUT', '$.sources', 'each source bundle occurs once')
                continue
            seen_sources.add(source.source_ref)
            valid = verify_source_context(source, context)
            if not valid.ok:
                errors.extend(valid.diagnostics)
                continue
            for unit in analysis.units:
                for declaration in unit.ast.declarations:
                    kind = EntityKind(declaration.kind)
                    explicit = [b for b in context.symbols if b.identity.kind is kind and b.name == declaration.name]
                    if explicit:
                        if len(explicit) != 1 or explicit[0].declared_source != source.source_ref:
                            error('GSL_DECLARATION_BINDING_MISMATCH', str(declaration.span.start), 'binding belongs to another source')
                            continue
                        identity = explicit[0].identity
                    elif kind is EntityKind.SOURCE:
                        candidates = [s for s in pins if s.entity.value == declaration.name]
                        if len(candidates) != 1:
                            error('GSL_SOURCE_NOT_PINNED', str(declaration.span.start), 'source declaration needs an exact context pin')
                            continue
                        identity = candidates[0]
                    else:
                        identity = EntityRef(context.project, kind,
                            EntityId(context.project, kind, declaration.name), source.revision)
                    if kind is EntityKind.SOURCE and identity not in pins:
                        error('GSL_SOURCE_NOT_PINNED', str(declaration.span.start), 'source symbol does not supply a material pin')
                        continue
                    key = (kind, declaration.name)
                    if key in seen_labels:
                        error('GSL_DUPLICATE_DECLARATION', str(declaration.span.start), 'namespace has multiple declarations')
                        continue
                    if identity in origins:
                        error('GSL_DUPLICATE_LOGICAL_ID', str(declaration.span.start), 'multiple labels collapse to one identity')
                        continue
                    seen_labels.add(key)
                    origins[identity] = source.source_ref
                    declarations.append(LinkedDeclaration(identity, source.source_ref, declaration))
                    table.setdefault(key, set()).add(identity)
        except (TypeError, ValueError, AttributeError) as exc:
            error('GSL_RESOLUTION_SOURCE_INVALID', '$.source', str(exc))
    if errors:
        return done()
    nodes = 0
    for declaration in declarations:
        for field in declaration.syntax.fields:
            expected = _REFERENCE_KIND.get((declaration.identity.kind, field.name))
            expression = field.expr
            if expected is not None:
                actual = (EntityKind.PROJECT if expression.tag == 'call' and expression.value == 'project'
                          else REFERENCE_CALLS.get(expression.value) if expression.tag == 'call'
                          else EntityKind.SOURCE if expression.tag == 'name' and expression.value == 'context' else None)
                if actual is not expected:
                    error('GSL_REFERENCE_KIND_MISMATCH', f'{declaration.syntax.name}.{field.name}', 'reference expression has wrong field kind')
            stack = [expression]
            while stack:
                node = stack.pop(); nodes += 1
                if nodes > max_nodes:
                    error('GSL_RESOLUTION_RESOURCE_LIMIT', '$', 'node budget exhausted; result is not partial success')
                    return done()
                path = f'$.{declaration.syntax.name}.{field.name}@{node.span.start}'
                if node.tag == 'name' and node.value == 'context' and expected is EntityKind.SOURCE:
                    linked.append(LinkedReference(declaration.source, declaration.identity, field.name,
                                                  node.span, declaration.source, 'PINNED_CONTEXT'))
                if node.tag != 'call':
                    stack.extend(reversed(node.args)); continue
                if node.value not in REFERENCE_CALLS and node.value not in ('source_item', 'project'):
                    # Predicate calls are NOT executed or claimed typechecked here.
                    stack.extend(reversed(node.args)); continue
                if any(a.tag != 'string' or type(a.value) is not str for a in node.args):
                    error('GSL_REFERENCE_ARGUMENT_INVALID', path, 'reference arguments must be string literals'); continue
                args = tuple(a.value for a in node.args)
                if node.value == 'project':
                    if args != (context.project.value,):
                        error('GSL_FOREIGN_PROJECT', path, 'project reference must select this project'); continue
                    linked.append(LinkedReference(declaration.source, declaration.identity, field.name, node.span, context.project, 'PROJECT_CONTEXT'))
                    continue
                if node.value == 'source_item':
                    if len(args) != 2 or not args[1]:
                        error('GSL_SOURCE_ITEM_INVALID', path, 'source item needs source name and item identity'); continue
                    targets = [s for s in pins if s.entity.value == args[0]]
                    if len(targets) != 1:
                        error('GSL_SOURCE_NOT_PINNED', path, 'source item has no unique pinned source'); continue
                    linked.append(LinkedReference(declaration.source, declaration.identity, field.name, node.span, targets[0], 'SOURCE_PIN_ONLY'))
                    unchecked.append((targets[0], args[1])); continue
                kind = REFERENCE_CALLS[node.value]
                if len(args) != 1:
                    error('GSL_REFERENCE_ARITY', path, 'this profile uses one label; revisions and imports are pinned in bindings'); continue
                try:
                    label = args[0]
                    candidates = table.get((kind, label), set())
                    if kind is EntityKind.SOURCE:
                        candidates = candidates | {s for s in pins if s.entity.value == label}
                    if len(candidates) > 1:
                        error('GSL_AMBIGUOUS_REFERENCE', path, 'multiple pinned revisions; choose one explicitly'); continue
                    target = next(iter(candidates)) if candidates else None
                    if target is not None and target in origins:
                        basis = 'LOCAL_DECLARATION'
                    elif target is not None and kind is EntityKind.SOURCE and target in pins:
                        basis = 'PINNED_SOURCE'
                    else:
                        if target is None or snapshot is None:
                            error('GSL_REFERENCE_NOT_FOUND', path, 'no exact declaration or record; no latest fallback'); continue
                        resolved = resolve_entity(target, snapshot, kind, imports, path=path)
                        if not resolved.ok:
                            errors.extend(resolved.diagnostics); continue
                        matching_bindings = [b for b in all_bindings if b.identity == target
                            and (b.name == label or b.identity.entity.value == label)]
                        if any(b.declared_source not in resolved.value.record.source_refs for b in matching_bindings):
                            error('GSL_SYMBOL_ORIGIN_MISMATCH', path, 'symbol provenance does not match the record source')
                            continue
                        basis = 'IMPORTED_RECORD' if resolved.value.imported else 'SNAPSHOT_RECORD'
                    linked.append(LinkedReference(declaration.source, declaration.identity, field.name, node.span, target, basis))
                except (TypeError, ValueError) as exc:
                    error('GSL_REFERENCE_IDENTITY_INVALID', path, str(exc))
    return done()
