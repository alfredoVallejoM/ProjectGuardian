# G-00…G-13 — Protocolo de implementación productiva progresiva
Fecha: 2026-10-20. Estado: propuesta operativa de ejecución (no ratificación de ADR ni cierre de campaña).
Autoridad: `architecture/campaigns.json` (14 campañas; 163 obligaciones canónicas), `architecture/requirements.json`, `architecture/decisions.json` y refinamientos de cada campaña. La propuesta no modifica los IDs, el sentido ni el nivel de aceptación de ninguna obligación.

## 1. Objetivo operativo

Implementar completamente el producto ProjectGuardian mediante ciclos de autoría y revisión por **obligación funcional**, después por **campaña** y finalmente por **flujo real entre campañas**. Está prohibido declarar «terminada» una campaña solo porque se han publicado su especificación, un AST, un bundle GSL, una interfaz vacía, un número elevado de tests o un porcentaje favorable de cobertura de líneas.

Fuera de alcance de este procedimiento: la disponibilidad y la certificación de CTK-01 o de componentes no dependientes del propio desarrollo ProjectGuardian. No son una barrera para iniciar G-00. Los experimentos GSL-0 son un frente independiente; ni sustituyen al dominio G-00 ni conceden certificados de código.

## 2. Dos definiciones obligatorias de cierre

**DEVELOPMENT_COMPLETE por obligación:** código productivo en su owner; contratos públicos y errores tipados implementados; todos sus refinamientos funcionales satisfechos; pruebas positivas, negativas, propiedades, adversarios y verificadores correspondientes escritos; integraciones con productores y consumidores exigidas en el tramo desarrollado; ausencia de placeholders que simulen funcionalidad. No exige materializar el suite ni emisión de recibo.

**CAMPAIGN_CLOSED:** además del desarrollo total de todas las obligaciones originales, ejecución material real del candidato, revisor independiente cuando la política lo exija, replays/fixtures, pruebas de integración y E2E exigidas, límites de confianza declarados y receipts válidos. La ausencia de Gatekeeper G-09 debe seguir apareciendo como HOLD de confianza; no se emiten certificados ficticios.

Entre ambos quedan estados explícitos: NOT_IMPLEMENTED, IN_PROGRESS, IMPLEMENTED_CANDIDATE, DEVELOPMENT_COMPLETE, MATERIAL_VALIDATED y CAMPAIGN_CLOSED. Ninguna transición se deduce automáticamente de contar tests.

## 3. Unidad mínima de trabajo reproducible

Para cada obligación canónica `GXX-NN`:

- **Authority:** fuente inmutable, versión, texto original, refinamientos y decisiones aplicables; separar ratificadas de propuestas.
- **Meaning:** entradas, salidas, invariantes, errores/diagnósticos, supuestos, garantías, casos límite, explícito no-alcance.
- **Owner:** ruta(s) reales, dueño semántico único, dependencia permitida, interfaz estable con consumidores.
- **Construction:** implementación real, no stub, anotación, fixture disfrazado de runtime ni adaptador que replique reglas.
- **Verification:** tests directos para cada subcláusula, pruebas de fallo específico, propiedades y mutaciones que una implementación defectuosa **no** supera.
- **Integration:** llamadas productor→dueño→consumidor, prueba de dos proyectos, datos verosímiles y rechazo controlado de entradas no autorizadas.
- **Review:** auditoría adversaria independiente posterior a la autoría de la unidad completa, findings por cláusula y archivo; constructor corrige y reenvía.
- **Evidence:** SHA exacto, paths, tests desarrollados, ejecutados/no ejecutados, cobertura del contrato, auditoría, HOLD y límites declarados.

Una API implementada con firma correcta pero semántica incompleta permanece parcial. Una cláusula con test que solo comprueba existencia, shape, imports, mocks internos o contador permanece sin demostrar funcionalidad.

## 4. Algoritmo de avance por campañas

