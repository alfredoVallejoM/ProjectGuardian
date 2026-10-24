"""Versioned, strict applicability-result codec; no normative promotion.

General domain record envelopes remain the responsibility of B06. This codec
preserves the four-valued result, its exact context and both sets of witnesses.
"""
from .identity import EntityRef, ProjectId, RevisionId, encode_identity, decode_identity
from .evidence_logic import FourValued
from .outcomes import Diagnostic, Result
from .scope import ScopeContext, ScopeWitness, ScopeConflict, ApplicabilityResult

SCHEMA = 'guardian.scope-applicability/v1'
_CONTEXT_FIELDS = ('project_id', 'project_revision', 'profile_revision', 'registry_revision',
                   'source_universe_ref', 'verification_policy_ref', 'milestone', 'candidate_ref')


def _shape(value, fields):
    if type(value) is not dict or set(value) != set(fields):
        raise ValueError('INVALID_SCOPE_SCHEMA')
    return value


def _decode_id(raw, typ):
    result = decode_identity(raw)
    if not result.ok or type(result.value) is not typ:
        raise ValueError('WRONG_SCOPE_ID_KIND')
    return result.value


def encode_applicability_result(result: ApplicabilityResult) -> dict:
    if type(result) is not ApplicabilityResult:
        raise TypeError('INVALID_APPLICABILITY_RESULT')
    ApplicabilityResult.__post_init__(result)
    context = {name: (getattr(result.context, name) if name == 'milestone' else
                      None if getattr(result.context, name) is None else encode_identity(getattr(result.context, name)))
               for name in _CONTEXT_FIELDS}
    def witnesses(items):
        return [{'source_ref': encode_identity(w.source_ref), 'identifier': w.identifier,
                 'description': w.description} for w in items]
    return {'schema': SCHEMA, 'context': context,
            'value': {'positive': result.value.positive, 'negative': result.value.negative},
            'positive_witnesses': witnesses(result.positive_witnesses),
            'negative_witnesses': witnesses(result.negative_witnesses),
            'retained_conflicts': [{'positive_witnesses': witnesses(c.positive_witnesses),
                                    'negative_witnesses': witnesses(c.negative_witnesses)}
                                   for c in result.retained_conflicts],
            'diagnostics': [{'code': d.code, 'path': d.path, 'expected': d.expected,
                             'actual_type': d.actual_type, 'reason': d.reason} for d in result.diagnostics]}


def decode_applicability_result(raw: object) -> Result[ApplicabilityResult]:
    try:
        _shape(raw, ('schema', 'context', 'value', 'positive_witnesses', 'negative_witnesses', 'diagnostics', 'retained_conflicts'))
        if type(raw['schema']) is not str or raw['schema'] != SCHEMA:
            raise ValueError('UNKNOWN_SCOPE_SCHEMA_VERSION')
        data = _shape(raw['context'], _CONTEXT_FIELDS)
        context = ScopeContext(
            _decode_id(data['project_id'], ProjectId), _decode_id(data['project_revision'], RevisionId),
            _decode_id(data['profile_revision'], RevisionId), _decode_id(data['registry_revision'], RevisionId),
            _decode_id(data['source_universe_ref'], EntityRef), _decode_id(data['verification_policy_ref'], EntityRef),
            data['milestone'], None if data['candidate_ref'] is None else _decode_id(data['candidate_ref'], EntityRef))
        value = _shape(raw['value'], ('positive', 'negative'))
        bits = FourValued(value['positive'], value['negative'])
        def witnesses(name, container=raw):
            items = container[name]
            if type(items) is not list or len(items) > 4096:
                raise ValueError('INVALID_SCOPE_WITNESSES')
            result = []
            for item in items:
                _shape(item, ('source_ref', 'identifier', 'description'))
                result.append(ScopeWitness(context, _decode_id(item['source_ref'], EntityRef),
                                           item['identifier'], item['description']))
            return tuple(result)
        if type(raw['diagnostics']) is not list or len(raw['diagnostics']) > 4096:
            raise ValueError('INVALID_SCOPE_DIAGNOSTICS')
        diagnostics = tuple(Diagnostic(**_shape(d, ('code','path','expected','actual_type','reason')))
                            for d in raw['diagnostics'])
        conflicts = raw['retained_conflicts']
        if type(conflicts) is not list or len(conflicts) > 4096:
            raise ValueError('INVALID_RETAINED_CONFLICTS')
        retained = []
        for conflict in conflicts:
            _shape(conflict, ('positive_witnesses', 'negative_witnesses'))
            retained.append(ScopeConflict(context, witnesses('positive_witnesses', conflict),
                                          witnesses('negative_witnesses', conflict)))
        return Result(ApplicabilityResult(context, bits, witnesses('positive_witnesses'),
                                         witnesses('negative_witnesses'), diagnostics, tuple(retained)))
    except (TypeError, ValueError, KeyError, AttributeError) as exc:
        return Result(diagnostics=(Diagnostic('INVALID_SCOPE_ENCODING', '$', SCHEMA,
                                             type(raw).__name__, str(exc)),))
