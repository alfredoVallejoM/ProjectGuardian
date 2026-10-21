"""G00-03: immutable source cuts, provenance, explicitly bounded universe.

Source observation and coverage descriptions are NEVER normative certificates.
Import grants are externally *supplied* trust assertions; authenticating them is
G09's responsibility. Every membership check is exact-cut and exact-path.
"""
from __future__ import annotations

import re
import unicodedata
from urllib.parse import urlsplit
from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from .identity import ContentDigest, EntityKind, EntityRef, ProjectId, RevisionId
from .outcomes import Diagnostic, Result, SourceStatus
from .project import MembershipStatus, MembershipVerdict, ProjectDefinition, RepositoryId

_COMMIT = re.compile(r'(?:[0-9a-f]{40}|[0-9a-f]{64})\Z', re.ASCII)


def validate_source_path(path: object) -> Result[str]:
    if (type(path) is not str or not path or len(path)>4096
            or path.startswith('/') or path.endswith('/') or '\\' in path or ':' in path
            or path!=unicodedata.normalize('NFC',path)
            or any(x in ('','.','..') for x in path.split('/'))
            or any(ord(c)<32 or ord(c)==127 for c in path)):
        return Result(diagnostics=(Diagnostic('INVALID_SOURCE_PATH','$.path','relative normalized POSIX path',type(path).__name__,'absolute, traversal, separator or control character'),))
    return Result(path)


class GitObjectKind(str,Enum):
    COMMIT='commit'
    TREE='tree'
    BLOB='blob'


@dataclass(frozen=True,slots=True)
class GitSourceCut:
    ref: EntityRef
    repository: RepositoryId
    commit: str
    object_kind: GitObjectKind
    path: str | None = None
    observed_digest: ContentDigest | None = None

    def __post_init__(self)->None:
        if not isinstance(self.ref,EntityRef) or self.ref.kind is not EntityKind.SOURCE:
            raise TypeError('GitSourceCut needs SOURCE entity reference with revision')
        if not isinstance(self.repository,RepositoryId):
            raise TypeError('GitSourceCut repository must be nominal')
        if type(self.commit) is not str or _COMMIT.fullmatch(self.commit) is None:
            raise ValueError('SOURCE_CUT_NOT_PINNED')
        if not isinstance(self.object_kind,GitObjectKind):
            raise TypeError('GIT_SOURCE_OBJECT_KIND')
        if self.object_kind is GitObjectKind.BLOB and self.path is None:
            raise ValueError('BLOB_PATH_REQUIRED')
        if self.object_kind is GitObjectKind.COMMIT and self.path is not None:
            raise ValueError('COMMIT_OBJECT_HAS_NO_PATH')
        if self.path is not None and not validate_source_path(self.path).ok:
            raise ValueError('INVALID_SOURCE_PATH')
        if self.observed_digest is not None and not isinstance(self.observed_digest,ContentDigest):
            raise TypeError('source digest must be tagged')


@dataclass(frozen=True,slots=True)
class DocumentSourceCut:
    ref: EntityRef
    locator: str
    document_version: str
    observed_digest: ContentDigest | None = None

    def __post_init__(self)->None:
        if not isinstance(self.ref,EntityRef) or self.ref.kind is not EntityKind.SOURCE:
            raise TypeError('DocumentSourceCut needs SOURCE ref')
        if (type(self.locator) is not str or not self.locator.strip() or self.locator!=self.locator.strip()
                or len(self.locator)>2048 or any(ord(c)<32 for c in self.locator)):
            raise ValueError('DOCUMENT_SOURCE_LOCATOR_MISSING')
        locator=urlsplit(self.locator)
        if locator.scheme not in ('https','file','urn') or (locator.scheme=='https' and not locator.netloc):
            raise ValueError('DOCUMENT_SCHEME_UNSUPPORTED')
        if (type(self.document_version) is not str or not self.document_version.strip()
                or self.document_version!=self.document_version.strip() or len(self.document_version)>128):
            raise ValueError('SOURCE_REVISION_REQUIRED')
        if self.observed_digest is not None and not isinstance(self.observed_digest,ContentDigest):
            raise TypeError('invalid document digest')


