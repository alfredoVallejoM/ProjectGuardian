# GSL0 C12 — diferencias tipadas, conservadoras y presupuestadas

Fecha: 2026-10-26. Base publicada: `a361981a4ab29b43110136a47141e070e66c649c`.
Estado: IMPLEMENTED_AND_SELECTED_TESTS_PASS; no cierre global de GSL ni G-00.
Autoridad de diseño: `docs/specification/GSL0_FORMAL_COMPILER_CONTRACT_PROPOSED.md`,
fase C12 y contratos de canonización/PO. No se modifica esa fuente original.

## Comportamiento productivo

`guardian.spec_lang.contract_diff.diff_contracts(before, after, budget)` recibe
bytes JSON exactos producidos por el serializer ContractIR. El decoder existente
valida versión, tipos nominales, referencias y campos; no se crea otra semántica
ni se toma un texto parecido como equivalencia. No se verifican los bytes fuente
originales mediante esta API: esa garantía pertenece a source maps y V0.

La correspondencia de declaraciones usa proyecto, clase e identidad lógica.
La revisión se compara por separado. Dos revisiones del mismo identificador en
un mismo input producen INCOMPARABLE, nunca latest-wins. Proyectos diferentes
no se fusionan. El orden de declaraciones, campos y PO se conserva explícitamente.

El informe identifica declaraciones añadidas/borradas, revisiones, orígenes,
corte y digest de fuente, campos añadidos/borrados/alterados y orden. Los campos
repetidos requires/verification mantienen multiplicidad e índice de aparición.
Las PO conservan identificador, origen exacto y estado: borrar una PO o cambiar
UNPROVEN por CHECKED_FINITE_DOMAIN produce una diferencia, no una prueba válida.

El estado puede ser COMPLETE, REJECTED, INCOMPARABLE o RESOURCE_LIMITED. Un
presupuesto agotado conserva los cambios parciales que se hubieran observado,
pero no puede producir structurally_identical=true. Se limitan bytes de entrada,
nodos, profundidad, cambios y bytes de valores de salida. Es un presupuesto lógico,
no una medición industrial de memoria/CPU. El parser JSON también queda acotado
por el límite de bytes; RecursionError se trata como límite, no como igualdad.

## Garantías separadas

`structurally_identical` significa igualdad del IR canónico del perfil actual.
`semantic_equivalence` permanece NOT_CHECKED: yes y not(no) se registran como
estructuras diferentes aunque sean lógicamente equivalentes. No se decide
implicación, debilitamiento o suficiencia semántica general. `requires_review`
indica cambio o imposibilidad de completar la comparación; no es permiso de merge.
`normatively_admitted` es siempre falso. Los resultados son inmutables y
`diff_to_data` los expone mediante guardian/gsl0/contract-diff/v1.

Este módulo puede consumir la serialización del IR elaborado por el servicio
productivo. En esta entrega se ejercita directamente el contrato del comparador
con IR nominal construido por fixtures; no se afirma una nueva ejecución de todo
el frontend/elaborador ni del verificador externo.

## Pruebas y evidencia ejecutada

67 casos nuevos, con positivos, negativos, permutaciones, payloads malformados,
revocación de presupuesto, inmutabilidad y una prueba sin reloj/fs/red.
196 regresiones seleccionadas de identidad y frontend/IR/V0: 263 PASS en total,
0 FAIL, 0 SKIP, Python 3.13.5. La selección enumera explícitamente sus archivos
en el registro de ejecución; no incluye LC04/LC05/LC06 ni la suite total G-00.
Los 23 blobs de dependencias y pruebas seleccionadas coinciden con los publicados.

Se detectaron seis mutaciones dirigidas: omitir declaración borrada, ignorar
orden, omitir PO borrada, mezclar proyectos, elegir última revisión ambigua e
ignorar presupuesto de nodos. Son fallos de aserción, no errores de colección,
timeout o SKIP. Es autoauditoría del constructor, no otro actor.

El total 1598 comunicado antes de publicar el candidato integrado es histórico;
no se suma a 263 ni se presenta aquí como suite íntegra reejecutada. Los archivos
y registros de esta entrega están bajo docs/verification/GSL0_C12_*.

## Pendientes conservados

G-00: consolidar suficiencia B08 para 120 cláusulas, 36 adversarios y siete
verticales; no basta con enlazar tests. B09 sigue sin revisión independiente,
ratificación o recibo protegido. No se han ejecutado Python 3.12 ni tipado estático.
GSL: imports/módulos generales, reconciliación histórica del corpus, incrementalidad,
emisión y cualificación completas. C12 estructural no implementa G-01 Evolution
ni demuestra que una edición preserve todos los requisitos del proyecto.
