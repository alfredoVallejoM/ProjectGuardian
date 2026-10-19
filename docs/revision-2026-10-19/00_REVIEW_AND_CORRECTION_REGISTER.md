# ProjectGuardian — Revisión integral y registro de correcciones (propuesta)

**Estado:** DESIGN_CORRECTION_PROPOSED; NO RATIFICADO; NO IMPLEMENTADO; NO CERTIFICADO.
**Corpus observado:** main af8c396e5598a1b00c764a27a8cde948ca7ade7e (2026-10-19).
**Alcance:** programa original G-00…G-13, 34 PG-REQ, 30 PG-ADR propuestas, 163 obligaciones, 142 ubicaciones propuestas; extensiones CCRR, suficiencia, realización estructural y autoverificación.
**Exclusión deliberada:** no diseñar todavía la gramática definitiva, semántica primitiva ni contrato de aceptación GSL-0. Se abrirá una deliberación específica posterior.
**Regla de autoridad:** este documento es un artefacto de revisión y propuesta; ni su publicación ni el uso de la palabra «corrección» ratifican cambios normativos. La fuente original permanece intacta.

## 1. Veredicto de revisión documental

El plan original distingue objetivo, capacidad, propiedad, obligación, implementación, verificación, ejecución, evidencia y certificado. Contiene una secuencia completa de catorce campañas y un procedimiento B00…B09 específico de G-00. Sus estados correctos son diseño propuesto, cero código productivo, cero tests materiales ejecutados, cero certificados. Es necesario **fortalecer la explicación de cómo se demuestra la suficiencia de las descomposiciones y la correspondencia con el código**, sin reemplazar el modelo ni su historia.

La trazabilidad global de architecture/traceability.json enlaza cada PG-REQ a campañas completas y enumera todas las obligaciones de las campañas elegidas; esta expansión es un **enlace grueso de asignación programática**, no una relación semántica fina. El documento ya indica fine_grained_semantic_links_verified=false. Cualquier numerador de «obligaciones cubiertas» obtenido de esos enlaces carece de autoridad para afirmar adecuación semántica. Hay que conservar el enlace histórico, etiquetarlo inequívocamente como grueso y construir una correspondencia candidata selectiva PG-REQ → faceta → obligación → subcláusula → verificación de suficiencia.

G-00 dispone de 120 subcláusulas, 58 contratos de API, 120 tests lógicos planificados, 36 mutaciones y 7 verticales previstas. La comprobación documental previa verifica referencias, **no** demuestra que las subcláusulas sean suficientes para cumplir cada obligación superior, que el código exista, que los tests hayan sido implementados ni que los verificadores sean sólidos.

Hay 30 ADR PROPOSED_NOT_RATIFIED. Sus conflictos y decisiones nuevas (lenguaje tipado, IR, suficiencia, oráculos de bootstrap, frontera de confianza) deben tramitarse mediante ratificación o enmienda. La arquitectura prevista es Python tipado, monolito modular, Git autoritativo o fuente histórica designada, SQLite derivado, agentes opcionales y Gatekeeper aislado. Se preserva la separación Lean/Rust de los proyectos consumidores; Guardian no los acopla como pipelines.

La rama main no figura protegida en la consulta realizada. Sin credenciales de escritura segregadas, las pruebas de un Gatekeeper local no acreditan imposibilidad de bypass de publicación.

## 2. Defectos de diseño y correcciones obligatorias propuestas

| ID | Problema objetivo | Corrección de diseño | Dueño propuesto | Evidencia de aceptación |
|---|---|---|---|---|
| COR-01 | Trazabilidad global gruesa usada como cobertura semántica | Mantener referencia histórica y publicar correspondencia fina *candidata*, por facetas y con huecos | G-10/G-02 | Ningún enlace CAMPAIGN_RESPONSIBILITY se computa como SUFFICIENT_REFINEMENT |
| COR-02 | Confundir muchos tests positivos con la suficiencia de una descomposición | RefinementCase: goal, children, bridges, assumptions, proof obligation, feasibility | G-02/G-04 | Modelo con todas las hojas verdaderas y padre falso bloquea cierre |
| COR-03 | No hay lenguaje de autoría normativo compilable | Reservar front-end GSL por perfiles y un IR tipado único; diseño de GSL-0 pendiente | G-00/G-11 | Ninguna semántica se aprueba sin contrato de compilación y source map |
| COR-04 | RealizationLink puede reducirse a enlace a archivo | RealizationWitness enlaza sujeto, build, symbol/route, representación y evidencias | G-05/G-07 | Función correcta no invocada por la API no acredita capacidad |
| COR-05 | Falta el bootstrap independiente | V0 externo y cortes SH como evidencias, no campañas normativas | G-00/G-13 | Mutación del candidato no puede alterar oráculo congelado |
| COR-06 | Mezcla de status de desarrollo y certificación | Estados de especificación, autoría, auditoría, material, evidencia, cierre y migración ortogonales | G-00/G-06 | Test authored no promueve material PASS |
| COR-07 | Semántica de recursos, proceso y arquitectura no uniforme | Tipos de obligación por dominio de observación y política de verificador | G-00/G-05/G-06 | Benchmark no certifica estructura; test funcional no certifica proceso |
| COR-08 | Implementaciones pueden crear rutas públicas no inspeccionadas | Cobertura de superficie productiva por build/profile y propagación de UNKNOWN | G-05/G-07 | Ruta alternativa insegura bloquea cualificación integral |
| COR-09 | Cambio normativo puede parecer editorial | Diff semántico y ratificación bajo constitución previa | G-01/G-09 | Enmienda autoautorizada rechazada |
| COR-10 | No existe garantía de cierre global composicional explícita | Argumento de suficiencia raíz + INT-01…INT-08 | G-13 y dueños por integración | PASS de módulos con falla E2E no cierra Guardian |
| COR-11 | Riesgo de overvalidation/reutilización insegura | Cono protegido tipado, dependencias completas o HOLD; equivalencia de replay | G-02/G-06/G-12 | Modificación irrelevante se reusa; relevante invalida |
| COR-12 | Riesgo de dos autoridades GSL/JSON/Markdown | Una revisión admitida de IR con fuente tipada y compilador fijados; precedencia histórica hasta ratificación | G-00/G-01/G-09 | Diferencia entre dos representaciones = SPEC_CONFLICT |
| COR-13 | Unidades sin garantías locales y de interacción | Cada familia de obligación declara verificador y condiciones de ensamblaje | G-04/G-06 | Paquete no omite bridge ni consumer |
| COR-14 | Interfaces de agentes pueden reconstruir normas distintas | CLI/API/MCP/UI acceden a los mismos servicios normativos | G-08/G-11 | Igual query, mismo snapshot y veredicto, distinto formato permitido |
| COR-15 | Falta un protocolo concreto de autodesarrollo | Cortes SH-00…12 con comparador externo, negativo y positivo | G-13 transversal | Solo promueve estado por evidencia independiente |
| COR-16 | GSL como posible gran diseño antes de validar necesidades | Posponer contrato detallado GSL-0; congelar solo requisitos previos del front-end | G-00/G-11 | No se confunde este registro con aprobación de gramática o semántica |

