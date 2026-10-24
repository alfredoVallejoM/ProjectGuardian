"""B04 fixtures using the real B02/B03/B06 source and record services."""
from dataclasses import replace
from foundation_b02 import entity, universe
from foundation_b03 import scenario
from guardian.domain.identity import EntityKind as K, RevisionId
from guardian.domain.scope import (ScopeContext, ScopeWitness, SupportProfile, FactSet,
    DimensionObservation, DimensionValue, ValueKind, foundation_dimension_registry,
    Atom, Operator, ScopeRevision)
from guardian.application.project_service import build_readonly_project_view


def fixture(name='project-alpha'):
    p, s, records, snapshot, ids = scenario(name)
    u = universe(p, (s,))
    source_view = build_readonly_project_view(p, u, {s.ref:s}, entities=snapshot.anchors).value
    registry = foundation_dimension_registry(RevisionId('rev-'+'e'*32))
    context = ScopeContext(p.project_id, snapshot.revision, RevisionId('rev-'+'f'*32), registry.revision,
        u.identity, p.source_policy_ref, 'm1')
    profile = SupportProfile(context, registry)
    facts = FactSet(context, frozenset({s.ref}))
    return p, s, records, snapshot, ids, source_view, profile, facts


def witness(profile, source, name='observation-main'):
    return ScopeWitness(profile.context, source.ref, name, 'Observed in the supplied immutable source cut')


def observation(profile, source, values=('feature-x',), complete=False, name='observation-main'):
    w = witness(profile, source, name)
    return DimensionObservation('features', 'v1', DimensionValue(ValueKind.TEXT_SET, frozenset(values)),
        (w,), complete, (w,) if complete else ())


def contains(name='feature-x'):
    return Atom('features', Operator.CONTAINS, DimensionValue(ValueKind.TEXT, name))


def scoped_fixture(observations=True):
    p,s,records,snapshot,ids,sv,profile,facts=fixture()
    scope = ScopeRevision(identity=records[5].applicability_ref, source_refs=(s.ref,),
        scope_ref=records[5].applicability_ref, registry=profile.registry, expression=contains())
    snapshot=replace(snapshot, records=snapshot.records+(scope,))
    if observations:
        facts=replace(facts, dimensions=(observation(profile,s),))
    return p,s,records,snapshot,ids,sv,profile,facts,scope
