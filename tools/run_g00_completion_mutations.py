"""Directed falsations of the local G00 completion candidate.

No mutation modifies the source checkout. A killed mutant must fail a selected
behavioral assertion; collection errors, skips and timeouts are invalid runs.
This is not an independent actor audit or an exhaustive mutation campaign.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

MUTANTS=(
 ('decision-body','src/guardian/domain/authority.py','a.decision == decision','a.decision.identity == decision.identity','tests/completion/test_authority_and_drafts.py::test_reusing_approval_for_different_decision_body_at_same_revision_fails'),
 ('external-quorum','src/guardian/domain/authority.py','minimum_approvals = max(minimum_approvals, *(r.minimum for r in requirements))','minimum_approvals = minimum_approvals','tests/completion/test_authority_and_drafts.py::test_external_quorum_cannot_be_weakened_by_candidate_constitution_or_parameter'),
 ('independent-author','src/guardian/domain/authority.py','independent_author = independent_author or any(r.independent_author for r in requirements)','independent_author = independent_author','tests/completion/test_authority_and_drafts.py::test_independent_author_policy_rejects_self_approval_even_with_capability_grant'),
 ('grant-scope','src/guardian/domain/authority.py','action.scope_ref in g.scope_refs','True','tests/completion/test_authority_and_drafts.py::test_grant_for_one_scope_or_target_does_not_expand_to_another'),
 ('fixed-constitution','src/guardian/constitution/evaluator.py',"if bound.get(constitution.identity)!=constitution:raise ValueError('NORMATIVE_BODY_MISMATCH')","if False:raise ValueError('NORMATIVE_BODY_MISMATCH')",'tests/constitution/test_pure_evaluator.py::test_candidate_cannot_weaken_fixed_normative_bodies_at_same_revision[constitution]'),
 ('scope-body','src/guardian/constitution/evaluator.py','if pinned != body:','if False:','tests/completion/test_initial_adversarial.py::test_pinned_rule_cannot_be_weakened_by_replacing_its_scope_body_at_same_revision'),
 ('report-denominator','src/guardian/constitution/evaluator.py',"errors.append(diagnostic('RULE_SET_INCOMPLETE','$.results','missing rule retained as unexamined'))",'pass','tests/constitution/test_pure_evaluator.py::test_collector_rejects_rule_omission_even_when_all_supplied_results_are_pass[missing]'),
 ('step-accounting','src/guardian/constitution/evaluator.py','self.steps += cost','self.steps += 0','tests/constitution/test_pure_evaluator.py::test_global_steps_are_an_upper_bound_not_a_partial_success_counter'),
 ('reader-features','src/guardian/persistence/schema_registry.py',"if set(required)-reader.reader_features:raise ValueError('UNSUPPORTED_NORMATIVE_FEATURE')","if False:raise ValueError('UNSUPPORTED_NORMATIVE_FEATURE')",'tests/persistence/test_domain_record_codec.py::test_adversarial_envelope_cannot_change_contract_or_namespace[reader-feature]'),
 ('missing-vs-default','src/guardian/persistence/schema_registry.py',"if type(raw) is not dict or set(raw)!=names:raise ValueError('INVALID_SCHEMA_SEMANTICS')","if type(raw) is not dict:raise ValueError('INVALID_SCHEMA_SEMANTICS')",'tests/persistence/test_domain_record_codec.py::test_omitted_optional_constructor_field_is_not_silently_defaulted_by_decoder'),
 ('source-provenance','src/guardian/persistence/schema_registry.py',"if source_refs is not None and source_refs!=native_sources:raise ValueError('ENVELOPE_PAYLOAD_SOURCE_MISMATCH')","if False:raise ValueError('ENVELOPE_PAYLOAD_SOURCE_MISMATCH')",'tests/persistence/test_domain_record_codec.py::test_adversarial_envelope_cannot_change_contract_or_namespace[source]'),
 ('envelope-identity','src/guardian/persistence/schema_registry.py',"if envelope_ref is not None and envelope_ref!=native:raise ValueError('ENVELOPE_PAYLOAD_IDENTITY_MISMATCH')","if False:raise ValueError('ENVELOPE_PAYLOAD_IDENTITY_MISMATCH')",'tests/persistence/test_domain_record_codec.py::test_adversarial_envelope_cannot_change_contract_or_namespace[identity]'),
 ('no-latest-wins','src/guardian/constitution/precedence.py',"return PrecedenceResolution(PrecedenceStatus.CONFLICT,(),('MISSING_APPROVED_SUPERSESSION',))","return PrecedenceResolution(PrecedenceStatus.LEFT_PRECEDES,(),('MISSING_APPROVED_SUPERSESSION',))",'tests/constitution/test_authority_conflicts.py::test_source_date_or_larger_revision_never_creates_precedence'),
 ('conflict-witnesses','src/guardian/constitution/precedence.py','return (self.left.identity,self.right.identity) + self.left.source_refs + self.right.source_refs','return (self.left.identity,) + self.left.source_refs','tests/constitution/test_authority_conflicts.py::test_opposite_normative_claims_retain_both_sources_and_conflict_without_supersession'),
 ('draft-promotion','src/guardian/domain/drafts.py',"if name=='declared_status' and value is not DecisionStatus.PROPOSED:raise ValueError('DRAFT_CANNOT_RATIFY')","if False:raise ValueError('DRAFT_CANNOT_RATIFY')",'tests/completion/test_authority_and_drafts.py::test_revising_draft_needs_new_revision_and_never_mutates_prior_or_admits_it'),
 ('conflict-pair-limit','src/guardian/constitution/precedence.py','if pairs >= policies.max_pairs:','if False:','tests/constitution/test_authority_conflicts.py::test_conflict_resource_limit_preserves_incomplete_outcome'),
)


def run(root: Path):
    rows=[]
    with tempfile.TemporaryDirectory(prefix='guardian-completion-mutations-') as temp:
        work=Path(temp)/'checkout'
        shutil.copytree(root,work,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache','.git','*.egg-info','dist','build'))
        for name,path,needle,replacement,node in MUTANTS:
            file=work/path;original=file.read_text()
            if original.count(needle)!=1:
                rows.append(dict(id=name,status='INVALID',reason='mutation target not unique'));continue
            file.write_text(original.replace(needle,replacement))
            for cache in work.rglob('__pycache__'):shutil.rmtree(cache)
            report=Path(temp)/(name+'.xml')
            try:
                process=subprocess.run([sys.executable,'-m','pytest','-q',node,'--junitxml='+str(report)],cwd=work,capture_output=True,text=True,timeout=30)
                cases=list(ET.parse(report).getroot().iter('testcase')) if report.exists() else []
                failures=[f for c in cases for f in c.findall('failure')]
                genuine=any('AssertionError' in (f.text or '') or 'DID NOT RAISE' in (f.text or '') for f in failures)
                invalid=not cases or any(c.find(t) is not None for c in cases for t in ('error','skipped'))
                status='KILLED' if process.returncode==1 and genuine and not invalid else 'SURVIVED' if process.returncode==0 else 'INVALID'
                rows.append(dict(id=name,status=status,target=node,exit_code=process.returncode,assertion_failures=len(failures)))
            except (subprocess.TimeoutExpired,ET.ParseError,OSError) as exc:
                rows.append(dict(id=name,status='INVALID',reason=type(exc).__name__))
            finally:file.write_text(original)
    return dict(scope='DIRECTED_NOT_EXHAUSTIVE_SELF_REVIEW',results=rows,
                killed=sum(x['status']=='KILLED' for x in rows),survived=sum(x['status']=='SURVIVED' for x in rows),invalid=sum(x['status']=='INVALID' for x in rows))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=run(args.root);args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
    sys.exit(0 if result['killed']==len(MUTANTS) and not result['invalid'] else 1)
