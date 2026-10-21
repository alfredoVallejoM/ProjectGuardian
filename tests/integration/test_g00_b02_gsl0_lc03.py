"""Productive read-only vertical: G00-B01 → B02 → LC00 → LC03."""
from dataclasses import replace
from hashlib import sha256
import pytest

from guardian.domain.identity import ContentDigest,DigestAlgorithm,EntityKind,Alias,AliasIndex,bind_alias,resolve_alias
from guardian.domain.source import (SourceEntry,HistoryRole,MissingSource,SourceExclusion)
from guardian.domain.outcomes import SourceStatus
from guardian.application.project_service import (build_readonly_project_view,
    verify_bundle_in_project,analyze_project_source)
from guardian.spec_lang.contract import CompileStatus,CompilationStage,SourceBundle
from guardian.spec_lang.syntax import analyze_source
from foundation_b02 import project,entity,cut,universe,bundle_context

TEXT=b'gsl "0.1";\nproject "project-alpha";\nsource "local" { locator: "spec/main.gsl"; source_cut: context; }\n'


def setup_project(raw=TEXT,*,name='project-alpha',acquisition=SourceStatus.CONTENT_OBSERVED,missing=(),included=None):
    p=project(name)
    s=cut(p)
    b,ctx=bundle_context(p,s,raw)
    s=replace(s,observed_digest=b.expected_digest)
    u=universe(p,(s,),missing=missing,included=included,
               entries=(SourceEntry(s,HistoryRole.BASE,acquisition,'history-a'),))
    view=build_readonly_project_view(p,u,{s.ref:s})
    assert view.ok,view.diagnostics
    return p,s,u,view.value,b,ctx


def test_g00_v01_real_two_project_source_parse_no_authority_merge():
    a=setup_project()
    raw=TEXT.replace(b'project-alpha',b'project-beta')
    b=setup_project(raw,name='project-beta')
    assert a[0].project_id!=b[0].project_id
    assert a[1].ref.entity.value==b[1].ref.entity.value
    assert a[1].ref!=b[1].ref
    ra=analyze_project_source(a[3],a[4],a[5],source_format='gsl')
    rb=analyze_project_source(b[3],b[4],b[5],source_format='gsl')
    assert ra.ok and rb.ok
    assert ra.units[0].ast.project=='project-alpha'
    assert rb.units[0].ast.project=='project-beta'
    foreign=analyze_project_source(a[3],b[4],b[5],source_format='gsl')
    assert not foreign.ok and foreign.diagnostics[0].code=='GSL_FOREIGN_PROJECT'


def test_g00_v01_alias_collision_project_scope_remains_safe():
    a=setup_project();b=setup_project(TEXT.replace(b'project-alpha',b'project-beta'),name='project-beta')
    e1=entity(a[0].project_id,EntityKind.OBLIGATION,'same')
    e2=entity(b[0].project_id,EntityKind.OBLIGATION,'same')
    idx=bind_alias(AliasIndex(),e1,Alias('Shared'),a[1].ref).index
    idx=bind_alias(idx,e2,Alias('Shared'),b[1].ref).index
    assert resolve_alias(idx,a[0].project_id,EntityKind.OBLIGATION,Alias('Shared')).value==e1
    assert resolve_alias(idx,b[0].project_id,EntityKind.OBLIGATION,Alias('Shared')).value==e2


def test_g00_v03_incomplete_universe_keeps_missing_but_allows_scoped_observed_input():
    p,s,u,v,b,ctx=setup_project(missing=(MissingSource('historical-1999','not acquired'),))
    assert len(v.source_universe.known_missing)==1
    # Parsing one included source is possible, qualifying entire corpus is not.
    out=analyze_project_source(v,b,ctx,source_format='gsl')
    assert out.ok and out.status is CompileStatus.ANALYZED


def test_g00_b02_lc03_fails_closed_when_source_not_observed():
    p,s,u,v,b,ctx=setup_project(acquisition=SourceStatus.IDENTIFIED)
    out=analyze_project_source(v,b,ctx,source_format='gsl')
    assert out.status is CompileStatus.REJECTED
    assert out.diagnostics[0].code=='GSL_SOURCE_NOT_OBSERVED'


def test_g00_b02_lc03_refuses_excluded_source_and_universe_drift():
    p,s,u,v,b,ctx=setup_project(included=(),missing=(MissingSource("missing baseline","excluded pending acquisition"),))
    out=analyze_project_source(v,b,ctx,source_format='gsl')
    assert not out.ok and out.diagnostics[0].code=='GSL_SOURCE_OUTSIDE_UNIVERSE'


def test_g00_b02_lc03_refuses_source_hash_change_even_if_context_pin_is_recalculated():
    p,s,u,v,b,ctx=setup_project()
    tampered=b.source_bytes.replace(b'"project-alpha"',b'"project-beta"')
    # Attacker controls a separate bundle/context; source catalogue pin must prevail.
    tb,tctx=bundle_context(p,replace(s,observed_digest=None),tampered)
    out=analyze_project_source(v,tb,tctx,source_format='gsl')
    assert not out.ok and out.diagnostics[0].code=='GSL_SOURCE_DIGEST_MISMATCH'


def test_b02_lc03_raw_and_markdown_normative_yield_identical_parsed_fields():
    p,s,u,v,b,ctx=setup_project()
    mdraw=b'Preface\r\n```gsl example\r\nignored\r\n```\r\n```gsl normative version=0.1\r\n'+TEXT+b'```\r\n'
    bmd,cmd=bundle_context(p,replace(s,observed_digest=None),mdraw)
    smd=replace(s,observed_digest=bmd.expected_digest)
    umd=universe(p,(smd,))
    vmd=build_readonly_project_view(p,umd,{smd.ref:smd})
    assert vmd.ok
    one=analyze_project_source(v,b,ctx,source_format='gsl')
    two=analyze_project_source(vmd.value,bmd,cmd,source_format='markdown')
    assert one.ok and two.ok
    assert one.units[0].ast.version==two.units[0].ast.version
    assert one.units[0].ast.declarations[0].fields[0].expr.value==two.units[0].ast.declarations[0].fields[0].expr.value
    assert two.units[0].cst.yield_bytes()==TEXT


def test_b02_lc03_detects_ast_deletion_from_normative_gsl():
    p,s,u,v,b,ctx=setup_project()
    src=b.source_bytes.replace(b'source "local" { locator: "spec/main.gsl"; source_cut: context; }\n',b'')
    modified,context=bundle_context(p,replace(s,observed_digest=None),src)
    # Parser cannot claim historical coverage; it faithfully exposes zero declarations.
    out=analyze_source(modified,context,source_format='gsl')
    assert out.ok and len(out.units[0].ast.declarations)==0
    # LC09 independent coverage inventory required to reject omitted original obligation.
    assert out.status is CompileStatus.ANALYZED


def test_b02_lc03_rejects_context_with_wrong_expected_digest():
    p,s,u,v,b,ctx=setup_project()
    bogus=ContentDigest(DigestAlgorithm.SHA256,'0'*64)
    other=replace(ctx,expected_sources=((s.ref,bogus),))
    out=analyze_project_source(v,b,other,source_format='gsl')
    assert out.status is CompileStatus.REJECTED
    assert out.diagnostics[0].code in ('GSL_SOURCE_DIGEST_MISMATCH','GSL_UNTRUSTED_SOURCE','GSL_SOURCE_PIN_MISMATCH')
