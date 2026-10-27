# ProjectGuardian

Infraestructura independiente para custodiar obligaciones, arquitectura y garantías.
Guardian distingue lo exigido, lo implementado y lo acreditado por ámbito.
Producir código, pruebas o documentos no concede autoridad normativa.

## Prioridad actual: terminar íntegramente la primera campaña G-00

**Estado actualizado: 27 de octubre de 2026.** El objetivo es desarrollar las
**doce obligaciones originales G00-01…G00-12**, con **120 cláusulas, 58 APIs,
36 adversarios y siete verticales**. B00…B09 son bloques de la misma campaña.
No se reduce el denominador ni se sustituye aceptación del producto por tests
del propio comprobador. GSL continúa como frente coordinado, no como sustituto
de G-00; CTK-01 permanece fuera de alcance y no bloquea el desarrollo.

**G00_DEVELOPMENT_COMPLETE y G00_CAMPAIGN_CLOSED siguen sin acreditarse.**
El núcleo integrado está publicado, pero su aceptación exhaustiva aún no está
terminada. Los estados históricos de architecture/ no se reescriben para
aparentar avance.

## Avance de este corte: contratos reales de G00-03

Se han corregido validaciones de metadatos de fuentes: rol histórico, estado de
adquisición, lineage, baseline, clase de referencias incluidas, justificación
de exclusiones y motivos de fuentes ausentes. La validación comprueba esos
datos antes de usar catálogos/historia/autoridad y no ejecuta hooks de subclases.
Los objetos válidos reconstruidos siguen admitidos.

**Ejecución nueva: 114 PASS, 0 FAIL, 0 ERROR, 0 SKIP**, Python 3.13.5:
80 regresiones seleccionadas + 20 casos positivo/negativo de G00-03-F01…F10 +
14 casos de fronteras. Ocho falsaciones fallaron sobre la base antes de reparar.
Cinco mutaciones dirigidas fueron detectadas. **No es el checkout íntegro ni el
cierre del padre G00-03**: quedan sus conexiones y la aceptación integral.

[Implementación, ocho fallos y límites](docs/audit/2026_10_27_G00_03_ACCEPTANCE.md) ·
[Ejecución y hashes](docs/verification/G00_03_ACCEPTANCE_EXECUTION.json) ·
[Mutaciones](docs/verification/G00_03_ACCEPTANCE_MUTATIONS.json).

El [registro de avance contractual](verification/completion/obligation_evidence.json)
conserva todos los IDs 12/120/58/36/7. Enlaza diez pares de cláusula ejecutados y
mantiene 110 cláusulas pendientes de consolidación. **No son 110 funcionalidades
inexistentes**: su implementación y evidencia histórica no se han reconciliado
en esta nueva proyección. No es un acceptance-plan/v2 ni un certificado.

## Base anterior preservada

