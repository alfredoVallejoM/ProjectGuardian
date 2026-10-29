"""G00-01: regression probes for the public identity boundary (no mocks of validators)."""
from dataclasses import fields, replace
from collections.abc import Mapping
import pytest
from guardian.domain.identity import (
    ProjectId, EntityId, EntityKind as K, RevisionId, ContentDigest, DigestAlgorithm as D,
    EntityRef, Alias, AliasBinding, AliasIndex, IdentityIndex, IdentityRegistration,
    parse_project_id, parse_entity_id, parse_revision_id, parse_content_digest,
    encode_identity, decode_identity, bind_alias, resolve_alias, register_identity,
)


def forged(record, **changes):
    obj = object.__new__(type(record))
    for f in fields(record):
        object.__setattr__(obj, f.name, changes.get(f.name, getattr(record, f.name)))
    return obj


def ref(name='entity-one', kind=K.OBLIGATION):
    p=ProjectId('project-alpha')
    return EntityRef(p,kind,EntityId(p,kind,name),RevisionId('rev-'+'a'*32))


def test_nested_project_is_validated_by_entity_parser():
    result=parse_entity_id(forged(ProjectId('project-alpha'),value='../bad'),K.OBLIGATION,'entity-one')
    assert not result.ok


def test_direct_reference_cannot_embed_a_mutable_revision():
    good=ref()
    with pytest.raises((TypeError,ValueError)):
        replace(good,revision=forged(good.revision,value='latest'))


@pytest.mark.parametrize('kind',['project','entity','revision','digest','reference'])
def test_encoder_validates_the_actual_nominal_payload(kind):
    good=ref()
    values={
        'project':forged(good.project,value=''),
        'entity':forged(good.entity,project=forged(good.project,value='')),
        'revision':forged(good.revision,value='HEAD'),
        'digest':forged(ContentDigest(D.SHA256,'a'*64),hex='abc'),
        'reference':forged(good,revision=forged(good.revision,value='latest')),
    }
    with pytest.raises((TypeError,ValueError)):
        encode_identity(values[kind])


@pytest.mark.parametrize('parser,args',[
    (parse_project_id,('',)),
    (parse_entity_id,(None,K.PROPERTY,'entity-one')),
    (parse_revision_id,('main',)),
    (parse_content_digest,('bad','x')),
    (decode_identity,({'type':'invalid'},)),
])
@pytest.mark.parametrize('path',[None,0,''])
def test_invalid_diagnostic_path_never_crashes_a_rejecting_parser(parser,args,path):
    result=parser(*args,path=path)
    assert not result.ok and result.diagnostics[0].path=='$'


def test_decode_rejects_custom_mapping_without_executing_it():
    calls=[]
    class Hostile(Mapping):
        def __getitem__(self,key):calls.append('getitem');return 'project_id'
        def __iter__(self):calls.append('iter');return iter(())
        def __len__(self):calls.append('len');return 0
    result=decode_identity(Hostile())
    assert not result.ok and calls==[]


def test_decode_does_not_call_payload_equality_or_string_conversion():
    calls=[]
    class Hostile:
        def __eq__(self,other):calls.append('eq');return False
        def __str__(self):calls.append('str');return 'untrusted'
    result=decode_identity({'schema':Hostile(),'type':'project_id','value':'project-alpha'})
    assert not result.ok and not calls


def test_alias_index_is_revalidated_before_resolution():
    target=ref();source=ref('source-one',K.SOURCE)
    good=AliasBinding(Alias('Readable'),target,source)
    invalid=forged(good,target=forged(target,revision=forged(target.revision,value='latest')))
    index=forged(AliasIndex(),bindings=(invalid,))
    result=resolve_alias(index,target.project,target.kind,good.alias)
    assert not result.ok


def test_registry_revalidates_existing_entries_before_adding():
    target=ref()
    old=IdentityRegistration(target.entity,'lineage-old')
    malformed=forged(old,identity=forged(target.entity,project=forged(target.project,value='')))
    index=forged(IdentityIndex(),registrations=(malformed,))
    result=register_identity(index,ref('entity-two').entity,'lineage-new')
    assert not result.ok


def test_alias_provenance_cannot_embed_a_floating_revision():
    target=ref();source=ref('source-one',K.SOURCE)
    with pytest.raises((TypeError,ValueError)):
        bind_alias(AliasIndex(),target,Alias('Name'),forged(source,revision=forged(source.revision,value='main')))


def test_nested_project_is_validated_by_direct_entity_constructor():
    bad=forged(ProjectId('project-alpha'),value='../bad')
    with pytest.raises((TypeError,ValueError)):
        EntityId(bad,K.OBLIGATION,'entity-one')


@pytest.mark.parametrize('member',["property","made_up"])
def test_fabricated_entity_enum_is_not_a_real_registered_kind(member):
    fake=str.__new__(K,member)
    object.__setattr__(fake,'_value_',member)
    object.__setattr__(fake,'_name_','FORGED')
    result=parse_entity_id(ProjectId('project-alpha'),fake,'entity-one')
    assert not result.ok and result.diagnostics[0].code=='WRONG_ID_KIND'
    with pytest.raises((TypeError,ValueError)):
        EntityId(ProjectId('project-alpha'),fake,'entity-one')


@pytest.mark.parametrize('name',['sha256','made_up'])
def test_fabricated_digest_enum_is_not_a_known_algorithm(name):
    fake=str.__new__(D,name)
    object.__setattr__(fake,'_value_',name)
    object.__setattr__(fake,'_name_','FORGED')
    result=parse_content_digest(fake,'a'*64)
    assert not result.ok and result.diagnostics[0].code=='UNSUPPORTED_DIGEST'


def test_encoder_adapter_keeps_external_metaclass_opaque():
    from guardian.application.identity_codec_service import encode_identity_result
    calls=[]
    class Meta(type):
        def __getattribute__(cls,name):
            if name=='__name__':calls.append(name)
            return super().__getattribute__(name)
    class External(metaclass=Meta):pass
    result=encode_identity_result(External())
    assert not result.ok and result.diagnostics[0].code=='WRONG_ID_KIND'
    assert calls==[]
