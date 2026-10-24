"""G00-B03 normative architecture descriptors, not an observed import graph."""
from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar, TYPE_CHECKING
from .project_view import ReadOnlyEntityView
from .outcomes import Result
if TYPE_CHECKING:
    from .references import TrustedEntityImports
from .identity import EntityKind
from .capability import SemanticOwner
from .record_base import RecordRevision, text, texts, validate_record


@dataclass(frozen=True, slots=True)
class Component:
    name: str
    owner: SemanticOwner
    interfaces: tuple[str, ...]

    def __post_init__(self) -> None:
        text(self.name, 'COMPONENT_NAME_REQUIRED')
        if type(self.owner) is not SemanticOwner:
            raise TypeError('SEMANTIC_OWNER_REQUIRED')
        texts(self.interfaces, 'COMPONENT_INTERFACES_REQUIRED', nonempty=True)


@dataclass(frozen=True, slots=True, kw_only=True)
class ArchitectureRevision(RecordRevision):
    KIND: ClassVar[EntityKind] = EntityKind.ARCHITECTURE
    components: tuple[Component, ...]
    allowed_dependencies: tuple[tuple[str, str], ...] = ()
    required_dependencies: tuple[tuple[str, str], ...] = ()
    forbidden_dependencies: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        RecordRevision.__post_init__(self)
        if type(self.components) is not tuple or not self.components or any(type(x) is not Component for x in self.components):
            raise TypeError('COMPONENTS_REQUIRED')
        names = [c.name for c in self.components]
        if len(names) != len(set(names)):
            raise ValueError('DUPLICATE_OWNER')
        if any(c.owner.project != self.identity.project for c in self.components):
            raise ValueError('FOREIGN_COMPONENT_OWNER')
        for edges in (self.allowed_dependencies, self.required_dependencies, self.forbidden_dependencies):
            if type(edges) is not tuple:
                raise TypeError('DEPENDENCIES_MUST_BE_IMMUTABLE')
            if any(type(e) is not tuple or len(e) != 2 or any(type(x) is not str or x not in names for x in e) for e in edges):
                raise ValueError('INVALID_DEPENDENCY_RULE')
            if len(set(edges)) != len(edges):
                raise ValueError('DUPLICATE_DEPENDENCY_RULE')
        if set(self.forbidden_dependencies) & (set(self.allowed_dependencies) | set(self.required_dependencies)):
            raise ValueError('CONFLICTING_DEPENDENCY_RULE')
        if not set(self.required_dependencies) <= set(self.allowed_dependencies):
            raise ValueError('REQUIRED_DEPENDENCY_NOT_ALLOWED')


def validate_architecture_contract(architecture: object, view: ReadOnlyEntityView | None = None, *, grants: TrustedEntityImports | None = None) -> Result[ArchitectureRevision]:
    return validate_record(architecture, ArchitectureRevision, view, grants=grants)
