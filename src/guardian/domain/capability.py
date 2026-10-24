"""G00-05 capability and semantic ownership, independent of implementation paths."""
from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar, TYPE_CHECKING
from .project_view import ReadOnlyEntityView
from .outcomes import Result
if TYPE_CHECKING:
    from .references import TrustedEntityImports
from .record_base import ReferenceUse
from .identity import EntityKind, EntityRef, ProjectId
from .record_base import RecordRevision, text, texts, refs, uses, validate_record


@dataclass(frozen=True, slots=True)
class SemanticOwner:
    project: ProjectId
    name: str

    def __post_init__(self) -> None:
        if type(self.project) is not ProjectId:
            raise TypeError('OWNER_PROJECT_REQUIRED')
        text(self.name, 'MISSING_SEMANTIC_OWNER')


@dataclass(frozen=True, slots=True, kw_only=True)
class CapabilityRevision(RecordRevision):
    KIND: ClassVar[EntityKind] = EntityKind.CAPABILITY
    owner: SemanticOwner
    behavior: str
    input_contracts: tuple[str, ...]
    output_contracts: tuple[str, ...]
    contract_version: str
    property_refs: tuple[EntityRef, ...]
    objective_refs: tuple[EntityRef, ...] = ()
    exclusions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        RecordRevision.__post_init__(self)
        if type(self.owner) is not SemanticOwner or self.owner.project != self.identity.project:
            raise ValueError('INVALID_CAPABILITY_OWNER')
        text(self.behavior, 'INVALID_CAPABILITY_CONTRACT')
        text(self.contract_version, 'CONTRACT_VERSION_REQUIRED')
        texts(self.input_contracts, 'INPUT_CONTRACT_REQUIRED', nonempty=True)
        texts(self.output_contracts, 'OUTPUT_CONTRACT_REQUIRED', nonempty=True)
        refs(self.property_refs, EntityKind.PROPERTY, 'PROPERTY_REF_REQUIRED', nonempty=True)
        refs(self.objective_refs, EntityKind.OBJECTIVE, 'INVALID_OBJECTIVE_REF')
        texts(self.exclusions, 'INVALID_EXCLUSIONS')

    def references(self) -> tuple[ReferenceUse, ...]:
        return (RecordRevision.references(self) + uses('$.property_refs', self.property_refs)
                + uses('$.objective_refs', self.objective_refs))


def validate_capability(capability: object, view: ReadOnlyEntityView, *, grants: TrustedEntityImports | None = None) -> Result[CapabilityRevision]:
    return validate_record(capability, CapabilityRevision, view, grants=grants)
