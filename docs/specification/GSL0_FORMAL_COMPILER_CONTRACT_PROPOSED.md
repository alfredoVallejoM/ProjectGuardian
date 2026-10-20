# GSL-0 — Especificación formal del compilador y sus procesos (candidata)

**Estado:** DESIGN_PROPOSED_NOT_RATIFIED. No existe compilador productivo, material PASS, teorema mecanizado ni admisión normativa. **Corte de Guardian:** 3d2d406de0f9bf42ae217fe15ab5860d919a7c33. **Reutilización examinada:** Charloom 3de6e1ec205394b6ac9c232dd66b1550ffad2fd9. Conservar 34 PG-REQ, 30 ADR propuestas y 163 obligaciones G-00…G-13. La propuesta anterior reservaba deliberación específica de GSL-0; éste es el candidato de contrato para dicha deliberación, no su ratificación.

## I. Enunciado constitucional del compilador

GSL-0 no es un compilador de programas ni un verificador total de contratos en lenguaje natural. Es un lenguaje de especificación cuyo frontend convierte una **fuente tipada admitida** a un **modelo normativo tipado reproducible**. La correspondencia total desde lenguaje natural libre no se reivindica. La edición/importación asistida produce propuestas separadas.

Sea S=(project, source_id, revision, digest, bytes); Γ=(project, source_cut, grants, symbols, type_registry, predicate_registry, semantic_version, compiler_identity). Compilar es una función pura:
    Compile_v : SourceBundle × Γ → Rejected(error) + Analyzed(partial,diagnostics) + Compiled(IR,SM,PO,manifest,diagnostics).
El modo estricto sólo devuelve Compiled si todas las construcciones del fragmento admitido se han tipado, resuelto y elaborado, y su source map es íntegro. Los predicados de comportamiento cuya **semántica está diferida** persisten como DeferredProperty; no califican como prueba ni desaparecen.

Diferenciar Compiled, SpecReady, RefinementSufficiencyProven, DevelopmentComplete, MateriallyQualified y NormativelyAdmitted. La compilación no puede ratificar normativa ni ejecutar código fuente arbitrario.

### Familias de compromisos

Commitment[K,Scope] con K = Existence, Behavior, Constitution, Execution/Resource, Development/Process y Integration/Migration, o variantes compatibles que la ADR ratifique. Cada K define universo de observación/semántica; no promocionar evidencia entre dominios sin prueba de puente. Objective/Capability/Property/Obligation/VerificationSpec son entidades diferentes, no distintos alias de texto.

### Lenguaje mínimo

Constructores candidatos: project, source, import, scope, objective, capability, property, obligation, relation, verification; literales, referencias nominales, términos, predicados, not/and/or; posible forall sobre universo **finito y fijado** en SourceUniverse. No se aprueba sintaxis final por este documento. En GSL-0 sólo se evalúan predicados constitucionales cuyas semánticas están registradas; algoritmos de programas, suficiencia refinada, timing y recursos específicos son obligaciones o propiedades diferidas de versiones GSL-1/2/3.

La lógica de información usa V4 = {(0,0) UNKNOWN, (1,0) YES, (0,1) NO, (1,1) CONFLICT}. Negación swap de componentes; conjunción (a+∧b+,a−∨b−); disyunción (a+∨b+,a−∧b−). El valor de evaluación no es una prueba admitida: se distingue información, autoridad de hechos y calificación. Aplicabilidad, exigibilidad temporal y satisfacción de realización son predicados distintos.

## II. Fuente textual y sustrato Charloom

Adquirir del SourceUniverse un SourceBundle congelado. La fuente original conserva bytes UTF-8 exactos, CR/LF/CRLF y digest completo; nunca tomar HEAD mutable implícito.

La transformación textual T(S) genera segmentos (start_byte,end_byte,kind) con:
1. start_0=0, end_i=start_{i+1}, end_n=|S|;
2. todos límites UTF-8 válidos;
3. cada segmento se obtiene de S en su posición exacta;
4. concatenar segmentos reconstruye bytes originales, incluso whitespace, comentarios y puntuación.

Estas propiedades tienen implementaciones candidatas en Charloom CL-T (LosslessScanner, TextRange64, StructureStore), no se consideran materialmente probadas en el crate nuevo hasta validación.

La extracción Markdown identifica bloques normativos GSL según convención versionada y produce spans físicos; **la jerarquía textual Charloom no es un parser Markdown**. No dar autoridad a un bloque de ejemplo.

