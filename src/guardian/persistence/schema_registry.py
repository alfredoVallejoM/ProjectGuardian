"""G00-09: version-pinned typed domain codecs, without storage I/O.

Only fixed local constructors can be used. The wire never chooses a module,
class, callback, default value or latest registry. Every init field is present;
absence/null/empty remain different. No encoded authority context authenticates
itself: authority runtime objects are deliberately absent from the wire registry.
"""
from __future__ import annotations
import dataclasses
from functools import lru_cache
from types import MappingProxyType
from dataclasses import dataclass
from enum import Enum
import json
import re
import types
from typing import get_type_hints, get_origin, get_args, Any
from guardian.domain.identity import EntityKind, EntityRef, EntityId, RevisionId, ProjectId, encode_identity, decode_identity
from guardian.domain.outcomes import Diagnostic, Result
from guardian.domain.record_base import RecordRevision

ENVELOPE='guardian/normative-envelope/v2'
FEATURES=frozenset({'identity.nominal.v1','record.typed.v1','numbers.exact.v1','scope.four-valued.v1'})
MAX_BYTES=4_000_000
MAX_DEPTH=64
MAX_NODES=100_000
INTEGER=re.compile(r'(?:0|-?[1-9][0-9]*)\Z',re.ASCII)


@lru_cache(maxsize=None)
def _hints(typ):
    # Annotations belong exclusively to registered local classes, never input.
    return MappingProxyType(get_type_hints(typ))


@lru_cache(maxsize=1)
def _classes():
    # Explicit trusted modules; no name here comes from a candidate record.
    from guardian.domain import identity,outcomes,evidence_logic,project,source,record_base,objective,capability,property,obligation,campaign,architecture,scope,authority,constitution,verification,foundation_records,clause
    modules=(identity,outcomes,evidence_logic,project,source,record_base,objective,capability,property,obligation,campaign,architecture,scope,authority,constitution,verification,foundation_records,clause)
    table={};enums={}
    excluded={'Result','RecordRevision','AuthorityContext','AuthorityGrant','ApprovalRecord',
              'AuthorityEvaluation','DecisionValidation','FactSet','ConstantAuthorization','VerifiedPredicateObservation'}
    for module in modules:
        for name,value in vars(module).items():
            if not isinstance(value,type) or value.__module__!=module.__name__ or name in excluded:continue
            if dataclasses.is_dataclass(value):table[module.__name__.split('.')[-1]+'.'+name]=value
            elif issubclass(value,Enum):enums[module.__name__.split('.')[-1]+'.'+name]=value
    # Include only the closed transitive set used by the admitted root records.
    # Reporting/helper dataclasses (e.g. DueDescription) are not wire types.
    reachable=set();pending=list(_root_types())+[identity.ProjectId,identity.EntityId,identity.RevisionId,
        identity.ContentDigest,identity.EntityRef,outcomes.TypedStatus]
    allowed=set(table.values())|set(enums.values())
    def children(hint):
        if isinstance(hint,type) and hint in allowed:return [hint]
        return [t for arg in get_args(hint) for t in children(arg)]
    while pending:
        typ=pending.pop()
        if typ in reachable:continue
        reachable.add(typ)
        if dataclasses.is_dataclass(typ):
            hints=_hints(typ)
            for f in dataclasses.fields(typ):
                if f.init:pending.extend(children(hints.get(f.name,object)))
    return (MappingProxyType({k:v for k,v in table.items() if v in reachable}),
            MappingProxyType({k:v for k,v in enums.items() if v in reachable}))


