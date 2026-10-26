"""GSL-T08/T10: pinned edits with an explicit full-rebuild fallback.

No cache reuse is claimed. Every successful update reruns the existing frontend,
resolver, typechecker and elaborator against the new complete source set. This
provides a safe incremental API before dependency-sensitive reuse is justified.
"""
from __future__ import annotations
from dataclasses import dataclass

from guardian.domain.identity import EntityRef, ContentDigest
from guardian.domain.outcomes import Diagnostic, Result
from .contract import SourceBundle, CompileContext
from .syntax import analyze_source
from .typecheck import TypedProgram, TypecheckBudget, typecheck_analyses
from .elaboration import ElaboratedProgram, elaborate_program


@dataclass(frozen=True, slots=True)
class SourceChange:
    before: EntityRef | None
    before_digest: ContentDigest | None
    after: SourceBundle | None
    source_format: str | None

    def __post_init__(self) -> None:
        if self.before is None:
            if self.before_digest is not None or self.after is None:
                raise ValueError('GSL_INVALID_SOURCE_ADDITION')
        elif type(self.before) is not EntityRef or type(self.before_digest) is not ContentDigest:
            raise TypeError('GSL_PINNED_SOURCE_CHANGE_REQUIRED')
        if self.after is not None:
            if type(self.after) is not SourceBundle or type(self.source_format) is not str or self.source_format not in ('gsl', 'markdown'):
                raise TypeError('GSL_TYPED_SOURCE_REPLACEMENT_REQUIRED')
            SourceBundle.__post_init__(self.after)
            if self.before is not None and self.before.entity != self.after.source_ref.entity:
                raise ValueError('GSL_REPLACEMENT_IDENTITY_DRIFT')
        elif self.source_format is not None:
            raise ValueError('GSL_DELETION_HAS_NO_FORMAT')


@dataclass(frozen=True, slots=True)
class RebuildResult:
    program: TypedProgram
    output: ElaboratedProgram

    @property
    def strategy(self) -> str:
        return 'FULL_REBUILD_NO_CACHE_REUSE'

    @property
    def normatively_admitted(self) -> bool:
        return False


def _failure(code: str, reason: str) -> Result:
    return Result(diagnostics=(Diagnostic(code, '$.changes', 'exact source delta and new context', 'input', reason),))


