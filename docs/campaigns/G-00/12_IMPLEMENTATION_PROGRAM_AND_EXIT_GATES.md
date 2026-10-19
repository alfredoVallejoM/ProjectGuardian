# G-00 / Programa de implementación, integración y criterios de cierre

**Estado de esta entrega:** PLANIFICADO, NO IMPLEMENTADO. **No alterar la campaña G-00 original:** 12 obligaciones y su desarrollo de 120 cláusulas subordinadas. El programa se organiza por unidades funcionales, no por metas numéricas de archivos o líneas.

## Bloques de desarrollo completos

| Corte | Responsabilidad | Prerequisitos | Salida obligatoria |
|---|---|---|---|
| `B00 — Design freeze` | Reconciliar 12 obligaciones originales con 120 cláusulas, 34 PG-REQ y ADR aplicables; ratificación o HOLD de decisiones | Especificación publicada | Snapshot normativo de G-00, referencias y alcance aprobados |
| `B01 — Identity kernel` | G00-01: ProjectId/EntityId/RevisionId/Digest/Alias, parsers, codecs, diagnoses; G00-07 enums básicos | B00 | Identidades tipadas y tests de confusión |
| `B02 — Project+Sources` | G00-02/03: aislamiento, modos embebido/sidecar/federado, fuente y universo, import/grant declarativo | B01 | Proyecto y SourceUniverse con falsaciones |
| `B03 — Commitment ontology` | G00-05/07: Objective, Capability, Property, Obligation, Campaign, ArchitectureRevision y estados distintos | B01, B02 | Objetos normativos validados y relación por refs |
| `B04 — Scope semantics` | G00-06: SupportProfile, AST de applicability, cuatro valores, testigos y limits | B01, B03 | Motor puro de scope con truth tables |
| `B05 — Constitution and authority` | G00-04/11: Rule/Decision/AuthorityContext, precedencia parcial, conflicto, enmiendas de diseño | B02, B03, B04 | RuleSets tipados, ConflictRecords sin self-approval |
| `B06 — Reference/schema boundary` | G00-08/09: integridad en snapshots, readers versionados, normative features | B01–B05 | Validadores exhaustivos, decode/encode y límites de schema |
| `B07 — Pure evaluator` | G00-10: evaluación de reglas con cobertura completa, applicability, precedencia, facts, presupuesto e informes | B04–B06 | API de evaluación determinista y falsaciones |
| `B08 — Contract test integration` | G00-12: 120 clause tests, 36 adversarios y siete verticales; imports architecture, reviewer-ready receipts | B01–B07 | Desarrollo completo de suites, integración y reporte |
| `B09 — Independent review / material qualification` | Auditoría adversaria por obligación, ejecución material, correcciones y receipts sobre SHA candidato | B08 | Cierre material de G-00, no certificación completa de Guardian |

**Importante:** B00–B09 son unidades de desarrollo dentro de G-00, no diez campañas canónicas nuevas. Su orden permite explorar contratos paralelos cuando no comparten ownership, pero sus condiciones de cierre son explícitas.

## Entregables por bloque

### B00
- Resolver si las cláusulas detalladas son refinamientos legítimos de G00-01…12 o modificaciones de alcance.
- Fijar símbolos de API y envelopes de schema; ratificar la política de IDs/SourceUniverse, applicability y authority.
- Congelar baseline/versión; registrar decisiones abiertas en un ledger, nunca presumir approval.

