# G-00 — Ampliación contractual CCRR (PROPUESTA)

Autoridad: NO RATIFICADA. Todas las 12 obligaciones originales de architecture/campaigns.json se conservan, sin afirmar código, tests o certificación material.

## Objetivo y frontera

Definir modelo de proyectos y compromisos, fuentes, identidades, constituciones, perfiles, aplicabilidad y estados.. Exclusión: No certificar cumplimiento científico ni crear agentes antes del modelo.. Hito selfhost: SH-00/01/02. Interfaces: INT-01, INT-02. GSL-0 no diseñado; B00…B09 y 120 cláusulas originales siguen como alcance propuesto.

## Matriz íntegra

Cada fila añade una condición de ingeniería candidata y conserva la falsación original. No es un nuevo identificador normativo.

| ID | Realización exigida originalmente | Refuerzo de garantía propuesto | Falsación original |
|---|---|---|---|
| G00-01 | IDs de proyecto, entidad, revisión y digest nominalmente distintos, serializables y con validación | Identidades nominales y estabilidad entre rutas | Dos entidades colapsan por compartir nombre o contenido |
| G00-02 | Project y fuente de autoridad por proyecto; políticas de importación independientes | Aislamiento de autoridad por proyecto | Se admite fuente de otro proyecto sin autorización |
| G00-03 | Universo de fuentes con commits, documentación, inclusiones, exclusiones y límites explícitos | Corte de fuentes completo y límites | Se certifica cobertura sin delimitar fuentes |
| G00-04 | Jerarquía de normas y decisiones con RATIFIED distinto de PROPOSED, autorización y precedencia | Propuesta no es ratificación | Propuesta se ratifica sin identidad de aprobador |
| G00-05 | Modelos independientes de Objective, Capability, Property y Obligation | Ontología de contratos y papeles | Capacidad se confunde con ImplementationUnit |
| G00-06 | SupportProfile tipado y predicados YES/NO/UNKNOWN/CONFLICT conservadores | Aplicabilidad cuatro-valuada | UNKNOWN se interpreta como NOT_APPLICABLE |
| G00-07 | Dimensiones source, implementation, audit, material, assurance, migration sin flag completed mutable | Estados ortogonales | PASS de test modifica autoridad científica |
| G00-08 | Referencias internas, revisión esperada y rutas interproyecto validadas | Referencias por revisión | Se admite referencia inexistente o cruzada |
| G00-09 | JSON Schema con normative features, validación de payload y versiones incompatibles | Features normativas versionadas | Se ignoran características normativas que el lector desconoce |
| G00-10 | Función de evaluación de normas sin E/S ni dependencia del clock | Evaluación pura determinista | Un mismo input genera resultados diferentes por estado externo |
| G00-11 | ConflictRecord con fuentes incompatibles y bloqueo de afirmaciones derivadas | Conflictos sin latest-wins | El sistema elige descripción más reciente silenciosamente |
| G00-12 | Pruebas positivas, negativas, invariantes de identidad, source scope y authority | Pruebas reales por obligación | Mutación constitucional no detectada produce PASS |

## Suficiencia e integración

La conjunción de hojas no acredita automáticamente la campaña. Generar RefinementCase con G objetivo, hijos D, bridges J, hipótesis A y PO para justificar A∧D∧J⇒G, comprobando además factibilidad. INT-01, INT-02 se ensaya sobre el propio ProjectGuardian con oráculo V0 y caso de mutación independiente.

Ataques de referencia: PROPOSED→RATIFIED, identidad tras mover ruta, UNKNOWN→NO, ejecución ficticia. Mantener UNKNOWN/HOLD cuando falte semántica o prueba, sin cambiar el contrato original.

## Criterio de cierre

Desarrollo terminado = todas las obligaciones originales y derivadas aplicables con implementación, pruebas, adversarios, verificadores e integración autoradas. Cierre material = además ejecución sobre candidato exacto, auditor independiente tras fin de bloque, recibos y autorización. La gramática/contrato específico de GSL-0 queda para discusión posterior.