SourceCut=GitSourceCut|DocumentSourceCut


def validate_git_source_cut(cut:object)->Result[GitSourceCut]:
    if not isinstance(cut,GitSourceCut):
        return Result(diagnostics=(Diagnostic('SOURCE_CUT_NOT_PINNED','$.source','immutable GitSourceCut',type(cut).__name__,'source cut missing or malformed'),))
    return Result(cut)


def validate_document_source(cut:object)->Result[DocumentSourceCut]:
    if not isinstance(cut,DocumentSourceCut):
        return Result(diagnostics=(Diagnostic('SOURCE_REVISION_REQUIRED','$.source','versioned DocumentSourceCut',type(cut).__name__,'document source not pinned'),))
    return Result(cut)


@dataclass(frozen=True,slots=True)
class ApprovedSourceImport:
    """Scoped grant descriptor whose approval is *not* authenticated by G00."""
    target_project: ProjectId
    source_ref: EntityRef
    repository: RepositoryId | None
    permitted_path: str | None
    approval_ref: EntityRef

    def __post_init__(self)->None:
        if not isinstance(self.target_project,ProjectId) or not isinstance(self.source_ref,EntityRef) or self.source_ref.kind is not EntityKind.SOURCE:
            raise TypeError('import must bind exact pinned source and target project')
        if self.target_project==self.source_ref.project:
            raise ValueError('IMPORT_SAME_PROJECT_REDUNDANT')
        if self.repository is not None and not isinstance(self.repository,RepositoryId):
            raise TypeError('import repository must be typed')
        if self.permitted_path is not None and not validate_source_path(self.permitted_path).ok:
            raise ValueError('INVALID_IMPORT_PATH')
        if self.repository is None and self.permitted_path is not None:
            raise ValueError('IMPORT_PATH_REQUIRES_REPOSITORY')
        if (not isinstance(self.approval_ref,EntityRef) or self.approval_ref.kind is not EntityKind.DECISION
                or self.approval_ref.project!=self.target_project):
            raise TypeError('grant must refer to local pinned decision')


@dataclass(frozen=True,slots=True)
class TrustedImportGrants:
    """Must be constructed at an external trust boundary. Not a signature proof."""
    grants: tuple[ApprovedSourceImport,...] = ()

    def __post_init__(self)->None:
        if type(self.grants) is not tuple or any(not isinstance(g,ApprovedSourceImport) for g in self.grants):
            raise TypeError('untyped grant list')
        if len(set(self.grants))!=len(self.grants):
            raise ValueError('duplicate import grant')


def check_source_membership(project:ProjectDefinition, source:SourceCut, grants:TrustedImportGrants|None=None)->MembershipVerdict:
    if not isinstance(project,ProjectDefinition) or not isinstance(source,(GitSourceCut,DocumentSourceCut)):
        return MembershipVerdict(MembershipStatus.UNKNOWN,'INVALID_SOURCE','project and typed source required')
    if source.ref.project==project.project_id:
        if isinstance(source,GitSourceCut) and source.repository not in project.source_policy.allow_repositories:
            return MembershipVerdict(MembershipStatus.DENIED,'SOURCE_REPOSITORY_DENIED','repo absent from project allowlist')
        return MembershipVerdict(MembershipStatus.ALLOWED,'SOURCE_MEMBER','source belongs to this project and source policy')
    if grants is None or not isinstance(grants,TrustedImportGrants):
        return MembershipVerdict(MembershipStatus.REQUIRES_APPROVAL,'IMPORT_REQUIRED','external trusted grant context required')
    for grant in grants.grants:
        if grant.target_project!=project.project_id or grant.source_ref!=source.ref:
            continue
        if isinstance(source,GitSourceCut):
            if grant.repository!=source.repository or grant.permitted_path!=source.path:
                continue
        else:
            if grant.repository is not None or grant.permitted_path is not None:
                continue
        return MembershipVerdict(MembershipStatus.ALLOWED,'IMPORTED_SOURCE_EXACT','externally trusted cut-scoped import')
    return MembershipVerdict(MembershipStatus.REQUIRES_APPROVAL,'UNAPPROVED_IMPORT_SCOPE','import does not cover exact source cut/repo/path')


