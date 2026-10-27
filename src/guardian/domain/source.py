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


def _validate_cut(cut: object, expected: type, code: str) -> Result:
    """Validate exact nominal data, never a caller-defined subclass hook."""
    try:
        if type(cut) is not expected:
            raise TypeError('EXACT_SOURCE_CUT_TYPE_REQUIRED')
        # Reconstructed dataclasses may bypass their normal constructors.
        # Check base nominal values before using equality, hashes or membership.
        ref = cut.ref
        if (type(ref) is not EntityRef or type(ref.project) is not ProjectId
                or type(ref.revision) is not RevisionId or type(ref.kind) is not EntityKind):
            raise TypeError('EXACT_SOURCE_IDENTITY_REQUIRED')
        from .identity import EntityId
        if type(ref.entity) is not EntityId or type(ref.entity.project) is not ProjectId:
            raise TypeError('EXACT_SOURCE_IDENTITY_REQUIRED')
        ProjectId.__post_init__(ref.project)
        ProjectId.__post_init__(ref.entity.project)
        RevisionId.__post_init__(ref.revision)
        EntityId.__post_init__(ref.entity)
        EntityRef.__post_init__(ref)
        if cut.observed_digest is not None:
            if type(cut.observed_digest) is not ContentDigest:
                raise TypeError('EXACT_SOURCE_DIGEST_REQUIRED')
            ContentDigest.__post_init__(cut.observed_digest)
        if expected is GitSourceCut:
            if type(cut.repository) is not RepositoryId or type(cut.object_kind) is not GitObjectKind:
                raise TypeError('EXACT_GIT_CUT_CONTEXT_REQUIRED')
            RepositoryId.__post_init__(cut.repository)
        expected.__post_init__(cut)
        return Result(cut)
    except (TypeError, ValueError, AttributeError) as exc:
        return Result(diagnostics=(Diagnostic(code, '$.source', expected.__name__,
                                             type(cut).__name__, str(exc)),))


def validate_git_source_cut(cut:object)->Result[GitSourceCut]:
    return _validate_cut(cut, GitSourceCut, 'SOURCE_CUT_NOT_PINNED')


def validate_document_source(cut:object)->Result[DocumentSourceCut]:
    return _validate_cut(cut, DocumentSourceCut, 'SOURCE_REVISION_REQUIRED')


def _validate_any_cut(cut: object) -> Result:
    if type(cut) is DocumentSourceCut:
        return validate_document_source(cut)
    return validate_git_source_cut(cut)


@dataclass(frozen=True,slots=True)
class ApprovedSourceImport:
    """Scoped grant descriptor whose approval is *not* authenticated by G00."""
    target_project: ProjectId
    source_ref: EntityRef
    repository: RepositoryId | None
    permitted_path: str | None
    approval_ref: EntityRef
    pinned_cut: SourceCut

    def __post_init__(self)->None:
        if not isinstance(self.pinned_cut,(GitSourceCut,DocumentSourceCut)) or self.pinned_cut.ref != self.source_ref:
            raise ValueError('IMPORT_PINNED_CUT_REQUIRED')
        if isinstance(self.pinned_cut,GitSourceCut):
            if self.repository!=self.pinned_cut.repository or self.permitted_path!=self.pinned_cut.path:
                raise ValueError('IMPORT_CUT_REPOSITORY_PATH_MISMATCH')
        elif self.repository is not None or self.permitted_path is not None:
            raise ValueError('IMPORT_DOCUMENT_CUT_SCOPE_MISMATCH')
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
    valid = _validate_any_cut(source)
    if not valid.ok:
        return MembershipVerdict(MembershipStatus.DENIED, valid.diagnostics[0].code, valid.diagnostics[0].reason)
    if source.ref.project==project.project_id:
        if isinstance(source,GitSourceCut) and source.repository not in project.permitted_source_repositories:
            return MembershipVerdict(MembershipStatus.DENIED,'SOURCE_REPOSITORY_DENIED','repo absent from project allowlist')
        return MembershipVerdict(MembershipStatus.ALLOWED,'SOURCE_MEMBER','source belongs to this project and source policy')
    if grants is None or not isinstance(grants,TrustedImportGrants):
        return MembershipVerdict(MembershipStatus.REQUIRES_APPROVAL,'IMPORT_REQUIRED','external trusted grant context required')
    for grant in grants.grants:
        if (grant.target_project!=project.project_id or grant.source_ref!=source.ref
                or grant.pinned_cut!=source):
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


def _source_reference(value: object, kind: EntityKind) -> None:
    """Revalidate reference contents before hashing or inspecting metadata."""
    from .identity import EntityId
    if (type(value) is not EntityRef or type(value.project) is not ProjectId
            or type(value.entity) is not EntityId or type(value.entity.project) is not ProjectId
            or type(value.revision) is not RevisionId or value.kind is not kind
            or type(value.entity.kind) is not EntityKind):
        raise TypeError('EXACT_SOURCE_REFERENCE_REQUIRED')
    ProjectId.__post_init__(value.project)
    ProjectId.__post_init__(value.entity.project)
    EntityId.__post_init__(value.entity)
    RevisionId.__post_init__(value.revision)
    EntityRef.__post_init__(value)


