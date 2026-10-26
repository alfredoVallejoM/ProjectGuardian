"""Source-backed refinement clause, not a proof of its parent's sufficiency.

The explicit body closes the GSL relation-reference boundary. A label or binding
alone still cannot fabricate a clause; sources and the exact parent are required.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from .identity import EntityKind, EntityRef
from .record_base import RecordRevision, ReferenceUse, ref, refs, text, texts, uses


@dataclass(frozen=True, slots=True, kw_only=True)
class ClauseRevision(RecordRevision):
    KIND: ClassVar[EntityKind] = EntityKind.CLAUSE
    parent_ref: EntityRef
    source_item: str
    statement: str
    acceptance: tuple[str, ...]
    falsification: tuple[str, ...]
    verification_spec_refs: tuple[EntityRef, ...] = ()

    def __post_init__(self) -> None:
        RecordRevision.__post_init__(self)
        ref(self.parent_ref, EntityKind.OBLIGATION, 'CLAUSE_PARENT_REQUIRED')
        text(self.source_item, 'CLAUSE_SOURCE_ITEM_REQUIRED')
        text(self.statement, 'CLAUSE_STATEMENT_REQUIRED')
        texts(self.acceptance, 'CLAUSE_ACCEPTANCE_REQUIRED', nonempty=True)
        texts(self.falsification, 'CLAUSE_FALSIFICATION_REQUIRED', nonempty=True)
        refs(self.verification_spec_refs, EntityKind.VERIFICATION, 'CLAUSE_VERIFICATION_KIND')

    def references(self) -> tuple[ReferenceUse, ...]:
        return (RecordRevision.references(self)
                + (ReferenceUse('$.parent_ref', self.parent_ref, EntityKind.OBLIGATION),)
                + uses('$.verification_spec_refs', self.verification_spec_refs))

    @property
    def refinement_sufficiency(self) -> str:
        return 'NOT_PROVEN'
