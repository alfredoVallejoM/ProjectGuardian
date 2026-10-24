# B00 / LC00–LC02 — reconciliación técnica y correspondencia externa

Fecha: 2026-10-24. Base: `edeb5c565012909f61feb1d27770f7bc037d0b79`.
Estado: `TECHNICAL_RECONCILIATION_AUTHORED_AND_TESTED`.
Este dictamen no ratifica normas, no es una auditoría por otro actor y no cierra
G-00 ni GSL-0. Las fuentes originales de `architecture/` no se reescriben.

## 1. Qué trabajo pendiente queda efectivamente entregado

| Entregable | Resultado técnico | Lo que no se deduce |
|---|---|---|
| Dictamen B00 | Doce juicios de cobertura de diseño y 120 disposiciones individuales | Prueba universal de suficiencia o implementación de los doce padres |
| APIs | Las 58 operaciones están reconciliadas con owner, firma real, bloque y decisión | Que las 58 estén implementadas; existen 23 nombres en el owner previsto |
| Formatos | Catálogo de 14 registros, cuatro JSON Schema 2020-12 y comprobador estricto | Decoder de los once registros de campañas posteriores |
| V0 externo | Correspondencia de declaraciones y campos del perfil GSL0/IR actual, incluida evaluación V4 | Existencia de todas las referencias, cobertura histórica o admisión normativa |
| Confianza | Lanzador con pins externos y comprobador real de separación de permisos | Instalación protegida, ratificación o revisión independiente ya realizadas |

Estos son entregables técnicos terminados dentro del alcance descrito. No se
recorta el contrato original para convertirlos en cierre global de campaña.

## 2. Dictamen semántico de B00, no solo conteo de enlaces

`verification/b00/parents.json` examina cada padre por dimensiones, indica el
puente necesario entre sus cláusulas y proporciona un contraejemplo en el que
los componentes aislados podrían pasar sin cumplir el padre.
`verification/b00/clauses.tsv` contiene las 120 disposiciones individuales:

- `REFINES`: descompone comportamiento exigido por su padre.
- `DESIGN_CHOICE`: fija una representación o algoritmo candidato; no es una
  consecuencia matemática única de la formulación del padre.
- `CROSS_CONTRACT`: necesita el contrato de otro padre o un detalle publicado
  de alcance. Se conserva la exigencia y se identifica la dependencia.
- `BOUNDARY`: delimita qué valida G-00 y qué deben producir sus consumidores.

El juicio es de cobertura de diseño condicionada a esos puentes, no un teorema
que convierta todos los tests de hojas en satisfacción de la raíz. En particular:
G00-01-F06 necesita resolución exacta, no solo EntityRef; Architecture y Campaign
se justifican por la especificación detallada de ontología, no por confundirlas
con las cuatro entidades del padre G00-05; las proyecciones y certificados no
se trasladan a G-00 por aparecer sus estados en G00-07.

La política de aceptación de 120 contratos, 36 ataques y siete verticales se
conserva íntegra. El código futuro deberá satisfacerla; este dictamen no marca
ninguna de esas pruebas futuras como escrita o ejecutada.

## 3. Reconciliación de APIs y decisiones

`verification/b00/apis.tsv` cubre exactamente G00-API-001…058. Para cada entrada
se registra la firma observada mediante AST y una disposición funcional
específica: correspondencia acotada, firma adaptada, API parcial, primitiva
escalar relacionada o implementación reservada al bloque propietario.

Las diferencias de codificación de fallo de encode/decode_identity permanecen
visibles como decisiones de compatibilidad pendientes de aceptación; no se
presentan excepciones o nombres de diagnóstico distintos como una identidad de
ABI ya ratificada. La firma de diseño sigue siendo referencia de obligación.
No se generan 35 funciones vacías para aparentar que el catálogo está completo.

`verification/b00/decisions.tsv` registra las 24 selecciones candidatas y su
justificación. Todas conservan `AWAITING_EXTERNAL_RATIFICATION`. La separación
actual entre CommitmentStatus (ciclo de vida) y DueStatus (exigibilidad temporal)
se documenta explícitamente, en lugar de reinterpretar silenciosamente los enums
originales. Las aprobaciones y sus fuentes no se inventan.

## 4. Formatos generales y controles implementados

`verification/b00/format_catalog.json` fija la envoltura común y la información
semántica que deben conservar los 14 registros. Distingue tres codecs actuales
(identidad, estado e IR) de los once registros cuyo decoder general aún no está
implementado. Los tipos futuros se rechazan, no se aceptan como diccionarios
opacos supuestamente tipados.

`schemas/guardian/` contiene esquemas 2020-12 para identidad, estado, ContractIR
y envoltura normativa. `tools/validate_record_envelope.py` usa un registro local
de esos esquemas fijados por hashes externos; no descarga `$ref` desde la red.
Comprueba discriminantes, variantes, versiones, campos obligatorios, tipos de
referencia y coherencia nominal básica de la envoltura. Distingue ausencia,
null y vacío. Rechaza claves JSON duplicadas, NaN, infinito, floats y enteros
fuera del rango interoperable sin codificación exacta explícita.

Las extensiones informativas solo se permiten en `info.*`. Los enteros grandes
usan `{"$type":"exact_integer","decimal":"..."}`. Una feature normativa que
el lector no conoce bloquea la lectura. El resultado es `WIRE_FORMAT_CHECKED`:
no demuestra integridad del dominio ni autentica autoridad o fuentes.

