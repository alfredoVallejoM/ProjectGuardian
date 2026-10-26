# ProjectGuardian

Infraestructura independiente para custodiar obligaciones, arquitectura y garantías.
Guardian distingue lo exigido, lo implementado y lo acreditado por ámbito. Personas
y agentes consumen los mismos contratos; producir resultados no concede autoridad.

## Estado actual — 26 de octubre de 2026

El candidato integrado G-00 y el recorrido GSL a IR tipado están publicados desde
[`a361981a`](https://github.com/alfredoVallejoM/ProjectGuardian/commit/a361981a4ab29b43110136a47141e070e66c649c).
El comparador estructural se añadió en `57539a9d`. Esta entrega incorpora:

- **G00/B08:** control de poblaciones, originales fijados, pruebas positivas y
  falsaciones, fases setup/call/teardown, archivos y colección realmente ejecutada.
- **GSL C14:** emisión canónica desde fuente, lectura con pin externo y contraste
  por reconstrucción. El bundle no concede autoridad ni demuestra realización.
- **GSL-T08/T10:** API de cambios fijados con reconstrucción completa, sin caché,
  y recomposición exacta de bytes UTF-8 fragmentados.

Validación de este corte: **887 PASS, 0 FAIL, 0 SKIP**: 780 regresiones seleccionadas
más 107 casos nuevos; doce mutaciones dirigidas detectadas. Python 3.13.5.
**No es la suite íntegra ni una cifra de obligaciones terminadas.**

[Implementación, APIs, garantías y pendientes](docs/implementation/G00_B08_GSL_EMISSION_REBUILD.md)
· [Ejecución y hashes](docs/verification/G00_B08_GSL_EMISSION_EXECUTION.json)
· [Mutaciones](docs/verification/G00_B08_GSL_EMISSION_MUTATIONS.json).

**G-00 y GSL-0 siguen abiertos.** El comprobador B08 no sustituye la revisión de
suficiencia de las 120 cláusulas, 36 adversarios y siete verticales. No hay un plan
nuevo que las declare aceptadas. B09, ratificación, instalación protegida, Python
3.12 y análisis estático de tipos no se afirman como ejecutados.

## Contratos e inventario original

[Índice integral](docs/README.md) · [Especificación G-00](docs/campaigns/G-00/INDEX.md)
· [14 campañas y 163 obligaciones](architecture/campaigns.json)
· [34 requisitos](architecture/requirements.json) · [30 ADR propuestas](architecture/decisions.json).

architecture/ permanece intacto. Sus estados históricos no se reescriben para
simular cierres. La [reconciliación B00](docs/closure/B00_LC00_RECONCILIATION_AND_EXTERNAL_CORRESPONDENCE.md)
conserva el denominador: un enlace o un símbolo de API no prueba suficiencia.
El catálogo histórico v1 no debe confundirse con los codecs v2 posteriores.

## Implementaciones y evidencia histórica

[B01 / LC00–LC02](docs/implementation/G00_B01_GSL0_LC00_LC02.md) ·
[B02 / LC03](docs/implementation/G00_B02_GSL0_LC03.md) ·
[Remediación inicial](docs/audit/2026_10_21_FOUNDATION_ADVERSARIAL_REVIEW.md) ·
[Q01–Q15](docs/audit/2026_10_23_FOUNDATION_REMEDIATION.md) ·
[Garantías V0](docs/verification/GSL0_V0_CORRESPONDENCE_PROFILE_V2.md) ·
[Perfil inicial y V0 externo](docs/closure/2026_10_24_INITIAL_TECHNICAL_HANDOFF.md) ·
[B03/B06/LC04](docs/implementation/G00_B03_B06_LC04_REFERENCE_SLICE.md) ·
[B04](docs/implementation/G00_B04_SCOPE_APPLICABILITY.md) ·
[Núcleo integrado](docs/implementation/G00_COMPLETION_CANDIDATE.md) ·
[Publicación del núcleo](verification/publication/recovered_candidate.json) ·
[Diff estructural](docs/implementation/GSL0_C12_STRUCTURAL_DIFF.md) ·
[Ejecución del diff](docs/verification/GSL0_C12_EXECUTION.json).

Las cifras históricas pertenecen a sus candidatos, no a todo cambio posterior.
No se suman los 1598 históricos, los 263 seleccionados del diff y los 887 actuales.

## Continuidad

Terminar la reconciliación de suficiencia B08 y ejecutar el checkout completo;
resolver hallazgos antes de B09. En GSL quedan imports/módulos generales,
reconciliación del corpus y cualificación completas. La emisión de perfil fijo y
el fallback completo de actualización no equivalen a optimización incremental.
CTK-01 no bloquea este desarrollo. GSL no sustituye la terminación de G-00.

## Arquitectura y reglas de trabajo

Python 3.12+ declarado; dominio nominal inmutable, núcleo funcional y servicios.
Sin reloj/red/fs en el dominio ni callbacks del proyecto como normas. No rebajar
obligaciones ni confundir test escrito con ejecución o autoauditoría con auditoría
independiente. Sin nuevas ramas no autorizadas ni GitHub Actions.
