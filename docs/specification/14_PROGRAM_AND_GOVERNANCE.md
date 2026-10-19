# 14 — Programa G-00…G-13, orden, cierres y gobierno

## La totalidad del programa
14 campañas y 163 obligaciones propuestas y trazadas en `architecture/campaigns.json`. Programas previos `ENG-00…ENG-10` conservan crosswalk de responsabilidades; nunca se reescriben silenciosamente como si no hubiesen existido.
G-00 dominio/autoridad; G-01 evolución; G-02 grafo; G-03 orientación; G-04 paquetes; G-05 conformidad; G-06 auditoría/evidencia; G-07 adaptadores; G-08 agentes; G-09 Gatekeeper; G-10 cobertura/migración; G-11 interfaces; G-12 fiabilidad; G-13 pilotos/cualificación.

## Dependencias normativas
G00→G01/G02; G01→G02/G04/G06/G09/G12; G02→G03/G04/G05/G07/G10/G12; G07→G05/G08/G10; G05→G06/G10; G06→G09/G10; G09→G08/G11/G12; G03/G04→G11; G04/G11→G08; G08/G10/G11/G12→G13. Estas son dependencias **de admisión de cierre**, no prohibición de escribir prototipos en paralelo.

## Campaña no equivale a tarea
Cada campaña tiene scope, exclusions, deps, owner, implementation obligations, planned source modules, tests, adversarios, integration and resources, DefinitionOfDevelopmentComplete y DefinitionOfCampaignClosed. El detalle por obligación se encuentra en los 14 dossiers generados desde el catálogo normativo propuesto.

## Estados
`DEVELOPMENT_COMPLETE` solo cuando **todas las obligaciones originales** de implementación + pruebas/verificadores/adversarios correspondientes están implementadas, sin que haga falta ejecutar todo el programa material. `CAMPAIGN_CLOSED` añade ejecución comprobada, integración, recursos y receipts. `GUARDIAN_PLATFORM_QUALIFIED` exige además pilotos E2E en perfiles. No confundir SPECIFICATION_DEFINED, IMPLEMENTED, RUN_PASS ni CERTIFIED.

## Modelo de responsabilidad
Un módulo con owner primario, API, invariantes, consumers, test targets, schema/records. Ninguna carpeta vacía como testigo de implementación. No doble autoridad editable. Cada acción fuera de la tabla original se vincula mediante ChangeSet, no por recreación de planes narrativos.

## Quality gates de especificación
PG-SPEC-01…12: requisitos registrados, trazados a campañas y obligaciones; campañas y obligaciones con aceptación/falsación; módulos con owner; DAG válido; evolución conservadora; levels de evidencia separados; seguridad previene self-admission; pruebas E2E cubren claims; extensión de schemas fail-closed. Estos gates son especificados, no ejecutados.

## Policy de avances
Un agente no se declara DONE cuando existen gaps exigibles. A3 entra después de implementación completa del bloque; A4 verifica integraciones y ejecuciones reales. Adaptadores/SDKs no ejercen autoridad normativa. Programmatic crosswalk REQUIREMENT→CAMPAIGN→OBLIGATION→MODULE→TEST→EVIDENCE. Informes de progreso muestran gaps, UNKNOWN, FUTURE y RESEARCH por separado.


## Suplemento propuesto: CCRR y SH (19-10-2026)

Las 14 campañas/163 obligaciones originales permanecen como programa funcional; SH-00…SH-12 son cortes transversales de ensayo y NO campañas adicionales. [Extensiones por campaña](../campaigns/CCRR_EXTENSION_INDEX.md). Un enlace de trazabilidad no prueba suficiencia de refinamiento; requieren puentes, hipótesis y PO independientes. [Orden y frontera de confianza](../revision-2026-10-19/04_ENGINEERING_CAMPAIGN_OWNERSHIP_AND_SEQUENCE.md). Ninguna ADR queda ratificada mediante este texto y GSL-0 aún no tiene contrato diseñado.
