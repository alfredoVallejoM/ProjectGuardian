"""G00-B02 read-only project and source-universe application boundary."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from guardian.domain.identity import EntityRef
from guardian.domain.project import ProjectDefinition, validate_project
from guardian.domain.source import (
    SourceCut, SourceUniverseRevision, SourceUniverseValidation,
    TrustedImportGrants, validate_source_universe,
)
from guardian.domain.outcomes import Diagnostic, Result, SourceStatus
from guardian.spec_lang.contract import SourceBundle, CompileContext, verify_source_context


@dataclass(frozen=True,slots=True)
class ReadOnlyProjectView:
    definition:ProjectDefinition
    source_universe:SourceUniverseRevision
    sources:tuple[SourceCut,...]
    entities:tuple[EntityRef,...]=()

    def __post_init__(self)->None:
        if (not isinstance(self.definition,ProjectDefinition) or not isinstance(self.source_universe,SourceUniverseRevision)
                or self.source_universe.identity.project!=self.definition.project_id):
            raise ValueError('PROJECT_SNAPSHOT_INVALID')
        if type(self.sources) is not tuple or any(not hasattr(s,'ref') for s in self.sources):
            raise TypeError('sources must be frozen typed cuts')
        if len({s.ref for s in self.sources})!=len(self.sources):
            raise ValueError('DUPLICATE_LOGICAL_ID')
        if type(self.entities) is not tuple or any(not isinstance(e,EntityRef) for e in self.entities):
            raise TypeError('project view entities must be pinned references')
        if len(set(self.entities))!=len(self.entities):
            raise ValueError('DUPLICATE_LOGICAL_ID')
        if any(e.project!=self.definition.project_id for e in self.entities):
            raise ValueError('FORBIDDEN_CROSS_PROJECT_REF')
        if {s.ref for s in self.sources}!={e.cut.ref for e in self.source_universe.entries}:
            raise ValueError('PROJECT_SOURCES_MISMATCH')


def inspect_project_definition(project:object)->Result[ProjectDefinition]:
    return validate_project(project)


def build_readonly_project_view(definition:ProjectDefinition,universe:SourceUniverseRevision,
                                 catalog:Mapping[EntityRef,SourceCut],entities:tuple[EntityRef,...]=(),
                                 grants:TrustedImportGrants|None=None, *,
                                 trusted_exclusion_decisions:frozenset[EntityRef]|None=None)->Result[ReadOnlyProjectView]:
    if not isinstance(definition,ProjectDefinition) or not isinstance(universe,SourceUniverseRevision) or not isinstance(catalog,Mapping):
        return Result(diagnostics=(Diagnostic('PROJECT_SNAPSHOT_INVALID','$.project','project+universe+catalog','untyped','invalid source inputs'),))
    validation=validate_source_universe(universe,definition,catalog,grants,
                                        trusted_exclusion_decisions=trusted_exclusion_decisions)
    blocking=tuple(d for d in validation.diagnostics if d.code not in ('SOURCE_COVERAGE_UNKNOWN',))
    if blocking:
        return Result(diagnostics=blocking)
    try:
        # Source gaps do not disappear: view keeps source_universe and known_missing.
        return Result(ReadOnlyProjectView(definition,universe,tuple(e.cut for e in universe.entries),entities))
    except (TypeError,ValueError) as exc:
        return Result(diagnostics=(Diagnostic('PROJECT_SNAPSHOT_INVALID','$.view','consistent immutable view','invalid',str(exc)),))


def verify_bundle_in_project(view:ReadOnlyProjectView,bundle:SourceBundle,context:CompileContext)->Result[SourceBundle]:
    """Validate connection, not source authenticity, normative acceptance or qualification."""
    if not isinstance(view,ReadOnlyProjectView) or not isinstance(bundle,SourceBundle) or not isinstance(context,CompileContext):
        return Result(diagnostics=(Diagnostic('GSL_PROJECT_CONTEXT_INVALID','$.bundle','typed project/source/compiler','untyped','invalid inputs'),))
    if view.definition.project_id!=bundle.project or context.project!=bundle.project:
        return Result(diagnostics=(Diagnostic('GSL_FOREIGN_PROJECT','$.bundle','same project','foreign','cross-project compilation'),))
    if bundle.source_ref not in view.source_universe.included:
        return Result(diagnostics=(Diagnostic('GSL_SOURCE_OUTSIDE_UNIVERSE','$.bundle','included pinned source cut','excluded','source not in declared include set'),))
    matching=[x for x in view.sources if x.ref==bundle.source_ref]
    if len(matching)!=1:
        return Result(diagnostics=(Diagnostic('GSL_SOURCE_CUT_MISSING','$.bundle','exact source','missing','no unique source cut'),))
    source=matching[0]
    entries=[x for x in view.source_universe.entries if x.cut.ref==bundle.source_ref]
    if len(entries)!=1 or entries[0].acquisition not in (SourceStatus.CONTENT_OBSERVED,SourceStatus.SEMANTIC_RECONCILED):
        return Result(diagnostics=(Diagnostic('GSL_SOURCE_NOT_OBSERVED','$.bundle','material source content observed','unknown','source acquisition state not sufficient'),))
    if source.observed_digest is not None and source.observed_digest!=bundle.expected_digest:
        return Result(diagnostics=(Diagnostic('GSL_SOURCE_DIGEST_MISMATCH','$.bundle','matching cut digest','mismatch','source observed digest differs'),))
    return verify_source_context(bundle,context)


def analyze_project_source(view:ReadOnlyProjectView,bundle:SourceBundle,context:CompileContext,*,source_format:str):
    """B02→LC03 read-only vertical, with project scope, cut and content checks.

    This is a contextual front-end ANALYSIS, not a normative admission.
    """
    from guardian.spec_lang.syntax import FrontendAnalysis,analyze_source
    from guardian.spec_lang.contract import CompileStatus,CompilationStage
    allowed=verify_bundle_in_project(view,bundle,context)
    if not allowed.ok:
        return FrontendAnalysis(CompileStatus.REJECTED,CompilationStage.ACQUIRE,(),allowed.diagnostics)
    return analyze_source(bundle,context,source_format=source_format)
