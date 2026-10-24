"""G00-05 explicit obligation contracts; lifecycle is not execution status."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, TYPE_CHECKING
from .project_view import ReadOnlyEntityView
from .outcomes import Result
if TYPE_CHECKING:
    from .references import TrustedEntityImports
from .record_base import ReferenceUse
from .identity import EntityKind, EntityRef
from .outcomes import DueStatus
from .capability import SemanticOwner
from .record_base import RecordRevision, ReferenceUse, text, texts, refs, ref, uses, validate_record


class CommitmentKind(str, Enum):
    EXISTENCE='existence'
    BEHAVIOR='behavior'
    CONSTITUTION='constitution'
    EXECUTION='execution'
    DEVELOPMENT='development'
    INTEGRATION='integration'
    MIGRATION='migration'


class DependencyMode(str, Enum):
    ALL='all'
    ANY='any'
    CONDITIONAL='conditional'


@dataclass(frozen=True, slots=True)
class Prerequisites:
    mode: DependencyMode
    obligations: tuple[EntityRef, ...]
    condition: EntityRef | None = None

    def __post_init__(self) -> None:
        if type(self.mode) is not DependencyMode:
            raise TypeError('PREREQUISITE_MODE_REQUIRED')
        refs(self.obligations, EntityKind.OBLIGATION, 'PREREQUISITES_REQUIRED', nonempty=True)
        if self.mode is DependencyMode.CONDITIONAL:
            ref(self.condition, EntityKind.SCOPE, 'PREREQUISITE_CONDITION_REQUIRED')
        elif self.condition is not None:
            raise ValueError('UNEXPECTED_PREREQUISITE_CONDITION')


@dataclass(frozen=True, slots=True, kw_only=True)
class ObligationRevision(RecordRevision):
    KIND: ClassVar[EntityKind] = EntityKind.OBLIGATION
    kind: CommitmentKind
    statement: str
    applicability_ref: EntityRef
    owner: SemanticOwner
    due: DueStatus
    milestone: str
    required_property_refs: tuple[EntityRef, ...]
    acceptance_contract: tuple[str, ...]
    falsification_contract: tuple[str, ...]
    verification_spec_refs: tuple[EntityRef, ...]
    objective_refs: tuple[EntityRef, ...] = ()
    architecture_rule_refs: tuple[EntityRef, ...] = ()
    consumer_contract_refs: tuple[EntityRef, ...] = ()
    resource_contract_refs: tuple[EntityRef, ...] = ()
    prerequisites: Prerequisites | None = None
    exclusions: tuple[str, ...] = ()
    lineage_refs: tuple[EntityRef, ...] = ()

    def __post_init__(self) -> None:
        RecordRevision.__post_init__(self)
        if type(self.kind) is not CommitmentKind or type(self.due) is not DueStatus:
            raise TypeError('OBLIGATION_KIND_AND_DUE_REQUIRED')
        text(self.statement, 'EMPTY_STATEMENT')
        ref(self.applicability_ref, EntityKind.SCOPE, 'APPLICABILITY_REF_REQUIRED')
        text(self.milestone, 'MILESTONE_REQUIRED')
        if type(self.owner) is not SemanticOwner or self.owner.project != self.identity.project:
            raise ValueError('INVALID_OBLIGATION_OWNER')
        refs(self.required_property_refs, EntityKind.PROPERTY, 'PROPERTY_REF_REQUIRED', nonempty=True)
        texts(self.acceptance_contract, 'REQUIRED_ACCEPTANCE_MISSING', nonempty=True)
        texts(self.falsification_contract, 'FALSIFICATION_MISSING', nonempty=True)
        refs(self.verification_spec_refs, EntityKind.VERIFICATION, 'VERIFICATION_SPEC_REQUIRED', nonempty=True)
        refs(self.objective_refs, EntityKind.OBJECTIVE, 'INVALID_OBJECTIVE_REF')
        refs(self.architecture_rule_refs, EntityKind.RULE, 'INVALID_ARCHITECTURE_RULE')
        refs(self.consumer_contract_refs, (EntityKind.CAPABILITY, EntityKind.PROPERTY), 'INVALID_CONSUMER_CONTRACT')
        refs(self.resource_contract_refs, EntityKind.PROPERTY, 'INVALID_RESOURCE_CONTRACT')
        refs(self.lineage_refs, EntityKind.OBLIGATION, 'INVALID_LINEAGE')
        texts(self.exclusions, 'INVALID_EXCLUSIONS')
        if self.prerequisites is not None and type(self.prerequisites) is not Prerequisites:
            raise TypeError('INVALID_PREREQUISITES')

    def references(self) -> tuple[ReferenceUse, ...]:
        result = RecordRevision.references(self) + (ReferenceUse('$.applicability_ref', self.applicability_ref, EntityKind.SCOPE),)
        for name in ('required_property_refs', 'verification_spec_refs', 'objective_refs',
                     'architecture_rule_refs', 'consumer_contract_refs', 'resource_contract_refs', 'lineage_refs'):
            result += uses('$.' + name, getattr(self, name))
        if self.prerequisites is not None:
            result += uses('$.prerequisites.obligations', self.prerequisites.obligations)
            if self.prerequisites.condition is not None:
                result += (ReferenceUse('$.prerequisites.condition', self.prerequisites.condition, EntityKind.SCOPE),)
        return result


def validate_obligation(obligation: object, view: ReadOnlyEntityView, *, grants: TrustedEntityImports | None = None) -> Result[ObligationRevision]:
    return validate_record(obligation, ObligationRevision, view, grants=grants)
