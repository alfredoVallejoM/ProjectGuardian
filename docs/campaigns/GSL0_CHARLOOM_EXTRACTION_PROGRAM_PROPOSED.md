# GSL-0 / CL-T — Programa de extracción y lanzamiento del frontend híbrido

**Estado:** PROPOSED_LAUNCH_PLAN; ni Charloom ni Guardian código productivo alterado en esta revisión. Aceptación material requiere compilar Rust y ejecutar Cargo, no disponibles en el entorno de la presente conversación. No crear ramas ni GH Actions. Esta programación se reconcilia con G-00 B00…B09, G-07 y los contratos LC00…LC12, no crea G-14 ni sustituye campañas.

## 1. Decisión de software

Objetivo: ahorrar infraestructura de texto/estructura existente sin acoplar Guardian a Compute Master. Origen exacto: Charloom main 3de6e1ec205394b6ac9c232dd66b1550ffad2fd9. Candidato de biblioteca: crates/charloom-source-kernel, Rust seguro, dependencias charloom-core / charloom-engine cuando son imprescindibles, sin dependencias del crate raíz, compute_master ni research-generalization en el producto extraído. Cargo publish=false hasta cualificación.

Dos fronteras:
- Rust CTK: UTF-8 byte spans, scanner lossless, árbol, índices, edición, streaming y generic CST/AST structural correspondence.
- Guardian: lexer de GSL (semántica de literales/comentarios), gramática, resolver, tipos, autoridad, contrato y IR. No reutilizar un generic IR de Charloom como CCRR IR.

Python Guardian podrá comunicarse inicialmente con ejecutable Rust de lote con protocolo versionado (stdin/stdout y límites), sin herramientas Git, red ni credenciales. Una extensión Python nativa opcional solo tras benchmark y conformance. Mantener alternativa Python/Lark para referencia independiente V0 y fallback de producto si la integración Rust resulta desproporcionada. La decisión de backend definitivo exige medir correctness/performance/maintenance en corpus real.

## 2. Cortes de extracción CTK

| Corte | Input Charloom real | Output esperado | Bloquea si |
|---|---|---|---|
| CTK-00 | Fuente pinned, tests y licencias | Manifest exacto APIs/tests/deps y esquema de procedencia | Ficheros sin revisión o dependencia Compute desconocida |
| CTK-01 | common.rs / core::utf8 / text.rs | SourceSnapshot + ByteSpan + lossless scanner + StructureStore | No reconstruye bytes o trae Compute |
| CTK-02 | text_stream.rs / tests t06 | StreamingParserSource, UTF-8 state | Chunk schedule cambia segmentación |
| CTK-03 | text_index.rs / tests t03 | StructuralIndex de rango/kind | Rango inválido aceptado o nodo incorrecto |
| CTK-04 | text_edit.rs / tests t08 | Edición UTF-8 local + full scan oracle | Patch difiere del rebuild |
| CTK-05 | compute_cst.rs CL-C02, genérico | Delimiter CST independiente con trivia | strings GSL mal agrupados o LayerStore Compute |
| CTK-06 | compute_ast.rs CL-C03, genérico | AST structural correspondence | AST node sin origen válido |
| CTK-07 | corpus.rs / argument_span.rs opcional | Anotaciones/source spans, sin autoridad | candidato NLP ratificado automáticamente |
| CTK-08 | Nuevo servicio Rust de lote | Protocolo versionado para Python y límites | mismatch protocol, fuera scope, ejecución arbitraria |
| CTK-09 | Tests de CL-T + V0 independiente | Conformance, modelos finitos y adversarios | Material PASS ausente o no reproducible |
| CTK-10 | G00 source texts y GSL-0 | Primera vertical G00-01 10 cláusulas | omisión, source map incorrecto, parser sintáctico promovido a norma |
| CTK-11 | Informe de cut y recibos | Corte propuesto de adopción por Guardian | claims fuera del ámbito acreditado |

CTK-05 y 06 NO trasladan literalmente módulos compute_*: se recorta y desacopla únicamente la parte language-neutral ya demostrablemente necesaria. CL-C04 generic HIR/IR se conserva como **diseño de correspondencias**, no código inicial obligatorio. No incluir parallelization ni computational scheduler sin prueba de rendimiento pertinente.

## 3. API candidata de Charloom Source Kernel

Conceptual:
    parse_utf8(bytes) -> SourceBuffer | InvalidUtf8;
    scan_lossless(&SourceBuffer) -> Segments;
    validate_segments(source,segments) -> bool;
    build_text_structure(source) -> ValidatedStructure;
    build_text_index(structure) -> RangeKindIndex;
    apply_text_edit(source, edit) -> UpdatedSourceAndPatch;
    parse_delimiter_cst(lexed_language_tokens) -> CST | SyntaxError;
    map_cst_ast(cst, ast_shape) -> Correspondence | InvalidMapping.

