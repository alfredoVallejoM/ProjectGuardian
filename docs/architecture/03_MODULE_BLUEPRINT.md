# Atlas de módulos previsto: 142 ubicaciones potenciales

**No es un objetivo de crear 142 ficheros físicos.** El atlas documenta responsabilidades, owners y tests; no supone código implementado. Los módulos pueden fusionarse si conservan invariantes, consumidores y obligaciones mediante cambio aprobado.

## adapters/agents

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/adapters/agents/tool_adapter.py` | G-08 | Agent tools and typed external execution interface | `tests/adapters/test_adapters_agents_tool_adapter.py` |
| `src/guardian/adapters/agents/multi_agent_profile.py` | G-08 | Optional A0-A4 coordination and handoffs | `tests/adapters/test_adapters_agents_multi_agent_profile.py` |

## adapters/artifacts

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/adapters/artifacts/content_store.py` | G-06 | CAS interface for large artifacts with digest and retention | `tests/adapters/test_adapters_artifacts_content_store.py` |
| `src/guardian/adapters/artifacts/receipt_codec.py` | G-06 | Canonical receipt serialization and decoding | `tests/adapters/test_adapters_artifacts_receipt_codec.py` |

## adapters/attestations

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/adapters/attestations/in_toto.py` | G-06 | Read and authenticate attestation envelopes by trust policy | `tests/adapters/test_adapters_attestations_in_toto.py` |

## adapters/filesystem

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/adapters/filesystem/workspace.py` | G-07 | Candidate worktree isolation cleanup and permissions | `tests/adapters/test_adapters_filesystem_workspace.py` |
| `src/guardian/adapters/filesystem/source_files.py` | G-07 | Deterministic source read without normative writes | `tests/adapters/test_adapters_filesystem_source_files.py` |

## adapters/git

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/adapters/git/reader.py` | G-07 | Exact Git tree blob commit and immutable ref inspector | `tests/adapters/test_adapters_git_reader.py` |
| `src/guardian/adapters/git/writer.py` | G-07 | Prepare commit candidates for protected publisher | `tests/adapters/test_adapters_git_writer.py` |
| `src/guardian/adapters/git/source_importer.py` | G-07 | Import and record immutable Git SourceUniverse | `tests/adapters/test_adapters_git_source_importer.py` |

## adapters/runners

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/adapters/runners/process_runner.py` | G-06 | Subprocess execution budgets status and signed receipt request | `tests/adapters/test_adapters_runners_process_runner.py` |
| `src/guardian/adapters/runners/verifier_registry.py` | G-06 | Verified verifier descriptors versions and scopes | `tests/adapters/test_adapters_runners_verifier_registry.py` |

## adapters/source_code/cpp

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/adapters/source_code/cpp/analyzer.py` | G-07 | Clang AST macros includes ABI compile commands | `tests/adapters/test_adapters_source_code_cpp_analyzer.py` |

## adapters/source_code/lean

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/adapters/source_code/lean/analyzer.py` | G-07 | Lean declarations compilation imported axioms and proof scope | `tests/adapters/test_adapters_source_code_lean_analyzer.py` |

## adapters/source_code/python

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/adapters/source_code/python/analyzer.py` | G-07 | Python AST imports exports entrypoints and dynamic gaps | `tests/adapters/test_adapters_source_code_python_analyzer.py` |

## adapters/source_code/rust

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/adapters/source_code/rust/analyzer.py` | G-07 | Cargo crates Rust symbols traits features generated inventory | `tests/adapters/test_adapters_source_code_rust_analyzer.py` |

