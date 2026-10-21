"""Immutable real-domain factories for G00-B02 and GSL0-LC03 tests."""
from hashlib import sha256

from guardian.domain.identity import (ProjectId, RevisionId, EntityId,
    EntityRef, EntityKind, DigestAlgorithm, ContentDigest)
from guardian.domain.project import (RepositoryId, StorageDescriptor,
    StorageMode, SourcePolicy, ProjectDefinition)
from guardian.domain.source import (GitSourceCut,GitObjectKind,SourceEntry,
    SourceUniverseRevision,CoverageScope,HistoryRole)
from guardian.domain.outcomes import SourceStatus
from guardian.spec_lang.contract import (SourceBundle,CompilerIdentity,
    CompileContext,LANGUAGE_VERSION,SEMANTIC_VERSION)


def entity(project,kind,name='local',revision=None):
    if revision is None:revision=RevisionId('rev-'+'a'*32)
    return EntityRef(project,kind,EntityId(project,kind,name),revision)


def project(name='project-alpha',mode=StorageMode.EMBEDDED,display='Alpha research'):
    p=ProjectId(name)
    r1=RepositoryId('github','science/'+name)
    r2=RepositoryId('github','science/'+name+'-docs')
    if mode is StorageMode.EMBEDDED:
        storage=StorageDescriptor(mode,r1,(r1,))
    elif mode is StorageMode.SIDECAR:
        storage=StorageDescriptor(mode,r2,(r1,))
    else:
        classes=('source','constitution','contract','evidence','decision')
        storage=StorageDescriptor(mode,r1,(r1,r2),tuple((c,r2 if c in ('source','evidence') else r1) for c in classes))
    rev=RevisionId('rev-'+'b'*32)
    policy=SourcePolicy(p,rev,storage.repositories)
    definition=ProjectDefinition(p,display,entity(p,EntityKind.CONSTITUTION,'constitution'),
        entity(p,EntityKind.SOURCE_POLICY,'policy',rev),policy,storage)
    return definition


def cut(prj,name='source-main',commit=None,repo=None,path='spec/main.gsl',digest=None):
    return GitSourceCut(entity(prj.project_id,EntityKind.SOURCE,name),repo or prj.storage.repositories[0],
        commit or 'c'*40,GitObjectKind.BLOB,path,digest)


def universe(prj,cuts,*,missing=(),included=None,entries=None,excluded=(),limits=('not externally qualified',)):
    if included is None:included=tuple(c.ref for c in cuts)
    if entries is None:
        entries=tuple(SourceEntry(c,HistoryRole.BASE,SourceStatus.CONTENT_OBSERVED,'history-'+c.ref.entity.value) for c in cuts)
    return SourceUniverseRevision(entity(prj.project_id,EntityKind.SOURCE_UNIVERSE,'source-universe'),
        CoverageScope(('gsl-foundation',),('specifications',),('linux',),'2026-10-21'),
        tuple(entries),tuple(included),tuple(excluded),tuple(missing),tuple(limits))


def bundle_context(prj,source,raw):
    digest=ContentDigest(DigestAlgorithm.SHA256,sha256(raw).hexdigest())
    if source.observed_digest is not None:
        assert source.observed_digest==digest
    b=SourceBundle(source.ref,raw,digest)
    c=CompileContext(prj.project_id,LANGUAGE_VERSION,SEMANTIC_VERSION,
        CompilerIdentity('guardian-python',SEMANTIC_VERSION,ContentDigest(DigestAlgorithm.SHA256,'f'*64)),
        ((source.ref,digest),),frozenset({'v4-atom','v4-and','v4-or','v4-not','finite-v4-oracle'}))
    return b,c
