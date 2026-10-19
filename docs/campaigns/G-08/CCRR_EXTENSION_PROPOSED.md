# G-08 — Extensión CCRR propuesta

**DOCUMENTO DE DISEÑO, NO RATIFICADO; 0 IMPLEMENTACIÓN O CERTIFICACIÓN NUEVAS.** Las 11 obligaciones originales y su autoridad permanecen intactas.

Objetivo histórico: Interfaces de agente independientes, con perfil A0–A4 opcional y gobierno externo.. Exclusión: No condicionar uso a cinco agentes ni conceder autoridad al SDK.. Dependencias de cierre: G-04, G-07, G-09, G-11. Autoaplicación SH-10, integración INT-07.

## Revisión completa de obligaciones

| Obligación | Contrato fuente | Condición CCRR a desarrollar | Falsación original |
|---|---|---|---|
| G08-01 | Protocolo de herramientas con schemas independientes de modelo SDK | Tool schema sin dependencia de LLM | Motor requiere API exclusiva de modelo |
| G08-02 | API orient entrega revisión y reglas antes del desarrollo | Orientación normativa vigente | Agente arranca sin normativa accesible |
| G08-03 | Recuperación fraccionada conserva index y exact closure | Retrieval sin loss de closure | Prompt corto borra requisito |
| G08-04 | Encargos identificados y leídos sin posibilidad de alterar contrato | Package inmutable por revisión | Modelo escribe obligaciones diferentes |
| G08-05 | Exponer graph impact sources consumers architecture mediante tool calls | Consulta sin inventar owners | Agente inventa owner no corroborado |
| G08-06 | Entrega estructurada con alcance, artifacts, test authored y claims no auto-validantes | Delivery manifest claim no prueba | Texto "PASS" certifica entrega |
| G08-07 | Flujo completo con una sesión humana/agent + posibles auditorías externas | Monoagente funcional | Se necesitan 5 agentes para validar |
| G08-08 | Perfil A0 organizador A1 research A2 build A3 adversarial A4 integrator | Multiagente perfil opcional | Cada subagente mantiene norma propia |
| G08-09 | Transporte de hashes de paquete, snapshot, findings y artifacts | Handoff conserva hashes/obligaciones | Se pierde obligación entre delegaciones |
| G08-10 | Autor/auditor/runner identificados y policy de review | Autor y auditor identidades distintas | A2 se autocertifica como A3 independiente |
| G08-11 | Cambiar proveedor/SDK conserva work package y estado normativo | Cambio modelo no cambia contrato | Cambio de LLM cambia significado de contrato |

## Suficiencia y aceptación

El contrato raíz G solo se considera satisfecho si existe prueba de suficiencia A∧D∧J⇒G, antecedente realizable y evidencia auténtica sobre el candidato para cada componente/bridge. Las obligaciones de tipo proceso, arquitectura, algoritmo y evidencia no son intercambiables. El grafo de trazabilidad no crea autoridad por enlaces.

Caso adversario propio: Se pierde una obligación en handoff o el constructor se hace pasar por auditor. Añadir caso positivo correspondiente. Ejecutar un ensayo real SH-10 sobre ProjectGuardian cuando estén construidos los verificadores, y conservar independencia de la raíz V0 o política previa protegida. No exigir un número fijo de agentes.

## Salidas por bloque

Contrato exacto y cierre de obligaciones, código/casos desarrollados, testigos de realización si aplican, pruebas de integración, matriz de falsaciones, auditoría independiente tras fin de implementación, recibos materiales al calificar, y decisión de cierre por revisión/alcance.

Se distinguen DEVELOPMENT_COMPLETE (código, tests, adversarios y verificadores escritos) y CAMPAIGN_CLOSED (además auditoría, ejecución material, receipts y autoridad). Sin GSL-0 aprobado ni modificación de obligaciones históricas por esta extensión.