## adapters/sqlite

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/adapters/sqlite/schema.py` | G-02 | Relational DDL foreign keys and FTS index | `tests/adapters/test_adapters_sqlite_schema.py` |
| `src/guardian/adapters/sqlite/projector.py` | G-02 | Replay authoritative changes to deterministic read model | `tests/adapters/test_adapters_sqlite_projector.py` |
| `src/guardian/adapters/sqlite/queries.py` | G-02 | Graph and coverage querying projection adapter | `tests/adapters/test_adapters_sqlite_queries.py` |

## application

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/application/project_service.py` | G-00 | Project inspect import compare recover | `tests/application/test_application_project_service.py` |
| `src/guardian/application/contract_service.py` | G-00 | Objectives contracts obligations proposals | `tests/application/test_application_contract_service.py` |
| `src/guardian/application/architecture_service.py` | G-05 | Specified versus observed architecture inspection | `tests/application/test_application_architecture_service.py` |
| `src/guardian/application/campaign_service.py` | G-01 | Campaign membership status and closure | `tests/application/test_application_campaign_service.py` |
| `src/guardian/application/evolution_service.py` | G-01 | ChangeSet proposal validation transition | `tests/application/test_application_evolution_service.py` |
| `src/guardian/application/orientation_service.py` | G-03 | Presentation of project and component context | `tests/application/test_application_orientation_service.py` |
| `src/guardian/application/work_service.py` | G-04 | Compile validate deliver work packages | `tests/application/test_application_work_service.py` |
| `src/guardian/application/compliance_service.py` | G-05 | Code contract gap and architecture compliance | `tests/application/test_application_compliance_service.py` |
| `src/guardian/application/assurance_service.py` | G-06 | Runner results claims and qualification workflows | `tests/application/test_application_assurance_service.py` |
| `src/guardian/application/governance_service.py` | G-09 | Authorization and admission workflow | `tests/application/test_application_governance_service.py` |

## assurance

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/assurance/verification_specs.py` | G-06 | Required positive negative adversarial and formal test specifications | `tests/assurance/test_assurance_verification_specs.py` |
| `src/guardian/assurance/evidence_policy.py` | G-06 | Typed evidence sufficiency ALL ANY and scope requirements | `tests/assurance/test_assurance_evidence_policy.py` |
| `src/guardian/assurance/receipt_validation.py` | G-06 | Verify runner origin input digests and exact candidate | `tests/assurance/test_assurance_receipt_validation.py` |
| `src/guardian/assurance/qualification.py` | G-06 | Claim qualification certificates and proof policies | `tests/assurance/test_assurance_qualification.py` |
| `src/guardian/assurance/coverage_assurance.py` | G-10 | Separate specification implementation scientific material coverage | `tests/assurance/test_assurance_coverage_assurance.py` |
| `src/guardian/assurance/adversarial_review.py` | G-06 | Findings by obligation independent reviewer | `tests/assurance/test_assurance_adversarial_review.py` |
| `src/guardian/assurance/integration_assurance.py` | G-05 | Producer consumer ABI and real E2E contract | `tests/assurance/test_assurance_integration_assurance.py` |
| `src/guardian/assurance/migration_assurance.py` | G-10 | Source target oracle parity conservative migration | `tests/assurance/test_assurance_migration_assurance.py` |
| `src/guardian/assurance/resource_assurance.py` | G-06 | Budgets profiles measurable resource contracts | `tests/assurance/test_assurance_resource_assurance.py` |
| `src/guardian/assurance/invalidation.py` | G-06 | Protected dependency cone staleness and selective invalidation | `tests/assurance/test_assurance_invalidation.py` |

## bootstrap

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/bootstrap/configuration.py` | G-12 | Installation config and declared trusted sources | `tests/bootstrap/test_bootstrap_configuration.py` |
| `src/guardian/bootstrap/dependency_wiring.py` | G-12 | Explicit service and port assembly without DI framework | `tests/bootstrap/test_bootstrap_dependency_wiring.py` |
| `src/guardian/bootstrap/runtime.py` | G-12 | Start local guardian service index and protected publisher | `tests/bootstrap/test_bootstrap_runtime.py` |

