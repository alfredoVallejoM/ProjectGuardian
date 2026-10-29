"""Direct acceptance of G00-01 F01..F10 and APIs 001..008.

These are product assertions, not tests of a synthetic acceptance checker.
The finite generators are controlled by the test; production never generates IDs.
"""
from dataclasses import FrozenInstanceError, fields, replace
from itertools import permutations, product
from pathlib import Path
import ast
import json
import pytest
from guardian.domain.identity import (
    ProjectId, EntityId, EntityRef, EntityKind as K, RevisionId, ContentDigest,
    DigestAlgorithm as D, Alias, AliasBinding, AliasIndex, IdentityIndex,
    parse_project_id, parse_entity_id, parse_revision_id, parse_content_digest,
    encode_identity, decode_identity, bind_alias, resolve_alias, register_identity,
    resolve_entity,
)
from guardian.application.identity_codec_service import encode_identity_result, decode_identity_result
from guardian.domain.references import RecordSnapshot, EntityImport, TrustedEntityImports
from guardian.domain.source import ApprovedSourceImport
from foundation_b02 import entity
from foundation_b03 import scenario


def ids():
    p=ProjectId('project-alpha');e=EntityId(p,K.PROPERTY,'entity-one');r=RevisionId('rev-'+'a'*32)
    return p,e,r,ContentDigest(D.SHA256,'a'*64),EntityRef(p,K.PROPERTY,e,r)


def reject(result,code,path=None):
    assert not result.ok and result.value is None
    assert result.diagnostics[0].code==code
    if path is not None:assert result.diagnostics[0].path==path


def test_F01_positive_all_nominal_parser_results_and_immutable_values():
    p,e,r,d,ref=ids()
    outputs=(parse_project_id(p.value),parse_entity_id(p,K.PROPERTY,e.value),
             parse_revision_id(r.value),parse_content_digest(d.algorithm,d.hex))
    for out,expected in zip(outputs,(p,e,r,d)):
        assert out.ok and out.value==expected and type(out.value) is type(expected)
        with pytest.raises(FrozenInstanceError):
            setattr(out.value,'hex' if type(out.value) is ContentDigest else 'value','changed')
    assert len({type(x) for x in (p,e,r,d,ref)})==5


def test_F01_negative_nominal_values_are_not_coerced_to_strings():
    p,e,r,d,_=ids()
    for value in (p,e,r,d,None,False,12,[],{},b'project-alpha'):
        assert not parse_project_id(value).ok
        assert not parse_revision_id(value).ok
        assert not parse_entity_id(p,K.PROPERTY,value).ok
    reject(parse_entity_id(p,r,'entity-one'),'WRONG_ID_KIND')


def test_F02_positive_namespace_kind_and_value_all_participate():
    projects=(ProjectId('project-alpha'),ProjectId('project-beta'))
    items=[EntityId(p,k,'same-value') for p,k in product(projects,K)]
    assert len(set(items))==len(items)
    assert all(a==b if i==j else a!=b for i,a in enumerate(items) for j,b in enumerate(items))
    for item in items:
        assert decode_identity(encode_identity(item)).value==item


def test_F02_negative_foreign_or_wrong_kind_reference_cannot_bind_local_id():
    p,e,r,_,_=ids();foreign=ProjectId('project-beta')
    with pytest.raises(ValueError):EntityRef(foreign,K.PROPERTY,e,r)
    with pytest.raises(ValueError):EntityRef(p,K.OBLIGATION,e,r)
    reject(parse_entity_id('project-alpha',K.PROPERTY,e.value),'PROJECT_REQUIRED')
    reject(parse_entity_id(p,'property',e.value),'WRONG_ID_KIND')


def test_F03_positive_grammar_boundaries_and_diagnostic_paths():
    for name in ('abc','a-b','a12','a'*96,'ab-'+'c'*93):
        assert parse_project_id(name).value==ProjectId(name)
        assert parse_entity_id(ids()[0],K.OBLIGATION,name).value.value==name
    assert parse_revision_id('rev-'+'0'*32).ok
    assert parse_revision_id('rev-'+'f'*32).ok


@pytest.mark.parametrize('name',['','a','ab','a'*97,'Upper','a--b','-abc','abc-','../x','/tmp','a_b','a:b','a b','abc\n','ábc','a\x00b'])
def test_F03_negative_grammar_never_normalizes_invalid_identity(name):
    code='EMPTY_ID' if name=='' else 'INVALID_ID_SYNTAX'
    reject(parse_project_id(name,path='$.project'),code,'$.project')
    reject(parse_entity_id(ids()[0],K.PROPERTY,name,path='$.entity'),'INVALID_ID_SYNTAX','$.entity')


