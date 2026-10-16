# 11 — Arquitectura de software y patrones de ingeniería

## Decisión tecnológica propuesta
Python 3.12+ tipado y testeado como núcleo de dominio inicial; `dataclasses(frozen=True,slots=True)`, Enum, tipos nominales, uniones discriminadas, `Protocol` para límites reales; JSON Schema 2020-12 en persistencia; Git como authority, SQLite/FTS5 como proyección, runners externos Rust/C++/Python/Lean; CLI y API; UI cliente opcional y herramientas para agentes. No introducir segundo núcleo Rust+Python; extracción futura de verificador crítico requiere pruebas de equivalencia y decisión.

## Monolito modular
No microservicios como premisa. Dominio puro define Project/Contract/Obligation/Property/Campaign/Claim/Source/Authority; Constitution/Graph/Program/Knowledge/Work/Assurance/Governance/Application agrupados por responsabilidad, no por número de líneas. Puertos hacia SourceReader, ProjectStore, GraphQuery, CodeInspector, VerificationRunner, AttestationVerifier, Authorization, ArtifactStore, AgentExecutor; adaptadores implementan los puertos. Ningún consumidor de interfaz reimplementa reglas.

## Patrones obligatorios y cuándo
- Domain-Driven Design: agregados pequeños con autoridad. No una clase Project omnipotente.
- Functional Core / Imperative Shell: `apply(state,command) -> Result`, `evaluate(scope,claim)` y `calculate_impact` puros; Git/network/process fuera.
- Hexagonal Ports & Adapters: dependencia hacia el dominio, nunca dominio→Git/SDK/DB.
- Immutable Value Objects + explicit revision: sin setters normativos.
- Algebraic Data Types: `PASS, FAIL, UNKNOWN, CONFLICT, NOT_APPLICABLE` y `RequiresApproval` distinguidos, errores operativos separados.
- CQRS ligero + snapshots: comandos normativos en Git, vistas en SQLite.
- Event-based evolution: acciones de contrato como eventos, no CRUD indiferenciado.
- Specification Pattern: applicability por predicates tipados, extensible pero no lenguaje arbitrario.
- Strategy/Registry: profiles de obligaciones/verificadores admitidos, no if por nombre de proyecto.
- Anti-Corruption Layer: importar FC2, Charloom, Reason Engine manteniendo status/ownership originales.
- Optimistic Concurrency + Unit of Work: publish CAS y reconstrucción de índice.
- Content-addressed evidence y protected dependency cones.
- Policy-as-code versionada, pero verificador matemático especializado se mantiene aparte.

## Evitar sobreingeniería
No abstract factories sin múltiples consumidores, BaseEntity universal, frameworks de inyección, ORM como semántica, event bus distribuido, DAG engine externo obligado, base Neo4j obligatoria, agentes embebidos en dominio, dashboards como source of truth, ni límite duro o blando de LOC. Dividir archivos por cohesión, estabilidad de contratos y motivos independientes de cambio, no por tamaño.

## Contratos internos
`evaluate_change(snapshot,changeset,policy)`, `required_obligations(snapshot,target,profile,milestone)`, `evaluate_coverage(closure,delivery,evidence)`, `calculate_impact(graph,changeset,profile)`. Cada método devuelve resultado tipado + evidencia/razones y no I/O. El ensamblaje de puertos está en bootstrap.

## Dependencias permitidas
domain imports stdlib solamente. constitution/graph/program dependen domain; knowledge proyecta observaciones usando ports, work usa graph+contracts+orientation, assurance consume VerificationSpec/Run/Evidence, governance admite cambios con protected policy, application coordina. adapters importan ports pero no reciben permiso de reescribir contratos. Ningún componente salvo publication modifica refs Git autorizadas.

## Recursos
Algoritmos de grafos por listas de adyacencia + índices inversos, DFS/BFS O(V+E), SCC y topología para proyecciones DAG, soporte con ALL/ANY/condicionales y presupuesto de cómputo. Escala real medida por perfiles con receipt, no complejidades inventadas para operaciones difíciles de SAT/alternativas.

## Política de test
Cada contrato produce positivo, negativo, frontera, mutación adversaria, prueba entre módulos, comparación de proyección/autoridad, y cuando corresponda recursos, concurrencia, crash/replay, seguridad y autenticidad. Los tests unitarios no sustituyen flujos E2E ni verificadores matemáticos independientes.


## Cliente interactivo (tecnología propuesta no ratificada)
El núcleo Guardian se desarrolla en Python tipado. La interfaz gráfica se diseña como cliente TypeScript modular (componentes React o equivalente), bajo `clients/web/`, consumiendo el mismo contrato de API que CLI/MCP. No importa clases de negocio Python ni implementa su propia semántica de certificación. Sus 16 módulos prospectivos se registran en el atlas para G-11 y podrán fusionarse por cohesión, no por meta numérica.
