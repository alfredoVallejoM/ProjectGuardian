# Charloom → Guardian — Auditoría de código real y selección de reutilización textual

**Fecha de revisión:** 2026-10-20. **Charloom HEAD observado:** 3de6e1ec205394b6ac9c232dd66b1550ffad2fd9, rama main. **Guardian:** 3d2d406de0f9bf42ae217fe15ab5860d919a7c33. **Tipo de evidencia:** lectura de código y tests en GitHub, NO compilación de Rust ni run material. **Estado:** extracción PROPUESTA, todavía no desarrollada/validada.

## 1. Fuentes primarias exactas

### Text processing CL-T
- src/generalization/common.rs: TextRange64, TextSummary, StructureNode/Store/Builder, validation. ~1060 líneas; internamente usa charloom-core/engine (no es independiente como archivo aislado).
- src/generalization/text.rs: LosslessScanner, LosslessSegment, scan_lossless, segments_reconstruct_source, build_lossless_structure. ~242 líneas.
- src/generalization/text_hierarchy.rs: bloques/líneas y terminadores de oración ASCII, NO parser Markdown, ~353 líneas.
- src/generalization/text_index.rs: StructuralIndex, covering_leaf/path, nodes_of_kind, intersecting_leaves; ~216 líneas.
- src/generalization/text_edit.rs: TextEdit, ValidatedLosslessSegments, plan/apply patch, patched_segments_match_full_rebuild; ~300 líneas. La equivalencia es entre segmentación incremental y full scan, no AST normativo.
- src/generalization/text_stream.rs: StreamingLosslessBuilder, chunk-invariant UTF-8 decoding y segmentation, ~248 líneas.
- src/generalization/text_parallel.rs: materialización paralela; aplazar por complejidad salvo benchmark.
- src/generalization/corpus.rs: CorpusForest, DocumentOrigin, Annotation, digests, index por kind; opcional de importación documental.

### Text core que no pierde contexto
- crates/charloom-core/src/utf8.rs: Utf8Decoder y Utf8Scalars, UTF-8 incremental.
- crates/charloom-core/src/scan.rs: TokenIter, TokenConfig; **no es lossless para GSL** porque puede omitir whitespace. No utilizar para CST fuente-exacto.
- crates/charloom-engine/src/document.rs: TextRange u32 y Document/DocumentToken; útil para análisis documental, pero límites u32 diferentes de TextRange64; no mezclar sin checks.

### Estructura genérica CL-C02/C03/C04 que aparece bajo compute_*
- src/generalization/compute_cst.rs: GenericToken, GenericCstPipeline, tokenización con trivia y grupos (),[],{}; dependencia en ComputeKind/Stage/LayerStore; su generic lexer no tiene toda la semántica de strings/comentarios GSL.
- src/generalization/compute_ast.rs: GenericAstPipeline, correspondencia AST↔CST; depende de ComputeStage y GenericCstPipeline.
- src/generalization/compute_lowering.rs: HIR/IR y correspondencias; extracción solo de mecanismos generales, no asumir que su IR equivale al de CCRR.
- src/generalization/language.rs: RustLanguageAdapter y clasificación de literales/comentarios Rust; referencia de diseño, no lexer GSL.

### Estructura documental G2 (opcional)
- src/generalization/argument_span.rs: DiscourseSpanStore con digest/fuente/rango, unidades como clause/quote/condition.
- src/generalization/argument_claim.rs: ClaimModality, ClaimQuantifier, ClaimAttribution, ClaimDraft, ClaimStore.
- src/generalization/information_schema.rs: PredicateSchema/SchemaRegistry.
- src/generalization/information_extractors.rs: extract_text_structure y extract_argument_seeds; el propio comentario de fuente afirma que ARG es seed y no semantic parsing. **No convertir a fuente normativa automáticamente**.

## 2. Estado, feature gates y pruebas localizadas

src/lib.rs exporta src/generalization bajo feature research-generalization, desactivada por defecto. El README identifica la superficie estable rc.4 como cinco facades distintos y la rama research como separada. Cargo workspace 0.9.0-rc.4 / Rust >=1.89; publish=false. Los archivos/tests existen pero **no se han ejecutado ni certificado materialmente en esta auditoría**.

