# G-00 / GSL-0 — Revisión de suficiencia y nuevas falsaciones

Fecha: 2026-10-26. Código examinado: `55fe58a28fde3f4e6c3f23b05643f303e38dd6d2`.
Estado: **OPEN_FINDINGS_NOT_CLOSED**. Esta entrega publica revisión y pruebas que fallan; no modifica producción ni las especificaciones originales. Es autoauditoría del constructor, no dictamen de un actor independiente.

## 1. Dictamen y alcance de la ejecución

La implementación fundacional y el recorrido GSL existen, pero el cierre de G-00 y GSL-0 sigue sin estar justificado. Se han reproducido seis familias de defectos: tres en el control de aceptación B08, una en validadores de fuentes y dos en las fronteras del compilador. No son únicamente aprobaciones o recibos pendientes.

| Ejecución | PASS | FAIL | ERROR | SKIP |
|---|---:|---:|---:|---:|
| Tests publicados del control B08, sin modificar | 44 | 0 | 0 | 0 |
| Nuevas falsaciones y controles | 8 | 16 | 0 | 0 |
| Selección conjunta | 52 | 16 | 0 | 0 |

Python 3.13.5. Se contrastaron 24 archivos con sus objetos Git exactos, incluidos los 19 módulos Guardian realmente importados. Los archivos observados no cambiaron entre comienzo y fin. Un subprocess real de pytest reproduce la importación de código de otra instalación. Los casos de GSL utilizan lexer, parser, resolución, tipado, elaboración y emisión productivos, sin mocks de esas operaciones.

**No es el checkout completo ni una nueva ejecución de los 887, 1598 u otros contadores históricos.** La copia de trabajo se reconstruyó selectivamente desde adjuntos y lecturas de GitHub. Se verificaron los blobs utilizados; no se presume correcto lo no ejecutado. Las pruebas del control B08 emplean la autoridad sintética declarada en su fixture original: no cuentan como aceptación de 120 contratos del producto.

[Registro de ejecución y pins](../../verification/review_2026_10_26/EXECUTION.json) · [Disposición individual de 120 cláusulas](../../verification/review_2026_10_26/CLAUSE_DISPOSITIONS.md).

## 2. G02 — La reconstrucción acepta una selección manipulada de unidades normativas

**Prioridad P1. Cuatro falsaciones fallan.** Afecta a extracción LC03, aceptación de análisis en LC05, elaboración LC06 y emisión. Contratos relacionados: GSL-T03/T06/T07 y separación entre ejemplos y norma.

La extracción normal de Markdown es correcta en los controles: dos fences `gsl normative` generan dos declaraciones; un fence `gsl example` no genera una declaración normativa. El fallo aparece al recibir objetos públicos `Extraction`/`FrontendAnalysis` preparados por el llamante.

La comprobación estructural acepta una partición sin pérdida de los bytes originales, pero no vuelve a decidir desde esos bytes qué fragmentos son normativos. La revalidación de `TypedProgram` vuelve a tipar los análisis suministrados; no reconstruye la extracción original.

Se ejecutaron dos alteraciones sin cambiar bytes, revisiones o pins de fuente:

1. Mover el segundo fence normativo a la población excluida. El tipado y la elaboración aceptan un IR con una declaración donde la fuente contiene dos.
2. Incorporar un fence de ejemplo como `NormativeUnit`, construyendo sus tokens/CST/AST con el frontend real. El tipado y la elaboración aceptan una declaración adicional.

Ambas variantes también pasan `emit_program`, `read_emission` y `verify_emission`. Este último reconstruye desde el mismo programa cuya extracción ya fue alterada. El hash del resultado puede ser perfectamente coherente con la omisión o inyección.

**Lo que falta no es comprobar únicamente:**

`yield(unidades + fragmentos_excluidos) == bytes_originales`

**También debe comprobarse:**

`unidades_aceptadas == Extract_version(bytes_originales, formato_fijado)`