def _universe_metadata_diagnostics(universe: object) -> tuple[Diagnostic, ...]:
    """Validate nested declarations, not only source-cut bytes and class tags.

    Reconstruction/deserialization can bypass constructors. This boundary calls
    only known base validators, never a hook defined by an untrusted subclass.
    Approval references remain declarations; this does not authenticate them.
    """
    try:
        if type(universe) is not SourceUniverseRevision:
            raise TypeError('EXACT_SOURCE_UNIVERSE_REQUIRED')
        SourceUniverseRevision.__post_init__(universe)
        _source_reference(universe.identity, EntityKind.SOURCE_UNIVERSE)
        if type(universe.scope) is not CoverageScope:
            raise TypeError('EXACT_COVERAGE_SCOPE_REQUIRED')
        CoverageScope.__post_init__(universe.scope)
    except (TypeError, ValueError, AttributeError) as exc:
        return (_diag('INVALID_SOURCE_UNIVERSE', '$.universe', str(exc)),)
    findings = []
    for i, entry in enumerate(universe.entries):
        path = f'$.entries[{i}]'
        if type(entry) is not SourceEntry:
            findings.append(_diag('INVALID_SOURCE_ENTRY', path, 'exact SourceEntry required'))
            continue
        try:
            checked = _validate_any_cut(entry.cut)
        except AttributeError as exc:
            findings.append(_diag('INVALID_SOURCE_ENTRY', path, str(exc)))
            continue
        if not checked.ok:
            findings.extend(_diag(d.code, path + '.cut', d.reason) for d in checked.diagnostics)
            continue
        try:
            if type(entry.role) is not HistoryRole or type(entry.acquisition) is not SourceStatus:
                raise TypeError('NOMINAL_HISTORY_AND_ACQUISITION_REQUIRED')
            if entry.baseline_ref is not None:
                _source_reference(entry.baseline_ref, EntityKind.SOURCE)
            SourceEntry.__post_init__(entry)
        except (TypeError, ValueError, AttributeError) as exc:
            findings.append(_diag('INVALID_SOURCE_ENTRY', path, str(exc)))
    for i, reference in enumerate(universe.included):
        try:
            _source_reference(reference, EntityKind.SOURCE)
        except (TypeError, ValueError, AttributeError) as exc:
            findings.append(_diag('INVALID_SOURCE_MEMBERSHIP_REF', f'$.included[{i}]', str(exc)))
    for i, exclusion in enumerate(universe.excluded):
        try:
            if type(exclusion) is not SourceExclusion:
                raise TypeError('EXACT_SOURCE_EXCLUSION_REQUIRED')
            _source_reference(exclusion.cut, EntityKind.SOURCE)
            _source_reference(exclusion.approval_ref, EntityKind.DECISION)
            SourceExclusion.__post_init__(exclusion)
        except (TypeError, ValueError, AttributeError) as exc:
            findings.append(_diag('EXCLUSION_UNJUSTIFIED', f'$.excluded[{i}]', str(exc)))
    for i, missing in enumerate(universe.known_missing):
        try:
            if type(missing) is not MissingSource:
                raise TypeError('EXACT_MISSING_SOURCE_REQUIRED')
            MissingSource.__post_init__(missing)
        except (TypeError, ValueError, AttributeError) as exc:
            findings.append(_diag('INVALID_MISSING_SOURCE', f'$.known_missing[{i}]', str(exc)))
    return tuple(findings)


def validate_inclusion_exclusion(universe:SourceUniverseRevision)->tuple[Diagnostic,...]:
    invalid = _universe_metadata_diagnostics(universe)
    return invalid if invalid else _membership_diagnostics(universe)


