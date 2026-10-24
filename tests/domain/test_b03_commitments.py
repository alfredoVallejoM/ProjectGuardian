"""G00-05-F01..F10, ADV-13..15: behavior, not file-count assertions."""
from dataclasses import FrozenInstanceError, fields, replace
import pytest
from foundation_b03 import scenario
from guardian.domain.identity import EntityKind as K
from guardian.domain.outcomes import DecisionStatus, DueStatus
from guardian.domain.objective import ObjectiveRevision, validate_objective
from guardian.domain.capability import CapabilityRevision, SemanticOwner, validate_capability
from guardian.domain.property import PropertyRevision, AssertionKind, validate_property
from guardian.domain.obligation import ObligationRevision, Prerequisites, DependencyMode, validate_obligation
from guardian.domain.campaign import CampaignRevision, Membership, MembershipMode, inspect_due, validate_campaign
from guardian.domain.architecture import ArchitectureRevision, Component, validate_architecture_contract
from guardian.domain.references import RecordSnapshot, resolve_entity
from foundation_b02 import entity

VALIDATORS = {ObjectiveRevision: validate_objective, CapabilityRevision: validate_capability,
    PropertyRevision: validate_property, ObligationRevision: validate_obligation,
    CampaignRevision: validate_campaign, ArchitectureRevision: validate_architecture_contract}


@pytest.mark.parametrize('index', range(11))
def test_all_six_record_classes_validate_with_real_project_and_source_view(index):
    _, _, records, snapshot, _ = scenario()
    record = records[index]
    assert VALIDATORS[type(record)](record, snapshot).ok
    assert not record.normatively_admitted


def test_f01_objective_is_not_a_task_or_completed_flag():
    _, _, records, _, _ = scenario()
    obj = records[0]
    assert obj.purpose and obj.success_criteria and len(obj.capability_refs) == 2
    with pytest.raises(TypeError):
        ObjectiveRevision(identity=obj.identity, source_refs=obj.source_refs, scope_ref=obj.scope_ref,
            purpose='goal', success_criteria=('criterion',), completed=True)
    with pytest.raises(ValueError, match='OBJECTIVE_CRITERIA_REQUIRED'):
        replace(obj, success_criteria=())


def test_f02_capability_requires_behavior_owner_and_contracts_not_implementation_path():
    p, _, records, snapshot, _ = scenario()
    cap = records[2]
    assert validate_capability(cap, snapshot).ok
    for values in (dict(behavior=''), dict(input_contracts=()), dict(output_contracts=()), dict(property_refs=())):
        with pytest.raises((ValueError, TypeError)):
            replace(cap, **values)
    other = scenario('project-beta')[0]
    with pytest.raises(ValueError, match='INVALID_CAPABILITY_OWNER'):
        replace(cap, owner=SemanticOwner(other.project_id, 'formal-contracts'))


def test_f03_f09_shared_property_and_multiple_objectives_keep_one_identity():
    _, _, records, snapshot, ids = scenario()
    assert records[2].property_refs == records[3].property_refs == (ids['property-shared'],)
    assert len(records[2].objective_refs) == 2
    a = resolve_entity(records[2].property_refs[0], snapshot, K.PROPERTY)
    b = resolve_entity(records[3].property_refs[0], snapshot, K.PROPERTY)
    assert a.ok and b.ok and a.value.record is b.value.record
    assert sum(r.identity == ids['property-shared'] for r in snapshot.records) == 1
    assert not a.value.normatively_admitted


@pytest.mark.parametrize('field', ['acceptance_contract', 'falsification_contract', 'verification_spec_refs', 'required_property_refs'])
@pytest.mark.parametrize('invalid', [None, [], ()])
def test_f04_f05_required_obligation_contracts_cannot_be_missing_null_or_empty(field, invalid):
    obligation = scenario()[2][5]
    with pytest.raises((TypeError, ValueError)):
        replace(obligation, **{field: invalid})


def test_f06_verification_contract_reference_never_creates_run_or_pass():
    _, _, records, snapshot, _ = scenario()
    prop = records[4]; obligation = records[5]
    assert validate_property(prop, snapshot).ok and validate_obligation(obligation, snapshot).ok
    assert prop.verification_spec_refs == obligation.verification_spec_refs
    for rec in records:
        assert not {'completed', 'verified', 'migrated', 'material_status', 'qualification'} & {f.name for f in fields(rec)}


