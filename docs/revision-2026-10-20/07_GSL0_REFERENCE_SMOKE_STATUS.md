# GSL-0 — Registro de verificación limitada y estado de los artefactos

**Fecha:** 2026-10-20. **Tipo:** smoke local independiente y lectura de GitHub; NO certificación material integral del candidato. **Corte examinado:** ProjectGuardian c0d7deebdc87d42a6d0908774884c38771ca015c; Charloom c54a06268e1f85167c5b98fecccb85f6b2438af7.

## Artefactos publicados

- Compilador GSL-0 candidato en `experiments/gsl0_reference/compiler.py`.
- Gramática Lark (`grammar.lark`), ejemplo simple, fixture G00-01, catálogo de fuentes y V0 de lógica finita.
- 30 funciones de test autoradas (28 en `tests/test_compiler.py` y 2 en `tests/test_v0_logic.py`).
- Bibliografía interna y plan GSL-0…3, fases y propiedad semántica separados.
- Rust CTK-01 publicado en Charloom bajo `components/charloom-source-kernel/`, con 7 tests Rust autorados. No se ha ejecutado Cargo en esta revisión.

## Verificaciones locales efectivamente ejecutadas

1. Se reconstruyó la **misma gramática** Lark 0.1 en una carpeta local aislada y se analizó el ejemplo simple. Resultado: **PASS, 6 declaraciones, 140 subárboles**; no constituye ejecución del módulo `compiler.py` completo.
2. Se generó el fixture G00-01 con la misma estructura normativa publicada, y se analizó con Lark. Resultado: **PASS sintáctico, 35 declaraciones**, 10 propiedades diferidas, 10 verificaciones y 10 relaciones.
3. Se ejecutó una réplica independiente de la semántica V4, con 32 verificaciones de tablas y 64 triples × 7 leyes (448 verificaciones). Resultado: **480 aserciones PASS**; no demuestra compilación ni procedencia real.
4. Se reconstruyó el AST sintáctico del ejemplo simple con el mismo patrón de Transformer Lark del candidato. Resultado: **PASS, 6 declaraciones y rangos UTF-8**.
5. Se revisó el diff remoto por API GitHub y se comprobó que los 14 archivos propuestos del experimento aparecen en `main`. Se preservaron las autoridades originales.
6. Se verificó que `CharProperties` y `EChar` se exportan desde `charloom-core` y que el nuevo crate CTK-01 se mantiene en workspace anidado sin root Compute dependency explícita. Esto no equivale a compilar ni a auditar todas las dependencias transitorias.

## NO demostrado / pendientes materiales

- No se ha ejecutado el conjunto completo de 30 tests pytest sobre el árbol remoto. **Estado: TESTS_AUTHORED, FULL_PYTEST_NOT_RUN_IN_THIS_VERIFICATION**.
- No se ha ejecutado Cargo, clippy ni fmt sobre CTK-01. **Estado: SOURCE_AUTHORED, MATERIAL_NOT_RUN**.
- No está construida una cadena GSL-0 productiva, parser Markdown normativo, tipado completo, importación histórica ratificada, ni correspondencia semántica demostrada.
- La matriz de fuente del experimento usa un catálogo inyectado; no acredita un SourceUniverse conectado y protegido.
- Se generan obligaciones `UNPROVEN`; ninguna PO fue probada por la mera compilación.
- Las decisiones arquitectónicas y extensiones CCRR/GSL están propuestas, no ratificadas; `main` sigue sin protección observada.
- El resultado local no sustituye auditoría independiente ni recibos de verificador para un candidato exacto.

## Pasos para verificación material posterior

Desde `experiments/gsl0_reference`, en una instalación con dependencias fijadas: ejecutar `python -m pytest tests -q`, corregir hallazgos, generar recibo de SHA. Desde Charloom: `cargo test --manifest-path components/charloom-source-kernel/Cargo.toml`; ejecutar clippy/fmt y tests adversarios, fijar el cargo lock y auditar dependencia real. Después activar revisor independiente tras el bloque completo.

**Interpretación:** el trabajo pendiente de publicación anterior sí se ha publicado; esto no equivale a terminar todo GSL ni a certificar CTK-01.
