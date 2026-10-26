"""Read-only B02 -> B05/B06 -> B04 -> B07 product integration.

Authentication of AuthorityContext and policy installation remain external.
This service never obtains approval from a field written by the candidate.
"""
from guardian.domain.identity import EntityKind
from guardian.domain.outcomes import Diagnostic, Result
from guardian.domain.references import RecordSnapshot, resolve_entity
from guardian.domain.constitution import ConstitutionRevision
from guardian.constitution.evaluator import EvaluationRequest, EvaluationBudget, evaluate_constitution
from .project_service import ReadOnlyProjectView


def evaluate_project_constitution(source_view, snapshot, facts, profile, authority, registry,
                                  candidate_ref, *, budget=None, entity_imports=None,
                                  source_imports=None, dependencies=None):
    if type(source_view) is not ReadOnlyProjectView or type(snapshot) is not RecordSnapshot:
        return Result(diagnostics=(Diagnostic('PROJECT_EVALUATION_VIEW_REQUIRED', '$.view',
            'explicit source view and record snapshot', 'invalid', 'no implicit current project'),))
    if source_view.project_id != snapshot.project_id:
        return Result(diagnostics=(Diagnostic('PROJECT_EVALUATION_CONTEXT_MISMATCH', '$.view',
            'same project', 'foreign', 'separate projects cannot share authority implicitly'),))
    if any(not source_view.contains_source(c.ref) or c not in source_view.sources for c in snapshot.sources):
        return Result(diagnostics=(Diagnostic('SNAPSHOT_SOURCE_MISMATCH', '$.sources',
            'exact included material cuts', 'mismatch', 'same nominal source is not enough'),))
    resolution=resolve_entity(source_view.definition.constitution_ref,snapshot,EntityKind.CONSTITUTION)
    if not resolution.ok:return Result(diagnostics=resolution.diagnostics)
    if type(resolution.value.record) is not ConstitutionRevision:
        return Result(diagnostics=(Diagnostic('CONSTITUTION_BODY_REQUIRED', '$.constitution',
            'actual ConstitutionRevision', 'anchor', 'no placeholder is evaluated'),))
    request=EvaluationRequest(resolution.value.record,snapshot,source_view.definition,
        source_view.source_universe,facts,profile,authority,candidate_ref,
        budget if budget is not None else EvaluationBudget(),entity_imports,source_imports,dependencies)
    try:
        return Result(evaluate_constitution(request,registry))
    except (ValueError,TypeError,AttributeError) as exc:
        return Result(diagnostics=(Diagnostic('INVALID_EVALUATION_INPUT', '$.request',
            'typed constitutional request', 'invalid', str(exc)),))
