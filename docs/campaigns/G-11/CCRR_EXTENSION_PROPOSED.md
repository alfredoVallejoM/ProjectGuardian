# G-11 — Extensión contractual CCRR y pruebas de autoverificación

**Estado: PROPUESTA DOCUMENTAL, no norma ratificada, código ni evidencia material.** Preservar 12 obligaciones canónicas de architecture/campaigns.json.

Objetivo: Exponer servicios del núcleo de manera uniforme y navegable.. Exclusión: Ninguna interfaz contiene segunda lógica de autoridad.. Dependencias de cierre: G-03, G-04, G-09. Contratos INT-07. Hito SH-10.

## Cláusulas originales y nuevos puentes de garantía

| ID original | Desarrollo fuente | Justificación/realización específica que se añade como candidata | Falsación histórica |
|---|---|---|---|
| G11-01 | Comandos para project, contract, obligation, campaign, graph, package, evidence, audit, change | CLI cubre casos de uso | Operación crítica solo accesible por script privado |
| G11-02 | Servicios tipados con validation de scopes y permissions | API valida scope y autoridad | Cliente escribe directamente SQLite normativo |
| G11-03 | MCP/API para orientación consultas entregas sin copiar source total a prompts | MCP sin contratos hardcoded | Skill con hardcoded contratos de cada proyecto |
| G11-04 | UI de objetivos/capacidades/propiedades/obligaciones many-to-many | Explorador de contratos many-to-many | Vista pierde conexiones múltiples |
| G11-05 | Vista specified/observed y límites/conflictos | Specified vs Observed separado | Arquitectura observada se muestra como aprobada |
| G11-06 | Conos de soporte/impacto, razones y limitaciones | Conos informativos ≠ proof | Link informativo se dibuja como proof edge |
| G11-07 | Denominadores per source/profile/milestone con unknowns visibles | Denominadores/UNKNOWN visibles | Unknown requirements se omiten |
| G11-08 | Versiones, changeset, revocations e invalidaciones navegables | Historia y revocación no se borran | Revocación borra certificado histórico |
| G11-09 | Manifest inmutable y vista explicativa diferenciados | Manifest distinto de prompt | Text prose sustituye normative manifest |
| G11-10 | Interfaz solicita autorizaciones sin autoadjudicación de permisos | UI solicita, no autoaprueba | Un click de UI ratifica sin identidad |
| G11-11 | Informes JSON/Markdown con revisión, fuente y scope | Export versionado y reproducible | Export pierde versión y evidencia |
| G11-12 | Las mismas llamadas de CLI/API/UI/MCP producen igual state/verdict | Paridad de veredictos por superficie | Un cliente calcula PASS alternativo |

## Contrato raíz y conexiones

G es el objetivo completo; D son las subobligaciones; J las integraciones; A los supuestos. Exigir PO para (A∧D∧J⇒G), factibilidad y realización concreta, sin conteos sustitutivos. Los contratos INT-07 deben probarse end-to-end con dueño y consumidores especificados. No promover soporte parcial a prueba científica, integración universal o seguridad del host.

## Adversarios y selfhost

MCP retorna otro alcance o PASS que la CLI del mismo snapshot. Añadir falsaciones originales de todas las filas y positivos. En SH-10 ejecutar caso sobre el propio Guardian y contrastar con V0, herramientas de referencia o Gatekeeper anterior para la propiedad correspondiente. La autoaplicación no es certificación propia.

## Hitos y cierre

Desarrollo: todas las obligaciones y pruebas/adversarios/verificadores exigidos implementados, sin placeholders y con integraciones. Material: suites y auditoría independiente post-bloque, receipts del candidato, identidad/permiso y certificados scoped. El desarrollo de GSL-0 sigue pendiente de debate específico, no se decide por este documento.