Lex_GSL mantiene estados para strings, escapes, comentarios y delimitadores; no se limita a dividir grupos genéricos Charloom. La función Yield de CST reconstruye exactamente el texto de la unidad, con trivia. Los nodos AST normativos conservan relación AST↔CST, aunque AST omita trivia; cada nodo IR conserva SourceOrigin(document_revision, digest, byte spans), incluyendo nodos derivados con ID de regla y premisas.

## III. Contratos exactos por fase

| Fase | Tipo salida | Invariante verificable |
|---|---|---|
| C00 Acquire | FrozenSourceBundle | todos los bytes/refs/versiones fijados; no autoescaneo remoto en core |
| C01 Extract | NormativeUnits | cobertura exacta de fences normativos; ejemplos excluidos |
| C02 Lex | TokenStream | yield(tokens+trivia)=source unit; strings protegidos |
| C03 Parse | CST | grupos balanceados, tipos de error, source reconstruction |
| C04 Abstract | ParsedAST | toda declaración normativa presente; origen CST |
| C05 Resolve | ResolvedAST | ningún símbolo ambiguo o fuera de proyecto; pin exacto |
| C06 Typecheck | TypedAST | firmas y dominios; referencias nominales |
| C07 SemanticCheck | CheckedAST | todos constructores soportados tienen semántica o DeferredProperty autorizado |
| C08 Elaborate | ContractIR | preservación de significado del fragmento; source provenance |
| C09 GeneratePO | ProofObligations | cada PO tipada y fundamentada; nunca PROVEN por generarla |
| C10 VerifyIR | IntegrityReport | sin nodos normativos huérfanos, fuentes omitidas, roles perdidos |
| C11 Canonicalize | CanonicalIR | determinismo, roundtrip y distinción de orden semántico |
| C12 Diff | ContractDiff | diferencia normativa typed, no debilitar por texto |
| C13 Emit | Bundle | fuente/código de compilador/schema/hash/diagnósticos referidos |
| fuera | AdmissionDecision | Gatekeeper con policy anterior y permisos ajenos al candidato |

**Contrato de error**: Rejected para errores fatales de sintaxis/tipos/referencia. Analyzed para partial AST de editor, nunca admisión estricta. UncompilableFeature para una construcción normativa desconocida, nunca ignorar silenciosamente. ResourceLimit no es PASS. Un predicado diferido queda en IR como EXPLICITLY_UNINTERPRETED, con PO pendiente y sin cualificación semántica.

**Contratos de tipos**: Γ⊢e:T; tipos nominales ProjectId ≠ RevisionId ≠ ContentDigest; Ref[Scope] ≠ Ref[VerificationSpec] ≠ Ref[Obligation]. Desacoplar comprobación estática de autoría material. Resolver por proyecto, namespace, clase e identidad; no adoptar alias textual ni última fuente.

**Contrato semántico**: para términos y predicados interpretados, cualquier contexto/valoración admisible ρ,
    Eval_IR(Elaborate(e),ρ)=Eval_GSL(e,ρ).
Prueba inductiva sobre expresiones atómicas, not, and, or y cuantificadores finitos cuando formen parte del perfil. Este resultado es condicional a exactitud de scanner/parser, interpretación atómica y verificador; no demuestra intención humana.

**Contrato de source map**: toda declaración original normativamente admitida tiene IR/diagnóstico de disposición, todo nodo normativo de IR tiene source span o derivación finita de regla admitida; los spans pertenecen al documento/digest/revisión de origen. Id lógicos no dependen de offsets ni de NodeId internos Charloom. No usar firmas algebraicas de texto como identidad criptográfica.

**Canonización**: Canonicalize(Decode(Canonicalize(IR)))=Canonicalize(IR); mismo corte, compilador, registry y semantic_version produce bytes canónicos iguales. Distinguir SourceDigest, ContractDigest y CompilationDigest. No normalizar conjuntos y listas con igual regla: el orden de roles o trazas puede ser semántico.

**Incrementalidad**: para un cambio Δ,
    CompileIncremental(D,Δ,Γ) ≅ CompileFull(D+Δ,Γ)
para contrato normalizado y diagnósticos semánticos en mismo contexto; en caso de imposibilidad de justificar independencia, reconstrucción completa o HOLD.

**Autoridad**: Compile no escribe Git ratificado; SourceBundle no contiene credenciales; ningún predicado arbitrario ejecuta módulos Python indicados por texto. La ratificación es operación protegida separada, y el IR es versión canónica derivada/fijada respecto a una fuente admitida, conforme decisión ADR pendiente.

## IV. Suficiencia respecto al proyecto Guardian

