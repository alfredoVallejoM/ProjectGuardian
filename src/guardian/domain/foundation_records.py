"""Pinned record adapters for existing project and source models.

The underlying models remain the semantic owners; these adapters only make
actual bodies available through the common exact-content snapshot.
"""
from dataclasses import dataclass
from typing import ClassVar
from .identity import EntityKind
from .project import SourcePolicy, ProjectDefinition
from .source import SourceUniverseRevision
from .record_base import RecordRevision, ReferenceUse, uses


@dataclass(frozen=True, slots=True, kw_only=True)
class SourcePolicyRevision(RecordRevision):
    KIND: ClassVar[EntityKind] = EntityKind.SOURCE_POLICY
    policy: SourcePolicy

    def __post_init__(self):
        RecordRevision.__post_init__(self)
        if type(self.policy) is not SourcePolicy:
            raise TypeError('SOURCE_POLICY_BODY_REQUIRED')
        SourcePolicy.__post_init__(self.policy)
        if self.policy.project != self.identity.project or self.policy.revision != self.identity.revision:
            raise ValueError('POLICY_BODY_IDENTITY_MISMATCH')


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceUniverseRecord(RecordRevision):
    KIND: ClassVar[EntityKind] = EntityKind.SOURCE_UNIVERSE
    universe: SourceUniverseRevision

    def __post_init__(self):
        RecordRevision.__post_init__(self)
        if type(self.universe) is not SourceUniverseRevision or self.universe.identity != self.identity:
            raise ValueError('UNIVERSE_BODY_IDENTITY_MISMATCH')
        SourceUniverseRevision.__post_init__(self.universe)

    def references(self) -> tuple[ReferenceUse, ...]:
        links = list(RecordRevision.references(self) + uses('$.universe.included', self.universe.included))
        for index, entry in enumerate(self.universe.entries):
            links.append(ReferenceUse(f'$.universe.entries[{index}].cut', entry.cut.ref, EntityKind.SOURCE))
            if entry.baseline_ref is not None:
                links.append(ReferenceUse(f'$.universe.entries[{index}].baseline_ref', entry.baseline_ref, EntityKind.SOURCE))
        for index, exclusion in enumerate(self.universe.excluded):
            links.append(ReferenceUse(f'$.universe.excluded[{index}].cut', exclusion.cut, EntityKind.SOURCE))
            links.append(ReferenceUse(f'$.universe.excluded[{index}].approval_ref', exclusion.approval_ref, EntityKind.DECISION))
        # MissingSource is a locator/reason, not an invented resolvable SourceRef.
        # Its absence remains in validate_source_universe / coverage diagnostics.
        return tuple(links)


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectRevision(RecordRevision):
    KIND: ClassVar[EntityKind] = EntityKind.PROJECT
    definition: ProjectDefinition

    def __post_init__(self):
        RecordRevision.__post_init__(self)
        if type(self.definition) is not ProjectDefinition or self.definition.project_id != self.identity.project:
            raise ValueError('PROJECT_BODY_IDENTITY_MISMATCH')
        ProjectDefinition.__post_init__(self.definition)

    def references(self) -> tuple[ReferenceUse, ...]:
        return RecordRevision.references(self) + uses('$.definition',
            (self.definition.constitution_ref,self.definition.source_policy_ref))