Corrección: fijar el formato de fuente y reconstruir extracción/análisis desde todos los bytes en la frontera que acepta objetos públicos; comparar población y disposiciones exactas. Conservar los positivos del extractor y las pruebas de Unicode, comentarios, CR/LF, mapas y fórmulas.

Límites del hallazgo: no se ha demostrado que el extractor normal elija mal los fences, ni que el servicio que parte de bytes frescos omita unidades espontáneamente. No se ha atacado el V0 externo en esta revisión. Ninguno de estos resultados concede `normatively_admitted=true`; el defecto es la representación fuente–IR y su pretendida reconstrucción fiel.

## 3. G01 — El borrado seguido de alta elude la revisión inmutable

**Prioridad P1. Dos falsaciones fallan.** Propietario: `spec_lang/rebuild.py`.

Un reemplazo directo de bytes bajo la misma `EntityRef`/revisión se rechaza con `GSL_SOURCE_REVISION_REUSE`. Dividir exactamente el mismo cambio en una baja y un alta permite cambiar el campo `campaign` de la fuente y elaborar un IR nuevo bajo la misma referencia. Se reproduce con ambos órdenes del delta.

El control compara anterior/posterior solo dentro de cada `SourceChange` individual. La representación compuesta del delta evade esa comparación.

Corrección: comparar la población completa anterior y posterior antes de aplicar el delta. Para toda referencia que reaparezca, los bytes y pins deben seguir cumpliendo el contrato de revisión. Un cambio real de contenido necesita nueva revisión, independientemente de cómo se hayan agrupado las operaciones.

Los positivos de reemplazo con nueva revisión pasan tanto en forma directa como dividida. Esto no refuta la equivalencia del full rebuild con una compilación completa: demuestra que se admite un delta que incumple una precondición de identidad. No hace falta una caché incremental para corregirlo.

## 4. A03 — Se acepta evidencia de un código distinto del candidato

**Prioridad P1. Cinco falsaciones fallan, una con ejecución real de pytest.** Propietarios: `tools/g00_acceptance.py` y `tools/pytest_g00_receipt.py`.

El plugin registra `loaded_guardian_modules`, pero el control de aceptación no consulta ese registro. Omitirlo, vaciarlo o proporcionar un módulo con ruta/hash incompatibles no impide el resultado estructural favorable.

La prueba de subprocess no fabrica el éxito de pytest: el candidato local contiene `behavior() -> 0`, otra instalación contiene `behavior() -> 1`, y los tests importan realmente la segunda. Las pruebas pasan, el recibo registra correctamente el módulo externo, los hashes locales quedan estables y el gate devuelve `STRUCTURAL_EXECUTION_BINDINGS_CHECKED`.

Corrección: el plan fijado por el operador debe declarar la correspondencia entre módulos ejecutados y artefactos esperados; cotejar población, rutas admisibles y, sobre todo, bytes. Una instalación aislada de wheel puede ser legítima si sus módulos corresponden a los artefactos fijados. Exigir simplemente que toda ruta esté dentro del checkout no es una solución general.

El gate nunca marca `campaign_closed=true`; el hallazgo no es una certificación final falsa sino una vinculación incorrecta entre código y ejecución. La autenticidad del runner y las modificaciones transitorias permanecen garantías distintas.

## 5. A01 — Una operación existente puede sustituir otra API

**Prioridad P1. Una falsación falla.** El control fija mediante hash el registro original de una API, pero comprueba después que la operación indicada por el plan exista en el owner indicado por el propio plan. No compara esa operación con la original ni exige una correspondencia autorizada de adaptador.

La prueba cambia `behavior` por una función existente `unrelated`, manteniendo el hash del requisito original. El gate acepta.

Corrección: vincular operación y propietario originales, o una adaptación expresamente revisada que preserve precondiciones, postcondiciones y errores. La existencia de un símbolo no demuestra que sea la API contratada. Esta prueba no demuestra que todas las 58 operaciones actuales estén mal ni que se haya falsificado un pin externo: muestra que el comprobador no detecta un plan incongruente que debería rechazar.

