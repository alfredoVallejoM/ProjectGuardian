"""G00-02: immutable project identity, source policy and declarative storage.

This is a pure model: repo handles and grant descriptors are *claims* supplied by
callers. Authentication, repo access and Git persistence belong to G07/G09.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from .identity import EntityKind, EntityRef, ProjectId, RevisionId
from .outcomes import Diagnostic, Result

_PART = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z", re.ASCII)
_PROVIDER = re.compile(r"[a-z][a-z0-9-]{1,31}\Z", re.ASCII)
_AUTHORITY_CLASSES = frozenset({'source','constitution','contract','evidence','decision'})


@dataclass(frozen=True, slots=True)
class RepositoryId:
    provider: str
    slug: str

    def __post_init__(self) -> None:
        if type(self.provider) is not str or _PROVIDER.fullmatch(self.provider) is None:
            raise ValueError('INVALID_REPOSITORY_PROVIDER')
        if (type(self.slug) is not str or len(self.slug)>240 or not self.slug
                or any(part in ('', '.', '..') or _PART.fullmatch(part) is None
                       for part in self.slug.split('/'))):
            raise ValueError('INVALID_REPOSITORY_ID')


class StorageMode(str, Enum):
    EMBEDDED = 'embedded'
    SIDECAR = 'sidecar'
    FEDERATED = 'federated'


@dataclass(frozen=True, slots=True)
class StorageDescriptor:
    mode: StorageMode
    authority_repository: RepositoryId
    repositories: tuple[RepositoryId, ...]
    authority_by_class: tuple[tuple[str, RepositoryId], ...] = ()

    def __post_init__(self) -> None:
        if (type(self.mode) is not StorageMode or not any(self.mode is mode for mode in StorageMode)
                or type(self.authority_repository) is not RepositoryId):
            raise TypeError('INVALID_STORAGE_DESCRIPTOR')
        if (type(self.repositories) is not tuple or not self.repositories
                or any(type(r) is not RepositoryId for r in self.repositories)):
            raise ValueError('INVALID_STORAGE_REPOSITORIES')
        RepositoryId.__post_init__(self.authority_repository)
        for repository in self.repositories:
            RepositoryId.__post_init__(repository)
        if len(set(self.repositories)) != len(self.repositories):
            raise ValueError('INVALID_STORAGE_REPOSITORIES')
        if type(self.authority_by_class) is not tuple:
            raise TypeError('INVALID_STORAGE_AUTHORITY_MAP')
        classes=set()
        for item in self.authority_by_class:
            if (type(item) is not tuple or len(item)!=2 or type(item[0]) is not str or item[0] not in _AUTHORITY_CLASSES
                    or type(item[1]) is not RepositoryId or item[0] in classes):
                raise ValueError('AMBIGUOUS_AUTHORITY')
            RepositoryId.__post_init__(item[1])
            classes.add(item[0])
        if self.mode is StorageMode.EMBEDDED:
            if self.repositories!=(self.authority_repository,) or self.authority_by_class:
                raise ValueError('AMBIGUOUS_EMBEDDED_AUTHORITY')
        elif self.mode is StorageMode.SIDECAR:
            if self.authority_repository in self.repositories or self.authority_by_class:
                raise ValueError('AMBIGUOUS_SIDECAR_AUTHORITY')
        elif self.mode is StorageMode.FEDERATED:
            if len(self.repositories)<2 or self.authority_repository not in self.repositories:
                raise ValueError('INVALID_FEDERATED_REPOSITORIES')
            if classes!=_AUTHORITY_CLASSES or any(r not in self.repositories for _,r in self.authority_by_class):
                raise ValueError('FEDERATED_AUTHORITY_INCOMPLETE')


def validate_storage_mode(descriptor: object) -> Result[StorageDescriptor]:
    try:
        if type(descriptor) is not StorageDescriptor:
            raise TypeError('EXACT_STORAGE_DESCRIPTOR_REQUIRED')
        StorageDescriptor.__post_init__(descriptor)
        return Result(descriptor)
    except (TypeError, ValueError, AttributeError) as exc:
        return Result(diagnostics=(Diagnostic('UNSUPPORTED_STORAGE_MODE','$.storage',
            'validated StorageDescriptor','StorageDescriptor' if type(descriptor) is StorageDescriptor else 'non-StorageDescriptor',str(exc) or 'invalid storage'),))


@dataclass(frozen=True, slots=True)
class SourcePolicy:
    project: ProjectId
    revision: RevisionId
    allow_repositories: tuple[RepositoryId, ...]

    def __post_init__(self) -> None:
        if type(self.project) is not ProjectId or type(self.revision) is not RevisionId:
            raise TypeError('source policy needs pinned project and revision')
        ProjectId.__post_init__(self.project)
        RevisionId.__post_init__(self.revision)
        if (type(self.allow_repositories) is not tuple or not self.allow_repositories
                or any(type(r) is not RepositoryId for r in self.allow_repositories)):
            raise ValueError('INVALID_SOURCE_POLICY')
        for repository in self.allow_repositories:
            RepositoryId.__post_init__(repository)
        if len(set(self.allow_repositories)) != len(self.allow_repositories):
            raise ValueError('INVALID_SOURCE_POLICY')


@dataclass(frozen=True, slots=True)
class ProjectDefinition:
    project_id: ProjectId
    display_name: str
    constitution_ref: EntityRef
    source_policy_ref: EntityRef
    source_policy: SourcePolicy
    storage: StorageDescriptor
    description: str = ''

    def __post_init__(self) -> None:
        if type(self.project_id) is not ProjectId:
            raise TypeError('PROJECT_ID_MISSING')
        ProjectId.__post_init__(self.project_id)
        if type(self.display_name) is not str or not self.display_name.strip() or self.display_name!=self.display_name.strip():
            raise ValueError('PROJECT_NAME_MISSING')
        if type(self.description) is not str:
            raise TypeError('INVALID_PROJECT_DESCRIPTION')
        if type(self.constitution_ref) is not EntityRef or self.constitution_ref.kind is not EntityKind.CONSTITUTION:
            raise TypeError('INVALID_CONSTITUTION_REF')
        if type(self.source_policy_ref) is not EntityRef or self.source_policy_ref.kind is not EntityKind.SOURCE_POLICY:
            raise TypeError('INVALID_SOURCE_POLICY_REF')
        if type(self.source_policy) is not SourcePolicy or type(self.storage) is not StorageDescriptor:
            raise TypeError('SOURCE_POLICY_MISSING')
        EntityRef.__post_init__(self.constitution_ref)
        EntityRef.__post_init__(self.source_policy_ref)
        SourcePolicy.__post_init__(self.source_policy)
        StorageDescriptor.__post_init__(self.storage)
        if (self.constitution_ref.project!=self.project_id or self.source_policy_ref.project!=self.project_id
                or self.source_policy.project!=self.project_id
                or self.source_policy.revision!=self.source_policy_ref.revision):
            raise ValueError('PROJECT_POLICY_REVISION_MISMATCH')
        if set(self.source_policy.allow_repositories)!=set(self.storage.repositories):
            raise ValueError('PROJECT_REPOSITORY_POLICY_MISMATCH')


    @property
    def permitted_source_repositories(self) -> tuple[RepositoryId, ...]:
        """Managed repositories plus the explicitly pinned sidecar authority."""
        if type(self) is not ProjectDefinition:
            raise TypeError('EXACT_PROJECT_DEFINITION_REQUIRED')
        ProjectDefinition.__post_init__(self)
        managed = self.source_policy.allow_repositories
        if self.storage.mode is StorageMode.SIDECAR:
            return managed + (self.storage.authority_repository,)
        return managed


def validate_project(definition: object) -> Result[ProjectDefinition]:
    """Validate the complete data contract, not just its dataclass tag."""
    try:
        if type(definition) is not ProjectDefinition:
            raise TypeError('EXACT_PROJECT_DEFINITION_REQUIRED')
        ProjectDefinition.__post_init__(definition)
        return Result(definition)
    except (TypeError, ValueError, AttributeError) as exc:
        return Result(diagnostics=(Diagnostic('PROJECT_SNAPSHOT_INVALID','$.project',
            'validated immutable project','ProjectDefinition' if type(definition) is ProjectDefinition else 'non-ProjectDefinition',str(exc) or 'invalid project'),))


class MembershipStatus(str, Enum):
    ALLOWED='allowed'
    DENIED='denied'
    REQUIRES_APPROVAL='requires_approval'
    UNKNOWN='unknown'


@dataclass(frozen=True, slots=True)
class MembershipVerdict:
    status: MembershipStatus
    code: str
    detail: str

    @property
    def allowed(self)->bool:
        return self.status is MembershipStatus.ALLOWED


def check_project_membership(project: ProjectDefinition, ref: EntityRef) -> MembershipVerdict:
    checked = validate_project(project)
    if not checked.ok:
        return MembershipVerdict(MembershipStatus.UNKNOWN,'INVALID_PROJECT_REFERENCE',checked.diagnostics[0].reason)
    try:
        if type(ref) is not EntityRef:
            raise TypeError('EXACT_ENTITY_REFERENCE_REQUIRED')
        EntityRef.__post_init__(ref)
    except (TypeError, ValueError, AttributeError) as exc:
        return MembershipVerdict(MembershipStatus.UNKNOWN,'INVALID_PROJECT_REFERENCE',str(exc) or 'invalid reference')
    if ref.project!=project.project_id:
        return MembershipVerdict(MembershipStatus.REQUIRES_APPROVAL,'FORBIDDEN_CROSS_PROJECT_REF','explicit scoped import and external trust required')
    return MembershipVerdict(MembershipStatus.ALLOWED,'PROJECT_MEMBER','scoped reference belongs to this project')
