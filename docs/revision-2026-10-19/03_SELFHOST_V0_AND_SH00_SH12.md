# SH-00…SH-12 — Programa de autoverificación progresiva

**Estado: PLANIFICADO, NO EJECUTADO.** SH son cortes de cualificación de G-00…G-13, no campañas originales nuevas.

## Frontera de confianza

V0 consta de modelos y verificadores externos al candidato Guardian: fuente congelada, reglas simples, tablas finitas y mutaciones negativas. La versión instalada como oráculo no importa código candidato ni puede ser escrita por el constructor. La concordancia V0/Guardian no demuestra corrección universal: se necesitan también hipótesis semánticas, casos adversarios y certificaciones contextuales.

Tres modos: SHADOW observa sin publicar; SELF_DEVELOPMENT prepara encargos y revisa código, con admisión externa; PROTECTED_GOVERNANCE requiere Gatekeeper instalado y credenciales segregadas. En cualquiera, autoaplicación no equivale a autocertificación.

## Cortes

| Corte | Propiedad demostrada sobre ProjectGuardian | Campañas | Falsación |
|---|---|---|---|
| SH-00 | Corpus congelado, cobertura fuente, correspondencias y oráculo V0 | B00/G00 | Eliminar obligación de inventario |
| SH-01 | Núcleo representa identidades, fuentes, scopes y autoridad propios | G00 | RATIFIED sin aprobación |
| SH-02 | Fragmento GSL futuro elabora a IR preservando fuente y semántica definida | G00 y decisión GSL pendiente | Omitir cláusula en compilación |
| SH-03 | Nuevas obligaciones y cambios conservan identidades y linajes | G01 | CURRENT→FUTURE silencioso |
| SH-04 | Refinamiento de G00 con puentes y suficiencia | G02 | Hojas PASS, padre FAIL |
| SH-05 | WorkPackage real y recalculado independientemente | G03/G04 | Resumen omite restricción |
| SH-06 | RealizationWitness del código Python real y arquitectura | G07/G05 | Función privada correcta, ruta pública rota |
| SH-07 | Evidencias auténticas y cualificación limitada de runs propios | G06 | Receipt inventado/obsoleto |
| SH-08 | Transporte de compromisos entre versiones propias | G10 | Pérdida de dominio histórico |
| SH-09 | Gatekeeper y política previa protegidos | G09 | Candidato cambia regla de aprobación |
| SH-10 | Agente nuevo utiliza MCP/CLI con mismo contrato | G08/G11 | Handoff mutila obligaciones |
| SH-11 | Crash recovery, Git→SQLite, incremental=full | G12 | Interrupción produce doble autoridad |
| SH-12 | Selfhost completo + pilotos externos | G13 | PASS local ocultando fallo E2E |

## SH-00/B00: expediente ejecutable

Se preservan los 34 PG-REQ, 30 ADR propuestas, 14 G, 163 obligaciones y G00 120 cláusulas/120 tests lógicos/36 adversarios/7 verticales previstas; todos son recuentos de diseño, nunca código ejecutado. Construir source-cut exacto, mapa de source refs, matriz de vínculos por tipo (responsabilidad gruesa, refinamiento, suficiencia), propuestas de facetas y pruebas negativas. Crear V0 independiente y fixtures mutados; ejecutar positivos y negativos solo cuando realmente estén implementados.

La auditoría de diseño puede hacerse antes del desarrollo. La revisión adversaria independiente de un bloque de implementación se activa **después** de completar su autoría; el constructor corrige findings y el auditor reevalúa. No se falsean fases.

## Promoción segura

Para cada SH:
- contrato/ruta/revisión exactos y autoridad explícita;
- tests, adversarios y verificadores desarrollados según obligaciones originales;
- pruebas materiales y auditoría independiente según perfil;
- comparador externo que no toma al candidato como oráculo único;
- UNKNOWN y soportes incompletos declarados, no PASS;
- evidencia de que una versión nueva conserva las obligaciones relevantes anteriores.

El candidato no publica su propio Gatekeeper. La autoridad de admisión utiliza instalación previamente protegida y política anterior; si hay escrituras directas a main fuera del Gatekeeper, declarar TRUST_GAP.

## No se diseña GSL-0 en este corte

SH-02 fija el *objetivo* de verificar una futura compilación GSL→IR, pero la gramática, constructores semánticos, oráculos y contrato de GSL-0 se decidirán después de esta revisión documental.
