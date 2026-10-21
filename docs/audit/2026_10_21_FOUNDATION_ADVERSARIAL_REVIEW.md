# ProjectGuardian — Revisión adversaria global de lo realmente desarrollado

**Corte sujeto:** `main` anterior `e3c5ac46dd459aeba097c9e2a6bd66c1bfc34911`; G00-B01, G00-B02 y GSL0-LC00…LC03. **Fecha:** 21 octubre 2026. **Resultado:** 11 defectos funcionales reproducidos/corregidos en candidato local. **NO es auditoría por agente independiente ni cierre normativo.**

## Autoridad examinada y método

Leído: `architecture/campaigns.json` (163 obligaciones de G-00…13), `architecture/g00_functional_refinement.json` (120 cláusulas G-00), `architecture/g00_api_contracts.json` (58 contratos), `architecture/g00_validation_plan.json` (120 contratos de test, 36 adversarios, siete verticales), `docs/campaigns/G-00/01…13`, contrato GSL-0 y revisión LC00–LC12/T01–T12. Ninguno de esos archivos canónicos ha sido modificado.

La auditoría partió de los bytes reconstruidos del candidato remoto y paquetes previos, comparó hashes Git de rutas de producto, revisó invariantes/manipulación de entradas y añadió pruebas que **fallaron antes de la reparación**. No se consideró suficiente el nombre del test, la presencia de tipos, un hash recalculado ni una fuente declarada. Después se ejecutó la suite corregida. Cuatro tests remotos no incluidos en el archivo previo se reconciliaron por su contrato y se ejecutaron localmente. Sin recibo material firmado sobre el commit nuevo.

## Hallazgos cerrados a nivel de código

| ID | Contrato / propiedad | Falsación previa reproducida | Corrección productiva | Test adversario nuevo |
|---|---|---|---|---|
| FND-01 | G00-03-F05/F07/F09 | Entrada `SourceStatus.MISSING` daba universo `.ok=True` sin diagnóstico | `SOURCE_MISSING` y `SOURCE_COVERAGE_UNKNOWN` explícitos | `test_missing_entry_blocks_positive_universe_validation` |
| FND-02 | G00-02-F10/G00-03-F03 | `ReadOnlyProjectView` construida directamente admitía source incluido/excluido a la vez | Invariantes de vista + veto en `verify_bundle_in_project` | `test_direct_view_cannot_bypass_universe_conflict` |
| FND-03 | G00-03-F06 | DELTA con baseline de otro repositorio no daba diagnóstico de vínculo histórico erróneo | Comparar repositorio y tipo real además de lineage | `test_cross_repository_delta_is_not_valid_history` |
| FND-04 | G00-02-F05/F06; ADV-05 | Una importación para commit A autorizaba commit B con mismo SourceRef | `ApprovedSourceImport` exige `pinned_cut` completo, compara igualdad de corte | `test_exact_import_grant_does_not_cover_different_commit` |
| FND-05 | GSL0-LC02, T05/T06 | Oráculo V4 aceptaba `no` en comentario como valor del campo `when: yes` al reescribir IR y hashes | Analizador independiente de ubicaciones de campos, omite strings/comentarios, exige valor completo/ocurrencia | `test_attack_ir_formula_bound_to_comment_instead_of_named_field` |
| FND-06 | G00-07-F10 | `render_status_vector` omitía ejes ausentes y ocultaba evidencias pendientes | Renderer presenta nueve ejes y `unobserved` explícito | `test_g00_07_renderer_never_hides_missing_material_or_qualification` |
| FND-07 | G00-07-F03/F08 | No existía estructura funcional `StatusObservation` con source/revision/scope/observer ni Due separado | Modelo y validador local sin facultad de admisión, enum DueStatus ortogonal | `test_g00_07_observation_is_descriptive_scoped_pinned_and_separate_from_authority` |
| FND-08 | GSL0-LC03, C02/T01 | El scanner se probaba aisladamente, pero no participaba en `analyze_source` productivo | C02 scanner en flujo, segmentos registrados/verificados y fail closed | `test_lc03_skipped_or_failing_lossless_scan_prevents_analyzed` |
| FND-09 | GSL0-LC01, límites de decodificación | `decode_ir` no acotaba bytes ni tamaño de colecciones antes de reconstrucción | Budget explícito de bytes, declaraciones, pruebas y campos | `test_decoder_exhaustion_rejected_before_parsing_untrusted_ir` |
| FND-10 | G00-02-F10 / fuente tipada | Vista admitía objeto con solo atributo `.ref` y corte cambiado bajo mismo ref | Exige `SourceCut` nominal y exacta igualdad de cortes | `test_readonly_view_rejects_untyped_cut_and_mismatch_of_equal_ref` |
| FND-11 | G00-01-F03/F08 | Parser ID ejecutaba `__eq__` de entrada arbitraria, pudiendo lanzar excepción no tipada | Comparar con cadena vacía solo con tipo `str` exacto | `test_id_parser_rejects_user_defined_equality_without_executing_it` |

