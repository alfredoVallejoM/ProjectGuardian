"""Actual source view -> obligation record -> resolved ScopeRevision -> evaluation."""
from dataclasses import replace
import pytest
from foundation_b04 import scoped_fixture, contains
from guardian.domain.identity import RevisionId
from guardian.domain.scope import StepBudget, ScopeRevision, EvaluationStatus
from guardian.domain.outcomes import DueStatus, SourceStatus
from guardian.application.contract_service import inspect_contract, inspect_contract_applicability
from guardian.domain.references import resolve_entity
from guardian.domain.identity import EntityKind as K


def test_scope_body_replaces_anchor_and_future_obligation_remains_future():
    _,_,records,snapshot,ids,source_view,p,f,scope=scoped_fixture()
    r=resolve_entity(records[5].applicability_ref,snapshot,K.SCOPE)
    assert r.ok and r.value.record is scope
    inspection=inspect_contract(ids['obligation-now'],snapshot)
    assert inspection.ok
    assert all('scope_ref' not in d.path and 'applicability_ref' not in d.path
               for d in inspection.value.reference_validation.diagnostics)
    # VerificationSpec still has no body; no placeholder or synthetic PASS.
    assert any(d.code=='REFERENCED_CONTENT_UNAVAILABLE' for d in inspection.value.reference_validation.diagnostics)
    for identity in ('obligation-now','obligation-future','obligation-research'):
        result=inspect_contract_applicability(ids[identity],snapshot,source_view,p,f)
        assert result.ok and result.value.applicability=='YES'
        assert result.value.admission=='NOT_CHECKED' and result.value.normatively_due is None
    assert records[6].due is DueStatus.FUTURE


def test_missing_scope_content_or_evidence_never_excludes_the_obligation():
    _,_,records,snapshot,ids,sv,p,f,scope=scoped_fixture(observations=False)
    result=inspect_contract_applicability(ids['obligation-now'],snapshot,sv,p,f)
    assert result.ok and result.value.applicability=='UNKNOWN'
    without=replace(snapshot,records=tuple(r for r in snapshot.records if type(r) is not ScopeRevision))
    result=inspect_contract_applicability(ids['obligation-now'],without,sv,p,f)
    assert not result.ok and result.diagnostics[0].code=='REFERENCED_CONTENT_UNAVAILABLE'
    limited=inspect_contract_applicability(ids['obligation-now'],snapshot,sv,p,f,budget=StepBudget(max_steps=1))
    assert not limited.ok and limited.diagnostics[0].code=='EVALUATION_RESOURCE_LIMITED'


@pytest.mark.parametrize('target',('snapshot','policy','universe','registry'))
def test_profile_cannot_silently_select_a_different_context(target):
    _,_,_,snapshot,ids,sv,p,f,scope=scoped_fixture();rev=RevisionId('rev-'+'1'*32)
    if target=='snapshot':p=replace(p,context=replace(p.context,project_revision=rev))
    elif target=='policy':p=replace(p,context=replace(p.context,verification_policy_ref=replace(p.context.verification_policy_ref,revision=rev)))
    elif target=='universe':p=replace(p,context=replace(p.context,source_universe_ref=replace(p.context.source_universe_ref,revision=rev)))
    else:
        p=replace(p,context=replace(p.context,registry_revision=rev),registry=replace(p.registry,revision=rev))
    # Empty observations isolate profile selection from witness matching.
    f=replace(f,context=p.context,dimensions=())
    r=inspect_contract_applicability(ids['obligation-now'],snapshot,sv,p,f)
    assert not r.ok and r.diagnostics[0].code in ('APPLICABILITY_CONTEXT_MISMATCH','DUE_SCOPE_CONTEXT_MISMATCH')


def test_unobserved_sources_cannot_supply_applicability_witnesses():
    _,_,_,snapshot,ids,sv,p,f,_=scoped_fixture()
    changed=replace(sv.source_universe,entries=tuple(replace(e,acquisition=SourceStatus.IDENTIFIED) for e in sv.source_universe.entries))
    source_view=replace(sv,source_universe=changed)
    r=inspect_contract_applicability(ids['obligation-now'],snapshot,source_view,p,f)
    assert not r.ok and r.diagnostics[0].code=='EVIDENCE_SOURCE_NOT_OBSERVED'