class HistoryRole(str,Enum):
    BASE='base'
    DELTA='delta'
    SUPERSEDED='superseded'
    REFERENCE='reference'


@dataclass(frozen=True,slots=True)
class SourceEntry:
    cut:SourceCut
    role:HistoryRole
    acquisition:SourceStatus
    lineage: str
    baseline_ref:EntityRef|None=None

    def __post_init__(self)->None:
        if not isinstance(self.cut,(GitSourceCut,DocumentSourceCut)) or not isinstance(self.role,HistoryRole) or not isinstance(self.acquisition,SourceStatus):
            raise TypeError('invalid source entry or acquisition status')
        if type(self.lineage) is not str or not self.lineage.strip():
            raise ValueError('source history requires lineage')
        if self.baseline_ref is not None and (not isinstance(self.baseline_ref,EntityRef) or self.baseline_ref.kind is not EntityKind.SOURCE):
            raise TypeError('baseline ref must be pinned source')
        if self.role in (HistoryRole.DELTA,HistoryRole.SUPERSEDED) and self.baseline_ref is None:
            raise ValueError('HISTORICAL_BASELINE_REQUIRED')
        if self.role in (HistoryRole.BASE,HistoryRole.REFERENCE) and self.baseline_ref is not None:
            raise ValueError('UNEXPECTED_HISTORICAL_BASELINE')
        if self.baseline_ref==self.cut.ref:
            raise ValueError('SELF_REFERENTIAL_SOURCE_CUT')


@dataclass(frozen=True,slots=True)
class SourceExclusion:
    cut: EntityRef
    reason: str
    approval_ref: EntityRef

    def __post_init__(self)->None:
        if not isinstance(self.cut,EntityRef) or self.cut.kind is not EntityKind.SOURCE:
            raise TypeError('source exclusion requires pinned SourceRef')
        if type(self.reason) is not str or not self.reason.strip():
            raise ValueError('EXCLUSION_UNJUSTIFIED')
        if not isinstance(self.approval_ref,EntityRef) or self.approval_ref.kind is not EntityKind.DECISION:
            raise ValueError('EXCLUSION_APPROVAL_REQUIRED')


@dataclass(frozen=True,slots=True)
class MissingSource:
    locator: str
    reason: str

    def __post_init__(self)->None:
        if type(self.locator) is not str or not self.locator.strip() or type(self.reason) is not str or not self.reason.strip():
            raise ValueError('MISSING_SOURCE_REQUIRES_REASON')


@dataclass(frozen=True,slots=True)
class CoverageScope:
    corpus: tuple[str,...]
    features: tuple[str,...]
    platforms: tuple[str,...]
    temporal_boundary: str

    def __post_init__(self)->None:
        if (any(type(x) is not tuple or not x or any(type(s) is not str or not s.strip() for s in x)
                for x in (self.corpus,self.features,self.platforms))
                or type(self.temporal_boundary) is not str or not self.temporal_boundary.strip()):
            raise ValueError('COVERAGE_SCOPE_INCOMPLETE')


