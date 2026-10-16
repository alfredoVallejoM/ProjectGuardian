# 03 — Grafo tipado, relaciones n-arias y soporte

## Modelo
`GraphNode = (project, logical_id, revision_id, kind)`.
`RelationRevision = (relation_id, type, role-indexed participants, scope, provenance, authority, revision)`. Roles n-arios y multiplicidad explícitos; una relación matemática de tres sujetos no se reduce a dos enlaces sin semántica.

## Relaciones y typing
`REFINES, GENERALIZES, SUPERSEDES, REQUIRES, HAS_PROPERTY, IMPLEMENTS, SUPPORTS, HAS_VERIFICATION, EXECUTED_AS, EVIDENCES, CONSUMES, OWNED_BY, DEPENDS_ON, CONTRADICTS, BLOCKS, DERIVED_FROM, INVALIDATES`.
Cada relation type declara participantes válidos, cardinalidades, ámbito, invariantes de autoridad y efectos sobre certificaciones. Importar "similar" no implica "equivalente"; un Crate no "demuestra" un Theorem por existir.

## Proyecciones (no cuatro bases de datos)
1. Semántica: objetivos, matemáticas, capacidades, leyes, owners; ciclos matemáticos permitidos.
2. Arquitectura: componentes, APIs, deps reales/permitidas/prohibidas.
3. Ejecución: prerequisitos estrictos DAG, alternativas y condiciones de applicability; ciclos estrictos bloquean despacho, salvo tratamiento explícito como conjunto o punto fijo.
4. Soporte: claim→property→verification→evidence→inputs protegidos.

## Support logic
Una propiedad puede requerir `ALL(E1,E2,E3)` o `ANY(ALL(E1,E2),ALL(E3,E4))`. No basta contar receipts; se evalúan alternativas, dependencias y ámbitos. `UNKNOWN` de una rama no es `PASS`. Falsaciones y tests adversarios se conectan al contrato original.

`SupportCone(q,S,r)` es el conjunto de dependencias **autorizadas como soporte** para claim q, perfil S y revisión r, no todo nodo alcanzable. `ImpactCone(Δ,S,r)` utiliza relaciones inversas de consumo/protección y recalcula estado de claims afectados hasta punto fijo. `SupportGap` muestra requisitos sin soporte admisible, desagregados por implementation/test/runtime/integration/source/applicability.

## Algoritmos
Mapas ID→Entity, adyacencias por tipo/dirección, índices inversos. Recorridos BFS/DFS O(V+E) en subgrafo, topología Kahn para DAG, componentes fuertemente conexas para conflictos de ejecución, punto fijo acotado en propagación. Expresiones conjuntas/alternativas no se interpretan como simples aristas. Consultas difíciles se presupuestan: `RESOURCE_LIMITED` no significa análisis completo.

## Índices derivados y autoridad
SQLite como proyección transaccional reconstruible, con tablas entities, relations, participants, source_refs, claims, work_packages y búsquedas FTS. Una nueva arista generada por un agente es propuesta con provenance, no hecho normativo. La equivalencia/propiedad matemática requiere verificador de dominio o autorización. No precalcular clausura transitiva global sin perfil real de rendimiento.

## Condiciones de cierre
Pruebas de tipos de relaciones, n-aridad, multiplicidad, integridad referencial, dependencias condicionales, owners incompatibles, scope, no mezcla interproyecto, ciclos, variantes ALL/ANY, staleness, invalidación, y explicación de soporte.

