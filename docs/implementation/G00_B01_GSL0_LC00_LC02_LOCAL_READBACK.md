# Readback material limitado — G00-B01 + GSL0-LC00…LC02

**Fecha:** 2026-10-21. **Candidato de código inicial:** `8a17518fc45d5a9623698349e358e9b06ed79cad`; alineamiento posterior del ABI candidato C00–C14 en `6d1129894ab2b2d98eb7e7e912d0a0233dfe74be`, prueba en `dc6759614b6cc29ff9e6777f0e1e3e749397eebf`.

## Entorno y ejecución local

- Python 3.13.5, pytest 9.0.2.
- Comando: `pytest -q`.
- Resultado reproducido sobre la copia de trabajo local: **104 passed**, **0 failed**, **0 skipped**, aprox. 0.18 segundos en este entorno.
- Compilación de sintaxis con `python -m compileall -q src tests`: PASS.
- Se contrastaron los hashes Git blob de **21/21** archivos de `src/`, `tests/` y `pyproject.toml` de la copia probada con el árbol de GitHub en `main`: correspondencia exacta. La ejecución local no incluyó el corpus completo de G-00 `architecture/*.json`; ese gate queda reservado para LC09.
- El manifiesto de obligaciones de G-00 publicado mantiene 12 padres, 120 cláusulas subordinadas, 120 contratos lógicos de test, 58 APIs, 36 adversarios y siete verticales: integridad estructural verificada, **no ejecución funcional del conjunto completo**.

## Interpretación correcta

El readback establece que los archivos fuente/test probados localmente corresponden por contenido a los objetos Git del repositorio. No equivale a clonar y reejecutar materialmente el commit remoto en otro runner, ni genera un receipt protegido por el futuro Gatekeeper.

**Estado:** `LOCAL_SOURCE_EQUIVALENCE_PASS`, `INDEPENDENT_REVIEW_PENDING`, `TRUST_ROOT_NOT_AVAILABLE`. Ninguna de las 163 obligaciones originales ni ninguna campaña G-00…G-13 se promociona por este documento a CAMPAIGN_CLOSED. GSL0-LC00 sigue pendiente de ratificación de autoridad; LC03–LC12 no forman parte del cierre de estos bloques.
