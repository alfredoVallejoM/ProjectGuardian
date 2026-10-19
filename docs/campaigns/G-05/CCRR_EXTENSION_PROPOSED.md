# G-05 — Extensión de ingeniería y verificación CCRR

**Propuesta, NO RATIFICADA.** Obligaciones originales intactas (12). No se afirma software o evidencia ejecutada. Fuente: architecture/campaigns.json y docs/campaigns/G-05.md.

## Compromiso y fronteras

Contrastar contrato/arquitectura especificada con código observado y obligaciones.. Exclusión: No convertir nombres de módulos y tests en prueba de funcionalidad.. Dependencias de cierre: G-02, G-07. Corte autorreferencial SH-06; integraciones INT-04/05.

## Correspondencia por obligación

| ID | Contrato original | Refuerzo de garantía candidato | Falsación histórica preservada |
|---|---|---|---|
| G05-01 | Modelos SpecifiedArchitecture y ObservedArchitecture comparados sin convertir observed en norma | Specified distinto de Observed | Codigo unario reduce contrato n-ario |
| G05-02 | Comparar bounded contexts, owners, módulos, funciones e invariantes | Roles no colapsan en ficheros | Módulo asume responsabilidad ajena |
| G05-03 | Import graph observado contra allowed/required/forbidden edges | Dependencias prohibidas transitivas | Import ilegal es aprobado |
| G05-04 | Verificar unicidad semántica según scope y conflictos | Owners únicos y scope | Dos propietarios incompatibles |
| G05-05 | Surface de API y versioning, consumidores y cambios ABI | API/ABI/consumers reales | Consumidor anterior roto sin finding |
| G05-06 | RealizationLink muchos-a-muchos para implementación y comportamiento | Testigo de realización por build/ruta | Se identifica archivo con capacidad funcional completa |
| G05-07 | VerificationLink y contratos de prueba por property | Propiedad real vs test nominal | Test genérico acredita ley no examinada |
| G05-08 | Distinguir subset, profile parcial, missing domain y fallback | Dominio parcial sin falsa completitud | Demo restringida sustituye implementacion completa |
| G05-09 | Contrastar claims y soporte entre revisiones de source/profile | Regresión por cono protegido | Propiedad degradada conserva PASS |
| G05-10 | Validar contratos para nuevo owner sin duplicación ni switches no permitidos | Extensión sin romper interfaz | Implementación rompe punto de extension aprobado |
| G05-11 | Contracts productor-consumidor y E2E por perfil | E2E productor-consumidor | Unit tests aislados cierran integración |
| G05-12 | ConformityReport exhaustivo de gaps, UNKNOWN y denominadores reales | Reporte gaps incl. suficiencia | Se oculta incompletitud del informe |

## Condición de suficiencia

El objetivo superior requiere la realización de los contratos hijos, sus bridges y las hipótesis autorizadas. A∧D∧J⇒G es una obligación verificable, no un status derivado de un contador. Para cambios de implementación y evidencias debe preservarse ámbito, sujeto, revisión, ruta ejecutada y clase de prueba; el motor de esta campaña no puede conceder autoridad a la mera presencia de ficheros.

## Ensayo adversario

Una implementación correcta pero no llamada públicamente recibe false PASS. La prueba de cada obligación incluye su falsación original y un caso positivo válido. Se debe comprobar además el flujo real INT-04/05, no solo simulaciones aisladas. SH-06 incorpora una realización auténtica sobre el propio ProjectGuardian; V0/runner independiente evita que el candidato sea el único juez.

## Estados de cierre

DEVELOPMENT_COMPLETE: todas las obligaciones y subcontratos aplicables desarrollados, pruebas/adversarios/verificadores autorados, integraciones realizadas; no obliga ya a ejecución material. CAMPAIGN_CLOSED: pruebas ejecutadas con candidate/profile correctos, auditor diferente tras fin de bloque, recibos válidos y conclusión acotada. El contrato GSL-0 sigue expresamente pendiente.
