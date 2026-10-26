"""G00 verification contracts are data, never a ValidationRun or PASS."""
from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from .identity import EntityKind, EntityRef
from .record_base import RecordRevision, ReferenceUse, refs, texts, text, uses


@dataclass(frozen=True, slots=True, kw_only=True)
class VerificationSpecRevision(RecordRevision):
    KIND: ClassVar[EntityKind] = EntityKind.VERIFICATION
    method: str
    targets: tuple[EntityRef, ...]
    property_refs: tuple[EntityRef, ...]
    acceptance: tuple[str, ...]
    falsification: tuple[str, ...]
    resource_limits: tuple[tuple[str,int], ...] = ()

    def __post_init__(self):
        RecordRevision.__post_init__(self)
        text(self.method,'VERIFICATION_METHOD_REQUIRED')
        refs(self.targets,(EntityKind.OBLIGATION,EntityKind.RULE,EntityKind.CAPABILITY,EntityKind.PROPERTY),'VERIFICATION_TARGETS',nonempty=True)
        refs(self.property_refs,EntityKind.PROPERTY,'VERIFICATION_PROPERTIES')
        texts(self.acceptance,'VERIFICATION_ACCEPTANCE_REQUIRED',nonempty=True)
        texts(self.falsification,'VERIFICATION_FALSIFICATION_REQUIRED',nonempty=True)
        if type(self.resource_limits) is not tuple:
            raise TypeError('VERIFICATION_LIMITS_REQUIRED')
        for item in self.resource_limits:
            if type(item) is not tuple or len(item)!=2 or type(item[0]) is not str or type(item[1]) is not int or item[1]<1:
                raise ValueError('INVALID_VERIFICATION_LIMIT')
        if len({k for k,_ in self.resource_limits})!=len(self.resource_limits):raise ValueError('DUPLICATE_RESOURCE_LIMIT')

    def references(self) -> tuple[ReferenceUse, ...]:
        return RecordRevision.references(self)+uses('$.targets',self.targets)+uses('$.property_refs',self.property_refs)

    @property
    def material_status(self):
        return 'NOT_RUN'