def _root_types():
    from guardian.domain.objective import ObjectiveRevision
    from guardian.domain.capability import CapabilityRevision
    from guardian.domain.property import PropertyRevision
    from guardian.domain.obligation import ObligationRevision
    from guardian.domain.campaign import CampaignRevision
    from guardian.domain.architecture import ArchitectureRevision
    from guardian.domain.scope import ScopeRevision,SupportProfile,ApplicabilityResult
    from guardian.domain.authority import DecisionRevision
    from guardian.domain.constitution import RuleRevision,ConstitutionRevision
    from guardian.domain.verification import VerificationSpecRevision
    from guardian.domain.clause import ClauseRevision
    from guardian.domain.foundation_records import SourcePolicyRevision,SourceUniverseRecord,ProjectRevision
    from guardian.domain.project import ProjectDefinition
    from guardian.domain.source import SourceUniverseRevision
    from guardian.domain.outcomes import StatusObservation
    return (ObjectiveRevision,CapabilityRevision,PropertyRevision,ObligationRevision,CampaignRevision,
            ArchitectureRevision,ScopeRevision,DecisionRevision,RuleRevision,ConstitutionRevision,
            VerificationSpecRevision,SourcePolicyRevision,SourceUniverseRecord,ProjectRevision,
            ProjectDefinition,SourceUniverseRevision,StatusObservation,SupportProfile,ApplicabilityResult,ClauseRevision)


@dataclass(frozen=True, slots=True)
class SchemaDescriptor:
    schema_id: str
    version: str
    record_type: str
    constructor_tag: str
    normative_features: frozenset[str]
    semantic_version: str = 'g00.domain/v1'

    def __post_init__(self):
        table,_=_classes()
        if any(type(x) is not str or not x for x in (self.schema_id,self.version,self.record_type,self.constructor_tag,self.semantic_version)):
            raise ValueError('INVALID_SCHEMA_DESCRIPTOR')
        if self.constructor_tag not in table or table[self.constructor_tag] not in _root_types():
            raise ValueError('UNSUPPORTED_RECORD_CONSTRUCTOR')
        if type(self.normative_features) is not frozenset or not self.normative_features or not self.normative_features<=FEATURES:
            raise ValueError('UNSUPPORTED_NORMATIVE_FEATURE')


@dataclass(frozen=True, slots=True)
class SchemaRegistry:
    revision: RevisionId
    descriptors: tuple[SchemaDescriptor,...]
    reader_features: frozenset[str] = FEATURES

    def __post_init__(self):
        if type(self.revision) is not RevisionId or type(self.descriptors) is not tuple or not self.descriptors:
            raise TypeError('PINNED_SCHEMA_REGISTRY_REQUIRED')
        for d in self.descriptors:
            if type(d) is not SchemaDescriptor:raise TypeError('SCHEMA_DESCRIPTOR_REQUIRED')
            SchemaDescriptor.__post_init__(d)
        if len({(d.schema_id,d.version) for d in self.descriptors})!=len(self.descriptors):raise ValueError('DUPLICATE_SCHEMA_DESCRIPTOR')
        if len({d.record_type for d in self.descriptors})!=len(self.descriptors):raise ValueError('DUPLICATE_RECORD_TYPE')
        if type(self.reader_features) is not frozenset or any(type(x) is not str for x in self.reader_features):
            raise TypeError('READER_FEATURES_REQUIRED')


def foundation_schema_registry(revision: RevisionId) -> SchemaRegistry:
    table,_=_classes();roots=_root_types()
    descriptors=tuple(SchemaDescriptor('guardian/'+name.split('.')[1], 'v1',name.split('.')[1],name,FEATURES)
                      for name,typ in sorted(table.items()) if typ in roots)
    return SchemaRegistry(revision,descriptors)


def _error(code,reason,path='$'):
    return Result(diagnostics=(Diagnostic(code,path,'pinned typed schema','wire data',reason),))


def lookup_schema_descriptor(schema_id: str, version: str, registry: SchemaRegistry) -> Result[SchemaDescriptor]:
    try:
        if type(registry) is not SchemaRegistry or type(schema_id) is not str or type(version) is not str:
            raise TypeError('PINNED_SCHEMA_REGISTRY_REQUIRED')
        SchemaRegistry.__post_init__(registry)
        found=[d for d in registry.descriptors if (d.schema_id,d.version)==(schema_id,version)]
        return Result(found[0]) if found else _error('UNKNOWN_SCHEMA','no latest fallback')
    except (TypeError,ValueError,AttributeError) as exc:return _error('INVALID_SCHEMA',str(exc))


