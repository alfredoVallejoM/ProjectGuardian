# G-00 / GSL-0 — Remediación A01–A03, D01, G01 y G02

Fecha: 2026-10-26. Base publicada: `9a673c4b5a83485c3c349ce0c36d2fa2791ebc2a`.
Estado: **REMEDIATED_SELECTED_EXECUTION**, no cierre de G-00/GSL.
Esta es autoauditoría del constructor. No hubo revisión por un actor distinto,
ratificación nueva, instalación protegida ni ejecución de GitHub Actions.

## 1. Rojo antes, verde después

Se reprodujo materialmente la revisión original: 44 tests del gate más 24 probes,
**52 PASS / 16 FAIL / 0 ERROR / 0 SKIP**. Los fallos son seis familias, no dieciséis
obligaciones independientes. Los tres archivos históricos de falsación y su
informe se conservan byte por byte en `verification/review_2026_10_26/`.

La selección final ejecutó **961 PASS / 0 FAIL / 0 ERROR / 0 SKIP** en Python
3.13.5: 780 regresiones recuperadas, 44 tests originales del gate, 63 tests de
emisión/rebuild, 24 casos activos de la revisión y 50 controles ampliados.
El registro lista exactamente los 31 archivos de tests ejecutados y los hashes
de los 25 módulos Guardian realmente cargados. Se comprobó la estabilidad de
las 77 entradas observadas antes/después de la ejecución.

**No es el checkout íntegro.** No se suman contadores históricos ni se atribuye
PASS a pruebas ausentes. La recuperación completa no estuvo disponible; las
operaciones del dominio constitucional, los codecs generales v2, el V0
contractual externo completo y B08 120/58/36/7 no se han reejecutado íntegramente.
La dependencia recuperada antigua de Q12 se reconcilió con su blob publicado
antes de la ejecución final: su falsación se conserva, no se debilitó el test.

## 2. G02 — Reconstrucción completa y formato fijado

`CompileContext.source_formats` fija la interpretación de cada fuente. Es una
tupla inmutable de pares referencia/formato y, si se utiliza, cubre exactamente
las fuentes fijadas. El mapa vacío conserva solo el perfil histórico de **GSL
crudo**; no autoriza a un análisis suministrado a escoger Markdown.

`FrontendAnalysis` conserva el formato declarado. `validate_analysis_source`
reconstruye extracción, scan, lexer, CST y AST desde todos los bytes originales,
y exige igualdad con el análisis suministrado. `resolve_analyses` ejecuta esa
comprobación antes de aceptar sus declaraciones. Tipado, elaboración, emisión,
reconstrucción de emisión y actualización vuelven a cruzar esta frontera.

Así se detectan tanto la eliminación de un fence normativo como la conversión
de un ejemplo en norma. Conservar una partición sin pérdida no basta. Se fijan
por separado los bytes y su interpretación; también se rechaza cambiar de
formato cuando los mismos bytes son sintácticamente válidos bajo ambos perfiles.
No se llama al V0 para construir el resultado ni se presenta esta reconstrucción
interna como un oráculo independiente.

El servicio que recibe bytes y `formats` fija ese mapa en el contexto; no permite
contradecir uno ya fijado. Los callers directos de Markdown deben suministrarlo.
La emisión conserva su formato de transporte v1: el mapa ya está representado
por los campos `sources[].source/format`, y el lector reconstruye y valida esa
correspondencia. El lector sigue comprobando transporte, no significado.

## 3. G01 — Inmutabilidad sobre el delta completo

Antes de modificar la población, `rebuild_program` compara todas las altas y
reemplazos con la población anterior completa. La misma referencia no puede
reaparecer con bytes o digest diferentes aunque el delta se exprese como baja
más alta y en cualquier orden. Tampoco puede cambiar de formato bajo la misma
referencia. Un cambio de contenido usa una nueva revisión y sus pins completos.

Se conservan positivos de cambios legítimos, incluidos Markdown con nueva
revisión, delta dividido y reconstrucción completa directa equivalente. Una
baja/alta idéntica sigue siendo un no-op válido. No hay reutilización de caché.

## 4. D01 — Validez del contenido, no solo isinstance

Los validadores de cortes exigen tipos nominales exactos y revalidan explícitamente
las invariantes de identidad, repositorio, digest y corte. No llaman hooks de una
subclase suministrada. El validador del universo hace lo mismo para cada corte
anidado antes de usarlo en catálogos o comprobar pertenencia.

También se prueban objetos del tipo exacto reconstruidos sin constructor con
commit mutable o versión documental vacía. Se devuelven diagnósticos con la ruta
del corte incorrecto; no se autentica la fuente ni se concede cobertura completa.