def test_F04_positive_alias_provenance_scope_duplicates_and_order():
    p,source,records,view,names=scenario();target=names['property-shared'];alias=Alias('Propiedad β')
    other_source=replace(source.ref,entity=replace(source.ref.entity,value='source-second'))
    outcomes=[]
    for order in permutations((source.ref,other_source)):
        index=AliasIndex()
        for provenance in order:index=bind_alias(index,target,alias,provenance).index
        result=resolve_alias(index,p.project_id,K.PROPERTY,alias)
        assert result.value==target
        assert {b.source for b in index.bindings}=={source.ref,other_source}
        assert resolve_entity(result.value,view,K.PROPERTY).value.record is records[4]
        duplicate=bind_alias(index,target,alias,order[0])
        assert duplicate.index is index and duplicate.diagnostics[0].code=='DUPLICATE_BINDING'
        outcomes.append(result)
    assert outcomes[0]==outcomes[1]


def test_F04_negative_ambiguous_alias_never_first_wins_ADV03():
    p,source,records,view,names=scenario();alias=Alias('Shared')
    first=names['property-shared'];second=entity(p.project_id,K.PROPERTY,'other-property')
    for order in permutations((first,second)):
        empty=AliasIndex();index=empty
        for target in order:out=bind_alias(index,target,alias,source.ref);index=out.index
        assert out.diagnostics and out.diagnostics[0].code=='AMBIGUOUS_ALIAS'
        reject(resolve_alias(index,p.project_id,K.PROPERTY,alias),'AMBIGUOUS_ALIAS')
        assert empty.bindings==()
    reject(resolve_alias(AliasIndex(),p.project_id,K.PROPERTY,alias),'UNKNOWN_ALIAS')


def test_F05_positive_alias_and_path_rename_preserve_logical_identity():
    p,source,records,view,names=scenario();old=records[4]
    moved=replace(source,ref=replace(source.ref,revision=RevisionId('rev-'+'b'*32)),path='moved/source.gsl')
    revised=replace(old,identity=replace(old.identity,revision=RevisionId('rev-'+'c'*32)),source_refs=(moved.ref,))
    assert revised.identity.entity==old.identity.entity and moved.ref.entity==source.ref.entity
    index=bind_alias(AliasIndex(),old.identity,Alias('Antes'),source.ref).index
    index=bind_alias(index,revised.identity,Alias('Después'),moved.ref).index
    revised_view=RecordSnapshot(p.project_id,view.revision,(old,revised),(source,moved),
        view.anchors,frozenset({old.identity}))
    for alias,record in ((Alias('Antes'),old),(Alias('Después'),revised)):
        found=resolve_alias(index,p.project_id,K.PROPERTY,alias).value
        assert resolve_entity(found,revised_view,K.PROPERTY).value.record is record
    assert source.path!=moved.path and source.ref.revision!=moved.ref.revision


def test_F05_negative_alias_does_not_retarget_or_regenerate_existing_identity():
    p,source,records,view,names=scenario();target=records[4].identity;alias=Alias('Name')
    original=bind_alias(AliasIndex(),target,alias,source.ref).index
    another=entity(p.project_id,target.kind,'renamed-object')
    updated=bind_alias(original,another,alias,source.ref)
    reject(resolve_alias(updated.index,p.project_id,target.kind,alias),'AMBIGUOUS_ALIAS')
    assert resolve_alias(original,p.project_id,target.kind,alias).value==target
    assert target.entity.value=='property-shared'


def test_F06_positive_exact_revision_history_facade_and_no_mutation():
    p,s,records,view,names=scenario();old=records[4]
    new=replace(old,identity=replace(old.identity,revision=RevisionId('rev-'+'b'*32)),statement='Version two')
    view=replace(view,records=view.records+(new,),historical=frozenset({old.identity}))
    before=(view.records,view.sources,view.anchors,view.historical,dict(view._by_ref),hash(view))
    for order in (view.records,tuple(reversed(view.records))):
        selected=replace(view,records=order)
        for record in (old,new):
            for _ in range(2):
                out=resolve_entity(record.identity,selected,K.PROPERTY)
                assert out.ok and out.value.record is record
                assert out.value.reference==record.identity
                assert out.value.historical==(record is old)
                assert not out.value.normatively_admitted
    assert (view.records,view.sources,view.anchors,view.historical,dict(view._by_ref),hash(view))==before