El componente no ofrece parse_contract, ratify, evaluate_policy, claim_proven, interpret_natural_language, execute_verifier. El soporte de GSL strings y comentarios es propiedad de Guardian; CST estructural de CTK opera sobre tokens ya marcados como literales/trivia.

## 4. Testigos y contratos matemáticos

CTK-P1 fuente lossless; P2 UTF-8 boundaries; P3 tree parents/preorder/subtree_end válidos; P4 source range index correcto; P5 chunk-invariant; P6 patch=full re-scan; P7 delimiter tokens reconstruyen input; P8 AST↔CST source anchors; P9 no Compute dependency; P10 conformance de salida Rust serializada vs referencia Python para casos finitos; P11 edición incremental AST GSL = full parse para fase posterior, no inferible de P6; P12 identidad SourceRevision y no confundir TreeNodeId con ObligationId.

En todos los casos: fixtures positivos y mutación negativa; tests originales transplantados con procedencia exacta y ejecutados; auditor independiente tras autoría del bloque; material receipts del SHA exacto. No afirmar done por tener fuente/test originalmente en Charloom.

## 5. Interface Rust ↔ Python sin doble autoridad

Versión inicial: servicio auxiliar de proceso único o batch con framing JSON versionado; entrada UTF-8 explícita, source digest, source_id, operación, límites. Salida de rangos UTF-8 byte offsets, node kinds, trivia y parse diagnostics, **NO contrato ratificado ni ProofStatus**. Python valida source digest, rangos, estructura y versión antes de usar; se recomienda crosscheck de un subconjunto con oráculo Python. Parser no importa plugin en runtime ni lee rutas arbitrarias; source bundle es inyectado por el servicio de fuentes autenticado.

Tres variantes para benchmark:
A Python+Lark propio; B Rust Charloom AST/CST front + Python semántica; C Rust solo scanner + Python parser. Congelar corpus y oráculo antes de comparar; elegir por exactitud/carga de mantenibilidad, no velocidad inventada. El build del helper registra Rust toolchain, crate SHA, dependencias y features.

## 6. Contratos de retorno del compilador

SourceBundle con revisión exacta → syntactic AST → Resolved AST → Typed AST → IR + SourceMap + ProofObligations. El helper Rust puede facilitar hasta AST **sintáctico** y nunca decide semántica de obligaciones ni ratificación. La comparación V0 valida semántica mínima y no copia la respuesta del candidato como expected.

GSL 0 mantiene identidad, fuente, scope, applicability (YES/NO/UNKNOWN/CONFLICT), objetivo/capacidad/propiedad/obligación/verification/relation. Propiedades de ejecución o proceso no soportadas se registran como DeferredProperty, no se borran ni califican. Todos los claims de suficiencia quedan pendientes de GSL-1/G-02.

## 7. Dependencias con las campañas

G-00: tipos y contratos fundacionales de GSL-0/LC00-LC12; G-07: adaptador Charloom y contrato de observación; G-02: relaciones y refinamientos; G-04: cierre WorkPackage; G-05: testigos al código; G-06: pruebas y material receipts; G-09: ratificación; G-11: CLI/API/MCP, sin semántica duplicada; G-13: selfhost y piloto externo. CTK es un track de extracción de componentes, no campaña normativa nueva.

### Secuencia de lanzamiento sin pruebas falsas

1. Ratificar perímetro de extracción y dueños; registrar manifest/digests/licencia.
2. Construir crate CTK-A y portar tests antes de conectarlo a Guardian.
3. Ejecutar Cargo local para compilar, tests y clippy/fmt cuando exista toolchain; no usar GH Actions.
4. Contrastar scanner/range/stream/edit con código original pinned y un oráculo simple independiente.
5. Extraer CTK-B; pruebas de balance, strings/comments protegidos por lexer GSL, CST origin, AST correspondence.
6. Publicar versión pre-release interna con tag/commit y receipts **cuando esté materialmente verificada**; no reclamar 0.9.0-rc.4 stable facade para research.
7. Conectar Guardian por adaptador de sólo procesamiento textual sin permisos normativos.
8. Completar GSL-0 y su primera vertical G00-01 con 10 cláusulas fuente.
9. Auditoría independiente post-bloque y aprobación de integración.

**Estado de la fecha:** sólo pasos de lectura y especificación; no existe crate extraído publicado/ejecutado ni un frontend GSL materialmente validado. El programa puede iniciarse sin arrastrar las campañas actuales de Compute Master, conservando sus líneas separadas.
