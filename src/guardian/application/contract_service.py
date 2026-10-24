"""Read-only inspection of actual B03 records; no mutation or certification."""
from dataclasses import dataclass
from guardian.domain.identity import EntityRef
from guardian.domain.record_base import RecordRevision, ReferenceUse
from guardian.domain.references import (RecordSnapshot, TrustedEntityImports,
    ReferenceValidation, resolve_entity, validate_references, issue)
from guardian.domain.outcomes import Result


@dataclass(frozen=True, slots=True)
class ContractInspection:
    record: RecordRevision
    references: tuple[ReferenceUse, ...]
    reference_validation: ReferenceValidation | None
    historical: bool
    imported: bool

    @property
    def scope_evaluation(self) -> str:
        return 'NOT_EVALUATED'

    @property
    def qualification(self) -> str:
        return 'NOT_CHECKED'

    @property
    def import_boundary(self) -> str:
        return 'RECORD_ONLY_NO_TRANSITIVE_GRANT' if self.imported else 'LOCAL_SNAPSHOT'


def inspect_contract(entity: EntityRef, view: RecordSnapshot,
                     grants: TrustedEntityImports | None = None) -> Result[ContractInspection]:
    if type(entity) is not EntityRef:
        return Result(diagnostics=(issue('INVALID_REFERENCE_INPUT', '$.entity', 'exact entity reference required'),))
    result = resolve_entity(entity, view, entity.kind, grants)
    if not result.ok:
        return Result(diagnostics=result.diagnostics)
    found = result.value
    # Authorization of one imported record never authorizes traversal of every
    # reference mentioned in it. Leave that separate operation visibly unchecked.
    validation = None if found.imported else validate_references((found.record,), view, grants)
    return Result(ContractInspection(found.record, found.record.references(), validation,
                                     found.historical, found.imported))
