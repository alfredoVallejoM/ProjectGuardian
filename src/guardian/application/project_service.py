"""G00-B02 read-only project and source-universe application boundary."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from guardian.domain.identity import EntityRef
from guardian.domain.project import ProjectDefinition, validate_project
from guardian.domain.source import (
    SourceCut, SourceUniverseRevision, SourceUniverseValidation,
    TrustedImportGrants, check_source_membership, validate_inclusion_exclusion,
    validate_source_universe, describe_source_coverage, SourceCoverageDescriptor,
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
        if type(self.sources) is not tuple or any(not isinstance(s,SourceCut) for s in self.sources):
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
        if any(s!=next(e.cut for e in self.source_universe.entries if e.cut.ref==s.ref)
               for s in self.sources):
            raise ValueError('PROJECT_SOURCES_MISMATCH')
        # Coverage incompleteness is not a structural error; conflicts,
        # duplicate membership and missing catalog entries are.
        fatal={'SOURCE_SCOPE_CONFLICT','DUPLICATE_SOURCE_MEMBERSHIP','UNKNOWN_SOURCE'}
        if any(d.code in fatal for d in validate_inclusion_exclusion(self.source_universe)):
            raise ValueError('INVALID_SOURCE_UNIVERSE_MEMBERSHIP')


    @property
    def project_id(self):
        return self.definition.project_id

    def contains_entity(self, ref: EntityRef) -> bool:
        return (isinstance(ref, EntityRef) and ref.project == self.project_id
                and ref in self.entities)

    def contains_source(self, ref: EntityRef) -> bool:
        return (isinstance(ref, EntityRef) and ref in self.source_universe.included
                and not any(x.cut == ref for x in self.source_universe.excluded)
                and any(s.ref == ref for s in self.sources))


@dataclass(frozen=True, slots=True)
class ProjectInspection:
    definition: ProjectDefinition
    source_coverage: SourceCoverageDescriptor
    missing_references: tuple[EntityRef, ...]
    diagnostics: tuple[Diagnostic, ...]
    qualified: bool = False


def inspect_project_definition(project: object, view: ReadOnlyProjectView | None = None) -> Result[ProjectInspection]:
    """G00-API-057: inspect the actual snapshot without inventing coverage.

    Source policy is supplied as a record; constitution existence must be
    witnessed in the entity catalog. Imports/approvals remain trust inputs.
    """
    valid = validate_project(project)
    if not valid.ok:
        return Result(diagnostics=valid.diagnostics)
    if not isinstance(view, ReadOnlyProjectView) or view.definition != project:
        return Result(diagnostics=(Diagnostic('PROJECT_VIEW_REQUIRED', '$.view',
            'matching immutable snapshot', type(view).__name__, 'inspection requires the project view'),))
    coverage = describe_source_coverage(view.source_universe)
    missing = tuple(ref for ref in (project.constitution_ref,)
                    if not view.contains_entity(ref))
    diagnostics = tuple(Diagnostic('ORPHAN_REFERENCE', '$.constitution',
        'exact entity in snapshot', 'missing', 'constitution content not supplied') for _ in missing)
    diagnostics += tuple(Diagnostic('SOURCE_MISSING', '$.sources',
        'observed source', 'missing', item.reason) for item in coverage.known_missing)
    return Result(ProjectInspection(project, coverage, missing, diagnostics))


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
    if any(x.cut==bundle.source_ref for x in view.source_universe.excluded):
        return Result(diagnostics=(Diagnostic('GSL_SOURCE_EXCLUDED','$.bundle','included and not excluded source','excluded',
                                              'source is explicitly denied by universe'),))
    if bundle.source_ref not in view.source_universe.included:
        return Result(diagnostics=(Diagnostic('GSL_SOURCE_OUTSIDE_UNIVERSE','$.bundle','included pinned source cut','excluded','source not in declared include set'),))
    matching=[x for x in view.sources if x.ref==bundle.source_ref]
    if len(matching)!=1:
        return Result(diagnostics=(Diagnostic('GSL_SOURCE_CUT_MISSING','$.bundle','exact source','missing','no unique source cut'),))
    source=matching[0]
    if not check_source_membership(view.definition,source).allowed:
        return Result(diagnostics=(Diagnostic('GSL_SOURCE_NOT_AUTHORIZED','$.bundle','authorized local pinned source',
                                              'unauthorized','source outside local repository/source policy'),))
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
