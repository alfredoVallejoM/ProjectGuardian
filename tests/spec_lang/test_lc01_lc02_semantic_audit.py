"""Independent V0 oracle detects omission, misleading grounding, and rehashing."""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json

import pytest

from guardian.domain.identity import ContentDigest, DigestAlgorithm, EntityId, EntityKind, EntityRef, ProjectId
from guardian.spec_lang.contract import SourceBundle, CompileContext
from guardian.spec_lang.ir import (
    ContractIR, DeclarationIR, FormulaIR, IRField, IRType, IRValue,
    CommitmentKind, SourceOrigin, SourceItem, canonical_bytes, contract_digest,
    decode_ir, ir_to_data,
)
from guardian.spec_lang.v0 import (
    FormulaGrounding, CoverageExpectation, OracleStatus, parse_source_formula, lower_formula,
    verify_semantics, verify_contract_semantics,
)


def ref(project,kind,name,rev):
    return EntityRef(project,kind,EntityId(project,kind,name),rev)


def instance(pinned):
    old,ctx=pinned
    text=b'when: not (alpha and beta);\r\nholds: (gamma or delta);\r\n'
    dig=ContentDigest(DigestAlgorithm.SHA256,sha256(text).hexdigest())
    bundle=SourceBundle(old.source_ref,text,dig)
    ctx=replace(ctx,expected_sources=((bundle.source_ref,dig),))
    origin=SourceOrigin(bundle.source_ref,dig,0,len(text))
    ob=ref(ctx.project,EntityKind.OBLIGATION,'verify-this-obligation',bundle.revision)
    prop=ref(ctx.project,EntityKind.PROPERTY,'preserve-this-property',bundle.revision)
    scope=ref(ctx.project,EntityKind.SCOPE,'local-scope',bundle.revision)
    subj=ref(ctx.project,EntityKind.PROJECT,'local-project',bundle.revision)
    left=b'not (alpha and beta)'
    right=b'(gamma or delta)'
    ob_dec=DeclarationIR(ob,origin,(
        IRField('from',IRValue(IRType.SOURCE_ITEM,SourceItem(bundle.source_ref,'G00-01-F01'))),
        IRField('kind',IRValue(IRType.KIND,CommitmentKind.CONSTITUTION)),
        IRField('scope',IRValue(IRType.REF,scope)),
        IRField('when',IRValue(IRType.V4,lower_formula(parse_source_formula(left))))
    ))
    prop_dec=DeclarationIR(prop,origin,(
        IRField('kind',IRValue(IRType.KIND,CommitmentKind.CONSTITUTION)),
        IRField('subject',IRValue(IRType.REF,subj)),
        IRField('holds',IRValue(IRType.V4,lower_formula(parse_source_formula(right))))
    ))
    ir=ContractIR(ctx.project,bundle.source_ref,dig,(ob_dec,prop_dec))
    groundings=tuple(FormulaGrounding(identity,field,0,SourceOrigin(bundle.source_ref,dig,text.index(expr),text.index(expr)+len(expr)))
                     for identity,field,expr in ((ob,'when',left),(prop,'holds',right)))
    expected=CoverageExpectation(frozenset({ob,prop}), frozenset({(ob,"when",0),(prop,"holds",0)}))
    return ir,bundle,ctx,groundings,expected


def test_entire_interpreted_contract_matches_pinned_source(pinned):
    ir,bundle,ctx,bindings,expected=instance(pinned)
    assert decode_ir(canonical_bytes(ir))==ir
    checked=verify_contract_semantics(ir,bundle,ctx,bindings,expectation=expected)
    assert checked.acceptable and checked.interpreted_fields==2 and checked.checked_fields==2
    assert checked.valuations_checked==32
    assert checked.deferred_properties==()


def test_deleting_one_formula_grounding_must_block_positive_verdict(pinned):
    ir,bundle,ctx,bindings,expected=instance(pinned)
    result=verify_contract_semantics(ir,bundle,ctx,bindings[:1],expectation=expected)
    assert result.status is OracleStatus.MISSING_BINDING and not result.acceptable
    result=verify_contract_semantics(ir,bundle,ctx,bindings+(bindings[0],),expectation=expected)
    assert result.status is OracleStatus.MISSING_BINDING and not result.acceptable


