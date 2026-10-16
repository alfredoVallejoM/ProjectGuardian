# 00 — Alcance integral, producto y requisitos

## Qué es
ProjectGuardian es **infraestructura de ingeniería contractual para proyectos**, independiente de cualquier proyecto que administre. Su objeto es conservar la relación entre (a) lo exigido, (b) lo implementado de verdad y (c) lo acreditado por evidencia; acompaña la totalidad del ciclo de vida del proyecto. No es un gestor de tareas, un framework de agentes, un sistema documental genérico ni un teorema prover universal.

Un proyecto se entiende como conjunto evolutivo de objetivos, capacidades, propiedades, obligaciones, decisiones, arquitectura, código, tests, consumidores, claims y evidencias, todos con procedencia, ámbito y versiones identificables. Las campañas organizan el desarrollo; los agentes son consumidores opcionales; ninguna de esas dimensiones monopoliza autoridad.

## Requisitos originales consolidados
El conjunto `PG-REQ-01…34` vive en `architecture/requirements.json` y se traza a las campañas. Las familias son:
- independencia entre Guardian y proyectos; generalidad para proyectos de software, ciencia e investigación; separación de fuentes entre Formal Core, Charloom y Reason Engine;
- constitución, contratos, objetivo, capacidad, propiedad y obligación con identidades separadas;
- evolución ilimitada de campañas y compromisos sin reescribir el motor, conservando historia, autorización, linajes y certificados anteriores acotados;
- grafo de relaciones tipadas y n-arias, propietarios, dependencias, soporte e impacto, además de universo de fuentes reconciliado;
- orientación global, por componente y tareas normativas compiladas para humanos/agentes con contexto incompleto;
- comprobación real de implementación, arquitectura, interfaces, consumidores, adversarios, pruebas e integración; separación escrita/ejecutada/cualificada;
- certificación honesta por claim, scope, perfil, revisión, universo y evidencia; reutilización selectiva por cono protegido;
- controles de seguridad que impidan modificar la constitución, autocertificarse o publicar por fuera de la autoridad confiable;
- modos humano, monoagente y multiagente, incluido perfil de cinco roles A0–A4 pero nunca obligatorio;
- explicabilidad, continuidad entre sesiones, interoperabilidad y autogobierno de la propia plataforma.

## Límites y exclusiones
- No afirma conocer todos los requisitos posibles ni fuentes no disponibles; cobertura completa siempre respecto de un `SourceUniverse` autenticado y explícito.
- No convierte una respuesta de IA, un documento, un test escrito, un commit SHA ni un receipt no autenticado en prueba matemática.
- No impone a proyectos las teorías de otros proyectos por similitud; las importaciones interproyecto requieren autorización registrada.
- No obliga a adoptar un único lenguaje, SDK, estructura de agente o protocolo de despliegue.
- No hay número fijo normativo de campañas, crates, módulos, agentes, tests ni líneas de archivo.
- No contiene automáticamente la matemática de cada dominio: los verificadores especializados acreditan sus garantías.
- No ejecuta cambios fuera del repositorio autorizado por el proyecto; no crea workflows GitHub Actions como requisito.

## Dimensiones inseparables del producto
**Contract Registry:** comprende visión, arquitectura, funcionalidades, propiedades y obligaciones.
**Evolution:** añade y modifica requisitos mediante `ChangeSet` versionados, no CRUD libre.
**Graph:** soporta relaciones con roles, dependencias conjunctivas/alternativas, `SupportCone` e `ImpactCone`.
**Repository Intelligence:** diferencia lo especificado de lo observado y reconoce límites de AST/features/macros/consumidores.
**Orientation & Task Compiler:** proporciona contextos humanos y encargos sin perder ninguna obligación obligatoria por resumir.
**Compliance & Assurance:** evalúa entregables, arquitectura, verificación, auditoría independiente según política y recibos acotados.
**Governance:** controla modificaciones, identidad, publicación y versiones del propio evaluador.
**Interfaces:** CLI/API/UI/protocolos para agentes sobre los mismos servicios de aplicación.

## Estados y terminación
`DEVELOPMENT_COMPLETE`: se ha implementado todo lo original exigible, incluidas pruebas, adversarios y verificadores; no exige ejecución material. `CAMPAIGN_CLOSED` añade ejecuciones, integración, recibos y cierre normativo. `QUALIFIED_IN_SCOPE` solo acredita claims en el perfil probado. `SOURCE_COVERAGE_PASS` nunca implica `SCIENTIFIC_PASS`.

## Condición de alcance
La especificación completa exige todas las familias anteriores. Ninguna campaña parcial o supuesto MVP puede retirar silenciosamente funcionalidades de la visión aprobada. Un despliegue por cortes incrementales es estrategia de implementación, no un recorte de obligaciones.

