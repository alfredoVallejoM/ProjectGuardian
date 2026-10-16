# G-00 / SupportProfile y semántica exacta de aplicabilidad

**Obligación primaria:** G00-06. **Owners:** \`domain/scope.py\`, \`constitution/evaluator.py\`.

## Problema

Una obligación no se aplica a todos los proyectos, compilaciones y dominios matemáticos por igual. Tampoco se puede excluir una obligación si faltan datos. Un motor booleano convencional tiende a convertir "propiedad ausente" en falso y eliminar indebidamente trabajo. G-00 debe evitarlo estructuralmente.

## SupportProfile y dimensiones

\`SupportProfile\` lleva \`project_id\`, \`project_revision\`, \`candidate_ref\` (si es relevante), \`source_universe_ref\`, \`milestone\`, \`features\`, \`platform\`, \`toolchain\`, \`domain\`, \`representation\`, \`consumers\`, \`resource_profile\`, \`verification_policy_ref\` y extensiones tipadas versionadas. Dimensiones desconocidas son explícitas: absent no significa false. Un valor matemático complejo requerirá un predicado especializado, no un parser de texto libre.

\`ScopeExpression\` es un AST, no código Python evaluable:
- \`Atom(field, operator, value, evidence_ref)\` con operadores registrados (typed equality, contains, range, presence).
- \`All(exprs)\`, \`Any(exprs)\`, \`Not(expr)\`, cada uno con reglas de aridad.
- \`VerifierPredicate(verifier_id, input_contract, version)\` admite un resultado **suministrado externamente**; G-00 no ejecuta scripts/plugins de proyecto.
- \`TrueConst\` y \`FalseConst\` solo como constantes explícitas autorizadas. Un \`All([])\` implícito no se convierte silenciosamente en TRUE para una obligación normativa.

## Cuatro valores como pares de evidencia

Para evitar convertir conflictos en desconocimiento, representamos una evaluación como dos bits:
\[
v=(t,f),\quad t,f\in\{0,1\}
\]
donde \(t\) indica soporte de aplicabilidad y \(f\) soporte de inaplicabilidad.

| Valor | Par | Interpretación |
|---|---|---|
| \`YES\` | (1,0) | Hay testigo para aplicar, sin contrario |
| \`NO\` | (0,1) | Hay testigo de exclusión, sin contrario |
| \`UNKNOWN\` | (0,0) | No hay evidencia suficiente en ninguna dirección |
| \`CONFLICT\` | (1,1) | Hay evidencia positiva y negativa incompatible |

Para \`AND\`, \((t_a\land t_b,\ f_a\lor f_b)\); para \`OR\`, \((t_a\lor t_b,\ f_a\land f_b)\); para \`NOT\`, intercambiar \((f,t)\). Estos son operadores sobre información suministrada, no afirmaciones de verdad matemática absoluta. Deben conservar las referencias a los testigos positivos/negativos y su ámbito.

**Nota sobre casos mixtos:** \`AND(CONFLICT, NO)\` puede resultar \`NO\` a nivel de aplicabilidad del compuesto porque el NO concluyente excluye el conjunto, pero el conflicto interno debe quedar en el informe de diagnóstico. No borrar conflictos internos de la traza. \`OR(CONFLICT, YES)\` puede resultar \`YES\`, sin ocultar la contradicción en el operando. El evaluador de admisión puede bloquear aun cuando la expresión final esté decidida si la política exige consistencia de testigos.

## Separar aplicabilidad y exigibilidad temporal

\[
\operatorname{Due}(o,S,m)
=
\operatorname{Approved}(o)
\land \operatorname{Applicable}(o,S)
\land \operatorname{CommittedAt}(o,m).
\]

Las tres evaluaciones tienen procedencia distinta. Una obligation aprobada FUTURE puede ser aplicable pero no exigible en el milestone current. G-00 proporciona los tipos de compromiso y la evaluación local de predicados; G-01/G-10 calculan memberships/versiones y cobertura completa.

\`UNKNOWN\` o \`CONFLICT\` nunca se tratan automáticamente como \`NOT_APPLICABLE\` para quitar obligaciones de un paquete que pretende cerrarse.

## Políticas de perfil y verificador

\`ProfileDimensionSchema\` identifica tipo, operadores válidos, namespace y versiones. Una extensión desconocida **normativa** produce \`UNKNOWN_REQUIRED_FEATURE\`, no se ignora. Los predicados referidos a leyes matemáticas, source exhaustiveness o certificados externos devuelven \`UNKNOWN\` en G-00 salvo que reciban una \`VerifiedPredicateObservation\` externa con procedencia. Ni siquiera ese dato equivale al proceso criptográfico del Gatekeeper, responsabilidad G-09.

## Algoritmo propuesto

\`evaluate_scope(expr,profile,facts,budget)\`:
1. Validar AST, tipos de campo, operador y límites estructurales.
2. Para cada átomo, obtener testigos positivos/negativos según hechos explícitos con mismo proyecto/revisión/ámbito.
3. Si falta hecho, responder UNKNOWN; si ambos, CONFLICT.
4. Evaluar composición con los operadores de dos bits, conservando diagnósticos internos.
5. Cortar ante profundidad/nodos/tiempo presupuestados por steps deterministas y devolver \`RESOURCE_LIMITED\` **como error de evaluación**, no \`NO\` ni \`YES\`.
6. Emitir \`ApplicabilityResult(value,positive_witnesses,negative_witnesses,diagnostics,policy_revision,profile_revision)\`.

**No usar reloj del sistema ni red para decidir el predicado.** Si hace falta fecha actual se pasa como dato de entrada firmado/fijado.

## Casos positivos y adversarios

- \`feature contains X\` cuando X está presente con testigo produce YES.
- \`feature contains X\` cuando la lista se declara **completa** y X no está produce NO.
- Lista features ausente/incompleta: preguntar X produce UNKNOWN.
- Dos fuentes incompatibles ofrecen YES/NO para X: CONFLICT.
- \`NOT(UNKNOWN)=UNKNOWN\`; \`NOT(CONFLICT)=CONFLICT\`.
- \`AND(YES,UNKNOWN)=UNKNOWN\`; \`OR(NO,UNKNOWN)=UNKNOWN\`.
- \`AND(YES,NO)=NO\`; \`OR(YES,NO)=YES\`.
- Operador aplicado a tipo erróneo es \`INVALID_SCOPE_EXPRESSION\`, no FALSE.
- Predicado externo desconocido devuelve UNKNOWN y no ejecuta código.
- \`All([])\` en regla normativa se rechaza; \`TrueConst\` explícito requiere revisión/autoridad.
- Profile de proyecto B no puede aplicar una norma A sin import.
- Condición futura ratificada no se mueve a current por el constructor.

## Fronteras

G-00 define semántica local y modelado. G-02 añade evaluación de expresiones de soporte ALL/ANY sobre **evidencias del grafo** (distinto de applicability). G-04 compila cierre de obligaciones. G-06 evalúa suficiencia de pruebas. G-10 calcula denominadores. No mezclar esas cuatro operaciones.
