"""G00-04/10: immutable constitutional contracts, distinct from their evaluator."""
from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from .identity import EntityKind, EntityRef
from .outcomes import Result
from .record_base import RecordRevision, ReferenceUse, ref, refs, text, texts, uses, validate_record
from .authority import ActionKind, exact_tuple

KNOWN_RULES = frozenset({
    'identity.kind_separation.v1', 'reference.project_isolation.v1',
    'source.cut_immutability.v1', 'normative.ratification_required.v1',
    'scope.four_valued.v1', 'status.axis_separation.v1',
    'architecture.dependencies_declared.v1', 'authority.conflict_localization.v1',
    'normative.non_erasure_precheck.v1',
})
CONSTITUTION_FEATURES = frozenset({'identity.nominal.v1','scope.four-valued.v1',
    'authority.context.v1','constitution.pure.v1','references.exact.v1'})


@dataclass(frozen=True, slots=True)
class RulePredicate:
    identifier: str
    subjects: tuple[EntityRef, ...] = ()
    expression_ref: EntityRef | None = None

    def __post_init__(self) -> None:
        text(self.identifier, 'PREDICATE_ID_REQUIRED')
        if len(self.identifier) > 160 or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789._-' for c in self.identifier):
            raise ValueError('UNSAFE_RULE_PREDICATE')
        exact_tuple(self.subjects, EntityRef, 'PREDICATE_SUBJECTS')
        if self.expression_ref is not None:
            ref(self.expression_ref, EntityKind.SCOPE, 'PREDICATE_SCOPE_REQUIRED')


@dataclass(frozen=True, slots=True)
class ApprovalRequirement:
    action: ActionKind
    scopes: frozenset[EntityRef]
    minimum: int = 1
    independent_author: bool = False

    def __post_init__(self) -> None:
        if type(self.action) is not ActionKind or type(self.scopes) is not frozenset or not self.scopes:
            raise TypeError('APPROVAL_REQUIREMENT_REQUIRED')
        if any(type(x) is not EntityRef or x.kind is not EntityKind.SCOPE for x in self.scopes):
            raise TypeError('APPROVAL_SCOPE_REQUIRED')
        if type(self.minimum) is not int or not 1 <= self.minimum <= 4096 or type(self.independent_author) is not bool:
            raise ValueError('INVALID_APPROVAL_REQUIREMENT')


@dataclass(frozen=True, slots=True, kw_only=True)
class RuleRevision(RecordRevision):
    KIND: ClassVar[EntityKind] = EntityKind.RULE
    rule_kind: str
    predicate: RulePredicate
    applicability_ref: EntityRef
    rationale: str
    semantic_version: str = 'g00.rules/v1'
    enforcement_profile: str = 'required'
    verification_refs: tuple[EntityRef, ...] = ()
    change_constraints: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        RecordRevision.__post_init__(self)
        text(self.rule_kind, 'RULE_KIND_REQUIRED')
        text(self.rationale, 'RULE_RATIONALE_REQUIRED')
        if type(self.predicate) is not RulePredicate:
            raise TypeError('UNTRUSTED_RULE_EXECUTOR')
        RulePredicate.__post_init__(self.predicate)
        ref(self.applicability_ref, EntityKind.SCOPE, 'RULE_APPLICABILITY_REQUIRED')
        if type(self.semantic_version) is not str or not self.semantic_version:
            raise TypeError('RULE_SEMANTIC_VERSION_REQUIRED')
        if type(self.enforcement_profile) is not str or self.enforcement_profile not in ('required','advisory'):
            raise ValueError('UNKNOWN_ENFORCEMENT_PROFILE')
        refs(self.verification_refs, EntityKind.VERIFICATION, 'VERIFICATION_REFS')
        texts(self.change_constraints, 'CHANGE_CONSTRAINTS')
        # Unknown identifiers remain data, so evaluation can report them rather
        # than deleting a rule from the constitution's expected population.
        if self.rule_kind != self.predicate.identifier:
            raise ValueError('RULE_PREDICATE_MISMATCH')

    def references(self) -> tuple[ReferenceUse, ...]:
        out = (RecordRevision.references(self)
               + (ReferenceUse('$.applicability_ref', self.applicability_ref, EntityKind.SCOPE),)
               + uses('$.predicate.subjects', self.predicate.subjects)
               + uses('$.verification_refs', self.verification_refs))
        if self.predicate.expression_ref is not None:
            out += (ReferenceUse('$.predicate.expression_ref', self.predicate.expression_ref, EntityKind.SCOPE),)
        return out


