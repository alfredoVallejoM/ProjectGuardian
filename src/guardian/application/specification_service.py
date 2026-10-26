"""Pure source -> frontend -> typed IR -> optional C14 emission, without admission.

Acquisition stays outside. All bytes and registries are passed explicitly. The
result is ELABORATED, not a complete compiler release or a realized G00 contract.
"""
from guardian.domain.outcomes import Diagnostic, Result
from guardian.domain.references import RecordSnapshot, TrustedEntityImports
from guardian.spec_lang.contract import CompileContext, SourceBundle, SymbolBinding
from guardian.spec_lang.syntax import analyze_source
from guardian.spec_lang.typecheck import TypecheckBudget, TypedProgram, typecheck_analyses
from guardian.spec_lang.elaboration import ElaboratedProgram, elaborate_program


def _typed_sources(sources: tuple[SourceBundle, ...], context: CompileContext, *,
                      formats: tuple[str, ...] | None = None,
                      snapshot: RecordSnapshot | None = None,
                      imports: TrustedEntityImports | None = None,
                      external_symbols: tuple[SymbolBinding, ...] = (),
                      budget: TypecheckBudget = TypecheckBudget()) -> Result[TypedProgram]:
    if (type(sources) is not tuple or not sources or any(type(s) is not SourceBundle for s in sources)
            or type(context) is not CompileContext or type(budget) is not TypecheckBudget):
        return Result(diagnostics=(Diagnostic('GSL_INVALID_SOURCE_BATCH','$','immutable pinned source batch','invalid','explicit source/context/budget required'),))
    if formats is None:
        formats=('gsl',)*len(sources)
    if type(formats) is not tuple or len(formats)!=len(sources) or any(type(f) is not str or f not in ('gsl','markdown') for f in formats):
        return Result(diagnostics=(Diagnostic('GSL_INVALID_SOURCE_FORMATS','$','one declared format per source','invalid','no implicit Markdown discovery'),))
    if len(sources)>budget.max_sources or sum(len(s.source_bytes) for s in sources)>budget.max_bytes:
        return Result(diagnostics=(Diagnostic('GSL_TYPECHECK_RESOURCE_LIMIT','$.sources','bounded source population','exceeded','before frontend allocation'),))
    analyses=tuple(analyze_source(source,context,source_format=fmt) for source,fmt in zip(sources,formats))
    errors=tuple(d for analysis in analyses for d in analysis.diagnostics)
    if errors:
        return Result(diagnostics=errors)
    typed=typecheck_analyses(analyses,context,snapshot=snapshot,imports=imports,
                           external_symbols=external_symbols,budget=budget)
    return typed


def elaborate_sources(sources: tuple[SourceBundle, ...], context: CompileContext, *,
                      formats: tuple[str, ...] | None = None,
                      snapshot: RecordSnapshot | None = None,
                      imports: TrustedEntityImports | None = None,
                      external_symbols: tuple[SymbolBinding, ...] = (),
                      budget: TypecheckBudget = TypecheckBudget()) -> Result[ElaboratedProgram]:
    typed = _typed_sources(sources, context, formats=formats, snapshot=snapshot,
                           imports=imports, external_symbols=external_symbols, budget=budget)
    return elaborate_program(typed.value) if typed.ok else Result(diagnostics=typed.diagnostics)


def emit_sources(sources: tuple[SourceBundle, ...], context: CompileContext, *,
                 formats: tuple[str, ...] | None = None,
                 snapshot: RecordSnapshot | None = None,
                 imports: TrustedEntityImports | None = None,
                 external_symbols: tuple[SymbolBinding, ...] = (),
                 budget: TypecheckBudget = TypecheckBudget(), emission_budget=None):
    """Source -> existing frontend/typechecker/elaborator -> C14 bundle.

    EMITTED_FIXED_PROFILE does not mean every GSL milestone is closed. Source
    sufficiency, external context authentication and admission remain separate.
    """
    from guardian.spec_lang.emission import EmissionBudget, emit_program
    if emission_budget is None:
        emission_budget = EmissionBudget()
    if type(emission_budget) is not EmissionBudget:
        return Result(diagnostics=(Diagnostic('GSL_INVALID_EMISSION_BUDGET', '$.budget',
            'EmissionBudget', type(emission_budget).__name__, 'explicit fixed limits required'),))
    typed = _typed_sources(sources, context, formats=formats, snapshot=snapshot,
                           imports=imports, external_symbols=external_symbols, budget=budget)
    return emit_program(typed.value, budget=emission_budget) if typed.ok else Result(diagnostics=typed.diagnostics)
