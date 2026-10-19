# G-04 — Contrato de extensión CCRR

**DISEÑO PROPUESTO, no ratificado ni ejecutado.** 12 obligaciones originales intactas. Autoridad histórica: architecture/campaigns.json y docs/campaigns/G-04.md.

## Objeto y límites

Generar WorkPackages completos por cierre de obligaciones, scope y milestone.. No bajar el contrato para adecuarlo a contexto o token budget.. Hito de autoaplicación: SH-05. Integración: INT-02/03/07. Prerrequisitos originales: G-01, G-02.

## Matriz de revisión exhaustiva por obligación

| ID original | Implementación original | Refuerzo/puente propuesto | Falsación original |
|---|---|---|---|
| G04-01 | Identificar capacidad, target scope, milestone y revisions originales | Contrato y perfil exactos | El encargo carece de identidad de contrato |
| G04-02 | Calcular conjunto aplicable completo desde fuente normativa y relaciones | Closure incluye suficiencia/bridges | Obligación indirecta omitida |
| G04-03 | Incluir invariantes, forbidden changes y policy snapshot | Restricciones de origen | Agente no recibe prohibición vigente |
| G04-04 | Reconstruir dependencias ALL/ANY, estados y bloqueos | Bloqueos ALL/ANY | Tarea bloqueada figura ready |
| G04-05 | Incluir IntegrationContracts, APIs y compatibilidades obligatorias | Consumidores reales incluidos | Consumidor relevante no aparece |
| G04-06 | Adjuntar SourceUniverse original y contratos históricos requeridos | Baseline histórico preservado | Migración ignora source owner |
| G04-07 | Vincular VerificationSpecs positivos, negativos, adversarios y recursos | Falsaciones requeridas | Paquete omite caso hostil obligatorio |
| G04-08 | Separar manifest inmutable de texto orientativo reescribible | Manifest distinto de explicación | Resumen recorta obligación del manifest |
| G04-09 | Descomponer sin perder obligations y conservar closure parent | Subtareas no pierden padre | Parent terminado con child pendiente |
| G04-10 | Detectar cambios de constitución, contrato, fuente o consumer desde baseline | Stale package reconocido | WorkPackage stale aceptado sin reevaluar |
| G04-11 | Planificador identifica escritura incompatible y dependencias de tareas | Dependencias semánticas concurrentes | Dos tareas alteran misma autoridad sin control |
| G04-12 | Recalcular closure para comparar paquetes recibidos o producidos | Closure recalculado externamente | Paquete escrito a mano omite contrato y pasa |

## Suficiencia y realización

El contrato superior G de esta campaña solo se acredita con una prueba de A∧D∧J⇒G, factibilidad y realización material de premisas pertinentes; una matriz de trazabilidad o un porcentaje de tests no lo justifica. Los contratos INT-02/03/07 llevan los puentes entre módulos/campañas. Los bindings de código identifican rutas y versiones reales; UNKNOWN no equivale a PASS.

## Falsación E2E de campaña

Manifest truncado elimina bridge; subpaquete declara padre DONE con hijo pendiente. Ejecutar también la falsación original de cada fila y un caso positivo. En SH-05 someter una parte auténtica de ProjectGuardian a la capacidad obtenida y contrastar con V0 u otro oráculo independiente.

## Salida de autoría y cualificación

DEVELOPMENT_COMPLETE exige 12 obligaciones implementadas, junto con pruebas, adversarios, verificadores y puentes exigidos escritos y sin placeholders. CAMPAIGN_CLOSED exige además auditoría independiente tras finalizar bloque de constructor, ejecución material por perfil, recibo auténtico y permiso de admisión. GSL-0 sigue pendiente de definición específica.
