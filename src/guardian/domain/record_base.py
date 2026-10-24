"""Shared immutable contracts for G00-B03, not evidence or admission.

References to scope/authority/verification are explicit dependency contracts;
this module does not implement their evaluators or grant authority to a label.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import ClassVar, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from .references import TrustedEntityImports

from .identity import EntityKind, EntityRef, ProjectId
from .outcomes import DecisionStatus, Diagnostic, Result
from .project_view import ReadOnlyEntityView


def text(value: object, code: str) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(code)


def texts(values: object, code: str, *, nonempty: bool = False) -> None:
    if type(values) is not tuple or (nonempty and not values):
        raise ValueError(code)
    for value in values:
        text(value, code)
    if len(set(values)) != len(values):
        raise ValueError(code + '_DUPLICATE')


def ref(value: object, kinds: EntityKind | tuple[EntityKind, ...], code: str) -> None:
    permitted = (kinds,) if isinstance(kinds, EntityKind) else kinds
    if type(value) is not EntityRef or value.kind not in permitted:
        raise TypeError(code)


def refs(values: object, kinds: EntityKind | tuple[EntityKind, ...], code: str,
         *, nonempty: bool = False) -> None:
    if type(values) is not tuple or (nonempty and not values):
        raise TypeError(code)
    for value in values:
        ref(value, kinds, code)
    if len(set(values)) != len(values):
        raise ValueError(code + '_DUPLICATE')


@dataclass(frozen=True, slots=True)
class ReferenceUse:
    """A field-specific reference; resolution never infers kind from its name."""
    path: str
    target: EntityRef
    expected_kind: EntityKind

    def __post_init__(self) -> None:
        text(self.path, 'REFERENCE_PATH_REQUIRED')
        if type(self.target) is not EntityRef or type(self.expected_kind) is not EntityKind:
            raise TypeError('TYPED_REFERENCE_USE_REQUIRED')
        if self.target.kind is not self.expected_kind:
            raise TypeError('WRONG_REFERENCE_KIND')


def uses(path: str, values: tuple[EntityRef, ...]) -> tuple[ReferenceUse, ...]:
    return tuple(ReferenceUse(f'{path}[{i}]', v, v.kind) for i, v in enumerate(values))


@dataclass(frozen=True, slots=True, kw_only=True)
class RecordRevision:
    identity: EntityRef
    source_refs: tuple[EntityRef, ...]
    scope_ref: EntityRef
    authority_ref: EntityRef | None = None
    declared_status: DecisionStatus = DecisionStatus.PROPOSED
    KIND: ClassVar[EntityKind | None] = None

    def __post_init__(self) -> None:
        if self.KIND is None:
            raise TypeError('ABSTRACT_RECORD_REVISION')
        ref(self.identity, self.KIND, 'RECORD_KIND_MISMATCH')
        refs(self.source_refs, EntityKind.SOURCE, 'RECORD_SOURCE_REQUIRED', nonempty=True)
        ref(self.scope_ref, EntityKind.SCOPE, 'RECORD_SCOPE_REQUIRED')
        if self.authority_ref is not None:
            ref(self.authority_ref, (EntityKind.DECISION, EntityKind.CONSTITUTION),
                'RECORD_AUTHORITY_KIND')
        if type(self.declared_status) is not DecisionStatus:
            raise TypeError('DECISION_AXIS_REQUIRED')
        if self.declared_status is DecisionStatus.APPROVED and self.authority_ref is None:
            raise ValueError('AUTHORITY_REF_REQUIRED')

    def references(self) -> tuple[ReferenceUse, ...]:
        result = uses('$.source_refs', self.source_refs)
        result += (ReferenceUse('$.scope_ref', self.scope_ref, EntityKind.SCOPE),)
        if self.authority_ref is not None:
            result += (ReferenceUse('$.authority_ref', self.authority_ref, self.authority_ref.kind),)
        return result

    @property
    def normatively_admitted(self) -> bool:
        # A serialized APPROVED label is an assertion, never an admission event.
        return False


TRecord = TypeVar('TRecord', bound=RecordRevision)


def validate_record(record: object, expected: type[TRecord],
                    view: ReadOnlyEntityView | None = None, *, grants: TrustedEntityImports | None = None) -> Result[TRecord]:
    """Shape and exact-reference membership only; never authenticates approval.

    Without a view only shape is checked. A view supplies anchors for future
    scope/authority consumers, not evidence that those contracts are satisfied.
    The full content resolver reports anchors as CONTENT_UNAVAILABLE.
    """
    if type(record) is not expected:
        return Result(diagnostics=(Diagnostic('WRONG_RECORD_TYPE', '$', expected.__name__,
                                             type(record).__name__, 'wrong nominal record'),))
    try:
        expected.__post_init__(record)
        links = record.references()
    except (TypeError, ValueError) as exc:
        return Result(diagnostics=(Diagnostic(str(exc) if re.fullmatch(r'[A-Z][A-Z0-9_]*', str(exc)) else 'INVALID_RECORD', '$', expected.__name__,
                                             type(record).__name__, str(exc)),))
    if view is None:
        return Result(record)
    if not isinstance(view, ReadOnlyEntityView) or view.project_id != record.identity.project:
        return Result(diagnostics=(Diagnostic('WRONG_PROJECT', '$.view', 'same explicit project',
                                             type(view).__name__, 'snapshot mismatch'),))
    errors = []
    for link in links:
        if link.target.project != view.project_id:
            from .references import RecordSnapshot, resolve_entity
            if type(view) is RecordSnapshot and link.expected_kind is not EntityKind.SOURCE:
                resolved = resolve_entity(link.target, view, link.expected_kind, grants, path=link.path)
                errors.extend(resolved.diagnostics)
                continue
            code = 'FORBIDDEN_CROSS_PROJECT_REF'
        elif link.expected_kind is EntityKind.SOURCE:
            code = None if view.contains_source(link.target) else 'UNKNOWN_SOURCE'
        else:
            code = None if view.contains_entity(link.target) else 'ORPHAN_REFERENCE'
        if code:
            errors.append(Diagnostic(code, link.path, link.expected_kind.value, 'EntityRef',
                                     'reference absent from exact local snapshot'))
    return Result(diagnostics=tuple(errors)) if errors else Result(record)
