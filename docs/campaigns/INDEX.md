# Programa G-00…G-13 — dosieres normativos propuestos

**14 campañas; 163 obligaciones detalladas. Ninguna campaña está íntegramente cerrada; hay código productivo de G00-B01/B02, sin completar todavía G-00.**

| Campaña | Objetivo | Obligaciones | Dependencias |
|---|---|---:|---|
| [G-00](G-00.md) | Fundamentos, ProjectContract y autoridad | 12 | — |
| [G-01](G-01.md) | Evolución continua de obligaciones y campañas | 12 | G-00 |
| [G-02](G-02.md) | Grafo de relaciones, soporte e impacto | 12 | G-00, G-01 |
| [G-03](G-03.md) | Project Orientation y recuperación de conocimiento | 10 | G-02 |
| [G-04](G-04.md) | Compilador de tareas y planificación contractual | 12 | G-01, G-02 |
| [G-05](G-05.md) | Conformidad arquitectónica y funcional | 12 | G-02, G-07 |
| [G-06](G-06.md) | Auditoría, evidencia, estados y certificación | 12 | G-01, G-05 |
| [G-07](G-07.md) | Adaptadores de proyectos, código y herramientas | 12 | G-02 |
| [G-08](G-08.md) | Interacción humana, monoagente y multiagente | 11 | G-04, G-07, G-09, G-11 |
| [G-09](G-09.md) | Gatekeeper, permisos y seguridad | 12 | G-01, G-06 |
| [G-10](G-10.md) | Cobertura integral, preservación y migraciones | 12 | G-02, G-05, G-06, G-07 |
| [G-11](G-11.md) | CLI, API, MCP e interfaz gráfica | 12 | G-03, G-04, G-09 |
| [G-12](G-12.md) | Fiabilidad, escala y operación | 10 | G-01, G-02, G-09 |
| [G-13](G-13.md) | Pilotos científicos y cualificación integral | 12 | G-08, G-10, G-11, G-12 |

## Contrato común de cierre
**Development complete** exige toda implementación, tests, adversarios y verificadores desarrollados. **Campaign closed** exige además auditoría, runs, integración, recursos y receipts reales. Las filas del registro original permanecen en SPECIFIED_NOT_IMPLEMENTED por ausencia de cierres de las obligaciones padres; hay desarrollo parcial real de B01/B02, documentado aparte. Los 34 requisitos y 30 ADR se relacionan mediante los registros architecture/; cambios semánticos por ChangeSet ratificado.

**G-00 en detalle:** [especificación completa de fundamentos, operaciones, tests y decisiones](G-00/INDEX.md) — 12 obligaciones originales desarrolladas en 120 cláusulas subordinadas, pendientes de ratificación e implementación.

## Extensiones CCRR propuestas

[Índice de las 14 extensiones por campaña](CCRR_EXTENSION_INDEX.md). Conservan los 163 IDs originales con falsaciones y puentes nuevos candidatos. No son nuevas campañas ni demostraciones de suficiencia ratificadas.

## Implementación productiva progresiva (20-10-2026)

El [protocolo de ejecución G-00…G-13](G00_G13_PROGRESSIVE_PRODUCT_IMPLEMENTATION.md) fija autoría, pruebas, adversarios, integración, revisión independiente y los dos estados separados DEVELOPMENT_COMPLETE / CAMPAIGN_CLOSED. No altera la autoridad de las 163 obligaciones.

El [ledger inicial de las 163 obligaciones](../../architecture/implementation_progress_2026_10_20.json) enumera cada ID canónico, y para G-00 sus cláusulas, APIs, pruebas, adversarios e integraciones esperadas. Es una proyección de seguimiento, **no** una fuente de autoridad ni un certificado. Es una instantánea histórica del 20-10-2026: no contabiliza los bloques implementados y publicados posteriormente.

## Estado de la primera implementación productiva (21-10-2026)

[Desarrollo G00-B01 y GSL0-LC00…LC02](../implementation/G00_B01_GSL0_LC00_LC02.md) · [matriz de progreso por cláusula y adversario](../implementation/G00_B01_GSL0_LC00_LC02_PROGRESS.json). Las 104 pruebas ejecutadas localmente y el code-cut remoto están separados de ratificación, auditoría independiente y cierre material de campaña.

## Segundo corte integrado — 21-10-2026

[Desarrollo G00-B02 y GSL0-LC03](../implementation/G00_B02_GSL0_LC03.md) · [20 cláusulas G00-02/03, 10 APIs y seis adversarios trazados](../implementation/G00_B02_GSL0_LC03_PROGRESS.json). Frontend textual ANALYZED, no COMPILADO; suites locales 206 PASS sin cierre de campaña.
