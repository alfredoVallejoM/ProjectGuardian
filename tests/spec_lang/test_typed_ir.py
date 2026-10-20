import json
from dataclasses import replace
import pytest

from guardian.domain.identity import ContentDigest, DigestAlgorithm, EntityId, EntityKind, EntityRef, ProjectId, RevisionId
from guardian.spec_lang.contract import ProofObligation, ProofState
from guardian.spec_lang.ir import (
    IRType, IRValue, IRField, FormulaIR, SourceItem, SourceOrigin,
    DeclarationIR, ContractIR, CommitmentKind, RelationKind,
    canonical_bytes, decode_ir, contract_digest, ir_to_data,
)


def ref(project,kind,value,rev):
    return EntityRef(project,kind,EntityId(project,kind,value),rev)


def sample(pinned):
    bundle,ctx=pinned
    p=ctx.project
    rev=bundle.revision
    scope=ref(p,EntityKind.SCOPE,'project-scope',rev)
    prop=ref(p,EntityKind.PROPERTY,'property-id',rev)
    obligation=ref(p,EntityKind.OBLIGATION,'obligation-id',rev)
    origin=SourceOrigin(bundle.source_ref,bundle.expected_digest,13,len(bundle.source_bytes)-2)
    prop_decl=DeclarationIR(prop,origin,(
        IRField('kind',IRValue(IRType.KIND,CommitmentKind.CONSTITUTION)),
        IRField('subject',IRValue(IRType.REF,ref(p,EntityKind.PROJECT,'project-record',rev))),
        IRField('deferred_semantics',IRValue(IRType.DEFERRED,'nominal-semantics-not-yet-interpreted')),
    ))
    ob_decl=DeclarationIR(obligation,origin,(
        IRField('from',IRValue(IRType.SOURCE_ITEM,SourceItem(bundle.source_ref,'G00-01-F01'))),
        IRField('kind',IRValue(IRType.KIND,CommitmentKind.CONSTITUTION)),
        IRField('scope',IRValue(IRType.REF,scope)),
        IRField('when',IRValue(IRType.V4,FormulaIR('not',(FormulaIR('and',(
            FormulaIR('atom',name='alpha'), FormulaIR('atom',name='beta'))),)))),
        IRField('requires',IRValue(IRType.REF,prop)),
    ))
    ir=ContractIR(p,bundle.source_ref,bundle.expected_digest,(prop_decl,ob_decl),
                  (ProofObligation('PO-NOMINAL',prop,ProofState.UNPROVEN),))
    return ir,bundle,ctx


def test_real_domain_nominal_refs_in_typed_ir(pinned):
    ir,bundle,ctx=sample(pinned)
    ir.verify_sources(bundle)
    assert ir.declarations[1].identity.kind is EntityKind.OBLIGATION
    assert ir.declarations[1].fields[3].typed_value.kind is IRType.V4
    assert ir.proofs[0].state is ProofState.UNPROVEN


def test_canonical_roundtrip_preserves_all_types_and_source(pinned):
    ir,bundle,ctx=sample(pinned)
    encoded=canonical_bytes(ir)
    back=decode_ir(encoded)
    assert back == ir
    assert canonical_bytes(back)==encoded
    assert len(contract_digest(ir).hex)==64
    assert contract_digest(back)==contract_digest(ir)


def test_ref_types_cannot_be_interchanged_or_cast_from_plain_string(pinned):
    ir,bundle,ctx=sample(pinned)
    obj=ir.declarations[1]
    wrong=IRField('scope',IRValue(IRType.REF,obj.identity))
    with pytest.raises(TypeError,match='WRONG_REFERENCE_KIND'):
        DeclarationIR(obj.identity,obj.origin,tuple(wrong if f.name=='scope' else f for f in obj.fields))
    with pytest.raises(TypeError):
        IRValue(IRType.REF,'obligation-id')
    with pytest.raises(TypeError):
        IRValue(IRType.BOOL,1)