**Cambio deliberadamente incompatible y fail-closed:** los cinco sitios de prueba que antes construían importaciones únicamente por identidad nominal se han adaptado para proporcionar el corte fuente material. Cualquier consumidor futuro debe pasar `pinned_cut`; no existe fallback permisivo.

## Revisión del alcance original: implementación real ≠ obligación padre cerrada

| Contrato | Lo desarrollado y contrastado | Sigue pendiente para obligación original completa |
|---|---|---|
| G00-01 (F01–F10) | IDs nominales, aliases, digests, codecs, colisiones, errores; pruebas directas y ataques ADV01–03; rechazo de `__eq__` hostil | Resolver completo G00-API-008 en snapshot G00-B06 y consumidor correspondiente; no cerrar G00-01 con simple parseo |
| G00-02 (F01–F10) | Project, storage modes, política de repos, imports exactos, view y validaciones; ADV04–06 | Autenticidad de `TrustedImportGrants` depende de G09; conexiones completas de referencias G00-08 y fuentes G07, no identificarlas como autoridad verificada |
| G00-03 (F01–F10) | Git/document cuts, inclusión/exclusión, historia, known missing, adquisición, scope; ADV07–09 y reparaciones | Censo real/observación G07 y cobertura cualificada G10, autoridad protegida G09; no certificar con enumeración de fuentes |
| G00-07 | Estados nominales, due separado, observaciones con procedencia, renderer de ejes íntegros | Políticas/ciclos G01, auditoría G06 y proyecciones autorizadas; G00-07 no cerrada |
| G00-08 | EntityRef exacta, rutas y límites de imports | Resolver completo/refs huérfanas, transiciones de versión y consumidores G00-B06 |
| G00-12 | Suites directas y adversarias de segmentos ya materializados | Todos los 120 contratos, 36 adversarios y 7 verticales de G-00, además de ejecución y revisión externa |
| GSL0-LC00 | Fuente/contexto pinneados, ABI C00–C14, separación `Compiled`/admisión | Ratificación de lenguaje/semántica y confianza externa |
| GSL0-LC01 | Typed IR nominal, codec estricto, límites de decoder | Integridad resolutiva general, LC04–LC08; tipado y semántica del compilador integral pendientes |
| GSL0-LC02 | Oráculo finito V4 independiente, falsación con hashes regenerados y unión a campo fuente | Grounding de declaraciones normativas globales y corpus original LC09; no equivale a prueba completa de fuente→IR |
| GSL0-LC03 | Extraction markdown normativa, lossless scan, lexer, CST, AST y diagnósticos productivos | LC04 nombres/imports; LC05 tipos; LC06 lowering; source maps globales, incrementalidad, cobertura histórica, certificación LC07–12 |

## Estado de GSL-T01…T12 (no declarar teoremas completos)

- **T01–T03:** pruebas funcionales acotadas de segmentación, CST y conservación de declaraciones/posiciones en el fragmento admitido. La preservación global del corpus no está demostrada.
- **T04:** sin demostración de preservación de tipos del compilador completo (LC05/06).
- **T05:** V4 finito comprobado y falsaciones semánticas reforzadas. No constituye prueba mecanizada ni semántica de todas las construcciones.
- **T06:** campos V4 ahora anclados de forma independiente; grounding global y derivaciones siguen abiertos.
- **T07:** cobertura documental del corpus original G-00 pendiente de LC09.
- **T08:** incremental vs full no implementado (LC07+); CTK no es una dependencia de este corte.
- **T09:** compilador sin API de ratificación; infraestructura externa de admisión no implementada.
- **T10:** streaming y edit incremental no implementados y fuera de LC03.
- **T11:** tablas finitas de información YES/NO/UNKNOWN/CONFLICT probadas dentro de V4; soporte confiable externo aún ausente.
- **T12:** estados de desarrollo, ejecución, auditoría y cualificación separados; política de certificación real pendiente.

## Verificación real, límites y próxima frontera

Suite ejecutada localmente en Python 3.13, `pytest -q`: **226 tests PASS, 0 SKIP** en el candidato reconstruido/remediado. Baseline remoto anterior: 206/206 en su propio corte, NO transferidos automáticamente a SHA nuevo. La suite es evidencia de regresión y falsación del ámbito ejecutado, no un certificado firmado, ni veredicto de auditor independiente. No se han usado GitHub Actions. No se debe modificar `architecture/campaigns.json`, ni sus 163 obligaciones, ni borrar tests adversarios por cambios de implementación.

**HOLD explícitos:** LC00 ratificación externa; audit independiente (autor/revisor distinto); material receipt sobre SHA aceptado; G00-B06 resolver; G00-B03 ontología; GSL0-LC04…12; G07 observación; G09 trust root; G10 cobertura. **Estado del presente corte:** `REMEDIATED_IMPLEMENTED_CANDIDATE`; no `G00_DEVELOPMENT_COMPLETE`, no `GSL0_DEVELOPMENT_COMPLETE`, no `CAMPAIGN_CLOSED`.
