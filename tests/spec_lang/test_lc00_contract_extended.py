"""LC00 typed context: pinned registries are declarations, not proof/admission."""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json

import pytest

from guardian.domain.identity import ContentDigest, DigestAlgorithm, EntityId, EntityKind, EntityRef, ProjectId
from guardian.spec_lang.contract import (
    CompilationResult, CompilationStage, CompileStatus, RegistryEntry, RegistrySnapshot,
    SymbolBinding, ExternalImportScope, verify_source_context,
)


def registry(namespace='predicates', entries=None):
    if entries is None:
        entries = (RegistryEntry('nominal_distinct', ('EntityKind','EntityKind'), 'Bool', 'v4_nominal_distinct'),)
    raw = json.dumps({'namespace':namespace, 'version':'0.1', 'entries':[
        {'name':e.name,'argument_types':list(e.argument_types),
         'result_type':e.result_type,'semantic_id':e.semantic_id}
        for e in entries
    ]}, sort_keys=True, ensure_ascii=False, separators=(',',':')).encode()
    return RegistrySnapshot(namespace, '0.1', entries, ContentDigest(DigestAlgorithm.SHA256, sha256(raw).hexdigest()))


def test_pinned_predicate_registry_digest_is_materially_checked(pinned):
    bundle, ctx = pinned
    r = registry()
    assert r.canonical_source()
    assert replace(ctx, predicate_registry=r).predicate_registry == r
    with pytest.raises(ValueError, match='REGISTRY_DIGEST_MISMATCH'):
        replace(r, entries=(RegistryEntry('different', (), 'Bool', 'other_semantics'),))
    with pytest.raises(ValueError, match='duplicate registry symbol'):
        registry(entries=(r.entries[0],r.entries[0]))
    with pytest.raises(ValueError, match='wrong type registry namespace'):
        replace(ctx, type_registry=r)
    with pytest.raises(TypeError, match='immutable typed signatures'):
        replace(r, entries=['nominal_distinct'])


def test_context_symbols_require_local_pinned_origin(pinned):
    bundle,ctx=pinned
    ident=EntityRef(ctx.project, EntityKind.PROPERTY,
                    EntityId(ctx.project,EntityKind.PROPERTY,'test-property'),bundle.revision)
    symbol=SymbolBinding('identity_property',ident,bundle.source_ref)
    assert replace(ctx,symbols=(symbol,)).symbols == (symbol,)
    with pytest.raises(ValueError,match='ambiguous symbol'):
        replace(ctx,symbols=(symbol,symbol))
    foreign=ProjectId('foreign-project')
    untrusted=EntityRef(foreign, EntityKind.PROPERTY,
                        EntityId(foreign,EntityKind.PROPERTY,'test-property'),bundle.revision)
    with pytest.raises(ValueError,match='different projects'):
        SymbolBinding('imported',untrusted,bundle.source_ref)


def test_scope_descriptor_never_authenticates_a_foreign_source(pinned):
    bundle,ctx=pinned
    foreign=ProjectId('foreign-project')
    src=EntityRef(foreign, EntityKind.SOURCE,
                  EntityId(foreign,EntityKind.SOURCE,'foreign-source'),bundle.revision)
    scope=ExternalImportScope(src,ctx.project,frozenset({EntityKind.CAPABILITY}))
    ctx2=replace(ctx,import_scopes=(scope,))
    assert ctx2.import_scopes == (scope,)
    from guardian.spec_lang.contract import SourceBundle
    alien=SourceBundle(src,bundle.source_bytes,bundle.expected_digest)
    assert verify_source_context(alien,ctx2).diagnostics[0].code == 'GSL_FOREIGN_PROJECT'
    with pytest.raises(ValueError,match='duplicate imported'):
        replace(ctx,import_scopes=(scope,scope))
    with pytest.raises(ValueError,match='nonempty typed kind'):
        ExternalImportScope(src,ctx.project,frozenset())


def test_compiled_requires_emitted_stage_not_intermediate_success(pinned):
    bundle,_=pinned
    with pytest.raises(ValueError,match='GSL_COMPILED_REQUIRES_FINAL_STAGE'):
        CompilationResult(CompileStatus.COMPILED,CompilationStage.TYPECHECK,(),bundle.expected_digest)
    assert CompilationResult(CompileStatus.COMPILED,CompilationStage.EMIT,(),bundle.expected_digest).status is CompileStatus.COMPILED
