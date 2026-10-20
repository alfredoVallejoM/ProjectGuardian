import sys
from pathlib import Path
from dataclasses import replace
sys.path.insert(0, str(Path(__file__).parents[1]))
from compiler import CompileContext, SourceRecord, compile_strict, parse, canonical_bytes

ROOT=Path(__file__).parents[1]
SRC=(ROOT/'example.gsl').read_text(encoding='utf-8')
CTX=CompileContext('ProjectGuardian', 'cut-001', {'PG-G00':SourceRecord('architecture/campaigns.json',frozenset({'G00-01','G00-01-T01','G00-01-F01'}))})

def result(s=SRC,ctx=CTX):return compile_strict(s,ctx)

def codes(s):return {d.code for d in result(s).diagnostics}

def test_valid_document_has_strict_ir_and_no_certificate():
    r=result();assert r.status=='COMPILED',r.diagnostics
    assert len(r.ir['declarations'])==6
    assert r.manifest['status']=='PROPOSED_NOT_RATIFIED'
    assert 'certification' not in r.ir

def test_provenance_span_utf8_bytes():
    s=SRC.replace('"PG-ID-DISTINCT"','"É-ID-DISTINCT"').replace('"PG-ID-DISTINCT");','"É-ID-DISTINCT");')
    r=result(s);assert r.status=='COMPILED',r.diagnostics
    span=r.source_map['property:É-ID-DISTINCT']; fragment=s.encode('utf8')[span['byte_start']:span['byte_end']].decode('utf8')
    assert fragment.startswith('property "É-ID-DISTINCT"')

def test_comment_and_format_do_not_change_ir():
    s=SRC.replace('gsl "0.1";', '// non-normative comment\ngsl "0.1";')
    assert result(s).manifest['contract_digest']==result().manifest['contract_digest']
    assert result(s).manifest['source_digest']!=result().manifest['source_digest']

def test_unknown_field_is_rejected():
    assert 'GSL-FIELD-UNKNOWN' in codes(SRC.replace('    when: true;', '    granted: true;\n    when: true;'))

def test_duplicate_identifier_is_rejected():
    extra='\nproperty "PG-ID-DISTINCT" { kind: constitution; subject: project("ProjectGuardian"); holds: true; }'
    assert 'GSL-ID-DUPLICATE' in codes(SRC+extra)

def test_missing_source_item_is_rejected():
    assert 'GSL-SOURCE-ITEM-MISSING' in codes(SRC.replace('"G00-01-T01");','"NOT-PRESENT");'))

def test_wrong_reference_type_is_rejected():
    assert 'GSL-TYPE' in codes(SRC.replace('scope: scope("G00-FOUNDATION")','scope: verification_ref("G00-01-T01")'))

def test_unresolved_reference_is_rejected():
    assert 'GSL-REF-MISSING' in codes(SRC.replace('property("PG-ID-DISTINCT")','property("ABSENT")'))

def test_ambiguous_field_rejected():
    assert 'GSL-FIELD-DUPLICATE' in codes(SRC.replace('    when: true;', '    when: true;\n    when: false;'))

def test_unknown_predicate_not_accepted():
    assert 'GSL-PRED-UNSUPPORTED' in codes(SRC.replace('nominal_distinct(', 'invented_semantics('))

def test_wrong_predicate_argument_types_are_rejected():
    assert 'GSL-PRED-TYPE' in codes(SRC.replace('kind("ProjectId")','project("ProjectGuardian")'))

def test_version_incompatibility_is_rejected():
    assert 'GSL-VERSION' in codes(SRC.replace('gsl "0.1";', 'gsl "1.0";'))

def test_foreign_project_rejected():
    assert 'GSL-FOREIGN-PROJECT' in codes(SRC.replace('project("ProjectGuardian");\n    campaign','project("External");\n    campaign'))

def test_changed_normative_property_changes_contract_digest():
    changed=SRC.replace('    when: true;', '    when: false;')
    assert result(changed).manifest['contract_digest']!=result().manifest['contract_digest']

def test_broken_syntax_is_rejected():
    assert 'GSL-PARSE' in codes(SRC.replace('when: true;', 'when true;'))

def test_unclosed_string_is_rejected():
    assert 'GSL-PARSE' in codes(SRC.replace('"G00-01" {','"G00-01 {'))