def _matches(value,hint):
    if hint is Any or hint is object:return True
    if hint is None or hint is type(None):return value is None
    origin,args=get_origin(hint),get_args(hint)
    if origin in (types.UnionType,__import__('typing').Union):return any(_matches(value,h) for h in args)
    if origin in (tuple,frozenset,list):
        if type(value) is not origin:return False
        if not args:return True
        if origin is tuple and len(args)==2 and args[1] is Ellipsis:return all(_matches(x,args[0]) for x in value)
        if origin is tuple:return len(value)==len(args) and all(_matches(x,h) for x,h in zip(value,args))
        return all(_matches(x,args[0]) for x in value)
    return type(value) is hint


class _Codec:
    def __init__(self):
        self.table,self.enums=_classes();self.names={v:k for k,v in self.table.items()};self.enum_names={v:k for k,v in self.enums.items()};self.nodes=0;self.active=set()

    def tick(self,depth):
        self.nodes+=1
        if depth>MAX_DEPTH or self.nodes>MAX_NODES:raise ValueError('CODEC_RESOURCE_LIMIT')

    def encode(self,value,depth=0):
        self.tick(depth);typ=type(value)
        if value is None or typ in (str,bool):
            if typ is str:value.encode('utf-8')
            return value
        if typ is int:
            return value if abs(value)<=9007199254740991 else {'$integer':str(value)}
        if typ in self.enum_names:return {'$enum':self.enum_names[typ],'value':value.value}
        if typ in (tuple,frozenset):
            entries=[self.encode(x,depth+1) for x in value]
            if typ is frozenset:entries.sort(key=lambda x:json.dumps(x,sort_keys=True,separators=(',',':')))
            return {'$tuple' if typ is tuple else '$set':entries}
        if typ not in self.names:raise TypeError('UNSUPPORTED_TYPED_VALUE')
        if id(value) in self.active:raise ValueError('CYCLIC_RECORD')
        self.active.add(id(value))
        try:
            if hasattr(typ,'__post_init__'):typ.__post_init__(value)
            hints=_hints(typ)
            fields={}
            for f in dataclasses.fields(value):
                if not f.init:continue
                item=getattr(value,f.name)
                if f.name in hints and not _matches(item,hints[f.name]):raise TypeError('RECORD_FIELD_TYPE:'+f.name)
                fields[f.name]=self.encode(item,depth+1)
            return {'$type':self.names[typ],'fields':fields}
        finally:self.active.remove(id(value))

    def decode(self,value,depth=0):
        self.tick(depth);typ=type(value)
        if value is None or typ in (str,bool):
            if typ is str:value.encode('utf-8')
            return value
        if typ is int:
            if abs(value)>9007199254740991:raise ValueError('EXACT_INTEGER_TAG_REQUIRED')
            return value
        if typ is not dict:raise ValueError('INVALID_TYPED_ENCODING')
        if set(value)=={'$integer'}:
            raw=value['$integer']
            if type(raw) is not str or len(raw)>4096 or not INTEGER.fullmatch(raw):raise ValueError('INVALID_EXACT_INTEGER')
            integer=int(raw)
            if abs(integer)<=9007199254740991:raise ValueError('NONCANONICAL_EXACT_INTEGER')
            return integer
        if set(value)=={'$enum','value'}:
            name=value['$enum'];raw=value['value']
            if type(name) is not str or name not in self.enums or type(raw) is not str:raise ValueError('UNSUPPORTED_VARIANT')
            try:return self.enums[name](raw)
            except ValueError:raise ValueError('UNSUPPORTED_VARIANT') from None
        if set(value) in ({'$tuple'},{'$set'}):
            tag=next(iter(value));raw=value[tag]
            if type(raw) is not list or len(raw)>25000:raise ValueError('INVALID_SEQUENCE')
            items=tuple(self.decode(x,depth+1) for x in raw)
            if tag=='$set':
                result=frozenset(items)
                if len(result)!=len(items):raise ValueError('DUPLICATE_SET_ELEMENT')
                return result
            return items
        if set(value)!={'$type','fields'} or type(value['$type']) is not str or value['$type'] not in self.table:
            raise ValueError('UNSUPPORTED_RECORD_CONSTRUCTOR')
        cls=self.table[value['$type']];raw=value['fields']
        names={f.name for f in dataclasses.fields(cls) if f.init}
        if type(raw) is not dict or set(raw)!=names:raise ValueError('INVALID_SCHEMA_SEMANTICS')
        data={k:self.decode(v,depth+1) for k,v in raw.items()};hints=_hints(cls)
        for name,item in data.items():
            if name in hints and not _matches(item,hints[name]):raise TypeError('RECORD_FIELD_TYPE:'+name)
        return cls(**data)


