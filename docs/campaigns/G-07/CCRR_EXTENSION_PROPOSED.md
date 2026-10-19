# G-07 — Extensión de ingeniería y verificación CCRR

**Propuesta, NO RATIFICADA.** Obligaciones originales intactas (12). No se afirma software o evidencia ejecutada. Fuente: architecture/campaigns.json y docs/campaigns/G-07.md.

## Compromiso y fronteras

Admitir software heterogéneo sin acoplar el núcleo a los lenguajes ni importar autoridades ajenas.. Exclusión: No certificar AST/feature exhaustivos con análisis parciales.. Dependencias de cierre: G-02. Corte autorreferencial SH-06/07; integraciones INT-01/04/05.

## Correspondencia por obligación

| ID | Contrato original | Refuerzo de garantía candidato | Falsación histórica preservada |
|---|---|---|---|
| G07-01 | Leer árboles, blobs, commits y diffs por commit exacto con source policy | Objetos Git inmutables | Branch mutable tratado como source cut fijo |
| G07-02 | Importar programas/registros históricos sin duplicar ID ni autoridad | Import sin autoridad duplicada | Import crea segunda fuente editable |
| G07-03 | Analizador Rust manifest AST features y generated con coverage report | Features Rust no visibles→UNKNOWN | Feature o macro omitido sin HOLD |
| G07-04 | Analizador C++ compile commands, Clang AST macros includes ABI | Macros/ABI C++ con cobertura | Macro/ABI ausente declarado completo |
| G07-05 | Analizar Python imports exports entrypoints y dinámico con límites | Imports Python dinámicos declarados | Import dinámico desconocido se asume comprendido |
| G07-06 | Analizador declarations/imports/axioms/proof reports reales con estados distintos | Lean statement/proof/axioms distintos | Nombre de teorema prueba compilación |
| G07-07 | Ejecutores de test/proof/resource con receipt fiable, errores tipados | Runner timeout≠PASS | Timeout aparece como PASS |
| G07-08 | Importaciones normativas con ApprovedSourceImport y provenance | Grant externo específico | Referencias de proyectos diferentes se fusionan por nombre |
| G07-09 | ProjectSourceUniverse puede contener cuts de varios repos con identidad separada | Multi repo sin mezclar IDs | Se mezclan HEADs y fuentes |
| G07-10 | Derivar deltas y conservar status/IDs históricos | Import incremental mantiene linaje | Nuevo import renombra silenciosamente unidades |
| G07-11 | Informar macros, reflection, generated sin cobertura y declarar límites | Unsupported construct visible | Inventario parcial afirma complete |
| G07-12 | Suite común source adapter para version, id, ambiguity, missing data y isolation | Conformance idéntico por adaptador | Un adaptador cambia significado de PASS |

## Condición de suficiencia

El objetivo superior requiere la realización de los contratos hijos, sus bridges y las hipótesis autorizadas. A∧D∧J⇒G es una obligación verificable, no un status derivado de un contador. Para cambios de implementación y evidencias debe preservarse ámbito, sujeto, revisión, ruta ejecutada y clase de prueba; el motor de esta campaña no puede conceder autoridad a la mera presencia de ficheros.

## Ensayo adversario

Feature no compilada, macro o plugin no observado se declara cobertura total. La prueba de cada obligación incluye su falsación original y un caso positivo válido. Se debe comprobar además el flujo real INT-01/04/05, no solo simulaciones aisladas. SH-06/07 incorpora una realización auténtica sobre el propio ProjectGuardian; V0/runner independiente evita que el candidato sea el único juez.

## Estados de cierre

DEVELOPMENT_COMPLETE: todas las obligaciones y subcontratos aplicables desarrollados, pruebas/adversarios/verificadores autorados, integraciones realizadas; no obliga ya a ejecución material. CAMPAIGN_CLOSED: pruebas ejecutadas con candidate/profile correctos, auditor diferente tras fin de bloque, recibos válidos y conclusión acotada. El contrato GSL-0 sigue expresamente pendiente.