def _membership_diagnostics(universe:SourceUniverseRevision)->tuple[Diagnostic,...]:
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
    # Metadata validity precedes hashing, authority membership and history.
    invalid = _universe_metadata_diagnostics(universe)
    if invalid:
        return SourceUniverseValidation(invalid, (), universe.scope, False)
    findings=list(_membership_diagnostics(universe))
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
            findings.append(_diag('SOURCE_MISSING','$.entries','declared source is missing; do not treat as observed'))
            unverified.append(e.cut.ref)
        elif e.acquisition is not SourceStatus.SEMANTIC_RECONCILED:
            unverified.append(e.cut.ref)
        if e.baseline_ref is not None:
            baseline=entries.get(e.baseline_ref)
            if (baseline is None or baseline.lineage!=e.lineage
                    or type(baseline.cut) is not type(e.cut)
                    or history_source_key(baseline.cut) != history_source_key(e.cut)):
                findings.append(_diag('INVALID_HISTORICAL_BASELINE','$.entries',
                                      'baseline absent, foreign repository/type, or different history'))
    # History applies to every admitted source kind, not Git alone. Labels
    # cannot make identical physical cuts disjoint or remove cycles.
    physical = [material_source_key(e.cut) for e in universe.entries]
    if len(set(physical)) != len(physical):
        findings.append(_diag('SOURCE_POPULATION_DOUBLE_COUNT', '$.entries',
                              'multiple nominal aliases of the same material cut'))
    groups: dict[tuple[object, ...], list[SourceEntry]] = {}
    for entry in universe.entries:
        groups.setdefault(history_source_key(entry.cut) + (entry.lineage,), []).append(entry)
    for group in groups.values():
        if sum(x.role is HistoryRole.BASE for x in group) > 1:
            findings.append(_diag('SOURCE_POPULATION_DOUBLE_COUNT', '$.entries',
                                  'multiple BASE cuts in one history'))
        if (any(x.role in (HistoryRole.DELTA, HistoryRole.SUPERSEDED) for x in group)
                and not any(x.role is HistoryRole.BASE for x in group)):
            findings.append(_diag('HISTORICAL_BASE_MISSING', '$.entries', 'history has no baseline'))
    # Traverse the entire baseline graph, even if an invalid lineage/type edge
    # was already reported. Multiple diagnostics must not hide an actual cycle.
    finished: set[EntityRef] = set()
    for entry in universe.entries:
        current = entry
        path: set[EntityRef] = set()
        while current.cut.ref not in finished:
            if current.cut.ref in path:
                findings.append(_diag('HISTORICAL_CYCLE', '$.entries', 'cyclic baseline chain'))
                break
            path.add(current.cut.ref)
            following = entries.get(current.baseline_ref)
            if following is None:
                break
            current = following
        finished.update(path)
    if universe.known_missing or any(e.acquisition is SourceStatus.MISSING for e in universe.entries):
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


def history_source_key(cut: SourceCut) -> tuple[object, ...]:
    """Physical history independent of caller-provided aliases/lineage labels."""
    if isinstance(cut, GitSourceCut):
        return ('git', cut.repository)
    return ('document', cut.locator)


def material_source_key(cut: SourceCut) -> tuple[object, ...]:
    if isinstance(cut, GitSourceCut):
        return ('git', cut.repository, cut.commit, cut.object_kind, cut.path)
    return ('document', cut.locator, cut.document_version)


def describe_source_coverage(universe:SourceUniverseRevision)->SourceCoverageDescriptor:
    if not isinstance(universe,SourceUniverseRevision):
        raise TypeError('SourceUniverseRevision required')
    invalid = _universe_metadata_diagnostics(universe)
    if invalid:
        # A coverage descriptor assumes typed acquisition/scope. Do not turn
        # malformed metadata into a plausible count or an invented scope.
        raise ValueError('INVALID_SOURCE_COVERAGE_INPUT:' + invalid[0].code)
    included = set(universe.included)
    entries = tuple(e for e in universe.entries if e.cut.ref in included)
    missing = list(universe.known_missing)
    for entry in universe.entries:
        if entry.acquisition is SourceStatus.MISSING:
            cut = entry.cut
            locator = (f'{cut.repository.provider}:{cut.repository.slug}@{cut.commit}:{cut.path or ""}'
                       if isinstance(cut, GitSourceCut) else f'{cut.locator}@{cut.document_version}')
            item = MissingSource(locator, 'SOURCE_MISSING: acquisition state is missing')
            if not any(m.locator == locator for m in missing):
                missing.append(item)
    limits = list(universe.declared_limits)
    if missing:
        limits.append('SOURCE_MISSING: source acquisition or known inventory gaps remain')
    if any(e.acquisition not in (SourceStatus.CONTENT_OBSERVED, SourceStatus.SEMANTIC_RECONCILED)
           for e in entries):
        limits.append('SOURCE_NOT_FULLY_OBSERVED: metadata does not establish source content coverage')
    # Sort each repository's physical paths rather than comparing O(n^2)
    # pairs. Adjacent prefixes suffice to detect all tree/file overlap.
    paths: dict[RepositoryId, list[str]] = {}
    documents: list[str] = []
    disjoint = (len(included) == len(universe.included) == len(entries)
                and not missing and not validate_inclusion_exclusion(universe))
    for entry in entries:
        cut = entry.cut
        if isinstance(cut, GitSourceCut):
            paths.setdefault(cut.repository, []).append(cut.path or '')
        else:
            documents.append(cut.locator)
    if (paths and documents) or len(set(documents)) != len(documents):
        disjoint = False
    for values in paths.values():
        ordered = sorted(values)
        if any(left == '' or right == left or right.startswith(left + '/')
               for left, right in zip(ordered, ordered[1:])):
            disjoint = False
    return SourceCoverageDescriptor(universe.scope,len(included),tuple(missing),
                                    tuple(dict.fromkeys(limits)),disjoint,False)
