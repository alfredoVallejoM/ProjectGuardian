# Decisiones de ingeniería que debemos discutir tras la publicación

Este documento fija **preguntas de arquitectura concretas**, alternativas y criterios de decisión. No pretende modificar lo ya especificado ni afirmar que existan archivos implementados.

## AD-D01 — Propiedad del ProjectContract
**Propuesta:** ProjectContractRevision como snapshot normativo compuesto de referencias a Objective/Capability/Property/Obligation/Campaign/Architecture/SourceUniverse, no un megaobjeto mutable con toda la información incrustada. Los agregados se versionan independientemente mediante ChangeSet. **Alternativa:** documento monolítico JSON por proyecto. **Criterio:** permitir evoluciones pequeñas, refs estables, no duplicación, replay y consultas de impacto.

## AD-D02 — Lógica de ámbitos y aplicabilidad
**Propuesta:** scope/profile como tipo de dominio con expresiones booleanas tipadas sobre dimensiones admisibles, más predicados opacos que requieren verificador especializado. Resultado YES/NO/UNKNOWN/CONFLICT con evidencia. **Alternativa:** expresiones de texto evaluadas por LLM. **Pruebas:** no se excluye obligación por UNKNOWN; memoria y recursos acotados; características normativas desconocidas bloquean.

## AD-D03 — Representación de obligaciones
**Propuesta:** ObligationRevision inmutable; statement, acceptance, falsification, verification, owner, exclusions y linked source. WorkPackage solo referencia obligs; Claim/Evidence no son campos de Obligation. **Alternativa:** task + completed boolean. **Prueba:** añadir 13a obligación a campaña cerrada no la autocualifica ni borra 12 anteriores.

## AD-D04 — Grafo y semántica ALL/ANY
**Propuesta:** RelationRevision n-aria con roles, scope, provenance, authority, y SupportExpr ALL/ANY/conditional; cuatro proyecciones. **Alternativa:** un grafo binario uniforme con edges textuales. **Prueba:** no cambia significado al componer fuentes/tres sujetos; soporte alternativo válido; ciclos matemáticos permitidos, ciclos de precedencia estricta rechazados.

## AD-D05 — Autoridad del event log
**Propuesta:** ChangeSet/Revision Git es commit lógico, SQLite derivado; cualquier registro embebido del proyecto preexistente mantiene authority mediante adaptador. **Alternativa:** SQLite como editable primario + Git reflejo. **Prueba:** crash-recovery/replay, CAS, acceso multi-repo; no dos escritores de obligación.

## AD-D06 — Frontera entre Constitution y Governance
**Propuesta:** evaluator y invariants puros en `constitution/`; principal, approval, protected installation y admission en `governance/`. Verificar contra policy anterior. **Alternativa:** un archivo que evalúa reglas y realiza Git push. **Prueba:** builder que muta policy no obtiene PASS.

## AD-D07 — Graph Support versus Assurance Policy
**Propuesta:** `graph/support.py` calcula la expresión y caminos de soporte; `assurance/evidence_policy.py` define qué evidencias son admisibles para property/scope; `assurance/qualification.py` emite verdict al combinar ambos. **Prueba:** arista documental no se convierte en certificado por traversability.

## AD-D08 — Cobertura normativa versus cobertura de fuente
**Propuesta:** `knowledge/coverage.py` determina SourceUniverse exhaustividad declarada; `assurance/coverage_assurance.py` acredita esa afirmación según política; `knowledge/reconciliation.py` no altera SpecifiedArchitecture por código observado. **Prueba:** todos los registros internos cubiertos pero fuente externa no examinada -> no SPECIFICATION_COMPLETE.

## AD-D09 — WorkPackage y Orientation
**Propuesta:** `work/orientation.py` vista explicativa; `work/package_compiler.py` closure normativo completo; `context_selection.py` fragmentos bajo presupuesto. **Alternativa:** un prompt generado que contenga parte de las obligaciones. **Prueba:** al reducir tokens no cambia cierre normativo.

## AD-D10 — Integración y responsabilidad de verificación
**Propuesta:** `assurance/integration_assurance.py` formaliza Producer/ConsumerContract; runners sólo producen observations; `assurance/qualification.py` evalúa suficiencia. Lean y Rust son verificadores de ámbitos separados. **Prueba:** una compilación Rust no implica prueba Lean; tests unitarios separados no cierran E2E.

## AD-D11 — Seguridad de la publicación
**Propuesta:** Guardian instalado con credencial de publicación distinta del worktree, trusted policy + compare-and-swap; paths permitidos por paquete. **Alternativa:** instrucción "no cambies la norma" en un prompt. **Prueba:** falsificación de rol, receipts, ruleset y carrera sobre branch bloqueadas.

## AD-D12 — Perfil de agentes
**Propuesta:** protocolo universal para humanos y agentes, cinco roles opcionales; A3 posterior a A2 sólo cuando es independiente y la política lo exige. No vendor lock-in. **Prueba:** monoagente puede crear entrega pero no emitirse auditoría independiente ficticia.

## AD-D13 — Física y cohesión de módulos
La topología de 142 archivos es un **atlas de responsabilidades**, no un objetivo numérico. La apertura de un archivo nuevo exige motivos de separación (distinta estabilidad, change reason, invariant, owner, test surface). No hacer skeletons; mantener cada módulo coherente aunque tenga muchas líneas.

## Resultado de la deliberación
Ratificar, enmendar o mantener HOLD por cada decisión anterior mediante ADR y análisis de impacto. Ningún resumen de esta conversación debe reemplazar las 34 necesidades, 30 ADR y 163 obligaciones existentes.



## AD-D14 — Cliente web como adaptador de presentación
**Propuesta:** TypeScript y componentes React o equivalentes, consumiendo API versionada. El núcleo Python conserva toda la evaluación normativa. **Alternativa:** duplicar estados y conformidad en navegador. **Criterio:** paridad de estados CLI/API/UI/MCP, accesibilidad, rechazo de aprobación por UI sin identidad del servidor y no dependencia del núcleo de ninguna librería frontend. La tecnología exacta sigue pendiente de ratificación.
