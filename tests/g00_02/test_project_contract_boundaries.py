"""G00-02 first sequential acceptance: real project data, no authority mocks.

These are descriptor/membership contracts, not whole-obligation closure. Cut
imports, readonly source views and constitutional consumers remain separate.
"""
from dataclasses import fields, replace, FrozenInstanceError
from itertools import permutations
import pytest
from guardian.domain.identity import ProjectId, EntityId, RevisionId, EntityRef, EntityKind as K
from guardian.domain.project import (RepositoryId, StorageMode, StorageDescriptor,
    SourcePolicy, ProjectDefinition, MembershipStatus, validate_project,
    validate_storage_mode, check_project_membership)

CLASSES = ('source', 'constitution', 'contract', 'evidence', 'decision')


def ref(project, kind=K.OBLIGATION, name='contract-main', revision=None):
    return EntityRef(project, kind, EntityId(project, kind, name),
                     revision or RevisionId('rev-' + 'a'*32))


def project(mode=StorageMode.EMBEDDED, name='project-alpha'):
    pid = ProjectId(name); rev = RevisionId('rev-' + 'b'*32)
    managed = RepositoryId('github', 'science/' + name)
    authority = RepositoryId('github', 'governance/' + name)
    if mode is StorageMode.EMBEDDED:
        storage = StorageDescriptor(mode, managed, (managed,))
    elif mode is StorageMode.SIDECAR:
        storage = StorageDescriptor(mode, authority, (managed,))
    else:
        storage = StorageDescriptor(mode, managed, (managed, authority),
            tuple((c, authority if c in ('source','evidence') else managed) for c in CLASSES))
    return ProjectDefinition(pid, 'Shared human name', ref(pid,K.CONSTITUTION,'constitution'),
        ref(pid,K.SOURCE_POLICY,'policy',rev), SourcePolicy(pid,rev,storage.repositories),storage)


def rebuilt(obj, **changes):
    """An untrusted reconstructed object; never replace the product validator."""
    value = object.__new__(type(obj))
    for f in fields(obj):
        object.__setattr__(value, f.name, changes.get(f.name, getattr(obj, f.name)))
    return value


@pytest.mark.parametrize('mode', list(StorageMode))
def test_valid_descriptors_and_reconstructed_values_stay_valid(mode):
    p=project(mode); before=hash(p)
    for value in (p, rebuilt(p)):
        assert validate_project(value).value is value
        assert validate_storage_mode(value.storage).value is value.storage
    assert hash(p)==before
    expected = p.storage.repositories + ((p.storage.authority_repository,) if mode is StorageMode.SIDECAR else ())
    assert p.permitted_source_repositories == expected


@pytest.mark.parametrize('attack', ['name','description','project','constitution-kind',
    'constitution-revision','foreign-constitution','policy-project','policy-revision',
    'allowlist','repository','storage-mode','storage-authority'])
def test_project_revalidation_rejects_invalid_nested_contract(attack):
    p=project(); q=project(name='project-beta')
    if attack=='name': bad=rebuilt(p,display_name=' ')
    elif attack=='description': bad=rebuilt(p,description=17)
    elif attack=='project': bad=rebuilt(p,project_id=rebuilt(p.project_id,value='../escape'))
    elif attack=='constitution-kind': bad=rebuilt(p,constitution_ref=ref(p.project_id,K.OBLIGATION))
    elif attack=='constitution-revision': bad=rebuilt(p,constitution_ref=rebuilt(p.constitution_ref,revision=rebuilt(p.constitution_ref.revision,value='latest')))
    elif attack=='foreign-constitution': bad=rebuilt(p,constitution_ref=q.constitution_ref)
    elif attack=='policy-project': bad=rebuilt(p,source_policy=rebuilt(p.source_policy,project=q.project_id))
    elif attack=='policy-revision': bad=rebuilt(p,source_policy=rebuilt(p.source_policy,revision=RevisionId('rev-'+'c'*32)))
    elif attack=='allowlist': bad=rebuilt(p,source_policy=rebuilt(p.source_policy,allow_repositories=(RepositoryId('github','other/repo'),)))
    elif attack=='repository': bad=rebuilt(p,source_policy=rebuilt(p.source_policy,allow_repositories=(rebuilt(p.storage.repositories[0],slug='../escape'),)))
    elif attack=='storage-mode': bad=rebuilt(p,storage=rebuilt(p.storage,mode='embedded'))
    else: bad=rebuilt(p,storage=rebuilt(p.storage,authority_repository=RepositoryId('github','other/repo')))
    result=validate_project(bad)
    assert not result.ok and result.value is None
    assert result.diagnostics[0].code=='PROJECT_SNAPSHOT_INVALID'
    assert result.diagnostics[0].path=='$.project'
    assert not check_project_membership(bad,ref(p.project_id)).allowed
    with pytest.raises((TypeError,ValueError,AttributeError)):
        _=bad.permitted_source_repositories
    assert validate_project(p).ok