def _unique(pairs):
    data={}
    for k,v in pairs:
        if k in data:raise ValueError('DUPLICATE_JSON_KEY')
        data[k]=v
    return data


def _json_load(raw):
    if type(raw) is not bytes or len(raw)>MAX_BYTES:raise ValueError('RECORD_BYTE_LIMIT')
    return json.loads(raw.decode('utf-8'),object_pairs_hook=_unique,
                      parse_constant=lambda _:(_ for _ in ()).throw(ValueError('NONFINITE_JSON')))


def validate_envelope(envelope: object, reader: SchemaRegistry) -> Result[SchemaDescriptor]:
    try:
        if type(reader) is not SchemaRegistry:raise TypeError('PINNED_SCHEMA_REGISTRY_REQUIRED')
        SchemaRegistry.__post_init__(reader)
        fields={'schema','record_type','payload_schema','payload_version','registry_revision','required_normative_features','payload','informational_extensions','project_id','logical_id','revision_id','source_refs'}
        if type(envelope) is not dict or set(envelope)!=fields:raise ValueError('INVALID_SCHEMA_SEMANTICS')
        if type(envelope['schema']) is not str or envelope['schema']!=ENVELOPE:raise ValueError('UNKNOWN_SCHEMA')
        ids=[]
        for key,kind in (('project_id',ProjectId),('logical_id',EntityId),('revision_id',RevisionId)):
            result=decode_identity(envelope[key])
            if not result.ok or type(result.value) is not kind:raise ValueError('ENVELOPE_IDENTITY_TYPE')
            ids.append(result.value)
        if ids[1].project!=ids[0]:raise ValueError('ENVELOPE_PROJECT_MISMATCH')
        sources=envelope['source_refs']
        if type(sources) is not list or not sources or len(sources)>4096:raise ValueError('ENVELOPE_SOURCE_REFS_REQUIRED')
        decoded=[]
        for value in sources:
            result=decode_identity(value)
            if not result.ok or type(result.value) is not EntityRef or result.value.kind is not EntityKind.SOURCE or result.value.project!=ids[0]:raise ValueError('ENVELOPE_SOURCE_IDENTITY')
            decoded.append(result.value)
        if len(set(decoded))!=len(decoded):raise ValueError('DUPLICATE_SOURCE_REF')

        if envelope['registry_revision']!=reader.revision.value:raise ValueError('REGISTRY_REVISION_MISMATCH')
        found=lookup_schema_descriptor(envelope['payload_schema'],envelope['payload_version'],reader)
        if not found.ok:return found
        d=found.value
        if envelope['record_type']!=d.record_type:raise ValueError('RECORD_DISCRIMINANT_MISMATCH')
        required=envelope['required_normative_features']
        if type(required) is not list or any(type(x) is not str for x in required) or len(set(required))!=len(required):raise ValueError('INVALID_NORMATIVE_FEATURES')
        if set(required)!=d.normative_features:raise ValueError('NORMATIVE_FEATURE_CONTRACT_MISMATCH')
        if set(required)-reader.reader_features:raise ValueError('UNSUPPORTED_NORMATIVE_FEATURE')
        info=envelope['informational_extensions']
        if type(info) is not dict or any(type(k) is not str or not re.fullmatch(r'info\.[A-Za-z_][A-Za-z_0-9.]*',k) for k in info):raise ValueError('INVALID_INFORMATIONAL_EXTENSION')
        # Informational values are preserved but cannot choose constructors or behavior.
        for value in info.values():_Codec().decode(value)
        payload=envelope['payload']
        if type(payload) is not dict or payload.get('$type')!=d.constructor_tag:raise ValueError('PAYLOAD_TYPE_MISMATCH')
        return Result(d)
    except (ValueError,TypeError,KeyError,AttributeError,RecursionError) as exc:return _error(str(exc),'record envelope rejected')


