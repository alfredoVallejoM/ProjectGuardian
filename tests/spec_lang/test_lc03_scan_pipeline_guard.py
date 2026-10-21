"""LC03 production path must run the C02 lossless scanner, not just test it alone."""
from guardian.spec_lang.contract import CompilationStage, CompileStatus
from guardian.spec_lang.text import FrontendError
from guardian.spec_lang.syntax import analyze_source
from foundation_b02 import project,cut,bundle_context


def test_lc03_production_scan_segments_cover_pinned_source():
    p=project();s=cut(p)
    raw=b'gsl "0.1";\r\nproject "project-alpha";\r\n// comment\r\n'
    bundle,ctx=bundle_context(p,s,raw)
    result=analyze_source(bundle,ctx,source_format='gsl')
    assert result.status is CompileStatus.ANALYZED
    assert b''.join(x.raw for x in result.segments)==raw
    assert result.segments[0].span.start==0 and result.segments[-1].span.end==len(raw)


def test_lc03_skipped_or_failing_lossless_scan_prevents_analyzed(monkeypatch):
    from guardian.spec_lang import syntax
    p=project();s=cut(p);bundle,ctx=bundle_context(p,s,b'gsl "0.1"; project "project-alpha";')
    def broken(_):raise FrontendError('GSL_SCAN_INJECTED_FAULT',0,'forced scan failure')
    monkeypatch.setattr(syntax,'lossless_scan',broken)
    report=analyze_source(bundle,ctx,source_format='gsl')
    assert report.status is CompileStatus.REJECTED
    assert report.stage is CompilationStage.SCAN
    assert report.diagnostics[0].code=='GSL_SCAN_INJECTED_FAULT'
