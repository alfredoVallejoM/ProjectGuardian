# ProjectGuardian

Infraestructura independiente para custodiar obligaciones, arquitectura y garantías.
Guardian distingue lo exigido, lo implementado y lo acreditado por ámbito.
Producir código, pruebas o documentos no concede autoridad normativa.

## Prioridad actual: terminar íntegramente la primera campaña G-00

**Fecha de esta actualización: 27 de octubre de 2026.** El objetivo es desarrollar
**las doce obligaciones originales G00-01…G00-12**, con sus **120 cláusulas,
58 contratos API, 36 adversarios y siete verticales**. B00…B09 son bloques de esa
misma campaña, no campañas nuevas. No se reduce el denominador ni se sustituye
la aceptación del producto por pruebas del comprobador de aceptación.

El núcleo integrado y el recorrido GSL del perfil actual están publicados.
**G00_DEVELOPMENT_COMPLETE y G00_CAMPAIGN_CLOSED siguen sin acreditarse.**
GSL es un frente coordinado: sus ampliaciones no sustituyen las obligaciones
pendientes de G-00. CTK-01 permanece fuera del alcance y no bloquea este trabajo.

## Última remediación y evidencia disponible

La última remediación de producto registrada es
[`158ff6f0`](https://github.com/alfredoVallejoM/ProjectGuardian/commit/158ff6f0cc98870d53bd350a8a2b6e6f5e53c470),
posterior a la revisión adversaria `9a673c4b`. Corrige seis familias:

| Familia | Protección incorporada |
|---|---|
| G02 | Formatos fijados y reconstrucción del frontend completo desde bytes originales; no omitir normas ni promover ejemplos mediante análisis manipulados. |
| G01 | Inmutabilidad de revisión sobre el delta completo, incluso una baja seguida de alta. |
| D01 | Tipos nominales exactos y revalidación de cortes y fuentes anidadas. |
| A01 | Correspondencia entre API original y operación real, o adaptación explícita fijada separadamente. |
| A02 | Propiedades de recibo tipadas y coincidencia exacta de diagnósticos. |
| A03 | Correspondencia de módulos ejecutados, archivos fuente, hashes y rutas permitidas; una instalación distinta no valida el candidato. |

La ejecución publicada de ese corte fue **961 PASS, 0 FAIL, 0 ERROR, 0 SKIP**, en
Python 3.13.5, y **9/9 mutaciones dirigidas detectadas**. Es una **selección**, no
la suite íntegra: 780 regresiones recuperadas + 44 tests del control B08 + 63 de
emisión/reconstrucción + 24 probes activos + 50 controles ampliados.

[Informe de remediación](docs/audit/2026_10_26_G00_GSL_REMEDIATION.md) ·
[Registro y alcance exacto de ejecución](docs/verification/G00_GSL_REMEDIATION_EXECUTION.json) ·
[Mutaciones](docs/verification/G00_GSL_REMEDIATION_MUTATIONS.json) ·
[Revisión previa con falsaciones preservadas](docs/audit/2026_10_26_G00_GSL_DEEP_REVIEW.md).

**Actualizar este README no es una nueva ejecución.** Las cifras anteriores de
887, 1598 y otros cortes son históricas: no se suman a 961 ni acreditan por sí
solas el HEAD actual. Una modificación documental ajena al código probado no
invalida sus evidencias; tampoco amplía su alcance.

## Desarrollo de G-00 y aceptación pendiente

| Bloque | Implementación o entrega existente | Pendiente de cierre |
|---|---|---|
| B00 | Reconciliación de diseño, doce padres, 120 cláusulas, APIs y decisiones candidatas | Decisiones y aceptación normativa no se presumen |
| B01 | Identidades nominales, aliases, revisiones, digests, codecs y estados básicos | Postcondiciones y aceptación integrada |
| B02 | Proyectos, políticas, universos, historia, inclusiones/exclusiones e imports acotados | Aceptación completa de conexiones y variantes |
| B03 | Seis modelos de compromisos, referencias compartidas y borradores | Revisión exhaustiva de contratos y transiciones |
| B04 | Aplicabilidad V4, perfiles, testigos, conflictos y presupuestos | Regresión y aceptación con todos sus consumidores |
| B05 | Decisiones, reglas, constituciones, aprobaciones externas, conflictos y precedencia | Suficiencia conjunta de acciones, cuerpos y ámbitos |
| B06 | Resolución exacta y codecs nominales versionados | Todas las postcondiciones, tipos raíz y compatibilidades |
| B07 | Evaluador constitucional puro con conjunto esperado de reglas | Suficiencia e integración completas de sus predicados |
| B08 | Suites, verticales, recibos y control de aceptación v2 | Matriz semántica consolidada real 120/58/36/7 y ejecución íntegra |
| B09 | Preparación del expediente y límites de confianza | Revisión por otro actor y cualificación material |

La presencia de un símbolo o de una fila de trazabilidad no es cumplimiento.
Para cada obligación: contrato original → código productivo → positivo →
falsación → consumidor → ejecución → límites. Cada padre necesita además un
juicio sobre la conexión de sus cláusulas. Lo aún no revisado no desaparece.

## Estado acotado de GSL

Existe el recorrido fuente → extracción/lexer/CST/AST → resolución del perfil
actual → tipado → ContractIR, con mapas, PO pendientes, diff estructural y
emisión canónica. La actualización de fuentes utiliza reconstrucción completa
sin reutilización de caché. Los verificadores V0 autónomos están separados del
constructor del IR.

Estos resultados no prueban por sí solos cobertura del corpus original,
realización en código ni admisión normativa. Permanecen pendientes imports y
módulos generales, reconciliación histórica del corpus, dependencias externas y
aceptación global LC00…LC12. La optimización incremental no se inventa como
condición donde el contrato admite reconstrucción completa.

[Núcleo integrado](docs/implementation/G00_COMPLETION_CANDIDATE.md) ·
[Diff estructural](docs/implementation/GSL0_C12_STRUCTURAL_DIFF.md) ·
[Emisión, reconstrucción y control B08](docs/implementation/G00_B08_GSL_EMISSION_REBUILD.md) ·
[V0 y reconciliación inicial](docs/closure/B00_LC00_RECONCILIATION_AND_EXTERNAL_CORRESPONDENCE.md).

## Fuentes autoritativas y reglas de trabajo

[Índice integral](docs/README.md) · [G-00](docs/campaigns/G-00/INDEX.md) ·
[Programa y salidas B00…B09](docs/campaigns/G-00/12_IMPLEMENTATION_PROGRAM_AND_EXIT_GATES.md) ·
[Cláusulas originales](architecture/g00_functional_refinement.json) ·
[APIs originales](architecture/g00_api_contracts.json) ·
[Pruebas y adversarios originales](architecture/g00_validation_plan.json) ·
[14 campañas y 163 obligaciones](architecture/campaigns.json).

Los estados históricos de architecture/ no se reescriben para simular avance.
El catálogo histórico de formatos v1 no sustituye los codecs v2 posteriores.
Se conservan los tests y falsaciones originales al añadir nuevas regresiones.

Pendientes de ejecución acreditada: checkout íntegro actual, paquete instalado
actual, Python 3.12, análisis estático de tipos, instalación protegida y revisión
independiente. No se convierte autoauditoría en aprobación externa.

Sin ramas nuevas salvo orden, sin GitHub Actions como sustituto del trabajo
local, sin reloj/red/fs en el dominio y sin callbacks de proyecto como normas.
Lean/Rust y proyectos ajenos quedan fuera de esta campaña.