def test_decl_not_merely_dictionary_and_required_fields(pinned):
    ir,bundle,ctx=sample(pinned)
    d=ir.declarations[1]
    with pytest.raises(ValueError,match='MISSING_NORMATIVE_FIELD'):
        DeclarationIR(d.identity,d.origin,tuple(f for f in d.fields if f.name!='from'))
    with pytest.raises(ValueError,match='UNKNOWN_NORMATIVE_FIELD'):
        DeclarationIR(d.identity,d.origin,d.fields+(IRField('unapproved',IRValue(IRType.BOOL,True)),))
    with pytest.raises(ValueError,match='DUPLICATE_FIELD'):
        DeclarationIR(d.identity,d.origin,d.fields+(d.fields[0],))


def test_foreign_project_and_wrong_origin_detected(pinned):
    ir,bundle,ctx=sample(pinned)
    foreign=ProjectId('foreign-project')
    foreign_ob=ref(foreign,EntityKind.OBLIGATION,'obligation-id',bundle.revision)
    with pytest.raises(ValueError,match='foreign declaration origin'):
        DeclarationIR(foreign_ob,ir.declarations[1].origin,ir.declarations[1].fields)
    with pytest.raises(ValueError,match='DUPLICATE_DECLARATION'):
        replace(ir,declarations=ir.declarations+(ir.declarations[1],))
    with pytest.raises(ValueError,match='IR_SOURCE_MISMATCH'):
        ir.verify_sources(replace(bundle,source_ref=ref(ctx.project,EntityKind.SOURCE,'other-source',bundle.revision)))


def test_source_origin_utf8_byte_boundaries_and_digest(pinned):
    ir,bundle,ctx=sample(pinned)
    text='É and beta'.encode('utf-8')
    from guardian.spec_lang.contract import SourceBundle
    from hashlib import sha256
    digest=ContentDigest(DigestAlgorithm.SHA256,sha256(text).hexdigest())
    utf8_bundle=SourceBundle(bundle.source_ref,text,digest)
    SourceOrigin(bundle.source_ref,digest,0,len(text)).verify_against(utf8_bundle)
    with pytest.raises(ValueError,match='SPLITS_UTF8'):
        SourceOrigin(bundle.source_ref,digest,0,1).verify_against(utf8_bundle)
    with pytest.raises(ValueError,match='OUT_OF_BOUNDS'):
        SourceOrigin(bundle.source_ref,digest,0,500).verify_against(utf8_bundle)


def test_decoder_rejects_schema_extension_recomputed_digest_and_duplicate_json_keys(pinned):
    ir,bundle,ctx=sample(pinned)
    raw=ir_to_data(ir)
    raw['future_normative_semantics']='silently-ignore'
    with pytest.raises(ValueError,match='IR_SCHEMA_FIELDS'):
        decode_ir(json.dumps(raw).encode())
    raw=ir_to_data(ir)
    raw['semantic_version']='gsl0-2'
    with pytest.raises(ValueError,match='UNSUPPORTED_IR_SCHEMA_VERSION'):
        decode_ir(json.dumps(raw).encode())
    with pytest.raises(ValueError,match='DUPLICATE_JSON_KEY'):
        decode_ir(b'{"schema":"x","schema":"y"}')


def test_mutation_changes_digest_but_does_not_authorize_new_semantics(pinned):
    ir,bundle,ctx=sample(pinned)
    ob=ir.declarations[1]
    wrong=IRField('when',IRValue(IRType.V4,FormulaIR('no')))
    changed=replace(ir,declarations=(ir.declarations[0],
        DeclarationIR(ob.identity,ob.origin,tuple(wrong if f.name=='when' else f for f in ob.fields))))
    assert contract_digest(ir)!=contract_digest(changed)
    assert decode_ir(canonical_bytes(changed))==changed
    # The independent source-to-IR oracle must catch this valid-but-wrong IR.
    from guardian.spec_lang.v0 import verify_semantics, OracleStatus
    res=verify_semantics(bundle,ctx,ob.origin,wrong.typed_value.value)
    assert res.status is OracleStatus.COUNTEREXAMPLE


def test_property_cannot_fake_proof_by_omitting_interpreted_vs_deferred(pinned):
    ir,bundle,ctx=sample(pinned)
    prop=ir.declarations[0]
    with pytest.raises(ValueError,match='precisely one'):
        DeclarationIR(prop.identity,prop.origin,tuple(f for f in prop.fields if f.name!='deferred_semantics'))