1. Leer las obligaciones originales de la campaña seleccionada y todos los refinamientos y auditorías; conciliar omisiones sin reducir la autoridad.
2. Formar una matriz de alcance *cerrada*: cada cláusula tiene owner, rutas de código, firmas, errores, test positivo y adversario, integración y criterio de aceptación. Los huecos se convierten en tareas explícitas, no desaparecen del denominador.
3. Ordenar trabajo por dependencias semánticas internas, no por facilidad de escribir tests. Las decisiones propuestas pueden materializarse como candidatos claramente etiquetados, pero no se promueven a autoridad sin ratificación.
4. Implementar un bloque funcional completo en archivos reales, añadiendo únicamente módulos que posean comportamiento productivo. El cambio es aditivo respecto de contratos ya certificados; una modificación exige análisis de impacto y pruebas de regresión.
5. Ejecutar una comprobación propia de completitud contra el texto original **antes** de entregar el bloque a un auditor distinto. Ninguna corrección disminuye expectativas previas.
6. Auditor independiente solo al terminar el bloque de autoría; informe de faltantes individual por obligación, fuente, API, test, adversario e integración. Reabrir las cláusulas fallidas y repetir hasta PASS de desarrollo u HOLD motivado.
7. Ejecutar suites materialmente cuando exista runner disponible. Separar `tests_written`, `tests_run`, `tests_pass`, y `claim_qualified`; preservar entornos, casos SKIP y costes.
8. Verificar consumidores existentes y los contratos reservados para campañas futuras. Si consumidor aún no existe, probar un contrato tipado y registrar una deuda de integración viva que bloquea el cierre correspondiente, **no** obligar a implementar prematuramente otra campaña.
9. Avanzar a la siguiente obligación y repetir. Cerrar campaña solo cuando su cierre sea una conjunción de todas las obligaciones y las integraciones exigidas.
10. Reabrir automáticamente el análisis de impacto de campañas anteriores cuando cambios posteriores afecten a su semántica o rutas públicas; conservar evidencia de regiones no afectadas.

## 5. Plan de dependencias, no atajos

| Frente | Contrato productivo necesario | Integración a preservar |
|---|---|---|
| G-00 | Identidad, proyectos, fuentes, ontología, autoridad, scope V4, estados, refs, schema, evaluador puro | Núcleo invocable sin Git/SQLite/LLM ni efectos |
| G-01 | ChangeSet, revisiones, evolución normativa y transporte de compromisos | Estado anterior recuperable, no sobrescritura |
| G-02 | Relaciones tipadas, SupportCone e ImpactCone | La clausura preserva obligaciones no satisfechas |
| G-03 | Orientación y contexto recuperado | Nada importante se pierde al resumir |
| G-04 | Paquetes y cierre de tareas | La suma de tareas no reemplaza suficiencia del padre |
| G-07 | Adaptadores reales, Git/código/fuentes | Observación no se eleva a norma |
| G-05 | Correspondencia especificación↔implementación | Exposición pública y rutas ejecutables |
| G-06 | Evidencias, auditoría y qualification | Mock o test escrito no acredita comportamiento |
| G-10 | Cobertura histórica, migración y preservación | Todo denominador y missing son explícitos |
| G-09 | Gatekeeper, autoridad y publicación segura | El candidato no cambia sus propias reglas |
| G-11 | CLI/API/MCP/UI productivos | La misma semántica en todas las interfaces |
| G-08 | Integración de agentes/humanos | Los agentes no se conceden autoridad |
| G-12 | Persistencia, recuperación y escala | Replays equivalentes, recuperación tras fallo |
| G-13 | Pilotos y calificación integral | Flujos de verdad de extremo a extremo |

Los requisitos de cierre originales siguen siendo vinculantes. El orden anterior es orientativo por dependencias, no reasigna competencias.

## 6. G-00: campaña activa prioritaria

Norma original: G00-01…G00-12. Refinamiento previsto: 120 cláusulas, 58 operaciones, 120 tests contractuales, 36 adversarios y siete escenarios verticales. No cuentan como construidos por estar descritos en la documentación ni en el experimento GSL-0.

