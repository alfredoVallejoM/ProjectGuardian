"""Versioned whitelist of pure built-in rule semantics, never project callbacks."""
from dataclasses import dataclass
from guardian.domain.identity import EntityKind, EntityRef, RevisionId
from guardian.domain.constitution import KNOWN_RULES
from guardian.domain.authority import diagnostic
from guardian.domain.record_base import ref
from guardian.domain.outcomes import Result


@dataclass(frozen=True, slots=True)
class TrustedRuleEvaluatorRegistry:
    revision: RevisionId
    policy_ref: EntityRef
    identifiers: frozenset[str] = KNOWN_RULES
    semantic_version: str = 'g00.rules/v1'

    def __post_init__(self):
        if type(self.revision) is not RevisionId:
            raise TypeError('REGISTRY_REVISION_REQUIRED')
        ref(self.policy_ref,(EntityKind.CONSTITUTION,EntityKind.SOURCE_POLICY),'REGISTRY_POLICY_REQUIRED')
        if (type(self.identifiers) is not frozenset or not self.identifiers
                or any(type(k) is not str or k not in KNOWN_RULES for k in self.identifiers)):
            raise ValueError('UNTRUSTED_RULE_EXECUTOR')
        if type(self.semantic_version) is not str or self.semantic_version != 'g00.rules/v1':
            raise ValueError('UNKNOWN_RULE_SEMANTICS')


def validate_rule_registry(registry: object) -> Result[TrustedRuleEvaluatorRegistry]:
    try:
        if type(registry) is not TrustedRuleEvaluatorRegistry:
            raise TypeError('UNTRUSTED_RULE_EXECUTOR')
        TrustedRuleEvaluatorRegistry.__post_init__(registry)
        return Result(registry)
    except (TypeError,ValueError,AttributeError) as exc:
        return Result(diagnostics=(diagnostic(str(exc),'$.registry','only pinned built-in semantics are executable'),))
