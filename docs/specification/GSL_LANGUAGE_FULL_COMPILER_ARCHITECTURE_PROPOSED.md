# GSL — Arquitectura formal del compilador de especificaciones

**Estado:** CANDIDATO DE DISEÑO, NO RATIFICADO. No se afirma que GSL completo esté implementado ni que existan teoremas Lean mecanizados. Contratos originales ProjectGuardian G-00…G-13 permanecen vigentes como propuesta sin alteración.

## 1. Objeto y fronteras

GSL compila especificaciones *ya tipadas* en un ContractIR, SourceMap, obligaciones de prueba y diagnósticos. Un modelo de IA puede asistir la interpretación de Markdown histórico pero su salida es Candidate, no norma. Compiled ≠ Ratified ≠ DevelopmentComplete ≠ MateriallyQualified.

El proyecto matemático es P=(Σ,N,X,A,W,H,E): Σ lenguaje; N constitución normativa; X estructura abstracta exigida; A argumentos de refinamiento; W realizaciones código/build/trazas; H transformaciones; E evidencia. N, X y W no se fusionan.

Una obligación o: Commitment[K,S] se interpreta sobre proyección π_{K,S}(w) del universo de realizaciones. K determina dominio: Existence, Behavior, Constitution, Execution, Development, Integration o Migration. La compilación conserva la exigencia; no decide si w la satisface.

## 2. Perfiles acumulativos del mismo lenguaje

| Nivel | Constructores admitidos | Trabajo formal posterior |
|---|---|---|
| GSL-0 | project, source, scope, objective, capability, property, obligation, relation, verification; términos y predicados tipados | Identidad, procedencia, ámbitos, lógica V4, estructura normativa |
| GSL-1 | refine, bridge, assume, depend, alternatives, revise, supersede | Hipergrafo, factibilidad y suficiencia A ∧ D ∧ J ⇒ G; transporte histórico |
| GSL-2 | model, operation, invariant, requires, ensures, implements, algorithm, observed_route | Estados abstractos, simulación de código, dominio soportado, rutas y consumidores |
| GSL-3 | process, event, transition, resource, budget, policy, qualification | Historias temporales, condiciones de auditoría, recursos, permisos y certificaciones |

Los cuatro niveles comparten ContractIR discriminado y versiones semánticas. Un compilador antiguo NO ignora un constructor normativo desconocido. Una nueva versión debe preservar la semántica del fragmento anterior o generar ChangeSet semántico con ratificación propia.

## 3. Semántica de compromisos y suficiencia

Una exigencia o tiene denotación [[o]]_{K,S} ⊆ Observations(K,S) o predicado φ_o. La conformidad w⊨o es diferente de poseer evidencia de conformidad.

RefinementCase=(Goal,ChildFormula,Bridges,Assumptions,Scope,PO,Origins). Sus condiciones son:
- ∀w, A(w)∧D(w)∧J(w) ⇒ G(w) (suficiencia);
- ∃w, A(w)∧D(w)∧J(w) (factibilidad);
- A(w*)∧D(w*)∧J(w*) (realización concreta).
Un grafo con todas las hojas en PASS no demuestra la raíz sin argumentar J y las implicaciones. Las derivaciones de soporte deben fundamentarse, sin ciclos vacíos.

Una migración conservadora Δ:P→Q debe justificar la proyección histórica πΔ(A(Q))⊆A(P) para compromisos protegidos. No representar enmienda como refinamiento conservador.

Para código, una realización C↠A requiere una relación R de estados, correspondencia de transiciones, outputs, dominio de entradas, terminación/efectos/algoritmo/recursos cuando se exijan. Un método privado correcto no acredita la ruta API pública.

## 4. Lógica fundacional V4

V4={(0,0) UNKNOWN, (1,0) YES, (0,1) NO, (1,1) CONFLICT}. Negación intercambia bits, AND=(a+∧b+,a−∨b−), OR=(a+∨b+,a−∧b−). Es información, no autoridad probatoria. Separar Applicability, Due y Satisfaction. Un error léxico no es UNKNOWN; un timeout no es NO.

Sistema de tipos: ProjectId≠RevisionId≠ContentDigest; Ref[Scope]≠Ref[VerificationSpec]; Predicate[D] posee firma, dominio, versión y semántica admitida. Una DeferredProperty conserva identidad/fuente/ámbito pero no genera PROVEN. Evitar ejecutar Python arbitrario por nombrar una función en el documento.

GSL-0 puede implementar cuantificadores solo sobre conjuntos finitos de un SourceUniverse completo y congelado; la exhaustividad del enumerador es otra obligación. No se presupone cuantificación abierta sobre cualquier programa.

## 5. Compiler ABI y estados de resultado

Compile_v(SourceBundle,CompileContext) = Rejected(errors) + Analyzed(partial,diagnostics) + Compiled(IR,SM,PO,Manifest,diagnostics).

SourceBundle preserva bytes originales, source IDs, revisiones y digests. CompileContext contiene project, pin exacto, registries de tipos/predicados, namespace grants, lenguaje e identidad de compilador. No HEAD mutable ni red en el núcleo puro.

C00 Acquire: SourceBundle; C01 Extract: unidades GSL normativas de Markdown, excluyendo ejemplos; C02 Lex: tokens y trivia sin pérdida; C03 Parse: CST; C04 Abstract: AST con correspondencias; C05 Resolve: referencias exactas; C06 Typecheck; C07 WellFormed/Semantics; C08 Elaborate: IR; C09 PO generation; C10 IR integrity; C11 Canonicalization; C12 ContractDiff; C13 Bundle emission. Admission está FUERA del compilador.

