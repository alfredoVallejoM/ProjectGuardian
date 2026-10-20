"""True in-memory G00 identity → typed GSL IR → independent V4 oracle.

This is a foundation integration, not the whole GSL0 compiler or G00 product.
"""
from hashlib import sha256

from guardian.domain.identity import (
    ProjectId, EntityId, EntityRef, RevisionId, EntityKind,
    ContentDigest, DigestAlgorithm, Alias, AliasIndex, bind_alias,resolve_alias,
)
from guardian.domain.outcomes import (
    TypedStatus,StatusAxis,MaterialStatus,QualificationStatus,render_status_vector,
)
from guardian.spec_lang.contract import (
    SourceBundle,CompileContext,CompilerIdentity,SEMANTIC_VERSION,LANGUAGE_VERSION,
    ProofObligation,
)
from guardian.spec_lang.ir import (
    ContractIR,DeclarationIR,IRField,IRValue,IRType,SourceItem,SourceOrigin,
    CommitmentKind,canonical_bytes,decode_ir,
)
from guardian.spec_lang.v0 import parse_source_formula,lower_formula,verify_semantics,OracleStatus


def bind(project,kind,name,revision):
    return EntityRef(project,kind,EntityId(project,kind,name),revision)


def integration_project(project_slug):
    project=ProjectId(project_slug)
    revision=RevisionId('rev-'+'c'*32)
    src=bind(project,EntityKind.SOURCE,'normative-source',revision)
    raw=b'when: not (a and b);\n'
    expr=b'not (a and b)'
    digest=ContentDigest(DigestAlgorithm.SHA256,sha256(raw).hexdigest())
    source=SourceBundle(src,raw,digest)
    context=CompileContext(project,LANGUAGE_VERSION,SEMANTIC_VERSION,
        CompilerIdentity('unit-compiler',SEMANTIC_VERSION,ContentDigest(DigestAlgorithm.SHA256,'d'*64)),
        ((src,digest),),frozenset({'v4-atom','v4-and','v4-not','finite-v4-oracle'}))
    scope=bind(project,EntityKind.SCOPE,'foundation-scope',revision)
    obligation=bind(project,EntityKind.OBLIGATION,'identity-obligation',revision)
    start=raw.index(expr)
    origin=SourceOrigin(src,digest,start,start+len(expr))
    ir_expr=lower_formula(parse_source_formula(raw[start:start+len(expr)]))
    d=DeclarationIR(obligation,origin,(
        IRField('from',IRValue(IRType.SOURCE_ITEM,SourceItem(src,'G00-01-F01'))),
        IRField('kind',IRValue(IRType.KIND,CommitmentKind.CONSTITUTION)),
        IRField('scope',IRValue(IRType.REF,scope)),
        IRField('when',IRValue(IRType.V4,ir_expr)),
    ))
    ir=ContractIR(project,src,digest,(d,),(ProofObligation('INTEGRATION-PENDING',obligation),))
    return source,context,obligation,origin,ir_expr,ir


def test_positive_product_interconnection_real_types():
    a=integration_project('project-alpha')
    source,ctx,ob,origin,expr,ir=a
    assert decode_ir(canonical_bytes(ir))==ir
    assert verify_semantics(source,ctx,origin,expr).status is OracleStatus.FINITE_EQUIVALENT
    idx=bind_alias(AliasIndex(),ob,Alias('Original historical ID'),source.source_ref).index
    assert resolve_alias(idx,ctx.project,EntityKind.OBLIGATION,Alias('Original historical ID')).value==ob
    assert ir.proofs[0].state.value=='UNPROVEN'
    status=render_status_vector((
        TypedStatus(StatusAxis.MATERIAL,MaterialStatus.NOT_RUN),
        TypedStatus(StatusAxis.QUALIFICATION,QualificationStatus.UNQUALIFIED),
    ))
    assert status.value=={'material':'not_run','qualification':'unqualified'}


def test_two_projects_with_overlapping_id_never_merge_authority():
    a=integration_project('project-alpha')
    b=integration_project('project-beta')
    assert a[2].entity.value==b[2].entity.value
    assert a[2] != b[2]
    assert a[5]!=b[5]
    idx=bind_alias(AliasIndex(),a[2],Alias('shared-alias'),a[0].source_ref).index
    idx=bind_alias(idx,b[2],Alias('shared-alias'),b[0].source_ref).index
    assert resolve_alias(idx,a[1].project,EntityKind.OBLIGATION,Alias('shared-alias')).value==a[2]
    assert resolve_alias(idx,b[1].project,EntityKind.OBLIGATION,Alias('shared-alias')).value==b[2]
    assert verify_semantics(b[0],a[1],b[3],b[4]).status is OracleStatus.UNTRUSTED_PIN
