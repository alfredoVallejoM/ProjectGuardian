from dataclasses import replace
from foundation_b02 import project, cut, universe, entity
from guardian.domain.identity import EntityKind
from guardian.domain.source import validate_source_universe


def test_physical_alias_reports_specific_diagnostic():
    p=project();a=cut(p,name='source-one')
    b=replace(a,ref=entity(p.project_id,EntityKind.SOURCE,'source-two'))
    result=validate_source_universe(universe(p,(a,b)),p,{a.ref:a,b.ref:b})
    assert 'SOURCE_POPULATION_DOUBLE_COUNT' in {d.code for d in result.diagnostics}