El descubrimiento de una discrepancia adicional se corrigió en producción:
FormulaIR ya no admite `true` ni `false` como átomos libres. La falsación Q12
original se conserva en su archivo histórico; la prueba activa forja
explícitamente un objeto inválido para seguir atacando también al verificador,
además de las nuevas pruebas que exigen rechazo en el constructor.

## 5. V0 externo de correspondencia completa del perfil actual

`verification/external_v0/contract_worker.py` es autónomo y solo usa la biblioteca
estándar. No importa Guardian, su lexer, su parser, source_inventory ni su VM.
Tiene inventario léxico y gramatical propio con offsets físicos UTF-8. Reconoce
las ocho clases del IR actual: source, scope, objective, capability, property,
obligation, verification y relation. Admite la convención Markdown normativa
fijada, excluyendo bloques de ejemplo y comentarios.

La expectativa fijada por el operador contiene digest fuente, proyecto, revisión,
inventario ordenado de declaraciones, bindings nominales y PO esperadas. El
candidato es el JSON real generado por `ir_to_data(ContractIR)`, no un modelo de
prueba que sustituya al producto. Se comprueban:

1. Cabeceras, población, identidad, revisión, proyecto y orden de declaraciones.
2. Origen de cada declaración obtenido de la fuente, sin confiar en sus spans.
3. Todos los nombres, posiciones, cardinalidades, discriminantes y valores de
   campos; referencias nominales y sus revisiones; source_item y modalidades.
4. Fórmulas V4 por dos evaluaciones distintas (tablas para fuente y bits para IR),
   con límites por fórmula y por contrato, contraejemplos y resultado inconcluso.
5. Preservación exacta de las PO fijadas externamente, sin promoción a PROVEN;
   las propiedades diferidas conservan su obligación pendiente.

La batería positiva integra las ocho clases y sus 25 campos del fixture completo.
Las pruebas adicionales cubren campos opcionales, repetidos y diferidos,
comentarios, Markdown, constantes, Unicode, referencias con revisión explícita,
mutaciones de fuente/IR y límites. Cadenas que contienen palabras clave o signos
no pueden convertirse en gramática por igualdad de su valor textual.

Un positivo devuelve `SOURCE_IR_CORRESPONDENT` y
`SOURCE_IR_CORRESPONDENCE_ONLY`. `reference_integrity`, `historical_coverage`,
`normative_admission` e `implementation_realization` permanecen `NOT_CHECKED`.
`full_contract_equivalent` permanece falso. La correspondencia completa de los
campos del perfil no sustituye las garantías posteriores de LC04–LC09.

El lanzador añade `--mode contract`, preservando `--mode formulas` para el worker
finito anterior. Comprueba los bytes y el hash del worker antes de ejecutarlos
con `python -I -S`, no reabre el fichero de código después del hash y exige que
la clase de resultado coincida con el modo solicitado. Los pins deben venir del
operador, no del candidato acompañado de sus propios hashes.

## 6. Verificación adversaria y ejecución material local

Base publicada reproducida: 780 PASS. Candidato final: **976 PASS, cero FAIL y
cero SKIP**, Python 3.13.5; **196 casos nuevos**. El paquete construido e instalado
aislado pasa los mismos 976 casos. Se verificó que los 17 módulos Guardian
importados procedían de la instalación aislada. compileall PASS.

Las 16 mutaciones anteriores vuelven a detectarse. Además, nueve mutaciones del
nuevo verificador externo se detectan por fallos de aserción específicos: identidad,
origen, valor, tipo, semántica V4, PO, pin fuente, presupuesto y promoción de
resultado. No se aceptan colección rota, timeout o SKIP como muertes de mutantes.
Es una campaña dirigida (25/25 en total), no mutación exhaustiva ni otro auditor.

El control del hito anterior pasa con sus 18 condiciones/24 funciones sobre el
JUnit actual. El nuevo control B00 comprueba 120 cláusulas, 12 padres, 58 APIs,
24 decisiones y sus pruebas enlazadas. Su PASS es estructural: la revisión
semántica está escrita en los dictámenes y necesita revisión independiente.

Las pruebas locales se ejecutan en una reconstrucción exacta de src/tests/tools/
verification de la base. Los originales normativos se leyeron mediante el
conector GitHub en la revisión fijada; no están todos materializados localmente.
Por ello el gate B00 se ejecutó con `external-readback` y señala expresamente
`EXTERNAL_GIT_READBACK_REQUIRED`. El árbol architecture y los documentos originales
se conservan por construir el commit sobre el árbol base sin reemplazarlos.
En un checkout íntegro el modo predeterminado `required` exige sus bytes y hashes.

Los registros de ejecución, hashes y resultados de mutación se publican en
`docs/verification/B00_EXTERNAL_CORRESPONDENCE_EXECUTION.json` y sus anexos.
No se ha ejecutado Python 3.12, mypy/pyright ni un actor independiente.

## 7. Confianza y salida exacta

`tools/check_external_verifier_installation.py` examina ownership, pins, permisos
reales del UID candidato, ancestros reemplazables y symlinks del worker y del
lanzador. No modifica permisos, crea cuentas ni falsifica aprobación. La ejecución
sobre el entorno actual devuelve correctamente HOLD: no hay separación de
identidades ni instalación protegida. Los positivos de política en tests usan
observaciones simuladas y no se presentan como despliegue real.

La autoría de reconciliación B00, el catálogo de APIs/formatos y el verificador
externo de correspondencia del perfil quedan entregados. B00 normativo y la
cualificación requieren aprobación externa de las decisiones, instalación con
permisos separados y revisión por otro actor. El cierre de G-00/GSL-0 sigue
requiriendo las implementaciones posteriores que el catálogo identifica.