@dataclass(frozen=True, slots=True)
class DecodedRecord:
    record: object
    informational_extensions: tuple[tuple[str,object], ...]

    @property
    def normatively_admitted(self):return False


def _record_context(record,envelope_ref=None,source_refs=None):
    """Never invent a record identity or provenance for a non-entity value."""
    native=getattr(record,'identity',None)
    if type(native) is not EntityRef:
        native=getattr(record,'entity',None)
    if type(native) is EntityRef:
        if envelope_ref is not None and envelope_ref!=native:raise ValueError('ENVELOPE_PAYLOAD_IDENTITY_MISMATCH')
        envelope_ref=native
    if type(envelope_ref) is not EntityRef:raise ValueError('EXPLICIT_ENVELOPE_REFERENCE_REQUIRED')
    from guardian.domain.scope import SupportProfile, ApplicabilityResult
    contextual = type(record) in (SupportProfile, ApplicabilityResult)
    project = record.context.project_id if contextual else getattr(record, 'project_id', None)
    if project is not None and project!=envelope_ref.project:raise ValueError('ENVELOPE_PAYLOAD_PROJECT_MISMATCH')
    native_sources=getattr(record,'source_refs',None)
    if native_sources is None and getattr(record,'source_ref',None) is not None:
        native_sources=(record.source_ref,)
    if native_sources is not None:
        if source_refs is not None and source_refs!=native_sources:raise ValueError('ENVELOPE_PAYLOAD_SOURCE_MISMATCH')
        source_refs=native_sources
    if contextual:
        if type(record) is SupportProfile:
            witnesses = tuple(w for d in record.dimensions for w in d.witnesses + d.completeness_witnesses)
        else:
            witnesses = record.positive_witnesses + record.negative_witnesses + tuple(
                w for c in record.retained_conflicts for w in c.positive_witnesses + c.negative_witnesses)
        derived = frozenset(w.source_ref for w in witnesses)
        if derived:
            if source_refs is not None and (type(source_refs) is not tuple or frozenset(source_refs) != derived):
                raise ValueError('ENVELOPE_PAYLOAD_SOURCE_MISMATCH')
            source_refs = tuple(sorted(derived, key=lambda x: (x.project.value, x.kind.value, x.entity.value, x.revision.value)))
        # An UNKNOWN value with no witnesses has no intrinsic provenance. Its
        # explicit transport metadata is not evidence or an external context pin.
    if type(source_refs) is not tuple or not source_refs or any(type(s) is not EntityRef or s.kind is not EntityKind.SOURCE or s.project!=envelope_ref.project for s in source_refs):
        raise ValueError('EXPLICIT_ENVELOPE_SOURCES_REQUIRED')
    if len(set(source_refs)) != len(source_refs):
        raise ValueError('DUPLICATE_ENVELOPE_SOURCE')
    return envelope_ref,source_refs


