"""Full-source positives plus false-PASS attacks for Q06..Q15 / R2..R4/R6."""
from dataclasses import replace
from hashlib import sha256
import pytest

from foundation_b02 import project, cut, bundle_context, entity
from test_audit_contract_gaps import make_two_obligations
from guardian.domain.identity import EntityKind, ContentDigest, DigestAlgorithm
from guardian.spec_lang.contract import CompilationResult, CompilationStage, CompileStatus, SourceBundle
from guardian.spec_lang.ir import SourceOrigin, FormulaIR, IRField, IRType, IRValue, CommitmentKind
from guardian.spec_lang.syntax import analyze_source
from guardian.spec_lang.text import NormativeUnit, TextSpan
from guardian.spec_lang.source_inventory import CheckStatus, source_inventory, independent_tokens
from guardian.spec_lang.v0 import (verify_semantics,verify_contract_semantics,OracleStatus,
    parse_source_formula,lower_formula,ContractSemanticResult)

FULL = b'''gsl "0.1"; project "project-alpha";
obligation "obl-one" { when: yes; from: source_item("source-main", "obl-one"); kind: constitution; scope: scope("scope-main"); }
obligation "obl-two" { when: no; from: source_item("source-main", "obl-two"); kind: constitution; scope: scope("scope-main"); }
'''


def test_full_source_correspondence_positive_keeps_unchecked_guarantees_visible():
    ir,b,c,g,e = make_two_obligations(FULL)
    r = verify_contract_semantics(ir,b,c,g,expectation=e)
    assert r.acceptable and r.formula_equivalent
    assert r.correspondence.declarations is CheckStatus.CHECKED
    assert r.correspondence.fields is CheckStatus.CHECKED
    assert r.correspondence.reference_integrity is CheckStatus.NOT_CHECKED
    assert r.correspondence.historical_coverage is CheckStatus.NOT_CHECKED
    assert r.correspondence.normative_admission is CheckStatus.NOT_CHECKED
    assert not r.full_contract_equivalent


@pytest.mark.parametrize('field,value', [
    ('kind', IRValue(IRType.KIND, CommitmentKind.BEHAVIOR)),
    ('scope', None),
])
def test_changing_non_v4_normative_fields_cannot_pass_as_source_correspondence(field,value):
    ir,b,c,g,e = make_two_obligations(FULL)
    if value is None:
        value = IRValue(IRType.REF,entity(ir.project,EntityKind.SCOPE,'wrong-scope'))
    d = ir.declarations[0]
    changed = replace(ir,declarations=(replace(d,fields=tuple(IRField(field,value) if f.name==field else f for f in d.fields)),ir.declarations[1]))
    from guardian.spec_lang.ir import canonical_bytes, decode_ir
    changed = decode_ir(canonical_bytes(changed))
    r = verify_contract_semantics(changed,b,c,g,expectation=e)
    assert r.formula_equivalent and not r.acceptable
    assert r.correspondence.fields is CheckStatus.MISMATCH


def test_a_candidate_cannot_reduce_both_its_ids_and_its_claimed_expectation():
    ir,b,c,g,e = make_two_obligations(FULL)
    d = ir.declarations[0]
    shortened = replace(ir,declarations=(d,))
    diminished = replace(e,declarations=frozenset({d.identity}),interpreted_fields=frozenset({(d.identity,'when',0)}))
    r = verify_contract_semantics(shortened,b,c,g[:1],expectation=diminished)
    assert not r.acceptable
    assert r.correspondence.declarations is CheckStatus.MISMATCH


def test_swap_only_v4_value_span_and_declaration_origin_is_detected_independently():
    ir,b,c,g,e = make_two_obligations(FULL)
    first,second = ir.declarations
    fields = tuple(IRField('when',IRValue(IRType.V4,FormulaIR('no'))) if f.name=='when' else f for f in first.fields)
    forged = replace(ir,declarations=(replace(first,origin=second.origin,fields=fields),second))
    swapped = (replace(g[0],origin=g[1].origin),g[1])
    r = verify_contract_semantics(forged,b,c,swapped,expectation=e)
    assert r.status is OracleStatus.MISSING_BINDING
    assert r.correspondence.reason == 'SOURCE_DECLARATION_ID_ORIGIN_MISMATCH'


@pytest.mark.parametrize('word,op', [('true','yes'),('false','no'),('yes','yes'),('no','no'),('unknown','unknown'),('conflict','conflict')])
@pytest.mark.parametrize('comment', ['', '/* } when: no; é */', '// comment\r', '// comment\n', '// comment\r\n'])
def test_frontend_and_v0_share_literal_and_comment_semantics(word,op,comment):
    p=project(); s=cut(p)
    expression=f'({word} {comment} and yes)'
    raw=('gsl "0.1"; project "project-alpha"; obligation "obl-main" { when: '+expression+'; }').encode()
    b,c=bundle_context(p,s,raw)
    parsed=analyze_source(b,c,source_format='gsl')
    assert parsed.ok
    expr=parsed.units[0].ast.declarations[0].fields[0].expr
    r=verify_semantics(b,c,SourceOrigin(b.source_ref,b.expected_digest,expr.span.start,expr.span.end),
                       FormulaIR('and',(FormulaIR(op),FormulaIR('yes'))))
    assert r.acceptable and r.valuations_checked==1


