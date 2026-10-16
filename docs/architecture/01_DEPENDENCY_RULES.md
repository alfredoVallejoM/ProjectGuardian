# Fronteras y dependencias del monolito modular

## Regla principal
`domain` solo stdlib + tipado estructural. `constitution`, `graph` y `program` pueden depender de domain y contratos puros; nunca de Git, SQLite, API, red, SDKs ni runners. `knowledge` recibe ObservedInventory del puerto; `work` recibe proyecciones y contratos; `assurance` evalúa evidencia sin ejecutar código dentro del dominio. `governance` usa `ProtectedPolicy` externa al worktree candidato. `application` compone casos de uso, `adapters` implementan puertos, `interfaces` presentan resultados.

## Matriz de responsabilidades
- Domain: tipos/identidades/validaciones locales. No consultar fuentes.
- Constitution: aplicación de decisiones, cambios y autoridad. No otorgar pruebas científicas.
- Graph: relaciones tipadas/proyecciones/cierres. No tratar aristas no ratificadas como soporte.
- Program: versionado/refinamiento/supersession. No material tests.
- Knowledge: source code inventory y source-intent-observed crosswalk. No auto-certificación.
- Work: orient, context select, package compile, decompositions. No editar obligaciones.
- Assurance: VerificationSpec, Run, Claims, auditing and qualification. No self-emitted execution.
- Governance: permissions, gatekeeper, publication CAS. No decidir teoremas.
- Ports/Adapters: acceso a herramientas, nunca autoridad normativa por sí solos.
- UI/MCP/CLI: todos llaman a application y ningún acceso de escritura directo a storage normativo.

## Dependencias de cierre entre campañas
G00→G01,G02; G01→G02,G04,G06,G09,G12; G02→G03,G04,G05,G07,G10,G12; G07→G05,G08,G10; G05→G06,G10; G06→G09,G10; G09→G08,G11,G12; G03,G04→G11; G04,G11→G08; G08,G10,G11,G12→G13.

## Arquitectura extensible
El núcleo de perfiles usa `ObligationProfile`, `VerificationRunner`, `SourceAnalyzer`, `AttestationVerifier` puertos con IDs/versiones; una obligación/campaña nueva cambia registros, no código. Un tipo normativo totalmente nuevo requiere versión de contrato y evaluación de compatibilidad, no un `if project == ...`.

## Diseño a debate
Ámbito del agregado Project Contract versus división de entidades y event log; si `SupportProfile` es propiedad del dominio o de assurance (propuesta: dominio); API del motor de reglas de aplicabilidad; ubicación del módulo de WorkPackage; criterios de independencia de auditor.

