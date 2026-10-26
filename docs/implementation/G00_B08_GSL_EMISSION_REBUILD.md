# G-00 B08 y GSL: ejecución enlazada, emisión y reconstrucción segura

Fecha: 2026-10-26. Base: `57539a9d4fe6727831629c226e630b2dc5443b4d`.
Estado: **IMPLEMENTED_SELECTED_EXECUTION**, no cierre de G-00 ni GSL-0.
Los originales de architecture/, los 12 padres, 120 cláusulas, 58 APIs,
36 adversarios y siete verticales se conservan sin modificación.

## 1. Desarrollo de G-00 B08

`tools/g00_acceptance.py` comprueba un plan de aceptación y un recibo cuyos
SHA-256 proporciona el operador separadamente. No acepta un hash autoafirmado
como prueba de autenticidad. Lee los tres registros originales de cláusulas,
APIs y validación, exige sus Git blob pins y compara las poblaciones por ID,
no solo sus tamaños. Cada fila enlaza el contenido original mediante hash,
implementación, pruebas positivas y falsaciones distintas; los padres conservan
su examen de conexión entre cláusulas. Los adversarios requieren diagnóstico
reconciliado y observación de ese diagnóstico en el registro de ejecución.

Compara la colección esperada completa con los nodeids realmente recogidos,
incluidas parametrizaciones. Setup, call y teardown deben pasar por separado;
SKIP, XFAIL/XPASS, deselección, fallo de colección, repetición de una fase o test
ausente impiden un resultado favorable. También fija los archivos de entrada
esperados, contrasta los hashes antes/después y vuelve a leer sus bytes actuales.
Un contador verde no sustituye ninguna de esas comprobaciones.

`tools/pytest_g00_receipt.py` captura fases, propiedades de prueba, colección,
archivos y módulos Guardian cargados. Es un plugin del runner, NO del dominio.
No firma ni autentica el recibo. Las instantáneas antes/después no demuestran
que no hubo una modificación transitoria revertida durante la ejecución: la
protección efectiva del runner sigue siendo responsabilidad del operador.

La salida máxima es `STRUCTURAL_EXECUTION_BINDINGS_CHECKED`. Mantiene siempre
`campaign_closed=false`, `semantic_sufficiency=NOT_ESTABLISHED_BY_LINK_CHECK`,
`receipt_authenticity=NOT_CHECKED` e `independent_review=NOT_CHECKED`.
Un texto de revisión presente tampoco demuestra que su contenido sea correcto.

**No se ha fabricado un plan que declare reconciliadas las 120 cláusulas.** Los
44 casos nuevos prueban el comprobador con autoridades y recibos sintéticos
explícitos y con un subprocess pytest real que pasa, falla y omite casos. Esos
fixtures NO cuentan como tests de los 120 contratos del producto. La aceptación
semántica exhaustiva B08 y su ejecución sobre checkout íntegro siguen abiertas.

### Uso en un checkout íntegro y con un plan ya revisado

```sh
python -m pytest -p tools.pytest_g00_receipt --g00-receipt=/tmp/g00-run.json
python tools/g00_acceptance.py --root . --plan /operator/g00-plan.json \
  --receipt /tmp/g00-run.json --plan-sha256 "$OPERATOR_PLAN_PIN" \
  --receipt-sha256 "$OPERATOR_RUN_PIN"
```

El plan identifica `schema=guardian/g00/acceptance-plan/v1`, `campaign=G-00`,
`original_git_blobs`, `expected_collection`, `expected_input_files`, `parents`,
`clauses`, `apis`, `attacks` y `verticals`. Cada fila no padre contiene `id`,
`original_sha256`, `code_paths`, `positive`, `negative` y `contract_review`.
Una cláusula añade `parent`, una API `owner/operation`, un ataque
`expected_diagnostic`; cada padre conserva `bridge_review`. Las pruebas de
ataques pueden usar `record_property('guardian.diagnostic', observed.code)`.
Esto registra lo observado; no vuelve independiente al autor de la prueba.

## 2. Emisión productiva de GSL

`spec_lang/emission.py` y `application.specification_service.emit_sources`
conectan bytes originales, frontend, resolución, tipado y elaboración con un
bundle inmutable `guardian/gsl0/emission/v1`. Se conserva `elaborate_sources`.
La etapa emitida es **C14_BUNDLE_EMIT**, conforme al ABI C00–C14 existente;
no se renumera el ABI por la nomenclatura C13 del documento de diseño anterior.

El bundle conserva fuentes UTF-8 exactas (también Markdown, trivia y CR/LF/CRLF),
refs y digests originales, identidad del compilador, registries y símbolos,
versiones, contratos canónicos, mapas de origen, referencias source_item no
reconciliadas y PO pendientes. SourceDigest, ContractDigest y CompilationDigest
se mantienen diferentes. Orden semántico y multiplicidades del IR no se borran.

