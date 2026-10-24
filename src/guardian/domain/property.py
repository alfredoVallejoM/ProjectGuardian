"""G00-05 properties: hypotheses and guarantee, never an executed test."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, TYPE_CHECKING
from .project_view import ReadOnlyEntityView
from .outcomes import Result
if TYPE_CHECKING:
    from .references import TrustedEntityImports
from .record_base import ReferenceUse
from .identity import EntityKind, EntityRef
from .record_base import RecordRevision, text, texts, refs, uses, validate_record


class AssertionKind(str, Enum):
    REQUIRED = 'required'
    PROPOSED = 'proposed'
    OBSERVED = 'observed'


@dataclass(frozen=True, slots=True, kw_only=True)
class PropertyRevision(RecordRevision):
    KIND: ClassVar[EntityKind] = EntityKind.PROPERTY
    statement: str
    hypotheses: tuple[str, ...]
    guarantee: str
    assertion_kind: AssertionKind
    forbidden_claims: tuple[str, ...] = ()
    verification_spec_refs: tuple[EntityRef, ...] = ()

    def __post_init__(self) -> None:
        RecordRevision.__post_init__(self)
        text(self.statement, 'EMPTY_STATEMENT')
        texts(self.hypotheses, 'INVALID_HYPOTHESIS')
        text(self.guarantee, 'EMPTY_GUARANTEE')
        if type(self.assertion_kind) is not AssertionKind:
            raise TypeError('ASSERTION_KIND_REQUIRED')
        texts(self.forbidden_claims, 'INVALID_FORBIDDEN_CLAIMS')
        refs(self.verification_spec_refs, EntityKind.VERIFICATION, 'INVALID_VERIFICATION_REF')

    def references(self) -> tuple[ReferenceUse, ...]:
        return RecordRevision.references(self) + uses('$.verification_spec_refs', self.verification_spec_refs)


def validate_property(property: object, view: ReadOnlyEntityView | None = None, *, grants: TrustedEntityImports | None = None) -> Result[PropertyRevision]:
    return validate_record(property, PropertyRevision, view, grants=grants)
