import dataclasses
import hashlib
import pytest

from guardian.domain.identity import ContentDigest, DigestAlgorithm, EntityId, EntityKind, EntityRef, ProjectId, RevisionId
from guardian.spec_lang.contract import (
    CompileContext, CompilerIdentity, CompileStatus, CompilationStage,
    CompilationResult, LANGUAGE_VERSION, SEMANTIC_VERSION, SourceBundle,
    ProofObligation, ProofState, verify_source_context,
)
from guardian.domain.outcomes import Diagnostic


def test_context_validates_external_pinned_source(pinned):
    bundle,ctx=pinned
    assert verify_source_context(bundle,ctx).value==bundle
    assert ctx.project==bundle.project
    assert bundle.source_bytes.endswith(b'\r\n')
    with pytest.raises(dataclasses.FrozenInstanceError):
        bundle.source_bytes=b'other'


def test_invalid_source_bytes_or_faked_digest_rejected(pinned):
    bundle,ctx=pinned
    with pytest.raises(ValueError,match='SOURCE_DIGEST_MISMATCH'):
        SourceBundle(bundle.source_ref,bundle.source_bytes+b' ',bundle.expected_digest)
    with pytest.raises(ValueError,match='SOURCE_NOT_UTF8'):
        raw=b'\xff'
        SourceBundle(bundle.source_ref,raw,ContentDigest(DigestAlgorithm.SHA256,hashlib.sha256(raw).hexdigest()))


def test_candidate_cannot_change_both_payload_and_digest_against_external_context(pinned):
    bundle,ctx=pinned
    text=b'not (alpha or beta)'
    new_digest=ContentDigest(DigestAlgorithm.SHA256,hashlib.sha256(text).hexdigest())
    forged=SourceBundle(bundle.source_ref,text,new_digest)
    result=verify_source_context(forged,ctx)
    assert result.diagnostics[0].code=='GSL_SOURCE_PIN_MISMATCH'


def test_context_rejects_foreign_project_or_revision(pinned):
    bundle,ctx=pinned
    other=ProjectId('foreign-project')
    other_ref=EntityRef(other,EntityKind.SOURCE,EntityId(other,EntityKind.SOURCE,'gsl0-source'),bundle.revision)
    forged=SourceBundle(other_ref,bundle.source_bytes,bundle.expected_digest)
    assert verify_source_context(forged,ctx).diagnostics[0].code=='GSL_FOREIGN_PROJECT'
    new_ref=EntityRef(ctx.project,EntityKind.SOURCE,bundle.source_ref.entity,RevisionId('rev-'+'b'*32))
    assert verify_source_context(SourceBundle(new_ref,bundle.source_bytes,bundle.expected_digest),ctx).diagnostics[0].code=='GSL_UNTRUSTED_SOURCE'


def test_context_rejects_unsupported_version_feature_duplicate_cuts(pinned):
    bundle,ctx=pinned
    with pytest.raises(ValueError,match='GSL_VERSION_UNSUPPORTED'):
        dataclasses.replace(ctx,language_version='1.0')
    with pytest.raises(ValueError,match='GSL_UNSUPPORTED_NORMATIVE_FEATURE'):
        dataclasses.replace(ctx,supported_features=frozenset({'allow_python_callbacks'}))
    with pytest.raises(ValueError,match='duplicate source'):
        dataclasses.replace(ctx,expected_sources=ctx.expected_sources+ctx.expected_sources)
    with pytest.raises(ValueError,match='semantic version'):
        CompilerIdentity('compiler','self-ratified',ctx.compiler.binary_digest)


def test_no_compiled_without_artifact_and_no_certification_promotion(pinned):
    bundle,ctx=pinned
    with pytest.raises(ValueError,match='requires digest'):
        CompilationResult(CompileStatus.COMPILED,CompilationStage.EMIT,())
    with pytest.raises(ValueError,match='requires diagnostic'):
        CompilationResult(CompileStatus.REJECTED,CompilationStage.PARSE,())
    with pytest.raises(ValueError,match='cannot claim complete digest'):
        CompilationResult(CompileStatus.ANALYZED,CompilationStage.PARSE,(),bundle.expected_digest)
    po=ProofObligation('GSL-T05',bundle.source_ref)
    x=CompilationResult(CompileStatus.COMPILED,CompilationStage.EMIT,(),bundle.expected_digest,(po,))
    assert po.state==ProofState.UNPROVEN and x.status==CompileStatus.COMPILED
    assert not hasattr(x,'ratify') and not hasattr(x,'qualify')
    assert 'RATIFIED' not in [s.value for s in CompileStatus]


def test_source_kind_must_be_correct(pinned):
    bundle,ctx=pinned
    src=EntityRef(ctx.project,EntityKind.OBLIGATION,EntityId(ctx.project,EntityKind.OBLIGATION,'source-one'),bundle.revision)
    with pytest.raises(TypeError):
        SourceBundle(src,bundle.source_bytes,bundle.expected_digest)