@pytest.mark.parametrize('attack', ['unknown-mode','fabricated-mode','mutable-repositories',
    'duplicate-repository','bad-repository','foreign-authority','missing-class',
    'duplicate-class','foreign-class-repository','nontext-class','mutable-pair'])
def test_federated_descriptor_revalidates_all_nested_metadata(attack):
    d=project(StorageMode.FEDERATED).storage
    if attack=='unknown-mode': bad=rebuilt(d,mode='federated')
    elif attack=='fabricated-mode':
        fake=str.__new__(StorageMode,'federated');object.__setattr__(fake,'_name_','FEDERATED');object.__setattr__(fake,'_value_','federated')
        bad=rebuilt(d,mode=fake)
    elif attack=='mutable-repositories': bad=rebuilt(d,repositories=list(d.repositories))
    elif attack=='duplicate-repository': bad=rebuilt(d,repositories=(d.repositories[0],)*2)
    elif attack=='bad-repository': bad=rebuilt(d,repositories=(rebuilt(d.repositories[0],provider='BAD'),d.repositories[1]))
    elif attack=='foreign-authority': bad=rebuilt(d,authority_repository=RepositoryId('github','other/repo'))
    elif attack=='missing-class': bad=rebuilt(d,authority_by_class=d.authority_by_class[:-1])
    elif attack=='duplicate-class': bad=rebuilt(d,authority_by_class=d.authority_by_class+(d.authority_by_class[0],))
    elif attack=='foreign-class-repository': bad=rebuilt(d,authority_by_class=((CLASSES[0],RepositoryId('github','other/repo')),)+d.authority_by_class[1:])
    elif attack=='nontext-class': bad=rebuilt(d,authority_by_class=((17,d.repositories[0]),)+d.authority_by_class[1:])
    else: bad=rebuilt(d,authority_by_class=([CLASSES[0],d.repositories[0]],)+d.authority_by_class[1:])
    result=validate_storage_mode(bad)
    assert not result.ok and result.diagnostics[0].code=='UNSUPPORTED_STORAGE_MODE'
    assert result.diagnostics[0].path=='$.storage'
    assert validate_storage_mode(d).ok


@pytest.mark.parametrize('endpoint', ['project','storage'])
def test_rejected_external_objects_do_not_execute_metaclass_or_validation_hooks(endpoint):
    seen=[]
    class Meta(type):
        def __getattribute__(self,name):
            if name=='__name__':seen.append(name);return 'ExternalName'
            return super().__getattribute__(name)
    class Opaque(metaclass=Meta):
        def __str__(self):seen.append('str');raise AssertionError('external conversion')
    fn=validate_project if endpoint=='project' else validate_storage_mode
    assert not fn(Opaque()).ok and not seen
    parent=ProjectDefinition if endpoint=='project' else StorageDescriptor
    class Hostile(parent):
        def __post_init__(self):seen.append('callback');raise AssertionError('external validator')
    value=object.__new__(Hostile)
    source=project() if endpoint=='project' else project().storage
    for f in fields(source):object.__setattr__(value,f.name,getattr(source,f.name))
    assert not fn(value).ok and not seen


