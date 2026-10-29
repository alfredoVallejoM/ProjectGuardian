# ProjectGuardian

Infraestructura independiente para custodiar obligaciones, arquitectura y garantías. Producir código, pruebas o documentos no concede autoridad normativa.

## Estado — 29 de octubre de 2026

**G00-01: desarrollo técnicamente cerrado sobre `f33c700d1bb2310662e7bc58b511f8b17ef6a6cc`. Única obligación siguiente activa: G00-02 — proyecto y aislamiento.**

El cierre se publica después de revisar adversariamente el expediente y comprobar los recibos completos. No equivale a revisión independiente, ratificación, cualificación B09 o cierre de toda G-00. G00-03 no se abre hasta aceptar íntegramente G00-02.

El objetivo sigue siendo la primera campaña completa: **12 padres, 120 cláusulas, 58 APIs, 36 adversarios y siete verticales**. Se conserva el desarrollo posterior, pero no se marca aceptado por existir. GSL queda como consumidor en regresión, no como ampliación lateral; CTK-01 está fuera de alcance.

### Cierre adversario de G00-01

Diez cláusulas, ocho APIs y tres adversarios, con conexión real alias -> codec -> resolución exacta. Se preservan firmas y formato identity/v1. Las falsaciones históricas dan 44 PASS / 50 FAIL antes de reparar y 94 PASS después; no son cincuenta fallos actuales.

**Evidencia material conservada:** 1.974 PASS desde fuentes y 1.974 PASS desde paquete instalado, misma colección, cero fallos/errores/omisiones/deselecciones/XFAIL. 52 módulos cotejados y 20/20 mutaciones dirigidas detectadas. Python 3.13.5. **Revisión nueva:** 67 regresiones de identidad y 34 controles adversarios del expediente, 101 PASS. No se suman contadores ni se presenta la revisión de recibos como una nueva ejecución completa.

Se corrigieron dos defectos documentales: positivo/negativo reutilizado en API-005 y genealogía del hash del acta local frente a la publicada. Los dos recibos se conservan completos en codificación textual reversible; el verificador reconstruye sus bytes exactos.

[Acta de cierre](verification/g00_01/closure/README.md) ·
[Decisión y límites](verification/g00_01/closure/CLOSURE.json) ·
[Matriz contractual](verification/g00_01/ACCEPTANCE.json) ·
[Pins](verification/g00_01/closure/PINS.json) ·
[Comprobador adversario](verification/g00_01/closure/audit_receipts.py).

```sh
python verification/g00_01/closure/audit_receipts.py --package verification/g00_01/closure/PAIRED_RECEIPTS.json.xz.b64 --acceptance verification/g00_01/ACCEPTANCE.json --pins verification/g00_01/closure/PINS.json
python -m pytest -q tests/g00_01
python -m pytest -q verification/g00_01/closure/test_dossier.py
```

### Secuencia y límites

G00-01 -> **G00-02** -> G00-03 -> ... -> G00-12. El expediente conserva implementación, positivo, falsación, consumidor, ejecución y límites por obligación. Una dependencia se termina para la obligación activa; no se aplaza mientras se abre la siguiente. Una regresión reabre la obligación afectada.

**G00_DEVELOPMENT_COMPLETE y G00_CAMPAIGN_CLOSED permanecen falsos.** Python 3.12, tipado estático, revisión por otro actor y runner protegido siguen pendientes. Los recibos son observaciones sin firma. La aceptación B08 de todo el corpus no se deduce del número de tests; B09 conserva sus requisitos externos.

Los bloques existentes incluyen proyectos/fuentes, compromisos/borradores, ámbitos V4, autoridad/constitución, resolución y codecs, y evaluador puro. Se aceptarán secuencialmente. El [registro acumulado](verification/completion/obligation_evidence.json) y las matrices históricas conservan el denominador, no certifican bloques posteriores.

## GSL y evidencia histórica

Existe fuente -> extracción/lexer/CST/AST -> resolución del perfil actual -> tipado -> ContractIR, mapas, pruebas pendientes, diff y emisión. Actualizaciones mediante reconstrucción completa. Imports/módulos generales, corpus histórico, dependencias externas y aceptación global siguen pendientes. Compilar no acredita realización del contrato ni admisión normativa.

[Reparaciones de G00-01](verification/g00_01/REVIEW_2026_10_29.md) ·
[Replay seleccionado anterior](verification/g00_01/REPLAY_2026_10_29.json) ·
[G00-03: metadatos](docs/audit/2026_10_27_G00_03_ACCEPTANCE.md) ·
[Remediación de fronteras](docs/audit/2026_10_26_G00_GSL_REMEDIATION.md) ·
[Núcleo integrado](docs/implementation/G00_COMPLETION_CANDIDATE.md) ·
[Diff GSL](docs/implementation/GSL0_C12_STRUCTURAL_DIFF.md) ·
[Emisión/reconstrucción](docs/implementation/G00_B08_GSL_EMISSION_REBUILD.md).

Los resultados 114, 961, 887, 1598 y 1030 pertenecen a sus candidatos y selecciones. No se suman ni se transfieren a código cambiado. Un cambio puramente documental no invalida código idéntico ni amplía su garantía.

## Fuentes originales

[Índice](docs/README.md) · [G-00](docs/campaigns/G-00/INDEX.md) ·
[Programa](docs/campaigns/G-00/12_IMPLEMENTATION_PROGRAM_AND_EXIT_GATES.md) ·
[Cláusulas](architecture/g00_functional_refinement.json) ·
[APIs](architecture/g00_api_contracts.json) ·
[Adversarios y verticales](architecture/g00_validation_plan.json).

Originales y tests históricos intactos. Sin ramas nuevas, GitHub Actions ni ratificaciones inventadas.