def test_f07_architecture_is_normative_not_observed_and_conflicting_rules_fail():
    arch = scenario()[2][-1]
    assert validate_architecture_contract(arch).ok
    with pytest.raises(ValueError, match='CONFLICTING_DEPENDENCY_RULE'):
        replace(arch, forbidden_dependencies=arch.allowed_dependencies)
    with pytest.raises(ValueError, match='DUPLICATE_OWNER'):
        replace(arch, components=(arch.components[0], arch.components[0]))
    with pytest.raises(ValueError, match='INVALID_DEPENDENCY_RULE'):
        replace(arch, allowed_dependencies=(('application', 'phantom'),))
    with pytest.raises(ValueError, match='REQUIRED_DEPENDENCY_NOT_ALLOWED'):
        replace(arch, allowed_dependencies=())


def test_f08_membership_is_reference_not_a_copy_and_no_auto_closure():
    _, _, records, snapshot, ids = scenario()
    c1, c2 = records[8:10]
    assert c1.membership == c2.membership
    assert resolve_entity(c1.membership[0].obligation, snapshot, K.OBLIGATION).value.record is records[5]
    assert resolve_entity(c2.membership[0].obligation, snapshot, K.OBLIGATION).value.record is records[5]
    with pytest.raises(ValueError, match='AMBIGUOUS_MEMBERSHIP'):
        replace(c1, membership=c1.membership + (c1.membership[0],))


def test_f10_future_research_and_current_are_not_changed_by_validation():
    _, _, records, snapshot, _ = scenario()
    for record, expected in zip(records[5:8], (DueStatus.CURRENT, DueStatus.FUTURE, DueStatus.RESEARCH)):
        assert validate_obligation(record, snapshot).ok
        result = inspect_due(record, 'm1').value
        assert result.declared_due is expected and result.at_declared_milestone
        assert result.applicability == 'NOT_EVALUATED' and result.admission == 'NOT_CHECKED'
        assert inspect_due(record, 'm2').value.declared_due is expected
        assert not inspect_due(record, 'm2').value.at_declared_milestone


def test_proposal_approved_label_is_never_authenticated_by_constructor():
    p, _, records, _, _ = scenario()
    with pytest.raises(ValueError, match='AUTHORITY_REF_REQUIRED'):
        replace(records[0], declared_status=DecisionStatus.APPROVED)
    candidate = replace(records[0], declared_status=DecisionStatus.APPROVED,
                        authority_ref=p.constitution_ref)
    assert not candidate.normatively_admitted


@pytest.mark.parametrize('index', range(11))
def test_record_constructors_are_transitively_immutable_and_namespace_checked(index):
    _, _, records, snapshot, _ = scenario()
    record = records[index]
    with pytest.raises(FrozenInstanceError):
        record.source_refs = ()
    with pytest.raises(TypeError):
        replace(record, source_refs=list(record.source_refs))
    other = scenario('project-beta')[3]
    result = VALIDATORS[type(record)](record, other)
    assert not result.ok and result.diagnostics[0].code == 'WRONG_PROJECT'


def test_foreign_and_missing_fields_fail_with_the_field_path():
    _, _, records, snapshot, _ = scenario()
    other = scenario('project-beta')
    bad = replace(records[2], property_refs=(other[4]['property-shared'],))
    result = validate_capability(bad, snapshot)
    assert not result.ok
    assert [(d.code, d.path) for d in result.diagnostics] == [('FORBIDDEN_CROSS_PROJECT_REF', '$.property_refs[0]')]
    missing = entity(snapshot.project_id, K.PROPERTY, 'property-missing')
    assert validate_capability(replace(records[2], property_refs=(missing,)), snapshot).diagnostics[0].code == 'ORPHAN_REFERENCE'


def test_prerequisites_and_alternative_membership_are_explicit_not_empty_all():
    _, _, records, _, ids = scenario()
    ob = records[5]
    for mode in DependencyMode:
        with pytest.raises(TypeError, match='PREREQUISITES_REQUIRED'):
            Prerequisites(mode, ())
    with pytest.raises(TypeError, match='PREREQUISITE_CONDITION_REQUIRED'):
        Prerequisites(DependencyMode.CONDITIONAL, (ids['obligation-future'],))
    condition = Prerequisites(DependencyMode.CONDITIONAL, (ids['obligation-future'],), ob.scope_ref)
    assert replace(ob, prerequisites=condition).references()[-1].target == ob.scope_ref
    with pytest.raises(ValueError, match='ALTERNATIVE_POLICY_REQUIRED'):
        Membership(ob.identity, ob.scope_ref, 'm1', MembershipMode.ALTERNATIVE)
    assert Membership(ob.identity, ob.scope_ref, 'm1', MembershipMode.ALTERNATIVE, 'alternative-a')


@pytest.mark.parametrize('index', range(11))
def test_wrong_record_kind_never_becomes_another_domain_entity(index):
    _, _, records, _, ids = scenario()
    record = records[index]
    bad = ids['property-shared'] if record.identity.kind is not K.PROPERTY else ids['objective-one']
    with pytest.raises(TypeError, match='RECORD_KIND_MISMATCH'):
        replace(record, identity=bad)