def test_swapping_field_provenance_fails_closed(pinned):
    ir,bundle,ctx,bindings,expected=instance(pinned)
    wrong=replace(bindings[0],origin=bindings[1].origin)
    result=verify_contract_semantics(ir,bundle,ctx,(wrong,bindings[1]),expectation=expected)
    assert result.status is OracleStatus.MISSING_BINDING and result.counterexample==wrong
    assert not result.acceptable


def test_ir_mutation_and_rehashed_digest_cannot_deceive_independent_oracle(pinned):
    ir,bundle,ctx,bindings,expected=instance(pinned)
    ob=ir.declarations[0]
    forged_fields=tuple(IRField('when',IRValue(IRType.V4,FormulaIR('yes'))) if f.name=='when' else f for f in ob.fields)
    forged=replace(ir,declarations=(replace(ob,fields=forged_fields),ir.declarations[1]))
    assert contract_digest(forged)!=contract_digest(ir)
    assert decode_ir(canonical_bytes(forged))==forged
    result=verify_contract_semantics(forged,bundle,ctx,bindings,expectation=expected)
    assert result.status is OracleStatus.COUNTEREXAMPLE and not result.acceptable


def test_incorrect_ir_span_or_altered_source_pin_blocks_equivalence(pinned):
    ir,bundle,ctx,bindings,expected=instance(pinned)
    off=replace(bindings[0],origin=replace(bindings[0].origin,byte_start=bindings[0].origin.byte_start+1))
    assert not verify_contract_semantics(ir,bundle,ctx,(off,bindings[1]),expectation=expected).acceptable
    foreign_ctx=replace(ctx,expected_sources=((bundle.source_ref,ContentDigest(DigestAlgorithm.SHA256,'0'*64)),))
    assert verify_contract_semantics(ir,bundle,foreign_ctx,bindings,expectation=expected).status is OracleStatus.UNTRUSTED_PIN


def test_zero_interpreted_fields_is_inconclusive_not_vacuous_pass(pinned):
    ir,bundle,ctx,bindings,expected=instance(pinned)
    from guardian.spec_lang.ir import IRValue
    prop=ir.declarations[1]
    deferred=replace(prop,fields=tuple(IRField('deferred_semantics',IRValue(IRType.DEFERRED,'future-solver'))
                     if f.name=='holds' else f for f in prop.fields))
    # A deferred property remains observable, never promoted to PROVEN.
    contract=replace(ir,declarations=(deferred,))
    report=verify_contract_semantics(contract,bundle,ctx,(),expectation=CoverageExpectation(frozenset({deferred.identity}),frozenset()))
    assert report.status is OracleStatus.INCONCLUSIVE_NO_INTERPRETED_FORMULAS
    assert report.deferred_properties==(deferred.identity,)


def test_hostile_source_depth_is_checked_before_python_recursion_limit(pinned):
    with pytest.raises(ValueError,match='GSL_V0_SOURCE_RESOURCE_LIMIT'):
        parse_source_formula((b'alpha and ' * 2000) + b'beta')
    with pytest.raises(ValueError,match='GSL_V0_MAX_DEPTH'):
        parse_source_formula(b'not ' * 80 + b'alpha')


def test_hostile_ir_depth_rejected_at_immutable_declaration_boundary(pinned):
    ir,bundle,ctx,bindings,expected=instance(pinned)
    root=FormulaIR('yes')
    for _ in range(75):
        root=FormulaIR('not',(root,))
    fields=tuple(IRField('when',IRValue(IRType.V4,root)) if f.name=='when' else f for f in ir.declarations[0].fields)
    with pytest.raises(ValueError,match='IR_FORMULA_RESOURCE_LIMIT'):
        replace(ir.declarations[0],fields=fields)


def test_ir_atom_with_unexpressible_name_cannot_bypass_typed_ir():
    for name in ('has-hyphen','not','', 'a.b','αβ'):
        with pytest.raises(ValueError,match='atom needs name'):
            FormulaIR('atom',name=name)


def test_duplicate_proof_ids_are_rejected_in_contract(pinned):
    ir,bundle,ctx,bindings,expected=instance(pinned)
    from guardian.spec_lang.contract import ProofObligation
    proof=ProofObligation('T05',ir.declarations[0].identity)
    with pytest.raises(ValueError,match='DUPLICATE_PROOF_OBLIGATION'):
        replace(ir,proofs=(proof,proof))


