"""C12: typed differences preserve removals, reference pins, order and proof state."""
from dataclasses import FrozenInstanceError, replace
import itertools
import json
import pytest
from guardian.domain.identity import ProjectId, EntityId, EntityRef, EntityKind as K, RevisionId, ContentDigest, DigestAlgorithm
from guardian.spec_lang.contract import ProofObligation, ProofState
from guardian.spec_lang.ir import (ContractIR, DeclarationIR, SourceOrigin, IRField, IRValue,
    IRType, FormulaIR, SourceItem, CommitmentKind, canonical_bytes, ir_to_data, decode_ir)
from guardian.spec_lang.contract_diff import (DiffBudget, DiffStatus, ChangeKind, ContractChange,
    ContractDiff, diff_contracts, diff_to_data)


def fixture(project='project-alpha'):
    p = ProjectId(project); revision = RevisionId('rev-'+'1'*32)
    def ref(kind, name): return EntityRef(p, kind, EntityId(p, kind, name), revision)
    source = ref(K.SOURCE, 'source-main'); digest = ContentDigest(DigestAlgorithm.SHA256, 'a'*64)
    origin = SourceOrigin(source, digest, 0, 100)
    scope = ref(K.SCOPE, 'scope-main'); prop = ref(K.PROPERTY, 'property-main'); ob = ref(K.OBLIGATION, 'obligation-main')
    def field(name, tag, value): return IRField(name, IRValue(tag, value))
    ds = (
        DeclarationIR(scope, origin, (field('project', IRType.REF, ref(K.PROJECT, project)),)),
        DeclarationIR(prop, origin, (field('kind', IRType.KIND, CommitmentKind.BEHAVIOR),
            field('subject', IRType.REF, ref(K.PROJECT, project)), field('holds', IRType.V4, FormulaIR('yes')))),
        DeclarationIR(ob, origin, (field('from', IRType.SOURCE_ITEM, SourceItem(source, 'G00-01-F01')),
            field('kind', IRType.KIND, CommitmentKind.BEHAVIOR), field('scope', IRType.REF, scope),
            field('when', IRType.V4, FormulaIR('atom', name='available')), field('requires', IRType.REF, prop))),
    )
    return ContractIR(p, source, digest, ds, (ProofObligation('interpret-property', prop, ProofState.UNPROVEN),))


def altered(ir, index, fields):
    declarations = list(ir.declarations)
    declarations[index] = replace(declarations[index], fields=tuple(fields))
    return replace(ir, declarations=tuple(declarations))


def compare(left, right, **limits):
    return diff_contracts(canonical_bytes(left), canonical_bytes(right), DiffBudget(**limits))


def kinds(result): return {c.kind for c in result.changes}


def test_identity_is_canonical_json_identity_not_normative_admission():
    ir=fixture();data=ir_to_data(ir)
    spaced=json.dumps(data,indent=3,ensure_ascii=True).encode()
    report=diff_contracts(canonical_bytes(ir),spaced)
    assert report.status is DiffStatus.COMPLETE and report.structurally_identical
    assert not report.requires_review and not report.normatively_admitted
    assert report.semantic_equivalence=='NOT_CHECKED'
    assert diff_to_data(report)['normatively_admitted'] is False


@pytest.mark.parametrize('remove', [0,1,2])
def test_each_declaration_removal_is_visible_even_when_remaining_rows_are_valid(remove):
    ir=fixture();remaining=tuple(d for i,d in enumerate(ir.declarations) if i!=remove)
    proofs=tuple(p for p in ir.proofs if p.origin in {d.identity for d in remaining})
    right=replace(ir,declarations=remaining,proofs=proofs)
    report=compare(ir,right)
    assert report.status is DiffStatus.COMPLETE and report.requires_review
    deletions=[c for c in report.changes if c.kind is ChangeKind.DECLARATION_REMOVED]
    assert len(deletions)==1 and json.loads(deletions[0].before)['identity']['entity']==ir.declarations[remove].identity.entity.value
    assert deletions[0].after is None
    reverse=compare(right,ir)
    assert ChangeKind.DECLARATION_ADDED in kinds(reverse) and reverse.requires_review


