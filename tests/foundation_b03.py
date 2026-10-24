"""Real immutable B03 records on the productive B02 project/source boundary."""
from foundation_b02 import project, cut, universe, entity, bundle_context
from guardian.domain.identity import EntityKind as K, RevisionId
from guardian.domain.outcomes import DueStatus
from guardian.domain.objective import ObjectiveRevision
from guardian.domain.capability import CapabilityRevision, SemanticOwner
from guardian.domain.property import PropertyRevision, AssertionKind
from guardian.domain.obligation import ObligationRevision, CommitmentKind
from guardian.domain.campaign import CampaignRevision, Membership
from guardian.domain.architecture import ArchitectureRevision, Component
from guardian.application.project_service import build_readonly_project_view, build_record_snapshot


def scenario(name='project-alpha'):
    p = project(name); s = cut(p)
    scope = entity(p.project_id, K.SCOPE, 'scope-main')
    proof = entity(p.project_id, K.VERIFICATION, 'verification-main')
    owner = SemanticOwner(p.project_id, 'formal-contracts')
    ids = {name: entity(p.project_id, kind, name) for name, kind in (
        ('objective-one', K.OBJECTIVE), ('objective-two', K.OBJECTIVE),
        ('capability-one', K.CAPABILITY), ('capability-two', K.CAPABILITY),
        ('property-shared', K.PROPERTY), ('obligation-now', K.OBLIGATION),
        ('obligation-future', K.OBLIGATION), ('obligation-research', K.OBLIGATION),
        ('campaign-one', K.CAMPAIGN), ('campaign-two', K.CAMPAIGN), ('architecture-main', K.ARCHITECTURE))}
    def header(key):
        return dict(identity=ids[key], source_refs=(s.ref,), scope_ref=scope)
    records = [ObjectiveRevision(**header(x), purpose='Preserve exact contracts', success_criteria=('No lost identity',),
                    capability_refs=(ids['capability-one'], ids['capability-two'])) for x in ('objective-one', 'objective-two')]
    records += [CapabilityRevision(**header(x), owner=owner, behavior='Resolve a pinned contract',
                    input_contracts=('EntityRef and snapshot',), output_contracts=('Exact record or issue',),
                    contract_version='v1', property_refs=(ids['property-shared'],),
                    objective_refs=(ids['objective-one'], ids['objective-two'])) for x in ('capability-one', 'capability-two')]
    records += [PropertyRevision(**header('property-shared'), statement='Identity is preserved',
                    hypotheses=('Source revision is pinned',), guarantee='No latest fallback',
                    assertion_kind=AssertionKind.REQUIRED, verification_spec_refs=(proof,))]
    records += [ObligationRevision(**header(x), kind=CommitmentKind.BEHAVIOR, statement='Resolve exactly',
                    applicability_ref=scope, owner=owner, due=due, milestone='m1',
                    required_property_refs=(ids['property-shared'],), acceptance_contract=('Exact body returned',),
                    falsification_contract=('Wrong revision must fail',), verification_spec_refs=(proof,))
                for x, due in (('obligation-now', DueStatus.CURRENT), ('obligation-future', DueStatus.FUTURE),
                               ('obligation-research', DueStatus.RESEARCH))]
    records += [CampaignRevision(**header(x), title=x,
                    membership=(Membership(ids['obligation-now'], scope, 'm1'),
                                Membership(ids['obligation-future'], scope, 'm2')),
                    closure_policy=('All required contracts with evidence',)) for x in ('campaign-one', 'campaign-two')]
    records += [ArchitectureRevision(**header('architecture-main'), components=(
                    Component('domain', owner, ('validate',)), Component('application', owner, ('inspect',))),
                    allowed_dependencies=(('application', 'domain'),),
                    required_dependencies=(('application', 'domain'),),
                    forbidden_dependencies=(('domain', 'application'),))]
    anchors = (scope, proof, p.constitution_ref)
    v = build_readonly_project_view(p, universe(p, (s,)), {s.ref: s}, entities=anchors).value
    result = build_record_snapshot(v, tuple(records), RevisionId('rev-'+'d'*32))
    assert result.ok, result.diagnostics
    return p, s, tuple(records), result.value, ids
