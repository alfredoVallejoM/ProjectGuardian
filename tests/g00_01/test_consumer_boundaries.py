"""G00-01 guarantees at existing consumer boundaries; no new GSL features."""
from dataclasses import fields,replace
from hashlib import sha256
import pytest
from guardian.domain.identity import ProjectId,EntityId,EntityRef,EntityKind as K,RevisionId,ContentDigest,DigestAlgorithm
from guardian.spec_lang.contract import (SourceBundle,CompileContext,CompilerIdentity,SymbolBinding,
    ProofObligation,ExternalImportScope,verify_source_context,CompilationResult,CompileStatus,CompilationStage)
from foundation_b02 import project,cut,bundle_context


def forge(record,**changes):
    obj=object.__new__(type(record))
    for f in fields(record):object.__setattr__(obj,f.name,changes.get(f.name,getattr(record,f.name)))
    return obj


def inputs():
    p=project();source=cut(p)
    bundle,context=bundle_context(p,source,b'gsl "0.1"; project "project-alpha"; scope "scope-one" {project:project("project-alpha");}')
    return bundle,context


@pytest.mark.parametrize('consumer',['bundle','proof','symbol','import'])
def test_reconstructed_mutable_reference_cannot_enter_a_nominal_consumer(consumer):
    b,c=inputs();bad=forge(b.source_ref,revision=forge(b.source_ref.revision,value='latest'))
    with pytest.raises((TypeError,ValueError)):
        if consumer=='bundle':SourceBundle(bad,b.source_bytes,b.expected_digest)
        elif consumer=='proof':ProofObligation('proof-one',bad)
        elif consumer=='symbol':SymbolBinding('source_one',bad,bad)
        else:ExternalImportScope(bad,ProjectId('project-beta'),frozenset({K.PROPERTY}))


@pytest.mark.parametrize('part',['source','compiler-digest','project'])
def test_compiler_context_revalidates_identity_inputs_not_only_type_tags(part):
    b,c=inputs()
    with pytest.raises((TypeError,ValueError)):
        if part=='source':
            bad=forge(b.source_ref,revision=forge(b.source_ref.revision,value='latest'))
            replace(c,expected_sources=((bad,b.expected_digest),))
        elif part=='compiler-digest':
            bad=forge(c.compiler,binary_digest=forge(c.compiler.binary_digest,hex='abc'))
            replace(c,compiler=bad)
        else:
            bad=forge(c.project,value='')
            replace(c,project=bad,expected_sources=((forge(b.source_ref,project=bad,entity=forge(b.source_ref.entity,project=bad)),b.expected_digest),))


def test_public_source_context_check_revalidates_reconstructed_source_and_context():
    b,c=inputs();ref=forge(b.source_ref,revision=forge(b.source_ref.revision,value='latest'))
    result=verify_source_context(forge(b,source_ref=ref),forge(c,expected_sources=((ref,b.expected_digest),)))
    assert not result.ok and result.value is None


def test_valid_sources_and_contexts_still_cross_the_boundary_without_admission():
    b,c=inputs()
    assert verify_source_context(b,c).value is b
    assert verify_source_context(forge(b),forge(c)).value==b
    assert b.source_ref.revision==b.revision


def test_compilation_result_cannot_publish_a_malformed_nominal_digest():
    b,c=inputs()
    bad=forge(b.expected_digest,hex='abc')
    with pytest.raises((TypeError,ValueError)):
        CompilationResult(CompileStatus.COMPILED,CompilationStage.EMIT,(),bad)
    valid=CompilationResult(CompileStatus.COMPILED,CompilationStage.EMIT,(),b.expected_digest)
    assert valid.artifact_digest==b.expected_digest
