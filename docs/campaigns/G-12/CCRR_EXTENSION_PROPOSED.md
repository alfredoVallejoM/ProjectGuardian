# G-12 — Extensión contractual CCRR y pruebas de autoverificación

**Estado: PROPUESTA DOCUMENTAL, no norma ratificada, código ni evidencia material.** Preservar 10 obligaciones canónicas de architecture/campaigns.json.

Objetivo: Persistencia reconstruible, recovery, concurrencia, rendimiento y compatibilidad de schema.. Exclusión: No ejecutar microservicios u ORM solo por complejidad aparente.. Dependencias de cierre: G-01, G-02, G-09. Contratos INT-06/08. Hito SH-11.

## Cláusulas originales y nuevos puentes de garantía

| ID original | Desarrollo fuente | Justificación/realización específica que se añade como candidata | Falsación histórica |
|---|---|---|---|
| G12-01 | Proyección SQLite reconstructible desde authority vigente | SQLite reconstruible desde Git | Perdida SQLite destruye norma |
| G12-02 | Detener cada fase publication y reconstruir sin partial authority | Crash no produce estado híbrido | Crash produce revisión parcial |
| G12-03 | Replays/retries no duplican eventos ni obligations | Idempotencia de reintentos | Reintento AddCampaign duplica |
| G12-04 | Consultas/impact graph escalan por subgrafo y revision | Cálculo incremental igual a full | Cada consulta reparsea corpus completo |
| G12-05 | Time/memory/input cardinality/config de analyzer y runner, resultados RESOURCE_LIMITED | RESOURCE_LIMITED no PASS | Analysis timeout afirma coverage completa |
| G12-06 | Migration readers fail closed por normative features desconocidos | Schema features desconocidas rechazan | Old reader ignora nueva regla obligatoria |
| G12-07 | Trazas de decisiones de admisión/verificador/candidate sin secretos | Logs explican decisiones sin secretos | No puede explicarse por qué se admitió |
| G12-08 | Conflictos por revisión expected y read/write protected sets | CAS concurrencia y read sets | Se pierde actualización simultánea |
| G12-09 | Install separada de candidate editable, configuración documentada | Policy fuera de worktree editable | Agente cambia Gatekeeper instalado |
| G12-10 | Benchmarks repetibles con ambiente, corpus y recursos reales | Benchmark con workload y entorno | Se declara throughput sin medición |

## Contrato raíz y conexiones

G es el objetivo completo; D son las subobligaciones; J las integraciones; A los supuestos. Exigir PO para (A∧D∧J⇒G), factibilidad y realización concreta, sin conteos sustitutivos. Los contratos INT-06/08 deben probarse end-to-end con dueño y consumidores especificados. No promover soporte parcial a prueba científica, integración universal o seguridad del host.

## Adversarios y selfhost

Tras crash SQLite discrepa del canon; caché obsoleta da PASS. Añadir falsaciones originales de todas las filas y positivos. En SH-11 ejecutar caso sobre el propio Guardian y contrastar con V0, herramientas de referencia o Gatekeeper anterior para la propiedad correspondiente. La autoaplicación no es certificación propia.

## Hitos y cierre

Desarrollo: todas las obligaciones y pruebas/adversarios/verificadores exigidos implementados, sin placeholders y con integraciones. Material: suites y auditoría independiente post-bloque, receipts del candidato, identidad/permiso y certificados scoped. El desarrollo de GSL-0 sigue pendiente de debate específico, no se decide por este documento.