@dataclass(frozen=True,slots=True)
class SourceUniverseRevision:
    identity:EntityRef
    scope:CoverageScope
    entries:tuple[SourceEntry,...]
    included:tuple[EntityRef,...]
    excluded:tuple[SourceExclusion,...]=()
    known_missing:tuple[MissingSource,...]=()
    declared_limits:tuple[str,...]=()

    def __post_init__(self)->None:
        if not isinstance(self.identity,EntityRef) or self.identity.kind is not EntityKind.SOURCE_UNIVERSE:
            raise TypeError('SourceUniverse requires pinned SOURCE_UNIVERSE identity')
        if not isinstance(self.scope,CoverageScope):
            raise TypeError('SourceUniverse requires explicit corpus/profile/time scope')
        if type(self.entries) is not tuple or any(not isinstance(e,SourceEntry) for e in self.entries):
            raise TypeError('universe entries must be immutable')
        if type(self.included) is not tuple or any(not isinstance(ref,EntityRef) for ref in self.included):
            raise TypeError('includes must be exact SourceRefs')
        if type(self.excluded) is not tuple or any(not isinstance(x,SourceExclusion) for x in self.excluded):
            raise TypeError('exclusions must be justified')
        if type(self.known_missing) is not tuple or any(not isinstance(x,MissingSource) for x in self.known_missing):
            raise TypeError('known missing records must be typed')
        if type(self.declared_limits) is not tuple or any(type(x) is not str or not x.strip() for x in self.declared_limits):
            raise TypeError('limits must be immutable nonempty strings')


@dataclass(frozen=True,slots=True)
class SourceUniverseValidation:
    diagnostics:tuple[Diagnostic,...]
    unresolved_sources:tuple[EntityRef,...]
    covered_scope:CoverageScope
    eligible_for_complete_claim:bool=False

    @property
    def ok(self)->bool:
        return not self.diagnostics


def _diag(code:str,path:str,reason:str)->Diagnostic:
    return Diagnostic(code,path,'valid source universe', 'SourceUniverseRevision',reason)


def validate_inclusion_exclusion(universe:SourceUniverseRevision)->tuple[Diagnostic,...]:
    entries={e.cut.ref for e in universe.entries}
    inc=set(universe.included)
    excluded={e.cut for e in universe.excluded}
    findings=[]
    if len(inc)!=len(universe.included) or len(excluded)!=len(universe.excluded):
        findings.append(_diag('DUPLICATE_SOURCE_MEMBERSHIP','$.universe','duplicate include/exclude'))
    if inc & excluded:
        findings.append(_diag('SOURCE_SCOPE_CONFLICT','$.universe','same source is both included and excluded'))
    if not inc and not universe.known_missing:
        findings.append(_diag('SOURCE_UNIVERSE_EMPTY','$.universe','empty universe cannot establish coverage'))
    if (inc | excluded)-entries:
        findings.append(_diag('UNKNOWN_SOURCE','$.universe','include/exclude ref has no observed source entry'))
    return tuple(findings)