def test_whitespace_and_comment_tokens_do_not_change_independent_declaration_population():
    p=project();s=cut(p)
    raw=b'/* obligation "forged" { when: no; } */\n'+FULL
    b,c=bundle_context(p,s,raw)
    assert [(d.kind,d.name) for d in source_inventory(b)] == [('obligation','obl-one'),('obligation','obl-two')]


def test_explicit_markdown_normative_fences_exclude_examples_independently():
    p=project();s=cut(p)
    raw=(b'```gsl\n'+FULL+b'```\n\n<!--\n```gsl normative\n'+FULL+b'```\n-->\n'
         +b'~~~gsl normative version=0.1\n'+FULL+b'~~~\n')
    b,c=bundle_context(p,s,raw)
    inventory=source_inventory(b,source_format='markdown')
    parsed=analyze_source(b,c,source_format='markdown')
    assert parsed.ok and len(inventory)==2
    assert [(d.start,d.end) for d in inventory]==[(d.span.start,d.span.end) for d in parsed.units[0].ast.declarations]
    with pytest.raises(ValueError):source_inventory(b,source_format='gsl')


def test_aggregate_oracle_budget_cannot_be_spent_once_per_field():
    ir,b,c,g,e=make_two_obligations(FULL)
    r=verify_contract_semantics(ir,b,c,g,expectation=e,max_total_valuations=1)
    assert r.status is OracleStatus.INCONCLUSIVE_RESOURCE_LIMIT
    assert r.checked_fields==1 and r.valuations_checked==1 and not r.acceptable
    assert verify_contract_semantics(ir,b,c,g,expectation=e,max_total_valuations=2).acceptable


@pytest.mark.parametrize('factory',[lambda b:[b.source_ref,b.expected_digest],lambda b:{'source':b.source_ref,'digest':b.expected_digest},lambda b:(b.source_ref,)])
def test_mutable_or_malformed_source_pin_pairs_are_rejected(factory):
    p=project();s=cut(p);b,c=bundle_context(p,s,FULL)
    with pytest.raises((TypeError,ValueError)):replace(c,expected_sources=(factory(b),))
    assert c.expected_sources==((b.source_ref,b.expected_digest),)


@pytest.mark.parametrize('bad',[True,42,{},[],b'digest','digest'])
def test_compilation_result_nominal_digest_boundary(bad):
    with pytest.raises(TypeError):
        CompilationResult(CompileStatus.COMPILED,CompilationStage.EMIT,(),bad)


def test_compiled_result_and_partial_result_cannot_exchange_guarantees():
    digest=ContentDigest(DigestAlgorithm.SHA256,'f'*64)
    with pytest.raises(ValueError):CompilationResult(CompileStatus.ANALYZED,CompilationStage.ABSTRACT,(),digest)
    with pytest.raises(ValueError):CompilationResult(CompileStatus.COMPILED,CompilationStage.TYPECHECK,(),digest)
    with pytest.raises(ValueError):ContractSemanticResult(OracleStatus.FINITE_EQUIVALENT,2,1,1)


def test_ast_or_cst_composite_reconstruction_cannot_relabel_a_literal():
    p=project();s=cut(p);b,c=bundle_context(p,s,FULL)
    r=analyze_source(b,c,source_format='gsl');unit=r.units[0]
    decl=unit.ast.declarations[0];f=decl.fields[0]
    forged=replace(decl,fields=(replace(f,expr=replace(f.expr,value='no')),)+decl.fields[1:])
    ast=replace(unit.ast,declarations=(forged,)+unit.ast.declarations[1:])
    with pytest.raises(ValueError,match='SYNTAX_MISMATCH'):replace(unit,ast=ast)


@pytest.mark.parametrize('raw',[b'yes /* unclosed',b'yes @ no',b'yes && no',b'"yes"'])
def test_v0_never_silently_reinterprets_unsupported_expression_syntax(raw):
    with pytest.raises((ValueError,UnicodeError)):parse_source_formula(raw)


@pytest.mark.parametrize('budget',[None,True,-1,0,'10'])
def test_invalid_aggregate_or_scalar_budgets_are_inconclusive_not_python_errors(budget):
    ir,b,c,g,e=make_two_obligations(FULL)
    for keyword in ('max_valuations','max_total_valuations'):
        r=verify_contract_semantics(ir,b,c,g,expectation=e,**{keyword:budget})
        assert r.status is OracleStatus.INCONCLUSIVE_RESOURCE_LIMIT and not r.acceptable
