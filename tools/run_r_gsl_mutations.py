"""Directed R01-R06 and source-to-IR mutations, never a closure certificate.

Reuse the existing assertion-aware temporary-checkout runner. Collection errors,
exceptions unrelated to assertions, skips and timeouts are invalid, not kills.
"""
from pathlib import Path
import argparse
import json
import sys
import run_g00_completion_mutations as harness

R='tests/remediation/test_r01_r06.py::'
G='tests/spec_lang/test_lc05_lc06_pipeline.py::'
MUTANTS=(
 ('R01-drop-population','src/guardian/constitution/evaluator.py','assertion_errors = _assertion_population(request)','assertion_errors = ()',R+'test_R01_pinned_normative_assertions_cannot_be_removed_to_claim_completeness[0]'),
 ('R02-unrelated-approval','src/guardian/constitution/evaluator.py','approvals, issues = _approved_exclusions(request, _meter)','approvals, issues = frozenset(a.decision.identity for a in request.authority.approvals if validate_decision(a.decision,request.authority).ok), ()',R+'test_R02_unrelated_rule_adoption_cannot_authorize_a_source_exclusion'),
 ('R03-body-check','src/guardian/constitution/evaluator.py','        _validate_project_bodies(request, bound)','        pass',R+'test_R03_source_policy_body_in_snapshot_cannot_disagree_with_request'),
 ('R04-hidden-reference','src/guardian/domain/foundation_records.py','for index, exclusion in enumerate(self.universe.excluded):','for index, exclusion in enumerate(()):',R+'test_R04_nested_exclusion_approval_is_part_of_reference_integrity'),
 ('R05-nested-context','src/guardian/persistence/schema_registry.py',"project = record.context.project_id if contextual else getattr(record, 'project_id', None)","project = getattr(record,'project_id',None)",R+'test_R05_applicability_cannot_be_encoded_with_foreign_envelope_context'),
 ('R06-first-wins','src/guardian/constitution/evaluator.py','    priority = (RuleVerdict.INVALID_INPUT, RuleVerdict.CONFLICT, RuleVerdict.FAIL, RuleVerdict.UNKNOWN, RuleVerdict.PASS)','    return rows[0]\n    priority = (RuleVerdict.INVALID_INPUT, RuleVerdict.CONFLICT, RuleVerdict.FAIL, RuleVerdict.UNKNOWN, RuleVerdict.PASS)',R+'test_R06_illegal_status_facts_preserve_all_witnesses_and_permutation_invariance'),
 ('GSL-source-population','src/guardian/spec_lang/typecheck.py','if set(bundles) != {p[0] for p in context.expected_sources} or len(bundles) != len(analyses):','if False:',G+'test_omitted_pinned_source_is_not_a_successful_subset_compilation'),
 ('GSL-required-field','src/guardian/spec_lang/typecheck.py','for name in sorted(_REQUIRED[kind] - set(names)):','for name in ():',G+'test_required_fields_are_not_defaulted[locator]'),
 ('GSL-feature','src/guardian/spec_lang/typecheck.py',"if 'v4-' + expr.tag not in context.supported_features:",'if False:',G+'test_semantic_feature_must_be_enabled_in_the_pinned_context[v4-and]'),
 ('GSL-formula-lowering','src/guardian/spec_lang/elaboration.py','return FormulaIR(value.operator,args,value.atom)',"return FormulaIR('or' if value.operator == 'and' else value.operator,args,value.atom)",G+'test_all_eight_declarations_are_resolved_typed_elaborated_and_externally_compared'),
 ('GSL-source-map','src/guardian/spec_lang/elaboration.py','if actual!=expected:','if False:',G+'test_exact_source_map_rejects_in_declaration_but_wrong_subspan[field]'),
 ('GSL-proof-promotion','src/guardian/spec_lang/elaboration.py',"proofs.append(ProofObligation('interpret:'+declaration.identity.entity.value,\n                                                      declaration.identity,ProofState.UNPROVEN))","proofs.append(ProofObligation('interpret:'+declaration.identity.entity.value,\n                                                      declaration.identity,ProofState.CHECKED_FINITE_DOMAIN))",G+'test_deferred_property_generates_unproven_obligation_preserved_by_oracle'),
)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();harness.MUTANTS=MUTANTS;result=harness.run(args.root)
    result['scope']='R01_R06_GSL_PROFILE_DIRECTED_SELF_REVIEW_NOT_INDEPENDENT'
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
    sys.exit(0 if result['killed']==len(MUTANTS) and not result['invalid'] else 1)
