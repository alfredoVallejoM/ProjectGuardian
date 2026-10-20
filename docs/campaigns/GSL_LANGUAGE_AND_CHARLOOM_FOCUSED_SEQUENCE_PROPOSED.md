# Programa prioritario GSL + Charloom — construcción por contratos y prueba progresiva

**Estado:** propuesta de desarrollo y experimento local comprobado parcialmente, no ratificación de G-00, no certificación global. Este programa **no añade G-14 ni sustituye las 163 obligaciones G-00…G-13**. Código del compilador en etapa experimental; Charloom source-kernel CTK-01 escrito como candidato, sin Cargo material ejecutado.

## 1. Prioridad y dependencias

PRIORIDAD 1: IR y semántica GSL, referencias y SourceUniverse, primera compilación verificable. PRIORIDAD 2: GSL-1 suficiencia de refinamientos y paquetes; GSL-2 correspondencia con código; GSL-3 procesos y recursos. Charloom refuerza sólo el frontend físico en paralelo, no bloquea al núcleo semántico Python. Todo cambio de decisión arquitectónica necesita ratificación conforme al programa original.

| Corte | Guardian GSL, obligación de implementación | Charloom CTK concurrente | Falsación principal |
|---|---|---|---|
| F00 | Versión de semántica y contrato IR; dueño normativo | CTK-00 inventory y dependencias | dos autoridades en conflicto |
| F01 | Referencia GSL0.1, gramática, registros y tipos del fragmento | CTK-01 scanner y rangos UTF-8 | omitir cláusula y continuar COMPILED |
| F02 | SourceBundle pin exacto y parser Markdown normativo | CTK-02 streaming independiente de chunks | bloque normativo perdido, delimitador dentro de string |
| F03 | AST tipado, namespacing, firmas semánticas | CTK-03 índices y árbol validado | Ref Scope tratado como Ref Verification |
| F04 | AST→IR, PO, source maps completos y canonicalización | CTK-04 edición incremental vs full rebuild | source origin incorrecto o digest inestable |
| F05 | V0 independiente con ejemplos revisados y mutación | CTK-05 CST genérico sin ComputeStage | dos parsers coinciden pero ambos ignoran un campo |
| F06 | Todos los G00 parent+cláusulas/test specs conservados | CTK-06 CST↔AST structural map | G00 F07 desaparece sin diagnóstico |
| F07 | GSL-1 RefinementCase, puente J y factibilidad | CTK-07 corpus/anotaciones opcionales | hojas PASS/raíz FALSE |
| F08 | GSL-2 abstract-state, invariants y RealizationWitness | CTK-08 protocolo batch Rust–Python | método privado PASS con API rota |
| F09 | GSL-3 proceso, resource models, policy | CTK-09 Cargo, clippy, equivalencia y SHA | auditor mismo que builder o p99 sin perfil |
| F10 | Replay, compatibilidad, incremental vs full, fuzz | CTK-10 corpus real para parser GSL | antigua versión acepta nueva feature ignorándola |
| F11 | E2E selfhost Guardian + pilotos externos | CTK-11 adopción scoped y receipts | programa se certifica a sí mismo |

Las dependencias originales G son condiciones de cierre de campaña, no prohibiciones absolutas de desarrollar prototipos aislados con interfaces fijadas.

## 2. Resultado real limitado ya ejecutado localmente

En una referencia Python/Lark aislada (experiments/gsl0_reference) se elaboró un fragmento GSL0.1 con declaraciones source/scope/objective/capability/property/obligation/verification/relation. El compilador candidato:
- Comprueba clases básicas de campos y cardinalidades.
- Resuelve referencias tipadas dentro del proyecto con SourceCatalog inyectado.
- Rechaza versiones, símbolos, predicados y métodos desconocidos.
- Produce un IR JSON canónico con referencias explícitas tipo/proyecto.
- Produce spans UTF-8 y separa SourceDigest de ContractDigest.
- Representa propiedades diferidas y enlaces padre/hijo con PO UNPROVEN.
- Mantiene estado PROPOSED_NOT_RATIFIED, nunca emite certificados.

