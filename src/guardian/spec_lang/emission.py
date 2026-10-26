"""C14 emission for the fixed GSL0 profile; pure and never normative admission.

An emitted bundle binds exact sources, compiler identity, context descriptors,
canonical contracts, exact source maps and pending proof obligations. The reader
checks a caller-supplied digest, not a digest asserted by the bundle itself.
Context authentication and historical source-item sufficiency are separate.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from guardian.domain.identity import ContentDigest, DigestAlgorithm, EntityRef, ProjectId, RevisionId, encode_identity, decode_identity
from guardian.domain.outcomes import Diagnostic, Result
from .contract import (TYPED_IR_SCHEMA, CompilationStage, ProofState, SourceBundle, CompileContext,
                       CompilerIdentity, RegistrySnapshot, RegistryEntry, SymbolBinding, ExternalImportScope)
from .elaboration import ElaboratedProgram, SourceMapEntry, elaborate_program
from .ir import canonical_bytes, decode_ir, SourceOrigin, IRType
from .typecheck import TypedProgram

BUNDLE_SCHEMA = 'guardian/gsl0/emission/v1'
LIMITS = {
    'normatively_admitted': False,
    'materially_qualified': False,
    'source_item_coverage': 'NOT_RECONCILED',
    'external_context_authentication': 'NOT_CHECKED',
    'dependency_body_pins': 'NOT_EXPORTED',
    'semantic_sufficiency': 'NOT_PROVEN',
}


@dataclass(frozen=True, slots=True)
class EmissionBudget:
    max_bytes: int = 32_000_000
    max_nodes: int = 500_000
    max_depth: int = 128

    def __post_init__(self) -> None:
        for value, cap in ((self.max_bytes, 64_000_000), (self.max_nodes, 1_000_000), (self.max_depth, 256)):
            if type(value) is not int or not 1 <= value <= cap:
                raise ValueError('GSL_INVALID_EMISSION_BUDGET')


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def _digest(raw: bytes) -> ContentDigest:
    return ContentDigest(DigestAlgorithm.SHA256, sha256(raw).hexdigest())


def _key(reference: EntityRef) -> tuple[str, ...]:
    return reference.project.value, reference.kind.value, reference.entity.value, reference.revision.value


def _shape(value: object, keys: tuple[str, ...]) -> dict:
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError('GSL_INVALID_BUNDLE_SHAPE')
    return value


def _nodes(value: object, budget: EmissionBudget) -> None:
    stack = [(value, 0)]
    count = 0
    while stack:
        item, depth = stack.pop()
        count += 1
        if count > budget.max_nodes or depth > budget.max_depth:
            raise ValueError('GSL_EMISSION_RESOURCE_LIMIT')
        if type(item) is dict:
            if any(type(k) is not str for k in item):
                raise TypeError('GSL_BUNDLE_STRING_KEYS_REQUIRED')
            stack.extend((v, depth + 1) for v in item.values())
        elif type(item) is list:
            stack.extend((v, depth + 1) for v in item)
        elif type(item) not in (str, int, bool, type(None)):
            raise TypeError('GSL_BUNDLE_PRIMITIVE_REQUIRED')


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('GSL_BUNDLE_DUPLICATE_KEY')
        result[key] = value
    return result


def _fail(exc: Exception) -> Result:
    code = str(exc)
    if not code.startswith('GSL_') or not code.replace('_', '').isalnum():
        code = 'GSL_EMISSION_REJECTED'
    return Result(diagnostics=(Diagnostic(code, '$.bundle',
        'pinned source-grounded emission', type(exc).__name__, str(exc)),))


@dataclass(frozen=True, slots=True)
class EmittedBundle:
    wire_bytes: bytes
    compilation_digest: ContentDigest

    def __post_init__(self) -> None:
        if type(self.wire_bytes) is not bytes or type(self.compilation_digest) is not ContentDigest:
            raise TypeError('GSL_BUNDLE_NOMINAL_BYTES_REQUIRED')
        if _digest(self.wire_bytes) != self.compilation_digest:
            raise ValueError('GSL_COMPILATION_DIGEST_MISMATCH')

    @property
    def status(self) -> str:
        return 'EMITTED_FIXED_PROFILE'

    @property
    def normatively_admitted(self) -> bool:
        return False


def _context(program: TypedProgram) -> dict:
    context = program.context
    def symbol(binding):
        return {'name': binding.name, 'identity': encode_identity(binding.identity),
                'source': encode_identity(binding.declared_source)}
    def registry(item):
        return None if item is None else {
            'canonical_source': item.canonical_source().decode('utf-8'),
            'digest': encode_identity(item.expected_digest)}
    return {
        'project': encode_identity(context.project),
        'language_version': context.language_version,
        'semantic_version': context.semantic_version,
        'compiler': {'implementation': context.compiler.implementation,
                     'semantic_version': context.compiler.semantic_version,
                     'binary_digest': encode_identity(context.compiler.binary_digest)},
        'source_pins': [{'source': encode_identity(ref), 'digest': encode_identity(digest)}
                        for ref, digest in sorted(context.expected_sources, key=lambda pair: _key(pair[0]))],
        'supported_features': sorted(context.supported_features),
        'symbols': sorted((symbol(b) for b in context.symbols), key=_canonical),
        'external_symbols': sorted((symbol(b) for b in program.external_symbols), key=_canonical),
        'type_registry': registry(context.type_registry),
        'predicate_registry': registry(context.predicate_registry),
        'import_scopes': sorted(({'source': encode_identity(g.source),
                                 'target_project': encode_identity(g.target_project),
                                 'admitted_kinds': sorted(k.value for k in g.admitted_kinds)}
                                for g in context.import_scopes), key=_canonical),
        # References identify dependencies; this field is deliberately NOT a
        # claim to export/authenticate the bodies of an external trust context.
        'snapshot_revision': None if program.snapshot is None else encode_identity(program.snapshot.revision),
    }


def emit_program(program: TypedProgram, output: ElaboratedProgram | None = None, *,
                 budget: EmissionBudget = EmissionBudget()) -> Result[EmittedBundle]:
    """Re-elaborate original sources before emitting; caller objects are not proofs.

    A provided output must equal the freshly produced result, including formulas,
    pending POs and source items. Checking source-map containment alone is unsafe.
    """
    try:
        if type(program) is not TypedProgram or type(budget) is not EmissionBudget:
            raise TypeError('GSL_EMISSION_INPUT_REQUIRED')
        EmissionBudget.__post_init__(budget)
        TypedProgram.__post_init__(program)
        if sum(len(a.extraction.source.source_bytes) for a in program.analyses) > budget.max_bytes:
            raise ValueError('GSL_EMISSION_RESOURCE_LIMIT')
        fresh = elaborate_program(program)
        if not fresh.ok:
            return Result(diagnostics=fresh.diagnostics)
        if output is not None and (type(output) is not ElaboratedProgram or output != fresh.value):
            raise ValueError('GSL_EMISSION_SOURCE_IR_MISMATCH')
        output = fresh.value
        if any(p.state is not ProofState.UNPROVEN for p in output.proofs):
            raise ValueError('GSL_EMISSION_PROOF_PROMOTION')
        sources = sorted((a.extraction.source for a in program.analyses), key=lambda b: _key(b.source_ref))
        formats = {}
        for analysis in program.analyses:
            kinds = {unit.format for unit in analysis.extraction.units}
            if len(kinds) != 1:
                raise ValueError('GSL_BUNDLE_MIXED_SOURCE_FORMAT')
            formats[analysis.extraction.source.source_ref] = 'gsl' if kinds == {'gsl'} else 'markdown'
        source_rows = [{'source': encode_identity(b.source_ref), 'digest': encode_identity(b.expected_digest),
                        'format': formats[b.source_ref], 'utf8': b.source_bytes.decode('utf-8')} for b in sources]
        contracts = [{'canonical_ir': raw.decode('utf-8'), 'contract_digest': encode_identity(digest)}
                     for raw, digest in zip(output.canonical_contracts, output.contract_digests)]
        maps = [{'declaration': encode_identity(m.declaration), 'path': m.path,
                 'source': encode_identity(m.origin.source), 'source_digest': encode_identity(m.origin.source_digest),
                 'byte_start': m.origin.byte_start, 'byte_end': m.origin.byte_end} for m in output.source_map]
        payload = {'schema': BUNDLE_SCHEMA, 'ir_schema': TYPED_IR_SCHEMA, 'stage': CompilationStage.EMIT.value, 'status': 'EMITTED_FIXED_PROFILE',
                   'context': _context(program), 'sources': source_rows, 'contracts': contracts,
                   'source_map': maps,
                   'unchecked_source_items': [{'source': encode_identity(s), 'item': item}
                                              for s, item in sorted(output.unchecked_source_items, key=lambda pair: (_key(pair[0]), pair[1]))],
                   'diagnostics': [], 'assurance': dict(LIMITS)}
        _nodes(payload, budget)
        raw = _canonical(payload)
        if len(raw) > budget.max_bytes:
            raise ValueError('GSL_EMISSION_RESOURCE_LIMIT')
        return Result(EmittedBundle(raw, _digest(raw)))
    except (TypeError, ValueError, AttributeError, KeyError, RecursionError, UnicodeError) as exc:
        return _fail(exc)


def read_emission(raw: bytes, expected_digest: ContentDigest, *,
                  budget: EmissionBudget = EmissionBudget()) -> Result[EmittedBundle]:
    """Validate transport against an external pin. Does NOT certify correspondence.

    Re-emission with verify_emission is required to compare original source
    meaning. The parsed dict is never retained as mutable authoritative state.
    """
    try:
        if type(raw) is not bytes or type(expected_digest) is not ContentDigest or type(budget) is not EmissionBudget:
            raise TypeError('GSL_EMISSION_INPUT_REQUIRED')
        EmissionBudget.__post_init__(budget)
        if len(raw) > budget.max_bytes:
            raise ValueError('GSL_EMISSION_RESOURCE_LIMIT')
        if _digest(raw) != expected_digest:
            raise ValueError('GSL_COMPILATION_DIGEST_MISMATCH')
        def reject_number(value):
            raise ValueError('GSL_BUNDLE_INVALID_NUMBER')
        data = json.loads(raw, object_pairs_hook=_pairs, parse_float=reject_number, parse_constant=reject_number)
        _nodes(data, budget)
        _shape(data, ('schema', 'ir_schema', 'stage', 'status', 'context', 'sources', 'contracts',
                      'source_map', 'unchecked_source_items', 'diagnostics', 'assurance'))
        if data['schema'] != BUNDLE_SCHEMA or data['ir_schema'] != TYPED_IR_SCHEMA:
            raise ValueError('GSL_UNKNOWN_BUNDLE_SCHEMA')
        if (data['stage'] != CompilationStage.EMIT.value or data['status'] != 'EMITTED_FIXED_PROFILE'
                or _canonical(data['assurance']) != _canonical(LIMITS) or data['diagnostics'] != []):
            raise ValueError('GSL_BUNDLE_AUTHORITY_PROMOTION')
        if _canonical(data) != raw:
            raise ValueError('GSL_NONCANONICAL_BUNDLE')
        # A transport reader must still reject corrupted typed IR and hashes.
        if type(data['contracts']) is not list or not data['contracts']:
            raise ValueError('GSL_BUNDLE_CONTRACTS_REQUIRED')
        decoded_contracts = []
        for item in data['contracts']:
            _shape(item, ('canonical_ir', 'contract_digest'))
            if type(item['canonical_ir']) is not str:
                raise ValueError('GSL_BUNDLE_CONTRACTS_REQUIRED')
            content = item['canonical_ir'].encode('utf-8')
            ir = decode_ir(content)
            if canonical_bytes(ir) != content or encode_identity(_digest(content)) != item['contract_digest']:
                raise ValueError('GSL_BUNDLE_CONTRACT_DIGEST_MISMATCH')
            if any(p.state is not ProofState.UNPROVEN for p in ir.proofs):
                raise ValueError('GSL_EMISSION_PROOF_PROMOTION')
            decoded_contracts.append(ir)
        _validate_transport(data, tuple(decoded_contracts))
        return Result(EmittedBundle(raw, expected_digest))
    except (TypeError, ValueError, AttributeError, KeyError, RecursionError, UnicodeError) as exc:
        return _fail(exc)


def verify_emission(raw: bytes, program: TypedProgram, expected_digest: ContentDigest, *,
                    budget: EmissionBudget = EmissionBudget()) -> Result[EmittedBundle]:
    """Source-grounded readback using the supplied compiler context; no authentication."""
    checked = read_emission(raw, expected_digest, budget=budget)
    if not checked.ok:
        return checked
    rebuilt = emit_program(program, budget=budget)
    if not rebuilt.ok:
        return rebuilt
    if rebuilt.value.wire_bytes != raw:
        return _fail(ValueError('GSL_EMISSION_REBUILD_MISMATCH'))
    return rebuilt


def _id(raw: object, typ: type):
    parsed = decode_identity(raw)
    if not parsed.ok or type(parsed.value) is not typ:
        raise ValueError('GSL_BUNDLE_ID_KIND_MISMATCH')
    return parsed.value


def _list(raw: object) -> list:
    if type(raw) is not list:
        raise ValueError('GSL_BUNDLE_ARRAY_REQUIRED')
    return raw


def _validate_transport(data: dict, contracts: tuple) -> None:
    """Cross-field integrity, not source meaning or authenticated context."""
    c = _shape(data['context'], ('project', 'language_version', 'semantic_version', 'compiler',
        'source_pins', 'supported_features', 'symbols', 'external_symbols', 'type_registry',
        'predicate_registry', 'import_scopes', 'snapshot_revision'))
    compiler = _shape(c['compiler'], ('implementation', 'semantic_version', 'binary_digest'))
    def symbol(raw):
        row = _shape(raw, ('name', 'identity', 'source'))
        return SymbolBinding(row['name'], _id(row['identity'], EntityRef), _id(row['source'], EntityRef))
    def registry(raw):
        if raw is None:
            return None
        row = _shape(raw, ('canonical_source', 'digest'))
        if type(row['canonical_source']) is not str:
            raise ValueError('GSL_INVALID_REGISTRY_ENCODING')
        body = json.loads(row['canonical_source'], object_pairs_hook=_pairs)
        _shape(body, ('namespace', 'version', 'entries'))
        entries = []
        for entry in _list(body['entries']):
            _shape(entry, ('name', 'argument_types', 'result_type', 'semantic_id'))
            entries.append(RegistryEntry(entry['name'], tuple(_list(entry['argument_types'])),
                                         entry['result_type'], entry['semantic_id']))
        return RegistrySnapshot(body['namespace'], body['version'], tuple(entries), _id(row['digest'], ContentDigest))
    pins = []
    for pin in _list(c['source_pins']):
        _shape(pin, ('source', 'digest'))
        pins.append((_id(pin['source'], EntityRef), _id(pin['digest'], ContentDigest)))
    from guardian.domain.identity import EntityKind
    imports = []
    for item in _list(c['import_scopes']):
        _shape(item, ('source', 'target_project', 'admitted_kinds'))
        imports.append(ExternalImportScope(_id(item['source'], EntityRef), _id(item['target_project'], ProjectId),
                       frozenset(EntityKind(k) for k in _list(item['admitted_kinds']))))
    features = _list(c['supported_features'])
    if any(type(f) is not str for f in features) or len(set(features)) != len(features):
        raise ValueError('GSL_BUNDLE_FEATURES_REQUIRED')
    context = CompileContext(_id(c['project'], ProjectId), c['language_version'], c['semantic_version'],
        CompilerIdentity(compiler['implementation'], compiler['semantic_version'], _id(compiler['binary_digest'], ContentDigest)),
        tuple(pins), frozenset(features), tuple(symbol(x) for x in _list(c['symbols'])),
        registry(c['type_registry']), registry(c['predicate_registry']), tuple(imports))
    for binding in _list(c['external_symbols']):
        symbol(binding)
    if c['snapshot_revision'] is not None:
        _id(c['snapshot_revision'], RevisionId)
    sources = {}
    for item in _list(data['sources']):
        _shape(item, ('source', 'digest', 'utf8', 'format'))
        if type(item['utf8']) is not str or item['format'] not in ('gsl', 'markdown'):
            raise ValueError('GSL_BUNDLE_SOURCE_ENCODING')
        bundle = SourceBundle(_id(item['source'], EntityRef), item['utf8'].encode('utf-8'), _id(item['digest'], ContentDigest))
        if bundle.source_ref in sources:
            raise ValueError('GSL_BUNDLE_DUPLICATE_SOURCE')
        sources[bundle.source_ref] = bundle
    if {ref: b.expected_digest for ref, b in sources.items()} != dict(context.expected_sources):
        raise ValueError('GSL_BUNDLE_SOURCE_POPULATION_MISMATCH')
    if {ir.source for ir in contracts} != set(sources) or len(contracts) != len(sources):
        raise ValueError('GSL_BUNDLE_CONTRACT_POPULATION_MISMATCH')
    for ir in contracts:
        ir.verify_sources(sources[ir.source])
    maps = []
    for row in _list(data['source_map']):
        _shape(row, ('declaration', 'path', 'source', 'source_digest', 'byte_start', 'byte_end'))
        origin = SourceOrigin(_id(row['source'], EntityRef), _id(row['source_digest'], ContentDigest),
                              row['byte_start'], row['byte_end'])
        if origin.source not in sources:
            raise ValueError('GSL_BUNDLE_ORPHAN_ORIGIN')
        origin.verify_against(sources[origin.source])
        maps.append(SourceMapEntry(_id(row['declaration'], EntityRef), row['path'], origin))
    unchecked = []
    for row in _list(data['unchecked_source_items']):
        _shape(row, ('source', 'item'))
        unchecked.append((_id(row['source'], EntityRef), row['item']))
    expected = [(field.typed_value.value.source, field.typed_value.value.logical_item)
                for ir in contracts for declaration in ir.declarations for field in declaration.fields
                if field.typed_value.kind is IRType.SOURCE_ITEM]
    key = lambda pair: (_key(pair[0]), pair[1])
    if sorted(unchecked, key=key) != sorted(expected, key=key):
        raise ValueError('GSL_BUNDLE_UNCHECKED_ITEMS_LOSS')
    ElaboratedProgram(contracts, tuple(maps), tuple(canonical_bytes(ir) for ir in contracts),
        tuple(_digest(canonical_bytes(ir)) for ir in contracts), tuple(unchecked))
