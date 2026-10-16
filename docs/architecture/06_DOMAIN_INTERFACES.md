# Domain model — entidades, owners, campos e interfaces públicas

**Propuesta de contrato de diseño**, no schemas de producción ni código. Cada entidad final requiere esquema versionado, validadores, tests adversarios y autoridad ratificada.

## Entidades

| Entidad | Campos mínimos propuestos | Owner | Invariante |
|---|---|---|---|
| Project | id, name, authorized_source_sets, constitution_ref, configuration, governance_policy | `src/guardian/domain/project.py` | Independent namespace; no inherited authority across projects |
| ProgramRevision | project_id, revision_id, source_universe_ref, constitution_ref, change_head | `src/guardian/program/revision.py` | Immutable admitted normative snapshot |
| SourceUniverse | source_cuts, include_rules, exclude_rules, coverage_claim_refs | `src/guardian/domain/source.py` | Completeness limited to declared authenticated sources |
| SourceRef | repository, commit, source_path, symbol_ref, object_digest, authority | `src/guardian/domain/source.py` | Mutable branch name not immutable source identity |
| ConstitutionRule | rule_id, revision, scope, predicate, authority, verification_refs | `src/guardian/domain/constitution.py` | Amendments evaluated under prior protected policy |
| ArchitectureRevision | component_refs, owner_scopes, allowed_required_forbidden_dependencies | `src/guardian/domain/architecture.py` | Observed source never replaces approved architecture |
| Decision | decision_id, revision, proposer, approver, status, rationale, effect_scope | `src/guardian/domain/authority.py` | Only externally verified approval authorizes RATIFIED |
| Objective | objective_id, revision, purpose, excluded_scope, source_refs | `src/guardian/domain/objective.py` | Not a task or implementation |
| Capability | capability_id, revision, owner, domain, behavior, contract_refs | `src/guardian/domain/capability.py` | Provider implementation not capability authority |
| Property | property_id, revision, hypotheses, guarantee, scope, required_verifications | `src/guardian/domain/property.py` | No proof by naming |
| ObligationRevision | logical_id, revision, statement, applicability, acceptance, falsification, verification, history | `src/guardian/domain/obligation.py` | No mutable completed flag; linage mandatory |
| CampaignRevision | id, revision, scope, milestone, memberships, prerequisites, closure_policy | `src/guardian/domain/campaign.py` | Membership may overlap; no duplicate authority |
| SupportProfile | candidate_ref, source_scope, features, platform, domain, consumer, budgets, verifier_policy | `src/guardian/domain/scope.py` | YES NO UNKNOWN CONFLICT conservative applicability |
| ImplementationUnit | source_symbol_refs, realized_capability_refs, kind, revision, owner | `src/guardian/domain/implementation.py` | Source file existence not functional compliance |
| PublicAPI | api_id, version, contract, consumers, compatibility_rules | `src/guardian/domain/implementation.py` | Observed API changes not auto-approved |
| VerificationSpec | verifier_id, scope, property, fixture, acceptance, falsification, resource_policy | `src/guardian/domain/verification.py` | Spec written not equivalent to run |
| ValidationRun | candidate_ref, verifier_revision, environment, inputs, result, execution_status | `src/guardian/domain/verification.py` | Execution status separate from mathematical verdict |
| EvidenceRecord | subject_revision, input_digests, output_digest, issuer, receipt, provenance | `src/guardian/domain/evidence.py` | Digest integrity is not issuer authentication |
| Claim | subject, property, profile, revision, asserted_result | `src/guardian/domain/claim.py` | No claim becomes proof via agent report |
| QualificationRecord | claim_ref, scope, policy, accepted_evidence, verdict, limitations | `src/guardian/domain/qualification.py` | Qualification only with admissible support |
| ChangeSet | change_id, base_revision, actor, operations, approvals, idempotency_key | `src/guardian/domain/change.py` | All changes atomic and traceable |
| AuditFinding | obligation_ref, candidate_ref, counterexample, required_correction, status, reviewer | `src/guardian/assurance/adversarial_review.py` | Audit requires scope and independent reviewer if mandated |
| WorkPackage | target, baseline, required_obligation_closure, forbidden_changes, verification_refs | `src/guardian/work/package_compiler.py` | Presentation never weakens immutable manifest |
| GraphRelation | relation_id, revision, kind, participants, scope, provenance, authority | `src/guardian/graph/relation_types.py` | N-ary participants with typed roles and multiplicity |

## Servicios

| Servicio | Primera campaña | Operaciones | Owner candidato |
|---|---|---|---|
| ProjectService | G-00 | `inspect`, `import_project`, `compare_revisions`, `replay` | `src/guardian/project_service.py` |
| ContractService | G-00 | `get_objective`, `get_capability`, `get_obligation`, `propose_obligation` | `src/guardian/contract_service.py` |
| ArchitectureService | G-05 | `specified`, `observed`, `check_dependencies`, `report_violations` | `src/guardian/architecture_service.py` |
| CampaignService | G-01 | `get_campaign`, `extend`, `coverage`, `closure` | `src/guardian/campaign_service.py` |
| EvolutionService | G-01 | `propose`, `validate_change`, `apply_candidate` | `src/guardian/evolution_service.py` |
| OrientationService | G-03 | `project_orientation`, `component_orientation`, `capability_orientation` | `src/guardian/orientation_service.py` |
| WorkService | G-04 | `compile_package`, `validate_package`, `submit_delivery` | `src/guardian/work_service.py` |
| ComplianceService | G-05 | `compare_source_contracts`, `evaluate_architecture`, `report_gaps` | `src/guardian/compliance_service.py` |
| AssuranceService | G-06 | `request_run`, `verify_receipt`, `evaluate_claim`, `issue_qualified_result` | `src/guardian/assurance_service.py` |
| GovernanceService | G-09 | `check_permissions`, `request_approval`, `admit`, `publish` | `src/guardian/governance_service.py` |
| GraphQuery | G-02 | `required_closure`, `support_cone`, `impact_cone`, `support_gap`, `conflicts` | `src/guardian/graph/traversal.py` |
| RepositoryIntelligence | G-07 | `inspect_source`, `extract_symbols`, `source_crosswalk`, `observed_architecture` | `src/guardian/knowledge/inventory.py` |
| AuditService | G-06 | `create_audit_scope`, `record_finding`, `review_coverage`, `close_findings` | `src/guardian/assurance/adversarial_review.py` |
| EvidenceService | G-06 | `get_evidence`, `verify_reuse`, `mark_stale`, `revoke` | `src/guardian/assurance/invalidation.py` |

## Principios de contratos
1. Los tipos son puros. Un `Claim` no es un `Certificate`, un `VerificationSpec` no es un `ValidationRun`.
2. Las acciones de norma pasan por `ChangeSet` y evaluación de la política protegida.
3. El código observado se representa con provenance; no actualiza su contrato objetivo.
4. Los servicios coordinan y los adaptadores ejecutan I/O; no nuevas fuentes de verdad.
5. La implementación futura puede ajustar nombres/granularidad por cohesión con ADR y traceability, sin reducir la capacidad funcional.

## Diseños no decididos
- Qué entidades son agregados y cuáles value objects; cuánto se guarda inline frente a references.
- Gramática exacta de ScopeExpression y contratos de verificadores opacos.
- Cómo versionar input/output schemas de runners de dominio y evidencias firmadas.
- Dónde conviene ubicar el índice de símbolos dinámicos entre Knowledge e Integration Adapter.
