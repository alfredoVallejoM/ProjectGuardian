"""G00-01-F01..F10 behavior and G00-ADV01..03 identity falsations."""
import dataclasses
import json

import pytest

from guardian.domain.identity import (
    Alias, AliasIndex, ContentDigest, DigestAlgorithm, EntityId, EntityKind,
    EntityRef, IdentityIndex, ProjectId, RevisionId, bind_alias, decode_identity,
    encode_identity, parse_content_digest, parse_entity_id, parse_project_id,
    parse_revision_id, register_identity, resolve_alias,
)

P = ProjectId("project-alpha")
Q = ProjectId("project-beta")
R1 = RevisionId("rev-" + "a" * 32)
R2 = RevisionId("rev-" + "b" * 32)


def entity(project=P, kind=EntityKind.OBLIGATION, value="obligation-01", revision=R1):
    eid = EntityId(project, kind, value)
    return EntityRef(project, kind, eid, revision)


def source(project=P):
    return entity(project, EntityKind.SOURCE, "source-001")


def code(result):
    assert not result.ok
    return result.diagnostics[0].code


def test_f01_nominal_wrappers_are_runtime_distinct():
    assert parse_project_id("project-alpha").value == P
    assert parse_entity_id(P, EntityKind.OBLIGATION, "obligation-01").value == entity().entity
    assert parse_revision_id(R1.value).value == R1
    assert parse_content_digest(DigestAlgorithm.SHA256, "f" * 64).ok
    assert P != R1
    with pytest.raises(TypeError):
        EntityId("project-alpha", EntityKind.OBLIGATION, "obligation-01")
    assert code(parse_entity_id(R1, EntityKind.OBLIGATION, "obligation-01")) == "PROJECT_REQUIRED"


def test_f02_project_and_kind_are_in_identity_equality():
    assert EntityId(P, EntityKind.OBLIGATION, "entity-001") != EntityId(Q, EntityKind.OBLIGATION, "entity-001")
    assert EntityId(P, EntityKind.OBLIGATION, "entity-001") != EntityId(P, EntityKind.PROPERTY, "entity-001")
    with pytest.raises(ValueError):
        EntityRef(Q, EntityKind.OBLIGATION, entity().entity, R1)


@pytest.mark.parametrize("raw", ["", "..", "../etc/passwd", "Aaa", "ab", "_bad", "x/y", "x:y", "x ", "x" * 97])
def test_f03_rejects_invalid_tokens(raw):
    assert not parse_project_id(raw).ok
    assert not parse_entity_id(P, EntityKind.SOURCE, raw).ok


def test_f03_errors_have_stable_location_and_reason():
    issue = parse_project_id("bad/path", "$.project").diagnostics[0]
    assert (issue.code, issue.path, issue.expected) == ("INVALID_ID_SYNTAX", "$.project", "ProjectId")
    assert issue.reason


def test_f04_alias_is_scoped_provenanced_and_never_first_wins():
    idx = AliasIndex()
    a = Alias("Misma obligaci\xf3n")
    first = bind_alias(idx, entity(), a, source())
    assert not first.diagnostics
    assert resolve_alias(first.index, P, EntityKind.OBLIGATION, a).value == entity()
    second = bind_alias(first.index, entity(value="obligation-02"), a, source())
    assert [i.code for i in second.diagnostics] == ["AMBIGUOUS_ALIAS"]
    assert code(resolve_alias(second.index, P, EntityKind.OBLIGATION, a)) == "AMBIGUOUS_ALIAS"
    cross = bind_alias(second.index, entity(project=Q), a, source(Q))
    assert not cross.diagnostics
    assert resolve_alias(cross.index, Q, EntityKind.OBLIGATION, a).value == entity(Q)


def test_f05_rename_is_not_a_new_id():
    idx = bind_alias(AliasIndex(), entity(), Alias("Antes"), source()).index
    idx = bind_alias(idx, entity(), Alias("Despu\xe9s"), source()).index
    assert resolve_alias(idx, P, EntityKind.OBLIGATION, Alias("Antes")).value == entity()
    assert resolve_alias(idx, P, EntityKind.OBLIGATION, Alias("Despu\xe9s")).value == entity()
    assert len({x.target.entity for x in idx.bindings}) == 1


def test_f06_revision_must_be_pinned_and_exact():
    assert code(parse_revision_id("HEAD")) == "INVALID_REVISION"
    assert code(parse_revision_id("main")) == "INVALID_REVISION"
    assert code(parse_revision_id(None)) == "REVISION_REQUIRED"
    assert entity(revision=R1) != entity(revision=R2)
    with pytest.raises(TypeError):
        EntityRef(P, EntityKind.OBLIGATION, entity().entity, "main")