## clients/web

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `clients/web/src/app/bootstrap.ts` | G-11 | Configura app y rutas; autentica principal del servidor; no alberga reglas de dominio | `clients/web/tests/app_bootstrap.test.ts` |
| `clients/web/src/api/contracts.ts` | G-11 | DTO versionados y validación de responses con revisión, scope y evidence | `clients/web/tests/api_contracts.test.ts` |
| `clients/web/src/api/guardian_client.ts` | G-11 | Cliente tipado de servicios Guardian sin acceso directo a base de datos | `clients/web/tests/api_guardian_client.test.ts` |
| `clients/web/src/state/project_scope.ts` | G-11 | Selección de proyecto, revision y SupportProfile con invalidación de cachés | `clients/web/tests/state_project_scope.test.ts` |
| `clients/web/src/shared/graph_view.tsx` | G-11 | Render de relaciones tipadas y roles n-arios con distinción proof/informational | `clients/web/tests/shared_graph_view.test.ts` |
| `clients/web/src/views/project_overview.tsx` | G-11 | Objetivos, fuentes, campañas, bloqueos, estatus y garantías por proyecto | `clients/web/tests/views_project_overview.test.ts` |
| `clients/web/src/views/contract_explorer.tsx` | G-11 | Árbol y grafo muchos-a-muchos de objetivos/capacidades/propiedades/obligaciones | `clients/web/tests/views_contract_explorer.test.ts` |
| `clients/web/src/views/architecture_explorer.tsx` | G-11 | Comparación de arquitectura especificada, observada, owner e imports | `clients/web/tests/views_architecture_explorer.test.ts` |
| `clients/web/src/views/campaign_explorer.tsx` | G-11 | Campañas, revisiones, obligaciones due y estados separados | `clients/web/tests/views_campaign_explorer.test.ts` |
| `clients/web/src/views/coverage_matrix.tsx` | G-11 | Denominadores, UNKNOWN y estados de evidencia por hito y perfil | `clients/web/tests/views_coverage_matrix.test.ts` |
| `clients/web/src/views/support_explorer.tsx` | G-11 | SupportCone, ImpactCone, ALL/ANY, SupportGap y rutas de evidencia | `clients/web/tests/views_support_explorer.test.ts` |
| `clients/web/src/views/audit_workspace.tsx` | G-11 | Hallazgos por obligación/candidato y acciones de resolución | `clients/web/tests/views_audit_workspace.test.ts` |
| `clients/web/src/views/change_history.tsx` | G-11 | Revisions, ChangeSets, revocations, diffs y dependencias | `clients/web/tests/views_change_history.test.ts` |
| `clients/web/src/views/work_package_inspector.tsx` | G-11 | WorkPackage normativo frente a orientación resumida y evidencia | `clients/web/tests/views_work_package_inspector.test.ts` |
| `clients/web/src/views/qualification_explorer.tsx` | G-11 | Claims, certificados, scope, receipts, staleness y limitaciones | `clients/web/tests/views_qualification_explorer.test.ts` |
| `clients/web/src/views/approval_queue.tsx` | G-11 | Propuestas de cambio, impacto, autoridad y approvals autenticadas | `clients/web/tests/views_approval_queue.test.ts` |