## 3. Lo que expresamente NO se cambia

- Los 34 identificadores PG-REQ, las 30 ADR originales, las 14 campañas G-00…G-13 y sus 163 obligaciones originales.
- B00…B09 de G-00; sus 120 subcláusulas, 58 contratos API y 120 contratos lógicos de test no son nuevas obligaciones históricas.
- Los estados de autoridad: PROPOSED no equivale a RATIFIED; DESIGN no equivale a IMPLEMENTED.
- La independencia por proyecto: ningún contrato de otro repositorio se adopta por similitud de texto.
- El criterio de cierre: DEVELOPMENT_COMPLETE = funcionalidades, pruebas, adversarios y verificadores exigidos desarrollados; CAMPAIGN_CLOSED agrega ejecución material, auditoría y evidencia conforme a política.
- Ninguna automatización de GitHub Actions; ninguna rama nueva por este plan. Los candidatos pueden prepararse en ubicaciones aisladas y la publicación a main requiere aprobación y barrera efectiva.

## 4. Doble revisión semántica de los contratos

**Downward:** PG-REQ → facetas verificables → obligaciones dueñas → relaciones de refinamiento → componentes y puentes → evidencias terminales.
**Upward:** código y eventos observados → testigos de realización → condiciones terminales → argumentos de suficiencia → compromisos superiores.

Un camino de enlace documental no es una demostración. Un certificado de cada hoja tampoco implica la raíz sin puentes y premisas. Toda promoción semántica exige un juicio distinto y su procedencia.

La tabla architecture/ccrr_requirement_crosswalk_proposed.json aporta correspondencias **selectivas candidatas**, no declara que estén justificadas. Cada entrada tiene una pregunta de aceptación y un contraejemplo a buscar.

## 5. Política de hallazgos y disposición

Cada problema identificado en la revisión recibe:
- ID estable, fuente exacta y revisión.
- Clase: SOURCE_OMISSION, UNGROUNDED_RESTRICTION, TYPE_GAP, SUFFICIENCY_GAP, REALIZATION_GAP, PROOF_GAP, TRUST_GAP, CONFLICT.
- Relación con PG-REQ y GXX-nn.
- Estado OPEN, FIX_PROPOSED, DEVELOPED, INDEPENDENTLY_REVIEWED, MATERIALLY_QUALIFIED o HOLD.
- Condición verificable de reparación y contraejemplo que debe dejar de pasar.
- Decisión de autoridad cuando altera un compromiso.

No se pueden cambiar los denominadores simplemente trasladando requisitos vigentes a FUTURE o eliminando los hallazgos de un informe.

## 6. Orden de corrección documental antes de GSL-0

1. Preservar snapshot y extraer corpus inmutable.
2. Revisar trazabilidad gruesa, introducir correspondencia fina candidata y huecos.
3. Asignar las nuevas responsabilidades a las 163 obligaciones originales y sus dueños.
4. Especificar formalmente justificación de refinamientos, realización y cualificación.
5. Completar fichas de campañas con fronteras, integración, adversarios y autoaplicación.
6. Definir V0, cortes SH, fronteras de confianza y criterios de promoción.
7. Reconciliar las decisiones propuestas con ADR existentes y registrar decisiones pendientes.
8. Auditar coherencia documental y publicar los cambios como PLANIFICACIÓN PROPUESTA.
9. **Después**, discutir y formalizar el contrato concreto de GSL-0: gramática, semántica, AST/IR, evaluador de referencia y oráculos.

No se llama a este trabajo «G-00 cerrado». El desarrollo material inicia solo con un contrato admitido del bloque correspondiente.
