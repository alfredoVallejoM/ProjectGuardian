"""G00-05: objectives are contracts, not tasks or implementation status."""
from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar, TYPE_CHECKING
from .project_view import ReadOnlyEntityView
from .outcomes import Result
if TYPE_CHECKING:
    from .references import TrustedEntityImports
from .record_base import ReferenceUse
from .identity import EntityKind, EntityRef
from .record_base import RecordRevision, text, texts, refs, uses, validate_record


@dataclass(frozen=True, slots=True, kw_only=True)
class ObjectiveRevision(RecordRevision):
    KIND: ClassVar[EntityKind] = EntityKind.OBJECTIVE
    purpose: str
    success_criteria: tuple[str, ...]
    exclusions: tuple[str, ...] = ()
    capability_refs: tuple[EntityRef, ...] = ()
    decision_refs: tuple[EntityRef, ...] = ()

    def __post_init__(self) -> None:
        RecordRevision.__post_init__(self)
        text(self.purpose, 'EMPTY_OBJECTIVE')
        texts(self.success_criteria, 'OBJECTIVE_CRITERIA_REQUIRED', nonempty=True)
        texts(self.exclusions, 'INVALID_EXCLUSIONS')
        refs(self.capability_refs, EntityKind.CAPABILITY, 'INVALID_CAPABILITY_REF')
        refs(self.decision_refs, EntityKind.DECISION, 'INVALID_DECISION_REF')

    def references(self) -> tuple[ReferenceUse, ...]:
        return (RecordRevision.references(self) + uses('$.capability_refs', self.capability_refs)
                + uses('$.decision_refs', self.decision_refs))


def validate_objective(objective: object, view: ReadOnlyEntityView | None = None, *, grants: TrustedEntityImports | None = None) -> Result[ObjectiveRevision]:
    return validate_record(objective, ObjectiveRevision, view, grants=grants)
