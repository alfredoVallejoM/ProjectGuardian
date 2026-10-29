"""Exact, in-memory content resolution for the B03/B06 boundary.

A snapshot anchor can prove declared presence but never fabricate content.
Imports are explicit externally-trusted inputs, bound to an exact source cut
AND a finite set of entity revisions. No network, latest selection or admission.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping
from .identity import EntityId, EntityKind, EntityRef, ProjectId, RevisionId
from .outcomes import Diagnostic, Result
from .record_base import RecordRevision
from .source import (ApprovedSourceImport, DocumentSourceCut, GitSourceCut, SourceCut,
                     validate_git_source_cut, validate_document_source)

MAX_RECORDS = 25000


def record_types() -> tuple[type[RecordRevision], ...]:
    from .objective import ObjectiveRevision
    from .capability import CapabilityRevision
    from .property import PropertyRevision
    from .obligation import ObligationRevision
    from .campaign import CampaignRevision
    from .architecture import ArchitectureRevision
    from .scope import ScopeRevision
    from .authority import DecisionRevision
    from .constitution import RuleRevision, ConstitutionRevision
    from .verification import VerificationSpecRevision
    from .clause import ClauseRevision
    from .foundation_records import SourcePolicyRevision, SourceUniverseRecord, ProjectRevision
    return (ObjectiveRevision, CapabilityRevision, PropertyRevision,
            ObligationRevision, CampaignRevision, ArchitectureRevision, ScopeRevision, DecisionRevision, RuleRevision,
            ConstitutionRevision, VerificationSpecRevision, SourcePolicyRevision,
            SourceUniverseRecord, ProjectRevision, ClauseRevision)


def issue(code: str, path: str, reason: str) -> Diagnostic:
    return Diagnostic(code, path, 'exact typed entity revision', 'EntityRef', reason)


@dataclass(frozen=True, slots=True)
class RecordSnapshot:
    project_id: ProjectId
    revision: RevisionId
    records: tuple[RecordRevision, ...]
    sources: tuple[SourceCut, ...]
    anchors: tuple[EntityRef, ...] = ()
    historical: frozenset[EntityRef] = frozenset()
    _by_ref: Mapping[EntityRef, RecordRevision] = field(init=False, repr=False, compare=False)
    _source_by_ref: Mapping[EntityRef, SourceCut] = field(init=False, repr=False, compare=False)
    _anchor_set: frozenset[EntityRef] = field(init=False, repr=False, compare=False)
    _entity_ids: frozenset[EntityId] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if type(self.project_id) is not ProjectId or type(self.revision) is not RevisionId:
            raise TypeError('SNAPSHOT_IDENTITY_REQUIRED')
        ProjectId.__post_init__(self.project_id)
        RevisionId.__post_init__(self.revision)
        if type(self.records) is not tuple or len(self.records) > MAX_RECORDS:
            raise ValueError('SNAPSHOT_RECORD_LIMIT')
        if any(not any(type(r) is model for model in record_types()) for r in self.records):
            raise TypeError('UNSUPPORTED_RECORD_TYPE')
        for record in self.records:
            type(record).__post_init__(record)
        ids = [r.identity for r in self.records]
        if len(set(ids)) != len(ids):
            raise ValueError('DUPLICATE_LOGICAL_ID')
        if any(r.project != self.project_id for r in ids):
            raise ValueError('FORBIDDEN_CROSS_PROJECT_REF')
        if type(self.anchors) is not tuple or len(self.anchors) > MAX_RECORDS or any(type(r) is not EntityRef or r.project != self.project_id or r.kind is EntityKind.SOURCE for r in self.anchors):
            raise TypeError('INVALID_SNAPSHOT_ANCHORS')
        for reference in self.anchors:
            EntityRef.__post_init__(reference)
        if len(set(self.anchors)) != len(self.anchors):
            raise ValueError('DUPLICATE_SNAPSHOT_ANCHOR')
        if type(self.historical) is not frozenset or any(type(r) is not EntityRef for r in self.historical):
            raise TypeError('HISTORICAL_REFS_REQUIRED')
        for reference in self.historical:
            EntityRef.__post_init__(reference)
        if not self.historical <= set(ids):
            raise ValueError('UNKNOWN_HISTORICAL_REVISION')
        current = [r.entity for r in ids if r not in self.historical]
        if len(set(current)) != len(current):
            raise ValueError('MULTIPLE_CURRENT_REVISIONS')
        if type(self.sources) is not tuple or len(self.sources) > MAX_RECORDS or any(type(s) not in (GitSourceCut, DocumentSourceCut) for s in self.sources):
            raise TypeError('PINNED_SNAPSHOT_SOURCES_REQUIRED')
        for source in self.sources:
            checked = (validate_git_source_cut(source) if type(source) is GitSourceCut
                       else validate_document_source(source))
            if not checked.ok:
                raise ValueError(checked.diagnostics[0].code)
        if len({s.ref for s in self.sources}) != len(self.sources):
            raise ValueError('DUPLICATE_SOURCE_REVISION')
        if any(s.ref.project != self.project_id for s in self.sources):
            raise ValueError('FOREIGN_SNAPSHOT_SOURCE')
        source_refs = {c.ref for c in self.sources}
        if any(s not in source_refs for r in self.records for s in r.source_refs):
            raise ValueError('RECORD_SOURCE_OUTSIDE_SNAPSHOT')
        object.__setattr__(self, '_by_ref', MappingProxyType({r.identity: r for r in self.records}))
        object.__setattr__(self, '_source_by_ref', MappingProxyType({s.ref: s for s in self.sources}))
        object.__setattr__(self, '_anchor_set', frozenset(self.anchors))
        object.__setattr__(self, '_entity_ids', frozenset(r.entity for r in ids))

    def contains_entity(self, reference: EntityRef) -> bool:
        return (type(reference) is EntityRef and reference.project == self.project_id
                and (reference in self._anchor_set or reference in self._by_ref))

    def contains_source(self, reference: EntityRef) -> bool:
        return type(reference) is EntityRef and reference in self._source_by_ref


def _checked_snapshot(view: RecordSnapshot) -> RecordSnapshot:
    """Reconstruct derived indexes from validated immutable input, not caller caches.

    This is not a refresh of the supplied snapshot: its fields and indexes remain
    untouched. References resolve to the actual record objects in its population.
    The batch validator does this once, then uses the private checked resolver.
    """
    if type(view) is not RecordSnapshot:
        raise TypeError('SNAPSHOT_REQUIRED')
    return RecordSnapshot(view.project_id, view.revision, view.records, view.sources,
                          view.anchors, view.historical)


@dataclass(frozen=True, slots=True)
class EntityImport:
    source_grant: ApprovedSourceImport
    entities: frozenset[EntityRef]
    snapshot: RecordSnapshot

    def __post_init__(self) -> None:
        if type(self.source_grant) is not ApprovedSourceImport or type(self.snapshot) is not RecordSnapshot:
            raise TypeError('TYPED_IMPORT_REQUIRED')
        if type(self.entities) is not frozenset or not self.entities or any(type(x) is not EntityRef for x in self.entities):
            raise TypeError('EXACT_ENTITY_IMPORT_SCOPE_REQUIRED')
        grant = self.source_grant
        if type(grant.target_project) is not ProjectId:
            raise TypeError('IMPORT_TARGET_PROJECT_REQUIRED')
        ProjectId.__post_init__(grant.target_project)
        if type(grant.source_ref) is not EntityRef or type(grant.approval_ref) is not EntityRef:
            raise TypeError('IMPORT_REFERENCES_REQUIRED')
        EntityRef.__post_init__(grant.source_ref)
        EntityRef.__post_init__(grant.approval_ref)
        ApprovedSourceImport.__post_init__(grant)
        for reference in self.entities:
            EntityRef.__post_init__(reference)
        snapshot = _checked_snapshot(self.snapshot)
        if snapshot.project_id != grant.source_ref.project:
            raise ValueError('IMPORT_SNAPSHOT_PROJECT_MISMATCH')
        if not any(c == grant.pinned_cut for c in snapshot.sources):
            raise ValueError('IMPORT_MATERIAL_CUT_MISMATCH')
        for target in self.entities:
            records = [r for r in snapshot.records if r.identity == target]
            if len(records) != 1 or grant.source_ref not in records[0].source_refs:
                raise ValueError('IMPORT_ENTITY_NOT_IN_PINNED_SOURCE')


@dataclass(frozen=True, slots=True)
class TrustedEntityImports:
    """Supplied by the external trust boundary; this is NOT authentication."""
    entries: tuple[EntityImport, ...] = ()

    def __post_init__(self) -> None:
        if type(self.entries) is not tuple or any(type(e) is not EntityImport for e in self.entries):
            raise TypeError('INVALID_IMPORT_CONTEXT')
        if len(self.entries) > MAX_RECORDS:
            raise ValueError('IMPORT_CONTEXT_LIMIT')
        for entry in self.entries:
            EntityImport.__post_init__(entry)
        if len(set(self.entries)) != len(self.entries):
            raise ValueError('DUPLICATE_IMPORT')


@dataclass(frozen=True, slots=True)
class ResolvedEntity:
    reference: EntityRef
    record: RecordRevision
    historical: bool
    imported: bool

    def __post_init__(self) -> None:
        if type(self.record) not in record_types() or self.record.identity != self.reference:
            raise ValueError('RESOLVED_CONTENT_IDENTITY_MISMATCH')
        if type(self.historical) is not bool or type(self.imported) is not bool:
            raise TypeError('INVALID_RESOLUTION_FLAGS')

    @property
    def normatively_admitted(self) -> bool:
        return False


def resolve_entity(reference: object, view: object, expected_kind: object,
                   grants: TrustedEntityImports | None = None, *, path: str = '$',
                   require_current: bool = False) -> Result[ResolvedEntity]:
    if (type(require_current) is not bool or type(path) is not str or not path
            or any(ord(c) < 32 for c in path)):
        return Result(diagnostics=(issue('INVALID_REFERENCE_INPUT', '$', 'invalid current policy or diagnostic path'),))
    if type(reference) is not EntityRef or type(view) is not RecordSnapshot or type(expected_kind) is not EntityKind:
        return Result(diagnostics=(issue('INVALID_REFERENCE_INPUT', path, 'typed reference, snapshot and kind required'),))
    try:
        EntityRef.__post_init__(reference)
        checked_view = _checked_snapshot(view)
    except (TypeError, ValueError, AttributeError):
        return Result(diagnostics=(issue('INVALID_REFERENCE_INPUT', path, 'invalid nominal reference or snapshot contents'),))
    return _resolve_checked(reference, checked_view, expected_kind, grants,
                            path=path, require_current=require_current)


def _resolve_checked(reference: EntityRef, view: RecordSnapshot, expected_kind: EntityKind,
                     grants: TrustedEntityImports | None, *, path: str,
                     require_current: bool = False) -> Result[ResolvedEntity]:
    if reference.kind is not expected_kind:
        return Result(diagnostics=(issue('WRONG_ID_KIND', path, 'field expects a different entity class'),))
    if reference.kind is EntityKind.SOURCE:
        return Result(diagnostics=(issue('SOURCE_RESOLVER_REQUIRED', path, 'sources use their own cut catalog'),))
    selected = view
    imported = reference.project != view.project_id
    if imported:
        if type(grants) is not TrustedEntityImports:
            return Result(diagnostics=(issue('FORBIDDEN_CROSS_PROJECT_REF', path, 'no external trusted import context'),))
        try:
            TrustedEntityImports.__post_init__(grants)
        except (TypeError, ValueError, AttributeError):
            return Result(diagnostics=(issue('INVALID_IMPORT_CONTEXT', path, 'invalid pinned import data'),))
        candidates = [e for e in grants.entries if e.source_grant.target_project == view.project_id
                      and reference in e.entities]
        if not candidates:
            return Result(diagnostics=(issue('UNAPPROVED_IMPORT_SCOPE', path, 'grant does not cover this entity revision'),))
        # Never first-result-wins if two trusted observations disagree.
        matches = [(e.snapshot, next(r for r in e.snapshot.records if r.identity == reference)) for e in candidates]
        if (any(r != matches[0][1] or (reference in s.historical) != (reference in matches[0][0].historical)
               for s, r in matches[1:]) or any(e.source_grant.pinned_cut != candidates[0].source_grant.pinned_cut for e in candidates[1:])):
            return Result(diagnostics=(issue('CONFLICTING_IMPORT_CONTENT', path, 'import catalogs disagree on pinned content'),))
        selected = _checked_snapshot(matches[0][0])
    record = selected._by_ref.get(reference)
    if record is None:
        if reference in selected.anchors:
            code = 'REFERENCED_CONTENT_UNAVAILABLE'
        elif reference.entity in selected._entity_ids:
            code = 'UNKNOWN_REVISION'
        else:
            code = 'ORPHAN_REFERENCE'
        return Result(diagnostics=(issue(code, path, 'no exact content; no latest or placeholder fallback'),))
    historical = reference in selected.historical
    if historical and require_current:
        return Result(diagnostics=(issue('HISTORICAL_REFERENCE_NOT_CURRENT', path, 'history cannot be promoted to current'),))
    return Result(ResolvedEntity(reference, record, historical, imported))


@dataclass(frozen=True, slots=True)
class ReferenceValidation:
    diagnostics: tuple[Diagnostic, ...]
    checked: int

    @property
    def ok(self) -> bool:
        return not self.diagnostics


def validate_references(records: tuple[RecordRevision, ...], view: RecordSnapshot,
                        grants: TrustedEntityImports | None = None) -> ReferenceValidation:
    if type(records) is not tuple or any(type(r) not in record_types() for r in records) or type(view) is not RecordSnapshot:
        return ReferenceValidation((issue('INVALID_REFERENCE_INPUT', '$', 'typed record catalog required'),), 0)
    try:
        view = _checked_snapshot(view)
    except (TypeError, ValueError, AttributeError):
        return ReferenceValidation((issue('INVALID_REFERENCE_INPUT', '$', 'invalid snapshot contents'),), 0)
    errors, checked = [], 0
    for record in records:
        if record.identity.project != view.project_id:
            errors.append(issue('WRONG_PROJECT', '$.identity', 'record outside snapshot'))
            continue
        try:
            type(record).__post_init__(record)
            links = record.references()
        except (TypeError, ValueError, AttributeError) as exc:
            errors.append(issue('INVALID_RECORD', '$.records', str(exc)))
            continue
        owner = f'$.records[{record.identity.kind.value}:{record.identity.entity.value}@{record.identity.revision.value}]'
        for use in links:
            checked += 1
            path = owner + use.path[1:]
            if use.expected_kind is EntityKind.SOURCE:
                if not view.contains_source(use.target):
                    errors.append(issue('UNKNOWN_SOURCE', path, 'source absent from exact catalog'))
                continue
            outcome = _resolve_checked(use.target, view, use.expected_kind, grants, path=path)
            errors.extend(outcome.diagnostics)
    # Cycles between well-typed records are legitimate; no generic DAG check.
    return ReferenceValidation(tuple(sorted(errors, key=lambda e: (e.path, e.code, e.reason))), checked)