La remediación [`158ff6f0`](https://github.com/alfredoVallejoM/ProjectGuardian/commit/158ff6f0cc98870d53bd350a8a2b6e6f5e53c470)
corrigió seis familias: extracción normativa y formatos de GSL (G02), revisión
inmutable en deltas compuestos (G01), validez nominal de cortes (D01), vínculo
API original/adaptador (A01), diagnósticos exactos (A02) y procedencia de módulos
ejecutados (A03). Su ejecución seleccionada fue **961 PASS y 9/9 mutaciones**.

[Informe de remediación](docs/audit/2026_10_26_G00_GSL_REMEDIATION.md) ·
[Registro histórico de ejecución](docs/verification/G00_GSL_REMEDIATION_EXECUTION.json) ·
[Revisión y falsaciones preservadas](docs/audit/2026_10_26_G00_GSL_DEEP_REVIEW.md).

961, 887, 1598 y los demás contadores anteriores pertenecen a sus cortes y
selecciones. **No se suman al 114 ni acreditan por sí solos el HEAD actual.**
Actualizar documentación no es una nueva ejecución; cambios documentales fuera
del código protegido tampoco invalidan evidencia ajena a esos cambios.

## Desarrollo de G-00 y aceptación pendiente

| Bloque | Entrega existente | Pendiente de cierre |
|---|---|---|
| B00 | Reconciliación de diseño, padres, cláusulas, APIs y decisiones candidatas | Aprobaciones y aceptación normativa no se presumen |
| B01 | Identidades nominales, aliases, revisiones, digests, codecs y estados | Postcondiciones y aceptación integrada |
| B02 | Proyectos, políticas, universos, historia, exclusiones e imports acotados | Conexiones y variantes completas |
| B03 | Seis modelos de compromisos, referencias compartidas y borradores | Contratos y transiciones completos |
| B04 | Aplicabilidad V4, testigos, conflictos y presupuestos | Regresión y aceptación de todos los consumidores |
| B05 | Decisiones, reglas, constituciones, aprobaciones externas y precedencia | Suficiencia conjunta de acciones/cuerpos/ámbitos |
| B06 | Resolución exacta y codecs nominales versionados | Postcondiciones, tipos raíz y compatibilidad |
| B07 | Evaluador puro con población esperada de reglas | Suficiencia e integración completas |
| B08 | Suites, verticales, recibos y control de aceptación v2 | Matriz semántica completa 120/58/36/7 y ejecución íntegra |
| B09 | Expediente y límites de confianza | Revisión por otro actor y cualificación material |

Cada obligación exige contrato original → código productivo → positivo →
falsación → consumidor → ejecución → límites. Cada padre necesita además el
juicio sobre la conexión de sus cláusulas. Un nombre de función no es cumplimiento.

## GSL: perfil funcional y límites

Existe fuente → extracción/lexer/CST/AST → resolución del perfil actual → tipado
→ ContractIR, con mapas, PO pendientes, diff estructural y emisión canónica.
Los cambios de fuentes usan reconstrucción completa sin reutilizar caché. Los
V0 autónomos no participan en la construcción del IR.

Permanecen pendientes imports/módulos generales, reconciliación del corpus,
dependencias externas y aceptación global LC00…LC12. Compilar no demuestra
realización en código, suficiencia del corpus ni admisión normativa. No se inventa
optimización incremental como condición donde se admite reconstrucción completa.
**No hay ampliaciones productivas de GSL en este corte de G00-03.**

[Núcleo integrado](docs/implementation/G00_COMPLETION_CANDIDATE.md) ·
[Diff](docs/implementation/GSL0_C12_STRUCTURAL_DIFF.md) ·
[Emisión/reconstrucción/B08](docs/implementation/G00_B08_GSL_EMISSION_REBUILD.md) ·
[V0 y reconciliación inicial](docs/closure/B00_LC00_RECONCILIATION_AND_EXTERNAL_CORRESPONDENCE.md).

## Fuentes autoritativas y reglas

[Índice](docs/README.md) · [G-00](docs/campaigns/G-00/INDEX.md) ·
[Programa B00…B09](docs/campaigns/G-00/12_IMPLEMENTATION_PROGRAM_AND_EXIT_GATES.md) ·
[Cláusulas](architecture/g00_functional_refinement.json) ·
[APIs](architecture/g00_api_contracts.json) ·
[Pruebas/adversarios](architecture/g00_validation_plan.json) ·
[14 campañas y 163 obligaciones](architecture/campaigns.json).

Se conservan originales y pruebas. El catálogo histórico v1 no sustituye a los
codecs v2. No se confunde autoauditoría con revisión independiente.
Pendientes de ejecución acreditada en este corte: checkout/paquete íntegros,
consumidores constitucionales y codecs generales, Python 3.12, tipado estático,
instalación protegida y otro revisor. Sin ramas nuevas salvo orden ni GitHub
Actions. Sin reloj/red/fs en el dominio ni callbacks del proyecto como normas.
