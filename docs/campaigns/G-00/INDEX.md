# G-00 — Especificación funcional completa de la campaña fundacional

**Autoridad original:** [G-00 canónica](../G-00.md), doce obligaciones G00-01…12, sin cambios de estado ni numeración. **Alcance:** datos e invariantes puros del proyecto, constitución, source universe, applicability, referencias, schemas y evaluador local.

## Guía de funcionamiento (documentación normativa de referencia; desarrollo parcial enlazado al final)

| Orden | Documento | Función |
|---|---|---|
| 00 | [Carta y cierre](00_CHARTER_AND_DELIVERABLES.md) | Qué pertenece a G-00 y qué a campañas siguientes |
| 01 | [IDs y referencias](01_IDS_AND_REFERENCES.md) | Identidad estable, revision, alias, digest |
| 02 | [Project y SourceUniverse](02_PROJECT_TENANCY_AND_SOURCES.md) | Aislamiento y fuentes históricas |
| 03 | [Constitución y autoridad](03_CONSTITUTION_AUTHORITY_CONFLICTS.md) | Normas, decisiones, conflictos, ratificación |
| 04 | [Ontología completa](04_OBJECTIVES_CAPABILITIES_PROPERTIES_OBLIGATIONS.md) | Objective, Capability, Property, Obligation, Campaign, Architecture |
| 05 | [Scope y applicability](05_SCOPE_AND_APPLICABILITY.md) | Perfil, predicados y cuatro valores de evidencia |
| 06 | [Estados ortogonales](06_ORTHOGONAL_STATUS_AND_OUTCOMES.md) | Estados separados, anti-promociones |
| 07 | [Referential integrity](07_REFERENTIAL_INTEGRITY.md) | Resolver IDs, revisiones y referencias externas |
| 08 | [Schemas/compatibilidad](08_SCHEMAS_VERSIONING_AND_SERIALIZATION.md) | Envelope normativo y fail closed de versiones |
| 09 | [Evaluador puro](09_PURE_EVALUATOR.md) | Inputs, pipeline, rule registry, diagnósticos |
| 10 | [Módulos y APIs](10_MODULE_APIS_AND_BOUNDARIES.md) | Owners, rutas, funciones, errores, tests |
| 11 | [Suite adversaria](11_TESTS_AND_ADVERSARIAL_MATRIX.md) | Pruebas, 36 mutaciones, 7 verticales |
| 12 | [Ejecución y cierre](12_IMPLEMENTATION_PROGRAM_AND_EXIT_GATES.md) | Cortes B00…B09, auditoría e integración |
| 13 | [120 cláusulas](13_FUNCTIONAL_REFINEMENT_MATRIX.md) | Cada G00-XX-FYY con aceptación/falsación/test |
| 14 | [58 operaciones](14_API_CONTRACT_CATALOG.md) | Pre/postcondiciones por API y errores |
| 15 | [24 decisiones](15_FOUNDATION_DESIGN_DECISIONS.md) | Selecciones a ratificar antes de implementar |
| 16 | [Trazabilidad fina](16_FINE_GRAIN_TRACEABILITY.md) | REQ/ADR → cláusula → API → test/owner |
| 17 | [Auditoría estática documental](17_DOCUMENTARY_AUDIT.md) | Resultados verificados y límites de cierre |

## Registros legibles por máquina

- [`architecture/g00_functional_refinement.json`](../../../architecture/g00_functional_refinement.json) — 120 cláusulas subordinadas a G00-01…12.
- [`architecture/g00_api_contracts.json`](../../../architecture/g00_api_contracts.json) — 58 operaciones de API de diseño.
- [`architecture/g00_validation_plan.json`](../../../architecture/g00_validation_plan.json) — 120 tests lógicos, 36 adversarios, 7 verticales.
- [`architecture/g00_design_decisions.json`](../../../architecture/g00_design_decisions.json) — 24 propuestas técnicas pendientes de ratificación.
- [`architecture/module_blueprint.json`](../../../architecture/module_blueprint.json) — owners y archivos previstos, no código existente.
- [`architecture/obligation_implementation_workmap.json`](../../../architecture/obligation_implementation_workmap.json) — 12 obligaciones padres y módulos de destino.

## Trazabilidad

**G00-01…12 → 10 cláusulas G00-XX-F01…F10 → un test lógico por cláusula → módulos/operaciones de diseño → pruebas y receipts futuros.** Los IDs de pruebas del catálogo son contratos históricos; el código de pruebas actualmente existente se informa por corte, sin sustituir el denominador de 120. La existencia de este catálogo no constituye G00_DEVELOPMENT_COMPLETE.

## Fronteras que hay que conservar

- G-00 produce evaluación constitucional **local y pura**, sin Git/SQLite/API/SDK.
- G-01 desarrolla evolución/eventos/campaign revisions operativas.
- G-02 desarrolla grafo SupportCone/ImpactCone.
- G-05/G-07 aportan arquitectura observada y analizadores de código.
- G-06 produce evidencias/qualifications reales.
- G-09 autentica autoridad, protege evaluator y realiza publicación.
- G-10 completa cobertura de especificación/migración.

El desarrollo de G-00 **no puede cerrar automáticamente ninguna campaña posterior**; las decisiones no ratificadas no son todavía políticas de publicación efectivas.

## Implementaciones materializadas desde la línea base documental

- [Primer corte G00-B01/GSL-LC00…02](../../implementation/G00_B01_GSL0_LC00_LC02.md).
- [Segundo corte G00-B02/GSL-LC03](../../implementation/G00_B02_GSL0_LC03.md) y [matriz de implementación](../../implementation/G00_B02_GSL0_LC03_PROGRESS.json).

Estos cortes no transforman la especificación canónica en una campaña cerrada ni ratifican las ADR originales.

## Auditoría adversaria de implementación (21-10-2026)

[Revisión y 11 defectos corregidos](../../audit/2026_10_21_FOUNDATION_ADVERSARIAL_REVIEW.md) · [trazabilidad por obligaciones](../../audit/2026_10_21_FOUNDATION_OBLIGATION_MATRIX.json). G00-B01/B02 ejecutados con 226 tests locales PASS junto a GSL-LC00…03. El desarrollo sigue parcial donde las obligaciones padres requieren B03/B06, consumidores, evidencia material y autoridad protegida.