@pytest.mark.parametrize('target', ['project','revision','kind'])
def test_membership_revalidates_reference_before_namespace_result(target):
    p=project();r=ref(p.project_id)
    if target=='project': bad=rebuilt(r,project=rebuilt(r.project,value='bad/path'))
    elif target=='revision': bad=rebuilt(r,revision=rebuilt(r.revision,value='main'))
    else: bad=rebuilt(r,kind='obligation')
    result=check_project_membership(p,bad)
    assert result.status is MembershipStatus.UNKNOWN and not result.allowed
    assert result.code=='INVALID_PROJECT_REFERENCE'
    assert check_project_membership(p,r).allowed


def test_rename_does_not_change_project_policy_or_constitution():
    p=project();renamed=replace(p,display_name='Renamed',description='New presentation')
    assert validate_project(renamed).ok
    assert (renamed.project_id,renamed.constitution_ref,renamed.source_policy_ref)==(p.project_id,p.constitution_ref,p.source_policy_ref)
    assert p.display_name=='Shared human name'


def test_policy_revision_change_is_explicit_and_old_definition_is_preserved():
    p=project();rev=RevisionId('rev-'+'c'*32)
    with pytest.raises(ValueError,match='PROJECT_POLICY_REVISION_MISMATCH'):
        replace(p,source_policy=replace(p.source_policy,revision=rev))
    newer=replace(p,source_policy=replace(p.source_policy,revision=rev),source_policy_ref=replace(p.source_policy_ref,revision=rev))
    assert validate_project(newer).ok and newer.project_id==p.project_id
    assert p.source_policy.revision!=newer.source_policy.revision


def test_alternating_projects_with_equal_human_names_cannot_share_authority():
    a,b=project(),project(name='project-beta'); before=hash(a),hash(b)
    assert a.display_name==b.display_name and a.project_id!=b.project_id
    for first,second in permutations((a,b)):
        assert check_project_membership(first,ref(first.project_id)).allowed
        other=check_project_membership(first,ref(second.project_id))
        assert other.status is MembershipStatus.REQUIRES_APPROVAL
        assert other.code=='FORBIDDEN_CROSS_PROJECT_REF' and not other.allowed
    assert (hash(a),hash(b))==before


def test_federated_order_preserves_declared_authorities_not_first_repository():
    p=project(StorageMode.FEDERATED);d=p.storage
    for repositories in permutations(d.repositories):
        revised=replace(d,repositories=repositories,authority_by_class=tuple(reversed(d.authority_by_class)))
        q=replace(p,storage=revised)
        assert validate_project(q).ok
        assert dict(q.storage.authority_by_class)==dict(d.authority_by_class)
        assert q.constitution_ref==p.constitution_ref
    with pytest.raises(FrozenInstanceError):p.display_name='mutated'


@pytest.mark.parametrize('mode', [StorageMode.EMBEDDED,StorageMode.SIDECAR])
def test_declared_modes_do_not_create_a_second_authority(mode):
    p=project(mode);d=p.storage
    bad=rebuilt(d,authority_by_class=(('decision',d.authority_repository),))
    assert not validate_storage_mode(bad).ok
    assert validate_project(p).ok


def test_malformed_authority_key_cannot_invoke_hash_or_equality():
    seen=[]
    class Key:
        def __hash__(self):seen.append('hash');raise AssertionError('project code executed')
        def __eq__(self,other):seen.append('eq');raise AssertionError('project code executed')
    d=project(StorageMode.FEDERATED).storage
    try:
        StorageDescriptor(d.mode,d.authority_repository,d.repositories,((Key(),d.authority_repository),))
    except (TypeError,ValueError):pass
    assert not seen
