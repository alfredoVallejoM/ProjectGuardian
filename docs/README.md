# Índice de especificación — ProjectGuardian

**Estado de autoridad:** PROJECT_SPECIFICATION_PROPOSED. La publicación fija una propuesta versionada para deliberación; no significa ratificación de ADR, implementación, ejecución de tests o certificación. El conjunto normativo completo requiere resolución y aprobación expresa de decisiones.

## Documentos fundamentales
- [00 — Alcance integral y requisitos](specification/00_SCOPE_AND_REQUIREMENTS.md)
- [01 — Constitución y autoridad](specification/01_CONSTITUTION_AND_AUTHORITY.md)
- [02 — Ontología, tipos y estados](specification/02_DOMAIN_AND_STATE_MODEL.md)
- [03 — Grafo, dependencias y soporte](specification/03_TYPED_GRAPH_AND_SUPPORT.md)
- [04 — Evolución abierta de contratos](specification/04_EVOLUTION_AND_CAMPAIGNS.md)
- [05 — Arquitectura especificada y código observado](specification/05_REPOSITORY_INTELLIGENCE.md)
- [06 — Project Orientation y compilación de tareas](specification/06_ORIENTATION_AND_WORK_PACKAGES.md)
- [07 — Cumplimiento, auditoría y certificación](specification/07_COMPLIANCE_AUDIT_ASSURANCE.md)
- [08 — Migraciones y preservación histórica](specification/08_MIGRATION_AND_REUSE.md)
- [09 — Gatekeeper y perímetros de confianza](specification/09_SECURITY_AND_GATEKEEPER.md)
- [10 — Persistencia, concurrencia y recuperación](specification/10_STORAGE_AND_HISTORY.md)
- [11 — Software, patrones, puertos y adaptadores](specification/11_ENGINEERING_ARCHITECTURE.md)
- [12 — Interfaces humanas, monoagente y multiagente](specification/12_INTERFACES_AND_AGENTS.md)
- [13 — Validación y pruebas adversarias](specification/13_QUALITY_AND_ACCEPTANCE.md)
- [14 — Plan completo y política de cierre](specification/14_PROGRAM_AND_GOVERNANCE.md)
- [15 — Modelo de autoridad de la documentación](specification/15_RATIFICATION_AND_SOURCE_POLICY.md)

## Autoridades de planificación
- `architecture/requirements.json`: 34 requisitos globales con trazabilidad.
- `architecture/decisions.json`: 30 decisiones arquitectónicas propuestas.
- `architecture/campaigns.json`: G-00…G-13 y 163 obligaciones de implementación propuestas, con criterios y falsaciones.
- `architecture/module_blueprint.json`: asignación de responsabilidades y rutas previstas de software.
- `architecture/status.json`: separación diseño/implementación/cualificación.
- `docs/campaigns/`: dosier de cada campaña, matriz de cierre.
- `docs/architecture/`: fronteras, dependencias y mapa de archivos.
- `docs/assurance/`: banco de falsaciones y pruebas cruzadas.
- `docs/decisions/`: fichas por ADR y enmiendas futuras.

**No hay código productivo ni evidencia material aún.** Los esquemas y rutas futuras se describen como diseños, nunca como archivos implementados. Las poblaciones de requisitos/obligaciones son propuestas revisables mediante un procedimiento de cambio versionado.

## Principio de permanencia
Una precisión posterior no sustituye el alcance anterior, salvo operación explícita `SUPERSEDE` con justificación, autoridad, correspondencia histórica y análisis de impacto. El proyecto no exige cinco agentes: opera con humanos, cero/uno/varios agentes. El grafo, el programa y la auditoría se subordinan al contrato íntegro del proyecto, no al último resumen narrativo.


## Desarrollo y revisión arquitectónica concreta
- [142 rutas de módulos y tests previstos](architecture/03_MODULE_BLUEPRINT.md), sin obligación de generarlas todas.
- [Matriz por las 163 obligaciones](traceability/OBLIGATION_IMPLEMENTATION_MATRIX.md), propuesta de asignación por módulo y test.
- [Entidades y servicios](architecture/06_DOMAIN_INTERFACES.md).
- [Interfaz gráfica independiente](architecture/08_WEB_CLIENT.md), cliente TypeScript propuesto, no ratificado.
- [Secuencia de discusión de arquitectura](architecture/07_ARCHITECTURE_REVIEW_SEQUENCE.md).

## Publicación y coherencia
- [Auditoría estática de la publicación](../docs/assurance/DESIGN_PUBLICATION_AUDIT.md): cotejo documental y límites de la evidencia.

### Profundización de la campaña fundacional
- [G-00 completa](campaigns/G-00/INDEX.md): modelos, interfaces, 120 cláusulas de comportamiento, 58 operaciones, 36 adversarios, 7 verticales y diez cortes de desarrollo. **Diseño sin implementación.**
- [Revisión documental estática de G-00](campaigns/G-00/17_DOCUMENTARY_AUDIT.md): integridad referencial comprobada, sin implementación material.

## Revisión CCRR 19-10-2026

[Informe de corrección y ampliación](revision-2026-10-19/INDEX.md) · [Extensiones G-00…G-13](campaigns/CCRR_EXTENSION_INDEX.md). Registros propuestos en architecture/ccrr_*.json. Sin código ni validación material nueva; GSL-0 pendiente.