@pytest.mark.parametrize('field_index',range(5))
def test_every_obligation_field_value_is_compared(field_index):
    ir=fixture();fields=list(ir.declarations[2].fields);old=fields[field_index];v=old.typed_value
    if v.kind is IRType.REF:
        x=replace(v.value,revision=RevisionId('rev-'+'2'*32))
    elif v.kind is IRType.SOURCE_ITEM:x=replace(v.value,logical_item='G00-01-F02')
    elif v.kind is IRType.KIND:x=CommitmentKind.CONSTITUTION
    else:x=FormulaIR('no')
    fields[field_index]=replace(old,typed_value=IRValue(v.kind,x))
    report=compare(ir,altered(ir,2,fields))
    assert ChangeKind.FIELD_CHANGED in kinds(report) and report.requires_review
    change=next(c for c in report.changes if c.kind is ChangeKind.FIELD_CHANGED)
    assert old.name in change.path


def test_repeated_required_references_preserve_multiplicity_and_occurrence():
    ir=fixture();fs=ir.declarations[2].fields
    expanded=altered(ir,2,fs+(fs[-1],))
    report=compare(expanded,ir)
    assert ChangeKind.FIELD_REMOVED in kinds(report)
    assert any('requires#1' in c.path for c in report.changes)
    assert ChangeKind.FIELD_ORDER_CHANGED in kinds(report)


@pytest.mark.parametrize('permutation',list(itertools.permutations(range(3)))[1:])
def test_declaration_reordering_is_not_normalized_as_a_set(permutation):
    ir=fixture();changed=replace(ir,declarations=tuple(ir.declarations[i] for i in permutation))
    report=compare(ir,changed)
    assert kinds(report)=={ChangeKind.DECLARATION_ORDER_CHANGED}
    assert report.requires_review


def test_field_reordering_and_retained_declaration_order_survive_add_remove():
    ir=fixture();right=altered(ir,2,tuple(reversed(ir.declarations[2].fields)))
    assert ChangeKind.FIELD_ORDER_CHANGED in kinds(compare(ir,right))
    right=replace(ir,declarations=(ir.declarations[2],ir.declarations[1]))
    report=compare(ir,right)
    assert ChangeKind.DECLARATION_ORDER_CHANGED in kinds(report)
    assert ChangeKind.DECLARATION_REMOVED in kinds(report)


def test_revision_changes_are_pins_not_deletion_or_latest_selection():
    ir=fixture();d=ir.declarations[2]
    revised=replace(d,identity=replace(d.identity,revision=RevisionId('rev-'+'3'*32)))
    r=compare(ir,replace(ir,declarations=ir.declarations[:2]+(revised,)))
    assert kinds(r)=={ChangeKind.DECLARATION_REVISION_CHANGED}
    ambiguous=replace(ir,declarations=ir.declarations+(revised,))
    report=compare(ir,ambiguous)
    assert report.status is DiffStatus.INCOMPARABLE
    assert report.diagnostics[0].code=='AMBIGUOUS_DECLARATION_LINEAGE'


def test_provenance_only_change_is_visible_and_requires_review():
    ir=fixture();right=replace(ir,declarations=tuple(replace(d,origin=replace(d.origin,byte_start=1,byte_end=101)) for d in ir.declarations))
    r=compare(ir,right)
    assert kinds(r)=={ChangeKind.DECLARATION_ORIGIN_CHANGED}
    assert r.requires_review and r.semantic_equivalence=='NOT_CHECKED'
    digest=ContentDigest(DigestAlgorithm.SHA256,'b'*64)
    right=replace(ir,source_digest=digest,declarations=tuple(replace(d,origin=replace(d.origin,source_digest=digest)) for d in ir.declarations))
    assert ChangeKind.SOURCE_DIGEST_CHANGED in kinds(compare(ir,right))


