# Cliente de interfaz gráfica: contratos, ubicación y pruebas

**Decisión propuesta, pendiente de ratificación:** cliente web TypeScript con componentes React o equivalentes. La biblioteca Guardian principal sigue en Python; el cliente no crea un segundo motor normativo.

## Por qué un cliente independiente
Las vistas de un proyecto con miles de obligaciones, contratos, relaciones múltiples, claims y evidencias requieren interacción y gráficos navegables. Un cliente web tipado consume la misma API que CLI y herramientas de agentes. Elegir la tecnología de vistas no cambia el significado del Project Contract.

## Módulos del cliente previstos (sin generar scaffolds)

| Ruta | Responsabilidad | Test previsto |
|---|---|---|
| `clients/web/src/app/bootstrap.ts` | Configura app y rutas; autentica principal del servidor; no alberga reglas de dominio | `clients/web/tests/app_bootstrap.test.ts` |
| `clients/web/src/api/contracts.ts` | DTO versionados y validación de responses con revisión, scope y evidence | `clients/web/tests/api_contracts.test.ts` |
| `clients/web/src/api/guardian_client.ts` | Cliente tipado de servicios Guardian sin acceso directo a base de datos | `clients/web/tests/api_guardian_client.test.ts` |
| `clients/web/src/state/project_scope.ts` | Selección de proyecto, revision y SupportProfile con invalidación de cachés | `clients/web/tests/state_project_scope.test.ts` |
| `clients/web/src/shared/graph_view.tsx` | Render de relaciones tipadas y roles n-arios con distinción proof/informational | `clients/web/tests/shared_graph_view.test.ts` |
| `clients/web/src/views/project_overview.tsx` | Objetivos, fuentes, campañas, bloqueos, estatus y garantías por proyecto | `clients/web/tests/views_project_overview.test.ts` |
| `clients/web/src/views/contract_explorer.tsx` | Árbol y grafo muchos-a-muchos de objetivos/capacidades/propiedades/obligaciones | `clients/web/tests/views_contract_explorer.test.ts` |
| `clients/web/src/views/architecture_explorer.tsx` | Comparación de arquitectura especificada, observada, owner e imports | `clients/web/tests/views_architecture_explorer.test.ts` |
| `clients/web/src/views/campaign_explorer.tsx` | Campañas, revisiones, obligaciones due y estados separados | `clients/web/tests/views_campaign_explorer.test.ts` |
| `clients/web/src/views/coverage_matrix.tsx` | Denominadores, UNKNOWN y estados de evidencia por hito y perfil | `clients/web/tests/views_coverage_matrix.test.ts` |
| `clients/web/src/views/support_explorer.tsx` | SupportCone, ImpactCone, ALL/ANY, SupportGap y rutas de evidencia | `clients/web/tests/views_support_explorer.test.ts` |
| `clients/web/src/views/audit_workspace.tsx` | Hallazgos por obligación/candidato y acciones de resolución | `clients/web/tests/views_audit_workspace.test.ts` |
| `clients/web/src/views/change_history.tsx` | Revisions, ChangeSets, revocations, diffs y dependencias | `clients/web/tests/views_change_history.test.ts` |
| `clients/web/src/views/work_package_inspector.tsx` | WorkPackage normativo frente a orientación resumida y evidencia | `clients/web/tests/views_work_package_inspector.test.ts` |
| `clients/web/src/views/qualification_explorer.tsx` | Claims, certificados, scope, receipts, staleness y limitaciones | `clients/web/tests/views_qualification_explorer.test.ts` |
| `clients/web/src/views/approval_queue.tsx` | Propuestas de cambio, impacto, autoridad y approvals autenticadas | `clients/web/tests/views_approval_queue.test.ts` |

## Contratos de interacción
**Read:** cada query incluye ProjectId, RevisionId y SupportProfile o los datos de ámbito necesarios; respuestas con tipos, provenance y estado de incertidumbre. **Write:** la UI sólo solicita ChangeSet/Approval/Delivery por API autorizada; no hay escritura de estado normativo en el navegador. **Evidence:** el cliente presenta digests/runner/verifier/claim sin inferir que un fichero es un certificado.

## Restricciones transversales
- No inferir relación matemática de proximidad visual en grafo; distinguir links informativos, soporte autorizado y conflictos.
- No ocultar UNKNOWN/NOT_RUN/FUTURE al computar denominadores.
- No presentar un estado de implementación del sistema como resultado de una campaña científica.
- Prevención XSS sobre Markdown/documentos no confiables, contenido escapado y permisos comprobados por servidor.
- Accesibilidad de teclado, contraste, representación textual alternativa de grafos y tablas paginadas.
- No confianza en controles de UI para permisos: Gatekeeper controla toda admisión desde instalación protegida.
- Tests de paridad CLI/API/UI/MCP para los mismos snapshots, y end-to-end de approvals y cambio de revisión durante edición.

## Decisiones que deben debatirse
El framework concreto (React u otro), empaquetado/embebido del cliente, qué visualizaciones requieren canvas/WebGL versus SVG, autenticación local/remota y estrategias de paginación/caché. La responsabilidad funcional de todas las vistas es parte de G-11 aun antes de esa selección.
