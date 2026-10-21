# GSL0-LC03 — Argumento de conservación textual y límites de la prueba

**Estado:** argumento informal + tests materializados sobre el fragmento descrito; **NO** teorema Lean, Coq ni verificación universal mecanizada. No afirmar que un Markdown histórico arbitrario es normativo ni que AST tipa su semántica.

## Hipótesis

Entrada `B` consiste en bytes UTF-8 válidos aportados por `SourceBundle` con digest externamente esperado, revisiones nominales y origen exacto. `extract_normative_units` recibe el formato explícito `gsl` o `markdown`. Límites iniciales: 2 MB, 100.000 tokens, profundidad de CST/AST 64; errores de límite son rechazos explícitos.

## Lema T01. Cobertura textual exacta

El segmentador recorre cada Unicode scalar sin transformarlo, aumenta el cursor físico por la longitud de su codificación UTF-8 y agrupa únicamente caracteres contiguos según la clase `newline/whitespace/content`. Si las posiciones de dos grupos consecutivos son `(s_i,e_i)` y `(s_{i+1},e_{i+1})`, el algoritmo establece `e_i=s_{i+1}`, y el último termina en `|B|`. Cada segmento conserva `B[s_i:e_i]`. Por concatenación, `concat(segments.raw)=B`. Las pruebas comprueban la propiedad con Unicode, CRLF, BOM, bytes vacíos y 100 composiciones pseudoaleatorias reproducibles.

Para Markdown, las unidades declaradas normativas y los huecos no normativos forman una partición ordenada de `B`: `concat(B[span])=B`. Una unidad solo existe dentro de un fence reconocido y cerrado, explícitamente marcado `gsl normative`; prosa y ejemplos se conservan en el complemento. Este hecho NO prueba que el usuario/editor haya ratificado el texto.

## Lema T02. Reconstrucción de tokenstream y CST

El lexer avanza el cursor sobre caracteres y genera para cada token el intervalo byte exacto del fragmento consumido, incluidos comentarios y espacios. Ninguna rama de lexer descarta bytes. `TokenStream.__post_init__` verifica igualdad byte a byte con la unidad fuente. La construcción CST sustituye cada par de delimitadores por un grupo que conserva sus tokens de apertura/cierre y sus hijos en el mismo orden. Por inducción en la profundidad de grupos, `Yield(group)` equivale a la concatenación de tokens que lo produjeron; la raíz reconstruye todos los bytes. Strings y comentarios se tratan como tokens atómicos, por lo que un `}` contenido en ellos no cierra grupo.

La comprobación directa `CSTGroup.__post_init__` rechaza un intervalo de hijos discontinuo, y el constructor rechaza delimitadores sin pareja o grupos excesivamente profundos.

## Lema T03. Conservación sintáctica de declaraciones

La gramática del fragmento exige encabezado versionado y proyecto, luego reconoce todas las declaraciones admitidas con nombre, campos y expresiones, sin producir objetos normativos cuando encuentra sintaxis desconocida. Cada declaración AST retiene su intervalo de bytes y cada campo/expresión un subintervalo válido. Las pruebas verifican presencia y orden de declaraciones y campos, y mutaciones sintácticas que se rechazan en lugar de desaparecer silenciosamente.

**No se demuestra** que un AST preserve la intención de una fuente de lenguaje natural, que todos los símbolos tengan referencia real, que `AST→IR` conserve semántica, que todos los documentos históricos estén incluidos, ni que un AST válido sea una especificación aprobada. Estas son obligaciones posteriores.

## Refutaciones exigidas y comprobadas

- Eliminar un delimitador, cerrar con signo equivocado o exceder profundidad: error sin CST positivo.
- Escapes JSON inválidos, strings abiertas, comentarios abiertos, caracteres no reconocidos y presupuestos excedidos: `REJECTED`.
- Fence sin marca normativa o bloque de ejemplo: cero unidades normativas; no admisión accidental.
- Mutar proyecto conservando gramática: `GSL_FOREIGN_PROJECT`.
- Crear manualmente `FrontendAnalysis(COMPILED)`: error estructural.
- Mover offsets entre bytes de un carácter Unicode: se comprueba por slicing exacto.

Estas pruebas son evidencia finita, no reemplazan auditoría independiente ni demostración universal.
