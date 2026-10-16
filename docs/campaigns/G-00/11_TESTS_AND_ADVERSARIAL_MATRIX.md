# G-00 / Plan funcional de pruebas, propiedades, mutaciones e integración

**Autoridad:** G00-12 y todas las G00-01…11. **Estado:** pruebas de diseño previstas, ninguna escrita ni ejecutada todavía. Registro: `architecture/g00_validation_plan.json`.

## Arquitectura de pruebas por contrato

No se necesita un archivo por cláusula. Se necesita evidencia de que cada una de las **120 cláusulas** tiene una comprobación positiva pertinente, falsación independiente de su condición y código del verificador escrito. La distribución física responde a invariantes y módulos, nunca a un límite numérico.

| Nivel | Qué verifica | Evidencia de cierre |
|---|---|---|
| Unit | Parser/constructor/validator y errores exactos | Casos positivos y negativos con valores reales |
| Contract | Firma/API/campo requerido y compatibilidad de tipos | Suite de contrato repetible |
| Property-based | Conjuntos aleatorios de IDs, sources, profiles, reglas, relaciones | Invariante universal acotado sin dependencia de orden |
| Mutation | Alteración deliberada del contrato y detección del incumplimiento | Falsación que falla de forma esperada |
| In-memory integration | Modelos de proyectos múltiples y evaluador puro | Resultado reproducible contra snapshot íntegro |
| Architecture/static | No imports hacia adaptadores desde Domain/Constitution | Grafo real de dependencias revisado |
| Material | Ejecución de tests sobre candidate real | Receipts y logs autenticables (campaña cerrada, no autoría) |

## Estructura de fixtures

`ValidProjectA`, `ValidProjectB`: mismos alias humanos, repos y constituciones diferentes. `PinnedGitSourceCut`, `UnresolvedMutableBranch`, `MissingHistoricalDocument`, `OverlappingHistoricalCuts`, `ScopedImportGrant`. `ObjectiveCapabilityPropertyFixture`: 1 objetivo, 2 capacidades, propiedad compartida y obligaciones exigibles/futuras. `FourValuedProfileFixture`: features completas e incompletas y contradicción evidenciada. `ConstitutionConflictFixture`: reglas compatibles/disjuntas/opuestas y decision de supersession. `BudgetLimitedRuleSet`: número de reglas mayor que presupuesto.

**Cada fixture referencia IDs y revisiones concretos.** No crear un Git real para pruebas puras; las pruebas de adaptadores Git las desarrolla G-07.

## Propiedades generales

1. `Parse(Encode(x)) = x` para tipos con schema/versión compatibles, manteniendo kind y project.
2. Resolver en la misma vista inmutable da siempre resultado idéntico.
3. Permutar el orden de diccionarios/listas no normativamente ordenadas no cambia veredicto.
4. Cambiar display name o path sin cambiar LogicalId no cambia identidad.
5. `NOT(UNKNOWN)=UNKNOWN` y `NOT(CONFLICT)=CONFLICT`.
6. Ninguna obligación desaparece porque una condición sea UNKNOWN.
7. Decision PROPOSED sin aprobación externa no gobierna reglas ratificadas.
8. Test escrito y Material.NOT_RUN permanecen sin cualificación.
9. Regla con kind desconocido no produce PASS de cobertura.
10. ProjectA + ProjectB compuestos no fusionan namespaces.
11. Evaluador no muta snapshots ni FactSet.
12. Budget agotado produce lista de reglas sin examinar.
13. Input de fuente no autenticada no crea SourceUniverse reconciled.
14. Una inconsistencia material entre fuente y norma se representa como conflicto, no como modificación de la norma.

## Banco adversario detallado