@pytest.mark.parametrize('state',[ProofState.COUNTEREXAMPLE,ProofState.CHECKED_FINITE_DOMAIN])
def test_proof_state_change_is_recorded_not_accepted_as_a_proof(state):
    ir=fixture();right=replace(ir,proofs=(replace(ir.proofs[0],state=state),))
    report=compare(ir,right)
    assert ChangeKind.PROOF_CHANGED in kinds(report)
    assert not report.normatively_admitted and report.requires_review


def test_removing_proof_or_replacing_interpretation_with_deferred_is_not_hidden():
    ir=fixture();report=compare(ir,replace(ir,proofs=()))
    assert ChangeKind.PROOF_REMOVED in kinds(report)
    fields=ir.declarations[1].fields[:-1]+(IRField('deferred_semantics',IRValue(IRType.DEFERRED,'proof pending')),)
    deferred=altered(ir,1,fields)
    report=compare(ir,deferred)
    assert {ChangeKind.FIELD_REMOVED,ChangeKind.FIELD_ADDED}<=kinds(report)
    assert report.requires_review


@pytest.mark.parametrize('budget', [dict(max_nodes=1),dict(max_input_bytes=1),dict(max_depth=1),dict(max_changes=1),dict(max_output_bytes=1)])
def test_resource_exhaustion_never_becomes_no_difference(budget):
    ir=fixture();right=replace(ir,declarations=(ir.declarations[2],),proofs=())
    r=compare(ir,right,**budget)
    assert r.status is DiffStatus.RESOURCE_LIMITED and not r.structurally_identical
    assert r.requires_review and r.diagnostics


@pytest.mark.parametrize('field', ['max_nodes','max_input_bytes','max_depth','max_changes','max_output_bytes'])
@pytest.mark.parametrize('value', [True,0,-1,1.5,'100'])
def test_resource_policy_has_no_coercions(field,value):
    with pytest.raises((TypeError,ValueError)):DiffBudget(**{field:value})


@pytest.mark.parametrize('raw', [b'{"schema":1,"schema":2}',b'{"v":NaN}',b'{"v":Infinity}',b'{',b'\xff',None,bytearray(b'{}')])
def test_malformed_or_ambiguous_bytes_have_no_positive_verdict(raw):
    result=diff_contracts(raw,canonical_bytes(fixture()))
    assert result.status is DiffStatus.REJECTED and not result.structurally_identical
    assert result.requires_review


def test_two_projects_with_identical_names_are_incomparable():
    result=compare(fixture(),fixture('project-beta'))
    assert result.status is DiffStatus.INCOMPARABLE and result.diagnostics[0].code=='DIFFERENT_PROJECTS'


def test_result_transitive_immutability_and_complete_status_are_checked():
    ir=fixture();result=compare(ir,replace(ir,proofs=()))
    with pytest.raises(FrozenInstanceError):result.changes=()
    with pytest.raises(TypeError):replace(result,changes=list(result.changes))
    with pytest.raises(ValueError):replace(result,changes=())
    with pytest.raises(ValueError):replace(result,status=DiffStatus.RESOURCE_LIMITED)
    with pytest.raises(ValueError):ContractChange(ChangeKind.FIELD_CHANGED,'$.x',b'1',b'1')


def test_exact_node_budget_and_determinism_do_not_depend_on_json_key_order():
    ir=fixture();right=replace(ir,proofs=());reference=compare(ir,right)
    exact=compare(ir,right,max_nodes=reference.visited_nodes)
    assert exact==reference
    assert compare(ir,right,max_nodes=reference.visited_nodes-1).status is DiffStatus.RESOURCE_LIMITED
    raw=json.dumps(ir_to_data(right),sort_keys=False,indent=2).encode()
    assert diff_contracts(canonical_bytes(ir),raw)==reference
    assert json.loads(json.dumps(diff_to_data(reference)))==diff_to_data(reference)