Orden operativo G-00: B00 (reconciliación/decisiones) → B01 (IDs y estados mínimos) → B02 (Project+SourceUniverse) → B03 (objetivos/capacidades/propiedades/obligaciones) → B04 (scope V4) → B05 (Constitution/authority) → B06 (refs y schema) → B07 (evaluador puro) → B08 (suite e integración integral) → B09 (revisión independiente y material). B00-B09 **son cortes de trabajo internos**, no campañas nuevas y no alteran G00-01…12.

El desarrollo G-00 no debe detenerse a causa de CTK-01. Tampoco debe fingir implementados G-07/G-09: los limites de I/O, fuente externa, autenticación y publicación permanecen fronteras explícitas.

## 7. Criterios de prueba que no se pueden sustituir

- **No aceptable:** `assert x is not None` como demostración de contrato, test que ejecuta un mock en lugar del módulo real, documento con ID de test no implementado, regresión omitida, SKIP no declarado, prueba tautológica que comparte el mismo bug que el algoritmo, auto-recepción de un resultado de auditoría.
- **Aceptable:** cada falsación se introduce en una implementación perturbada o fixture hostil y el verificador específico emite el diagnóstico normativo correcto; pruebas diferenciales con oráculo independiente cuando hay reducción/compilación; e integración in-memory multi-proyecto para G-00 y real con Git y runners en campañas propietarias.
- **Protección:** un cambio de código certificado dispara análisis de cono de impacto; cambios documentales o aditivos fuera del corte no invalidan evidencia exacta sin relación con los artefactos protegidos.

## 8. Registro de progreso obligatorio por obligación

Campos mínimos: `campaign_id`, `obligation_id`, `authority_ref`, `source_sha`, `refinements_expected`, `refinements_implemented`, `apis_expected`, `apis_implemented`, `tests_authored`, `tests_executed`, `adversaries_authored`, `adversaries_executed`, `integration_scenarios`, `required_consumer_contracts`, `code_paths`, `review_findings`, `review_actor`, `candidate_sha`, `status`, `holds`.

Los contadores no son veredictos semánticos: cada item debe enlazar a prueba y función concretas. Estado ausente equivale a INCOMPLETE. Los cambios de presupuesto o nuevas dependencias no reducen el conjunto originalmente exigido.

## 9. Regla de implementación de la campaña siguiente

Puede comenzarse trabajo independiente de G-(n+1) sobre contratos tipados ya estabilizados de G-n, sin exigir que todo G-n tenga receipt material. **No** puede cerrarse G-(n+1) pasando por alto una dependencia semántica G-n incompleta. Una campaña anterior sigue abierta para regresiones y correcciones cuando un consumidor posterior descubra un fallo.

## 10. Reglas del repositorio y verdad de publicación

- Desarrollo sobre `main` sin abrir ramas nuevas salvo orden explícita; jamás GH Actions como condición de cierre.
- No modificar `architecture/campaigns.json` ni refinamientos originales para falsear el estado; toda enmienda genuina requiere autoridad y trazabilidad.
- No confundir un test local aislado con un test ejecutado en el SHA remoto.
- No publicar estado DEVELOPMENT_COMPLETE si queda una implementación exigida pendiente.
- Registrar cada hallazgo real como corrección del dueño semántico; no crear segundo evaluador/otro AST para taparlo.
- El producto se considera funcionalmente terminado cuando **las 163 obligaciones canónicas**, sus refinamientos exigibles y los E2E intercampaña están efectivamente desarrollados. La certificación material completa es un estado posterior distinto.

## 11. Trabajo siguiente que depende del constructor

Primero desarrollar el **runtime productivo** de G00-01 sobre `src/guardian/domain/identity.py` con tests nominales, aliases, colisiones, codecs y semántica de revisión. Después completar sus enlaces a resolver y proyecto con G00-02/G00-08; continuar G00-03…12. Mantener para cada paso el diff de obligación y un indicador explícito de lo implementado versus lo que todavía falta.
