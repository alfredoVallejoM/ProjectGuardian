"""Coordinated G00-B01 / GSL0-LC00…02, without mock domain identities."""
import hashlib
import pytest

from guardian.domain.identity import ContentDigest, DigestAlgorithm, EntityId, EntityKind, EntityRef, ProjectId, RevisionId
from guardian.spec_lang.contract import SourceBundle, CompileContext, CompilerIdentity, LANGUAGE_VERSION, SEMANTIC_VERSION


@pytest.fixture
def pinned():
    project=ProjectId('project-guardian')
    rev=RevisionId('rev-'+'a'*32)
    src=EntityRef(project,EntityKind.SOURCE,EntityId(project,EntityKind.SOURCE,'gsl0-source'),rev)
    content=b'// normative\nnot (alpha and beta)\r\n'
    digest=ContentDigest(DigestAlgorithm.SHA256,hashlib.sha256(content).hexdigest())
    bundle=SourceBundle(src,content,digest)
    compiler=CompilerIdentity('guardian-python',SEMANTIC_VERSION,ContentDigest(DigestAlgorithm.SHA256,'1'*64))
    ctx=CompileContext(project,LANGUAGE_VERSION,SEMANTIC_VERSION,compiler,((src,digest),),
                       frozenset({'v4-atom','v4-not','v4-and','v4-or','finite-v4-oracle'}))
    return bundle,ctx
