# Remediación de la auditoría integral — Q01…Q15

Base examinada: `ae8561f020b73693972c8d6d27d541e2709a9d9b`.
Fecha: 23 de octubre de 2026. Alcance: G00-B01/B02 y GSL0-LC00…LC03.
Estado: `REMEDIATED_BOUNDED_CANDIDATE`, no cierre de G-00/GSL-0 ni ratificación.

## Evidencia ejecutada

Se reconstruyeron los árboles exactos de la auditoría: src `326f7ec2d558b1b7ed5f9f88bbe18b990f963177`, tests `7ea72685649ef4319d2af5a55195c22169a899dd`.
La base dio 226 PASS. Las 16 falsaciones originales dieron 16 FAIL antes de modificar producción. Se conservan literalmente en `verification/ae8561f_original_falsifications.py.txt`.

El candidato remediado da 691 PASS, cero FAIL y cero SKIP en Python 3.13.5. Se repitió con PYTHONHASHSEED 0, 1 y 777: mismo resultado. El wheel se construyó, instaló en un directorio aislado y pasó la suite completa de 691 casos, comprobando que los 17 módulos guardian importados procedían de esa instalación, no del árbol fuente. compileall sobre src/tests/tools PASS.

Se ejecutaron 16 mutantes dirigidos (Q01…Q15 y una promoción de resultado parcial): 16 KILLED; cero supervivientes, errores de colección o SKIP admitidos como muertes. No es una campaña exhaustiva de todas las mutaciones posibles. `tools/run_foundation_mutations.py` reproduce los ataques en copias temporales.

Cobertura medida: 2503/2832 sentencias (88,38 %) y 1037/1358 ramas (76,36 %). Son métricas de ejecución, no porcentajes de obligaciones terminadas.

## Correcciones

| ID | Reparación productiva | Falsación preservada |
|---|---|---|
| Q01 | Parser nominal estricto; enum de otro eje rechazado; codec versionado | Matriz cartesiana de nueve ejes, tipos hostiles y roundtrip |
| Q02 | Fuentes gestionadas y repositorio de autoridad SIDECAR explícito | Ruta real fuente SIDECAR → vista → frontend; repo ajeno rechazado |
| Q03 | Identidad física independiente de alias/linaje; solapamiento de rutas | Dos alias del mismo corte generan SOURCE_POPULATION_DOUBLE_COUNT |
| Q04 | Baselines y ciclos para Git y documentos | DAG documental válido; ciclos y baselines ajenos rechazados |
| Q05 | Descriptor integra known_missing y adquisición MISSING | Ambos canales visibles sin perder límites ni conceder cualificación |
| Q06 | Pares de pins estrictamente inmutables | Lista/dict/tupla malformada no puede alterar un contexto frozen |
| Q07 | Digest nominal y coherencia de resultados | COMPILED no admite cadena/bytes/bool como digest |
| Q08 | Límites reales y fronteras UTF-8 en NormativeUnit | Rango excesivo y corte de carácter multibyte rechazados |
| Q09 | Protocolo de lectura puro en domain; application lo implementa | Verificación AST de imports, incluso dentro de funciones |
| Q10 | Presencia exacta de entidad, scope y evidencias en snapshot | Referencia huérfana o revisión distinta no se valida |
| Q11 | Coherencia entre fuente, tokens, CST, AST y extracción | AST extranjero o literal reescrito no produce ANALYZED válido |
| Q12 | true/false son constantes yes/no en el oráculo | Comparación contra átomos libres no recibe equivalencia |
| Q13 | Lexer independiente respeta comentarios de bloque y CR/LF/CRLF | Matriz de literales y comentarios compartida con el frontend |
| Q14 | Inventario independiente de cabeceras, declaraciones y campos | Intercambiar ID/origen conserva los hashes, pero es rechazado |
| Q15 | Correspondencia de campos no-V4 separada de equivalencia V4 | Cambiar scope/kind no recibe correspondencia positiva |

Se completó además `inspect_project_definition(project, view)` como inspección real del snapshot: informa política fijada, fuentes ausentes y constitución sin contenido, sin emitir cualificación. No se conserva el alias anterior que solo validaba el tipo de ProjectDefinition.