def test_field_same_text_in_another_kind_is_not_matched_as_same_declaration():
    ir=fixture();scope=ir.declarations[0];prop=ir.declarations[1]
    other=replace(scope,identity=replace(scope.identity,entity=EntityId(ir.project,K.SCOPE,prop.identity.entity.value)))
    right=replace(ir,declarations=(scope,other,ir.declarations[2]),proofs=())
    r=compare(ir,right)
    assert {ChangeKind.DECLARATION_ADDED,ChangeKind.DECLARATION_REMOVED}<=kinds(r)


def test_pure_diff_does_not_call_files_clock_or_network(monkeypatch):
    import builtins,time,socket,os
    before=canonical_bytes(fixture());after=canonical_bytes(replace(fixture(),proofs=()))
    def fail(*args,**kwargs):raise AssertionError('unexpected IO')
    monkeypatch.setattr(builtins,'open',fail);monkeypatch.setattr(time,'time',fail)
    monkeypatch.setattr(socket,'socket',fail);monkeypatch.setattr(os,'getenv',fail)
    assert diff_contracts(before,after).status is DiffStatus.COMPLETE


def test_source_revision_is_reported_separately_from_each_declaration_origin():
    ir=fixture();source=replace(ir.source,revision=RevisionId('rev-'+'4'*32))
    ds=tuple(replace(d,origin=replace(d.origin,source=source),fields=tuple(
        replace(f,typed_value=IRValue(IRType.SOURCE_ITEM,replace(f.typed_value.value,source=source)))
        if f.typed_value.kind is IRType.SOURCE_ITEM else f for f in d.fields)) for d in ir.declarations)
    right=replace(ir,source=source,declarations=ds)
    report=compare(ir,right)
    assert report.status is DiffStatus.COMPLETE
    assert ChangeKind.SOURCE_PIN_CHANGED in kinds(report)
    assert len([c for c in report.changes if c.kind is ChangeKind.DECLARATION_ORIGIN_CHANGED])==3
    assert report.requires_review


def test_proof_addition_and_reordering_preserve_identity_origin_and_state():
    ir=fixture();second=ProofObligation('prove-refinement',ir.declarations[2].identity,ProofState.UNPROVEN)
    expanded=replace(ir,proofs=ir.proofs+(second,))
    addition=compare(ir,expanded)
    assert ChangeKind.PROOF_ADDED in kinds(addition)
    payload=json.loads(next(c.after for c in addition.changes if c.kind is ChangeKind.PROOF_ADDED))
    assert payload['state']=='UNPROVEN' and payload['identifier']=='prove-refinement'
    reordered=compare(expanded,replace(expanded,proofs=tuple(reversed(expanded.proofs))))
    assert kinds(reordered)=={ChangeKind.PROOF_ORDER_CHANGED}
    assert reordered.requires_review and not reordered.normatively_admitted


def test_partial_changes_survive_exhaustion_but_never_indicate_complete_comparison():
    ir=fixture();right=replace(ir,declarations=(ir.declarations[2],),proofs=())
    report=compare(ir,right,max_changes=1)
    assert report.status is DiffStatus.RESOURCE_LIMITED and len(report.changes)==1
    wire=diff_to_data(report)
    assert wire['status']=='RESOURCE_LIMITED' and wire['requires_review']
    assert not wire['structurally_identical'] and not wire['normatively_admitted']


def test_structurally_distinct_but_logically_equivalent_formulas_still_require_review():
    ir=fixture();fields=list(ir.declarations[1].fields)
    fields[-1]=replace(fields[-1],typed_value=IRValue(IRType.V4,FormulaIR('not',(FormulaIR('no'),))))
    report=compare(ir,altered(ir,1,fields))
    assert kinds(report)=={ChangeKind.FIELD_CHANGED}
    assert report.semantic_equivalence=='NOT_CHECKED' and report.requires_review
