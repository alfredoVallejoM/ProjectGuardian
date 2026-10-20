"""GSL0-LC01: nominal, versioned typed contract IR.

Only a checked/fixed subset is admitted here. Later LC03–LC08 produce this IR;
this module does NOT implement parsing or claim normative admission.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Any, Mapping

from guardian.domain.identity import (
    ContentDigest, DigestAlgorithm, EntityKind, EntityRef, ProjectId,
    decode_identity, encode_identity,
)
from guardian.spec_lang.contract import (
    TYPED_IR_SCHEMA, SEMANTIC_VERSION, ProofObligation,
    SourceBundle, ProofState,
)


class IRType(str, Enum):
    TEXT = 'text'
    BOOL = 'bool'
    INTEGER = 'integer'
    REF = 'ref'
    SOURCE_ITEM = 'source_item'
    KIND = 'kind'
    V4 = 'v4'
    DEFERRED = 'deferred'


class CommitmentKind(str, Enum):
    EXISTENCE = 'existence'
    BEHAVIOR = 'behavior'
    CONSTITUTION = 'constitution'
    EXECUTION = 'execution'
    DEVELOPMENT = 'development'
    INTEGRATION = 'integration'
    MIGRATION = 'migration'


class RelationKind(str, Enum):
    PROPOSED_DETAIL = 'proposed_detail'
    REFERENCES = 'references'


@dataclass(frozen=True, slots=True)
class IRValue:
    kind: IRType
    value: object

    def __post_init__(self) -> None:
        if not isinstance(self.kind, IRType):
            raise TypeError('IR kind must be a recognized discriminant')
        checks = {
            IRType.TEXT: lambda v: isinstance(v,str),
            IRType.BOOL: lambda v: type(v) is bool,
            IRType.INTEGER: lambda v: type(v) is int,
            IRType.REF: lambda v: isinstance(v,EntityRef),
            IRType.SOURCE_ITEM: lambda v: isinstance(v,SourceItem),
            IRType.KIND: lambda v: isinstance(v,CommitmentKind) or isinstance(v,RelationKind),
            IRType.V4: lambda v: isinstance(v,FormulaIR),
            IRType.DEFERRED: lambda v: isinstance(v,str) and bool(v),
        }
        if not checks[self.kind](self.value):
            raise TypeError(f'IR value does not match {self.kind.value} discriminant')


@dataclass(frozen=True, slots=True)
class SourceItem:
    source: EntityRef
    logical_item: str

    def __post_init__(self) -> None:
        if not isinstance(self.source,EntityRef) or self.source.kind is not EntityKind.SOURCE:
            raise TypeError('source item must bind pinned SOURCE ref')
        if not isinstance(self.logical_item,str) or not self.logical_item:
            raise ValueError('source item requires nonempty logical ID')


@dataclass(frozen=True, slots=True)
class FormulaIR:
    """IR-specific formula, not the source-language formula AST."""
    op: str
    args: tuple['FormulaIR', ...] = ()
    name: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.args,tuple) or not all(isinstance(a, FormulaIR) for a in self.args):
            raise TypeError('formula args must be typed')
        if self.op == 'atom':
            if not isinstance(self.name,str) or not self.name or self.args:
                raise ValueError('atom needs name and no operands')
        elif self.op in ('yes','no','unknown','conflict'):
            if self.name is not None or self.args:
                raise ValueError('constant takes no args/name')
        elif self.op == 'not':
            if self.name is not None or len(self.args) != 1:
                raise ValueError('not takes exactly one operand')
        elif self.op in ('and','or'):
            if self.name is not None or len(self.args) < 2:
                raise ValueError('connective takes >=2 operands')
        else:
            raise ValueError('unknown normative formula operator')


@dataclass(frozen=True, slots=True)
class SourceOrigin:
    source: EntityRef
    source_digest: ContentDigest
    byte_start: int
    byte_end: int

    def __post_init__(self) -> None:
        if not isinstance(self.source,EntityRef) or self.source.kind is not EntityKind.SOURCE:
            raise TypeError('origin requires pinned SOURCE ref')
        if not isinstance(self.source_digest,ContentDigest):
            raise TypeError('source origin requires tagged digest')
        if type(self.byte_start) is not int or type(self.byte_end) is not int or self.byte_start<0 or self.byte_start>=self.byte_end:
            raise ValueError('source origin requires nonempty, ordered byte span')

    def verify_against(self, bundle: SourceBundle) -> None:
        if self.source != bundle.source_ref or self.source_digest != bundle.expected_digest:
            raise ValueError('SOURCE_ORIGIN_MISMATCH')
        if self.byte_end > len(bundle.source_bytes):
            raise ValueError('SOURCE_ORIGIN_OUT_OF_BOUNDS')
        try:
            bundle.source_bytes[:self.byte_start].decode('utf-8','strict')
            bundle.source_bytes[:self.byte_end].decode('utf-8','strict')
        except UnicodeDecodeError as exc:
            raise ValueError('SOURCE_ORIGIN_SPLITS_UTF8') from exc


@dataclass(frozen=True, slots=True)
class IRField:
    name: str
    typed_value: IRValue

    def __post_init__(self) -> None:
        if not isinstance(self.name,str) or not self.name or not self.name.isidentifier():
            raise ValueError('invalid IR field name')
        if not isinstance(self.typed_value,IRValue):
            raise TypeError('field requires an IRValue')


@dataclass(frozen=True, slots=True)
class DeclarationIR:
    identity: EntityRef
    origin: SourceOrigin
    fields: tuple[IRField,...]

    def __post_init__(self) -> None:
        if not isinstance(self.identity,EntityRef) or not isinstance(self.origin,SourceOrigin):
            raise TypeError('nominal identity and source origin required')
        if self.identity.kind not in _FIELDS:
            raise ValueError('unsupported normative declaration kind')
        if self.identity.project!=self.origin.source.project:
            raise ValueError('foreign declaration origin')
        if not isinstance(self.fields,tuple) or any(not isinstance(f,IRField) for f in self.fields):
            raise TypeError('IR fields must be immutable and typed')
        by_name:dict[str,int]={}
        for field in self.fields:
            kind= _FIELDS[self.identity.kind].get(field.name)
            if kind is None:
                raise ValueError(f'UNKNOWN_NORMATIVE_FIELD:{field.name}')
            if kind != field.typed_value.kind:
                raise TypeError(f'WRONG_FIELD_TYPE:{field.name}')
            expected_ref=_REFERENCE_KIND.get((self.identity.kind,field.name))
            if expected_ref is not None and (field.typed_value.value.kind != expected_ref):
                raise TypeError(f'WRONG_REFERENCE_KIND:{field.name}')
            if field.typed_value.kind is IRType.KIND:
                expected_enum = RelationKind if self.identity.kind is EntityKind.RELATION else CommitmentKind
                if not isinstance(field.typed_value.value,expected_enum):
                    raise TypeError(f'WRONG_ENUM_KIND:{field.name}')
            by_name[field.name]=by_name.get(field.name,0)+1
            if by_name[field.name]>1 and field.name not in ('requires','verification'):
                raise ValueError(f'DUPLICATE_FIELD:{field.name}')
        if not _REQUIRED[self.identity.kind].issubset(by_name):
            raise ValueError(f'MISSING_NORMATIVE_FIELD:{sorted(_REQUIRED[self.identity.kind]-by_name.keys())}')
        if self.identity.kind is EntityKind.PROPERTY:
            if ('holds' in by_name) == ('deferred_semantics' in by_name):
                raise ValueError('property requires precisely one interpreted or deferred semantics')


_FIELDS: dict[EntityKind,dict[str,IRType]]={
    EntityKind.SOURCE: {'locator':IRType.TEXT,'source_cut':IRType.TEXT},
    EntityKind.SCOPE: {'project':IRType.REF,'campaign':IRType.TEXT},
    EntityKind.OBJECTIVE: {'from':IRType.SOURCE_ITEM,'scope':IRType.REF},
    EntityKind.CAPABILITY: {'from':IRType.SOURCE_ITEM,'scope':IRType.REF},
    EntityKind.PROPERTY: {'from':IRType.SOURCE_ITEM,'kind':IRType.KIND,'subject':IRType.REF,'holds':IRType.V4,'deferred_semantics':IRType.DEFERRED},
    EntityKind.OBLIGATION: {'from':IRType.SOURCE_ITEM,'kind':IRType.KIND,'scope':IRType.REF,'when':IRType.V4,'requires':IRType.REF,'verification':IRType.REF},
    EntityKind.VERIFICATION: {'from':IRType.SOURCE_ITEM,'target':IRType.REF,'property':IRType.REF,'method':IRType.TEXT},
    EntityKind.RELATION: {'kind':IRType.KIND,'parent':IRType.REF,'child':IRType.REF},
}
_REQUIRED: dict[EntityKind,frozenset[str]]={
    EntityKind.SOURCE: frozenset({'locator','source_cut'}),
    EntityKind.SCOPE: frozenset({'project'}),
    EntityKind.OBJECTIVE: frozenset({'from','scope'}),
    EntityKind.CAPABILITY: frozenset({'from','scope'}),
    EntityKind.PROPERTY: frozenset({'kind','subject'}),
    EntityKind.OBLIGATION: frozenset({'from','kind','scope','when'}),
    EntityKind.VERIFICATION: frozenset({'from','target','property','method'}),
    EntityKind.RELATION: frozenset({'kind','parent','child'}),
}
_REFERENCE_KIND={
    (EntityKind.SCOPE,'project'):EntityKind.PROJECT,
    (EntityKind.OBJECTIVE,'scope'):EntityKind.SCOPE,
    (EntityKind.CAPABILITY,'scope'):EntityKind.SCOPE,
    (EntityKind.PROPERTY,'subject'):EntityKind.PROJECT,
    (EntityKind.OBLIGATION,'scope'):EntityKind.SCOPE,
    (EntityKind.OBLIGATION,'requires'):EntityKind.PROPERTY,
    (EntityKind.OBLIGATION,'verification'):EntityKind.VERIFICATION,
    (EntityKind.VERIFICATION,'target'):EntityKind.OBLIGATION,
    (EntityKind.VERIFICATION,'property'):EntityKind.PROPERTY,
    (EntityKind.RELATION,'parent'):EntityKind.OBLIGATION,
    (EntityKind.RELATION,'child'):EntityKind.CLAUSE,
}


@dataclass(frozen=True, slots=True)
class ContractIR:
    project: ProjectId
    source: EntityRef
    source_digest: ContentDigest
    declarations: tuple[DeclarationIR,...]
    proofs: tuple[ProofObligation,...] = ()
    schema: str = TYPED_IR_SCHEMA
    semantic_version: str = SEMANTIC_VERSION

    def __post_init__(self) -> None:
        if self.schema != TYPED_IR_SCHEMA or self.semantic_version != SEMANTIC_VERSION:
            raise ValueError('UNSUPPORTED_IR_SCHEMA_VERSION')
        if not isinstance(self.project,ProjectId) or not isinstance(self.source,EntityRef):
            raise TypeError('typed project/source required')
        if self.source.kind is not EntityKind.SOURCE or self.source.project!=self.project:
            raise ValueError('source must be local and pinned')
        if not isinstance(self.source_digest,ContentDigest):
            raise TypeError('source digest must be typed')
        if not isinstance(self.declarations,tuple) or not all(isinstance(d,DeclarationIR) for d in self.declarations):
            raise TypeError('declarations must be a tuple')
        if not isinstance(self.proofs,tuple) or not all(isinstance(p,ProofObligation) for p in self.proofs):
            raise TypeError('proofs must be a tuple')
        ids:set[EntityRef]=set()
        for d in self.declarations:
            if d.identity.project!=self.project or d.origin.source!=self.source or d.origin.source_digest!=self.source_digest:
                raise ValueError('foreign/ungrounded IR declaration')
            if d.identity in ids:
                raise ValueError('DUPLICATE_DECLARATION')
            ids.add(d.identity)
            for f in d.fields:
                v=f.typed_value
                if v.kind is IRType.REF and v.value.project!=self.project:
                    raise ValueError('FOREIGN_PROJECT_REFERENCE')
                if v.kind is IRType.SOURCE_ITEM and v.value.source!=self.source:
                    raise ValueError('FOREIGN_SOURCE_ITEM')
        if any(p.origin.project!=self.project or p.origin not in ids for p in self.proofs):
            raise ValueError('ORPHAN_PROOF_OBLIGATION')

    def verify_sources(self,bundle:SourceBundle) -> None:
        if self.source != bundle.source_ref or self.source_digest!=bundle.expected_digest:
            raise ValueError('IR_SOURCE_MISMATCH')
        for d in self.declarations:
            d.origin.verify_against(bundle)


def _ref_to_data(ref:EntityRef)->dict[str,object]:
    return encode_identity(ref)


def _value_to_data(v:IRValue)->dict[str,object]:
    x=v.value
    if v.kind is IRType.REF:
        encoded=_ref_to_data(x)
    elif v.kind is IRType.SOURCE_ITEM:
        encoded={'source':_ref_to_data(x.source),'logical_item':x.logical_item}
    elif v.kind is IRType.KIND:
        encoded={'enum':'relation' if isinstance(x,RelationKind) else 'commitment','value':x.value}
    elif v.kind is IRType.V4:
        encoded=_formula_to_data(x)
    else:
        encoded=x
    return {'tag':v.kind.value,'value':encoded}


def _formula_to_data(f:FormulaIR)->dict[str,object]:
    return {'op':f.op,'name':f.name,'args':[_formula_to_data(a) for a in f.args]}


def ir_to_data(ir:ContractIR)->dict[str,object]:
    return {'schema':ir.schema,'semantic_version':ir.semantic_version,
            'project':encode_identity(ir.project),'source':_ref_to_data(ir.source),
            'source_digest':encode_identity(ir.source_digest),
            'declarations':[
                {'identity':_ref_to_data(d.identity),
                 'origin':{'source':_ref_to_data(d.origin.source),'digest':encode_identity(d.origin.source_digest),
                           'byte_start':d.origin.byte_start,'byte_end':d.origin.byte_end},
                 'fields':[{'name':f.name,'value':_value_to_data(f.typed_value)} for f in d.fields]}
                for d in ir.declarations],
            'proofs':[{'identifier':p.identifier,'origin':_ref_to_data(p.origin),'state':p.state.value} for p in ir.proofs]}


def canonical_bytes(ir:ContractIR)->bytes:
    # Preserve declaration and field order: ordering may encode semantics.
    return json.dumps(ir_to_data(ir),sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')


def contract_digest(ir:ContractIR)->ContentDigest:
    return ContentDigest(DigestAlgorithm.SHA256,sha256(canonical_bytes(ir)).hexdigest())


def _exact(obj:object,fields:frozenset[str])->dict:
    if not isinstance(obj,dict) or set(obj)!=fields:
        raise ValueError(f'IR_SCHEMA_FIELDS expected {sorted(fields)}')
    return obj


def _ref(value:object)->EntityRef:
    r=decode_identity(value)
    if not r.ok or not isinstance(r.value,EntityRef):
        raise ValueError('IR_REFERENCE_MUST_BE_NOMINAL')
    return r.value


def _digest(value:object)->ContentDigest:
    r=decode_identity(value)
    if not r.ok or not isinstance(r.value,ContentDigest):
        raise ValueError('IR_DIGEST_MUST_BE_NOMINAL')
    return r.value


def _formula_from_data(obj:object)->FormulaIR:
    x=_exact(obj,frozenset({'op','name','args'}))
    if not isinstance(x['args'],list):
        raise ValueError('IR_FORMULA_ARGS')
    return FormulaIR(x['op'],tuple(_formula_from_data(a) for a in x['args']),x['name'])


def _value_from_data(obj:object)->IRValue:
    v=_exact(obj,frozenset({'tag','value'}))
    kind=IRType(v['tag'])
    value=v['value']
    if kind is IRType.REF:
        value=_ref(value)
    elif kind is IRType.SOURCE_ITEM:
        x=_exact(value,frozenset({'source','logical_item'}))
        value=SourceItem(_ref(x['source']),x['logical_item'])
    elif kind is IRType.KIND:
        x=_exact(value,frozenset({'enum','value'}))
        value=CommitmentKind(x['value']) if x['enum']=='commitment' else RelationKind(x['value']) if x['enum']=='relation' else None
    elif kind is IRType.V4:
        value=_formula_from_data(value)
    return IRValue(kind,value)


def decode_ir(raw:bytes)->ContractIR:
    """Strict decoder; unsupported fields/versions/semantic discriminants fail closed."""
    if not isinstance(raw,bytes):
        raise TypeError('IR decoder accepts exact bytes')
    def reject_duplicates(pairs:list[tuple[str,Any]])->dict:
        out:dict[str,Any]={}
        for k,v in pairs:
            if k in out:
                raise ValueError('DUPLICATE_JSON_KEY')
            out[k]=v
        return out
    data=_exact(json.loads(raw.decode('utf-8','strict'),object_pairs_hook=reject_duplicates),
                frozenset({'schema','semantic_version','project','source','source_digest','declarations','proofs'}))
    project=decode_identity(data['project'])
    if not project.ok or not isinstance(project.value,ProjectId):
        raise ValueError('IR_PROJECT_MUST_BE_NOMINAL')
    if not isinstance(data['declarations'],list) or not isinstance(data['proofs'],list):
        raise ValueError('IR_COLLECTION_SCHEMA')
    ds=[]
    for raw_decl in data['declarations']:
        d=_exact(raw_decl,frozenset({'identity','origin','fields'}))
        o=_exact(d['origin'],frozenset({'source','digest','byte_start','byte_end'}))
        if not isinstance(d['fields'],list):
            raise ValueError('IR_FIELDS_NOT_LIST')
        fs=[]
        for raw_field in d['fields']:
            f=_exact(raw_field,frozenset({'name','value'}))
            fs.append(IRField(f['name'],_value_from_data(f['value'])))
        ds.append(DeclarationIR(_ref(d['identity']),
            SourceOrigin(_ref(o['source']),_digest(o['digest']),o['byte_start'],o['byte_end']),tuple(fs)))
    ps=[]
    for raw_po in data['proofs']:
        p=_exact(raw_po,frozenset({'identifier','origin','state'}))
        ps.append(ProofObligation(p['identifier'],_ref(p['origin']),ProofState(p['state'])))
    return ContractIR(project.value,_ref(data['source']),_digest(data['source_digest']),
                      tuple(ds),tuple(ps),data['schema'],data['semantic_version'])