def rebuild_program(previous: TypedProgram, changes: tuple[SourceChange, ...], context: CompileContext, *,
                    budget: TypecheckBudget = TypecheckBudget()) -> Result[RebuildResult]:
    """Atomic in-memory add/remove/replace. No stale previous IR is returned on error."""
    try:
        if type(previous) is not TypedProgram or type(context) is not CompileContext or type(budget) is not TypecheckBudget:
            raise TypeError('GSL_REBUILD_CONTEXT_REQUIRED')
        if type(changes) is not tuple or len(changes) > budget.max_sources * 2 or any(type(c) is not SourceChange for c in changes):
            raise TypeError('GSL_IMMUTABLE_SOURCE_CHANGES_REQUIRED')
        TypecheckBudget.__post_init__(budget)
        verified = elaborate_program(previous)
        if not verified.ok:
            return Result(diagnostics=verified.diagnostics)
        if previous.context.project != context.project:
            raise ValueError('GSL_REBUILD_PROJECT_MISMATCH')
        inputs = {}
        for analysis in previous.analyses:
            source = analysis.extraction.source
            inputs[source.source_ref] = (source, analysis.source_format)
        removed = set()
        added = set()
        # Validate the whole delta against the original population before changing
        # anything. Order of additions and removals cannot select a winner.
        for change in changes:
            SourceChange.__post_init__(change)
            if change.before is not None:
                if change.before in removed or change.before not in inputs:
                    raise ValueError('GSL_REBUILD_UNKNOWN_OR_DUPLICATE_SOURCE')
                old = inputs[change.before][0]
                if old.expected_digest != change.before_digest:
                    raise ValueError('GSL_REBUILD_OLD_DIGEST_MISMATCH')
                if (change.after is not None and change.after.source_ref == change.before
                        and change.after.source_bytes != old.source_bytes):
                    raise ValueError('GSL_SOURCE_REVISION_REUSE')
                removed.add(change.before)
            if change.after is not None:
                if change.after.source_ref in added:
                    raise ValueError('GSL_REBUILD_DUPLICATE_REPLACEMENT')
                added.add(change.after.source_ref)
        # Compare the complete old population with ALL replacements, even when
        # remove and add are separate operations or presented in reverse order.
        for change in changes:
            if change.after is not None and change.after.source_ref in inputs:
                old, old_format = inputs[change.after.source_ref]
                if (change.after.source_bytes != old.source_bytes
                        or change.after.expected_digest != old.expected_digest):
                    raise ValueError('GSL_SOURCE_REVISION_REUSE')
                if change.source_format != old_format:
                    raise ValueError('GSL_SOURCE_FORMAT_REVISION_REUSE')
        if added & (set(inputs) - removed):
            raise ValueError('GSL_REBUILD_SOURCE_COLLISION')
        inputs = {ref: item for ref, item in inputs.items() if ref not in removed}
        for change in changes:
            if change.after is not None:
                inputs[change.after.source_ref] = (change.after, change.source_format)
        if not inputs or len(inputs) > budget.max_sources or sum(len(b.source_bytes) for b, _ in inputs.values()) > budget.max_bytes:
            raise ValueError('GSL_REBUILD_SOURCE_BUDGET')
        CompileContext.__post_init__(context)
        if {ref: bundle.expected_digest for ref, (bundle, _) in inputs.items()} != dict(context.expected_sources):
            raise ValueError('GSL_REBUILD_PIN_SET_MISMATCH')
        ordered = sorted(inputs.values(), key=lambda item: (item[0].source_ref.entity.value, item[0].revision.value))
        analyses = tuple(analyze_source(bundle, context, source_format=fmt) for bundle, fmt in ordered)
        errors = tuple(d for analysis in analyses for d in analysis.diagnostics)
        if errors:
            return Result(diagnostics=errors)
        typed = typecheck_analyses(analyses, context, snapshot=previous.snapshot, imports=previous.imports,
                                  external_symbols=previous.external_symbols, budget=budget)
        if not typed.ok:
            return Result(diagnostics=typed.diagnostics)
        elaborated = elaborate_program(typed.value)
        if not elaborated.ok:
            return Result(diagnostics=elaborated.diagnostics)
        return Result(RebuildResult(typed.value, elaborated.value))
    except (TypeError, ValueError, AttributeError, KeyError, RecursionError) as exc:
        code = str(exc) if str(exc).startswith('GSL_') else 'GSL_REBUILD_REJECTED'
        return _failure(code, str(exc))


def source_from_chunks(source: EntityRef, chunks: tuple[bytes, ...], expected_digest: ContentDigest, *,
                       max_bytes: int = 8_000_000, max_chunks: int = 100_000) -> Result[SourceBundle]:
    """Join bounded immutable UTF-8 bytes without decoding partial characters.

    The expected pin is external. This is byte-preserving acquisition, not a
    streaming parser or an assertion of constant-space frontend operation.
    """
    try:
        if type(max_bytes) is not int or type(max_chunks) is not int or not 1 <= max_bytes <= 8_000_000 or not 1 <= max_chunks <= 1_000_000:
            raise ValueError('GSL_CHUNK_BUDGET_REQUIRED')
        if type(chunks) is not tuple or any(type(chunk) is not bytes for chunk in chunks):
            raise TypeError('GSL_IMMUTABLE_BYTE_CHUNKS_REQUIRED')
        if len(chunks) > max_chunks or sum(map(len, chunks)) > max_bytes:
            raise ValueError('GSL_CHUNK_RESOURCE_LIMIT')
        return Result(SourceBundle(source, b''.join(chunks), expected_digest))
    except (TypeError, ValueError, AttributeError) as exc:
        return _failure('GSL_CHUNK_REJECTED', str(exc))
