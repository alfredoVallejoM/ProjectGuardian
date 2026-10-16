# Orden de discusión arquitectónica — decisiones concretas para aterrizar el desarrollo

El diseño integral está publicado. No abrir G-00 todavía: primero debemos revisar y ratificar los contratos de responsabilidad y sus dependencias. Propuesta de sesiones de arquitectura:

## 1 — Núcleo de dominio y agregados
¿Quién posee ProjectContractRevision? Propuesta: snapshot agregado de referencias, no megaobjeto mutable. ObligationRevision y CapabilityRevision tienen ID/lifecycle separados. Decidir la validez de objetos en memoria, granularidad de cambios y reglas de schema. Interfaces de `domain/project.py`, `obligation.py`, `scope.py`, `authority.py` y `program/revision.py`.

## 2 — Constitución y motor de cambio
Diferenciar `constitution/evaluator.py` (evaluación pura), `program/transitions.py` (evolución) y `governance/admission.py` (publicación efectiva). Precisar autoridad, scopes, enmiendas, source of trust y cómo testear preservación de requisitos sin solver universal.

## 3 — Grafo y prueba de soporte
Definir relation types, participantes n-arios, owners, expresiones ALL/ANY/condiciones, SupportCone, ImpactCone y Gap. `graph/support.py` calcula relaciones; `assurance/evidence_policy.py` decide exigencias epistemológicas. Prever alternativas y límites de búsqueda.

## 4 — Estado observado e importación
Qué produce un SourceAnalyzer, cómo declarar límites de macros/features/dynamic imports, versiones Git, imports interproyecto y correspondencias semánticas. `knowledge/observed_architecture.py` no puede modificar SpecifiedArchitecture. Decidir interfaz a AST externos.

## 5 — WorkPackage y orientación
Compilar cierre normativo desde fuentes y etapas de hito, dividir tareas sin pérdida, hacer consultas progresivas, proteger snapshot y versionar deliveries. Lo que ve el agente es vista; lo que el Gatekeeper comprueba es el manifest completo.

## 6 — Evidencia y certificación
VerificationSpec vs Run vs Evidence vs Claim vs Qualification; scopes; runners; autenticidad; continuidad de antiguos certificados; criterios de "desarrollo terminado" frente a "campaña cerrada"; auditorías por obligación y documento.

## 7 — Gatekeeper, persistencia y despliegue
Protección del evaluator, policy anterior para cambios, compare-and-swap Git, persistencia pura (events/snapshots) versus adaptadores Git/SQLite, permisos, runners aislados, recuperación y limitaciones de un admin con bypass.

## 8 — Interfaces y operación
CLI/API/UI/MCP sin lógica duplicada; perfiles de proyectos, agents opcionales, servicios por casos de uso, tests contractuales entre interfaces y prueba del procedimiento en dos proyectos realmente independientes.

## Resultado exigido por cada sesión
- ADR aprobada/propuesta/hold, no interpretación informal.
- Entradas y salidas de cada módulo.
- Invariantes y transiciones autorizadas.
- Dependencias permitidas y prohibidas.
- Consumers y rutas de origen.
- Tests positivos, mutaciones negativas y evidencias.
- Impacto sobre G-00…G-13 y mapeo de 142 rutas prospectivas.

Los módulos se crean solamente al implementar su primer consumidor; no se persigue materializar 142 archivos por obligación numérica.


## 9 — Cliente web y contratos de presentación
Concretar TypeScript, servidor API, modelo de caching por ProjectRevision y SupportProfile, representaciones muchos-a-muchos, grafos n-arios, permisos, accesibilidad, paginación y pruebas de paridad con CLI/MCP. No duplicar el evaluador normativo en la UI.
