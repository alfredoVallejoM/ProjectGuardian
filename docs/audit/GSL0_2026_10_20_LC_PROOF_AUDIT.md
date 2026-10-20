# GSL-0 — Revisión exhaustiva de los cortes LC00…LC12 y las obligaciones de preservación

**Auditoría 20-10-2026; NO DESARROLLO COMPLETO.** Se compara el diseño GSL-0 publicado con el experimento remoto y la implementación local aislada (113 PASS, 1 SKIP después de corregir links), que **no está sincronizada con GitHub**. El desarrollo G-00 del dominio no existe en `main`.

## 1. Obligaciones LC por unidad

| Unidad | Objeto exigido | Evidencia disponible | Estado | Bloqueo específico |
|---|---|---|---|---|
| `LC00` | Contrato y ratificación formal | Formalismo candidato documentado; GSL0 0.1 aún no ratificado | **INCOMPLETE** | No semantics-proof package ni ADR ratificada |
| `LC01` | IR tipado, nominal y discrimantes | IR JSON candidato y dataclasses en prototipo local; Product domain G-00 ausente | **PARTIAL** | No firmas completas ni coexistencia normativa |
| `LC02` | V0 externo y oráculos | Evaluador V4 y validador estructural; 4-valued finite tests | **PARTIAL** | No prueba semántica fuente→IR resistente a recomputación de digest |
| `LC03` | Markdown, lexer, CST, parser | Markdown normative fences, Lark AST y tokens+trivia locales | **PARTIAL** | No CST jerárquico completo, equivalencia exhaustiva ni material del repo |
| `LC04` | Imports, namespaces y resolución | Resolución de nombres y grafo imports en implementación local | **PARTIAL** | No grants multinivel ni AuthorityContext real |
| `LC05` | Tipado y predicados constitucionales | Nominal refs, 2 predicados fundacionales, cuantificadores finitos locales | **PARTIAL** | Extensibilidad semántica/versiones insuficientes |
| `LC06` | Lowering AST→IR | Elaborador IR estable y pruebas diferenciales sobre subfragmento | **PARTIAL** | Falsa equivalencia fuente↔IR bajo tampering con digests regenerados |
| `LC07` | SourceMap y canonización | Spans UTF-8, separación de digests, JSON canónico | **PARTIAL** | No fundamentación de todo nodo derivado ni incremental completo |
| `LC08` | Obligaciones y diagnóstico | Emite PO UNPROVEN, parser typed diagnostics | **PARTIAL** | No PO de todas las leyes CCRR ni alcance completo |
| `LC09` | Corpus G-00 integral | G00-01 10 cláusulas/10 tests en fixture candidato | **PARTIAL** | G00-02…12 no elaborados; test auténtico corpus SKIPPED |
| `LC10` | Auditoría adversaria y mutaciones | 113 PASS locales después de reparar enlaces, 1 SKIP | **PARTIAL** | No auditor independiente ni suite remota sobre SHA publicado |
| `LC11` | Servicio CLI / integración real | CLI candidata que consume bundles locales | **PARTIAL** | No product Guardian service, CLI/API/MCP paridad |
| `LC12` | Cualificación material | No receipts ni certificado de compilación integral | **ABSENT** | Sin replays sobre SHA completo ni ratificación |

## 2. Teoremas y propiedades objetivo

| Obligación | Qué debe establecer | Evidencia | Resultado |
|---|---|---|---|
| `GSL-T01` | Conservación bytes/spans | Tests parciales de lexer UTF-8 | **PARTIAL** |
| `GSL-T02` | CST yield y trivia | scan_concrete aplanado, sin CST jerárquico completo | **PARTIAL** |
| `GSL-T03` | AST conserva declaraciones | Pruebas de pérdida con ID y fuente, pero no prueba general | **PARTIAL** |
| `GSL-T04` | Preservación tipos | Test subset, demostración formal no mecanizada | **PARTIAL** |
| `GSL-T05` | Preservación semántica V4 | Dos intérpretes con subset; falsificación de IR recompuesto aún posible | **PARTIAL** |
| `GSL-T06` | Grounding de todo nodo IR | SourceMap nominal; no prueba completa de derivaciones | **PARTIAL** |
| `GSL-T07` | Cobertura fuente→IR | IDs 10/10 sintéticos; fuente real sin material test | **PARTIAL** |
| `GSL-T08` | Incremental vs full | Sin motor incremental y sin prueba de equivalencia | **ABSENT** |
| `GSL-T09` | No auto-ratificación | La API del compilador no publica; host real no protegido | **PARTIAL** |
| `GSL-T10` | Streaming/edit equivalencia | CTK-01 sin Cargo; GSL0 no realiza streaming ni edit incremental | **ABSENT** |
| `GSL-T11` | V4 no rebaja UNKNOWN/CONFLICT | Álgebra con finite tests; hechos externos/autoridad ausentes | **PARTIAL** |
| `GSL-T12` | Estados de desarrollo/cert separados | Candidata marca UNPROVEN; Product G-00 sin modelo integral | **PARTIAL** |

## 3. Evidencias adversarias materializadas en revisión local

- **Miswire positivo:** cambiar `G00-01-T01.property` de F01 a F02 sin cambiar ID/test count devuelve `COMPILED` en la versión sin contrato de links. Lo mismo ocurre con `F01-DETAIL.child = F02`, y con eliminación de referencia desde padre. Reparación local mediante `required_property_origins`, `required_verification_bindings`, `required_relation_bindings` y 5 nuevas pruebas → 113 PASS, 1 SKIP. Esta corrección NO está en `main`.
- **Mutación IR:** desde un contrato con `when:true`, cambiar a `when:false`, recalcular `contract_digest` y `compilation_digest` y conservar bytes originales. `inspect_bundle` devuelve **ningún hallazgo**. El validador estructural no demuestra equivalencia semántica con fuente; se necesita un oracle independiente/attestation protegida.
- **Corpus real:** `test_real_g00_corpus.py` aparece como `SKIP` cuando faltan los tres JSON históricos en el checkout local; las pruebas sintéticas no sustituyen esa ejecución.

## 4. Distinciones normativas que no se pueden rebajar

Compiled ≠ SpecificationReady ≠ RefinementSufficient ≠ ImplementationRealized ≠ MateriallyQualified. GSL0 puede representar una propiedad histórica como `deferred_semantics` sin implementarla. G00-01-F01…F10 no están implementadas porque aparezcan diez registros IR. La fuente de verdad es `architecture/campaigns.json`, `g00_functional_refinement.json` y `g00_validation_plan.json` con estados originales intactos.

## 5. Requisitos del siguiente gate

Un bundle compilado sólo podrá ser calificado si (i) procede de fuentes pinneadas, (ii) preserva tipos, identidad, semántica y estructura, (iii) su source map está justificado, (iv) existe comparación semántica independiente capaz de detectar mutaciones con hashes regenerados, (v) el corpus G-00 real ha sido ejecutado y contrastado, (vi) la auditoría de implementación tiene sujeto/SHA exactos. La cualificación G-00 añade además 12 obligaciones padre, 120 cláusulas, 58 APIs, 120 test contracts, 36 adversarios y siete verticales realmente implementados y ejecutados bajo sus políticas.
