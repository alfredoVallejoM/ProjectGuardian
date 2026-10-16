# 12 — API, CLI, interfaz humana y uno/varios agentes

## Consumidores independientes
Human developer, CLI, API, UI, agent tool protocol y coordinación A0–A4 consumen los mismos casos de uso. No hay estado autoritativo dentro de un chat, UI ni SDK. Con cero agentes Guardian sigue orientando, verificando y certificando.

## Servicios
ProjectService: inspect/import/compare/replay.
SpecificationService: objective/capability/property/obligation/contract.
ArchitectureService: specified/observed/compliance.
GraphService: dependencies/consumers/support/impact/conflicts.
CampaignService: membership/closure/extend.
EvolutionService: propose/validate/admit change.
OrientationService: global/component/capability.
WorkService: compile/validate/deliver packages.
ComplianceService: code versus obligation/architecture.
AuditService: scope/findings/review-coverage.
AssuranceService: VerificationSpec/Run/Qualification.
EvidenceService: reuse/invalidate/verify receipt.
GovernanceService: permissions/approval/publish.

## CLI deseada
`guardian project inspect/status/doctor/replay`; `guardian orient`; `guardian contract show`; `guardian obligation explain/impact`; `guardian campaign extend/coverage`; `guardian architecture diff`; `guardian graph dependencies/consumers/conflicts`; `guardian work prepare/validate`; `guardian delivery submit/check`; `guardian audit scope/findings`; `guardian evidence verify/reuse`; `guardian qualification inspect`; `guardian change propose/validate/admit`. Cada consulta con project+revision+SupportProfile cuando influya en resultado. JSON machine-first y Markdown renderizado como vistas, no autoridades.

## UI completa prevista
Project Overview, Contract Explorer, Architecture Specified-vs-Observed, Implementation Matrix, Campaign Explorer, Verification Matrix, Support/Impact Explorer, Gap Explorer, History/Diff, Audit Workspace, WorkPackage Inspector, Qualification Explorer, Approval Queue. Preservar relaciones muchos-a-muchos, filtros por hito/scope y disclaimers explícitos ante UNKNOWN/STALE.

## Agentes
El usuario final puede emplear cualquier agente para `orient`, `prepare`, `explain`, `inspect`, `submit`, `audit`, `request_validation`, `propose_change`. Una skill enseña el protocolo, no copia toda la constitución del proyecto.
Perfil opcional de cinco agentes: A0 organiza, A1 recupera matemática/fuentes, A2 implementa, A3 audita después del bloque implementado, A4 integra y solicita validación real. A3 no revisa la propia autocertificación como fuente normativa; A4 no finge ejecuciones. Paquetes por snapshot, revisión exacta y tool permissions. Los handoffs no cambian la autoridad y no omiten obligaciones.

## Aislamiento de lenguaje/proveedor
Integración de agentes detrás de `AgentExecutor` y herramientas con contratos estables; no SDK obligatorio. Desarrolladores humanos reciben el mismo Project Contract. MCP y HTTP pueden ser adaptadores, no núcleos. La autenticidad de identidad/permiso viene del host confiable, no de JSON autodescrito.