def test_f07_digest_algorithm_and_full_length_canonicalization():
    a = parse_content_digest(DigestAlgorithm.SHA256, "A" * 64)
    assert a.ok and a.value.hex == "a" * 64
    assert code(parse_content_digest("sha256", "a" * 64)) == "UNSUPPORTED_DIGEST"
    assert code(parse_content_digest(DigestAlgorithm.SHA256, "a" * 8)) == "DIGEST_MALFORMED"
    assert code(parse_content_digest(DigestAlgorithm.SHA256, "z" * 64)) == "DIGEST_MALFORMED"
    assert ContentDigest(DigestAlgorithm.SHA256, "a" * 64) != ContentDigest(DigestAlgorithm.SHA512, "a" * 128)


def test_f08_domain_accepts_given_ids_without_clock_or_randomness(monkeypatch):
    import time
    import uuid
    def fail(*args, **kwargs):
        raise AssertionError("environmental dependency")
    monkeypatch.setattr(time, "time", fail)
    monkeypatch.setattr(uuid, "uuid4", fail)
    for _ in range(3):
        assert parse_project_id("project-alpha").value == P
        assert parse_revision_id(R1.value).value == R1


@pytest.mark.parametrize("identity", [P, EntityId(P, EntityKind.PROPERTY, "property-01"), R1,
    ContentDigest(DigestAlgorithm.SHA512, "b" * 128), entity()])
def test_f09_typed_codec_roundtrip(identity):
    envelope = encode_identity(identity)
    value = decode_identity(json.loads(json.dumps(envelope)))
    assert value.ok and value.value == identity
    assert type(value.value) is type(identity)


def test_f09_codec_fail_closed_no_kind_loss_or_unknown_features():
    data = encode_identity(entity())
    del data["entity_kind"]
    assert code(decode_identity(data)) == "INVALID_ID_SCHEMA"
    data = encode_identity(P)
    data["normative_new_feature"] = True
    assert code(decode_identity(data)) == "INVALID_ID_SCHEMA"
    data = encode_identity(P)
    data["schema"] = "guardian.identity/v2"
    assert code(decode_identity(data)) == "INVALID_ID_SCHEMA"
    assert code(decode_identity({"schema": "guardian.identity/v1", "type": "unknown"})) == "UNKNOWN_ID_KIND"
    assert code(decode_identity({"schema": "guardian.identity/v1", "type": []})) == "UNKNOWN_ID_KIND"


def test_f10_registry_detects_same_id_distinct_lineages():
    eid = entity().entity
    first = register_identity(IdentityIndex(), eid, "lineage-one")
    assert first.ok
    assert register_identity(first.value, eid, "lineage-one").value == first.value
    assert code(register_identity(first.value, eid, "lineage-two")) == "DUPLICATE_LOGICAL_ID"
    assert register_identity(first.value, EntityId(Q, EntityKind.OBLIGATION, eid.value), "lineage-two").ok


def test_adversarial_01_same_text_never_cross_type_decodes():
    assert code(parse_revision_id(P.value)) == "INVALID_REVISION"
    raw = encode_identity(P)
    raw["type"] = "revision_id"
    assert code(decode_identity(raw)) == "INVALID_ID_SCHEMA"


def test_adversarial_02_reference_missing_semantic_kind_is_rejected():
    raw = encode_identity(entity())
    del raw["entity_kind"]
    assert code(decode_identity(raw)) == "INVALID_ID_SCHEMA"


def test_adversarial_03_duplicate_alias_is_ambiguous_regardless_of_order():
    a = Alias("same")
    b1 = bind_alias(AliasIndex(), entity(value="obligation-01"), a, source()).index.bindings[0]
    b2 = bind_alias(AliasIndex(), entity(value="obligation-02"), a, source()).index.bindings[0]
    for order in ((b1, b2), (b2, b1)):
        assert code(resolve_alias(AliasIndex(order), P, EntityKind.OBLIGATION, a)) == "AMBIGUOUS_ALIAS"


def test_immutability_and_exact_collision_behavior():
    initial = AliasIndex()
    next_one = bind_alias(initial, entity(), Alias("Sample"), source())
    assert len(initial.bindings) == 0
    assert next_one.index != initial
    assert next_one.diagnostics == ()
    same = bind_alias(next_one.index, entity(), Alias("Sample"), source())
    assert [d.code for d in same.diagnostics] == ["DUPLICATE_BINDING"]
    with pytest.raises(dataclasses.FrozenInstanceError):
        P.value = "project-beta"
