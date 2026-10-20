"""GSL0-LC00: versioned contract, immutable source and compiler ABI.

This module deliberately has NO ratify/admit/qualify operation. The language
contract remains a design candidate until the external authority ratifies it.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256, sha512

from guardian.domain.identity import ContentDigest, DigestAlgorithm, EntityKind, EntityRef, ProjectId, RevisionId
from guardian.domain.outcomes import Diagnostic, Result

LANGUAGE_VERSION = '0.1'
SEMANTIC_VERSION = 'gsl0/v4-0.1'
TYPED_IR_SCHEMA = 'guardian/gsl0/typed-ir/v0.1'
CONTRACT_AUTHORITY = 'DESIGN_CANDIDATE_NOT_RATIFIED'


class CompilationStage(str, Enum):
    ACQUIRE = 'C00_ACQUIRE'
    EXTRACT = 'C01_EXTRACT'
    LEX = 'C02_LEX'
    PARSE = 'C03_PARSE'
    ABSTRACT = 'C04_ABSTRACT'
    RESOLVE = 'C05_RESOLVE'
    TYPECHECK = 'C06_TYPECHECK'
    SEMANTIC_CHECK = 'C07_SEMANTIC_CHECK'
    ELABORATE = 'C08_ELABORATE'
    GENERATE_PO = 'C09_GENERATE_PO'
    VERIFY_IR = 'C10_VERIFY_IR'
    CANONICALIZE = 'C11_CANONICALIZE'
    DIFF = 'C12_DIFF'
    EMIT = 'C13_EMIT'


class CompileStatus(str, Enum):
    REJECTED = 'REJECTED'
    ANALYZED = 'ANALYZED'
    COMPILED = 'COMPILED'


class ProofState(str, Enum):
    UNPROVEN = 'UNPROVEN'
    COUNTEREXAMPLE = 'COUNTEREXAMPLE'
    CHECKED_FINITE_DOMAIN = 'CHECKED_FINITE_DOMAIN'


@dataclass(frozen=True, slots=True)
class ProofObligation:
    identifier: str
    origin: EntityRef
    state: ProofState = ProofState.UNPROVEN

    def __post_init__(self) -> None:
        if not isinstance(self.identifier, str) or not self.identifier.strip():
            raise ValueError('proof obligation ID required')
        if not isinstance(self.origin, EntityRef) or not isinstance(self.state, ProofState):
            raise TypeError('proof obligations require nominal origin and state')


@dataclass(frozen=True, slots=True)
class SourceBundle:
    """Immutable bytes with an EXPECTED digest from a trusted external cut.

    Digest equality checks byte integrity, not who authorized the cut. A malicious
    caller controlling both bytes and expected digest remains outside this core's
    trust boundary; G09 will own authenticity of the upstream assertion.
    """
    source_ref: EntityRef
    source_bytes: bytes
    expected_digest: ContentDigest

    def __post_init__(self) -> None:
        if not isinstance(self.source_ref, EntityRef) or self.source_ref.kind != EntityKind.SOURCE:
            raise TypeError('source must be a pinned SOURCE EntityRef')
        if not isinstance(self.source_bytes, bytes):
            raise TypeError('source payload must be immutable bytes')
        if not isinstance(self.expected_digest, ContentDigest):
            raise TypeError('source digest must be nominal and algorithm tagged')
        alg = self.expected_digest.algorithm
        actual = (sha256(self.source_bytes) if alg is DigestAlgorithm.SHA256 else sha512(self.source_bytes)).hexdigest()
        if actual != self.expected_digest.hex:
            raise ValueError('SOURCE_DIGEST_MISMATCH: bytes do not match independently provided pin')
        try:
            self.source_bytes.decode('utf-8', 'strict')
        except UnicodeDecodeError as exc:
            raise ValueError('SOURCE_NOT_UTF8') from exc

    @property
    def project(self) -> ProjectId:
        return self.source_ref.project

    @property
    def revision(self) -> RevisionId:
        return self.source_ref.revision


@dataclass(frozen=True, slots=True)
class CompilerIdentity:
    implementation: str
    semantic_version: str
    binary_digest: ContentDigest

    def __post_init__(self) -> None:
        if not isinstance(self.implementation, str) or not self.implementation:
            raise ValueError('compiler implementation must be identified')
        if self.semantic_version != SEMANTIC_VERSION:
            raise ValueError('unsupported semantic version')
        if not isinstance(self.binary_digest, ContentDigest):
            raise TypeError('compiler digest is not nominal')


@dataclass(frozen=True, slots=True)
class CompileContext:
    project: ProjectId
    language_version: str
    semantic_version: str
    compiler: CompilerIdentity
    expected_sources: tuple[tuple[EntityRef, ContentDigest], ...]
    supported_features: frozenset[str]

    def __post_init__(self) -> None:
        if not isinstance(self.project, ProjectId) or not isinstance(self.compiler, CompilerIdentity):
            raise TypeError('project and compiler must be typed')
        if self.language_version != LANGUAGE_VERSION or self.semantic_version != SEMANTIC_VERSION:
            raise ValueError('GSL_VERSION_UNSUPPORTED')
        if self.compiler.semantic_version != self.semantic_version:
            raise ValueError('GSL_COMPILER_VERSION_MISMATCH')
        if not isinstance(self.expected_sources, tuple) or not self.expected_sources:
            raise ValueError('at least one trusted source cut is required')
        if not isinstance(self.supported_features, frozenset) or not all(isinstance(x,str) for x in self.supported_features):
            raise TypeError('features must be a frozen set of names')
        if not self.supported_features <= {'v4-atom','v4-not','v4-and','v4-or','deferred-property','finite-v4-oracle'}:
            raise ValueError('GSL_UNSUPPORTED_NORMATIVE_FEATURE')
        seen: set[EntityRef] = set()
        for source_ref, digest in self.expected_sources:
            if not isinstance(source_ref, EntityRef) or source_ref.kind != EntityKind.SOURCE:
                raise TypeError('expected sources require pinned SOURCE EntityRef')
            if source_ref.project != self.project or not isinstance(digest, ContentDigest):
                raise ValueError('cross-project source or untyped digest')
            if source_ref in seen:
                raise ValueError('duplicate source reference')
            seen.add(source_ref)


def verify_source_context(bundle: SourceBundle, context: CompileContext) -> Result[SourceBundle]:
    if not isinstance(bundle, SourceBundle) or not isinstance(context, CompileContext):
        return Result(diagnostics=(Diagnostic('GSL_CONTEXT_INVALID','$.source','SourceBundle+CompileContext','unknown','untyped argument'),))
    if bundle.project != context.project:
        return Result(diagnostics=(Diagnostic('GSL_FOREIGN_PROJECT','$.source','same project','EntityRef','source belongs to another project'),))
    trusted = dict(context.expected_sources)
    if bundle.source_ref not in trusted:
        return Result(diagnostics=(Diagnostic('GSL_UNTRUSTED_SOURCE','$.source','trusted source cut','EntityRef','source not in pinned context'),))
    if trusted[bundle.source_ref] != bundle.expected_digest:
        return Result(diagnostics=(Diagnostic('GSL_SOURCE_PIN_MISMATCH','$.source','expected trusted digest','ContentDigest','candidate presented different source pin'),))
    return Result(bundle)


@dataclass(frozen=True, slots=True)
class CompilationResult:
    """A typed stage outcome. Compiled does not mean admitted/qualified."""
    status: CompileStatus
    stage: CompilationStage
    diagnostics: tuple[Diagnostic, ...]
    artifact_digest: ContentDigest | None = None
    proof_obligations: tuple[ProofObligation, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.status, CompileStatus) or not isinstance(self.stage, CompilationStage):
            raise TypeError('invalid GSL stage or status')
        if not isinstance(self.diagnostics, tuple) or any(not isinstance(d,Diagnostic) for d in self.diagnostics):
            raise TypeError('invalid diagnostics')
        if self.status == CompileStatus.REJECTED and not self.diagnostics:
            raise ValueError('rejection requires diagnostic')
        if self.status == CompileStatus.COMPILED and (self.diagnostics or self.artifact_digest is None):
            raise ValueError('compiled artifact requires digest and zero errors')
        if self.status != CompileStatus.COMPILED and self.artifact_digest is not None:
            raise ValueError('partial/rejected artifacts cannot claim complete digest')
        if not isinstance(self.proof_obligations, tuple) or any(not isinstance(p,ProofObligation) for p in self.proof_obligations):
            raise TypeError('proof obligations must be typed')