En la sesión de desarrollo autoral, 30 tests Python pasaron, incluidos casos negativos. La vertical G00-01 CANDIDATA tiene 35 declaraciones (3 fuentes, 1 scope, 10 properties, 1 obligation, 10 verification specs, 10 relaciones) y genera 20 PO UNPROVEN. Los IDs reales se basan en tres catálogos fuente distintos: campaigns.json, g00_functional_refinement.json y g00_validation_plan.json.

**Esto NO equivale a GSL-0 completo ni a conformidad de todas las obligaciones G00.** Faltan import Markdown, parser normativo completo, cuantificador finito, recuperación de errores formal, scopes completos, firmas de predicados extensibles, correspondencia con dominio productivo, evaluación material de código, fuente Git congelada con grants, hermeticidad/seguridad y prueba semántica mecanizada. El catálogo del experimento está inyectado y no es un gate de autoridad.

## 3. CTK-01 de Charloom y próximos cortes

Un componente Rust aislado es candidato bajo components/charloom-source-kernel, con workspace anidado, dependencia en charloom-core y API TextRange64 / LosslessKind / LosslessSegment / scan_lossless / validate_lossless_segments. Reutiliza Unicode EChar y la clasificación CL-T; no incorpora estructuras de Compute. Los tests Rust están **autorados pero NO EJECUTADOS** por ausencia de Cargo en el entorno de autoría.

CTK-02 añade streaming con equivalencia frente a scan completo por partición arbitraria. CTK-03 extrae StructureStore e índices sin acoplar módulos Compute. CTK-04 adapta patch lossless con prueba incremental=full. CTK-05 extrae algoritmo de delimitadores de CL-C02 sin GenericComputeStage; un token GSL String literal jamás abre un grupo. CTK-06 aporta correspondencia AST↔CST sin semántica propia de CCRR. CTK-08 establece protocolo Rust/Python con entradas UTF-8, digests, spans, límites de recursos y ninguna credencial.

No se afirma que la copia inicial de CTK-01 pase los tests existentes de CL-T hasta reejecutarlos en el corte nuevo contra el source pin de Charloom.

## 4. Condiciones de puesta en marcha de cada unidad

Un constructor de GSL empieza por fuente/contrato exactos, firmas, API, decisiones y pruebas adversarias. Desarrolla la totalidad del bloque, tests, verificador y puente aplicable. Solo al declarar bloque terminado interviene el auditor independiente con su informe por obligación. Después se ejecutan pruebas materiales y recibos. No registrar DOWNSTREAM PASS si el upstream es diagnóstico/UNKNOWN.

La nomenclatura F/LC/CTK son unidades subordinadas de ingeniería, NO campañas normativas adicionales. Las obligaciones pertenecen a G-00 (tipos/sources), G-01 (versiones), G-02 (refinamiento), G-04 (paquetes), G-05/G-07 (código/adapter), G-06 (evidencia), G-09 (admisión), G-11 (CLI/MCP) y G-13 (E2E).

No GH Actions, no ramas nuevas, no hard SHA global si la evidencia protegida no depende de otros cambios. Cuando el build material pueda ejecutarse, registrar exacto commit, perfil, dependencias y logs; no inventar Cargo PASS.

## 5. Criterio de verdad para un gate

DESIGN_READY: contrato entero del corte con semántica, obligaciones y excepciones conocidas. DEVELOPMENT_COMPLETE: source, pruebas, adversarios, verificadores y puentes autorados e implementados, sin placeholders. MATERIAL_QUALIFIED: prueba material ejecutada, auditor distinto, recibos independientes y sujeto/código/revisión exactos. Pueden existir resultados negativos valiosos sin que el programa esté globalmente certificado.

La raíz externa V0 compara modelos finitos, inventario original y alteraciones negativas; no importa el compilador candidato. Toda claim superior necesita argumento de suficiencia además de soporte para sus hijos.
