"""Adversarial review of the authored slice, separate from happy-path fixtures."""
from dataclasses import replace
import pytest
from foundation_b03 import scenario
from foundation_b02 import project, cut, bundle_context, entity
from guardian.domain.identity import EntityKind as K
from guardian.domain.references import validate_references
from guardian.spec_lang.contract import SymbolBinding
from guardian.spec_lang.syntax import analyze_source
from guardian.spec_lang.resolution import resolve_analyses, LinkedReference, ResolutionReport


def analyze(raw, p=None, source=None, transform=None):
    p=p or project();source=source or cut(p)
    b,c=bundle_context(p,source,raw)
    if transform:c=transform(c,b)
    a=analyze_source(b,c,source_format='gsl');assert a.ok
    return a,c


def test_named_binding_must_match_record_source_provenance():
    p,s,records,snapshot,ids=scenario()
    other=cut(p,name='other-source',path='other.gsl')
    raw=b'gsl "0.1"; project "project-alpha"; obligation "obligation-main" { requires: property("named_property"); }'
    a,c=analyze(raw,p,other,lambda c,b:replace(c,symbols=(SymbolBinding('named_property',ids['property-shared'],b.source_ref),)))
    result=resolve_analyses((a,),c,snapshot=snapshot)
    assert not result.ok and 'GSL_SYMBOL_ORIGIN_MISMATCH' in {d.code for d in result.diagnostics}


def test_explicit_source_symbol_does_not_invent_a_material_source_pin():
    raw=b'gsl "0.1"; project "project-alpha"; source "phantom_source" { locator: "other.gsl"; source_cut: context; }'
    def inject(c,b):
        phantom=entity(c.project,K.SOURCE,'phantom-source')
        return replace(c,symbols=(SymbolBinding('phantom_source',phantom,b.source_ref),))
    a,c=analyze(raw,transform=inject)
    result=resolve_analyses((a,),c)
    assert not result.ok and 'GSL_SOURCE_NOT_PINNED' in {d.code for d in result.diagnostics}


def test_reference_diagnostics_identify_owning_record_not_only_field():
    _,_,records,snapshot,ids=scenario()
    errors=validate_references((records[0],records[1]),snapshot).diagnostics
    assert any('objective-one' in d.path for d in errors)
    assert any('objective-two' in d.path for d in errors)


def test_declaration_budget_is_enforced_even_without_expression_nodes():
    raw=b'gsl "0.1"; project "project-alpha";'+b''.join(f'property "property-{i}" {{}}'.encode() for i in range(20))
    a,c=analyze(raw)
    result=resolve_analyses((a,),c,max_nodes=5)
    assert not result.ok and 'GSL_RESOLUTION_RESOURCE_LIMIT' in {d.code for d in result.diagnostics}


def test_unchecked_source_items_remain_immutable_in_public_result():
    raw=b'gsl "0.1"; project "project-alpha"; objective "objective-main" {from:source_item("source-main","item");}'
    a,c=analyze(raw);report=resolve_analyses((a,),c);assert report.ok
    with pytest.raises(TypeError):
        replace(report,unchecked_source_items=list(report.unchecked_source_items))


def test_linked_reference_rejects_untyped_or_foreign_declaration_metadata():
    raw=b'gsl "0.1"; project "project-alpha"; scope "scope-main" {project: project("project-alpha");}'
    a,c=analyze(raw);r=resolve_analyses((a,),c).references[0]
    with pytest.raises(TypeError):
        replace(r,target='project-alpha')
    with pytest.raises(ValueError):
        replace(r,source=entity(project('project-beta').project_id,K.SOURCE,'source-main'))


def test_expression_budget_is_counted_after_declaration_budget():
    raw=b'gsl "0.1"; project "project-alpha"; property "property-main" {holds: a and b and c and d and e and f;}'
    a,c=analyze(raw)
    result=resolve_analyses((a,),c,max_nodes=5)
    assert not result.ok and 'GSL_RESOLUTION_RESOURCE_LIMIT' in {d.code for d in result.diagnostics}


def test_symbol_alias_cannot_shadow_local_declaration_with_foreign_record():
    from guardian.domain.source import ApprovedSourceImport
    from guardian.domain.references import EntityImport,TrustedEntityImports
    a,b=scenario(),scenario('project-beta');target=b[4]['property-shared'];s=b[1]
    raw=b'gsl "0.1"; project "project-alpha"; property "shared_property" {} obligation "obligation-main" {requires:property("shared_property");}'
    # The local declaration has an explicit canonical identity to preserve the
    # current GSL shorthand grammar instead of inventing an ID from an alias.
    local=entity(a[0].project_id,K.PROPERTY,'local-property')
    parsed,c=analyze(raw,transform=lambda c,bundle:replace(c,symbols=(SymbolBinding('shared_property',local,bundle.source_ref),)))
    grant=ApprovedSourceImport(a[0].project_id,s.ref,s.repository,s.path,entity(a[0].project_id,K.DECISION,'import-decision'),s)
    imports=TrustedEntityImports((EntityImport(grant,frozenset({target}),b[3]),))
    result=resolve_analyses((parsed,),c,snapshot=a[3],imports=imports,
        external_symbols=(SymbolBinding('shared_property',target,s.ref),))
    assert not result.ok and 'GSL_AMBIGUOUS_REFERENCE' in {d.code for d in result.diagnostics}
