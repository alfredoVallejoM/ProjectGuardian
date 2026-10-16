# ProjectGuardian

**Infraestructura independiente para custodiar las obligaciones, la arquitectura y las garantías de proyectos a lo largo de su desarrollo.**

Guardian preserva lo que se **exigió**, distingue lo que se **implementó realmente** y verifica qué se **acreditó** mediante fuentes y evidencias por ámbito. Opera con personas, cero/uno/varios agentes y distintos lenguajes y repositorios. La coordinación multiagente es una aplicación opcional; el guardián del contrato del proyecto es el producto central.

## Estado real
**DESIGN SPECIFICATION PROPOSED · CODE NOT IMPLEMENTED · TESTS NOT RUN · NOT CERTIFIED.**
La documentación se ha normalizado desde la conversación de diseño; no constituye una transcripción literal ni un cierre de la fuente histórica. No se han ratificado formalmente aún las ADR ni iniciado campañas de implementación.

## Qué está registrado
- [Índice integral de documentación](docs/README.md): 16 capítulos de especificación sobre alcance, constitución, tipos, grafo, evolución, repositorios, orientación, encargos, conformidad, pruebas, migraciones, seguridad, persistencia, ingeniería, interfaces y campañas.
- [Requisitos globales](architecture/requirements.json): 34 exigencias acumuladas, en propuesta.
- [Decisiones de arquitectura](architecture/decisions.json) y [dosieres ADR](docs/decisions/INDEX.md): 30 propuestas sin ratificar.
- [Programa de campañas](architecture/campaigns.json) y [dosieres G-00…13](docs/campaigns/INDEX.md): 14 campañas y 163 obligaciones, con aceptación, falsación y perfil de verificación.
- [Mapa prospectivo de módulos](architecture/module_blueprint.json): 142 ubicaciones de diseño previstas, propietarios, responsabilidades y tests esperados; sin archivos de código creados.
- [Arquitectura y distribución](docs/architecture/INDEX.md): límites, dependencias, responsabilidades de archivos e [interfaz gráfica](docs/architecture/08_WEB_CLIENT.md) por debatir.
- [Trazabilidad](architecture/traceability.json): enlaces requisitos/campañas/obligaciones, con [163 asignaciones de implementación propuestas](docs/traceability/OBLIGATION_IMPLEMENTATION_MATRIX.md); los enlaces a código efectivo y evidencias siguen pendientes.
- [Banco adversario](docs/assurance/NEGATIVE_TEST_BANK.md): 24 ataques transversales definidos para convertirse en tests, aún sin ejecución.
- [Estado explícito](architecture/status.json).
- [Auditoría documental de la publicación](docs/assurance/DESIGN_PUBLICATION_AUDIT.md): lectura remota, integridad de enlaces y ausencia explícita de implementación.

## Principios vinculantes del diseño propuesto
No borrar ni rebajar obligaciones; ninguna prueba escrita implica ejecución; no certificados científicos por evidencia documental; ningún agente autocertifica sus entregas; cada proyecto mantiene su autoridad; nuevos requisitos/campañas se añaden sin modificar el núcleo; los paquetes de trabajo no reducen el cierre normativo por límites de contexto; los cambios impactan solo conos protegidos cuando es demostrable.

## Próxima deliberación
Leer [decisiones de ubicación y patrones](docs/architecture/04_CONCRETE_DESIGN_DISCUSSION.md) y [mapa completo de archivos](docs/architecture/03_MODULE_BLUEPRINT.md). Concretar interfaces de cada agregado y subsistema; registrar cambios mediante decisión versionada antes de generar código. No crear scaffolds ni iniciar campañas de forma implícita.

## Contorno técnico
Python 3.12+ tipado, monolito modular, domain inmutable + functional core/imperative shell, puertos y adaptadores; Git como autoridad, SQLite como índice derivado, verificadores externos por ámbito, CLI/API/UI/MCP y agent SDK optativos. Sin microservicios por defecto ni hard cap de LOC.

## Campaña fundacional desarrollada en detalle
La [especificación completa de G-00](docs/campaigns/G-00/INDEX.md) documenta identidad, proyectos, fuentes, ontología de obligaciones, scope, constitución, referencias, schemas, evaluador, APIs, falsaciones y criterios de cierre. Los números son compromisos de diseño y **no reflejan tests o código desarrollados**.
