# ProjectGuardian

Infraestructura independiente para custodiar las obligaciones, la arquitectura y
las garantías de proyectos. Guardian distingue lo exigido, lo implementado y lo
acreditado mediante fuentes y evidencias por ámbito. Personas y agentes consumen
los mismos contratos; ningún agente se concede autoridad por producir resultados.

## Estado actual — 24 de octubre de 2026

**G00-B04 implementado como candidato e integrado con B02/B03/B06.**
La suite completa de producto pasa: **1214 PASS, 0 FAIL, 0 SKIP**, Python 3.13.5,
también sobre el paquete instalado aisladamente. Las 12 mutaciones dirigidas de
B04 y las 16 Q anteriores son detectadas. Son casos de prueba, no 1214 obligaciones.
**G-00 todavía no está terminado ni certificado; no hay auditoría independiente
ni ratificación nueva.** Python 3.12 y tipado estático siguen NOT_RUN.

El replay completo de la base dio 1071 PASS e incorporó los 196 controles que no
se habían reejecutado en el corte B03. Ya no se limita esta validación a los 875
casos seleccionados de aquella entrega.

- [Implementación B04, cláusulas y siguientes bloques](docs/implementation/G00_B04_SCOPE_APPLICABILITY.md).
- [Matriz B04: diez cláusulas, ocho APIs y cinco adversarios](verification/b04/scope_manifest.json).
- [Ejecución, árboles, mutaciones y límites](docs/verification/B04_SCOPE_EXECUTION.json).

## Contratos e inventario original

[Índice integral](docs/README.md) · [Especificación G-00](docs/campaigns/G-00/INDEX.md)
· [Programa de 14 campañas y 163 obligaciones](architecture/campaigns.json)
· [34 requisitos](architecture/requirements.json) · [30 ADR propuestas](architecture/decisions.json).

Los originales de architecture/ permanecen intactos. Sus estados históricos no
se reescriben para simular cierres; los avances están en las matrices por corte.
[Reconciliación técnica B00/LC00](docs/closure/B00_LC00_RECONCILIATION_AND_EXTERNAL_CORRESPONDENCE.md)
explica las 120 cláusulas, 58 APIs, decisiones y formatos. Un vínculo o un nombre
de función existente no demuestra por sí solo satisfacción de la obligación.

## Implementaciones anteriores y evidencia histórica

- [B01 / LC00–LC02](docs/implementation/G00_B01_GSL0_LC00_LC02.md): identidades, IR y V4.
- [B02 / LC03](docs/implementation/G00_B02_GSL0_LC03.md): proyectos, fuentes y frontend.
- [Remediación inicial](docs/audit/2026_10_21_FOUNDATION_ADVERSARIAL_REVIEW.md).
- [Q01–Q15](docs/audit/2026_10_23_FOUNDATION_REMEDIATION.md) y [garantías V0 separadas](docs/verification/GSL0_V0_CORRESPONDENCE_PROFILE_V2.md).
- [Perfil inicial y V0 finito externo](docs/closure/2026_10_24_INITIAL_TECHNICAL_HANDOFF.md).
- [B03/B06/LC04: contratos y resolución exacta](docs/implementation/G00_B03_B06_LC04_REFERENCE_SLICE.md).

Las cifras de estos documentos corresponden a sus cortes históricos, no al candidato actual.

## Continuidad hacia G-00

B05 construye autoridad/constitución/conflictos sobre el motor de scope de B04.
B06 completa los cuerpos y codecs restantes; B07 integra el evaluador constitucional;
B08/B09 completan integración, revisión y evidencia. El flujo general de borradores
B03 también permanece pendiente. GSL no se expande a costa de terminar G-00.

## Principios y arquitectura

Python 3.12+ declarado; núcleo funcional puro, dominio nominal inmutable, servicios
de aplicación, puertos y adaptadores. No reloj/red/fs en el dominio, no current_project
implícito, no callbacks de proyecto como normas. [Arquitectura](docs/architecture/INDEX.md).

No rebajar obligaciones, no confundir test escrito con ejecución, no autocertificación.
Un cambio fuera de los artefactos protegidos no invalida evidencia sin relación con él.
Sin nuevas ramas no autorizadas ni GitHub Actions como requisito de trabajo.
