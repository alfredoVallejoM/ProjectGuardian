# G-09 — Extensión CCRR propuesta

**DOCUMENTO DE DISEÑO, NO RATIFICADO; 0 IMPLEMENTACIÓN O CERTIFICACIÓN NUEVAS.** Las 12 obligaciones originales y su autoridad permanecen intactas.

Objetivo histórico: Impedir alteración de normas/verificadores por el productor y garantizar publicación controlada.. Exclusión: No confiar en prompt/hook local como frontera real de seguridad.. Dependencias de cierre: G-01, G-06. Autoaplicación SH-09, integración INT-06.

## Revisión completa de obligaciones

| Obligación | Contrato fuente | Condición CCRR a desarrollar | Falsación original |
|---|---|---|---|
| G09-01 | Autorización por principal autenticado, proyecto, ámbito, expiración y acción | Capacidades de permiso autenticadas | Agente reclama permisos en JSON |
| G09-02 | Evaluador/reglas viven fuera de candidato editable con trust boundary real | Evaluador protegido fuera de candidate | A2 cambia policy y obtiene PASS |
| G09-03 | Modificación normativa usa constitución previa y aprobaciones explícitas | Enmienda bajo reglas anteriores | Regla nueva se aprueba a sí misma |
| G09-04 | Validar rutas modificadas, áreas prohibidas, cambios de authority | Paths y scopes autorizados | Commit incluye archivo no autorizado |
| G09-05 | Vincular package, audit, tests y commit que se publica | Candidato publicado = auditado | Se publica código diferente del auditado |
| G09-06 | Verificación de firma/identidad y materiales de ejecución según policy | Receipts auténticos | Fake receipt JSON obtiene PASS |
| G09-07 | Version/scopes de plugin con admission policy y isolation | Verifier registry acotado | Plugin always PASS obtiene poder universal |
| G09-08 | Run processes no confiables con red/fs/mem/time definidos | Aislamiento del runner | Malicioso altera policy host |
| G09-09 | Publicación atómica a ref esperada sin force bypass | CAS ref esperado | Candidatos paralelos sobrescriben |
| G09-10 | Enmiendas requieren autoridad, impacy y tests de la policy vieja | ConstitutionChange trazable | Obligación ratificada se debilita |
| G09-11 | Interrupciones entre candidate/ref/sqlite no producen dual authority | Crash sin dual authority | Crash deja estado parcialmente admitido |
| G09-12 | Tests de permisos, self-certification, receipt forgery, tampering y branch race | Red team de self-certification | Mutación del Gatekeeper no detectada pasa |

## Suficiencia y aceptación

El contrato raíz G solo se considera satisfecho si existe prueba de suficiencia A∧D∧J⇒G, antecedente realizable y evidencia auténtica sobre el candidato para cada componente/bridge. Las obligaciones de tipo proceso, arquitectura, algoritmo y evidencia no son intercambiables. El grafo de trazabilidad no crea autoridad por enlaces.

Caso adversario propio: Candidate modifica policy antes de validarse o falsifica un receipt. Añadir caso positivo correspondiente. Ejecutar un ensayo real SH-09 sobre ProjectGuardian cuando estén construidos los verificadores, y conservar independencia de la raíz V0 o política previa protegida. No exigir un número fijo de agentes.

## Salidas por bloque

Contrato exacto y cierre de obligaciones, código/casos desarrollados, testigos de realización si aplican, pruebas de integración, matriz de falsaciones, auditoría independiente tras fin de implementación, recibos materiales al calificar, y decisión de cierre por revisión/alcance.

Se distinguen DEVELOPMENT_COMPLETE (código, tests, adversarios y verificadores escritos) y CAMPAIGN_CLOSED (además auditoría, ejecución material, receipts y autoridad). Sin GSL-0 aprobado ni modificación de obligaciones históricas por esta extensión.
