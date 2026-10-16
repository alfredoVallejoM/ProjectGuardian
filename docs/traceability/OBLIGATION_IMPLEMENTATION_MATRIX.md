# Matriz por obligación: implementación, propietario y pruebas

**163 filas con asignación de diseño a módulos concretos; ninguna implementación ni test desarrollado.** El test objetivo por obligación es un *identificador de trazabilidad*, no una orden de crear 163 ficheros unitarios. Durante la revisión arquitectónica se decidirá la agrupación por comportamiento y el diseño de los tests efectivos.

| Obligación | Título | Módulos responsables propuestos | Test de contrato | Estado |
|---|---|---|---|---|
| `G00-01` | Identidades tipadas | `src/guardian/domain/identity.py` | `tests/campaign_contracts/G-00/test_G00_01.py` | NOT_IMPLEMENTED |
| `G00-02` | Project y aislamiento | `src/guardian/domain/project.py` | `tests/campaign_contracts/G-00/test_G00_02.py` | NOT_IMPLEMENTED |
| `G00-03` | SourceUniverse | `src/guardian/domain/source.py` | `tests/campaign_contracts/G-00/test_G00_03.py` | NOT_IMPLEMENTED |
| `G00-04` | Constitución y decisión | `src/guardian/domain/constitution.py`, `src/guardian/domain/authority.py`, `src/guardian/constitution/authority_resolution.py` | `tests/campaign_contracts/G-00/test_G00_04.py` | NOT_IMPLEMENTED |
| `G00-05` | Ontología de compromisos | `src/guardian/domain/objective.py`, `src/guardian/domain/capability.py`, `src/guardian/domain/property.py`, `src/guardian/domain/obligation.py` | `tests/campaign_contracts/G-00/test_G00_05.py` | NOT_IMPLEMENTED |
| `G00-06` | Scope y applicability | `src/guardian/domain/scope.py`, `src/guardian/constitution/evaluator.py` | `tests/campaign_contracts/G-00/test_G00_06.py` | NOT_IMPLEMENTED |
| `G00-07` | Estados separados | `src/guardian/domain/outcomes.py`, `src/guardian/domain/qualification.py` | `tests/campaign_contracts/G-00/test_G00_07.py` | NOT_IMPLEMENTED |
| `G00-08` | Integridad de referencias | `src/guardian/domain/identity.py`, `src/guardian/domain/source.py` | `tests/campaign_contracts/G-00/test_G00_08.py` | NOT_IMPLEMENTED |
| `G00-09` | Esquemas versionados | `src/guardian/persistence/schema_registry.py` | `tests/campaign_contracts/G-00/test_G00_09.py` | NOT_IMPLEMENTED |
| `G00-10` | Evaluador constitucional puro | `src/guardian/constitution/evaluator.py` | `tests/campaign_contracts/G-00/test_G00_10.py` | NOT_IMPLEMENTED |
| `G00-11` | Conflictos de autoridad | `src/guardian/constitution/precedence.py` | `tests/campaign_contracts/G-00/test_G00_11.py` | NOT_IMPLEMENTED |
| `G00-12` | Tests fundamentales | `src/guardian/constitution/invariants.py` | `tests/campaign_contracts/G-00/test_G00_12.py` | NOT_IMPLEMENTED |
| `G01-01` | ChangeSet tipado | `src/guardian/program/commands.py`, `src/guardian/domain/change.py` | `tests/campaign_contracts/G-01/test_G01_01.py` | NOT_IMPLEMENTED |
| `G01-02` | Añadir obligaciones y campañas | `src/guardian/program/commands.py`, `src/guardian/program/transitions.py` | `tests/campaign_contracts/G-01/test_G01_02.py` | NOT_IMPLEMENTED |
| `G01-03` | Extender campaña | `src/guardian/program/campaign_membership.py`, `src/guardian/program/transitions.py` | `tests/campaign_contracts/G-01/test_G01_03.py` | NOT_IMPLEMENTED |
| `G01-04` | Refinar obligación | `src/guardian/program/refinement.py` | `tests/campaign_contracts/G-01/test_G01_04.py` | NOT_IMPLEMENTED |
| `G01-05` | Generalizar contrato | `src/guardian/program/generalization.py` | `tests/campaign_contracts/G-01/test_G01_05.py` | NOT_IMPLEMENTED |
| `G01-06` | Sustituir y retirar | `src/guardian/program/commands.py`, `src/guardian/program/revision.py` | `tests/campaign_contracts/G-01/test_G01_06.py` | NOT_IMPLEMENTED |
| `G01-07` | Revisiones y replay | `src/guardian/persistence/events.py`, `src/guardian/persistence/snapshots.py` | `tests/campaign_contracts/G-01/test_G01_07.py` | NOT_IMPLEMENTED |
| `G01-08` | Concurrencia optimista | `src/guardian/program/evolution_validation.py` | `tests/campaign_contracts/G-01/test_G01_08.py` | NOT_IMPLEMENTED |
| `G01-09` | Estados event-derived | `src/guardian/program/transitions.py` | `tests/campaign_contracts/G-01/test_G01_09.py` | NOT_IMPLEMENTED |
| `G01-10` | Atomicidad de aplicación | `src/guardian/program/transitions.py` | `tests/campaign_contracts/G-01/test_G01_10.py` | NOT_IMPLEMENTED |
| `G01-11` | Diff semántico | `src/guardian/program/revision.py` | `tests/campaign_contracts/G-01/test_G01_11.py` | NOT_IMPLEMENTED |
| `G01-12` | Ampliación postcertificación | `src/guardian/program/compatibility.py`, `src/guardian/program/campaign_membership.py` | `tests/campaign_contracts/G-01/test_G01_12.py` | NOT_IMPLEMENTED |
| `G02-01` | Nodos y relaciones tipados | `src/guardian/graph/relation_types.py`, `src/guardian/graph/relation_validation.py` | `tests/campaign_contracts/G-02/test_G02_01.py` | NOT_IMPLEMENTED |
| `G02-02` | N-aridad y multiplicidad | `src/guardian/graph/relation_validation.py` | `tests/campaign_contracts/G-02/test_G02_02.py` | NOT_IMPLEMENTED |
| `G02-03` | Registro de relaciones | `src/guardian/graph/relation_types.py` | `tests/campaign_contracts/G-02/test_G02_03.py` | NOT_IMPLEMENTED |
| `G02-04` | Owner semántico | `src/guardian/graph/consistency.py` | `tests/campaign_contracts/G-02/test_G02_04.py` | NOT_IMPLEMENTED |
| `G02-05` | Grafo arquitectónico | `src/guardian/graph/projection.py` | `tests/campaign_contracts/G-02/test_G02_05.py` | NOT_IMPLEMENTED |
| `G02-06` | Grafo de ejecución | `src/guardian/graph/dependency.py` | `tests/campaign_contracts/G-02/test_G02_06.py` | NOT_IMPLEMENTED |
| `G02-07` | ALL ANY condicional | `src/guardian/graph/dependency.py`, `src/guardian/graph/support.py` | `tests/campaign_contracts/G-02/test_G02_07.py` | NOT_IMPLEMENTED |
| `G02-08` | SupportCone | `src/guardian/graph/support.py` | `tests/campaign_contracts/G-02/test_G02_08.py` | NOT_IMPLEMENTED |
| `G02-09` | ImpactCone | `src/guardian/graph/impact.py` | `tests/campaign_contracts/G-02/test_G02_09.py` | NOT_IMPLEMENTED |
| `G02-10` | SupportGap | `src/guardian/graph/gaps.py` | `tests/campaign_contracts/G-02/test_G02_10.py` | NOT_IMPLEMENTED |
| `G02-11` | Proyecciones reconstruibles | `src/guardian/adapters/sqlite/projector.py`, `src/guardian/graph/projection.py` | `tests/campaign_contracts/G-02/test_G02_11.py` | NOT_IMPLEMENTED |
| `G02-12` | Tests de grafo y escala | `src/guardian/graph/consistency.py`, `src/guardian/graph/traversal.py` | `tests/campaign_contracts/G-02/test_G02_12.py` | NOT_IMPLEMENTED |
| `G03-01` | Orientación global | `src/guardian/work/orientation.py` | `tests/campaign_contracts/G-03/test_G03_01.py` | NOT_IMPLEMENTED |
| `G03-02` | Orientación de componente | `src/guardian/work/orientation.py` | `tests/campaign_contracts/G-03/test_G03_02.py` | NOT_IMPLEMENTED |
| `G03-03` | Orientación de capacidad | `src/guardian/work/orientation.py` | `tests/campaign_contracts/G-03/test_G03_03.py` | NOT_IMPLEMENTED |
| `G03-04` | Fuentes verificables | `src/guardian/knowledge/provenance.py` | `tests/campaign_contracts/G-03/test_G03_04.py` | NOT_IMPLEMENTED |
| `G03-05` | Vistas derivadas | `src/guardian/work/orientation.py`, `src/guardian/interfaces/reporting/markdown.py` | `tests/campaign_contracts/G-03/test_G03_05.py` | NOT_IMPLEMENTED |
| `G03-06` | Contexto progresivo | `src/guardian/work/context_selection.py` | `tests/campaign_contracts/G-03/test_G03_06.py` | NOT_IMPLEMENTED |
| `G03-07` | Explicar estado observado | `src/guardian/application/orientation_service.py` | `tests/campaign_contracts/G-03/test_G03_07.py` | NOT_IMPLEMENTED |
| `G03-08` | Conflictos y desconocidos | `src/guardian/knowledge/reconciliation.py`, `src/guardian/work/orientation.py` | `tests/campaign_contracts/G-03/test_G03_08.py` | NOT_IMPLEMENTED |
| `G03-09` | Navegación objetivos | `src/guardian/work/orientation.py`, `src/guardian/knowledge/source_mapping.py` | `tests/campaign_contracts/G-03/test_G03_09.py` | NOT_IMPLEMENTED |
| `G03-10` | Admisión de un agente nuevo | `src/guardian/work/orientation.py`, `src/guardian/work/context_selection.py` | `tests/campaign_contracts/G-03/test_G03_10.py` | NOT_IMPLEMENTED |
| `G04-01` | Unidad de trabajo | `src/guardian/work/package_compiler.py` | `tests/campaign_contracts/G-04/test_G04_01.py` | NOT_IMPLEMENTED |
| `G04-02` | Closure de obligaciones | `src/guardian/work/package_compiler.py`, `src/guardian/graph/traversal.py` | `tests/campaign_contracts/G-04/test_G04_02.py` | NOT_IMPLEMENTED |
| `G04-03` | Constitución aplicable | `src/guardian/work/package_compiler.py`, `src/guardian/constitution/evaluator.py` | `tests/campaign_contracts/G-04/test_G04_03.py` | NOT_IMPLEMENTED |
| `G04-04` | Prerequisitos | `src/guardian/work/scheduling.py`, `src/guardian/graph/dependency.py` | `tests/campaign_contracts/G-04/test_G04_04.py` | NOT_IMPLEMENTED |
| `G04-05` | Consumidores | `src/guardian/work/package_compiler.py`, `src/guardian/knowledge/source_mapping.py` | `tests/campaign_contracts/G-04/test_G04_05.py` | NOT_IMPLEMENTED |
| `G04-06` | Fuente y migración | `src/guardian/work/package_compiler.py`, `src/guardian/knowledge/source_universe.py` | `tests/campaign_contracts/G-04/test_G04_06.py` | NOT_IMPLEMENTED |
| `G04-07` | Pruebas y falsaciones | `src/guardian/work/package_compiler.py`, `src/guardian/assurance/verification_specs.py` | `tests/campaign_contracts/G-04/test_G04_07.py` | NOT_IMPLEMENTED |
| `G04-08` | Manifest y explicación | `src/guardian/work/package_compiler.py`, `src/guardian/work/context_selection.py` | `tests/campaign_contracts/G-04/test_G04_08.py` | NOT_IMPLEMENTED |
| `G04-09` | Subtrabajos completos | `src/guardian/work/task_decomposition.py` | `tests/campaign_contracts/G-04/test_G04_09.py` | NOT_IMPLEMENTED |
| `G04-10` | Revisión durante trabajo | `src/guardian/work/completion.py` | `tests/campaign_contracts/G-04/test_G04_10.py` | NOT_IMPLEMENTED |
| `G04-11` | Concurrencia | `src/guardian/work/scheduling.py` | `tests/campaign_contracts/G-04/test_G04_11.py` | NOT_IMPLEMENTED |
| `G04-12` | Validador independiente | `src/guardian/work/completion.py`, `src/guardian/work/package_compiler.py` | `tests/campaign_contracts/G-04/test_G04_12.py` | NOT_IMPLEMENTED |
| `G05-01` | Arquitecturas separadas | `src/guardian/knowledge/observed_architecture.py`, `src/guardian/knowledge/reconciliation.py` | `tests/campaign_contracts/G-05/test_G05_01.py` | NOT_IMPLEMENTED |
| `G05-02` | Componentes y responsabilidades | `src/guardian/knowledge/reconciliation.py` | `tests/campaign_contracts/G-05/test_G05_02.py` | NOT_IMPLEMENTED |
| `G05-03` | Dependencias | `src/guardian/knowledge/observed_architecture.py` | `tests/campaign_contracts/G-05/test_G05_03.py` | NOT_IMPLEMENTED |
| `G05-04` | Ownership | `src/guardian/graph/consistency.py`, `src/guardian/knowledge/reconciliation.py` | `tests/campaign_contracts/G-05/test_G05_04.py` | NOT_IMPLEMENTED |
| `G05-05` | API consumers | `src/guardian/knowledge/source_mapping.py`, `src/guardian/knowledge/observed_architecture.py` | `tests/campaign_contracts/G-05/test_G05_05.py` | NOT_IMPLEMENTED |
| `G05-06` | Capability implementation | `src/guardian/knowledge/source_mapping.py` | `tests/campaign_contracts/G-05/test_G05_06.py` | NOT_IMPLEMENTED |
| `G05-07` | Properties verification | `src/guardian/assurance/verification_specs.py`, `src/guardian/knowledge/reconciliation.py` | `tests/campaign_contracts/G-05/test_G05_07.py` | NOT_IMPLEMENTED |
| `G05-08` | Partial contracts | `src/guardian/knowledge/reconciliation.py` | `tests/campaign_contracts/G-05/test_G05_08.py` | NOT_IMPLEMENTED |
| `G05-09` | Regresiones | `src/guardian/assurance/invalidation.py` | `tests/campaign_contracts/G-05/test_G05_09.py` | NOT_IMPLEMENTED |
| `G05-10` | Extensibilidad | `src/guardian/knowledge/reconciliation.py`, `src/guardian/graph/consistency.py` | `tests/campaign_contracts/G-05/test_G05_10.py` | NOT_IMPLEMENTED |
| `G05-11` | Integración real | `src/guardian/assurance/integration_assurance.py` | `tests/campaign_contracts/G-05/test_G05_11.py` | NOT_IMPLEMENTED |
| `G05-12` | Informe gaps | `src/guardian/knowledge/reconciliation.py`, `src/guardian/graph/gaps.py` | `tests/campaign_contracts/G-05/test_G05_12.py` | NOT_IMPLEMENTED |
| `G06-01` | VerificationSpec | `src/guardian/assurance/verification_specs.py` | `tests/campaign_contracts/G-06/test_G06_01.py` | NOT_IMPLEMENTED |
| `G06-02` | ValidationRun | `src/guardian/domain/verification.py`, `src/guardian/adapters/runners/process_runner.py` | `tests/campaign_contracts/G-06/test_G06_02.py` | NOT_IMPLEMENTED |
| `G06-03` | Claim Evidence | `src/guardian/domain/claim.py`, `src/guardian/domain/evidence.py` | `tests/campaign_contracts/G-06/test_G06_03.py` | NOT_IMPLEMENTED |
| `G06-04` | Suficiencia | `src/guardian/assurance/evidence_policy.py` | `tests/campaign_contracts/G-06/test_G06_04.py` | NOT_IMPLEMENTED |
| `G06-05` | Certificados scoped | `src/guardian/assurance/qualification.py` | `tests/campaign_contracts/G-06/test_G06_05.py` | NOT_IMPLEMENTED |
| `G06-06` | Support freshness | `src/guardian/assurance/invalidation.py`, `src/guardian/graph/support.py` | `tests/campaign_contracts/G-06/test_G06_06.py` | NOT_IMPLEMENTED |
| `G06-07` | Invalidación | `src/guardian/assurance/invalidation.py` | `tests/campaign_contracts/G-06/test_G06_07.py` | NOT_IMPLEMENTED |
| `G06-08` | Runner authenticity | `src/guardian/assurance/receipt_validation.py`, `src/guardian/adapters/attestations/in_toto.py` | `tests/campaign_contracts/G-06/test_G06_08.py` | NOT_IMPLEMENTED |
| `G06-09` | Auditoría granular | `src/guardian/assurance/adversarial_review.py` | `tests/campaign_contracts/G-06/test_G06_09.py` | NOT_IMPLEMENTED |
| `G06-10` | Independencia | `src/guardian/assurance/adversarial_review.py`, `src/guardian/governance/permissions.py` | `tests/campaign_contracts/G-06/test_G06_10.py` | NOT_IMPLEMENTED |
| `G06-11` | Estados ortogonales | `src/guardian/domain/outcomes.py`, `src/guardian/assurance/qualification.py` | `tests/campaign_contracts/G-06/test_G06_11.py` | NOT_IMPLEMENTED |
| `G06-12` | Suite hostile certificates | `src/guardian/assurance/receipt_validation.py`, `src/guardian/assurance/qualification.py` | `tests/campaign_contracts/G-06/test_G06_12.py` | NOT_IMPLEMENTED |
| `G07-01` | Git immutable refs | `src/guardian/adapters/git/reader.py`, `src/guardian/adapters/git/source_importer.py` | `tests/campaign_contracts/G-07/test_G07_01.py` | NOT_IMPLEMENTED |
| `G07-02` | Importer existente | `src/guardian/adapters/git/source_importer.py`, `src/guardian/knowledge/source_mapping.py` | `tests/campaign_contracts/G-07/test_G07_02.py` | NOT_IMPLEMENTED |
| `G07-03` | Rust Cargo | `src/guardian/adapters/source_code/rust/analyzer.py` | `tests/campaign_contracts/G-07/test_G07_03.py` | NOT_IMPLEMENTED |
| `G07-04` | C++ toolchain | `src/guardian/adapters/source_code/cpp/analyzer.py` | `tests/campaign_contracts/G-07/test_G07_04.py` | NOT_IMPLEMENTED |
| `G07-05` | Python AST | `src/guardian/adapters/source_code/python/analyzer.py` | `tests/campaign_contracts/G-07/test_G07_05.py` | NOT_IMPLEMENTED |
| `G07-06` | Lean formal | `src/guardian/adapters/source_code/lean/analyzer.py` | `tests/campaign_contracts/G-07/test_G07_06.py` | NOT_IMPLEMENTED |
| `G07-07` | Runner adapter | `src/guardian/adapters/runners/process_runner.py` | `tests/campaign_contracts/G-07/test_G07_07.py` | NOT_IMPLEMENTED |
| `G07-08` | Cross repo policy | `src/guardian/knowledge/source_universe.py`, `src/guardian/knowledge/provenance.py` | `tests/campaign_contracts/G-07/test_G07_08.py` | NOT_IMPLEMENTED |
| `G07-09` | Multi-repository | `src/guardian/adapters/git/source_importer.py` | `tests/campaign_contracts/G-07/test_G07_09.py` | NOT_IMPLEMENTED |
| `G07-10` | Import incremental | `src/guardian/knowledge/inventory.py`, `src/guardian/adapters/git/source_importer.py` | `tests/campaign_contracts/G-07/test_G07_10.py` | NOT_IMPLEMENTED |
| `G07-11` | Unsupported constructs | `src/guardian/knowledge/inventory.py` | `tests/campaign_contracts/G-07/test_G07_11.py` | NOT_IMPLEMENTED |
| `G07-12` | Conformance tests | `src/guardian/adapters/git/reader.py`, `src/guardian/knowledge/source_mapping.py` | `tests/campaign_contracts/G-07/test_G07_12.py` | NOT_IMPLEMENTED |
| `G08-01` | Tool contracts | `src/guardian/interfaces/mcp/tools.py`, `src/guardian/adapters/agents/tool_adapter.py` | `tests/campaign_contracts/G-08/test_G08_01.py` | NOT_IMPLEMENTED |
| `G08-02` | Orient inicial | `src/guardian/interfaces/mcp/tools.py`, `src/guardian/work/orientation.py` | `tests/campaign_contracts/G-08/test_G08_02.py` | NOT_IMPLEMENTED |
| `G08-03` | Retrieval progresiva | `src/guardian/work/context_selection.py`, `src/guardian/adapters/agents/tool_adapter.py` | `tests/campaign_contracts/G-08/test_G08_03.py` | NOT_IMPLEMENTED |
| `G08-04` | Immutable package | `src/guardian/work/package_compiler.py`, `src/guardian/adapters/agents/tool_adapter.py` | `tests/campaign_contracts/G-08/test_G08_04.py` | NOT_IMPLEMENTED |
| `G08-05` | Consulta durante trabajo | `src/guardian/interfaces/mcp/tools.py`, `src/guardian/graph/traversal.py` | `tests/campaign_contracts/G-08/test_G08_05.py` | NOT_IMPLEMENTED |
| `G08-06` | Delivery manifest | `src/guardian/work/completion.py`, `src/guardian/adapters/agents/tool_adapter.py` | `tests/campaign_contracts/G-08/test_G08_06.py` | NOT_IMPLEMENTED |
| `G08-07` | Monoagente | `src/guardian/adapters/agents/tool_adapter.py` | `tests/campaign_contracts/G-08/test_G08_07.py` | NOT_IMPLEMENTED |
| `G08-08` | Multiagente opcional | `src/guardian/adapters/agents/multi_agent_profile.py` | `tests/campaign_contracts/G-08/test_G08_08.py` | NOT_IMPLEMENTED |
| `G08-09` | Handoffs | `src/guardian/work/handoff.py`, `src/guardian/adapters/agents/multi_agent_profile.py` | `tests/campaign_contracts/G-08/test_G08_09.py` | NOT_IMPLEMENTED |
| `G08-10` | Independencia efectiva | `src/guardian/assurance/adversarial_review.py`, `src/guardian/adapters/agents/multi_agent_profile.py` | `tests/campaign_contracts/G-08/test_G08_10.py` | NOT_IMPLEMENTED |
| `G08-11` | Model switching | `src/guardian/adapters/agents/tool_adapter.py` | `tests/campaign_contracts/G-08/test_G08_11.py` | NOT_IMPLEMENTED |
| `G09-01` | Permission capabilities | `src/guardian/governance/permissions.py` | `tests/campaign_contracts/G-09/test_G09_01.py` | NOT_IMPLEMENTED |
| `G09-02` | Protected policy | `src/guardian/governance/protected_policy.py` | `tests/campaign_contracts/G-09/test_G09_02.py` | NOT_IMPLEMENTED |
| `G09-03` | Old-rule amendments | `src/guardian/constitution/amendments.py`, `src/guardian/governance/protected_policy.py` | `tests/campaign_contracts/G-09/test_G09_03.py` | NOT_IMPLEMENTED |
| `G09-04` | Path and scope | `src/guardian/governance/candidate.py`, `src/guardian/governance/admission.py` | `tests/campaign_contracts/G-09/test_G09_04.py` | NOT_IMPLEMENTED |
| `G09-05` | Candidate exactness | `src/guardian/governance/candidate.py`, `src/guardian/governance/admission.py` | `tests/campaign_contracts/G-09/test_G09_05.py` | NOT_IMPLEMENTED |
| `G09-06` | Runner trust | `src/guardian/assurance/receipt_validation.py`, `src/guardian/governance/admission.py` | `tests/campaign_contracts/G-09/test_G09_06.py` | NOT_IMPLEMENTED |
| `G09-07` | Verifier registry | `src/guardian/adapters/runners/verifier_registry.py` | `tests/campaign_contracts/G-09/test_G09_07.py` | NOT_IMPLEMENTED |
| `G09-08` | Isolation budgets | `src/guardian/adapters/runners/process_runner.py`, `src/guardian/governance/admission.py` | `tests/campaign_contracts/G-09/test_G09_08.py` | NOT_IMPLEMENTED |
| `G09-09` | Git CAS | `src/guardian/governance/publication.py` | `tests/campaign_contracts/G-09/test_G09_09.py` | NOT_IMPLEMENTED |
| `G09-10` | Constitution changes | `src/guardian/constitution/amendments.py`, `src/guardian/governance/approval.py` | `tests/campaign_contracts/G-09/test_G09_10.py` | NOT_IMPLEMENTED |
| `G09-11` | Crash recovery | `src/guardian/persistence/recovery.py`, `src/guardian/governance/publication.py` | `tests/campaign_contracts/G-09/test_G09_11.py` | NOT_IMPLEMENTED |
| `G09-12` | Adversarial gatekeeper | `src/guardian/governance/admission.py`, `src/guardian/governance/audit_trail.py` | `tests/campaign_contracts/G-09/test_G09_12.py` | NOT_IMPLEMENTED |
| `G10-01` | Source coverage | `src/guardian/knowledge/source_universe.py`, `src/guardian/knowledge/coverage.py` | `tests/campaign_contracts/G-10/test_G10_01.py` | NOT_IMPLEMENTED |
| `G10-02` | Requirements crosswalk | `src/guardian/knowledge/source_mapping.py` | `tests/campaign_contracts/G-10/test_G10_02.py` | NOT_IMPLEMENTED |
| `G10-03` | Implementation coverage | `src/guardian/knowledge/coverage.py`, `src/guardian/knowledge/reconciliation.py` | `tests/campaign_contracts/G-10/test_G10_03.py` | NOT_IMPLEMENTED |
| `G10-04` | Verification coverage | `src/guardian/assurance/coverage_assurance.py` | `tests/campaign_contracts/G-10/test_G10_04.py` | NOT_IMPLEMENTED |
| `G10-05` | Denominators | `src/guardian/program/campaign_membership.py`, `src/guardian/knowledge/coverage.py` | `tests/campaign_contracts/G-10/test_G10_05.py` | NOT_IMPLEMENTED |
| `G10-06` | Migration contract | `src/guardian/assurance/migration_assurance.py` | `tests/campaign_contracts/G-10/test_G10_06.py` | NOT_IMPLEMENTED |
| `G10-07` | Parity real | `src/guardian/assurance/migration_assurance.py` | `tests/campaign_contracts/G-10/test_G10_07.py` | NOT_IMPLEMENTED |
| `G10-08` | Evidence reuse | `src/guardian/assurance/invalidation.py` | `tests/campaign_contracts/G-10/test_G10_08.py` | NOT_IMPLEMENTED |
| `G10-09` | Conservative generalization | `src/guardian/program/generalization.py`, `src/guardian/assurance/migration_assurance.py` | `tests/campaign_contracts/G-10/test_G10_09.py` | NOT_IMPLEMENTED |
| `G10-10` | Consumers | `src/guardian/knowledge/source_mapping.py`, `src/guardian/assurance/integration_assurance.py` | `tests/campaign_contracts/G-10/test_G10_10.py` | NOT_IMPLEMENTED |
| `G10-11` | SupportGap closure | `src/guardian/graph/gaps.py`, `src/guardian/assurance/coverage_assurance.py` | `tests/campaign_contracts/G-10/test_G10_11.py` | NOT_IMPLEMENTED |
| `G10-12` | Scoped certification | `src/guardian/assurance/coverage_assurance.py`, `src/guardian/assurance/qualification.py` | `tests/campaign_contracts/G-10/test_G10_12.py` | NOT_IMPLEMENTED |
| `G11-01` | CLI integral | `src/guardian/interfaces/cli/commands.py`, `src/guardian/interfaces/cli/main.py` | `tests/campaign_contracts/G-11/test_G11_01.py` | NOT_IMPLEMENTED |
| `G11-02` | API versionada | `src/guardian/interfaces/api/contracts.py`, `src/guardian/interfaces/api/server.py` | `tests/campaign_contracts/G-11/test_G11_02.py` | NOT_IMPLEMENTED |
| `G11-03` | Agent tools | `src/guardian/interfaces/mcp/tools.py`, `src/guardian/interfaces/mcp/server.py` | `tests/campaign_contracts/G-11/test_G11_03.py` | NOT_IMPLEMENTED |
| `G11-04` | Contract explorer | `clients/web/src/views/contract_explorer.tsx` | `tests/campaign_contracts/G-11/test_G11_04.py` | NOT_IMPLEMENTED |
| `G11-05` | Architecture explorer | `clients/web/src/views/architecture_explorer.tsx` | `tests/campaign_contracts/G-11/test_G11_05.py` | NOT_IMPLEMENTED |
| `G11-06` | Support impact explorer | `clients/web/src/views/support_explorer.tsx`, `clients/web/src/shared/graph_view.tsx` | `tests/campaign_contracts/G-11/test_G11_06.py` | NOT_IMPLEMENTED |
| `G11-07` | Coverage matrix | `clients/web/src/views/coverage_matrix.tsx` | `tests/campaign_contracts/G-11/test_G11_07.py` | NOT_IMPLEMENTED |
| `G11-08` | History and diff | `clients/web/src/views/change_history.tsx` | `tests/campaign_contracts/G-11/test_G11_08.py` | NOT_IMPLEMENTED |
| `G11-09` | WorkPackage inspector | `clients/web/src/views/work_package_inspector.tsx` | `tests/campaign_contracts/G-11/test_G11_09.py` | NOT_IMPLEMENTED |
| `G11-10` | Approval workflow | `clients/web/src/views/approval_queue.tsx` | `tests/campaign_contracts/G-11/test_G11_10.py` | NOT_IMPLEMENTED |
| `G11-11` | Export reproducible | `src/guardian/interfaces/reporting/json.py`, `src/guardian/interfaces/reporting/markdown.py` | `tests/campaign_contracts/G-11/test_G11_11.py` | NOT_IMPLEMENTED |
| `G11-12` | Interface parity | `clients/web/src/api/guardian_client.ts`, `src/guardian/interfaces/api/contracts.py` | `tests/campaign_contracts/G-11/test_G11_12.py` | NOT_IMPLEMENTED |
| `G12-01` | Rebuild from Git | `src/guardian/adapters/sqlite/projector.py`, `src/guardian/persistence/snapshots.py` | `tests/campaign_contracts/G-12/test_G12_01.py` | NOT_IMPLEMENTED |
| `G12-02` | Crash-safe admission | `src/guardian/persistence/recovery.py`, `src/guardian/governance/publication.py` | `tests/campaign_contracts/G-12/test_G12_02.py` | NOT_IMPLEMENTED |
| `G12-03` | Idempotency | `src/guardian/persistence/events.py` | `tests/campaign_contracts/G-12/test_G12_03.py` | NOT_IMPLEMENTED |
| `G12-04` | Index incremental | `src/guardian/adapters/sqlite/queries.py` | `tests/campaign_contracts/G-12/test_G12_04.py` | NOT_IMPLEMENTED |
| `G12-05` | Budgets | `src/guardian/adapters/runners/process_runner.py` | `tests/campaign_contracts/G-12/test_G12_05.py` | NOT_IMPLEMENTED |
| `G12-06` | Schema compatibility | `src/guardian/persistence/schema_registry.py` | `tests/campaign_contracts/G-12/test_G12_06.py` | NOT_IMPLEMENTED |
| `G12-07` | Logs and observability | `src/guardian/governance/audit_trail.py` | `tests/campaign_contracts/G-12/test_G12_07.py` | NOT_IMPLEMENTED |
| `G12-08` | Concurrent writers | `src/guardian/governance/publication.py` | `tests/campaign_contracts/G-12/test_G12_08.py` | NOT_IMPLEMENTED |
| `G12-09` | Protected deployment | `src/guardian/bootstrap/runtime.py`, `src/guardian/governance/protected_policy.py` | `tests/campaign_contracts/G-12/test_G12_09.py` | NOT_IMPLEMENTED |
| `G12-10` | Performance receipts | `src/guardian/adapters/sqlite/queries.py`, `src/guardian/adapters/runners/process_runner.py` | `tests/campaign_contracts/G-12/test_G12_10.py` | NOT_IMPLEMENTED |
| `G13-01` | Proyecto sintético | `src/guardian/application/project_service.py` | `tests/campaign_contracts/G-13/test_G13_01.py` | NOT_IMPLEMENTED |
| `G13-02` | Ampliar proyecto | `src/guardian/program/commands.py`, `src/guardian/application/campaign_service.py` | `tests/campaign_contracts/G-13/test_G13_02.py` | NOT_IMPLEMENTED |
| `G13-03` | Rust real | `src/guardian/adapters/source_code/rust/analyzer.py`, `src/guardian/application/compliance_service.py` | `tests/campaign_contracts/G-13/test_G13_03.py` | NOT_IMPLEMENTED |
| `G13-04` | C++ real | `src/guardian/adapters/source_code/cpp/analyzer.py`, `src/guardian/application/compliance_service.py` | `tests/campaign_contracts/G-13/test_G13_04.py` | NOT_IMPLEMENTED |
| `G13-05` | Lean real | `src/guardian/adapters/source_code/lean/analyzer.py`, `src/guardian/application/assurance_service.py` | `tests/campaign_contracts/G-13/test_G13_05.py` | NOT_IMPLEMENTED |
| `G13-06` | Multi repo | `src/guardian/adapters/git/source_importer.py`, `src/guardian/knowledge/provenance.py` | `tests/campaign_contracts/G-13/test_G13_06.py` | NOT_IMPLEMENTED |
| `G13-07` | Migración real | `src/guardian/assurance/migration_assurance.py` | `tests/campaign_contracts/G-13/test_G13_07.py` | NOT_IMPLEMENTED |
| `G13-08` | Monoagente | `src/guardian/work/completion.py`, `src/guardian/adapters/agents/tool_adapter.py` | `tests/campaign_contracts/G-13/test_G13_08.py` | NOT_IMPLEMENTED |
| `G13-09` | Multiagente | `src/guardian/work/handoff.py`, `src/guardian/adapters/agents/multi_agent_profile.py` | `tests/campaign_contracts/G-13/test_G13_09.py` | NOT_IMPLEMENTED |
| `G13-10` | Security red team | `src/guardian/governance/admission.py`, `src/guardian/governance/protected_policy.py` | `tests/campaign_contracts/G-13/test_G13_10.py` | NOT_IMPLEMENTED |
| `G13-11` | Selective invalidation | `src/guardian/graph/impact.py`, `src/guardian/assurance/invalidation.py` | `tests/campaign_contracts/G-13/test_G13_11.py` | NOT_IMPLEMENTED |
| `G13-12` | Independent system audit | `src/guardian/assurance/qualification.py`, `src/guardian/governance/audit_trail.py` | `tests/campaign_contracts/G-13/test_G13_12.py` | NOT_IMPLEMENTED |

## Criterios de revisión
Cada vínculo debe validarse contra las interfaces originales, ownership y consumidores. Un módulo puede necesitar otra ubicación al concretar sus invariantes. Cambios permitidos con ADR/ChangeSet, sin debilitar el alcance. Se enlazarán ImplementationUnit/VerificationSpec reales, el repo/commit y receipts tras implementación y ejecución.

## Autoridad
Registro propuesto: `architecture/obligation_implementation_workmap.json`. Obligaciones originales: `architecture/campaigns.json`. Archivos objetivo: `architecture/module_blueprint.json`. **La matriz no certifica cobertura material.**
