# G-00 / Constitución, decisiones, autoridad y resolución de conflictos

**Obligaciones:** G00-04, G00-10, G00-11. **Owners:** \`domain/constitution.py\`, \`domain/authority.py\`, \`constitution/precedence.py\`, \`constitution/authority_resolution.py\`, \`constitution/evaluator.py\`.

## El problema de autoridad

No existe una única escala de "fuente más confiable". El código autenticado tiene autoridad sobre **hechos observados de ese código**, pero no sobre la voluntad contractual del proyecto. Una decisión ratificada tiene autoridad normativa, pero no puede cambiar retrospectivamente qué bytes contenía un commit. Una inferencia de agente carece de autoridad para ratificar aunque sea plausible.

G-00 modela tipos de afirmación y relaciones de precedencia **según dominio**. La arquitectura actual y el código observado tienen significados diferentes, que no deben fusionarse.

## Estructuras fundamentales

**\`ConstitutionRevision\`:** \`project_id\`, \`constitution_id\`, \`revision_id\`, referencias inmutables a RuleRevisions y Decisions ratificadas, ámbito, source universe, compatibilidad de versiones, exclusiones explícitas y precondiciones.

**\`RuleRevision\`:** \`rule_id\`, \`revision_id\`, \`rule_kind\`, \`scope_expression\`, \`requirement_predicate\`, \`applicability\`, \`authority_ref\`, \`enforcement_profile\`, \`verification_refs\`, texto de fundamento y restricciones de cambio. No se admiten funciones Python arbitrarias cargadas desde JSON de proyectos.

**\`DecisionRevision\`:** \`decision_id\`, \`proposal_revision\`, \`state\`, \`actor_ref\`, \`approval_record_ref\`, \`affected_contracts\`, \`rationale\`, \`alternatives\`, \`effective_scope\`, \`supersedes\`, \`source_refs\`. La validación distingue que **un registro diga** \`RATIFIED\` de que una autoridad protegida haya confirmado una aprobación. La primera no prueba la segunda.

**\`AuthorityContext\`:** información ya autenticada por un perímetro superior: IDs de decisiones válidas, roles/capacidades de principals y versiones de política admitidas. G-00 acepta únicamente este contexto explícito en su interfaz pura; **no lo construye leyendo strings autocertificados**. En pruebas puede utilizar un context factory de confianza del test harness.

**\`ConflictRecord\`:** identificación estable del conflicto, conjunto de afirmaciones incompatibles, tipos de autoridad, intersección de ámbitos, testigos de incompatibilidad, propiedades dependientes y política de resolución requerida. No resuelve el conflicto por sí mismo.

## Clases de norma

| Clase | Ejemplo | Evaluabilidad de G-00 |
|---|---|---|
| \`IDENTITY_INVARIANT\` | No confundir RevisionId y EntityId | Completa, con validación pura |
| \`REFERENCE_INTEGRITY\` | Una referencia pertenece al proyecto y versión | Completa para snapshot en memoria |
| \`SOURCE_POLICY\` | Fuente permitida o requiere importación aprobada | Estructural, evidencia de aprobación externa como input |
| \`OWNERSHIP_CONSTRAINT\` | Owner único para una clase/ámbito | Reglas estructurales sobre catálogo de ejemplo; grafos completos G-02 |
| \`ARCHITECTURE_CONSTRAINT\` | Dependencia de módulos autorizada | Contrato de regla y hechos tipados; extracción real G-05/G-07 |
| \`APPLICABILITY_CONSTRAINT\` | Exigible solo en cierto perfil | Evaluación pura con cuatro valores |
| \`VERIFIER_REQUIRED\` | Necesita evidencia formal | G-00 solo identifica la obligación, no ejecuta prueba |
| \`CUSTOM_DOMAIN_POLICY\` | Ley algebraica especializada | Descriptor y \`UNKNOWN\` hasta adaptador confiable |

Un procedimiento que no comprende un \`rule_kind\` o una característica normativa debe bloquear el juicio, no ignorarla y sumar un PASS.

## Semántica de precedencia y conflictos

El proceso de evaluación comprueba:
1. ¿Las afirmaciones refieren la misma entidad, propiedad y **ámbitos con intersección demostrada**?
2. ¿Son del mismo género (hecho observado, obligación vigente, propuesta, aprobación) o tipos distintos que conviven sin contradicción?
3. ¿Existe una relación de reemplazo/supersesión **aprobada y vigente** que establece precedencia?
4. Si no existe, ¿las dos restricciones no pueden satisfacerse conjuntamente?
5. Si hay desacuerdo, generar \`ConflictRecord\` y bloquear solo las operaciones/cualificaciones dependientes del conflicto, preservando otras partes del proyecto.

La novedad cronológica **no** aporta precedencia por defecto. Tampoco basta con un hash de mayor longitud o un documento con el título "FINAL".

## Contratos de operación

- \`validate_constitution(snapshot, catalog)\` → \`ConstitutionValidation\`: IDs conocidos, reglas no duplicadas, ámbito y source refs, compatibilidad de features, decisiones/approvals consistentes.
- \`evaluate_authority(subject, action, context)\` → \`Authorized | RequiresApproval | Denied | Unknown\`; el resultado es una evaluación **condicional** al context de autoridad suministrado, no comprobación criptográfica.
- \`detect_conflicts(assertions, profile, policies)\` → conjunto de \`ConflictRecord\`, no mutación de normas.
- \`resolve_precedence(assertion_a, assertion_b, approved_supersession)\` → \`Precedes | Coexists | Conflict | Unknown\`, con reasons.
- \`propose_amendment(rule, revised, impact)\` → descriptor \`AmendmentRequest\` de diseño; G-09 valida y publica.

## Invariantes

- \`PROPOSED\` no puede convertirse en \`RATIFIED\` por cambio de nombre o de campo.
- Mismo contenido documental con aprobadores diferentes no equivale a misma autoridad.
- Una fuente Git observada no puede modificar una regla constitucional automáticamente.
- Una regla con aplicabilidad \`UNKNOWN\` no se ignora para permitir el cierre.
- Un conflicto se conserva con testigos y decisión pendiente.
- Un \`AuthorityContext\` debe corresponder a una revisión política y un ámbito definido.
- Una nueva versión constitucional no cambia la evaluación de una revisión anterior si ambas están fijadas.

## Pruebas positivas, negativas y adversarias

**Positivas:** dos fuentes observadas de épocas distintas no se interpretan como normas contradictorias; regla vigente para proyecto A no se aplica a B; decisión ratificada con token externo de test tiene precedente explícito sobre decisión superseded; dos reglas compatibles coexisten.

**Negativas:** propuesta autodenominada RATIFIED sin comprobación externa; duplicación de RuleId para revisiones distintas sin linaje; contexto de autoridad de otro proyecto; alegación "este es el archivo más nuevo" como justificación suficiente; importación interproyecto sin decisión; \`CustomPolicy\` no registrado tratado como PASS.

**Adversarios:** alterar aprobador textual y conservar hash de fuente; falsificar precedente temporal; ofrecer dos reglas opuestas sobre ámbitos intersectantes; presentar dos reglas de ámbitos disjuntos como conflicto; ocultar una de las fuentes de conflicto; cambiar la policy en el mismo candidato.

**Fronteras:** \`constitution/precedence.py\` detecta conflictos; \`constitution/evaluator.py\` evalúa; \`governance/protected_policy.py\` (G-09) carga política confiable; \`governance/approval.py\` autentica decisiones; no duplicar la autoridad.