Tests de fuente:
- tests/generalization_t02_c02.rs: pérdida cero de jerarquía, CST genérico y delimitadores;
- tests/generalization_t03_c03.rs: índices, AST y correspondencia CST;
- tests/generalization_t06_c06.rs: streaming UTF-8, distintas fronteras;
- tests/generalization_t08_c08.rs: edición y propiedad full rebuild;
- tests/generalization_t09_c09.rs: corpus/anotaciones;
- tests/generalization_g2_argument_foundation.rs: spans, modalidad, cuantificador, fuente y diferencias entre claims;
- tests/generalization_g2_information_extractors.rs: hechos estructurales fundamentados;
- tests/generalization_c11_c13.rs: code intelligence / RustLanguageAdapter;
- tests/generalization_end_to_end.rs: integración de ramo textual y pruebas del ramo compute (excluir compute en extracción).

**No asumir 'test existe' = 'test pasó'**. También existen barreras/candidaturas de campaña que no son contratos del paquete rc.4.

## 3. Decisión técnica propuesta

Extraer **un nuevo crate independiente** dentro del workspace Charloom (nombre candidato charloom-source-kernel) que depende solo de charloom-core y, mientras permanezcan TextSummary/SignatureState, de charloom-engine; NO del crate raíz charloom ni de src/generalization/compute*, ni de Compute Master. La extracción física debe fijar un manifesto de ficheros, líneas/cambios y digests originales; conservar tests y licencias.

Primer corte CTK-A: rangos, UTF-8, lossless scanning, validación, StructureStore, índices y patches. Segundo corte CTK-B: algoritmos genéricos de CST de CL-C02 y correspondencias AST de CL-C03, **desacoplados** de ComputeStage/LayerStore (no transposición literal). Tercer corte opcional CTK-C: spans, corpus y claim candidates, aislados de autoridad CCRR.

TextSummary.signature es una firma algebraica y no identidad criptográfica: la identidad material se apoya en digest de bytes completos y namespace, los ID normativos proceden de Guardian. NodeId interno es posición en árbol, no ObligationId.

## 4. Restricciones de licenciamiento y distribución

Repositorio usa AGPL-3.0-only comunitaria y documenta vía comercial separada en LICENSING.md. Publicación en crates.io desactivada. La extracción debe preservar headers, copyright, provenance y avisos; revisar dependencias y compatibilidad de la licencia según distribución real. El hecho de que Charloom y Guardian estén bajo control del mismo usuario no justifica inferir derechos sobre código ajeno sin comprobar titulares/contribuciones.

Cargo rust toolchain y resolución GitHub no están disponibles en el runtime de esta conversación; ninguna compilación/test Rust se ha afirmado como realizado. No activar GitHub Actions como solución de validación; usar runner local apropiado/autoridad externa cuando esté disponible.

## 5. Pruebas que pueden y no pueden transferirse

Los tests CL-T existentes sirven como referencia de conformance después de extraer código. Reutilizar no es heredar automáticamente certificación: toda prueba debe reejecutarse en nueva crate sobre SHA concreto. GSL lexer debe comprobar strings, escapes, fences y comentarios propios, más parser Markdown normativo independiente.

Ejemplos obligatorios:
- Unicode y CRLF, bytes originales exactos, rangos frontera.
- chunks 1/2/3/4 bytes y UTF-8 incompleto; streaming=full.
- inserción/eliminación en multibyte; patch=full segmentation.
- tokens de GSL con '}' dentro de string nunca cierran grupo.
- AST GSL conserva SourceMap; incremental AST equivale full parse (nueva propiedad fuera de CL-T).
- ninguna librería Compute Master en closure de dependencias.
- después de modificar el CST, source labels/claims no se convierten en RATIFIED.

## 6. Links al código congelado

https://github.com/alfredoVallejoM/charloom/tree/3de6e1ec205394b6ac9c232dd66b1550ffad2fd9/src/generalization

https://github.com/alfredoVallejoM/charloom/blob/3de6e1ec205394b6ac9c232dd66b1550ffad2fd9/LICENSING.md

https://github.com/alfredoVallejoM/charloom/blob/3de6e1ec205394b6ac9c232dd66b1550ffad2fd9/src/lib.rs