### B01
- Nominal wrappers y codecs; defectos de IDs/tipos; eliminación de posibles dependencias a clock/RNG en funciones puras.
- Objetos \`Result\`, \`Diagnostic\`, \`TypedStatus\`, distintos de certificado.
- Tests de parser y propiedades de roundtrip con casos adversarios.

### B02
- Definir ProjectDefinition/SourcePolicy/SourceUniverseRevision; referencias de fuentes con cortes completos.
- \`TrustedImportGrant\` es un input de contexto, no una garantía de autenticación producida por G-00.
- Fixtures de dos proyectos y cortes federados/históricos solapados.

### B03
- Enunciados del compromiso como entidades distintas y referidas por revisión.
- Contratos de aceptación y falsación; normas de hito y membership sin ciclo de vida persistido todavía.
- Tests de relaciones compartidas que no duplican autoridad.

### B04
- Gramática AST de predicados tipados y semántica \`(positive_evidence,negative_evidence)\`.
- Operadores AND/OR/NOT, complete/incomplete features, conflicto y MissingEvidence.
- Budget determinista; sin plugin runtime ni solvers externos.

### B05
- RuleRevision/DecisionRevision, AuthorityContext tipado, ConflictRecord y precedencia.
- El evaluador no valida firmas reales: G-09 aporta identidad y approvals de confianza.
- Tests de conflictos solapados/disjuntos, latest-wins falso, proposal≠ratified.

### B06
- Resolver local de referencias, tipos, scopes, foreign imports.
- Esquemas JSON 2020-12 versionados y envelope; features normativas desconocidas se rechazan.
- Los cambios de significado y las migraciones de schemas históricos son G-01/G-12.

### B07
- Evaluador \`evaluate_constitution\` con registry de predicados puros, sin I/O.
- Enumeración completa de RuleSets y diagnóstico por regla.
- Report de recurso limitado, fact missing, unknown evaluator, conflict y non-applicable.

### B08
- Testear los contratos de las 120 cláusulas con suites agrupadas por comportamiento, no un test trivial por nombre.
- Integrar los siete escenarios G00-V01…V07 y las 36 mutaciones negativas ADV-01…ADV-36.
- Generar un paquete de handoff completo: módulos reales, pruebas escritas, source refs, desviaciones y HOLDs.

### B09
- Un revisor independiente (humano u otro agente, según capacidad real disponible) recibe obligaciones originales, pruebas y código, no solo autoevaluación.
- A3/reviewer interviene después de B08, y devuelve findings por obligación y documento. Constructor corrige y se repite auditoría.
- Ejecutar pytest/typing/schema tests reales, comprobación de imports, test de dos proyectos, property/mutation tests y presupuesto acordado.
- Emitir receipt material según infraestructura confiable disponible. No afirmar \`G00_CAMPAIGN_CLOSED\` si el perímetro aún no puede garantizar las condiciones exigidas; puede registrarse \`IMPLEMENTED_CANDIDATE\` o \`HOLD_TRUST_ROOT\`.

## Bootstrap de confianza: el problema de la primera campaña

**No existe todavía el Gatekeeper G-09.** Eso significa que sería falso decir que G-00 ya está protegido por el mecanismo que todavía estamos diseñando. Para iniciar de forma segura:
1. Congelar un baseline normativo aprobado por autoridad humana sobre la rama/configuración de trabajo.
2. Prohibir que el autor aplique directamente changes a las reglas de aceptación sin revisión humana de cambios.
3. Ejecutar un validador mínimo externo a los cambios candidatos, bajo control del mantenedor, para comprobar que el corte original de obligaciones se conserva.
4. Requerir revisión independiente de código, tests y reglas constitucionales de G-00.
5. Registrar los límites de confianza efectivos; no simular un receipt firmado.
6. Después de G-09, migrar gradualmente los flujos de admisión a un Gatekeeper verdaderamente protegido, con comprobaciones de equivalencia y sin reescribir la historia.

No prometer enforcement automático antes de que exista una barrera real. El bootstrap externo es un procedimiento de proceso y permisos, no una excepción que permita rebajar G-00.

## Contratos consumidores

| Consumidor | Qué exige de G-00 | Qué desarrollará posteriormente |
|---|---|---|
| G-01 Evolution | IDs, ObligationRevision, CampaignRevision, Source/AuthorityRefs | Apply, ChangeSet, historia, event store |
| G-02 Graph | EntityRefs, relation kinds base, typed ScopeExpression | Grafos n-arios, closure, soporte, impacto |
| G-03 Orientation | informes tipados, normas y fuentes | Context retrieval y vistas narrativas |
| G-04 Task Compiler | obligación, applicability, milestone | RequiredObligationClosure y WorkPackage |
| G-05 Compliance | ArchitectureRevision, Property, Contract | Inspección real de código vs especificación |
| G-06 Assurance | VerificationSpec types, result axes | Runs, Evidence, Claims y Certificates |
| G-07 Adapters | SourceRef, ProjectId, SourceUniverse descriptor | Lectura Git/AST/consumidores |
| G-09 Gatekeeper | ConstitutionRevision, AuthorityContext interfaz, Report | Firma/identidad/permiso/autorización/publicación |
| G-10 Coverage | SourceUniverse, estados y compromiso | Denominadores certificados y migración |
| G-11 Interfaces | Result/Diagnostic/Status/Scope | CLI/API/UI/MCP y navegación |

## Definición de avance medible

No declarar porcentaje por archivos presentes. Para cada obligación original G00-XX se requiere:
- 10 cláusulas funcionales especificadas y revisadas/ratificadas.
- Contratos de objetos/APIs/errores implementados.
- Tests positivos y falsadores desarrollados y enlazados.
- Integración entre entidades y evaluador demostrable por tests.
- Ningún placeholder o implementación limitada presentada como completa.

La auditoría debe listar cada uno de los 12 padres y sus 10 cláusulas, distinguir \`SPECIFIED\` / \`DEVELOPED\` / \`AUDITED\` / \`MATERIAL_PASS\` / \`QUALIFIED\` sin confundir estados.

## Condición de salida

\`G00_DEVELOPMENT_COMPLETE\` solo si todo G-00 original y cada cláusula aplicable está implementada, incluida autoría de pruebas/verificadores. \`G00_CAMPAIGN_CLOSED\` exige material execution + adversarial review + integration + receipts válidos para el ámbito G-00. Nunca implica que G-01…G-13 o la plataforma completa estén terminadas.


## Enmienda de planificación propuesta (sin cambiar B00…B09)

B00 debe examinar la suficiencia de 120 subcláusulas respecto a los doce padres, separar enlaces de fuente de implicaciones semánticas y preparar la raíz externa V0. [Especificación corregida de la etapa](../../revision-2026-10-19/03_SELFHOST_V0_AND_SH00_SH12.md). No se añade una obligación histórica nueva ni se ratifica GSL-0. B01…B09 desarrollan las mismas 12 obligaciones, con testigos de refinamiento cuando el contrato los exija. Ningún resultado del candidato se utiliza como único oráculo de su propia corrección.