## 6. A02 — El diagnóstico esperado se acepta como subcadena

**Prioridad P2. Una falsación falla.** El recibo normal contiene listas de códigos; el gate no valida ese tipo y aplica el operador `in` a lo recibido. Una cadena escalar `NOT_OBSERVED:SYNTHETIC_REJECT:UNRELATED` satisface el diagnóstico esperado `SYNTHETIC_REJECT`.

Corrección: esquema estricto de propiedades, listas de strings primitivos y coincidencia exacta de código. La falsación ataca un recibo malformado; no afirma que el plugin normal produzca esa cadena.

## 7. D01 — Validar una fuente no revalida sus invariantes

**Prioridad P2. Tres falsaciones fallan.** Afecta a G00-03-F01/F02 y APIs 013, 014 y 015.

Los constructores ordinarios rechazan un commit `main` y una versión documental vacía. Sin embargo, una subclase que omite `__post_init__` permite construir esos payloads, y los validadores públicos de fuentes los aceptan basándose en `isinstance`. El corte Git mutable también pasa la validación del universo sin diagnósticos.

Corrección: admisión nominal exacta o revalidación explícita de invariantes base, también al recorrer cortes anidados, sin delegar esa comprobación en hooks suministrados por la subclase.

No se ha demostrado admisión constitucional completa ni autenticación eludida. El resultado de cobertura cualificada permanece falso y otras fronteras, como el snapshot de tipos exactos, pueden rechazar la subclase. El incumplimiento concreto es que estos validadores publican validez de un corte que no cumple su contrato.

## 8. Estado de las doce obligaciones originales

La matriz adjunta enumera las 120 cláusulas individualmente. Sus filas son disposiciones de revisión: **no 120 PASS, no 120 fallos y no 120 funcionalidades ausentes**. La evidencia histórica no se descarta por no reejecutarse en esta selección.

| Padre | Implementación conocida | Aceptación/corrección pendiente |
|---|---|---|
| G00-01 | Identidades, codecs, aliases y resolver exacto | Postcondiciones de adapters públicos y replay integrado; no reescribir el núcleo |
| G00-02 | Proyectos, modos, políticas e imports finitos | Variantes de aislamiento de consumidores y contextos |
| G00-03 | Cortes, universos, historia y exclusiones | D01; regresión de aprobación específica y cobertura delimitada |
| G00-04 | Autoridad, decisiones, reglas y constituciones | Conexión completa de acciones, cuerpos, ámbitos y precedencia |
| G00-05 | Seis modelos, borradores y verificaciones separadas | Postcondiciones completas y relaciones compartidas |
| G00-06 | V4 con testigos y presupuesto | Reejecución integral y aceptación en servicios/codecs |
| G00-07 | Nueve ejes y observaciones | No promociones en todos los consumidores; labels no autentican auditoría |
| G00-08 | Resolver con cuerpos, historia e imports exactos | Todas las referencias anidadas y límites de anchors/imports |
| G00-09 | Codecs nominales v1/v2 y features | Todos los tipos raíz, compatibilidad y decisión de ABI explícita |
| G00-10 | Evaluador con población de reglas y presupuesto | Suficiencia de todos los predicados y hechos/diagnósticos simultáneos |
| G00-11 | Conflictos, supersesión y localización | Población fijada, testigos y determinismo de todas las entradas |
| G00-12 | Tests, mutaciones, verticales y control B08 | A01/A02/A03 y aceptación real 120/36/7, no solo fixtures del gate |

El test `tests/completion/test_api_projection.py` comprueba símbolos y firmas. Su propio contrato dice que es proyección estructural, no completitud. Falta concluir las 58 postcondiciones con positivos y falsadores pertinentes.

Los 36 adversarios deben rechazar la causa original y conservar el diagnóstico esperado o su adaptación explícita. Una mutación de otra familia no los sustituye. Las siete verticales existen en el desarrollo previo; no se han reejecutado todas aquí ni se da por suficiente cada una sin comparar su contrato íntegro.

## 9. Brecha documental de B08