La fuente original PG-REQ/G-00 es inventario externo. Coverage de declaraciones GSL válidas al IR no demuestra cobertura del corpus original: documentar por separado (A) Source→GSL y (B) GSL→IR. La primera vía requiere reconciliación por fuente y decisiones, la segunda puede verificarse como ley de compilador.

Un enlace entre obligación padre y cláusula hija no constituye prueba de suficiencia A∧D∧J⇒G. En GSL-0 se conserva relación documental y PO pendiente; GSL-1 y G-02 desarrollan RefinementCase y pruebas. GSL-2 vincula realización al código verdadero; GSL-3 procesos/recursos. El compilador no hace el trabajo de G-02/G-05/G-06/G-09.

## V. Caso de referencia obligatorio G00-01

La fuente real architecture/g00_functional_refinement.json contiene G00-01-F01…F10 y test contracts G00-01-T01…T10:
F01 wrappers nominales; F02 namespace/EntityKind; F03 gramática/diagnóstico; F04 alias con ámbito; F05 rename preserves LogicalId; F06 referencia con revisión inmutable; F07 ContentDigest completo; F08 constructor puro sin clock/RNG; F09 codecs conservan kind/project; F10 duplicados no sobrescriben.

El experimento exige correspondencia 10/10 de fuente a GSL candidato y a IR, sin inventar semántica de comportamiento que el fragmento aún no interpreta. Sus verificaciones materiales permanecen pendientes hasta desarrollar el código y sus testigos. No afirmar que F01…F10 ya demuestran G00-01; producir PO de suficiencia diferida, además de verificar source coverage.

## VI. Teoremas objetivo y modelo de prueba

- GSL-T01: conservación textual y spans; UTF-8, CRLF, Unicode y offsets.
- GSL-T02: yield CST = secuencia original de tokens/trivia.
- GSL-T03: conservación de las declaraciones normativas de parser→AST (con source mapping).
- GSL-T04: preservación de tipos Γ⊢e:T ⇒ Γ'⊢Lower(e):Translate(T).
- GSL-T05: evaluación del fragmento V4 conservada por lowering.
- GSL-T06: todo nodo normativo IR tiene anclaje fuente/derivación.
- GSL-T07: ninguna declaración GSL válida sin representación/disposición.
- GSL-T08: igualdad de compilación incremental y total en modelo declarado.
- GSL-T09: compilación no confiere Ratified/MateriallyQualified.
- GSL-T10: UTF-8 stream/chunk y text edit full rebuild igualan referencia independiente.
- GSL-T11: compilación no diluye UNKNOWN y CONFLICT.
- GSL-T12: diferencia estricta entre compilación, PO, realización en código y cualificación.

La ausencia de compilación Lean/material Cargo significa **no teoremas mecanizados ni PASS material**. Preparar modelos V0 independientes, pruebas de mutación y auditores por bloque antes de cierre.

## VII. Estados y programa de ingeniería

LC00 contrato de lenguaje/semántica; LC01 tipos/IR; LC02 V0; LC03 extractor/lexer/parser; LC04 resolver; LC05 typechecker; LC06 elaboración; LC07 source maps y canonización; LC08 diagnósticos/PO; LC09 G00 vertical; LC10 auditor adversario; LC11 integración del servicio; LC12 cualificación. Reconciliar todos con B00…B09 de G-00, sin duplicar owners semánticos ni crear campañas G-14.

**DevelopmentComplete** = original/derivadas aplicables, artefactos, tests y adversarios authored. **CampaignClosed** agrega auditoría independiente después de bloque, ejecución material y recibos sobre candidato exacto. Un listado de tests lógicos no significa tests authored. Un oráculo que compara implementaciones pero toma de una de ellas el resultado esperado no es independiente.

## VIII. Interfaces y seguridad

El frontend no importa las políticas de Gatekeeper, Git writer, agente SDK, SQL projector ni código Compute Master. Python Domain/Constitution conserva semántica normativa; Rust sintaxis textual puede ejecutarse como helper bajo protocolo versionado; V0 es independiente de ambos. Todos los errores incluyen código, fuente, offset, frontera que falló y efecto de admisibilidad. La herramienta no contiene un botón de «self RATIFY» y el builder no controla verificadores protegidos.

**Gate de diseño:** gramática/constructores exactos, firmas, IR, autoría, source maps, corpus G00, V0 y todas PO definidas. **Gate material:** Cargo o implementaciones del frontend y tests reales, oráculos/fixtures ejecutados, mutaciones detectadas, recibos exactos, auditor externo, sin elevar resultados más allá de su perfil.
