# G-10 — Extensión CCRR propuesta

**DOCUMENTO DE DISEÑO, NO RATIFICADO; 0 IMPLEMENTACIÓN O CERTIFICACIÓN NUEVAS.** Las 12 obligaciones originales y su autoridad permanecen intactas.

Objetivo histórico: Acreditar especificación para SourceUniverse, soporte contextual y paridad histórica.. Exclusión: Nunca llamar científica a cobertura estructural.. Dependencias de cierre: G-02, G-05, G-06, G-07. Autoaplicación SH-08, integración INT-01/04/08.

## Revisión completa de obligaciones

| Obligación | Contrato fuente | Condición CCRR a desarrollar | Falsación original |
|---|---|---|---|
| G10-01 | Certificar universo autenticado con inclusiones/exclusiones y cobertura de inventario | Universo fuente completo por corte | Se afirma exhaustividad con fuentes sin analizar |
| G10-02 | Mapear cada requisito fuente a obligación/decision/hito sin perder original | Crosswalk fino por facetas | Requisito no aparece y nadie lo advierte |
| G10-03 | Correspondencia obligación-implementación en perfil y versión | Denominador original externo al código | Obligación sin code recibe complete |
| G10-04 | Mapa property/VerificationSpec/actual test/run/evidence | Proof coverage por property y run | Test genérico se cuenta para todo |
| G10-05 | Coverage separado por source revision scope milestone y unknowns | UNKNOWN fuera de porcentaje falso | CURRENT se traslada a FUTURE para obtener 100% |
| G10-06 | Source/target, domain, relation, effects, consumers, resources | Migración preserva dominio | Subset sustituye dominio histórico |
| G10-07 | Ejecutar original destino y oráculo con fixtures equiparables | Oráculo histórico real | Dos mocks nuevos sustituyen original |
| G10-08 | Protected dependency cone con decision REUSE/RECOMPUTE/HOLD | Conos protegidos de evidencia | SHA global irrelevante fuerza todo o cambio importante se ignora |
| G10-09 | Prueba conservar garantía en D_old y nuevas obligaciones D_new | Generalización conserva D_old | Generalización pierde caso original |
| G10-10 | API/ABI/consumer parity antes de retirar legacy provider | Consumers vivos protegidos | Se retira dueño original con consumidores vivos |
| G10-11 | Detectar deficits de implicaciones, material y audit antes de cerrar | Gaps no desaparecen por editar status | Un gap se oculta reduciendo definición |
| G10-12 | SOURCE, SPEC, IMPLEMENTED, INTEGRATION, SCIENTIFIC, MIGRATION no se implican | Certificados SOURCE vs SCIENTIFIC | SOURCE_COVERAGE produce SCIENTIFIC_PASS |

## Suficiencia y aceptación

El contrato raíz G solo se considera satisfecho si existe prueba de suficiencia A∧D∧J⇒G, antecedente realizable y evidencia auténtica sobre el candidato para cada componente/bridge. Las obligaciones de tipo proceso, arquitectura, algoritmo y evidencia no son intercambiables. El grafo de trazabilidad no crea autoridad por enlaces.

Caso adversario propio: Se limita dominio histórico y luego se declara cobertura plena de nueva implementación. Añadir caso positivo correspondiente. Ejecutar un ensayo real SH-08 sobre ProjectGuardian cuando estén construidos los verificadores, y conservar independencia de la raíz V0 o política previa protegida. No exigir un número fijo de agentes.

## Salidas por bloque

Contrato exacto y cierre de obligaciones, código/casos desarrollados, testigos de realización si aplican, pruebas de integración, matriz de falsaciones, auditoría independiente tras fin de implementación, recibos materiales al calificar, y decisión de cierre por revisión/alcance.

Se distinguen DEVELOPMENT_COMPLETE (código, tests, adversarios y verificadores escritos) y CAMPAIGN_CLOSED (además auditoría, ejecución material, receipts y autoridad). Sin GSL-0 aprobado ni modificación de obligaciones históricas por esta extensión.