def test_F06_negative_no_latest_anchor_or_source_substitution_API008():
    _,s,records,view,names=scenario();wanted=names['property-shared']
    absent=replace(wanted,revision=RevisionId('rev-'+'f'*32))
    reject(resolve_entity(absent,view,K.PROPERTY),'UNKNOWN_REVISION')
    reject(resolve_entity(wanted,view,K.CAPABILITY),'WRONG_ID_KIND')
    reject(resolve_entity(records[0].scope_ref,view,K.SCOPE),'REFERENCED_CONTENT_UNAVAILABLE')
    reject(resolve_entity(s.ref,view,K.SOURCE),'SOURCE_RESOLVER_REQUIRED')
    historic=replace(view,historical=frozenset({wanted}))
    reject(resolve_entity(wanted,historic,K.PROPERTY,require_current=True),'HISTORICAL_REFERENCE_NOT_CURRENT')
    for raw in (None,'','main','HEAD','latest','rev-'+ 'f'*31):
        assert not parse_revision_id(raw).ok


def test_F06_import_is_exact_entity_revision_and_material_cut():
    a=scenario();b=scenario('project-beta');target=b[4]['property-shared'];src=b[1]
    approval=entity(a[0].project_id,K.DECISION,'decision-import')
    grant=ApprovedSourceImport(a[0].project_id,src.ref,src.repository,src.path,approval,src)
    imports=TrustedEntityImports((EntityImport(grant,frozenset({target}),b[3]),))
    reject(resolve_entity(target,a[3],K.PROPERTY),'FORBIDDEN_CROSS_PROJECT_REF')
    out=resolve_entity(target,a[3],K.PROPERTY,imports)
    assert out.ok and out.value.record is b[2][4] and out.value.imported
    reject(resolve_entity(b[4]['capability-one'],a[3],K.CAPABILITY,imports),'UNAPPROVED_IMPORT_SCOPE')
    other=replace(target,revision=RevisionId('rev-'+'b'*32))
    reject(resolve_entity(other,a[3],K.PROPERTY,imports),'UNAPPROVED_IMPORT_SCOPE')
    with pytest.raises(ValueError,match='IMPORT_MATERIAL_CUT_MISMATCH'):
        replace(imports.entries[0],snapshot=replace(b[3],sources=(replace(src,commit='d'*40),)))


