# Topología objetivo y responsabilidad de archivos

Este documento organiza la discusión siguiente. `architecture/module_blueprint.json` contiene cada ruta propuesta con owner, función, dependencias y obligación de cobertura. **No son archivos implementados**: la topología es diseño y deberá materializarse según justificación de cohesión.

## Dominio
`domain/identity.py`: IDs nominales y validación; `project.py`: identificación de proyecto y aislamiento; `source.py`: SourceRef/SourceUniverse; `authority.py`: tipos de autoridad; `constitution.py`: invariantes/decisiones; `architecture.py`: Component/Boundary/ArchitectureRevision; `objective.py`: propósitos; `capability.py`: contratos de capacidad; `property.py`: propiedades; `obligation.py`: requisitos exigibles + revisión; `campaign.py`: memberships/closure; `scope.py`: perfil + applicability; `implementation.py`: SourceUnit, API, Consumer; `verification.py`: Specification/Run types; `evidence.py`: Evidence/Receipt; `claim.py`: assertion; `qualification.py`: certificados; `change.py`: ChangeSet; `outcomes.py`: ADT de verdicts.

## Núcleo de reglas
`constitution/evaluator.py`: comprobar reglas; `precedence.py`: conflictos; `invariants.py`: invariant registry; `amendments.py`: protected amendment; `authority_resolution.py`: permisos de decisión.
`graph/relation_types.py`: gramática de aristas y n-aridad; `relation_validation.py`: type checking; `projection.py`: vistas; `traversal.py`: cierre; `dependency.py`: DAG; `support.py`: ALL/ANY y SupportCone; `impact.py`: invalidación; `gaps.py`: SupportGap; `consistency.py`: integridad.
`program/commands.py`: operaciones tipadas; `transitions.py`: Apply puro; `revision.py`: diff/lineage; `refinement.py`: preservación; `generalization.py`: extensión; `compatibility.py`: versiones; `campaign_membership.py`: due/scope; `evolution_validation.py`: no-debilitamiento.

## Inteligencia y entregas
`knowledge/source_universe.py`: cobertura de fuentes; `inventory.py`: hechos observados; `source_mapping.py`: correspondencia intent-source-code; `observed_architecture.py`: observed DAG; `provenance.py`: hechos y testigos; `reconciliation.py`: conflictos; `coverage.py`: denominadores.
`work/orientation.py`: ProjectOrientation; `context_selection.py`: fragmentos y citas; `package_compiler.py`: RequiredClosure; `task_decomposition.py`: subpaquetes sin pérdida; `scheduling.py`: prerequisitos; `handoff.py`: snapshots entre agentes; `completion.py`: entrega versus contrato.

## Assurance y confianza
`assurance/verification_specs.py`: specs de prueba; `evidence_policy.py`: suficiencia de evidencia; `receipt_validation.py`: atestaciones; `qualification.py`: claims/SCOPED; `coverage_assurance.py`: condiciones certificadas; `adversarial_review.py`: findings; `integration_assurance.py`: productores/consumidores; `migration_assurance.py`: paridad histórica; `resource_assurance.py`: límites; `invalidation.py`: staleness.
`governance/permissions.py`: capabilities autorizadas; `approval.py`: decisiones; `candidate.py`: freeze; `admission.py`: decisión protegida; `protected_policy.py`: regla anterior; `publication.py`: CAS Git; `audit_trail.py`: historia.

## Aplicación, puertos y adaptadores
`application/*_service.py`: casos de uso, no reglas duplicadas.
`ports/*`: contratos Repository, Reader, Inspector, Runner, Attestor, Auth, Agent; definiciones independientes de infraestructura.
`adapters/git`: commit, diff y publicación; `sqlite`: proyección; `filesystem/artifacts`: IO; `source_code/{rust,cpp,python,lean}`: AST/build; `runners`: subprocesos aislados; `attestations`: verificación; `agents`: transporte de herramientas.
`interfaces/cli,api,mcp,reporting`: representación y entrada; `bootstrap`: configuración y wiring.

## Políticas de archivos
No crear scaffolds vacíos. Cada módulo se abre en su primera campaña propietaria; no hay límite de LOC. `lib.rs` no aplica porque núcleo Python. Un test apunta a un comportamiento, no a una función por simetría. Nuevos archivos requieren owner, propósito, consumidores, pruebas, policy de dependencias y registro en atlas físico al implementarse.



## Persistencia pura frente a adaptadores
`persistence/events.py`, `snapshots.py`, `canonicalization.py`, `schema_registry.py` y `recovery.py` poseen reglas de serialización, eventos, snapshots y propuestas de recuperación sin E/S; el Git real vive en `adapters/git/` y el SQL real en `adapters/sqlite/`. No deben duplicarse implementaciones de persistencia.


## Cliente gráfico
`clients/web/src` constituye un cliente TypeScript previsto en G-11; la API autentica y responde por proyecto/revisión/perfil. Las vistas no implementan lógica normativa ni escriben a SQLite. El mapa detallado de responsabilidades está en `docs/architecture/08_WEB_CLIENT.md` y `architecture/module_blueprint.json`.