def test_external_inventory_catches_deleted_declaration_even_if_bindings_are_edited(pinned):
    ir,bundle,ctx,bindings,expected=instance(pinned)
    shortened=replace(ir,declarations=(ir.declarations[0],))
    result=verify_contract_semantics(shortened,bundle,ctx,bindings[:1],expectation=expected)
    assert result.status is OracleStatus.MISSING_BINDING and not result.acceptable


def test_without_independent_inventory_no_whole_contract_equivalence_can_be_claimed(pinned):
    ir,bundle,ctx,bindings,expected=instance(pinned)
    status=verify_contract_semantics(ir,bundle,ctx,bindings)
    assert status.status is OracleStatus.INCONCLUSIVE_EXPECTED_COVERAGE and not status.acceptable


def test_semantically_equal_interpreted_fields_do_not_auto_discharge_pending_proofs(pinned):
    ir,bundle,ctx,bindings,expected=instance(pinned)
    from guardian.spec_lang.contract import ProofObligation
    pending=ProofObligation('REFINEMENT-SUFFICIENCY-PENDING',ir.declarations[0].identity)
    with_proof=replace(ir,proofs=(pending,))
    checked=verify_contract_semantics(with_proof,bundle,ctx,bindings,expectation=expected)
    assert checked.status is OracleStatus.FINITE_EQUIVALENT
    assert checked.pending_proofs==(pending,) and not checked.acceptable


def test_deferred_semantics_cannot_masquerade_as_whole_contract_pass(pinned):
    ir,bundle,ctx,bindings,expected=instance(pinned)
    property_decl=ir.declarations[1]
    deferred=replace(property_decl,fields=tuple(
        IRField('deferred_semantics',IRValue(IRType.DEFERRED,'external-behavior-check'))
        if field.name=='holds' else field for field in property_decl.fields))
    partial=replace(ir,declarations=(ir.declarations[0],deferred))
    expected_partial=CoverageExpectation(expected.declarations,frozenset({(ir.declarations[0].identity,'when',0)}))
    result=verify_contract_semantics(partial,bundle,ctx,bindings[:1],expectation=expected_partial)
    assert result.status is OracleStatus.FINITE_EQUIVALENT
    assert result.deferred_properties==(deferred.identity,) and not result.acceptable


def test_shared_immutable_subterms_are_legal_but_cycles_are_not(pinned):
    ir,bundle,ctx,bindings,expected=instance(pinned)
    atom=FormulaIR('atom',name='reusable')
    shared=FormulaIR('and',(atom,atom))
    fields=tuple(IRField('when',IRValue(IRType.V4,shared)) if f.name=='when' else f for f in ir.declarations[0].fields)
    assert replace(ir.declarations[0],fields=fields)
    cycle=FormulaIR('not',(FormulaIR('yes'),))
    object.__setattr__(cycle,'args',(cycle,))
    with pytest.raises(ValueError,match='IR_FORMULA_CYCLE'):
        replace(ir.declarations[0],fields=tuple(
            IRField('when',IRValue(IRType.V4,cycle)) if f.name=='when' else f
            for f in ir.declarations[0].fields))


def test_seeded_96_source_formula_families_have_exhaustive_v4_equivalence(pinned):
    """The translation is checked against a separately interpreted source tree."""
    from random import Random
    rng=Random(20261021)
    old,context=pinned
    atoms=('alpha','beta','gamma')

    def formula(depth):
        if depth==0 or rng.randrange(5)==0:
            return rng.choice(atoms+('yes','no','unknown','conflict'))
        if rng.randrange(3)==0:
            return '(not '+formula(depth-1)+')'
        a=formula(depth-1)
        b=formula(depth-1)
        return '('+a+' '+rng.choice(('and','or'))+' '+b+')'

    for _ in range(96):
        raw=formula(4).encode('utf-8')
        digest=ContentDigest(DigestAlgorithm.SHA256,sha256(raw).hexdigest())
        bundle=SourceBundle(old.source_ref,raw,digest)
        pinned_context=replace(context,expected_sources=((bundle.source_ref,digest),))
        grounded=SourceOrigin(bundle.source_ref,digest,0,len(raw))
        candidate=lower_formula(parse_source_formula(raw))
        checked=verify_semantics(bundle,pinned_context,grounded,candidate,max_atoms=3,max_valuations=64)
        assert checked.status is OracleStatus.FINITE_EQUIVALENT, (raw,checked)
