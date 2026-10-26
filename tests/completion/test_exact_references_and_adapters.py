from dataclasses import replace
import pytest
from foundation_completion import scenario
from foundation_b02 import entity
from completion_support import body
from guardian.domain.identity import EntityKind as K,RevisionId,encode_identity,Alias,AliasIndex,bind_alias,resolve_alias
from guardian.domain.references import resolve_entity,validate_references
from guardian.application.identity_codec_service import encode_identity_result,decode_identity_result


def test_exact_revision_no_latest_current_vs_history_and_no_placeholder():
    req,_,ids=scenario();ref=ids['property-main'];old=body(req,ref)
    new=replace(old,identity=replace(ref,revision=RevisionId('rev-'+'9'*32)),guarantee='new revised guarantee')
    with pytest.raises(ValueError,match='MULTIPLE_CURRENT_REVISIONS'):replace(req.view,records=req.view.records+(new,))
    view=replace(req.view,records=req.view.records+(new,),historical=frozenset({ref}))
    assert resolve_entity(ref,view,K.PROPERTY).value.record is old
    assert resolve_entity(new.identity,view,K.PROPERTY).value.record is new
    assert not resolve_entity(ref,view,K.PROPERTY,require_current=True).ok
    absent=replace(ref,revision=RevisionId('rev-'+'8'*32))
    assert resolve_entity(absent,view,K.PROPERTY).diagnostics[0].code=='UNKNOWN_REVISION'
    anchor=entity(req.view.project_id,K.PROPERTY,'unavailable-property')
    assert resolve_entity(anchor,replace(view,anchors=(anchor,)),K.PROPERTY).diagnostics[0].code=='REFERENCED_CONTENT_UNAVAILABLE'


def test_entire_new_snapshot_resolves_actual_content_without_treating_ontology_as_DAG():
    req,_,_=scenario();before=hash(req.view)
    result=validate_references(req.view.records,req.view)
    assert result.ok,result.diagnostics
    assert result.checked>100
    assert validate_references(tuple(reversed(req.view.records)),req.view)==result
    assert hash(req.view)==before


def test_alias_ambiguity_cannot_choose_a_content_or_revision():
    req,_,ids=scenario();alias=Alias('Contrato');source=req.view.sources[0].ref
    index=bind_alias(AliasIndex(),ids['obligation-now'],alias,source).index
    index=bind_alias(index,ids['obligation-future'],alias,source).index
    result=resolve_alias(index,req.view.project_id,K.OBLIGATION,alias)
    assert not result.ok and result.diagnostics[0].code=='AMBIGUOUS_ALIAS'


def test_source_refs_do_not_use_the_entity_content_resolver():
    req,_,_=scenario();s=req.view.sources[0].ref
    result=resolve_entity(s,req.view,K.SOURCE)
    assert not result.ok and result.diagnostics[0].code=='SOURCE_RESOLVER_REQUIRED'
    assert resolve_entity(req.constitution.rule_refs[0],req.view,K.OBLIGATION).diagnostics[0].code=='WRONG_ID_KIND'


@pytest.mark.parametrize('bad',[None,'plain-string',{},1,True])
def test_public_encoder_adapts_invalid_inputs_to_original_error_contract(bad):
    result=encode_identity_result(bad)
    assert not result.ok and result.diagnostics[0].code=='WRONG_ID_KIND'


def test_public_decoder_maps_schema_alias_without_hiding_unknown_kind():
    req,_,ids=scenario();wire=encode_identity(ids['obligation-now'])
    assert decode_identity_result(wire).value==ids['obligation-now']
    malformed=dict(wire);malformed['schema']='future.schema/v9'
    errors=decode_identity_result(malformed).diagnostics
    assert errors[0].code=='INVALID_SCHEMA' and '[INVALID_ID_SCHEMA]' in errors[0].reason
    malformed=dict(wire);malformed['type']='new-unrecognized-identity'
    assert decode_identity_result(malformed).diagnostics[0].code=='UNKNOWN_ID_KIND'


def test_draft_does_not_execute_a_hostile_object_disguised_as_frozen_data():
    from guardian.domain.drafts import RecordDraft
    req,_,ids=scenario();touched=[]
    class Hostile:
        def __getattribute__(self,name):
            touched.append(name);raise AssertionError('candidate code executed')
    with pytest.raises(TypeError):RecordDraft(ids['obligation-now'],(('owner',Hostile()),))
    assert not touched
