# Programa G-00…G-13 — dosieres normativos propuestos

**14 campañas; 163 obligaciones detalladas, ninguna implementada, ejecutada ni certificada.**

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
**Development complete** exige toda implementación, tests, adversarios y verificadores desarrollados. **Campaign closed** exige además auditoría, runs, integración, recursos y receipts reales. Todas las filas están SPECIFIED_NOT_IMPLEMENTED. Los 34 requisitos y 30 ADR se relacionan mediante los registros architecture/; cambios semánticos por ChangeSet ratificado.

**G-00 en detalle:** [especificación completa de fundamentos, operaciones, tests y decisiones](G-00/INDEX.md) — 12 obligaciones originales desarrolladas en 120 cláusulas subordinadas, pendientes de ratificación e implementación.