def test_deferred_property_allowed_but_not_proven():
    old='holds: nominal_distinct(kind("ProjectId"), kind("RevisionId"));'
    s=SRC.replace(old,'deferred_semantics: "future/program-observations";')
    r=result(s);assert r.status=='COMPILED',r.diagnostics
    assert r.manifest['status']=='PROPOSED_NOT_RATIFIED'
    assert any(v['name']=='deferred_semantics' for d in r.ir['declarations'] if d['node_type']=='property' for v in d['fields'])

def test_cannot_introduce_unregistered_project_source():
    assert 'GSL-SOURCE-UNKNOWN' in codes(SRC.replace('source "PG-G00"','source "UNKNOWN"'))

def test_disallow_spontaneous_project_authority():
    foreign=replace(CTX,project='External')
    assert compile_strict(SRC,foreign).status=='REJECTED'

def test_determinism():
    a=result();b=result();assert canonical_bytes(a.ir)==canonical_bytes(b.ir)
    assert a.manifest==b.manifest

def historical_context():
    import json
    catalog=json.loads((ROOT/'g00_01_source_catalog_candidate.json').read_text(encoding='utf-8'))
    return CompileContext('ProjectGuardian','guardian-pinned-cut',{
        k:SourceRecord(v['locator'],frozenset(v['logical_items'])) for k,v in catalog.items()
    },{k:frozenset(v['logical_items']) for k,v in catalog.items()}, frozenset(f"G00-01-F{i:02}-DETAIL" for i in range(1,11)))


def test_full_g00_01_inventory_compiles_without_claiming_sufficiency():
    fixture=(ROOT/'g00_01_candidate.gsl').read_text(encoding='utf-8')
    outcome=compile_strict(fixture,historical_context())
    assert outcome.status=='COMPILED',outcome.diagnostics
    assert len(outcome.ir['declarations'])==35
    assert len([p for p in outcome.proof_obligations if p['kind']=='PROPERTY_INTERPRETATION_PENDING'])==10
    assert len([p for p in outcome.proof_obligations if p['kind']=='REFINEMENT_SUFFICIENCY_PENDING'])==10
    assert all(p['status']=='UNPROVEN' for p in outcome.proof_obligations)


def test_omitting_historical_clause_is_detected_from_independent_catalog():
    src=(ROOT/'g00_01_candidate.gsl').read_text(encoding='utf-8')
    src='\n'.join(x for x in src.splitlines() if not x.startswith('property "G00-01-F07-P"'))
    assert 'GSL-COVERAGE-MISSING' in {d.code for d in compile_strict(src,historical_context()).diagnostics}


def test_missing_historical_verification_is_detected():
    src=(ROOT/'g00_01_candidate.gsl').read_text(encoding='utf-8')
    src='\n'.join(x for x in src.splitlines() if not x.startswith('verification "G00-01-T04"'))
    assert 'GSL-COVERAGE-MISSING' in {d.code for d in compile_strict(src,historical_context()).diagnostics}


def test_foreign_subject_is_rejected_even_if_project_scope_is_correct():
    assert 'GSL-FOREIGN-PROJECT' in codes(SRC.replace('subject: project("ProjectGuardian")','subject: project("Untrusted")'))


def test_deleting_relation_to_parent_is_not_silently_accepted():
    src=(ROOT/'g00_01_candidate.gsl').read_text(encoding='utf-8')
    src='\n'.join(x for x in src.splitlines() if not x.startswith('relation "G00-01-F08-DETAIL"'))
    outcome=compile_strict(src,historical_context())
    assert 'GSL-RELATION-COVERAGE-MISSING' in {d.code for d in outcome.diagnostics}


def test_ir_contains_typed_references_not_raw_function_names():
    outcome=result();assert outcome.status=='COMPILED',outcome.diagnostics
    obligation=next(d for d in outcome.ir['declarations'] if d['node_type']=='obligation')
    scope=next(f['value'] for f in obligation['fields'] if f['name']=='scope')
    assert scope=={'op':'resolved_ref','project':'ProjectGuardian','kind':'scope','id':'G00-FOUNDATION'}


def test_unknown_verification_method_fails_closed():
    assert 'GSL-METHOD-UNKNOWN' in codes(SRC.replace('method: property_and_negative;', 'method: imaginary_check;'))


def test_unknown_relation_signature_fails_closed():
    assert 'GSL-RELATION-UNKNOWN' in codes(SRC.replace('kind: proposed_detail;', 'kind: magical_refinement_proven;'))
