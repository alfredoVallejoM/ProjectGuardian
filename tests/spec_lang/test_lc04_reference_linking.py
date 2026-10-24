"""Pinned LC03→LC04 bindings, with actual B03 imported record bodies."""
from dataclasses import replace
import pytest
from foundation_b02 import project, cut, bundle_context, entity
from foundation_b03 import scenario
from guardian.domain.identity import EntityKind as K, RevisionId
from guardian.domain.references import EntityImport, TrustedEntityImports
from guardian.domain.source import ApprovedSourceImport
from guardian.spec_lang.contract import SymbolBinding
from guardian.spec_lang.syntax import analyze_source
from guardian.spec_lang.resolution import resolve_analyses, ResolutionStatus

RAW = b'''gsl "0.1"; project "project-alpha";
obligation "obligation-main" { from: source_item("source-main","obligation-main");
 kind: behavior; scope: scope("scope-main"); when: true; requires: property("property-main");
 verification: verification_ref("verification-main"); }
verification "verification-main" { from: source_item("source-main","verification-main");
 target: obligation("obligation-main"); property: property("property-main"); method: property_and_negative; }
property "property-main" { kind: behavior; subject: project("project-alpha"); deferred_semantics: "not proved"; }
scope "scope-main" { project: project("project-alpha"); }
source "source-main" { locator: "spec/main.gsl"; source_cut: context; }
'''


def parse(raw=RAW, context_change=None):
    p=project();s=cut(p);b,c=bundle_context(p,s,raw)
    if context_change is not None:c=context_change(c,b)
    a=analyze_source(b,c,source_format='gsl')
    assert a.ok, a.diagnostics
    return a,c


def test_two_pass_forward_references_cycles_sources_and_project_share_nominal_ids():
    a,c=parse();result=resolve_analyses((a,),c)
    assert result.ok, result.diagnostics
    assert len(result.declarations)==5
    assert [(r.declaration.kind, r.field) for r in result.references] == [
        (K.OBLIGATION, 'from'), (K.OBLIGATION, 'scope'), (K.OBLIGATION, 'requires'),
        (K.OBLIGATION, 'verification'), (K.VERIFICATION, 'from'),
        (K.VERIFICATION, 'target'), (K.VERIFICATION, 'property'),
        (K.PROPERTY, 'subject'), (K.SCOPE, 'project'), (K.SOURCE, 'source_cut')]
    assert not result.compiled and not result.typechecked
    ob=next(d.identity for d in result.declarations if d.identity.kind is K.OBLIGATION)
    back=[r for r in result.references if r.field=='target'][0]
    assert back.target==ob
    assert result.unchecked_source_items  # source catalog item coverage is LC09, not invented.


@pytest.mark.parametrize('old,new,code', [
    ('property("property-main")','property("missing-property")','GSL_REFERENCE_NOT_FOUND'),
    ('scope("scope-main")','property("property-main")','GSL_REFERENCE_KIND_MISMATCH'),
    ('project("project-alpha")','project("project-beta")','GSL_FOREIGN_PROJECT'),
    ('source_item("source-main"','source_item("missing-source"','GSL_SOURCE_NOT_PINNED'),
    ('property("property-main")','property("property-main", "main")','GSL_REFERENCE_ARITY'),
    ('property("property-main")','property("property-main", "rev-'+ 'c'*32 +'")','GSL_REFERENCE_ARITY'),
])
def test_reference_falsations(old,new,code):
    a,c=parse(RAW.decode().replace(old,new).encode());r=resolve_analyses((a,),c)
    assert not r.ok and code in {d.code for d in r.diagnostics}


def test_duplicate_declarations_or_source_inputs_never_first_result_win():
    a,c=parse(RAW+b'\nproperty "property-main" { kind: behavior; subject: project("project-alpha"); holds: true; }')
    assert 'GSL_DUPLICATE_DECLARATION' in {d.code for d in resolve_analyses((a,),c).diagnostics}
    a,c=parse()
    assert 'GSL_DUPLICATE_SOURCE_INPUT' in {d.code for d in resolve_analyses((a,a),c).diagnostics}


def test_unpinned_source_and_budget_do_not_yield_resolved():
    a,c=parse()
    assert not resolve_analyses((a,),replace(c,expected_sources=((c.expected_sources[0][0],replace(c.expected_sources[0][1],hex='0'*64)),))).ok
    assert resolve_analyses((a,),c,max_nodes=1).diagnostics[-1].code=='GSL_RESOLUTION_RESOURCE_LIMIT'


def test_explicit_import_uses_real_record_and_exact_domain_grant():
    local, foreign=scenario(),scenario('project-beta')
    target=foreign[4]['property-shared']
    raw=('gsl "0.1"; project "project-alpha"; obligation "obligation-main" { requires: property("foreign_property"); }').encode()
    a,c=parse(raw)
    approval=entity(local[0].project_id,K.DECISION,'approve-import')
    s=foreign[1]
    grant=ApprovedSourceImport(local[0].project_id,s.ref,s.repository,s.path,approval,s)
    imports=TrustedEntityImports((EntityImport(grant,frozenset({target}),foreign[3]),))
    symbols=(SymbolBinding('foreign_property',target,s.ref),)
    rejected=resolve_analyses((a,),c,snapshot=local[3],external_symbols=symbols)
    assert rejected.diagnostics[0].code=='FORBIDDEN_CROSS_PROJECT_REF'
    ok=resolve_analyses((a,),c,snapshot=local[3],imports=imports,external_symbols=symbols)
    assert ok.ok,ok.diagnostics
    assert ok.references[0].target==target and ok.references[0].basis=='IMPORTED_RECORD'


def test_context_binding_does_not_establish_entity_existence_without_body():
    def change(c,b):
        target=entity(c.project,K.PROPERTY,'property-absent')
        return replace(c,symbols=(SymbolBinding('external_property',target,b.source_ref),))
    raw=b'gsl "0.1"; project "project-alpha"; obligation "obligation-main" { requires: property("external_property"); }'
    a,c=parse(raw,change)
    assert not resolve_analyses((a,),c).ok
    assert resolve_analyses((a,),c,snapshot=scenario()[3]).diagnostics[0].code=='ORPHAN_REFERENCE'


def test_all_reference_positions_are_preserved_and_deterministic():
    a,c=parse();first=resolve_analyses((a,),c)
    assert first==resolve_analyses((a,),c)
    raw=a.extraction.source.source_bytes
    for use in first.references:
        fragment=raw[use.span.start:use.span.end].decode()
        assert fragment=='context' or '(' in fragment
