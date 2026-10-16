# Procedimiento de materialización y desarrollo de módulos

## Fronteras de cierre
Un corte puede comenzar con requisitos normativos ya definidos, pero una implementación no recibe DEVELOPMENT_COMPLETE hasta tener todas sus obligaciones y tests/adversarios/verificadores desarrollados. A3 revisa solo tras el cierre del bloque de A2; A4 ejecuta/integra sin autocertificación.

## Ciclo por unidad
1. Consultar los 34 requisitos y 30 ADR (propuestas hasta ratificación) y cerrar su alcance.
2. Seleccionar una obligación GXX-nn con dependencias, source, owner y perfil.
3. Identificar archivos previstos en module_blueprint; materializar solo los necesarios para esa responsabilidad.
4. Fijar firma/API, typed inputs/outputs, invariantes, tests positivos y falsaciones antes de escribir código.
5. Desarrollar implementación completa, tests y verificadores sin modificar la obligación.
6. Auditar por otro actor según policy; registrar findings y corregir hasta PASS o HOLD.
7. Ejecutar pruebas materiales en runner autorizado y validar consumers/presupuestos.
8. Admitir candidatos mediante Gatekeeper instalado y política previa; actualizar Git + proyecciones.

## Orden lógico por dependencias, no fases restringidas
- **G-00** (12 obligaciones): Fundamentos, ProjectContract y autoridad. Prerequisitos de cierre: —. Módulos: `src/guardian/domain/identity.py`, `src/guardian/domain/project.py`, `src/guardian/domain/scope.py`, `src/guardian/constitution/evaluator.py`.
- **G-01** (12 obligaciones): Evolución continua de obligaciones y campañas. Prerequisitos de cierre: G-00. Módulos: `src/guardian/program/commands.py`, `src/guardian/program/transitions.py`, `src/guardian/program/refinement.py`, `src/guardian/program/evolution_validation.py`.
- **G-02** (12 obligaciones): Grafo de relaciones, soporte e impacto. Prerequisitos de cierre: G-00, G-01. Módulos: `src/guardian/graph/relation_types.py`, `src/guardian/graph/relation_validation.py`, `src/guardian/graph/support.py`, `src/guardian/graph/impact.py`.
- **G-03** (10 obligaciones): Project Orientation y recuperación de conocimiento. Prerequisitos de cierre: G-02. Módulos: `src/guardian/work/orientation.py`, `src/guardian/work/context_selection.py`, `src/guardian/knowledge/provenance.py`.
- **G-04** (12 obligaciones): Compilador de tareas y planificación contractual. Prerequisitos de cierre: G-01, G-02. Módulos: `src/guardian/work/package_compiler.py`, `src/guardian/work/task_decomposition.py`, `src/guardian/work/scheduling.py`, `src/guardian/work/completion.py`.
- **G-05** (12 obligaciones): Conformidad arquitectónica y funcional. Prerequisitos de cierre: G-02, G-07. Módulos: `src/guardian/knowledge/observed_architecture.py`, `src/guardian/knowledge/reconciliation.py`, `src/guardian/assurance/integration_assurance.py`.
- **G-06** (12 obligaciones): Auditoría, evidencia, estados y certificación. Prerequisitos de cierre: G-01, G-05. Módulos: `src/guardian/assurance/verification_specs.py`, `src/guardian/assurance/receipt_validation.py`, `src/guardian/assurance/qualification.py`, `src/guardian/assurance/adversarial_review.py`.
- **G-07** (12 obligaciones): Adaptadores de proyectos, código y herramientas. Prerequisitos de cierre: G-02. Módulos: `src/guardian/adapters/git`, `src/guardian/adapters/source_code`, `src/guardian/ports/source_reader.py`, `src/guardian/knowledge/inventory.py`.
- **G-08** (11 obligaciones): Interacción humana, monoagente y multiagente. Prerequisitos de cierre: G-04, G-07, G-09, G-11. Módulos: `src/guardian/interfaces/mcp`, `src/guardian/adapters/agents`, `src/guardian/work/handoff.py`.
- **G-09** (12 obligaciones): Gatekeeper, permisos y seguridad. Prerequisitos de cierre: G-01, G-06. Módulos: `src/guardian/governance/permissions.py`, `src/guardian/governance/admission.py`, `src/guardian/governance/protected_policy.py`, `src/guardian/governance/publication.py`.
- **G-10** (12 obligaciones): Cobertura integral, preservación y migraciones. Prerequisitos de cierre: G-02, G-05, G-06, G-07. Módulos: `src/guardian/knowledge/source_universe.py`, `src/guardian/knowledge/coverage.py`, `src/guardian/assurance/migration_assurance.py`.
- **G-11** (12 obligaciones): CLI, API, MCP e interfaz gráfica. Prerequisitos de cierre: G-03, G-04, G-09. Módulos: `src/guardian/interfaces/cli`, `src/guardian/interfaces/api`, `src/guardian/interfaces/mcp`, `src/guardian/interfaces/reporting`.
- **G-12** (10 obligaciones): Fiabilidad, escala y operación. Prerequisitos de cierre: G-01, G-02, G-09. Módulos: `src/guardian/persistence/events.py`, `src/guardian/persistence/recovery.py`, `src/guardian/adapters/git/writer.py`, `src/guardian/adapters/sqlite/projector.py`, `src/guardian/bootstrap/runtime.py`.
- **G-13** (12 obligaciones): Pilotos científicos y cualificación integral. Prerequisitos de cierre: G-08, G-10, G-11, G-12. Módulos: `tests/end_to_end`, `tests/adversarial`, `fixtures/synthetic_projects`, `fixtures/historical_migrations`.

## Cambios estructurales
Una decisión que cambie el owner/boundary requiere ArchitectureChange y comprobación de imports/deps. Una obligación nueva se añade por AddObligation sin modificar motor. Una modificación de policy/validator se evalúa con policy anterior y aprobación externa.

## Evidencia protegida
Una campaign closure no se mide por cuántos archivos tienen tests o cuántos receipts existen, sino por la suficiencia de soporte por claim/perfil/revisión. No exigir exact branch SHA global para evidencias históricas si cambian fuentes no protegidas.

## Cómo reusar documentación de proyectos anteriores
El adaptador importa fuentes y registros como observed historical assertions con provenance; no crea copias canónicas sin procedimiento de migración de autoridad. Charloom y FC2 aislados salvo importación explícitamente autorizada.

