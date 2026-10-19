# G-06 — Extensión de ingeniería y verificación CCRR

**Propuesta, NO RATIFICADA.** Obligaciones originales intactas (12). No se afirma software o evidencia ejecutada. Fuente: architecture/campaigns.json y docs/campaigns/G-06.md.

## Compromiso y fronteras

Separar pruebas escritas, ejecución real, claims y qualification contextual.. Exclusión: No aceptar PASS por test escrito, filename receipt o decisión de LLM.. Dependencias de cierre: G-01, G-05. Corte autorreferencial SH-07; integraciones INT-05/06/08.

## Correspondencia por obligación

| ID | Contrato original | Refuerzo de garantía candidato | Falsación histórica preservada |
|---|---|---|---|
| G06-01 | Definir método, perfil, propiedad, falsaciones y expected verdict independiente del código test | Spec de prueba separada de ejecución | Test authored se considera ejecución |
| G06-02 | Registrar candidato exacto, entorno, runner, fixtures, output y status material | Run auténtico por candidato | Run de otro commit se reutiliza ciegamente |
| G06-03 | Entidades separadas con relación typed evidence y scope | Claim distinto de Evidence | Receipt existe y se llama teorema |
| G06-04 | Policy de ALL/ANY, oráculos independientes y requisitos científicos | Soporte probatorio distinto de refinamiento | Prueba trivial satisface theorem claim |
| G06-05 | Certificate por revision SourceUniverse profile evidence verifier policy | Certificado ligado a perfil/policy | Certificado acotado se amplía a otro dominio |
| G06-06 | SupportCone por revision y verificación de equivalencia inputs | Dependencias protegidas completas | Cambio relevante no invalida soporte |
| G06-07 | Revocar/disputar/STALE cuando protegido cambia y mantener historia | Invalidación contextual y reversible | Receipt invalidado continúa CURRENT |
| G06-08 | Receipts de ejecución auténtica verificados contra emitter/trust model | Atestación de runner, no JSON agente | Archivo JSON escrito por agente pasa |
| G06-09 | AuditRecord por obligación, documento, finding y counterexample | Auditoría granular con testigos | Una frase general cierra decenas de requisitos |
| G06-10 | Políticas reales entre author/reviewer/runner y monoagente | Independencia por identidad protegida | El mismo agente se acredita independiente |
| G06-11 | Desarrollo auditoría material integración qualification por separado | Development y Material ortogonales | DEVELOPED promueve QUALIFIED |
| G06-12 | Rechazar receipts falsos, scopes erróneos, tests circulares y missing refs | Pruebas hostiles de falsificación | Certificado manipulado recibe PASS |

## Condición de suficiencia

El objetivo superior requiere la realización de los contratos hijos, sus bridges y las hipótesis autorizadas. A∧D∧J⇒G es una obligación verificable, no un status derivado de un contador. Para cambios de implementación y evidencias debe preservarse ámbito, sujeto, revisión, ruta ejecutada y clase de prueba; el motor de esta campaña no puede conceder autoridad a la mera presencia de ficheros.

## Ensayo adversario

Un test escrito o recibo manual obtiene certificación; un ciclo sostiene claim sin hoja. La prueba de cada obligación incluye su falsación original y un caso positivo válido. Se debe comprobar además el flujo real INT-05/06/08, no solo simulaciones aisladas. SH-07 incorpora una realización auténtica sobre el propio ProjectGuardian; V0/runner independiente evita que el candidato sea el único juez.

## Estados de cierre

DEVELOPMENT_COMPLETE: todas las obligaciones y subcontratos aplicables desarrollados, pruebas/adversarios/verificadores autorados, integraciones realizadas; no obliga ya a ejecución material. CAMPAIGN_CLOSED: pruebas ejecutadas con candidate/profile correctos, auditor diferente tras fin de bloque, recibos válidos y conclusión acotada. El contrato GSL-0 sigue expresamente pendiente.
