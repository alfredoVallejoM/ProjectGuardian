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
        if not isinstance(self.mode, StorageMode) or not isinstance(self.authority_repository, RepositoryId):
            raise TypeError('INVALID_STORAGE_DESCRIPTOR')
        if (type(self.repositories) is not tuple or not self.repositories
                or any(not isinstance(r,RepositoryId) for r in self.repositories)
                or len(set(self.repositories))!=len(self.repositories)):
            raise ValueError('INVALID_STORAGE_REPOSITORIES')
        if type(self.authority_by_class) is not tuple:
            raise TypeError('INVALID_STORAGE_AUTHORITY_MAP')
        classes=set()
        for item in self.authority_by_class:
            if (type(item) is not tuple or len(item)!=2 or item[0] not in _AUTHORITY_CLASSES
                    or not isinstance(item[1],RepositoryId) or item[0] in classes):
                raise ValueError('AMBIGUOUS_AUTHORITY')
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
    if not isinstance(descriptor, StorageDescriptor):
        return Result(diagnostics=(Diagnostic('UNSUPPORTED_STORAGE_MODE','$.storage','StorageDescriptor',type(descriptor).__name__,'invalid declarative storage mode'),))
    return Result(descriptor)


@dataclass(frozen=True, slots=True)
class SourcePolicy:
    project: ProjectId
    revision: RevisionId
    allow_repositories: tuple[RepositoryId, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.project, ProjectId) or not isinstance(self.revision, RevisionId):
            raise TypeError('source policy needs pinned project and revision')
        if (type(self.allow_repositories) is not tuple or not self.allow_repositories
                or any(not isinstance(r,RepositoryId) for r in self.allow_repositories)
                or len(set(self.allow_repositories))!=len(self.allow_repositories)):
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
        if not isinstance(self.project_id,ProjectId):
            raise TypeError('PROJECT_ID_MISSING')
        if type(self.display_name) is not str or not self.display_name.strip() or self.display_name!=self.display_name.strip():
            raise ValueError('PROJECT_NAME_MISSING')
        if type(self.description) is not str:
            raise TypeError('INVALID_PROJECT_DESCRIPTION')
        if not isinstance(self.constitution_ref,EntityRef) or self.constitution_ref.kind is not EntityKind.CONSTITUTION:
            raise TypeError('INVALID_CONSTITUTION_REF')
        if not isinstance(self.source_policy_ref,EntityRef) or self.source_policy_ref.kind is not EntityKind.SOURCE_POLICY:
            raise TypeError('INVALID_SOURCE_POLICY_REF')
        if not isinstance(self.source_policy,SourcePolicy) or not isinstance(self.storage,StorageDescriptor):
            raise TypeError('SOURCE_POLICY_MISSING')
        if (self.constitution_ref.project!=self.project_id or self.source_policy_ref.project!=self.project_id
                or self.source_policy.project!=self.project_id
                or self.source_policy.revision!=self.source_policy_ref.revision):
            raise ValueError('PROJECT_POLICY_REVISION_MISMATCH')
        if set(self.source_policy.allow_repositories)!=set(self.storage.repositories):
            raise ValueError('PROJECT_REPOSITORY_POLICY_MISMATCH')


def validate_project(definition: object) -> Result[ProjectDefinition]:
    if not isinstance(definition, ProjectDefinition):
        return Result(diagnostics=(Diagnostic('PROJECT_SNAPSHOT_INVALID','$.project','ProjectDefinition',type(definition).__name__,'expected validated immutable project'),))
    return Result(definition)


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
    if not isinstance(project,ProjectDefinition) or not isinstance(ref,EntityRef):
        return MembershipVerdict(MembershipStatus.UNKNOWN,'INVALID_PROJECT_REFERENCE','typed project and entity reference required')
    if ref.project!=project.project_id:
        return MembershipVerdict(MembershipStatus.REQUIRES_APPROVAL,'FORBIDDEN_CROSS_PROJECT_REF','explicit scoped import and external trust required')
    return MembershipVerdict(MembershipStatus.ALLOWED,'PROJECT_MEMBER','scoped reference belongs to this project')