| Caso | Obligación | Mutación | Diagnóstico esperado |
|---|---|---|---|
| `ADV-01` | `G00-01` | Use the same raw string as ProjectId and RevisionId | `WRONG_ID_KIND` |
| `ADV-02` | `G00-01` | Deserialize a reference without entity kind | `INVALID_ID_SCHEMA` |
| `ADV-03` | `G00-01` | Alias resolves to two entities in the same namespace | `AMBIGUOUS_ALIAS` |
| `ADV-04` | `G00-02` | Read another project's obligation under matching human name | `FORBIDDEN_CROSS_PROJECT_REF` |
| `ADV-05` | `G00-02` | Approve all of an external repository based on a file-level grant | `UNAPPROVED_IMPORT_SCOPE` |
| `ADV-06` | `G00-02` | Change a project's display name and regenerate its ProjectId | `LOGICAL_ID_DRIFT` |
| `ADV-07` | `G00-03` | Use branch HEAD string as immutable source revision | `SOURCE_CUT_NOT_PINNED` |
| `ADV-08` | `G00-03` | Declare a universe complete with known_missing records | `SOURCE_COVERAGE_UNKNOWN` |
| `ADV-09` | `G00-03` | Sum overlapping base/delta files as disjoint semantic capabilities | `SOURCE_POPULATION_DOUBLE_COUNT` |
| `ADV-10` | `G00-04` | Declare RATIFIED without a trusted approval context | `UNTRUSTED_RATIFICATION` |
| `ADV-11` | `G00-04` | Load a foreign project's rule as local constitution | `FOREIGN_CONSTITUTION_RULE` |
| `ADV-12` | `G00-04` | Treat most recently edited requirement as supercession | `MISSING_APPROVED_SUPERSESSION` |
| `ADV-13` | `G00-05` | Equate a capability with the path of its implementation | `CAPABILITY_ID_COLLAPSE` |
| `ADV-14` | `G00-05` | Create admitted obligation with empty acceptance criteria | `REQUIRED_ACCEPTANCE_MISSING` |
| `ADV-15` | `G00-05` | Duplicate a Property when referenced by two campaigns | `DUPLICATE_LOGICAL_ID` |
| `ADV-16` | `G00-06` | Interpret an absent feature list as a negative witness | `APPLICABILITY_UNKNOWN` |
| `ADV-17` | `G00-06` | Convert NOT(UNKNOWN) to YES | `FOUR_VALUE_NEGATION_INCORRECT` |
| `ADV-18` | `G00-06` | Treat evidence of both inclusion and exclusion as NO | `APPLICABILITY_CONFLICT` |
| `ADV-19` | `G00-06` | Accept an executable Python expression as ScopePredicate | `UNSAFE_SCOPE_PREDICATE` |
| `ADV-20` | `G00-06` | Run out of evaluation steps then return PASS | `EVALUATION_RESOURCE_LIMITED` |
| `ADV-21` | `G00-07` | Map Implementation.DEVELOPED to Material.PASS | `ILLEGAL_STATUS_PROMOTION` |
| `ADV-22` | `G00-07` | Map Audit.PASS directly to Scientific QUALIFIED | `ILLEGAL_STATUS_PROMOTION` |
| `ADV-23` | `G00-07` | Treat Material.NOT_RUN as a passing test | `MATERIAL_NOT_RUN` |
| `ADV-24` | `G00-08` | Resolve entity by latest revision when explicit revision missing | `REVISION_REQUIRED` |
| `ADV-25` | `G00-08` | Use an absolute or parent-traversal Git path | `INVALID_SOURCE_PATH` |
| `ADV-26` | `G00-08` | Create ratified placeholder for unresolved EntityRef | `ORPHAN_REFERENCE` |
| `ADV-27` | `G00-09` | Ignore required normative feature unknown to reader | `UNSUPPORTED_NORMATIVE_FEATURE` |
| `ADV-28` | `G00-09` | Treat null and empty acceptance list as equivalent defaults | `INVALID_SCHEMA_SEMANTICS` |
| `ADV-29` | `G00-09` | Coerce unknown status enum to first known member | `UNSUPPORTED_VARIANT` |
| `ADV-30` | `G00-10` | Return PASS without evaluating one required RuleRevision | `RULE_SET_INCOMPLETE` |
| `ADV-31` | `G00-10` | Let a pure evaluator read wall clock / environment to decide | `IMPURE_EVALUATION` |
| `ADV-32` | `G00-10` | Run a project-provided callback as a trusted RuleEvaluator | `UNTRUSTED_RULE_EXECUTOR` |
| `ADV-33` | `G00-11` | Silently prefer the newest of two incompatible ratified rules | `UNRESOLVED_NORMATIVE_CONFLICT` |
| `ADV-34` | `G00-11` | Block a disjoint project with another project's conflict | `CONFLICT_SCOPE_LEAK` |
| `ADV-35` | `G00-11` | Drop one witness when merging conflict diagnostics | `CONFLICT_WITNESS_LOSS` |
| `ADV-36` | `G00-12` | Modify a normative condition and make tests pass by deleting adversarial case | `VERIFICATION_CONTRACT_DRIFT` |

Los diagnósticos son **expectativas de contrato por ratificar**, no códigos ya implementados. Un test no vale por detectar cualquier error si no diagnostica la violación que el caso pretende falsar.

