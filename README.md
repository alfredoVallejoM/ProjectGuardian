# ProjectGuardian

Infraestructura independiente para custodiar obligaciones, arquitectura y garantías.
Guardian distingue lo exigido, lo implementado y lo acreditado por ámbito. Personas
y agentes consumen los mismos contratos; producir resultados no concede autoridad.

## Estado actual — 26 de octubre de 2026

**Publicado el candidato integrado G-00 y el recorrido acotado de GSL a IR tipado.**
Incluye borradores, decisiones y aprobaciones, reglas y constituciones, conflictos,
codecs nominales v2, evaluador puro, remediación R01–R06, tipado, elaboración,
mapas de origen y PO pendientes. La publicación inicial es
[`a361981a`](https://github.com/alfredoVallejoM/ProjectGuardian/commit/a361981a4ab29b43110136a47141e070e66c649c).

Esta entrega añade **C12: diff estructural tipado de ContractIR**, con borrados,
cambios de campos/referencias/revisión, orden, procedencia y PO visibles. No decide
equivalencia semántica, no autoriza cambios y no completa todo GSL.

Validación nueva de C12: **263 PASS, 0 FAIL, 0 SKIP** (67 nuevos y 196 regresiones
seleccionadas); seis mutaciones dirigidas detectadas. Python 3.13.5. No es una
reejecución de la suite íntegra. Los 1598 PASS comunicados en la autoría anterior
son un resultado histórico, no se suman a 263 ni se atribuyen al commit nuevo.

**G-00 y GSL-0 siguen abiertos.** B08 necesita la aceptación exhaustiva de las
120 cláusulas y 36 adversarios originales, junto con las siete verticales. B09
sigue sin auditoría independiente, ratificación ni recibo protegido. Python 3.12
y el análisis estático de tipos no se afirman como ejecutados.

[Implementación integrada y límites](docs/implementation/G00_COMPLETION_CANDIDATE.md)
· [Publicación por árboles exactos](verification/publication/recovered_candidate.json)
· [Contrato C12 y pruebas](docs/implementation/GSL0_C12_STRUCTURAL_DIFF.md)
· [Ejecución C12](docs/verification/GSL0_C12_EXECUTION.json).

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
[B04](docs/implementation/G00_B04_SCOPE_APPLICABILITY.md).

Las cifras históricas pertenecen a sus candidatos, no a todo cambio posterior.

## Continuidad

Terminar la reconciliación de suficiencia B08 y ejecutar el checkout completo;
resolver hallazgos antes de B09. En GSL quedan imports/módulos generales,
reconciliación del corpus, incrementalidad, emisión y cualificación completas.
CTK-01 no bloquea este desarrollo. GSL no sustituye la terminación de G-00.

## Arquitectura y reglas de trabajo

Python 3.12+ declarado; dominio nominal inmutable, núcleo funcional y servicios.
Sin reloj/red/fs en el dominio ni callbacks del proyecto como normas. No rebajar
obligaciones ni confundir test escrito con ejecución o autoauditoría con auditoría
independiente. Sin nuevas ramas no autorizadas ni GitHub Actions.