## constitution

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/constitution/evaluator.py` | G-00 | Evaluate scoped rule set with detailed diagnostics | `tests/constitution/test_constitution_evaluator.py` |
| `src/guardian/constitution/precedence.py` | G-00 | Conflict detection among sources decisions and rules | `tests/constitution/test_constitution_precedence.py` |
| `src/guardian/constitution/invariants.py` | G-00 | Versioned invariant registry without I/O | `tests/constitution/test_constitution_invariants.py` |
| `src/guardian/constitution/amendments.py` | G-09 | Amendment contract evaluated against preceding policy | `tests/constitution/test_constitution_amendments.py` |
| `src/guardian/constitution/authority_resolution.py` | G-00 | Determine required approvals and unresolved conflicts | `tests/constitution/test_constitution_authority_resolution.py` |

## domain

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/domain/identity.py` | G-00 | Nominal IDs LogicalId RevisionId Digest Alias and namespacing | `tests/domain/test_domain_identity.py` |
| `src/guardian/domain/project.py` | G-00 | Project identity authorized repositories and isolation | `tests/domain/test_domain_project.py` |
| `src/guardian/domain/source.py` | G-00 | SourceRef SourceCut SourceUniverse and historical observation | `tests/domain/test_domain_source.py` |
| `src/guardian/domain/authority.py` | G-00 | Actor Decision approval provenance and authority levels | `tests/domain/test_domain_authority.py` |
| `src/guardian/domain/constitution.py` | G-00 | RuleRevision ConstitutionRevision and conflicts | `tests/domain/test_domain_constitution.py` |
| `src/guardian/domain/architecture.py` | G-00 | Component Boundary Dependency OwnerScope ArchitectureRevision | `tests/domain/test_domain_architecture.py` |
| `src/guardian/domain/objective.py` | G-00 | ObjectiveRevision purpose and excluded scope | `tests/domain/test_domain_objective.py` |
| `src/guardian/domain/capability.py` | G-00 | CapabilityRevision owner and behavior contracts | `tests/domain/test_domain_capability.py` |
| `src/guardian/domain/property.py` | G-00 | PropertyRevision hypotheses guarantees and scope | `tests/domain/test_domain_property.py` |
| `src/guardian/domain/obligation.py` | G-00 | ObligationRevision statement applicability verification and lineage | `tests/domain/test_domain_obligation.py` |
| `src/guardian/domain/campaign.py` | G-00 | CampaignRevision memberships prerequisites closure | `tests/domain/test_domain_campaign.py` |
| `src/guardian/domain/scope.py` | G-00 | SupportProfile ScopeExpression applicability four-valued result | `tests/domain/test_domain_scope.py` |
| `src/guardian/domain/implementation.py` | G-05 | ImplementationUnit API Consumer RealizationLink | `tests/domain/test_domain_implementation.py` |
| `src/guardian/domain/verification.py` | G-06 | VerificationSpec ValidationRun typed contracts | `tests/domain/test_domain_verification.py` |
| `src/guardian/domain/evidence.py` | G-06 | EvidenceRecord ReceiptRef protected inputs | `tests/domain/test_domain_evidence.py` |
| `src/guardian/domain/claim.py` | G-06 | ClaimRevision property scope candidate | `tests/domain/test_domain_claim.py` |
| `src/guardian/domain/qualification.py` | G-06 | QualificationRecord Certificate status and conditions | `tests/domain/test_domain_qualification.py` |
| `src/guardian/domain/change.py` | G-01 | ChangeSet and typed domain commands | `tests/domain/test_domain_change.py` |
| `src/guardian/domain/outcomes.py` | G-00 | ADT PASS FAIL UNKNOWN CONFLICT NOT_APPLICABLE ResourceLimited | `tests/domain/test_domain_outcomes.py` |

## governance

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/governance/permissions.py` | G-09 | Principal capability project scope expiry authorization | `tests/governance/test_governance_permissions.py` |
| `src/guardian/governance/approval.py` | G-09 | Approval records and human ratification authority | `tests/governance/test_governance_approval.py` |
| `src/guardian/governance/candidate.py` | G-09 | Frozen candidate commit and protected read set | `tests/governance/test_governance_candidate.py` |
| `src/guardian/governance/admission.py` | G-09 | Admission gates with original obligations and policy | `tests/governance/test_governance_admission.py` |
| `src/guardian/governance/protected_policy.py` | G-09 | Read previously installed trusted constitution and verifiers | `tests/governance/test_governance_protected_policy.py` |
| `src/guardian/governance/publication.py` | G-09 | Git candidate CAS ref update and recovery | `tests/governance/test_governance_publication.py` |
| `src/guardian/governance/audit_trail.py` | G-09 | Decision provenance of admitted and blocked change | `tests/governance/test_governance_audit_trail.py` |

## graph

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/graph/relation_types.py` | G-02 | Typed n-ary relation grammar roles and cardinality | `tests/graph/test_graph_relation_types.py` |
| `src/guardian/graph/relation_validation.py` | G-02 | Check endpoints revisions provenance and applicability | `tests/graph/test_graph_relation_validation.py` |
| `src/guardian/graph/projection.py` | G-02 | Semantic architecture execution and evidence graph views | `tests/graph/test_graph_projection.py` |
| `src/guardian/graph/traversal.py` | G-02 | Scope-aware bounded graph traversals and closure | `tests/graph/test_graph_traversal.py` |
| `src/guardian/graph/dependency.py` | G-02 | ALL ANY conditional prerequisites SCC and topological scheduling | `tests/graph/test_graph_dependency.py` |
| `src/guardian/graph/support.py` | G-02 | SupportExpr SupportCone with admission of evidence paths | `tests/graph/test_graph_support.py` |
| `src/guardian/graph/impact.py` | G-02 | Inverse ImpactCone propagation and incremental invalidation | `tests/graph/test_graph_impact.py` |
| `src/guardian/graph/gaps.py` | G-02 | SupportGap structured missing evidence obligations and statuses | `tests/graph/test_graph_gaps.py` |
| `src/guardian/graph/consistency.py` | G-02 | Graph integrity ownership ambiguity and orphan validation | `tests/graph/test_graph_consistency.py` |

