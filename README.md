# ProjectGuardian

**Infraestructura independiente para custodiar las obligaciones, la arquitectura y las garantías de proyectos a lo largo de su desarrollo.**

Guardian preserva lo que se **exigió**, distingue lo que se **implementó realmente** y verifica qué se **acreditó** mediante fuentes y evidencias por ámbito. Opera con personas, cero/uno/varios agentes y distintos lenguajes y repositorios. La coordinación multiagente es una aplicación opcional; el guardián del contrato del proyecto es el producto central.

## Estado real
**ESPECIFICACIÓN GENERAL PROPUESTA · G00-B01/B02 Y GSL0-LC00…LC03 COMO CANDIDATO REMEDIADO · 226 PRUEBAS LOCALES PASS · SIN CERTIFICACIÓN MATERIAL NI AUDITORÍA INDEPENDIENTE.**
La documentación se ha normalizado desde la conversación de diseño; no constituye una transcripción literal ni un cierre de la fuente histórica. No se han ratificado formalmente las ADR. Se ha iniciado la implementación productiva de los bloques fundacionales; ninguna campaña G-00…G-13 está cerrada.

## Qué está registrado
- [Índice integral de documentación](docs/README.md): 16 capítulos de especificación sobre alcance, constitución, tipos, grafo, evolución, repositorios, orientación, encargos, conformidad, pruebas, migraciones, seguridad, persistencia, ingeniería, interfaces y campañas.
- [Requisitos globales](architecture/requirements.json): 34 exigencias acumuladas, en propuesta.
- [Decisiones de arquitectura](architecture/decisions.json) y [dosieres ADR](docs/decisions/INDEX.md): 30 propuestas sin ratificar.
- [Programa de campañas](architecture/campaigns.json) y [dosieres G-00…13](docs/campaigns/INDEX.md): 14 campañas y 163 obligaciones, con aceptación, falsación y perfil de verificación.
- [Mapa prospectivo de módulos](architecture/module_blueprint.json): 142 ubicaciones de diseño previstas, propietarios, responsabilidades y tests esperados; el primer conjunto de módulos reales ya existe en `src/guardian/`.
- [Arquitectura y distribución](docs/architecture/INDEX.md): límites, dependencias, responsabilidades de archivos e [interfaz gráfica](docs/architecture/08_WEB_CLIENT.md) por debatir.
- [Trazabilidad](architecture/traceability.json): enlaces requisitos/campañas/obligaciones, con [163 asignaciones de implementación propuestas](docs/traceability/OBLIGATION_IMPLEMENTATION_MATRIX.md); la trazabilidad global hasta el código sigue abierta; el primer corte tiene su propia matriz de progreso y pruebas.
- [Banco adversario](docs/assurance/NEGATIVE_TEST_BANK.md): 24 ataques transversales definidos para convertirse en tests, aún sin ejecución.
- [Estado explícito](architecture/status.json).
- [Auditoría documental de la publicación](docs/assurance/DESIGN_PUBLICATION_AUDIT.md): lectura remota, integridad de enlaces y ausencia explícita de implementación.

## Principios vinculantes del diseño propuesto
No borrar ni rebajar obligaciones; ninguna prueba escrita implica ejecución; no certificados científicos por evidencia documental; ningún agente autocertifica sus entregas; cada proyecto mantiene su autoridad; nuevos requisitos/campañas se añaden sin modificar el núcleo; los paquetes de trabajo no reducen el cierre normativo por límites de contexto; los cambios impactan solo conos protegidos cuando es demostrable.

## Próxima deliberación
Continuar G00-B03/B06 y GSL0-LC04…LC08, aprovechando los dos cortes fundacionales publicados. Resolver las decisiones de autoridad pendientes sin confundir implementación con ratificación, y mantener la auditoría adversaria independiente antes de admitir cierres.

## Contorno técnico
Python 3.12+ tipado, monolito modular, domain inmutable + functional core/imperative shell, puertos y adaptadores; Git como autoridad, SQLite como índice derivado, verificadores externos por ámbito, CLI/API/UI/MCP y agent SDK optativos. Sin microservicios por defecto ni hard cap de LOC.

## Campaña fundacional desarrollada en detalle
La [especificación completa de G-00](docs/campaigns/G-00/INDEX.md) documenta identidad, proyectos, fuentes, ontología de obligaciones, scope, constitución, referencias, schemas, evaluador, APIs, falsaciones y criterios de cierre. Los números del dosier son compromisos de diseño: **no reflejan por sí solos código ni pruebas**. Ver la primera implementación productiva y su estado separado.

## Revisión de octubre 2026

[Corrección propuesta CCRR y campañas](docs/revision-2026-10-19/INDEX.md). GSL-0 completo y su ratificación siguen pendientes; LC00…LC02 tienen ya código productivo acotado.

## Primer corte productivo — 21-10-2026

- [Código y validación: G00-B01 + GSL0-LC00…LC02](docs/implementation/G00_B01_GSL0_LC00_LC02.md).
- [Ledger acotado por bloque, sin falsos cierres](docs/implementation/G00_B01_GSL0_LC00_LC02_PROGRESS.json).
- Pruebas ejecutadas localmente: **104 PASS / 0 SKIP**, Python 3.13.5; [commit de código publicado](https://github.com/alfredoVallejoM/ProjectGuardian/commit/8a17518fc45d5a9623698349e358e9b06ed79cad), blobs exactos verificados con el candidato. No se atribuye certificación fuerte ni se afirma que el compilador total esté desarrollado.

- [Argumento de preservación V4](docs/verification/GSL0_LC02_V4_PRESERVATION.md) y [readback exacto de los módulos/product tests](docs/implementation/G00_B01_GSL0_LC00_LC02_LOCAL_READBACK.md).

## Segundo corte productivo — 21-10-2026

- [G00-B02 + GSL0-LC03: implementación real e integración](docs/implementation/G00_B02_GSL0_LC03.md).
- [Matriz específica de cláusulas, adversarios, APIs y controles](docs/implementation/G00_B02_GSL0_LC03_PROGRESS.json).
- [Preservación textual](docs/verification/GSL0_LC03_LOSSLESS_PRESERVATION.md) y [autorrevisión adversaria, no auditoría independiente](docs/audit/G00_B02_GSL0_LC03_SELF_REVIEW.md).
- Suite local del corte: **206 PASS / 0 SKIP**; los límites de compilación, ratificación y certificación material siguen explícitos.

## Auditoría adversaria y remediación — 21-10-2026

- [Acta de revisión adversaria del código fundacional](docs/audit/2026_10_21_FOUNDATION_ADVERSARIAL_REVIEW.md): once defectos reproducidos y corregidos en el candidato (fuentes, imports, autoridad, procedencia V4, estados, límites de recursos).
- [Matriz de obligaciones y falsaciones](docs/audit/2026_10_21_FOUNDATION_OBLIGATION_MATRIX.json): 30 cláusulas G00-01/02/03 enlazadas a pruebas directas; 163 obligaciones canónicas preservadas.
- Código remediado en [commit `ac13444b`](https://github.com/alfredoVallejoM/ProjectGuardian/commit/ac13444b62219beeb53570fc81ce7220832dacb4); **226/226 PASS localmente, sin SKIP**, y 18/18 objetos Git comprobados. Sin run independiente sobre SHA remoto ni recibo firmado.
