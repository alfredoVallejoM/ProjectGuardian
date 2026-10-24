"""G00-01: nominal and immutable identity kernel.

All parsers are total over caller-provided values and return typed diagnostics.
Direct dataclass construction is checked too, so it cannot bypass validity.
The contract does not use clocks, randomness, filesystem, network or globals.
Content resolution delegates to the B03/B06 reference kernel. Unsupported
record bodies remain explicit; no alias or anchor fabricates their content.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, TYPE_CHECKING

if TYPE_CHECKING:
    from .record_base import RecordRevision
    from .references import RecordSnapshot, TrustedEntityImports, ResolvedEntity, ReferenceValidation

from .outcomes import Diagnostic, Result

_TOKEN = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z", re.ASCII)
_REVISION = re.compile(r"rev-[0-9a-f]{32}\Z", re.ASCII)
_HEX = re.compile(r"[0-9a-f]+\Z", re.ASCII)
_SCHEMA = "guardian.identity/v1"


def _reject(code: str, path: str, expected: str, value: object, reason: str) -> Result:
    return Result(diagnostics=(Diagnostic(code, path, expected, type(value).__name__, reason),))


def _token(text: str, name: str) -> None:
    if type(text) is not str:
        raise TypeError(f"{name} must be a plain string")
    if not 3 <= len(text) <= 96 or _TOKEN.fullmatch(text) is None:
        raise ValueError(f"invalid canonical {name}")


class EntityKind(str, Enum):
    OBJECTIVE = "objective"
    CAPABILITY = "capability"
    PROPERTY = "property"
    OBLIGATION = "obligation"
    CAMPAIGN = "campaign"
    ARCHITECTURE = "architecture"
    CONSTITUTION = "constitution"
    DECISION = "decision"
    RULE = "rule"
    SOURCE = "source"
    SOURCE_POLICY = "source_policy"
    SOURCE_UNIVERSE = "source_universe"
    SCOPE = "scope"
    CLAUSE = "clause"
    RELATION = "relation"
    VERIFICATION = "verification"
    IMPLEMENTATION = "implementation"
    PROJECT = "project"


class DigestAlgorithm(str, Enum):
    SHA256 = "sha256"
    SHA512 = "sha512"


@dataclass(frozen=True, slots=True)
class ProjectId:
    value: str

    def __post_init__(self) -> None:
        _token(self.value, "ProjectId")


@dataclass(frozen=True, slots=True)
class EntityId:
    project: ProjectId
    kind: EntityKind
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.project, ProjectId):
            raise TypeError("EntityId requires ProjectId")
        if not isinstance(self.kind, EntityKind):
            raise TypeError("EntityId requires EntityKind")
        _token(self.value, "EntityId")


@dataclass(frozen=True, slots=True)
class RevisionId:
    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str or _REVISION.fullmatch(self.value) is None:
            raise ValueError("RevisionId must be a pinned, opaque revision token")


@dataclass(frozen=True, slots=True)
class ContentDigest:
    algorithm: DigestAlgorithm
    hex: str

    def __post_init__(self) -> None:
        if not isinstance(self.algorithm, DigestAlgorithm):
            raise TypeError("digest algorithm must be known")
        if type(self.hex) is not str:
            raise TypeError("digest hex must be a string")
        length = {DigestAlgorithm.SHA256: 64, DigestAlgorithm.SHA512: 128}[self.algorithm]
        if len(self.hex) != length or _HEX.fullmatch(self.hex) is None:
            raise ValueError("digest must be full-length lowercase hexadecimal")


@dataclass(frozen=True, slots=True)
class EntityRef:
    project: ProjectId
    kind: EntityKind
    entity: EntityId
    revision: RevisionId

    def __post_init__(self) -> None:
        if not isinstance(self.project, ProjectId) or not isinstance(self.kind, EntityKind):
            raise TypeError("EntityRef requires typed project and kind")
        if not isinstance(self.entity, EntityId) or not isinstance(self.revision, RevisionId):
            raise TypeError("EntityRef requires typed entity and immutable revision")
        if self.entity.project != self.project or self.entity.kind != self.kind:
            raise ValueError("EntityRef project/kind must match EntityId")


def parse_project_id(raw: object, path: str = "$") -> Result[ProjectId]:
    if type(raw) is str and raw == "":
        return _reject("EMPTY_ID", path, "ProjectId", raw, "empty project ID")
    try:
        return Result(ProjectId(raw))
    except (ValueError, TypeError):
        return _reject("INVALID_ID_SYNTAX", path, "ProjectId", raw, "noncanonical project ID")


def parse_entity_id(project: object, kind: object, raw: object, path: str = "$") -> Result[EntityId]:
    if not isinstance(project, ProjectId):
        return _reject("PROJECT_REQUIRED", path, "ProjectId", project, "project namespace missing")
    if not isinstance(kind, EntityKind):
        return _reject("WRONG_ID_KIND", path, "EntityKind", kind, "entity kind missing or wrong")
    try:
        return Result(EntityId(project, kind, raw))
    except (ValueError, TypeError):
        return _reject("INVALID_ID_SYNTAX", path, "EntityId", raw, "noncanonical entity ID")


def parse_revision_id(raw: object, path: str = "$") -> Result[RevisionId]:
    if raw is None or (type(raw) is str and raw == ""):
        return _reject("REVISION_REQUIRED", path, "RevisionId", raw, "revision must be fixed")
    try:
        return Result(RevisionId(raw))
    except (ValueError, TypeError):
        return _reject("INVALID_REVISION", path, "RevisionId", raw, "mutable or invalid revision token")


def parse_content_digest(algorithm: object, hex_value: object, path: str = "$") -> Result[ContentDigest]:
    if not isinstance(algorithm, DigestAlgorithm):
        return _reject("UNSUPPORTED_DIGEST", path, "DigestAlgorithm", algorithm, "unrecognized digest algorithm")
    if type(hex_value) is not str:
        return _reject("DIGEST_MALFORMED", path, "hex string", hex_value, "invalid digest")
    try:
        return Result(ContentDigest(algorithm, hex_value.lower()))
    except (ValueError, TypeError):
        return _reject("DIGEST_MALFORMED", path, "full digest", hex_value, "truncated or nonhex digest")


Identity = ProjectId | EntityId | RevisionId | ContentDigest | EntityRef


def encode_identity(identity: Identity) -> dict[str, object]:
    base: dict[str, object] = {"schema": _SCHEMA}
    if isinstance(identity, ProjectId):
        return {**base, "type": "project_id", "value": identity.value}
    if isinstance(identity, EntityId):
        return {**base, "type": "entity_id", "project": identity.project.value,
                "entity_kind": identity.kind.value, "value": identity.value}
    if isinstance(identity, RevisionId):
        return {**base, "type": "revision_id", "value": identity.value}
    if isinstance(identity, ContentDigest):
        return {**base, "type": "content_digest", "algorithm": identity.algorithm.value,
                "hex": identity.hex}
    if isinstance(identity, EntityRef):
        return {**base, "type": "entity_ref", "project": identity.project.value,
                "entity_kind": identity.kind.value, "entity": identity.entity.value,
                "revision": identity.revision.value}
    raise TypeError("identity must be a supported nominal type")


_FIELDS: dict[str, frozenset[str]] = {
    "project_id": frozenset({"schema", "type", "value"}),
    "entity_id": frozenset({"schema", "type", "project", "entity_kind", "value"}),
    "revision_id": frozenset({"schema", "type", "value"}),
    "content_digest": frozenset({"schema", "type", "algorithm", "hex"}),
    "entity_ref": frozenset({"schema", "type", "project", "entity_kind", "entity", "revision"}),
}


def decode_identity(envelope: object, path: str = "$") -> Result[Identity]:
    if not isinstance(envelope, Mapping):
        return _reject("INVALID_ID_SCHEMA", path, "identity envelope", envelope, "expected map")
    typ = envelope.get("type")
    if not isinstance(typ, str) or typ not in _FIELDS:
        return _reject("UNKNOWN_ID_KIND", path + ".type", "known identity discriminant", typ, "unknown type")
    if envelope.get("schema") != _SCHEMA or set(envelope) != _FIELDS[typ]:
        return _reject("INVALID_ID_SCHEMA", path, _SCHEMA, envelope, "missing/extra fields or schema version")
    try:
        if typ == "project_id":
            return Result(ProjectId(envelope["value"]))
        if typ == "revision_id":
            return Result(RevisionId(envelope["value"]))
        if typ == "content_digest":
            return Result(ContentDigest(DigestAlgorithm(envelope["algorithm"]), envelope["hex"]))
        project = ProjectId(envelope["project"])
        kind = EntityKind(envelope["entity_kind"])
        if typ == "entity_id":
            return Result(EntityId(project, kind, envelope["value"]))
        entity = EntityId(project, kind, envelope["entity"])
        return Result(EntityRef(project, kind, entity, RevisionId(envelope["revision"])))
    except (TypeError, ValueError, KeyError):
        return _reject("INVALID_ID_SCHEMA", path, str(typ), envelope, "invalid typed identity payload")


@dataclass(frozen=True, slots=True)
class Alias:
    label: str

    def __post_init__(self) -> None:
        if type(self.label) is not str or not 1 <= len(self.label.strip()) <= 256:
            raise ValueError("alias must be nonempty Unicode text, up to 256 characters")
        if self.label != unicodedata.normalize("NFC", self.label) or self.label != self.label.strip():
            raise ValueError("alias must be NFC and not padded")


@dataclass(frozen=True, slots=True)
class AliasBinding:
    alias: Alias
    target: EntityRef
    source: EntityRef

    def __post_init__(self) -> None:
        if not isinstance(self.alias, Alias) or not isinstance(self.target, EntityRef):
            raise TypeError("alias and target must be typed")
        if not isinstance(self.source, EntityRef) or self.source.kind != EntityKind.SOURCE:
            raise TypeError("alias provenance must be pinned SOURCE EntityRef")
        if self.source.project != self.target.project:
            raise ValueError("source and target must belong to same project")


@dataclass(frozen=True, slots=True)
class AliasIndex:
    bindings: tuple[AliasBinding, ...] = ()

    def __post_init__(self) -> None:
        if type(self.bindings) is not tuple or not all(isinstance(b, AliasBinding) for b in self.bindings):
            raise TypeError("AliasIndex requires immutable typed bindings")
        if len(set(self.bindings)) != len(self.bindings):
            raise ValueError("DUPLICATE_ALIAS_BINDING")


@dataclass(frozen=True, slots=True)
class AliasBindingResult:
    index: AliasIndex
    diagnostics: tuple[Diagnostic, ...] = ()


def bind_alias(index: AliasIndex, target: EntityRef, alias: Alias, source: EntityRef) -> AliasBindingResult:
    """Pure index update, exposing duplicates and ambiguities, never first-wins."""
    if not isinstance(index, AliasIndex):
        raise TypeError("expected AliasIndex")
    binding = AliasBinding(alias, target, source)
    if binding in index.bindings:
        return AliasBindingResult(index, (Diagnostic("DUPLICATE_BINDING", "$.alias", "new alias binding", "AliasBinding", "already present"),))
    updated = AliasIndex(index.bindings + (binding,))
    matches = {b.target for b in updated.bindings if b.target.project == target.project
               and b.target.kind == target.kind and b.alias == alias}
    if len(matches) > 1:
        return AliasBindingResult(updated, (Diagnostic("AMBIGUOUS_ALIAS", "$.alias", "unique target", "Alias", "more than one exact candidate"),))
    return AliasBindingResult(updated)


def resolve_alias(index: AliasIndex, project: ProjectId, kind: EntityKind, alias: Alias) -> Result[EntityRef]:
    if not isinstance(index, AliasIndex):
        return _reject("INVALID_ID_SCHEMA", "$.aliases", "AliasIndex", index, "invalid alias index")
    if not isinstance(project, ProjectId) or not isinstance(kind, EntityKind) or not isinstance(alias, Alias):
        return _reject("WRONG_ID_KIND", "$.alias", "typed alias scope", alias, "scope is not typed")
    matches = {b.target for b in index.bindings if b.target.project == project and b.target.kind == kind and b.alias == alias}
    if not matches:
        return _reject("UNKNOWN_ALIAS", "$.alias", "bound alias", alias, "no matching binding")
    if len(matches) > 1:
        return _reject("AMBIGUOUS_ALIAS", "$.alias", "unique target", alias, "multiple matching bindings")
    return Result(next(iter(matches)))


@dataclass(frozen=True, slots=True)
class IdentityRegistration:
    identity: EntityId
    lineage: str

    def __post_init__(self) -> None:
        if not isinstance(self.identity, EntityId):
            raise TypeError("registration requires typed EntityId")
        _token(self.lineage, "lineage")


@dataclass(frozen=True, slots=True)
class IdentityIndex:
    registrations: tuple[IdentityRegistration, ...] = ()

    def __post_init__(self) -> None:
        if type(self.registrations) is not tuple or not all(isinstance(r, IdentityRegistration) for r in self.registrations):
            raise TypeError("IdentityIndex requires immutable typed registrations")
        seen: dict[EntityId, str] = {}
        for item in self.registrations:
            if item.identity in seen and seen[item.identity] != item.lineage:
                raise ValueError("DUPLICATE_LOGICAL_ID")
            if item.identity in seen:
                raise ValueError("DUPLICATE_IDENTITY_REGISTRATION")
            seen[item.identity] = item.lineage


def register_identity(index: IdentityIndex, identity: EntityId, lineage: str) -> Result[IdentityIndex]:
    """Refuse silent overwrite when one scoped ID has two logical lineages."""
    if not isinstance(index, IdentityIndex):
        return _reject("INVALID_ID_SCHEMA", "$.registry", "IdentityIndex", index, "wrong registry")
    try:
        record = IdentityRegistration(identity, lineage)
    except (TypeError, ValueError):
        return _reject("INVALID_ID_SYNTAX", "$.lineage", "typed identity and stable lineage", lineage, "invalid registration")
    previous = [r for r in index.registrations if r.identity == identity]
    if any(r.lineage != lineage for r in previous):
        return _reject("DUPLICATE_LOGICAL_ID", "$.identity", "one lineage per identity", identity, "identity already bound to different lineage")
    if record in index.registrations:
        return Result(index)
    return Result(IdentityIndex(index.registrations + (record,)))


def resolve_entity(ref: EntityRef, view: RecordSnapshot, kind: EntityKind,
                   grants: TrustedEntityImports | None = None, *,
                   require_current: bool = False) -> Result[ResolvedEntity]:
    """G00-API-008: canonical facade; one semantic owner in references."""
    from .references import resolve_entity as resolve_content
    return resolve_content(ref, view, kind, grants, require_current=require_current)


def validate_references(entities: tuple[RecordRevision, ...], view: RecordSnapshot,
                        grants: TrustedEntityImports | None = None) -> ReferenceValidation:
    """G00-API-043: exact local integrity, not the global G-02 graph."""
    from .references import validate_references as validate_content_references
    return validate_content_references(entities, view, grants)