Antes de emitir se vuelve a elaborar desde las fuentes. Un ElaboratedProgram
suministrado que cambia fórmula, mapa o source_item se rechaza, aunque mantenga
forma nominal y hashes coherentes. Todas las PO emitidas permanecen UNPROVEN.
No se transforman los ejemplos Markdown en declaraciones normativas.

`read_emission` contrasta primero el digest esperado externamente, luego JSON
estricto y canónico, fuentes, poblaciones, contextos, contratos, mapas y PO.
**Es integridad de transporte, no equivalencia semántica.**
`verify_emission` reconstruye desde un TypedProgram suministrado y compara los
bytes. La prueba adversaria recalcula los hashes de una fórmula alterada: puede
pasar la integridad de transporte, pero no la reconstrucción desde la fuente.
Esta comprobación reutiliza el compilador productivo; NO es un nuevo V0
independiente. El V0 autónomo anterior se conserva sin cambios.

El resultado es `EMITTED_FIXED_PROFILE`, no una certificación global COMPILED.
Sus límites permanecen dentro del propio bundle: admisión y cualificación falsas,
suficiencia no demostrada, source_items no reconciliados y autenticación externa
no comprobada. La revisión del snapshot externo se registra, pero sus cuerpos
normativos/dependencias no se exportan como pins autenticados: `NOT_EXPORTED`.
El bundle no reemplaza esos inputs de confianza ni habilita imports generales.

## 3. GSL-T08/T10: cambios fijados y reconstrucción completa

`spec_lang/rebuild.py` aporta SourceChange y `rebuild_program`: añadir, retirar
o reemplazar fuentes de forma atómica en memoria. Exige ref y digest anteriores,
población nueva coincidente con el contexto, ausencia de colisiones y otra
revisión cuando cambian los bytes. Un cambio inválido nunca devuelve IR anterior
como si representara la fuente nueva. Una fuente retirada que seguía siendo
referenciada produce rechazo de resolución, no un enlace obsoleto.

La estrategia es **FULL_REBUILD_NO_CACHE_REUSE**. Se ejecuta de nuevo el recorrido
existente completo; no se anuncia optimización incremental ni análisis de impacto
selectivo. Las pruebas comparan el resultado con compilación completa directa,
incluidas adiciones, bajas, cambios semánticos y permutaciones de fuentes.
Snapshot, importaciones y bindings externos mantienen el contexto del programa
anterior; cambiar esos cuerpos requiere una compilación nueva explícita.

`source_from_chunks` recompone bytes acotados antes de decodificar UTF-8, de modo
que un corte dentro de un carácter o entre CR/LF no pierde información. Comprueba
el digest externo. No se presenta como parser streaming ni memoria constante.

## 4. Ejecución material de esta entrega

Python 3.13.5: **887 PASS, cero FAIL/ERROR/SKIP**. Son **780 regresiones exactas
seleccionadas + 107 casos nuevos** (63 GSL, 44 del control B08). Veintiocho archivos
de tests/fixtures previos coinciden con sus blobs publicados. Los 25 módulos
Guardian importados en la ejecución corresponden a 22 dependencias exactas de
la base y tres archivos de esta entrega. Entradas antes/después sin cambios.

Doce mutaciones dirigidas se detectan por AssertionError real registrado mediante
un hook de pytest, no por buscar una cadena en un traceback. Cero supervivientes
y cero ejecuciones inválidas en la ejecución final. No cuentan errores de colección,
timeouts o SKIP. Son mutaciones dirigidas, no auditor independiente ni exhaustividad.

**No se ha reejecutado todo el repositorio.** La copia de trabajo se reconstruyó
parcialmente desde artefactos y lecturas Git verificadas. Una tentativa de colección
global encontró dependencias no recuperadas; no se atribuye ese problema de copia
al producto. Tampoco se cuentan archivos antiguos no cargados como código del
candidato validado. El registro lista exactamente las pruebas y dependencias
utilizadas. Las cifras históricas de 1598 o de la entrega C12 no se suman al PASS.
El control B08 contra todos los originales reales permanece NOT_RUN.

No se han ejecutado paquete instalado, Python 3.12, mypy/pyright, revisión por otro
actor ni instalación externa protegida en esta entrega. No hay ratificación nueva.

## 5. Pendientes conservados

G-00: revisión de suficiencia conjunta 120/36/7, postcondiciones de las 58 APIs,
regresión del checkout íntegro, corrección de los hallazgos que esa revisión
revele y B09. Este control evita cierres sin evidencias; no termina ese examen.

GSL: imports/módulos generales, reconciliación histórica del corpus G00,
exportación/verificación independiente de dependencias de contexto, optimización
incremental si se pretende, aceptación global LC00–LC12 y cualificación. La emisión
y el fallback de reconstrucción del perfil actual sí tienen código y tests reales.
CTK-01 permanece fuera de alcance. No se modifican las obligaciones originales,
no se crean ramas y no se utiliza GitHub Actions.
