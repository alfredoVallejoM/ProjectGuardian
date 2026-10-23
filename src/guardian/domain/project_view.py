"""Read-only domain port; no application imports or authentication capability.

Membership is exact project/kind/entity/revision presence, not proof of the
entity's behavior, admission, or historical currency. B06 owns full resolution.
"""
from __future__ import annotations
from typing import Protocol, runtime_checkable
from .identity import EntityRef, ProjectId


@runtime_checkable
class ReadOnlyEntityView(Protocol):
    @property
    def project_id(self) -> ProjectId: ...

    def contains_entity(self, ref: EntityRef) -> bool: ...

    def contains_source(self, ref: EntityRef) -> bool: ...
