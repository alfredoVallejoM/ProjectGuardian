# 15 — Ratificación, procedencia y no afirmaciones de ejecución

## Qué significa la publicación
Se archiva la especificación propuesta a partir de las conversaciones que la motivaron, para poder debatirla, ratificar decisiones y convertirla en implementación sin pérdida de intención. Publicación ≠ aprobación automática de las 30 ADR, ≠ código implementado, ≠ validaciones materiales, ≠ teoremas probados ni sistema capaz ya de bloquear un agente.

## Autoridad textual versus registros
El contenido normativo propuesto reside en `architecture/requirements.json`, `architecture/decisions.json`, `architecture/campaigns.json` y `architecture/module_blueprint.json`. Los Markdown explican y detallan el razonamiento y las condiciones; cuando haya divergencia de contenido detectada, se abre `SPEC_CONFLICT` y no se da prioridad silenciosa. Al ratificar se fijarán revisión, signatures/approval y esquema canónico. No fingir que existe ratificación ahora.

## Fuente histórica y correspondencia
Requisitos 34 proceden del hilo acumulado de diseño, consolidado manualmente; no se afirma haber auditado archivos privados no accedidos. Los programas ENG se conservan mediante crosswalk, G-00..13 es reorganización detallada del mismo proyecto (no cambio a framework multiagente). Las estructuras Project Audit Graph (SupportCone/ImpactCone/SupportGap, Objective/Capability/Property/ImplementationUnit/VerificationSpec/ValidationRun/SupportProfile/Evidence/Claim) se mantienen como compromisos del modelo, no necesariamente como código histórico importado.

## Proceso de ratificación
1. Revisión humana del alcance y las 34 necesidades.
2. Revisión de 30 ADR por impacto, alternativas y límites.
3. Revisar inventario de módulos y fronteras físicas sin imponer archivos vacíos.
4. Revisar las 14 campañas, 163 obligaciones y falsaciones.
5. Resolver conflictos, registrar `APPROVED` y revisión.
6. Congelar snapshot normativo para emitir WorkPackages futuros.
Cualquier alteración posterior usa `ChangeSet`, linaje, alcance y autorización.

## Cambios editoriales
Las correcciones tipográficas pueden actualizar vistas sin cambiar contrato; cambios semánticos alteran revision y requieren evaluación de impacto. No permitir que los tests se reescriban para reinterpretar el mismo requisito.

## Riesgos y límites declarados
Aún no hay código, runner confiable, servidor MCP, interfaz UI, base SQLite, firmas ni test material. Solo plan y catálogos preparados. No garantizar matemáticas indecidibles o integridad ante credenciales administrativas fuera del Gatekeeper. El programa de garantías exige aislamientos/controles reales antes de prometer enforcement.

## Siguiente deliberación técnica
No iniciar implementación sin revisar la topología: dónde residen source adapters vs knowledge, quién es owner del Scope/Applicability, dónde se declara el evaluador de SupportCone, qué es núcleo confiable, cuándo registrar perfiles y cómo versionar contratos. Un nuevo documento no sustituye automáticamente estas decisiones.


## Corrección de fuente normativa y GSL (propuesta 19-10-2026)

[Delta de ratificación de ADR](../revision-2026-10-19/06_ADR_RATIFICATION_DELTA.md). La futura fuente tipada GSL y el IR no pueden competir como dos autoridades editables; la regla exacta de propiedad de fuente/IR es una decisión ABIERTA para GSL-0. Los registros CCRR y los enlaces finos nuevos son PROPOSED_NOT_RATIFIED; el corpus original y sus estados permanecen como fuentes para reconciliación. Una compilación exitosa o enlace semántico candidato no es ratificación. No fingir evidencia material ni aprobar cambios con la política que el propio candidato introduzca.
