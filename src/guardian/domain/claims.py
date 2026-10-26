"""G00-11 immutable assertion data; authority is supplied separately."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .identity import EntityKind,EntityRef,RevisionId
from .record_base import ref,refs,text


class AssertionDomain(str, Enum):
    NORMATIVE = 'normative'
    OBSERVED = 'observed'
    PROPOSED = 'proposed'
    INFERENCE = 'inference'


@dataclass(frozen=True, slots=True)
class Assertion:
    identity: EntityRef
    subject: EntityRef
    property_name: str
    value: str | int | bool
    domain: AssertionDomain
    scope_ref: EntityRef
    source_refs: tuple[EntityRef, ...]
    authority_ref: EntityRef | None = None
    observation_revision: RevisionId | None = None

    def __post_init__(self):
        if type(self.identity) is not EntityRef or type(self.subject) is not EntityRef:
            raise TypeError('ASSERTION_IDENTITY_REQUIRED')
        text(self.property_name,'ASSERTION_PROPERTY_REQUIRED')
        if type(self.value) not in (str,int,bool) or type(self.domain) is not AssertionDomain:
            raise TypeError('ASSERTION_VALUE_OR_DOMAIN')
        ref(self.scope_ref,EntityKind.SCOPE,'ASSERTION_SCOPE_REQUIRED')
        refs(self.source_refs,EntityKind.SOURCE,'ASSERTION_SOURCE_REQUIRED',nonempty=True)
        if self.authority_ref is not None:
            ref(self.authority_ref,EntityKind.DECISION,'ASSERTION_AUTHORITY_REQUIRED')
        if self.observation_revision is not None and type(self.observation_revision) is not RevisionId:
            raise TypeError('OBSERVATION_REVISION_REQUIRED')
        if self.domain is AssertionDomain.OBSERVED and self.observation_revision is None:
            raise ValueError('OBSERVATION_REVISION_REQUIRED')
        if any(x.project != self.identity.project for x in (self.subject,self.scope_ref) + self.source_refs
               + ((self.authority_ref,) if self.authority_ref else ())):
            raise ValueError('ASSERTION_PROJECT_MISMATCH')


