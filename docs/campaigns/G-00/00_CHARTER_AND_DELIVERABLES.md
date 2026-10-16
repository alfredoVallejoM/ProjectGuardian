# G-00 — Carta de funcionamiento, fronteras y entregables

**Estado:** DESIGN_REFINEMENT_PROPOSED; no hay implementación ni ejecución. **Autoridad original preservada:** \`architecture/campaigns.json\` → \`G-00\`, obligaciones \`G00-01…G00-12\`. Este documento es una especialización funcional de esas doce obligaciones, no un cambio de numeración ni una autorización de recortar el programa global.

## Propósito de G-00

Crear el **lenguaje interno de dominio y el evaluador constitucional puro** sobre el cual todos los subsistemas posteriores pueden razonar acerca de qué es un proyecto, qué fuentes le pertenecen, qué identidades se preservan, qué obligaciones son compromisos, cómo se aplican reglas y cuándo falta conocimiento.

G-00 es completo a nivel de sus obligaciones solo si proporciona modelos utilizables, validadores y operaciones con resultados precisos, pruebas de comportamiento y adversarios escritos. No se admite cerrar G-00 porque existan 19 archivos de origen, structs/datatypes sueltos, una schema superficial o una demo sin contratos.

## Funcionalidades completas dentro del ámbito

1. **Identidades normativas (G00-01):** IDs tipados, estables y separados de ruta, alias, revisión y digest, con validación, serialización y detección de colisiones.
2. **Aislamiento de proyectos (G00-02):** identidad, owner de fuentes, configuración de modo EMBEDDED/SIDECAR/FEDERATED como **política declarativa**, importaciones explícitas entre universos sin conferir autoridad.
3. **SourceUniverse (G00-03):** fuentes inmutables identificadas, inclusiones/exclusiones verificables, estado de adquisición distinto del de cobertura, diagnóstico de carencias y ámbito de cualquier afirmación de completitud.
4. **Constitución/decisiones (G00-04):** declaración de normas, jerarquía tipada, estado PROPOSED distinto de RATIFIED, emisión de conflictos y validación estructural de approvals **sin autenticar credenciales externas** (responsabilidad posterior del Gatekeeper).
5. **Ontología de compromisos (G00-05):** Objective, Capability, Property, Obligation y referencias a Architecture/Implementation/Verification separadas, con invariantes de campo, cardinalidad y autoridad.
6. **Applicability/SupportProfile (G00-06):** perfiles tipados, predicados de alcance, lógica YES/NO/UNKNOWN/CONFLICT, explicaciones por testigo y presupuestos de evaluación.
7. **Estados ortogonales (G00-07):** tipos distintos para fuente, compromiso, desarrollo, auditoría, material, soporte, cualificación y migración; nunca bool \`complete\` como autoridad.
8. **Integridad de referencias (G00-08):** resolución bajo snapshot de proyecto, namespace y revisión fijada, comprobación de tipo y pertenencia, prohibición de referencias interproyecto implícitas.
9. **Esquemas versionados (G00-09):** validación de forma y requisitos normativos soportados, compatibilidad de lectura conservadora y rechazo de características desconocidas; no se exige todavía el store Git/SQLite completo.
10. **Evaluación constitucional pura (G00-10):** evaluador total sobre el subconjunto admitido, resultados y diagnósticos reproducibles, dependencias tipadas, sin reloj/red/fs, cobertura de reglas y evaluación no confiada a un modelo.
11. **Conflictos de autoridad (G00-11):** desacuerdos con testigos, ámbitos y bloqueo localizado, sin elección automática por fecha.
12. **Pruebas fundamentales (G00-12):** tests unitarios/propiedades/negativos/mutaciones/integración en memoria, por contratos, que falsen explícitamente las once familias anteriores.

## Qué NO debe implementarse por sustitución de responsabilidades

| No pertenece al cierre productivo de G-00 | Campaña responsable y frontera |
|---|---|
| Escritura, versionado causal y aplicación de ChangeSet a un store Git real | G-01, G-12 |
| Closure de grafo complejo, proyección many-to-many, SupportCone e ImpactCone | G-02 |
| ProjectOrientation completo y texto recuperado de corpus | G-03 |
| Compilación de paquetes de trabajo y scheduling | G-04 |
| Analizador real de código y conformidad funcional | G-05, G-07 |
| Emisión/autenticación material de receipts, certificación matemática | G-06, G-10 |
| Verificación de claves, identidad externa, publicación Git protegida | G-09 |
| MCP, SDKs de agentes, API/UI final | G-08, G-11 |
| Crash-recovery, persistencia de eventos y schema migrator completo | G-01, G-12 |
| Cualquier pretensión de completitud de todas las fuentes de proyectos | G-07, G-10, con universos delimitados |

**Regla de interfaz futura:** G-00 sí debe definir los tipos y contratos que esos consumidores necesitarán. Un contrato de G-00 puede quedar listo para ser consumido sin exigir la implementación del consumidor posterior. Los límites se documentan como interfaces, no como funcionalidades pendientes de G-00.

## Entradas, salidas y ciclo funcional en memoria

Entrada: \`ProjectDefinition\` + \`ProjectContext\` (source refs, ConstitutionRevision, catálogo acotado de entidades y tipos, SupportProfile, hechos/candidatos), todos pasados explícitamente. No hay carga implícita de GitHub o LLM.

Operaciones:
1. Normalizar/validar tipos y namespaces.
2. Validar fuente y scopes sin afirmar que ya se haya leído su contenido.
3. Construir \`ReadOnlyProjectView\` con referencias por revisión.
4. Comprobar integridad referencial y conflictos.
5. Resolver applicability para reglas con predicados de dominio admitidos.
6. Evaluar las reglas constitucionales puras.
7. Emitir \`DomainValidationReport\` y \`ConstitutionEvaluationReport\` con rule refs, causas, testigos, incertidumbres y límites.

Salida: objetos de resultado **sin autoridad de publicación ni certificación**. El adaptador futuro podrá convertir estos resultados en eventos después de sus propias comprobaciones de permiso y evidencia.

## Definición formal de terminación

\`G00_DEVELOPMENT_COMPLETE\`:
- Todos los contratos funcionales detallados para G00-01…12 implementados.
- Todos los validadores funcionales, errores tipados, invariantes y operaciones de G-00 desarrollados.
- Todas las pruebas directas, propiedades y casos adversarios exigidos están escritos y enlazados a cada cláusula.
- No queda una función \`NotImplemented\`, un \`pass\`, un fallback silencioso o dependencia temporal que reduzca una obligación de G-00.
- El contrato con G-01/G-02/G-03/G-04/G-09 es explícito, sin exigir su implementación prematura.

\`G00_CAMPAIGN_CLOSED\` añade: ejecutar suite real sobre candidato exacto, auditoría independiente según política, recibo real, validación de interfaces y dependencias y aceptación de los ámbitos de prueba especificados. No dar por cerrado con \`DESIGN_VALID\` ni con pruebas aún no ejecutadas.

## Dos niveles de autoridad documental

El manifiesto inicial de doce obligaciones no se reescribe. \`architecture/g00_functional_refinement.json\` será un registro de **cláusulas subordinadas** \`G00-XX-FYY\`: refinan el comportamiento exigido, no son nuevas campañas y no convierten por sí mismas 163 obligaciones históricas en 283. Deben ratificarse antes de actuar como condiciones de admisión. Si una cláusula introduce un compromiso realmente nuevo no derivable de su padre, deberá tramitarse \`AddObligation\`/decisión de alcance, no introducirse como "aclaración".
