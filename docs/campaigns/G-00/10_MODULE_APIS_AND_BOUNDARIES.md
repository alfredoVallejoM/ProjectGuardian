# G-00 / Diseño por archivo: APIs, precondiciones y pruebas

**Estado:** contrato de diseño, no código. Registra responsabilidades e interfaces de G00-01…12 y evita duplicar las campañas siguientes.

## Dirección de dependencias

`application/project_service.py` y `application/contract_service.py` coordinan llamadas sobre snapshots suministrados, sin escritura.

`constitution/evaluator.py`, `precedence.py`, `invariants.py` y `authority_resolution.py` reciben tipos de `domain`. No importan Git, SQLite, agentes ni API remotas.

`domain/*.py` construye objetos de valor nominales, validadores locales y contratos. No lee configuración global. `persistence/schema_registry.py` proporciona el descriptor de versiones/codec de G-00, sin history replay (G-01).

## Contratos por archivo

| Ruta relativa a `src/guardian/` | Funcionalidades y operaciones | Errores/invariantes | Tests directos |
|---|---|---|---|
| `domain/identity.py` | ProjectId, EntityId, RevisionId, DigestRef, Alias, EntityRef; parse/encode/resolve | No intercambio implícito; alias ambiguo | `tests/domain/test_domain_identity.py` |
| `domain/project.py` | ProjectDefinition, StorageMode, ProjectNamespace; validate_project/check_project_membership | No current project global, fuentes externas bloqueadas | `tests/domain/test_domain_project.py` |
| `domain/source.py` | SourceRef, SourceCut, SourceUniverseRevision; validate_universe/check_source_membership | Pinned refs, known missing e imports explícitos | `tests/domain/test_domain_source.py` |
| `domain/authority.py` | DecisionRevision, ApprovalRef, AuthorityContext, validate_decision | Proposal no ratificado por texto | `tests/domain/test_domain_authority.py` |
| `domain/constitution.py` | ConstitutionRevision, RuleRevision, ConflictRecord; validate_rule | No regla sin scope, kind o autoridad | `tests/domain/test_domain_constitution.py` |
| `domain/architecture.py` | ArchitectureRevision, OwnerScope, Boundary, DependencyPolicy; validate_contract | Specified distinto de observed; no owners fantasma | `tests/domain/test_domain_architecture.py` |
| `domain/objective.py` | ObjectiveRevision; define/validate | Objetivo no es tarea; excluir scope explícito | `tests/domain/test_domain_objective.py` |
| `domain/capability.py` | CapabilityRevision, OwnerRef; validate | Capability distinta de implementación | `tests/domain/test_domain_capability.py` |
| `domain/property.py` | PropertyRevision; validate | Property no es VerificationSpec ni PASS | `tests/domain/test_domain_property.py` |
| `domain/obligation.py` | ObligationRevision; validate obligation, acceptance y falsification | No completed boolean; no ratificación de borrador | `tests/domain/test_domain_obligation.py` |
| `domain/campaign.py` | CampaignRevision, Membership, MilestoneRef; validate refs | Membership no crea segunda obligación | `tests/domain/test_domain_campaign.py` |
| `domain/scope.py` | SupportProfile, ScopeExpression, ApplicabilityResult; evaluate_scope | UNKNOWN no es NO; tipos y resources | `tests/domain/test_domain_scope.py` |
| `domain/outcomes.py` | TypedStatus, Result, Diagnostic, ErrorCode, RuleVerdict | No mezclar ejes/errores/perfil | `tests/domain/test_domain_outcomes.py` |
| `constitution/evaluator.py` | EvaluationRequest, RuleEvaluation, evaluate_constitution | Determinismo, sin I/O, full rule coverage | `tests/constitution/test_constitution_evaluator.py` |
| `constitution/precedence.py` | detect_conflicts, resolve_precedence | No elegir latest by date | `tests/constitution/test_constitution_precedence.py` |
| `constitution/invariants.py` | TrustedRuleEvaluatorRegistry, validate_rule_catalog | No project callbacks ejecutables | `tests/constitution/test_constitution_invariants.py` |
| `constitution/authority_resolution.py` | required_approvals, evaluate_authority | Sin autenticación desde JSON de candidato | `tests/constitution/test_constitution_authority_resolution.py` |
| `application/project_service.py` | inspect_definition, validate_project_snapshot | Caso de uso in-memory; Git import/replay posterior | `tests/application/test_application_project_service.py` |
| `application/contract_service.py` | inspect_objective/capability/obligation, validate_draft | Sin modificación normativa ni autoapproval | `tests/application/test_application_contract_service.py` |
| `persistence/schema_registry.py` | validate_envelope, lookup_descriptor, decode_record, check_reader_compatibility | Fail closed de features, no migración de registros histórica | `tests/persistence/test_schema_registry.py` |