## Verticales de integración en memoria

### G00-V01 — Two isolated projects
Create projects A/B with overlapping aliases, distinct source universes and decisions; validate separate snapshots and block foreign reference.

Obligaciones vinculadas: `G00-01`, `G00-02`, `G00-03`, `G00-08`.

**Cierre:** escenario positivo completo, variación adversaria, revisión del estado separado, salida sin falsas certificaciones, y tests materialmente ejecutados en la fase de cierre de campaña.

### G00-V02 — Founding mathematical specification
One objective supports 2 capabilities, a shared Property, 3 Obligations, one current and one future campaign; inspect without code or tests.

Obligaciones vinculadas: `G00-05`, `G00-07`, `G00-08`.

**Cierre:** escenario positivo completo, variación adversaria, revisión del estado separado, salida sin falsas certificaciones, y tests materialmente ejecutados en la fase de cierre de campaña.

### G00-V03 — Incomplete historical SourceUniverse
Two overlapping Git cuts, one unavailable source, declared exclusions and candidate coverage claim; refuse complete source certification.

Obligaciones vinculadas: `G00-02`, `G00-03`, `G00-11`.

**Cierre:** escenario positivo completo, variación adversaria, revisión del estado separado, salida sin falsas certificaciones, y tests materialmente ejecutados en la fase de cierre de campaña.

### G00-V04 — Policy proposal versus ratification
Create proposal and authenticated-context decision, evaluate two incompatible scoped rules; conflict/localization no self-approval.

Obligaciones vinculadas: `G00-04`, `G00-10`, `G00-11`.

**Cierre:** escenario positivo completo, variación adversaria, revisión del estado separado, salida sin falsas certificaciones, y tests materialmente ejecutados en la fase de cierre de campaña.

### G00-V05 — Four-valued applicability
Evaluate YES/NO/UNKNOWN/CONFLICT and nested ALL/ANY/NOT with complete/incomplete feature sets, conflicts and budget limit.

Obligaciones vinculadas: `G00-06`, `G00-09`, `G00-10`.

**Cierre:** escenario positivo completo, variación adversaria, revisión del estado separado, salida sin falsas certificaciones, y tests materialmente ejecutados en la fase de cierre de campaña.

### G00-V06 — Schema backwards reader
Roundtrip 4 domain entity kinds, deny unknown normative feature while preserving authorized informational extension.

Obligaciones vinculadas: `G00-01`, `G00-05`, `G00-09`.

**Cierre:** escenario positivo completo, variación adversaria, revisión del estado separado, salida sin falsas certificaciones, y tests materialmente ejecutados en la fase de cierre de campaña.

### G00-V07 — Deterministic end-to-end in memory
Take valid snapshot+rules+facts+profile, evaluate constitutional status, permute map order and assert identical reports and zero mutations.

Obligaciones vinculadas: `G00-07`, `G00-10`, `G00-11`, `G00-12`.

**Cierre:** escenario positivo completo, variación adversaria, revisión del estado separado, salida sin falsas certificaciones, y tests materialmente ejecutados en la fase de cierre de campaña.


## Condiciones de cobertura de G00-12

Una cláusula funcional es `TESTS_AUTHORED` cuando existe código de prueba directo o propiedad generativa capaz de fallar ante el defecto previsto, con referencia bidireccional a su clause ID. No basta que el test tenga el mismo nombre.

`G00-12 DEVELOPMENT_COMPLETE` exige:
- 120 cláusulas tienen tests/properties adecuados escritos.
- Las 36 falsaciones transversales tienen tests adversarios que rechazan el fallo descrito.
- Las siete verticales tienen secuencias funcionales en memoria con consumidores de G-00 reales.
- No hay placeholders, skips, mocks que simulen la propia lógica constitucional bajo prueba ni validadores que siempre devuelvan PASS.
- Los imports y dependencias reales de los módulos producidos respetan la constitución del propio Guardian.

`G00 CAMPAIGN_CLOSED` exige además ejecutar suites y mutaciones, recibir auditoría independiente cuando proceda y publicar receipts sobre commit exacto y scope. Un test no ejecutado no constituye PASS material.

## Límites del plan

Los 120 contratos de prueba y 36 escenarios son compromisos detallados derivados de las doce obligaciones propuestas; no están ratificados aún ni se deben contar como tests físicos ya existentes. Las suites futuras pueden agruparse por módulo y comportamiento, pero no perder la capacidad de falsar cada cláusula.