def validate_source_universe(universe:SourceUniverseRevision,project:ProjectDefinition,
                             source_catalog:Mapping[EntityRef,SourceCut],grants:TrustedImportGrants|None=None,
                             *,trusted_exclusion_decisions:frozenset[EntityRef]|None=None)->SourceUniverseValidation:
    """Pure structural evaluation. Exclusion approvals are trustworthy only
    when the caller supplies the externally verified exact DecisionRefs.
    Neither a SourceExclusion nor this function authenticates a human actor.
    """
    if not isinstance(universe,SourceUniverseRevision) or not isinstance(project,ProjectDefinition) or not isinstance(source_catalog,Mapping):
        raise TypeError('source universe validator needs typed universe, project, catalog')
    findings=list(validate_inclusion_exclusion(universe))
    if universe.identity.project!=project.project_id:
        findings.append(_diag('WRONG_PROJECT','$.identity','universe belongs to another project'))
    if trusted_exclusion_decisions is not None and (type(trusted_exclusion_decisions) is not frozenset
            or any(not isinstance(x,EntityRef) or x.kind is not EntityKind.DECISION for x in trusted_exclusion_decisions)):
        raise TypeError('exclusion trust context must be a frozen set of exact DECISION refs')
    for exclusion in universe.excluded:
        if exclusion.approval_ref.project != universe.identity.project:
            findings.append(_diag('EXCLUSION_WRONG_PROJECT','$.excluded','exclusion must be authorized by owning target project'))
        if (trusted_exclusion_decisions is None or exclusion.approval_ref not in trusted_exclusion_decisions):
            findings.append(_diag('EXCLUSION_AUTHORITY_UNVERIFIED','$.excluded',
                                  'approval reference alone does not prove an authenticated decision'))
    if len({item.locator for item in universe.known_missing})!=len(universe.known_missing):
        findings.append(_diag('DUPLICATE_MISSING_SOURCE','$.known_missing','duplicate source gap'))
    entries={e.cut.ref:e for e in universe.entries}
    if len(entries)!=len(universe.entries):
        findings.append(_diag('DUPLICATE_SOURCE_REF','$.entries','duplicate source revision'))
    unverified=[]
    for e in universe.entries:
        if source_catalog.get(e.cut.ref)!=e.cut:
            findings.append(_diag('SOURCE_CATALOG_MISMATCH','$.entries','catalog source cut differs from universe'))
        status=check_source_membership(project,e.cut,grants)
        if not status.allowed:
            findings.append(_diag(status.code,'$.entries',status.detail))
        if e.acquisition is SourceStatus.MISSING:
            unverified.append(e.cut.ref)
        elif e.acquisition is not SourceStatus.SEMANTIC_RECONCILED:
            unverified.append(e.cut.ref)
        if e.baseline_ref is not None:
            baseline=entries.get(e.baseline_ref)
            if baseline is None or baseline.lineage!=e.lineage:
                findings.append(_diag('INVALID_HISTORICAL_BASELINE','$.entries','baseline not found in same history'))
    # A lineage with multiple BASE cuts is ambiguous; distinguish history roles.
    groups:dict[tuple[RepositoryId,str],list[SourceEntry]]={}
    for e in universe.entries:
        if isinstance(e.cut,GitSourceCut):
            groups.setdefault((e.cut.repository,e.lineage),[]).append(e)
    for group in groups.values():
        if sum(x.role is HistoryRole.BASE for x in group)>1:
            findings.append(_diag('SOURCE_POPULATION_DOUBLE_COUNT','$.entries','multiple BASE cuts in one history'))
        if any(x.role in (HistoryRole.DELTA,HistoryRole.SUPERSEDED) for x in group) and not any(x.role is HistoryRole.BASE for x in group):
            findings.append(_diag('HISTORICAL_BASE_MISSING','$.entries','delta/superseded history has no baseline'))
        lookup={x.cut.ref:x for x in group}
        for entry in group:
            at=entry
            seen=set()
            while at.baseline_ref is not None:
                if at.cut.ref in seen:
                    findings.append(_diag('HISTORICAL_CYCLE','$.entries','cyclic baseline chain'))
                    break
                seen.add(at.cut.ref)
                nxt=lookup.get(at.baseline_ref)
                if nxt is None:
                    break  # INVALID_HISTORICAL_BASELINE is reported above.
                at=nxt
    if universe.known_missing:
        findings.append(_diag('SOURCE_COVERAGE_UNKNOWN','$.known_missing','known source gaps are visible'))
    if not universe.declared_limits:
        findings.append(_diag('COVERAGE_LIMITS_NOT_DECLARED','$.scope','explicit coverage limitations required'))
    # No G00 source validation can issue material coverage qualification.
    return SourceUniverseValidation(tuple(findings),tuple(dict.fromkeys(unverified)),universe.scope,False)


@dataclass(frozen=True,slots=True)
class SourceCoverageDescriptor:
    scope:CoverageScope
    counted_source_cuts:int
    known_missing:tuple[MissingSource,...]
    limitations:tuple[str,...]
    source_population_disjoint:bool
    coverage_qualified:bool=False


def describe_source_coverage(universe:SourceUniverseRevision)->SourceCoverageDescriptor:
    if not isinstance(universe,SourceUniverseRevision):
        raise TypeError('SourceUniverseRevision required')
    lineages={}
    for e in universe.entries:
        key=(e.cut.repository if isinstance(e.cut,GitSourceCut) else e.cut.ref.project,e.lineage)
        lineages[key]=lineages.get(key,0)+1
    return SourceCoverageDescriptor(universe.scope,len(universe.included),universe.known_missing,
                                    universe.declared_limits,all(n==1 for n in lineages.values()),False)