def encode_record(record: object, registry: SchemaRegistry, *, envelope_ref: EntityRef | None=None, source_refs: tuple[EntityRef,...] | None=None, informational_extensions: tuple[tuple[str,object],...]=()) -> Result[dict]:
    try:
        if type(registry) is not SchemaRegistry:raise TypeError('PINNED_SCHEMA_REGISTRY_REQUIRED')
        SchemaRegistry.__post_init__(registry)
        codec=_Codec();tag=codec.names.get(type(record))
        d=next((d for d in registry.descriptors if d.constructor_tag==tag),None)
        if d is None:raise ValueError('UNSUPPORTED_RECORD_CONSTRUCTOR')
        if type(informational_extensions) is not tuple:raise TypeError('IMMUTABLE_EXTENSION_INPUT_REQUIRED')
        info={}
        for entry in informational_extensions:
            if type(entry) is not tuple or len(entry)!=2 or type(entry[0]) is not str or entry[0] in info:raise ValueError('INVALID_INFORMATIONAL_EXTENSION')
            info[entry[0]]=_Codec().encode(entry[1])
        identity, sources = _record_context(record,envelope_ref,source_refs)
        encoded=dict(schema=ENVELOPE,record_type=d.record_type,payload_schema=d.schema_id,payload_version=d.version,
                     project_id=encode_identity(identity.project),logical_id=encode_identity(identity.entity),revision_id=encode_identity(identity.revision),
                     source_refs=[encode_identity(r) for r in sources],
                     registry_revision=registry.revision.value,required_normative_features=sorted(d.normative_features),
                     payload=codec.encode(record),informational_extensions=info)
        valid=validate_envelope(encoded,registry)
        if not valid.ok:return valid
        if len(json.dumps(encoded,ensure_ascii=True).encode())>MAX_BYTES:raise ValueError('RECORD_BYTE_LIMIT')
        return Result(encoded)
    except (TypeError,ValueError,KeyError,AttributeError,RecursionError) as exc:return _error('INVALID_RECORD_ENCODING',str(exc))


def decode_record(payload: object, registry: SchemaRegistry) -> Result[DecodedRecord]:
    try:
        if type(payload) is bytes:payload=_json_load(payload)
        valid=validate_envelope(payload,registry)
        if not valid.ok:return valid
        record=_Codec().decode(payload['payload'])
        logical=decode_identity(payload['logical_id']).value;revision=decode_identity(payload['revision_id']).value
        envelope_ref=EntityRef(logical.project,logical.kind,logical,revision)
        sources=tuple(decode_identity(r).value for r in payload['source_refs'])
        _record_context(record,envelope_ref,sources)
        extras=tuple((k,_Codec().decode(v)) for k,v in sorted(payload['informational_extensions'].items()))
        return Result(DecodedRecord(record,extras))
    except (TypeError,ValueError,KeyError,AttributeError,RecursionError) as exc:return _error('INVALID_SCHEMA_SEMANTICS',str(exc))


class Compatibility(str,Enum):
    COMPATIBLE='COMPATIBLE'
    REQUIRES_MIGRATION='REQUIRES_MIGRATION'
    UNSUPPORTED='UNSUPPORTED'


def check_reader_compatibility(writer: SchemaDescriptor, reader: SchemaDescriptor,
                               features: frozenset[str]) -> Compatibility:
    if type(writer) is not SchemaDescriptor or type(reader) is not SchemaDescriptor or type(features) is not frozenset:
        return Compatibility.UNSUPPORTED
    if writer.normative_features-features or writer.record_type!=reader.record_type:return Compatibility.UNSUPPORTED
    if writer!=reader:return Compatibility.REQUIRES_MIGRATION
    return Compatibility.COMPATIBLE


def validate_schema_refs(record: RecordRevision, view, grants=None):
    from guardian.domain.references import validate_references
    return validate_references((record,),view,grants)


