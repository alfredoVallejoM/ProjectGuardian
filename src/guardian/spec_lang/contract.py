"""GSL0-LC00: versioned contract, immutable source and compiler ABI.

This module deliberately has NO ratify/admit/qualify operation. The language
contract remains a design candidate until the external authority ratifies it.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256, sha512
import json
import re

from guardian.domain.identity import ContentDigest, DigestAlgorithm, EntityKind, EntityRef, ProjectId, RevisionId
from guardian.domain.outcomes import Diagnostic, Result

LANGUAGE_VERSION = '0.1'
SEMANTIC_VERSION = 'gsl0/v4-0.1'
TYPED_IR_SCHEMA = 'guardian/gsl0/typed-ir/v0.1'
CONTRACT_AUTHORITY = 'DESIGN_CANDIDATE_NOT_RATIFIED'
_SYMBOL_NAME = re.compile(r'[A-Za-z_][A-Za-z_0-9]*\Z', re.ASCII)


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
class RegistryEntry:
    """Declarative semantic signature, not executable project-supplied Python."""
    name: str
    argument_types: tuple[str, ...]
    result_type: str
    semantic_id: str

    def __post_init__(self) -> None:
        values = (self.name, self.result_type, self.semantic_id)
        if any(type(x) is not str or _SYMBOL_NAME.fullmatch(x) is None for x in values):
            raise ValueError('registry entry requires canonical names')
        if (type(self.argument_types) is not tuple or
                any(type(x) is not str or _SYMBOL_NAME.fullmatch(x) is None for x in self.argument_types)):
            raise TypeError('registry argument types must be a finite immutable tuple of names')


@dataclass(frozen=True, slots=True)
class RegistrySnapshot:
    """Fully pinned registry descriptor; independent verification of entries.

    The digest here validates registry byte identity, not its trusted signer or
    the correctness of the denotation referenced by semantic_id.
    """
    namespace: str
    version: str
    entries: tuple[RegistryEntry, ...]
    expected_digest: ContentDigest

    def __post_init__(self) -> None:
        if type(self.namespace) is not str or _SYMBOL_NAME.fullmatch(self.namespace) is None:
            raise ValueError('registry namespace must be canonical')
        if type(self.version) is not str or not self.version:
            raise ValueError('registry requires pinned version')
        if type(self.entries) is not tuple or any(not isinstance(e, RegistryEntry) for e in self.entries):
            raise TypeError('registry entries must be immutable typed signatures')
        if len({e.name for e in self.entries}) != len(self.entries):
            raise ValueError('duplicate registry symbol')
        if not isinstance(self.expected_digest, ContentDigest):
            raise TypeError('registry requires a tagged digest')
        raw = self.canonical_source()
        alg = self.expected_digest.algorithm
        digest = (sha256(raw) if alg is DigestAlgorithm.SHA256 else sha512(raw)).hexdigest()
        if digest != self.expected_digest.hex:
            raise ValueError('REGISTRY_DIGEST_MISMATCH')

    def canonical_source(self) -> bytes:
        obj = {'namespace': self.namespace, 'version': self.version, 'entries': [
            {'name': e.name, 'argument_types': list(e.argument_types),
             'result_type': e.result_type, 'semantic_id': e.semantic_id} for e in self.entries
        ]}
        return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                          separators=(',', ':'), allow_nan=False).encode('utf-8')


@dataclass(frozen=True, slots=True)
class SymbolBinding:
    name: str
    identity: EntityRef
    declared_source: EntityRef

    def __post_init__(self) -> None:
        if type(self.name) is not str or _SYMBOL_NAME.fullmatch(self.name) is None:
            raise ValueError('symbol names must be canonical')
        if not isinstance(self.identity, EntityRef) or not isinstance(self.declared_source, EntityRef):
            raise TypeError('symbol requires nominal identity and source')
        if self.declared_source.kind is not EntityKind.SOURCE:
            raise TypeError('symbol origin must be a SOURCE reference')
        if self.identity.project != self.declared_source.project:
            raise ValueError('symbol identity and origin have different projects')


@dataclass(frozen=True, slots=True)
class ExternalImportScope:
    """Scoped, untrusted-until-authenticated descriptor for future LC04.

    Merely listing a grant in a CompileContext does not permit GSL0-LC00 to
    authenticate an external principal or admit an imported obligation.
    """
    source: EntityRef
    target_project: ProjectId
    admitted_kinds: frozenset[EntityKind]

    def __post_init__(self) -> None:
        if not isinstance(self.source, EntityRef) or self.source.kind is not EntityKind.SOURCE:
            raise TypeError('external import needs a pinned source')
        if not isinstance(self.target_project, ProjectId):
            raise TypeError('external import needs the target project')
        if (type(self.admitted_kinds) is not frozenset or not self.admitted_kinds or
                any(not isinstance(x, EntityKind) for x in self.admitted_kinds)):
            raise ValueError('external import needs a nonempty typed kind scope')


@dataclass(frozen=True, slots=True)
class CompileContext:
    project: ProjectId
    language_version: str
    semantic_version: str
    compiler: CompilerIdentity
    expected_sources: tuple[tuple[EntityRef, ContentDigest], ...]
    supported_features: frozenset[str]
    symbols: tuple[SymbolBinding, ...] = ()
    type_registry: RegistrySnapshot | None = None
    predicate_registry: RegistrySnapshot | None = None
    import_scopes: tuple[ExternalImportScope, ...] = ()

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
        if type(self.symbols) is not tuple or any(not isinstance(x, SymbolBinding) for x in self.symbols):
            raise TypeError('symbols must be typed immutable bindings')
        if len({(x.name, x.identity.project) for x in self.symbols}) != len(self.symbols):
            raise ValueError('ambiguous symbol binding')
        if any(x.identity.project != self.project or x.declared_source not in seen for x in self.symbols):
            raise ValueError('nonlocal or unpinned symbol binding')
        if self.type_registry is not None and not isinstance(self.type_registry, RegistrySnapshot):
            raise TypeError('type registry must be a pinned RegistrySnapshot')
        if self.predicate_registry is not None and not isinstance(self.predicate_registry, RegistrySnapshot):
            raise TypeError('predicate registry must be a pinned RegistrySnapshot')
        if self.type_registry is not None and self.type_registry.namespace != 'types':
            raise ValueError('wrong type registry namespace')
        if self.predicate_registry is not None and self.predicate_registry.namespace != 'predicates':
            raise ValueError('wrong predicate registry namespace')
        if type(self.import_scopes) is not tuple or any(not isinstance(x, ExternalImportScope) for x in self.import_scopes):
            raise TypeError('import scopes must be immutable typed descriptors')
        if any(g.target_project != self.project for g in self.import_scopes):
            raise ValueError('external scope cannot change local project')
        if len(set(self.import_scopes)) != len(self.import_scopes):
            raise ValueError('duplicate imported source scope')


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
        if self.status == CompileStatus.COMPILED and self.stage is not CompilationStage.EMIT:
            raise ValueError('GSL_COMPILED_REQUIRES_FINAL_STAGE')
        if self.status != CompileStatus.COMPILED and self.artifact_digest is not None:
            raise ValueError('partial/rejected artifacts cannot claim complete digest')
        if not isinstance(self.proof_obligations, tuple) or any(not isinstance(p,ProofObligation) for p in self.proof_obligations):
            raise TypeError('proof obligations must be typed')
