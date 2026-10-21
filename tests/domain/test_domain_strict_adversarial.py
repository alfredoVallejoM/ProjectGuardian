"""Adversarial G00-B01: direct construction must not evade nominal invariants."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
import pytest

from guardian.domain.identity import (
    Alias, AliasIndex, AliasBinding, ContentDigest, DigestAlgorithm, EntityId,
    EntityKind, EntityRef, IdentityIndex, IdentityRegistration, ProjectId,
    RevisionId, bind_alias, parse_project_id, resolve_alias,
)
from guardian.domain.outcomes import (
    AuditStatus, ImplementationStatus, MaterialStatus, QualificationStatus,
    StatusAxis, TypedStatus, check_illegal_promotion,
)


def refs():
    p = ProjectId('core-project')
    r = RevisionId('rev-' + '1' * 32)
    subject = EntityRef(p, EntityKind.OBLIGATION,
                        EntityId(p, EntityKind.OBLIGATION, 'test-obligation'), r)
    source = EntityRef(p, EntityKind.SOURCE,
                       EntityId(p, EntityKind.SOURCE, 'test-source'), r)
    return p, subject, source


def test_kind_tag_cannot_masquerade_as_plain_project_string():
    with pytest.raises(TypeError):
        ProjectId(EntityKind.SOURCE)
    assert not parse_project_id(EntityKind.SOURCE).ok
    assert parse_project_id(EntityKind.SOURCE).diagnostics[0].code == 'INVALID_ID_SYNTAX'


def test_alias_indices_refuse_untyped_and_duplicate_input():
    _, target, source = refs()
    binding = AliasBinding(Alias('Historical'), target, source)
    with pytest.raises(TypeError, match='typed bindings'):
        AliasIndex((object(),))
    with pytest.raises(ValueError, match='DUPLICATE_ALIAS_BINDING'):
        AliasIndex((binding, binding))
    with pytest.raises(TypeError, match='expected AliasIndex'):
        bind_alias(None, target, Alias('Historical'), source)
    assert not resolve_alias(None, target.project, target.kind, Alias('Historical')).ok


def test_identity_index_cannot_be_built_with_undisclosed_collisions():
    _, target, _ = refs()
    first = IdentityRegistration(target.entity, 'lineage-one')
    with pytest.raises(ValueError, match='DUPLICATE_LOGICAL_ID'):
        IdentityIndex((first, IdentityRegistration(target.entity, 'lineage-two')))
    with pytest.raises(ValueError, match='DUPLICATE_IDENTITY_REGISTRATION'):
        IdentityIndex((first, first))
    with pytest.raises(TypeError):
        IdentityIndex((first, 'untyped'))


def test_immutable_identity_and_alg_tag_prevents_identity_drift():
    p, target, _ = refs()
    d1 = ContentDigest(DigestAlgorithm.SHA256, 'a' * 64)
    d2 = ContentDigest(DigestAlgorithm.SHA512, 'a' * 128)
    assert d1 != d2
    with pytest.raises(FrozenInstanceError):
        target.revision = RevisionId('rev-' + '2' * 32)
    assert p != target.entity


def test_cross_axis_cannot_promote_from_audit_to_qualification():
    implementation = TypedStatus(StatusAxis.IMPLEMENTATION, ImplementationStatus.DEVELOPMENT_COMPLETE)
    audit = TypedStatus(StatusAxis.AUDIT, AuditStatus.PASS)
    material = TypedStatus(StatusAxis.MATERIAL, MaterialStatus.PASS)
    qualified = TypedStatus(StatusAxis.QUALIFICATION, QualificationStatus.QUALIFIED)
    for candidate in (audit, material, qualified):
        assert check_illegal_promotion(implementation, candidate).diagnostics[0].code == 'ILLEGAL_STATUS_PROMOTION'