def schema_document(registry: SchemaRegistry) -> dict:
    """Materialize a closed JSON Schema 2020-12 for this exact registry.

    Schema validates representation, while decoding also checks nominal cross-
    field invariants. All refs are local; no runtime network resolution exists.
    The new v2 envelope is not silently accepted by the original v1 reader.
    """
    if type(registry) is not SchemaRegistry:raise TypeError('PINNED_SCHEMA_REGISTRY_REQUIRED')
    SchemaRegistry.__post_init__(registry)
    table,enums=_classes();names={t:n for n,t in table.items()};enum_names={t:n for n,t in enums.items()}
    def object_schema(properties):
        return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}
    def reference(name):return {'$ref':'#/$defs/'+name}
    primitive=[{'type':'null'},{'type':'string'},{'type':'boolean'},
               {'type':'integer','minimum':-9007199254740991,'maximum':9007199254740991},reference('exact_integer')]
    defs={'exact_integer':object_schema({'$integer':{'type':'string','maxLength':4096,'pattern':r'^(?:0|-?[1-9][0-9]*)$'}})}
    def spec(hint):
        origin,args=get_origin(hint),get_args(hint)
        if hint is Any or hint is object:return reference('value')
        if hint is type(None):return {'type':'null'}
        if origin in (types.UnionType,__import__('typing').Union):return {'anyOf':[spec(t) for t in args]}
        if hint is str:return {'type':'string'}
        if hint is bool:return {'type':'boolean'}
        if hint is int:return {'anyOf':[primitive[3],reference('exact_integer')]}
        if hint in names:return reference(names[hint])
        if hint in enum_names:return reference(enum_names[hint])
        if origin in (tuple,frozenset):
            items={'type':'array','maxItems':25000}
            if origin is tuple and len(args)==2 and args[1] is Ellipsis:items['items']=spec(args[0])
            elif origin is tuple:
                items.update(prefixItems=[spec(t) for t in args],minItems=len(args),maxItems=len(args),items=False)
            else:items.update(items=spec(args[0]),uniqueItems=True)
            return object_schema({'$tuple' if origin is tuple else '$set':items})
        raise TypeError('UNSUPPORTED_SCHEMA_FIELD:'+str(hint))
    for name,typ in sorted(enums.items()):
        defs[name]=object_schema({'$enum':{'const':name},'value':{'enum':[v.value for v in typ]}})
    for name,typ in sorted(table.items()):
        hints=_hints(typ)
        inner={f.name:spec(hints.get(f.name,object)) for f in dataclasses.fields(typ) if f.init}
        defs[name]=object_schema({'$type':{'const':name},'fields':object_schema(inner)})
    defs['value']={'anyOf':primitive+[reference(n) for n in sorted(table)]+[reference(n) for n in sorted(enums)]+[
        object_schema({'$tuple':{'type':'array','items':reference('value'),'maxItems':25000}}),
        object_schema({'$set':{'type':'array','items':reference('value'),'uniqueItems':True,'maxItems':25000}})]}
    token={'type':'string','minLength':3,'maxLength':96,'pattern':'^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$'}
    kinds=[x.value for x in EntityKind]
    def nominal(typ,props):return object_schema({'schema':{'const':'guardian.identity/v1'},'type':{'const':typ},**props})
    defs['wire_project']=nominal('project_id',{'value':token})
    defs['wire_entity']=nominal('entity_id',{'project':token,'entity_kind':{'enum':kinds},'value':token})
    defs['wire_revision']=nominal('revision_id',{'value':{'type':'string','pattern':'^rev-[0-9a-f]{32}$'}})
    defs['wire_source']=nominal('entity_ref',{'project':token,'entity_kind':{'const':'source'},'entity':token,'revision':{'type':'string','pattern':'^rev-[0-9a-f]{32}$'}})
    envelope=object_schema({'schema':{'const':ENVELOPE},'registry_revision':{'const':registry.revision.value},
        'record_type':{'type':'string'},'payload_schema':{'type':'string'},'payload_version':{'type':'string'},
        'project_id':reference('wire_project'),'logical_id':reference('wire_entity'),'revision_id':reference('wire_revision'),
        'source_refs':{'type':'array','items':reference('wire_source'),'uniqueItems':True,'minItems':1,'maxItems':4096},
        'required_normative_features':{'type':'array','items':{'type':'string'},'uniqueItems':True,'minItems':1},
        'payload':{},'informational_extensions':{'type':'object','propertyNames':{'pattern':r'^info\.[A-Za-z_][A-Za-z_0-9.]*$'},'additionalProperties':reference('value')}})
    envelope['oneOf']=[{'properties':{'record_type':{'const':d.record_type},'payload_schema':{'const':d.schema_id},'payload_version':{'const':d.version},
        'required_normative_features':{'type':'array','items':{'enum':sorted(d.normative_features)},'uniqueItems':True,'minItems':len(d.normative_features),'maxItems':len(d.normative_features)},
        'payload':reference(d.constructor_tag)}} for d in registry.descriptors]
    envelope.update({'$schema':'https://json-schema.org/draft/2020-12/schema',
        '$id':'https://projectguardian.invalid/schemas/domain-record-v2/'+registry.revision.value,'$defs':defs,
        'description':'Wire representation only. Exact nominal invariants and authority remain separate checks.'})
    return envelope