Cada etapa produce tipo nominal e invariantes verificables, nunca un dict cualquiera como prueba de corrección. El parser en modo editor no puede promover un PartialAST como contrato íntegro.

## 6. Leyes de preservación

T-0 (fuente): concatenación de segmentos/tokens+trivia y Yield(CST) reconstruyen bytes GSL originales; los offsets son UTF-8 byte offsets válidos.
T-1 (AST): toda declaración normativa admitida tiene nodo y anclaje CST.
T-2 (tipos): Γ⊢e:T ⇒ Γ'⊢Lower(e):Translate(T).
T-3 (semántica): Eval_IR(Lower(e),ρ)=Eval_GSL(e,ρ) para expresiones y modelos interpretados. Inducción en constantes, átomos, not, AND, OR y cuantificación finita cuando se habilite.
T-4 (source grounding): cada IR normativo tiene SourceOrigin o derivación finita autorizada.
T-5 (coverage): las declaraciones GSL válidas están representadas en IR; NO implica que el corpus original en lenguaje natural haya sido importado exhaustivamente.
T-6 (determinismo): misma fuente, contexto y compilador fijados producen mismo IR canónico.
T-7 (incrementalidad): compile_incremental(D,Δ) ≅ compile_full(D+Δ); al cambiar estados lexicales se expande la región de invalidez.
T-8 (autorización): Compile no tiene capacidad para emitir Ratified, MateriallyQualified ni escribir la referencia Git protegida.

Son teoremas OBJETIVO para formalización y pruebas adversarias, no certificados actuales.

## 7. SourceMap e identidades

SourceOrigin=(ProjectId,DocumentId,RevisionId,CryptoDigest,[start_byte,end_byte),rule_origin?). Mismo contenido en dos documentos no convierte sus fuentes en una. NodeId del backend textual NO equivale a ObligationId. Line/column es vista calculada, no identidad. SourceDigest es de bytes originales, ContractDigest es semántico/canónico, CompilationDigest liga compilador, registries y contexto. Una firma algebraica no sustituye hash criptográfico.

No canonizar listas con orden semántico (roles n-arios, eventos, pasos algorítmicos). Normalizaciones entre expresiones semánticamente equivalentes requieren regla demostrada; no inferir equivalencia universal por ordenar diccionarios.

## 8. Importación Markdown histórica

Entrada histórica: SourceUniverse + spans y hechos exactos; extracción asistida del lenguaje natural → candidaturas GSL con origen. Esta transformación NO es el compilador confiable. Para cada requisito: REPRESENTED, PARTIAL, DEFERRED, CONFLICT o OUT_OF_SCOPE_WITH_REASON. Un inventario externo independiente detecta omisiones. La compilación GSL→IR es otra propiedad: C1 no implica que el importador haya cumplido cobertura C2.

Primera vertical G00-01: padre en architecture/campaigns.json; diez F01..F10 en architecture/g00_functional_refinement.json; diez T01..T10 en architecture/g00_validation_plan.json. El frontend debe conservar 10+10 y declarar refinamientos/proof obligations abiertos, no que todos fueron materialmente desarrollados.

## 9. Charloom y separación entre backends

Charloom CTK (Rust) aporta UTF-8, rangos, pérdida cero y después CST genérico/AST↔CST. GSL lexer/parser agrega semántica de strings/comentarios. Guardian Python contiene tipo normativo, autoridad, IR y semántica CCRR. El helper Rust recibe bytes sin credenciales ni autoridad, responde spans/tokens/estructura bajo protocolo versionado; nunca Ratified o PROVEN.

Dos backends de referencia: parser Python/Lark para fragmento acotado y Rust Charloom para etapas de fuente; equivalencia se comprueba con fixture independiente y benchmark por corpus, no se asume. Charloom Compute Master queda explícitamente excluido. El plan de extracción concreta CTK-01.. está en Charloom y en documentación de Guardian.

## 10. Desarrollo y condiciones de admisión

LC00 semántica/fichas de constructores; LC01 IR tipado; LC02 V0; LC03 Markdown/lexer/parser; LC04 resolver; LC05 typecheck; LC06 lowering; LC07 canonización/source map; LC08 PO y diagnósticos; LC09 integración con G00; LC10 auditor adversario tras desarrollo del bloque; LC11 interfaces; LC12 cualificación scoped. Reconciliar B00..B09, no crear otra campaña G14 ni repetir owners.

Un test authored no es run PASS. DevelopmentComplete requiere todas las obligaciones productivas, pruebas, adversarios, verificadores y bridges implementados. CampaignClosed añade material runners, auditoría independiente y recibos por SHA/perfil. Ninguna fase del lenguaje puede ratificarse a sí misma.

## 11. Preguntas que todavía necesitan ratificación

Forma normativa exacta de Markdown y GSL, semántica de fuente GSL vs IR como autoridad fijada, fragmento cuantificado GSL-0, IR Schema compatible con ProjectContract original, versión/firma de los registries, semántica de errores de import, perfil de coste aceptado, frontend Python frente Rust, garantías de seguridad del helper. No convertir decisiones de un experimento en ADR aprobadas.