## 5. A01/A02/A03 — Correspondencia real de plan y ejecución

El plan pasa a `guardian/g00/acceptance-plan/v2`; los planes v1 no reciben un
resultado favorable con garantías nuevas implícitas. El recibo mantiene v1 porque
ya registraba la procedencia de módulos. El plugin existente no se modifica.

**A01.** La operación y el propietario deben corresponder a `function_name` y
`owner_path` del registro original fijado. Una adaptación es posible únicamente
mediante un registro explícito con origen, destino, examen de precondiciones,
postcondiciones y errores, y archivo de revisión vinculado a la ejecución.
La lista de adaptaciones necesita además un SHA-256 proporcionado separadamente
por el operador (`--api-adapters-sha256`). Esto comprueba la correspondencia
registrada, no demuestra equivalencia semántica ni autentica ratificaciones.

**A02.** Las propiedades de cada test son diccionarios de listas de strings
primitivos. El diagnóstico se coteja por igualdad exacta, nunca como subcadena.
Un escalar, una lista con tipos incorrectos o un código solo parecido se rechaza.

**A03.** El plan exige `expected_runtime_modules`: por nombre de módulo Guardian,
`source_path`, `sha256` y `allowed_paths`. El conjunto cargado debe coincidir con
el esperado, el archivo fuente debe estar entre las entradas fijadas y sus bytes
deben coincidir con los observados. Las rutas se validan y deben estar permitidas.
Una copia instalada fuera del checkout es legítima si está expresamente mapeada
y contiene los mismos bytes. Dos subprocesses reales comprueban el positivo y
el negativo: pytest pasa en ambos, pero el gate rechaza solo el código distinto.

Este control no protege frente a un runner que mienta, modificaciones transitorias
revertidas, monkeypatch deliberado de objetos en memoria o módulos no observados.
No firma ni autentica el recibo. Su salida máxima sigue siendo
`STRUCTURAL_EXECUTION_BINDINGS_CHECKED`, con campaña abierta, admisión falsa y
suficiencia semántica/revisión independiente no establecidas.

## 6. Pruebas preservadas y adaptaciones explícitas

Los probes históricos quedan fuera de la suite normal como evidencia del corte
rojo. Sus copias activas están en `tests/remediation/test_review_*_active.py`.
Las expectativas negativas se conservan; no se convierten en skip ni xfail.
La fixture Markdown activa añade el nuevo pin de formato, y la fixture del gate
usa el plan v2 con módulos esperados. Al alterar código para comprobar A01 se
actualiza también su pin runtime: el rechazo no depende de un hash obsoleto.

`test_boundary_repairs.py` añade 50 controles: ataques aislados con diagnósticos
precisos, adaptador explícito, instalación idéntica/diferente, revalidación de
payloads, deltas legítimos, mapas de formato y las seis fronteras públicas del
compilador. Los 44 tests previos del gate y 63 de emisión mantienen su intención.
Solo sus fixtures se adaptan donde las nuevas precondiciones lo requieren.
Un control adicional ejecuta la CLI desde fuera del checkout sin PYTHONPATH.

## 7. Mutaciones y reproducción

`tools/run_review_boundary_mutations.py` ejecuta nueve mutaciones en copias
temporales: nueve detectadas, cero supervivientes, cero runs inválidos en los
lotes registrados. Solo un AssertionError real en la fase call cuenta; errores
de colección, timeout y omisiones no sirven. La primera tentativa conjunta
agotó el límite de la herramienta y no cuenta como ejecución válida; se repitió
en tres grupos explícitos, cuyos nueve resultados están registrados.

```sh
PYTHONPATH=. python -m pytest -q tests/remediation tests/acceptance/test_execution_bindings.py tests/spec_lang/test_emission_rebuild.py
python tools/run_review_boundary_mutations.py --output /tmp/review-mutations.json
```

La suite seleccionada de 961 está enumerada en el JSON de ejecución; un `pytest
tests` en el checkout completo recoge otras pruebas que no forman parte de este
recibo. Los pins de fuentes y de las falsaciones históricas permiten verificar
qué se ejecutó sin sustituir autenticidad del runner ni revisión semántica.

## 8. Pendiente conservado

Las seis familias de defectos están remediadas dentro del perfil probado. Siguen
abiertos el replay íntegro de repositorio/paquete, la matriz semántica 120/58/36/7,
la aceptación B08/B09 y las etapas generales pendientes de GSL. Python 3.12,
comprobador estático, instalación protegida y revisión por otro actor: NOT_RUN.
No se ha reducido ninguna obligación ni ratificado el contrato de formato por
el hecho de implementar una protección. CTK-01 sigue fuera de alcance.