## Resultado semántico: garantías separadas

`formula_equivalent` describe únicamente el resultado finito de las fórmulas V4 enumeradas. `correspondence.declarations` y `correspondence.fields` describen el contraste independiente con el texto. `reference_integrity`, `historical_coverage` y `normative_admission` quedan explícitamente NOT_CHECKED por este verificador.

El antiguo `acceptable` se ha restringido: requiere fórmulas comprobadas, cabeceras y campos coincidentes y ausencia de propiedades diferidas/PO pendientes. Es una aceptación de correspondencia fuente→IR dentro del perfil, NO una cualificación del contrato ni de su implementación. `full_contract_equivalent` permanece falso mientras las dimensiones necesarias no estén comprobadas. No hay emisión de certificados ni métodos de admisión.

El inventario independiente no importa el parser/lexer productivo. Se deriva de bytes fijados externamente, reconoce declaraciones completas y la convención Markdown normativa explícita, excluye comentarios/ejemplos y conserva offsets. La abreviatura de referencia local se liga a la revisión de fuente o a un SymbolBinding explícito; esta correspondencia no prueba existencia. No se reivindica implementar LC04…LC09 mediante este módulo.

El presupuesto de enumeración es por fórmula y agregado por contrato. Agotar cualquiera devuelve un resultado inconcluso, nunca un PASS parcial.

## Cambios de pruebas positivos, sin borrar las falsaciones

1. Las observaciones válidas ahora incluyen entidad y scope realmente presentes en el snapshot; los casos huérfanos se mantienen negativos.
2. El descriptor conserva el límite declarado y agrega SOURCE_MISSING, en vez de ocultarlo para mantener una igualdad de tupla antigua.
3. Dos positivos de V0 que solo contenían fragmentos `when/holds` conservan su equivalencia de fórmula y ahora comprueban que NO implican correspondencia global.
4. Los positivos completos de Q14/Q15 incluyen en el texto los campos from/kind/scope antes inventados solo en el IR. Las permutas de origen y cambios de scope se conservan y exigen el diagnóstico específico. No se ha rebajado una falsación para hacerla pasar.

## Trazabilidad y autoridad

`verification/ae8561f_remediation_baseline.json` es una proyección congelada de auditoría, no una autoridad nueva. Conserva los 120 IDs de cláusula, 58 APIs, 36 adversarios y siete verticales; no los marca implementados por enumerarlos. Sus cuatro pins canónicos se contrastaron con el árbol Git remoto. `verification/remediation_manifest.json` vincula los 15 hallazgos, sus obligaciones, símbolos productivos y falsaciones.

`tools/check_remediation_contracts.py` exige el SHA-256 de baseline suministrado por el ejecutor. Detecta desaparición/reasignación de cláusulas y tests, símbolos inexistentes, SKIP/xfail y aserciones triviales. Su PASS es estructural: no demuestra suficiencia de una prueba ni independencia del revisor. La protección del baseline requiere un ejecutor externo que no permita al candidato sustituir el hash esperado.

No se reescriben `architecture/campaigns.json` ni sus refinamientos. Se preservan la autoridad, los denominadores y la distinción entre propuestas y normas ratificadas. El corpus histórico completo no se ha recompilado: LC09 permanece abierto.

## Límites explícitos

No se han implementado las campañas futuras, el resolver integral B06/LC04, el typechecker/lowering completos, el evaluador constitucional integral o las siete verticales completas de G-00. La comprobación Q10 es pertenencia exacta a un catálogo suministrado, no resolución de contenidos/autoridad de todas las entidades. Las familias R10 y las partes futuras de R11/R12 conservan su dependencia.

No se dispone en esta ejecución de Python 3.12, mypy/pyright ni de un auditor distinto del constructor. Esos controles están NOT_RUN, no PASS. Tampoco se emite un recibo firmado o una garantía de rendimiento industrial. No se ha ejecutado ni promovido el prototipo experiments como producto.

No se abren ramas nuevas ni se usan GitHub Actions. La publicación debe conservar exactamente los árboles src/tests ejecutados y usar avance de main con comprobación del padre; un cambio concurrente requiere reconciliación, no force-push.
