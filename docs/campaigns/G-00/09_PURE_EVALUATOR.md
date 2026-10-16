# G-00 / Evaluador constitucional puro — contrato de funcionamiento

**Obligaciones:** G00-04, G00-06, G00-10, G00-11 y G00-12. **Owner:** `constitution/evaluator.py` con `constitution/precedence.py`, `constitution/invariants.py` y tipos de `domain/`. **Estado:** no implementado.

## Naturaleza del motor

El evaluador interpreta **normas tipadas y predicados estructurados confiables**. No es un LLM, un programa que ejecuta expresiones arbitrarias del proyecto ni un demostrador científico. La misma entrada, incluso si el orden de inserción de los diccionarios cambia, produce el mismo resultado ordenado.

`evaluate_constitution(request, trusted_registry) -> ConstitutionEvaluationReport`. La solicitud recibe explícitamente ConstitutionRevision, ReadOnlyProjectView, FactSet, SupportProfile, AuthorityContext **ya autenticado por un actor exterior**, StepBudget y candidate revision. El dominio no lee reloj, filesystem, Git, red ni variables ambientales.

## Pipeline contractual

1. **Validar entradas.** Verificar esquema/normative features, ProjectId, SourceRefs, policy revision, regla duplicada y tipos de datos. Fallo estructural es INVALID_INPUT y **no** un FAIL matemático.
2. **Congelar RuleSet exigible.** Enumerar todas las RuleRevisions vigentes para proyecto/revisión. Si falta un kind normativo soportado por la constitución, registrarlo como RULE_UNKNOWN, no omitirlo.
3. **Aplicabilidad.** Evaluar ScopeExpression con YES, NO, UNKNOWN, CONFLICT y testigos. NOT_APPLICABLE requiere NO con evidencia; UNKNOWN no reduce el denominador.
4. **Precedencia.** Resolver DecisionRefs y overrides mediante AuthorityContext externo; registrar ConflictRecords con fuentes y scopes.
5. **Evaluación local.** Para reglas aplicables, despachar funciones puras de un `TrustedRuleEvaluatorRegistry` de RuleKinds/versiones conocidas. Una ley de dominio sin verificador admitido produce UNKNOWN_REQUIRED_VERIFIER.
6. **Recopilar TODOS los resultados.** Una regla fallida no borra conflictos de otra; un resultado favorable no oculta reglas pendientes. Diagnósticos por rule ID, cause, witness y path.
7. **Presupuestos.** Si se agotan steps/rules/depth/nodes, devolver RESOURCE_LIMITED con lista de reglas sin examinar. Nunca PASS por ejecución parcial.
8. **Salida determinista.** Ordenar reglas y causas por ID; emitir report con constitution revision, candidate, coverage qualifier y límites.
9. **No mutar ni certificar.** El resultado no es un receipt autenticado, ni una decisión ratificada, ni permiso de publicación. G-09 aplica el Gatekeeper verdadero.

## Tipos propuestos

`EvaluationRequest(project_id, constitution_ref, project_view, facts, profile, authority_context, candidate_ref, evaluation_budget)`.

`RuleEvaluation(rule_ref, applicability, verdict, positive_witnesses, negative_witnesses, missing_refs, conflicts, diagnostics, evaluator_id)`.

`ConstitutionEvaluationReport(request_ref, policy_ref, candidate_ref, rule_results, examined_rule_ids, unexamined_rule_ids, aggregate_verdict, resource_status, coverage_scope)`.

Errores distintos: INVALID_INPUT, UNSUPPORTED_NORMATIVE_FEATURE, UNKNOWN_RULE_KIND, MISSING_AUTHORITY_CONTEXT, MISSING_FACT, RULE_CONFLICT, EVALUATION_RESOURCE_LIMITED, INTERNAL_EVALUATOR_ERROR. Un error operativo no prueba que una propiedad sea falsa.

## Agregación

- PASS constitucional estructural solo con todas las reglas obligatorias examinadas, condiciones aplicables comprobadas y ninguna incertidumbre pendiente.
- FAIL por incumplimiento demostrado; puede coexistir con CONFLICT y UNKNOWN, todos mostrados.
- UNKNOWN cuando falta evidencia o un verificador.
- CONFLICT cuando se poseen testigos incompatibles que afectan el juicio.
- NOT_APPLICABLE por regla y scope mediante exclusión acreditada.
- RESOURCE_LIMITED nunca se convierte en un veredicto favorable.
- El resultado de G-00 **no equivale a ADMISSION_PASS**, que necesita G-09.

## Predicados iniciales de G-00

| Regla | Inputs | Verificación |
|---|---|---|
| `identity.kind_separation.v1` | Typed IDs, refs | No equiparar identificadores de clases distintas |
| `reference.project_isolation.v1` | ProjectView, imports | Sin imports implícitos |
| `source.cut_immutability.v1` | SourceUniverse | Cortes fijos o HOLD |
| `normative.ratification_required.v1` | Decision, AuthorityContext | Sin ratificación por texto |
| `scope.four_valued.v1` | Expression, Profile | Semántica YES/NO/UNKNOWN/CONFLICT |
| `status.axis_separation.v1` | TypedStatus | No promocionar ejes |
| `architecture.dependencies_declared.v1` | ArchitectureRevision + observed facts | Comprobar restricciones cuando facts existen |
| `authority.conflict_localization.v1` | Claims y ámbito | Sin resolver por fecha |
| `normative.non_erasure_precheck.v1` | Dos conjuntos de refs explícitos | Señalar pérdidas, full evolution pertenece a G-01 |

## Tests obligatorios

Determinismo con permutación de facts; no mutación de inputs; corpus con dos proyectos aislados; ratificación falsa; reglas desconocidas; applicability UNKNOWN/CONFLICT; NOT_APPLICABLE con evidencia; reglas de scope disjunto; conflictos con testigos; budget agotado y diagnósticos de reglas no evaluadas; mixed FAIL+CONFLICT sin pérdida; fuente externa no autorizada; verificador externo ausente; registro de RuleKind desconocido no produce PASS; orden de dict no altera informe.

## Prohibiciones de implementación

No `eval/exec` dinámicos, no Python callbacks importados desde el proyecto como política de confianza, no lógica de permisos hardcodeada desde un campo `role`, no I/O dentro del evaluador, no reportar certificado material, no usar tests que solo comprueben nombres de funciones.

