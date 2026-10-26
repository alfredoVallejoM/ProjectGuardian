"""B03 incomplete authored records, separate from completed contract bodies.

A draft records supplied fields without inventing missing values. Completion
constructs a PROPOSED record only; approval and publication are not draft actions.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, MISSING
from .identity import EntityKind, EntityRef
from .outcomes import DecisionStatus, Diagnostic, Result
from .record_base import RecordRevision


def _constructors():
    from .objective import ObjectiveRevision
    from .capability import CapabilityRevision
    from .property import PropertyRevision
    from .obligation import ObligationRevision
    from .campaign import CampaignRevision
    from .architecture import ArchitectureRevision
    return {t.KIND:t for t in (ObjectiveRevision,CapabilityRevision,PropertyRevision,ObligationRevision,CampaignRevision,ArchitectureRevision)}


def _immutable(value,depth=0,budget=None):
    # Closed nominal data only: an object pretending to be a frozen dataclass
    # must not receive attribute lookups or equality calls from this boundary.
    from .identity import ProjectId,EntityId,RevisionId,ContentDigest,EntityKind,DigestAlgorithm
    from .outcomes import DueStatus
    from .capability import SemanticOwner
    from .obligation import Prerequisites,CommitmentKind,DependencyMode
    from .property import AssertionKind
    from .campaign import Membership,MembershipMode
    from .architecture import Component
    primitives=(str,int,bool)
    models=(ProjectId,EntityId,RevisionId,ContentDigest,EntityRef,SemanticOwner,Prerequisites,Membership,Component)
    enums=(EntityKind,DigestAlgorithm,DecisionStatus,DueStatus,CommitmentKind,DependencyMode,AssertionKind,MembershipMode)
    if budget is None:budget=[0]
    budget[0]+=1
    if depth>64 or budget[0]>100000:raise ValueError('DRAFT_DEPTH_OR_NODE_LIMIT')
    typ=type(value)
    if value is None or typ in primitives or typ in enums:return
    if typ in (tuple,frozenset):
        if len(value)>4096:raise ValueError('DRAFT_FIELD_LIMIT')
        for v in value:_immutable(v,depth+1,budget)
        return
    if typ in models:
        for f in fields(typ):
            if f.init:_immutable(getattr(value,f.name),depth+1,budget)
        if hasattr(typ,'__post_init__'):typ.__post_init__(value)
        return
    raise TypeError('DRAFT_VALUE_NOT_IMMUTABLE')


@dataclass(frozen=True, slots=True)
class RecordDraft:
    identity: EntityRef
    supplied_fields: tuple[tuple[str,object], ...] = ()
    prior: EntityRef | None = None

    def __post_init__(self):
        if type(self.identity) is not EntityRef or self.identity.kind not in _constructors():raise TypeError('DRAFT_ENTITY_KIND_REQUIRED')
        if type(self.supplied_fields) is not tuple or len(self.supplied_fields)>128:raise TypeError('DRAFT_FIELDS_REQUIRED')
        allowed={f.name for f in fields(_constructors()[self.identity.kind]) if f.init}-{'identity'}
        seen=set()
        for pair in self.supplied_fields:
            if type(pair) is not tuple or len(pair)!=2 or type(pair[0]) is not str or pair[0] not in allowed or pair[0] in seen:
                raise ValueError('INVALID_DRAFT_FIELD')
            name,value=pair;seen.add(name);_immutable(value)
            if name=='declared_status' and value is not DecisionStatus.PROPOSED:raise ValueError('DRAFT_CANNOT_RATIFY')
        if self.prior is not None and (type(self.prior) is not EntityRef or self.prior.entity!=self.identity.entity or self.prior.revision==self.identity.revision):
            raise ValueError('DRAFT_LINEAGE_INVALID')

    @property
    def normatively_admitted(self):return False


@dataclass(frozen=True, slots=True)
class DraftInspection:
    missing_fields: tuple[str,...]
    diagnostics: tuple[Diagnostic,...]
    candidate: RecordRevision | None

    @property
    def contract_ready(self):return self.candidate is not None and not self.diagnostics and not self.missing_fields


def inspect_draft(draft: RecordDraft) -> DraftInspection:
    if type(draft) is not RecordDraft:raise TypeError('DRAFT_REQUIRED')
    RecordDraft.__post_init__(draft)
    cls=_constructors()[draft.identity.kind];provided=dict(draft.supplied_fields)
    missing=tuple(f.name for f in fields(cls) if f.init and f.name!='identity' and f.default is MISSING and f.default_factory is MISSING and f.name not in provided)
    errors=tuple(Diagnostic('DRAFT_FIELD_MISSING','$.fields.'+n,'required contract field','absent','draft does not supply this field') for n in missing)
    if missing:return DraftInspection(missing,errors,None)
    try:
        value=cls(identity=draft.identity,**provided)
        return DraftInspection((),(),value)
    except (TypeError,ValueError,AttributeError) as exc:
        return DraftInspection((),(Diagnostic('DRAFT_CONTRACT_INVALID','$.fields','complete typed contract','invalid',str(exc)),),None)


def revise_draft(draft: RecordDraft, identity: EntityRef, replacements: tuple[tuple[str,object],...],
                 *, remove: frozenset[str]=frozenset()) -> RecordDraft:
    if type(draft) is not RecordDraft or type(identity) is not EntityRef:raise TypeError('DRAFT_REQUIRED')
    if identity.entity!=draft.identity.entity or identity.revision==draft.identity.revision:raise ValueError('DRAFT_NEW_REVISION_REQUIRED')
    if type(replacements) is not tuple or type(remove) is not frozenset or any(type(x) is not str for x in remove):raise TypeError('DRAFT_REVISION_FIELDS_REQUIRED')
    values=dict(draft.supplied_fields)
    if not remove<=values.keys():raise ValueError('UNKNOWN_DRAFT_FIELD')
    for key in remove:del values[key]
    seen=set()
    for pair in replacements:
        if type(pair) is not tuple or len(pair)!=2 or type(pair[0]) is not str or pair[0] in seen:raise ValueError('DUPLICATE_DRAFT_REPLACEMENT')
        seen.add(pair[0]);values[pair[0]]=pair[1]
    return RecordDraft(identity,tuple(sorted(values.items())),draft.identity)


def complete_draft(draft: RecordDraft) -> Result[RecordRevision]:
    inspected=inspect_draft(draft)
    return Result(inspected.candidate) if inspected.contract_ready else Result(diagnostics=inspected.diagnostics)