En el árbol publicado del candidato no existe `verification/completion/obligation_evidence.json`. La matriz histórica de 47 cláusulas/once familias pertenecía a un candidato local anterior, no debe citarse como si estuviera publicada y actualizada en este HEAD.

El árbol de `verification/` sí conserva b00, b03, b04 y los perfiles/recibos históricos. La última entrega de B08 declara correctamente que no ha creado un plan real que certifique las 120 cláusulas. Su fixture usa dos tests sintéticos para ejercitar el gate. Esto permite probar el mecanismo, no acreditar la funcionalidad del producto.

Pendiente: publicar la matriz consolidada real con código, pruebas positivas, falsaciones, ejecuciones y juicio de conexión de los doce padres. La presente disposición de 120 filas orienta ese examen, pero no reemplaza esa evidencia ni lo marca terminado.

## 10. GSL: lo implementado y lo aún no aceptado

LC00–LC02 tienen contrato candidato, IR y V0, sin nueva ratificación ni reejecución del oráculo independiente en esta revisión. LC03 tiene frontend real, pero G02 afecta a la aceptación de resultados de extracción. LC04 resuelve referencias del perfil actual; imports y módulos generales siguen pendientes. LC05/LC06 tipan y elaboran ocho clases de declaración, pero aceptar un análisis manipulado no equivale a preservar la fuente completa.

LC07/LC08 tienen mapas, canonización, diagnósticos y PO pendientes. Tener spans válidos no demuestra conservar todas las declaraciones. LC09 sigue necesitando reconciliar el corpus original con GSL, separadamente de GSL→IR. El diff, la emisión y el full rebuild existen; G01/G02 afectan a sus condiciones de fidelidad. Las dependencias de contexto emitidas conservan `NOT_EXPORTED`: no son un paquete autónomo autenticado de toda la raíz de confianza.

La optimización incremental NO es un requisito que debamos inventar para cerrar un perfil cuyo contrato permite reconstrucción completa. Sí debe cumplirse la identidad de fuentes y la equivalencia bajo las mismas precondiciones. CTK-01 no bloquea esta revisión.

## 11. Secuencia concreta de remediación y cierre

Primero: proteger la población normativa de GSL (G02), los deltas inmutables (G01) y la correspondencia código-ejecución (A03). Después: cerrar las fronteras de fuentes y del plan/recibo (D01/A01/A02). Cada reparación conserva sus controles positivos y una falsación roja antes/verde después; no se eliminan ni se convierten en xfail.

A continuación: completar la matriz real 120/58/36/7 y sus juicios de suficiencia, ejecutar todo el checkout con módulos verificados, comprobar el paquete instalado y cerrar las variaciones adversarias de las siete verticales. Solo después procede el dictamen independiente B09 y la cualificación según las condiciones efectivas de confianza.

Python 3.12, análisis estático de tipos, suite global, revisión por otro actor y runner protegido no están ejecutados aquí. No es necesario implementar todo G-09 ni G-01…G-13 para acabar los validadores puros de G-00; sí declarar los límites del bootstrap.

## 12. Reproducción

Los probes viven fuera del directorio `tests/` para no convertir un acta de revisión con defectos abiertos en una modificación silenciosa de la suite normal. No usan skip ni xfail y no sustituyen pruebas anteriores. El comando explícito debe fallar sobre el SHA examinado:

```sh
PYTHONPATH=. python -m pytest -q \
  tests/acceptance/test_execution_bindings.py \
  verification/review_2026_10_26/test_gate_findings.py \
  verification/review_2026_10_26/test_source_and_rebuild_findings.py \
  verification/review_2026_10_26/test_extraction_binding_findings.py \
  -p tools.pytest_g00_receipt --g00-receipt=/tmp/g00-review.json \
  --junitxml=/tmp/g00-review.xml
```

El registro enumera los nodeids fallidos y hashes de los inputs y de los tres archivos de probes. No hay certificado de cierre: los seis hallazgos siguen abiertos y producción no se ha corregido en esta entrega de revisión.