@pytest.mark.parametrize('algorithm,length',[(D.SHA256,64),(D.SHA512,128)])
def test_F07_positive_digest_algorithm_length_normalization_roundtrip(algorithm,length):
    raw='ABCDEF01'*(length//8)
    result=parse_content_digest(algorithm,raw)
    assert result.value==ContentDigest(algorithm,raw.lower())
    out=decode_identity(encode_identity(result.value)).value
    assert out.algorithm is algorithm and out.hex==raw.lower()


@pytest.mark.parametrize('algorithm,length',[(D.SHA256,64),(D.SHA512,128)])
def test_F07_negative_truncation_algorithm_and_nonhex(algorithm,length):
    for raw in ('a'*(length-1),'a'*(length+1),'g'*length,' '*length,'',None,True):
        reject(parse_content_digest(algorithm,raw),'DIGEST_MALFORMED')
    reject(parse_content_digest(algorithm.value,'a'*length),'UNSUPPORTED_DIGEST')


def test_F08_positive_identity_operations_do_not_use_environment_clock_or_rng(monkeypatch):
    import time,random,uuid,os
    p,e,r,d,ref=ids()
    def forbidden(*args,**kwargs):raise AssertionError('impure identity operation')
    with monkeypatch.context() as m:
        for module,attr in ((time,'time'),(time,'time_ns'),(random,'random'),(random,'getrandbits'),(uuid,'uuid4'),(os,'getenv'),(os,'urandom')):
            m.setattr(module,attr,forbidden)
        for _ in range(5):
            assert parse_project_id(p.value).value==p
            assert parse_entity_id(p,e.kind,e.value).value==e
            assert parse_revision_id(r.value).value==r
            assert parse_content_digest(d.algorithm,d.hex).value==d
            assert decode_identity(encode_identity(ref)).value==ref
            assert register_identity(IdentityIndex(),e,'lineage-one').ok


def test_F08_negative_external_values_cannot_execute_coercion_or_metaclass_hooks():
    calls=[]
    class Meta(type):
        def __getattribute__(cls,name):
            if name=='__name__':calls.append('name')
            return super().__getattribute__(name)
        def __eq__(cls,other):calls.append('class-equality');return False
    class External(metaclass=Meta):
        def __str__(self):calls.append('str');return 'project-alpha'
        def __repr__(self):calls.append('repr');return 'project-alpha'
    value=External()
    assert not parse_project_id(value).ok
    assert not parse_revision_id(value).ok
    assert not decode_identity(value).ok
    with pytest.raises(TypeError):encode_identity(value)
    assert not calls


def test_F09_positive_serialization_injective_over_finite_nominal_population():
    values=[]
    for i in range(32):
        p=ProjectId(f'project-{i}');r=RevisionId('rev-'+format(i,'032x'))
        values.extend((p,r,ContentDigest(D.SHA256,format(i,'064x')),ContentDigest(D.SHA512,format(i,'0128x'))))
        for kind in K:
            e=EntityId(p,kind,f'entity-{i}');values.extend((e,EntityRef(p,kind,e,r)))
    encodings=[]
    for value in values:
        encoded=encode_identity(value);copy=json.loads(json.dumps(encoded))
        assert decode_identity(copy).value==value and type(decode_identity(copy).value) is type(value)
        encodings.append(json.dumps(encoded,sort_keys=True,separators=(',',':')))
    assert len(set(encodings))==len(set(values))==len(values)


def test_F09_negative_fields_discriminants_schema_and_namespace_are_never_defaulted_ADV02():
    for value in ids():
        wire=encode_identity(value)
        for key in wire:
            changed=dict(wire);del changed[key]
            assert not decode_identity(changed).ok
        assert not decode_identity(dict(wire,extra='unknown normative field')).ok
        reject(decode_identity(dict(wire,schema='guardian.identity/v99')),'INVALID_ID_SCHEMA')
        reject(decode_identity(dict(wire,type='new_unknown_kind')),'UNKNOWN_ID_KIND')
    ref=encode_identity(ids()[-1]);ref.pop('entity_kind')
    reject(decode_identity(ref),'INVALID_ID_SCHEMA')
    reject(decode_identity_result(ref),'INVALID_SCHEMA')


def test_F10_positive_same_lineage_idempotent_independent_namespaces():
    p,e,_,_,_=ids();empty=IdentityIndex()
    one=register_identity(empty,e,'lineage-one').value
    assert register_identity(one,e,'lineage-one').value is one
    others=(EntityId(ProjectId('project-beta'),e.kind,e.value),EntityId(p,K.OBLIGATION,e.value))
    current=one
    for item in others:current=register_identity(current,item,'lineage-other').value
    assert len(current.registrations)==3 and not empty.registrations
    assert one.registrations[0].identity==e


def test_F10_negative_collision_never_overwrites_previous_identity():
    _,e,_,_,_=ids();index=register_identity(IdentityIndex(),e,'lineage-one').value
    before=index.registrations
    reject(register_identity(index,e,'different-lineage'),'DUPLICATE_LOGICAL_ID')
    assert index.registrations is before
    assert register_identity(index,e,'lineage-one').value==index


def test_API001_004_catalogued_errors_and_paths():
    p,*_=ids()
    cases=((parse_project_id,('',),'EMPTY_ID'),(parse_project_id,('invalid id',),'INVALID_ID_SYNTAX'),
      (parse_entity_id,(None,K.PROPERTY,'entity-one'),'PROJECT_REQUIRED'),
      (parse_entity_id,(p,K.PROPERTY,''),'INVALID_ID_SYNTAX'),
      (parse_revision_id,(None,),'REVISION_REQUIRED'),(parse_revision_id,('main',),'INVALID_REVISION'),
      (parse_content_digest,('md5','0'*32),'UNSUPPORTED_DIGEST'),
      (parse_content_digest,(D.SHA256,'0'*4),'DIGEST_MALFORMED'))
    for fn,args,code in cases:
        result=fn(*args,path='$.contract.id');reject(result,code,'$.contract.id')
        assert result.diagnostics[0].expected and result.diagnostics[0].reason


def test_API005_006_diagnostic_adapters_preserve_values_and_original_causes():
    for value in ids():
        encoded=encode_identity_result(value)
        assert encoded.value==encode_identity(value)
        decoded=decode_identity_result(encoded.value,'$.wire')
        assert decoded.value==value
    for value in (None,False,0,'project-alpha',{}):
        reject(encode_identity_result(value),'WRONG_ID_KIND','$.identity')
    reject(decode_identity_result({'type':'not-known'}),'UNKNOWN_ID_KIND')
    invalid=dict(encode_identity(ids()[0]),schema='newer')
    result=decode_identity_result(invalid,'$.wire')
    reject(result,'INVALID_SCHEMA','$.wire')
    assert '[INVALID_ID_SCHEMA]' in result.diagnostics[0].reason


def test_ADV01_wrong_kind_is_explicit_and_no_cross_axis_identity_equality():
    p,e,r,_,_=ids()
    reject(parse_entity_id(p,r,e.value),'WRONG_ID_KIND')
    assert not parse_revision_id(p.value).ok
    assert p!=e and p!=r and e!=r


def test_parent_connection_alias_codec_snapshot_history_and_collision():
    p,s,records,view,names=scenario();target=records[4].identity
    registry=register_identity(IdentityIndex(),target.entity,'stable-lineage').value
    aliases=bind_alias(AliasIndex(),target,Alias('Contrato'),s.ref).index
    requested=decode_identity(json.loads(json.dumps(encode_identity(resolve_alias(aliases,p.project_id,K.PROPERTY,Alias('Contrato')).value)))).value
    actual=resolve_entity(requested,view,K.PROPERTY)
    assert actual.value.record is records[4] and actual.value.reference==target
    assert not actual.value.normatively_admitted
    reject(register_identity(registry,target.entity,'another-lineage'),'DUPLICATE_LOGICAL_ID')
    absent=replace(requested,revision=RevisionId('rev-'+'e'*32))
    reject(resolve_entity(absent,view,K.PROPERTY),'UNKNOWN_REVISION')
    foreign=scenario('project-beta')
    reject(resolve_entity(requested,foreign[3],K.PROPERTY),'FORBIDDEN_CROSS_PROJECT_REF')


def test_same_lexeme_in_distinct_grammars_stays_nominal_not_interchangeable():
    raw='rev-'+'a'*32
    project=parse_project_id(raw).value;revision=parse_revision_id(raw).value
    assert project is not None and revision is not None and project!=revision
    assert encode_identity(project)['type']=='project_id'
    assert encode_identity(revision)['type']=='revision_id'
    reject(parse_entity_id(revision,K.PROPERTY,'entity-one'),'PROJECT_REQUIRED')
    assert not parse_revision_id(project).ok


def test_all_existing_normative_bodies_preserve_identity_through_v2_codec_and_resolver():
    from foundation_completion import scenario as complete_scenario
    from guardian.persistence.schema_registry import foundation_schema_registry,encode_record,decode_record
    request,_,identities=complete_scenario();registry=foundation_schema_registry(request.view.revision)
    from guardian.domain.clause import ClauseRevision
    clause=ClauseRevision(identity=entity(request.view.project_id,K.CLAUSE,'clause-g00-01'),
        source_refs=(request.view.sources[0].ref,),scope_ref=identities['scope-main'],
        parent_ref=identities['obligation-now'],source_item='G00-01-F06',
        statement='Preserve exact revision',acceptance=('Return the exact body',),
        falsification=('A missing revision must not return latest',))
    request=replace(request,view=replace(request.view,records=request.view.records+(clause,)))
    seen=set()
    for original in request.view.records:
        wire=encode_record(original,registry)
        assert wire.ok,wire.diagnostics
        restored=decode_record(json.loads(json.dumps(wire.value)),registry)
        assert restored.ok,restored.diagnostics
        value=restored.value.record
        assert type(value) is type(original) and value.identity==original.identity
        assert value.source_refs==original.source_refs and not restored.value.normatively_admitted
        found=resolve_entity(value.identity,request.view,value.identity.kind)
        assert found.ok and found.value.record is original
        seen.add(type(original))
        changed=json.loads(json.dumps(wire.value));changed['project_id']['value']='project-foreign'
        assert not decode_record(changed,registry).ok
    assert len(seen)==15


def test_identity_rule_consumer_keeps_valid_input_and_rejects_mutable_nested_revision():
    from foundation_completion import scenario as complete_scenario
    from guardian.constitution.evaluator import evaluate_constitution,RuleVerdict
    from test_boundary_red import forged
    request,engine,_=complete_scenario()
    good=evaluate_constitution(request,engine)
    assert good.aggregate_verdict is RuleVerdict.PASS
    record=next(x for x in request.view.records if x.identity.kind is K.PROPERTY)
    altered=forged(record,identity=forged(record.identity,revision=forged(record.identity.revision,value='main')))
    bad_view=forged(request.view,records=tuple(altered if x is record else x for x in request.view.records))
    bad=evaluate_constitution(replace(request,view=bad_view),engine)
    assert bad.aggregate_verdict is RuleVerdict.INVALID_INPUT
    assert bad.expected_rule_refs==good.expected_rule_refs
    assert not bad.normatively_admitted
