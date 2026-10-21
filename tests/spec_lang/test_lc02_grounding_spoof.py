from dataclasses import replace
from hashlib import sha256
from guardian.domain.identity import ContentDigest,DigestAlgorithm
from guardian.spec_lang.contract import SourceBundle
from guardian.spec_lang.ir import SourceOrigin,IRValue,IRType,IRField,FormulaIR
from guardian.spec_lang.v0 import verify_contract_semantics,OracleStatus
from test_lc01_lc02_semantic_audit import instance

def test_attack_ir_formula_bound_to_comment_instead_of_named_field(pinned):
    ir,bundle,ctx,bindings,expected=instance(pinned)
    data=b'when: yes; // no\nholds: (gamma or delta);\n'
    digest=ContentDigest(DigestAlgorithm.SHA256,sha256(data).hexdigest())
    bundle=SourceBundle(bundle.source_ref,data,digest)
    ctx=replace(ctx,expected_sources=((bundle.source_ref,digest),))
    declarations=[]
    for d in ir.declarations:
        origin=replace(d.origin,source_digest=digest,byte_start=0,byte_end=len(data))
        fields=d.fields
        if d.identity==ir.declarations[0].identity:
            fields=tuple(IRField('when',IRValue(IRType.V4,FormulaIR('no'))) if f.name=='when' else f for f in fields)
        declarations.append(replace(d,origin=origin,fields=fields))
    ir=replace(ir,source_digest=digest,declarations=tuple(declarations))
    wrong=replace(bindings[0],origin=SourceOrigin(bundle.source_ref,digest,data.index(b'no'),data.index(b'no')+2))
    right=replace(bindings[1],origin=SourceOrigin(bundle.source_ref,digest,data.index(b'(gamma'),data.index(b'(gamma')+len(b'(gamma or delta)')))
    report=verify_contract_semantics(ir,bundle,ctx,(wrong,right),expectation=expected)
    assert not report.acceptable and report.status is OracleStatus.MISSING_BINDING


def _new_source_contract(pinned,data,value,field_span):
    ir,bundle,ctx,bindings,expected=instance(pinned)
    digest=ContentDigest(DigestAlgorithm.SHA256,sha256(data).hexdigest())
    bundle=SourceBundle(bundle.source_ref,data,digest)
    ctx=replace(ctx,expected_sources=((bundle.source_ref,digest),))
    declarations=[]
    for i,d in enumerate(ir.declarations):
        origin=replace(d.origin,source_digest=digest,byte_start=0,byte_end=len(data))
        fields=tuple(IRField('when',IRValue(IRType.V4,FormulaIR(value))) if i==0 and f.name=='when' else f for f in d.fields)
        declarations.append(replace(d,origin=origin,fields=fields))
    ir=replace(ir,source_digest=digest,declarations=tuple(declarations))
    begin,end=field_span
    left=replace(bindings[0],origin=SourceOrigin(bundle.source_ref,digest,begin,end))
    right_text=b'(gamma or delta)'
    right_start=data.index(right_text)
    right=replace(bindings[1],origin=SourceOrigin(bundle.source_ref,digest,right_start,right_start+len(right_text)))
    return verify_contract_semantics(ir,bundle,ctx,(left,right),expectation=expected)


def test_comment_or_string_text_never_satisfies_field_binding(pinned):
    for raw in (b'when: yes; // no\nholds: (gamma or delta);\n',
                b'when: yes; label: "when: no";\nholds: (gamma or delta);\n',
                b'when: yes; /* when: no; */ holds: (gamma or delta);\n'):
        idx=raw.index(b'no')
        report=_new_source_contract(pinned,raw,'no',(idx,idx+2))
        assert report.status is OracleStatus.MISSING_BINDING and not report.acceptable


def test_duplicate_field_and_truncated_formula_cannot_earn_equivalence(pinned):
    raw=b'when: yes; when: no;\nholds: (gamma or delta);\n'
    begin=raw.index(b'yes')
    assert _new_source_contract(pinned,raw,'yes',(begin,begin+3)).status is OracleStatus.MISSING_BINDING
    raw=b'when: yes and no;\nholds: (gamma or delta);\n'
    begin=raw.index(b'yes')
    assert _new_source_contract(pinned,raw,'yes',(begin,begin+3)).status is OracleStatus.MISSING_BINDING


def test_expected_named_field_span_still_accepts_valid_normative_formula(pinned):
    raw=b'/* when: no; */\nwhen: yes; // ignore no\nholds: (gamma or delta);\n'
    begin=raw.index(b'yes')
    report=_new_source_contract(pinned,raw,'yes',(begin,begin+3))
    assert report.acceptable and report.status is OracleStatus.FINITE_EQUIVALENT


def test_decoder_exhaustion_rejected_before_parsing_untrusted_ir():
    import pytest
    from guardian.spec_lang.ir import decode_ir
    with pytest.raises(ValueError,match='IR_SCHEMA_RESOURCE_LIMIT'):
        decode_ir(b' '*8_000_001)
