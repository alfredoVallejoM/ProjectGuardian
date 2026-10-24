"""Read-only inspection of actual B03 records; no mutation or certification."""
from dataclasses import dataclass
from guardian.domain.identity import EntityRef
from guardian.domain.record_base import RecordRevision, ReferenceUse
from guardian.domain.references import (RecordSnapshot, TrustedEntityImports,
    ReferenceValidation, resolve_entity, validate_references, issue)
from guardian.domain.outcomes import Result


@dataclass(frozen=True, slots=True)
class ContractInspection:
    record: RecordRevision
    references: tuple[ReferenceUse, ...]
    reference_validation: ReferenceValidation | None
    historical: bool
    imported: bool

    @property
    def scope_evaluation(self) -> str:
        return 'NOT_EVALUATED'

    @property
    def qualification(self) -> str:
        return 'NOT_CHECKED'

    @property
    def import_boundary(self) -> str:
        return 'RECORD_ONLY_NO_TRANSITIVE_GRANT' if self.imported else 'LOCAL_SNAPSHOT'


def inspect_contract(entity: EntityRef, view: RecordSnapshot,
                     grants: TrustedEntityImports | None = None) -> Result[ContractInspection]:
    if type(entity) is not EntityRef:
        return Result(diagnostics=(issue('INVALID_REFERENCE_INPUT', '$.entity', 'exact entity reference required'),))
    result = resolve_entity(entity, view, entity.kind, grants)
    if not result.ok:
        return Result(diagnostics=result.diagnostics)
    found = result.value
    # Authorization of one imported record never authorizes traversal of every
    # reference mentioned in it. Leave that separate operation visibly unchecked.
    validation = None if found.imported else validate_references((found.record,), view, grants)
    return Result(ContractInspection(found.record, found.record.references(), validation,
                                     found.historical, found.imported))


def inspect_contract_applicability(entity, view, source_view, profile, facts, *, budget=None):
    """B02 -> B03/B06 -> B04: inspect an obligation with its actual scope body.

    A source reference being present is not enough: acquisition, source universe,
    project snapshot, policy revision and scope registry must match the profile.
    This read-only service does not authenticate facts or confer admission.
    """
    from guardian.domain.identity import EntityKind
    from guardian.domain.obligation import ObligationRevision
    from guardian.domain.scope import SupportProfile, FactSet, ScopeRevision
    from guardian.domain.campaign import inspect_due
    from guardian.domain.outcomes import Diagnostic, SourceStatus
    from .project_service import ReadOnlyProjectView

    def fail(code, reason):
        return Result(diagnostics=(Diagnostic(code, '$.applicability',
            'exact source/snapshot/profile context', 'mismatch', reason),))

    if (type(view) is not RecordSnapshot or type(source_view) is not ReadOnlyProjectView
            or type(profile) is not SupportProfile or type(facts) is not FactSet):
        return fail('INVALID_APPLICABILITY_CONTEXT', 'typed contexts required')
    if (view.project_id != source_view.project_id or profile.project_id != view.project_id
            or profile.project_revision != view.revision
            or profile.context.source_universe_ref != source_view.source_universe.identity
            or profile.context.verification_policy_ref not in
                (source_view.definition.source_policy_ref, source_view.definition.constitution_ref)):
        return fail('APPLICABILITY_CONTEXT_MISMATCH', 'profile cannot select another snapshot, universe or policy')
    if facts.context != profile.context:
        return fail('EVIDENCE_CONTEXT_MISMATCH', 'facts belong to another profile')
    for cut in view.sources:
        if not source_view.contains_source(cut.ref) or cut not in source_view.sources:
            return fail('SNAPSHOT_SOURCE_MISMATCH', 'content snapshot has a source outside this source view')
    for source in facts.source_refs:
        if not view.contains_source(source) or not source_view.contains_source(source):
            return fail('EVIDENCE_SOURCE_OUTSIDE_CATALOG', 'unknown source cannot supply applicability evidence')
        entry = next((e for e in source_view.source_universe.entries if e.cut.ref == source), None)
        if entry is None or entry.acquisition not in (SourceStatus.CONTENT_OBSERVED, SourceStatus.SEMANTIC_RECONCILED):
            return fail('EVIDENCE_SOURCE_NOT_OBSERVED', 'source identifier alone is not observed evidence')
    resolved = resolve_entity(entity, view, EntityKind.OBLIGATION)
    if not resolved.ok:
        return Result(diagnostics=resolved.diagnostics)
    if type(resolved.value.record) is not ObligationRevision:
        return fail('WRONG_RECORD_TYPE', 'only an obligation has an applicability contract')
    obligation = resolved.value.record
    scope = resolve_entity(obligation.applicability_ref, view, EntityKind.SCOPE)
    if not scope.ok:
        return Result(diagnostics=scope.diagnostics)
    if type(scope.value.record) is not ScopeRevision:
        return fail('REFERENCED_CONTENT_UNAVAILABLE', 'scope must have an actual expression body')
    return inspect_due(obligation, profile.context.milestone, profile, facts=facts,
                       scope_record=scope.value.record, budget=budget)