## interfaces/api

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/interfaces/api/contracts.py` | G-11 | HTTP transport DTO schemas and API versions | `tests/interfaces/test_interfaces_api_contracts.py` |
| `src/guardian/interfaces/api/server.py` | G-11 | Network handlers calling authorized application services | `tests/interfaces/test_interfaces_api_server.py` |

## interfaces/cli

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/interfaces/cli/main.py` | G-11 | CLI entrypoint parsing and uniform error encoding | `tests/interfaces/test_interfaces_cli_main.py` |
| `src/guardian/interfaces/cli/commands.py` | G-11 | Project contract task audit evidence and change commands | `tests/interfaces/test_interfaces_cli_commands.py` |

## interfaces/mcp

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/interfaces/mcp/tools.py` | G-11 | Tool schemas for orient prepare audit inspect and change | `tests/interfaces/test_interfaces_mcp_tools.py` |
| `src/guardian/interfaces/mcp/server.py` | G-11 | Agent tool transport principal identity integration | `tests/interfaces/test_interfaces_mcp_server.py` |

## interfaces/reporting

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/interfaces/reporting/json.py` | G-11 | Machine JSON report renderer with revision citations | `tests/interfaces/test_interfaces_reporting_json.py` |
| `src/guardian/interfaces/reporting/markdown.py` | G-11 | Human readable verified report renderer | `tests/interfaces/test_interfaces_reporting_markdown.py` |

## knowledge

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/knowledge/source_universe.py` | G-10 | Source inclusion exclusions and scope coverage | `tests/knowledge/test_knowledge_source_universe.py` |
| `src/guardian/knowledge/inventory.py` | G-07 | Observed source files symbols features interfaces and limits | `tests/knowledge/test_knowledge_inventory.py` |
| `src/guardian/knowledge/source_mapping.py` | G-07 | Intent source obligation symbol evidence crosswalk | `tests/knowledge/test_knowledge_source_mapping.py` |
| `src/guardian/knowledge/observed_architecture.py` | G-07 | Actual module API ownership and dependency projection | `tests/knowledge/test_knowledge_observed_architecture.py` |
| `src/guardian/knowledge/provenance.py` | G-03 | Authenticity and cited trace of observed statements | `tests/knowledge/test_knowledge_provenance.py` |
| `src/guardian/knowledge/reconciliation.py` | G-05 | Observed versus specified architecture drift and dispositions | `tests/knowledge/test_knowledge_reconciliation.py` |
| `src/guardian/knowledge/coverage.py` | G-10 | Explicit source coverage denominators and scope gaps | `tests/knowledge/test_knowledge_coverage.py` |

## persistence

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/persistence/events.py` | G-01 | Typed event encoding, validation and deterministic replay interpretation | `tests/persistence/test_events.py` |
| `src/guardian/persistence/snapshots.py` | G-01 | Pure ProgramSnapshot construction/diff and version stability | `tests/persistence/test_snapshots.py` |
| `src/guardian/persistence/canonicalization.py` | G-06 | Canonical JSON payload encoding and digest scope separation | `tests/persistence/test_canonicalization.py` |
| `src/guardian/persistence/recovery.py` | G-12 | Pure recovery plan from Git/ref and projection consistency observations | `tests/persistence/test_recovery.py` |
| `src/guardian/persistence/schema_registry.py` | G-01 | Versioned schema lookup, required normative feature compatibility | `tests/persistence/test_schema_registry.py` |

