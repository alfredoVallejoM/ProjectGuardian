"""Pure source -> LC03 -> LC04 -> LC05 -> LC06 service, without admission.

Acquisition stays outside. All bytes and registries are passed explicitly. The
result is ELABORATED, not a complete compiler release or a realized G00 contract.
"""
from guardian.domain.outcomes import Diagnostic, Result
from guardian.domain.references import RecordSnapshot, TrustedEntityImports
from guardian.spec_lang.contract import CompileContext, SourceBundle, SymbolBinding
from guardian.spec_lang.syntax import analyze_source
from guardian.spec_lang.typecheck import TypecheckBudget, typecheck_analyses
from guardian.spec_lang.elaboration import ElaboratedProgram, elaborate_program


def elaborate_sources(sources: tuple[SourceBundle, ...], context: CompileContext, *,
                      formats: tuple[str, ...] | None = None,
                      snapshot: RecordSnapshot | None = None,
                      imports: TrustedEntityImports | None = None,
                      external_symbols: tuple[SymbolBinding, ...] = (),
                      budget: TypecheckBudget = TypecheckBudget()) -> Result[ElaboratedProgram]:
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
    return elaborate_program(typed.value) if typed.ok else Result(diagnostics=typed.diagnostics)