@dataclass(frozen=True, slots=True, kw_only=True)
class ConstitutionRevision(RecordRevision):
    KIND: ClassVar[EntityKind] = EntityKind.CONSTITUTION
    rule_refs: tuple[EntityRef, ...]
    decision_refs: tuple[EntityRef, ...]
    source_universe_ref: EntityRef
    policy_ref: EntityRef
    required_normative_features: frozenset[str] = CONSTITUTION_FEATURES
    approval_requirements: tuple[ApprovalRequirement, ...] = ()
    precondition_refs: tuple[EntityRef, ...] = ()
    exclusions: tuple[str, ...] = ()
    semantic_version: str = 'g00.constitution/v1'

    def __post_init__(self) -> None:
        RecordRevision.__post_init__(self)
        refs(self.rule_refs, EntityKind.RULE, 'CONSTITUTION_RULES_REQUIRED', nonempty=True)
        refs(self.decision_refs, EntityKind.DECISION, 'CONSTITUTION_DECISIONS')
        refs(self.precondition_refs, EntityKind.SCOPE, 'CONSTITUTION_PRECONDITIONS')
        ref(self.source_universe_ref, EntityKind.SOURCE_UNIVERSE, 'CONSTITUTION_UNIVERSE_REQUIRED')
        ref(self.policy_ref, (EntityKind.CONSTITUTION,EntityKind.SOURCE_POLICY), 'CONSTITUTION_POLICY_REQUIRED')
        if any(x.project != self.identity.project for x in self.rule_refs + self.decision_refs + self.precondition_refs + (self.source_universe_ref,self.policy_ref)):
            raise ValueError('FOREIGN_CONSTITUTION_RULE')
        if len({x.entity for x in self.rule_refs}) != len(self.rule_refs):
            raise ValueError('DUPLICATE_RULE_ID')
        exact_tuple(self.approval_requirements, ApprovalRequirement, 'APPROVAL_REQUIREMENTS')
        if any(s.project != self.identity.project for q in self.approval_requirements for s in q.scopes):
            raise ValueError('APPROVAL_SCOPE_PROJECT_MISMATCH')
        if type(self.required_normative_features) is not frozenset or not self.required_normative_features or any(type(x) is not str for x in self.required_normative_features):
            raise TypeError('NORMATIVE_FEATURES_REQUIRED')
        texts(self.exclusions, 'INVALID_CONSTITUTION_EXCLUSIONS')
        text(self.semantic_version, 'CONSTITUTION_VERSION_REQUIRED')

    def references(self) -> tuple[ReferenceUse, ...]:
        out = RecordRevision.references(self) + uses('$.rule_refs',self.rule_refs) + uses('$.decision_refs',self.decision_refs)
        out += uses('$.precondition_refs',self.precondition_refs)
        out += (ReferenceUse('$.policy_ref',self.policy_ref,self.policy_ref.kind),
                ReferenceUse('$.source_universe_ref',self.source_universe_ref,EntityKind.SOURCE_UNIVERSE))
        for index, requirement in enumerate(self.approval_requirements):
            out += uses(f'$.approval_requirements[{index}].scopes',tuple(sorted(requirement.scopes,key=lambda r:r.entity.value)))
        return out


def validate_rule(rule: object) -> Result[RuleRevision]:
    return validate_record(rule, RuleRevision)


def validate_constitution(revision: object, view) -> Result[ConstitutionRevision]:
    basic = validate_record(revision, ConstitutionRevision, view)
    if not basic.ok:
        return basic
    from .authority import diagnostic
    from .references import validate_references
    errors = []
    if revision.semantic_version != 'g00.constitution/v1':
        errors.append(diagnostic('UNSUPPORTED_CONSTITUTION_VERSION','$.semantic_version','no implicit migration'))
    if revision.required_normative_features - CONSTITUTION_FEATURES:
        errors.append(diagnostic('UNSUPPORTED_NORMATIVE_FEATURE','$.required_normative_features','unknown requirements retained'))
    errors.extend(validate_references((revision,),view).diagnostics)
    return Result(diagnostics=tuple(errors)) if errors else Result(revision)
