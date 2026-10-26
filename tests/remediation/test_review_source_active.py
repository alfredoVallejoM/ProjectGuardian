"""Product-path falsifications on unchanged published modules; no runtime mocks."""
from dataclasses import replace
from hashlib import sha256
import pytest
from foundation_b02 import project,cut,bundle_context
from guardian.domain.identity import ContentDigest,DigestAlgorithm
from guardian.domain.source import (GitSourceCut,DocumentSourceCut,
    validate_git_source_cut,validate_document_source)
from guardian.spec_lang.contract import SourceBundle
from guardian.spec_lang.syntax import analyze_source
from guardian.spec_lang.typecheck import typecheck_analyses
from guardian.spec_lang.elaboration import elaborate_program
from guardian.spec_lang.rebuild import rebuild_program, SourceChange


def fixture():
    p=project();s=cut(p)
    raw=b'gsl "0.1"; project "project-alpha"; scope "scope-main" { project: project("project-alpha"); campaign: "before"; }'
    source,context=bundle_context(p,s,raw)
    analysis=analyze_source(source,context,source_format='gsl')
    assert analysis.ok,analysis.diagnostics
    typed=typecheck_analyses((analysis,),context)
    assert typed.ok,typed.diagnostics
    output=elaborate_program(typed.value)
    assert output.ok,output.diagnostics
    newbytes=raw.replace(b'"before"',b'"after"')
    revised=SourceBundle(source.source_ref,newbytes,ContentDigest(DigestAlgorithm.SHA256,sha256(newbytes).hexdigest()))
    context2=replace(context,expected_sources=((revised.source_ref,revised.expected_digest),))
    return typed.value,source,revised,context2


def test_control_direct_replacement_cannot_reuse_revision():
    program,old,new,context=fixture()
    result=rebuild_program(program,(SourceChange(old.source_ref,old.expected_digest,new,'gsl'),),context)
    assert not result.ok and result.diagnostics[0].code=='GSL_SOURCE_REVISION_REUSE'


@pytest.mark.parametrize('reverse',[False,True])
def test_review_G01_split_delete_add_must_not_bypass_revision_immutability(reverse):
    program,old,new,context=fixture()
    changes=(SourceChange(old.source_ref,old.expected_digest,None,None),SourceChange(None,None,new,'gsl'))
    if reverse:changes=tuple(reversed(changes))
    result=rebuild_program(program,changes,context)
    assert not result.ok, 'Split deletion/addition rewrites the source and scope under exactly the same revision'


@pytest.mark.parametrize('kind',['git','document'])
def test_review_D01_source_validator_must_validate_payload_not_only_class(kind):
    # An actual subclass with an invalid payload, not a mock of the validator.
    # This exercises the exported object-validation boundary, not authentication.
    p=project();source=cut(p)
    if kind=='git':
        class Unchecked(GitSourceCut):
            def __post_init__(self):pass
        value=Unchecked(source.ref,source.repository,'main',source.object_kind,source.path)
        result=validate_git_source_cut(value)
    else:
        class Unchecked(DocumentSourceCut):
            def __post_init__(self):pass
        value=Unchecked(source.ref,'https://example.invalid/spec','')
        result=validate_document_source(value)
    assert not result.ok, 'Exported source validator accepts invalid concrete payload solely by isinstance'


def test_review_D01_universe_does_not_reject_mutable_git_cut_subclass():
    from foundation_b02 import universe
    from guardian.domain.source import validate_source_universe
    p=project();source=cut(p)
    class Unchecked(GitSourceCut):
        def __post_init__(self):pass
    value=Unchecked(source.ref,source.repository,'main',source.object_kind,source.path)
    result=validate_source_universe(universe(p,(value,)),p,{value.ref:value})
    assert not result.ok, 'Universe validation accepts a mutable branch in an unchecked GitSourceCut subclass'


@pytest.mark.parametrize('kind',['git','document'])
def test_control_nominal_constructors_reject_invalid_source_payload(kind):
    p=project();source=cut(p)
    with pytest.raises((ValueError,TypeError)):
        if kind=='git':GitSourceCut(source.ref,source.repository,'main',source.object_kind,source.path)
        else:DocumentSourceCut(source.ref,'https://example.invalid/spec','')


def test_control_valid_source_passes_validator_and_universe():
    from foundation_b02 import universe
    from guardian.domain.source import validate_source_universe
    p=project();source=cut(p)
    assert validate_git_source_cut(source).ok
    assert validate_source_universe(universe(p,(source,)),p,{source.ref:source}).ok


@pytest.mark.parametrize('split',[False,True])
def test_control_changed_source_with_new_revision_is_rebuilt(split):
    from guardian.domain.identity import RevisionId
    program,old,new,context=fixture()
    new=replace(new,source_ref=replace(new.source_ref,revision=RevisionId('rev-'+'b'*32)))
    context=replace(context,expected_sources=((new.source_ref,new.expected_digest),))
    changes=((SourceChange(old.source_ref,old.expected_digest,None,None),SourceChange(None,None,new,'gsl'))
             if split else (SourceChange(old.source_ref,old.expected_digest,new,'gsl'),))
    result=rebuild_program(program,changes,context)
    assert result.ok,result.diagnostics
    assert result.value.output.contracts[0].source==new.source_ref