## ports

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/ports/project_store.py` | G-01 | Repository interface for immutable normative snapshots | `tests/ports/test_ports_project_store.py` |
| `src/guardian/ports/source_reader.py` | G-07 | Interface for exact source and provenance reads | `tests/ports/test_ports_source_reader.py` |
| `src/guardian/ports/graph_reader.py` | G-02 | Graph index query interface by profile and revision | `tests/ports/test_ports_graph_reader.py` |
| `src/guardian/ports/code_inspector.py` | G-07 | ObservedInventory extraction interface | `tests/ports/test_ports_code_inspector.py` |
| `src/guardian/ports/verifier.py` | G-06 | Run VerificationSpec against candidate environment | `tests/ports/test_ports_verifier.py` |
| `src/guardian/ports/artifact_store.py` | G-06 | Content-addressed storage interface and retention | `tests/ports/test_ports_artifact_store.py` |
| `src/guardian/ports/attestation.py` | G-06 | Trusted receipt authenticity verification interface | `tests/ports/test_ports_attestation.py` |
| `src/guardian/ports/authorization.py` | G-09 | Principal permission and approval lookup port | `tests/ports/test_ports_authorization.py` |
| `src/guardian/ports/agent_executor.py` | G-08 | Optional agent runtime interface not normative | `tests/ports/test_ports_agent_executor.py` |

## program

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/program/commands.py` | G-01 | Add Extend Refine Generalize Supersede ChangeCommitment typed commands | `tests/program/test_program_commands.py` |
| `src/guardian/program/transitions.py` | G-01 | Pure Apply ProgramSnapshot ChangeSet | `tests/program/test_program_transitions.py` |
| `src/guardian/program/revision.py` | G-01 | Lineage snapshots replay and semantic revision diffs | `tests/program/test_program_revision.py` |
| `src/guardian/program/refinement.py` | G-01 | Preservation implication proof obligations for refinement | `tests/program/test_program_refinement.py` |
| `src/guardian/program/generalization.py` | G-01 | Conservative extension old and new domains | `tests/program/test_program_generalization.py` |
| `src/guardian/program/compatibility.py` | G-01 | Schema feature compatibility and reader fail closed | `tests/program/test_program_compatibility.py` |
| `src/guardian/program/campaign_membership.py` | G-01 | Campaign obligation scope and milestone applicability | `tests/program/test_program_campaign_membership.py` |
| `src/guardian/program/evolution_validation.py` | G-01 | Non-erasure authorization impact and historical integrity | `tests/program/test_program_evolution_validation.py` |

## work

| Archivo | Campaña inicial | Responsabilidad | Prueba propuesta |
|---|---|---|---|
| `src/guardian/work/orientation.py` | G-03 | Global project and component onboarding snapshot | `tests/work/test_work_orientation.py` |
| `src/guardian/work/context_selection.py` | G-03 | Progressive retrieval with preserved full normative index | `tests/work/test_work_context_selection.py` |
| `src/guardian/work/package_compiler.py` | G-04 | Compile WorkPackage from closure across contracts | `tests/work/test_work_package_compiler.py` |
| `src/guardian/work/task_decomposition.py` | G-04 | Split packages preserving parent obligations | `tests/work/test_work_task_decomposition.py` |
| `src/guardian/work/scheduling.py` | G-04 | Ready blocked tasks and conflicting write scopes | `tests/work/test_work_scheduling.py` |
| `src/guardian/work/handoff.py` | G-08 | Transfer snapshots evidence and obligations between agents | `tests/work/test_work_handoff.py` |
| `src/guardian/work/completion.py` | G-04 | Check DeliveryManifest vs full applicable obligations | `tests/work/test_work_completion.py` |

## Criterios de creación y límites
Materializar un archivo solo cuando tenga un consumidor y un contrato desarrollado; nombres no sustituyen comportamiento. No LOC cap. Dominios y obligaciones separados de adaptadores y UI. Gatekeeper y runners no se autocertifican.

## Unicidad de autoridad
`domain` define tipos; `constitution` evalúa normas; `program` evoluciona; `graph` calcula relaciones/soporte; `assurance` decide suficiencia de evidencia; `governance` controla la publicación. CLI/API/UI/MCP nunca escriben registros normativos por su cuenta.
