"""C14 and GSL-T08/T10 through real source -> typechecker -> elaborator paths."""
from dataclasses import replace
from hashlib import sha256
import itertools
import json
import pytest

from foundation_b02 import project, cut, bundle_context
from guardian.domain.identity import ContentDigest, DigestAlgorithm, RevisionId
from guardian.spec_lang.contract import SourceBundle, ProofState
from guardian.spec_lang.syntax import analyze_source
from guardian.spec_lang.typecheck import typecheck_analyses
from guardian.spec_lang.elaboration import elaborate_program
from guardian.spec_lang.ir import IRType, IRValue, IRField, FormulaIR, canonical_bytes, contract_digest
from guardian.spec_lang.emission import emit_program, read_emission, verify_emission, EmissionBudget
from guardian.spec_lang.rebuild import SourceChange, rebuild_program, source_from_chunks


def digest(raw):
    return ContentDigest(DigestAlgorithm.SHA256, sha256(raw).hexdigest())


def canonical(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def typed(raw=None, fmt='gsl'):
    p = project(); source = cut(p)
    raw = raw if raw is not None else (
        'gsl "0.1"; project "project-alpha";\r\n'
        'scope "scope-main" { project: project("project-alpha"); }\r\n'
        'property "property-main" { kind: behavior; subject: project("project-alpha"); '
        'holds: not (alpha and beta) or unknown; }\r\n'
        'obligation "obligation-main" { from: source_item("source-main", "G00-01"); '
        'kind: behavior; scope: scope("scope-main"); when: yes; requires: property("property-main"); }\r\n'
    ).encode()
    bundle, context = bundle_context(p, source, raw)
    analysis = analyze_source(bundle, context, source_format=fmt)
    assert analysis.ok, analysis.diagnostics
    checked = typecheck_analyses((analysis,), context)
    assert checked.ok, checked.diagnostics
    return checked.value


def emitted():
    program = typed()
    result = emit_program(program)
    assert result.ok, result.diagnostics
    return program, result.value


def test_real_pipeline_emission_roundtrip_and_separate_digests():
    program, result = emitted()
    assert read_emission(result.wire_bytes, result.compilation_digest).ok
    checked = verify_emission(result.wire_bytes, program, result.compilation_digest)
    assert checked.ok and checked.value == result
    data = json.loads(result.wire_bytes)
    assert data['sources'][0]['utf8'].encode() == program.analyses[0].extraction.source.source_bytes
    assert result.compilation_digest != program.context.expected_sources[0][1]
    assert result.compilation_digest.hex != data['contracts'][0]['contract_digest']['hex']
    assert not result.normatively_admitted
    assert data['assurance']['source_item_coverage'] == 'NOT_RECONCILED'


def test_deferred_property_remains_pending_in_emitted_ir():
    raw = b'gsl "0.1"; project "project-alpha"; property "property-main" { kind: behavior; subject: project("project-alpha"); deferred_semantics: "mathematical claim"; }'
    p = project(); s = cut(p); b, c = bundle_context(p, s, raw)
    c = replace(c, supported_features=c.supported_features | {'deferred-property'})
    t = typecheck_analyses((analyze_source(b,c,source_format='gsl'),),c).value
    r = emit_program(t)
    assert r.ok, r.diagnostics
    data = json.loads(r.value.wire_bytes)
    ir = json.loads(data['contracts'][0]['canonical_ir'])
    assert ir['proofs'] and {x['state'] for x in ir['proofs']} == {'UNPROVEN'}


@pytest.mark.parametrize('attack', ['formula', 'map', 'source-item'])
def test_self_consistent_elaborated_object_cannot_replace_original_source(attack):
    p = typed(); out = elaborate_program(p).value
    if attack == 'formula':
        ir = out.contracts[0]; decls = list(ir.declarations); prop = decls[1]
        fields = tuple(replace(f, typed_value=IRValue(IRType.V4, FormulaIR('yes'))) if f.name=='holds' else f for f in prop.fields)
        decls[1] = replace(prop, fields=fields); ir = replace(ir, declarations=tuple(decls))
        # Preserve a valid map population for the malicious formula's smaller tree.
        maps = tuple(m for m in out.source_map if not (m.declaration==prop.identity and '.args[' in m.path))
        out = replace(out,contracts=(ir,),canonical_contracts=(canonical_bytes(ir),),contract_digests=(contract_digest(ir),),source_map=maps)
    elif attack == 'map':
        maps = list(out.source_map); item = next(i for i,m in enumerate(maps) if m.path=='$.fields[0]')
        maps[item] = replace(maps[item], origin=replace(maps[item].origin, byte_end=maps[item].origin.byte_end-1))
        out = replace(out, source_map=tuple(maps))
    else:
        out = replace(out, unchecked_source_items=())
    r = emit_program(p, out)
    assert not r.ok and r.diagnostics[0].code == 'GSL_EMISSION_SOURCE_IR_MISMATCH'


@pytest.mark.parametrize('field', ['normatively_admitted', 'materially_qualified', 'semantic_sufficiency', 'source_item_coverage'])
def test_bundle_does_not_promote_claims_even_with_recomputed_hash(field):
    _, bundle = emitted(); data = json.loads(bundle.wire_bytes)
    data['assurance'][field] = True
    raw = canonical(data)
    assert not read_emission(raw, digest(raw)).ok


@pytest.mark.parametrize('attack', ['source-bytes','source-missing','source-duplicate','contract-missing','map-missing','map-duplicate','items-missing','project','source-pin','schema','extra-key','noncanonical'])
def test_transport_cross_fields_fail_closed(attack):
    _, bundle = emitted(); data = json.loads(bundle.wire_bytes)
    if attack=='source-bytes': data['sources'][0]['utf8'] += '\n'
    if attack=='source-missing': data['sources'] = []
    if attack=='source-duplicate': data['sources'] *= 2
    if attack=='contract-missing': data['contracts'] = []
    if attack=='map-missing': data['source_map'].pop()
    if attack=='map-duplicate': data['source_map'].append(data['source_map'][0])
    if attack=='items-missing': data['unchecked_source_items'] = []
    if attack=='project': data['context']['project']['value'] = 'project-beta'
    if attack=='source-pin': data['context']['source_pins'] = []
    if attack=='schema': data['schema'] = 'unknown/v2'
    if attack=='extra-key': data['authority'] = 'ratified'
    raw = canonical(data) + (b' ' if attack=='noncanonical' else b'')
    assert not read_emission(raw, digest(raw)).ok


def test_external_pin_not_the_candidates_self_declared_hash():
    p, bundle = emitted(); raw = bundle.wire_bytes + b' '
    assert not read_emission(raw, bundle.compilation_digest).ok
    assert verify_emission(bundle.wire_bytes, p, bundle.compilation_digest).ok


def test_rehashed_formula_change_is_detected_by_rebuilding_source():
    p, bundle = emitted(); data = json.loads(bundle.wire_bytes)
    ir = json.loads(data['contracts'][0]['canonical_ir'])
    field = next(f for d in ir['declarations'] for f in d['fields'] if f['name']=='when')
    field['value']['value']['op'] = 'no'
    raw_ir = canonical(ir)
    data['contracts'][0]['canonical_ir'] = raw_ir.decode()
    data['contracts'][0]['contract_digest']['hex'] = sha256(raw_ir).hexdigest()
    raw = canonical(data)
    assert read_emission(raw, digest(raw)).ok  # transport, not semantic correspondence
    r = verify_emission(raw, p, digest(raw))
    assert not r.ok and r.diagnostics[0].code=='GSL_EMISSION_REBUILD_MISMATCH'


@pytest.mark.parametrize('kind,value', [('max_bytes', 1), ('max_nodes',1), ('max_depth',1)])
def test_emission_budget_never_returns_partial_bundle(kind,value):
    p = typed(); r = emit_program(p,budget=replace(EmissionBudget(),**{kind:value}))
    assert not r.ok and r.value is None


@pytest.mark.parametrize('ending', [b'\n', b'\r', b'\r\n'])
def test_chunks_split_unicode_and_crlf_preserve_full_pipeline(ending):
    p = typed(); old = p.analyses[0].extraction.source
    raw = '// áβ🙂'.encode() + ending + old.source_bytes
    source = replace(old.source_ref,revision=RevisionId('rev-'+'b'*32))
    b = SourceBundle(source, raw, digest(raw))
    context = replace(p.context, expected_sources=((source,b.expected_digest),))
    full = typecheck_analyses((analyze_source(b,context,source_format='gsl'),), context).value
    expected = emit_program(full).value
    for n in range(1, min(40,len(raw))):
        result = source_from_chunks(source, (raw[:n],raw[n:]), b.expected_digest)
        assert result.ok and result.value==b
        t = typecheck_analyses((analyze_source(result.value,context,source_format='gsl'),),context).value
        assert emit_program(t).value==expected


def replacement(program, raw):
    old = program.analyses[0].extraction.source
    ref = replace(old.source_ref,revision=RevisionId('rev-'+'c'*32))
    new = SourceBundle(ref,raw,digest(raw))
    context=replace(program.context,expected_sources=((ref,new.expected_digest),))
    return SourceChange(old.source_ref,old.expected_digest,new,'gsl'),context


@pytest.mark.parametrize('edit', [lambda b:b+b'\n// note', lambda b:b.replace(b'when: yes',b'when: no'), lambda b:b.replace(b'unknown',b'conflict')])
def test_update_is_explicit_full_rebuild_and_matches_direct_compilation(edit):
    p=typed(); change,context=replacement(p,edit(p.analyses[0].extraction.source.source_bytes))
    result=rebuild_program(p,(change,),context)
    assert result.ok, result.diagnostics
    full=typecheck_analyses((analyze_source(change.after,context,source_format='gsl'),),context).value
    assert result.value.output==elaborate_program(full).value
    assert emit_program(result.value.program).value==emit_program(full).value
    assert result.value.strategy=='FULL_REBUILD_NO_CACHE_REUSE'


@pytest.mark.parametrize('attack',['old-digest','missing-pin','duplicate-change','same-revision','bad-syntax'])
def test_invalid_update_never_returns_stale_ir(attack):
    p=typed(); old=p.analyses[0].extraction.source
    change,context=replacement(p,old.source_bytes+b'\n')
    changes=(change,)
    if attack=='old-digest':changes=(replace(change,before_digest=digest(b'not old')),)
    if attack=='missing-pin':context=p.context
    if attack=='duplicate-change':changes=(change,change)
    if attack=='same-revision':
        b=SourceBundle(old.source_ref,change.after.source_bytes,change.after.expected_digest)
        changes=(replace(change,after=b),);context=replace(context,expected_sources=((b.source_ref,b.expected_digest),))
    if attack=='bad-syntax':
        b=SourceBundle(change.after.source_ref,b'not valid gsl',digest(b'not valid gsl'))
        changes=(replace(change,after=b),);context=replace(context,expected_sources=((b.source_ref,b.expected_digest),))
    result=rebuild_program(p,changes,context)
    assert not result.ok and result.value is None


def test_noop_rebuild_and_tampered_previous_program():
    p=typed();r=rebuild_program(p,(),p.context)
    assert r.ok and r.value.output==elaborate_program(p).value
    decl=replace(p.declarations[0], fields=())
    wrong=replace(p,declarations=(decl,)+p.declarations[1:])
    assert not rebuild_program(wrong,(),p.context).ok


@pytest.mark.parametrize('chunks', [[b'a'],(bytearray(b'a'),),('text',)])
def test_chunk_input_does_not_execute_iterators_or_coerce(chunks):
    p=typed();old=p.analyses[0].extraction.source
    assert not source_from_chunks(old.source_ref,chunks,digest(b'a')).ok


def test_service_emits_from_original_bytes_without_a_handwritten_ir():
    from guardian.application.specification_service import elaborate_sources, emit_sources
    from guardian.spec_lang.contract import CompilationStage
    p = typed(); source = p.analyses[0].extraction.source
    compiled = emit_sources((source,), p.context)
    assert compiled.ok and compiled.value == emit_program(p).value
    assert elaborate_sources((source,), p.context).value == elaborate_program(p).value
    assert json.loads(compiled.value.wire_bytes)['stage'] == CompilationStage.EMIT.value


@pytest.mark.parametrize('attack', ['context', 'list', 'formats', 'format-count', 'source-count', 'source-bytes', 'emission-budget'])
def test_source_service_rejects_invalid_batches_without_partial_ir(attack):
    from guardian.application.specification_service import emit_sources
    from guardian.spec_lang.typecheck import TypecheckBudget
    p = typed(); args = {'sources': (p.analyses[0].extraction.source,), 'context': p.context}
    if attack == 'context': args['context'] = None
    if attack == 'list': args['sources'] = list(args['sources'])
    if attack == 'formats': args['formats'] = ('guess',)
    if attack == 'format-count': args['formats'] = ()
    if attack == 'source-count': args['sources'] = ()
    if attack == 'source-bytes': args['budget'] = replace(TypecheckBudget(), max_bytes=1)
    if attack == 'emission-budget': args['emission_budget'] = {'max_bytes': 999999}
    result = emit_sources(**args)
    assert not result.ok and result.value is None


def test_markdown_examples_are_preserved_but_never_normative():
    raw = (b'# Specification\r\n\r\n```gsl example\r\nnot valid GSL example\r\n```\r\n'
           b'```gsl normative\r\ngsl "0.1"; project "project-alpha";\r\n'
           b'scope "scope-main" { project: project("project-alpha"); }\r\n```\r\n')
    p = typed(raw=raw, fmt='markdown'); result = emit_program(p)
    assert result.ok, result.diagnostics
    data = json.loads(result.value.wire_bytes)
    assert data['sources'][0]['format'] == 'markdown'
    assert data['sources'][0]['utf8'].encode() == raw
    assert len(json.loads(data['contracts'][0]['canonical_ir'])['declarations']) == 1
    rebuilt = rebuild_program(p, (), p.context)
    assert rebuilt.ok and emit_program(rebuilt.value.program).value == result.value


def second_source(p):
    from foundation_b02 import entity
    from guardian.domain.identity import EntityKind
    raw = b'gsl "0.1"; project "project-alpha"; scope "scope-second" { project: project("project-alpha"); }'
    ref = entity(p.context.project, EntityKind.SOURCE, 'source-second', RevisionId('rev-'+'d'*32))
    return SourceBundle(ref, raw, digest(raw))


def test_source_addition_removal_and_input_order_match_full_compilation():
    p = typed(); other = second_source(p)
    context = replace(p.context, expected_sources=p.context.expected_sources+((other.source_ref,other.expected_digest),))
    updated = rebuild_program(p, (SourceChange(None,None,other,'gsl'),), context)
    assert updated.ok, updated.diagnostics
    original = p.analyses[0].extraction.source
    direct = typecheck_analyses(tuple(analyze_source(b,context,source_format='gsl') for b in (other,original)), context)
    assert direct.ok
    assert emit_program(updated.value.program).value == emit_program(direct.value).value
    recovered = rebuild_program(updated.value.program, (SourceChange(other.source_ref,other.expected_digest,None,None),), p.context)
    assert recovered.ok and emit_program(recovered.value.program).value == emit_program(p).value


def test_removed_referenced_source_cannot_leave_stale_linked_declarations():
    p = typed(); other = second_source(p)
    original = p.analyses[0].extraction.source
    raw = original.source_bytes.replace(b'scope("scope-main")', b'scope("scope-second")')
    change, _ = replacement(p, raw)
    context = replace(p.context, expected_sources=((change.after.source_ref,change.after.expected_digest),(other.source_ref,other.expected_digest)))
    initial = rebuild_program(p, (change,SourceChange(None,None,other,'gsl')), context)
    assert initial.ok, initial.diagnostics
    smaller = replace(context, expected_sources=context.expected_sources[:1])
    failed = rebuild_program(initial.value.program, (SourceChange(other.source_ref,other.expected_digest,None,None),), smaller)
    assert not failed.ok and failed.value is None
    assert any(d.code == 'GSL_REFERENCE_NOT_FOUND' for d in failed.diagnostics)


@pytest.mark.parametrize('change', ['compiler', 'features', 'symbols'])
def test_changed_context_cannot_validate_an_earlier_emission(change):
    from guardian.spec_lang.contract import SymbolBinding
    p, bundle = emitted()
    if change == 'compiler': context = replace(p.context, compiler=replace(p.context.compiler, implementation='another-build'))
    elif change == 'features': context = replace(p.context, supported_features=p.context.supported_features | {'deferred-property'})
    else:
        declaration = p.declarations[0]
        context = replace(p.context, symbols=(SymbolBinding('scope_alias',declaration.identity,declaration.origin.source),))
    fresh = typecheck_analyses(p.analyses, context)
    assert fresh.ok
    result = verify_emission(bundle.wire_bytes, fresh.value, bundle.compilation_digest)
    assert not result.ok and result.diagnostics[0].code == 'GSL_EMISSION_REBUILD_MISMATCH'


@pytest.mark.parametrize('attack', ['duplicate-key', 'nonfinite', 'float', 'integer-bool', 'wrong-stage', 'proof-promotion'])
def test_strict_bundle_transport_rejects_ambiguous_or_promoted_encodings(attack):
    _, bundle = emitted(); data = json.loads(bundle.wire_bytes)
    if attack == 'duplicate-key': raw = bundle.wire_bytes[:-1] + b',"schema":"guardian/gsl0/emission/v1"}'
    elif attack == 'nonfinite': raw = bundle.wire_bytes.replace(b'"diagnostics":[]', b'"diagnostics":[NaN]')
    elif attack == 'float': raw = bundle.wire_bytes.replace(b'"diagnostics":[]', b'"diagnostics":[1.0]')
    else:
        if attack == 'integer-bool': data['assurance']['normatively_admitted'] = 0
        if attack == 'wrong-stage': data['stage'] = 'C13_CONTRACT_DIFF'
        if attack == 'proof-promotion': data['assurance']['materially_qualified'] = True
        raw = canonical(data)
    assert not read_emission(raw,digest(raw)).ok


def test_valid_bundle_with_the_wrong_external_pin_is_rejected():
    _, bundle = emitted()
    result = read_emission(bundle.wire_bytes, digest(b'not the operator pin'))
    assert not result.ok and result.diagnostics[0].code == 'GSL_COMPILATION_DIGEST_MISMATCH'


def test_external_pin_is_checked_before_decoding_unverified_bundle(monkeypatch):
    import guardian.spec_lang.emission as emission
    _, bundle = emitted()
    def forbidden(*args, **kwargs):
        raise AssertionError('unverified candidate bytes were decoded')
    monkeypatch.setattr(emission.json, 'loads', forbidden)
    result = read_emission(bundle.wire_bytes, digest(b'wrong external pin'))
    assert not result.ok and result.diagnostics[0].code == 'GSL_COMPILATION_DIGEST_MISMATCH'