Las 19 rutas de dominio/constitución/aplicación se complementan con dos límites compartidos cuyo **contrato inicial** debe existir en G-00: `persistence/schema_registry.py` (lector y validador de esquemas; migración completa G-01/G-12) y `constitution/amendments.py` (creación pura de propuestas de enmienda; autorización/publicación protegida G-09). Ambas atribuciones se registran en el atlas sin alterar las obligaciones canónicas. Las funciones futuras no se presentan como implementadas por G-00.

## Operaciones mínimas públicas (semántica antes que sintaxis final)

### Validación del proyecto y fuente
`validate_project(ProjectDefinition) -> Validation[ProjectDefinition]`.
Pre: ID de proyecto bien formado; owner y fuente de autoridad declarados. Post: referencia estable a un Project validado o lista exhaustiva de diagnósticos. No crea repositorio.

`validate_source_universe(SourceUniverseRevision, ProjectDefinition, SourceCatalogView) -> SourceUniverseValidation`.
Pre: fuentes con cortes/revisiones; catálogo observado inmutable. Post: cobertura de identidad y conocidas faltas, sin certificación de contenidos.

### IDs y referencias
`parse_identity(EntityKind,ProjectId,RawId) -> ParseResult[TypedId]`.
`resolve_entity(EntityRef, ReadOnlyProjectView, ExpectedKind, TrustedImportGrants) -> Resolution`.
Pre: snapshot y ProjectId explícitos. Post: entidad exacta o ISSUE; nunca fallback al latest ni al primer alias.

### Obligaciones y perfiles
`validate_obligation(ObligationRevision,ReadOnlyProjectView) -> ObligationValidation`.
Pre: manifiesto de fuente/acceptance/falsification, versión y scopes. Post: errores por cláusula; no estado de cumplimiento.

`evaluate_scope(ScopeExpression,SupportProfile,FactSet,StepBudget) -> ScopeEvaluation`.
Pre: AST, hechos tipados y presupuesto de pasos. Post: YES/NO/UNKNOWN/CONFLICT + testigos; un error operativo no es valor de ámbito.

### Constitución
`validate_constitution(ConstitutionRevision,ReadOnlyProjectView) -> ConstitutionValidation`.
`detect_conflicts(AssertionSet,SupportProfile) -> tuple[ConflictRecord,...]`.
`evaluate_constitution(EvaluationRequest,TrustedRuleEvaluatorRegistry) -> ConstitutionEvaluationReport`.
Pre: policy/authority ya seleccionadas, sin ejecutar código arbitrario. Post: informe reproducible con veredictos por regla, reasons y alcance, sin concesión de derechos.

## Contratos de tipos y errores

Todos los validadores devolverán \`Result[T, tuple[Diagnostic,...]]\` o un ADT específico. \`Diagnostic\`: code estable, location (JSON path o EntityRef), project_revision, expected/actual tipos seguros para logs, offending_ref, originating_rule, witness_refs, remediation_hint. No silencios por excepciones genéricas. Un error de programación interno permanece distinto de FAIL de negocio.

## Evitar sobreingeniería

No generar 20 archivos vacíos; abrir solo los que una obligación y consumidor requiera al desarrollarse. Agrupar funciones cohesivas sin límite LOC. Domain define el contrato; G-01 implementa evoluciones persistidas; G-02 el grafo; G-05/G-07 lectura AST; G-06 qualification; G-09 autenticación/publicación. Ningún servicio duplica código de aplicación de normas.

## Criterios de aceptación por módulo

Cada módulo materializado debe tener owner e invariantes; API mínima utilizable; tests positivos y negativos derivados de G00-Fxx; casos de referencia de dos proyectos; contrato con consumidores posteriores; código en paths autorizados y sin dependencia de Git/SQLite/SDKs en el dominio. En G-00 se verificará el **grafo de dependencias de código realmente escrito**; que el atlas declare un límite no demuestra que lo respete.
