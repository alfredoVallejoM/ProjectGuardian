# G00-02: proyecto y aislamiento — único frente activo

Predecesor: cierre técnico de G00-01 publicado en `c4e7c83c9cb4c6dcc069182febb30e3bb3b10e0d`. Este tramo **no cierra G00-02 ni abre G00-03**.

## Contrato y reparación

Se releyeron el detalle original de proyectos/fuentes, las diez cláusulas G00-02 y el catálogo. El alcance contiene seis APIs: 009, 010, 011, 012, **016** y 057. No basta comprobar ProjectDefinition; debe conservarse la autoridad al construir vistas, consultar fuentes e importar cortes.

La base aceptaba objetos del tipo correcto con datos reconstruidos inválidos. Se reprodujeron 31 casos fallidos y siete controles positivos. La reparación reutiliza los validadores base de identidad y valida todo el descriptor de proyecto, su política, referencias y repositorios. Se comprueba que StorageMode sea un miembro real, no un str-enum fabricado; el mapa de autoridad tiene claves primitivas y repositorios válidos antes de compararlos.

validate_project y validate_storage_mode no llaman validadores definidos por subclases ni consultan su metaclase al generar el diagnóstico. check_project_membership revalida proyecto y referencia antes de decidir pertenencia. La propiedad permitted_source_repositories tampoco expone permisos derivados de un descriptor inválido. Las firmas se conservan.

EMBEDDED sigue teniendo un repositorio de autoridad único; SIDECAR conserva su repositorio de gobierno separado; FEDERATED mantiene autoridad explícita por clase y repositorios distintos. Cambiar el nombre no cambia identidad/constitución. Revisar la política exige referencia y cuerpo concordantes. La pertenencia al namespace **no** comprueba existencia del cuerpo ni autentica un import.

Los códigos externos históricos PROJECT_SNAPSHOT_INVALID, UNSUPPORTED_STORAGE_MODE e INVALID_PROJECT_REFERENCE se conservan; la causa original queda en reason. La reconciliación exhaustiva de diagnósticos del catálogo permanece en la aceptación pendiente, no se declara resuelta por coincidencia de nombres.

## Ejecución

Misma batería nueva: **7 PASS / 31 FAIL** sobre la base exacta; **38 PASS** tras reparar. Selección conjunta: **139 PASS, cero FAIL/ERROR/SKIP** (38 nuevos + 67 regresiones de identidad + 34 controles del expediente). Python 3.13.5. Nueve mutaciones dirigidas detectadas mediante aserciones, sin contar errores de colección o timeouts.

La primera tentativa P06 produjo un error del formateador de pytest al consultar una metaclase hostil; no se contó como detección. El ataque ahora registra la llamada y exige que no se produzca, de modo que la retirada de la protección falla por aserción. MUTATIONS_INITIAL.json conserva ese intento.

**No es la suite íntegra ni el paquete instalado actual.** No se transfieren los 1.974 PASS históricos al project.py modificado. El cierre de G00-01 conserva su candidato fijado; sus regresiones pertinentes se repiten y una regresión reabre la obligación afectada.

## Próximo trabajo, sin cambiar de obligación

Completar construcción e inspección de vistas reales, importaciones exactas, fuentes de SIDECAR y cortes independientes de FEDERATED, contextos constitucionales y codecs, y juicio del padre con todas sus postcondiciones. La matriz enumera las diez cláusulas y sus pendientes. No se permite saltar a G00-03.

```sh
python -m pytest -q tests/g00_02
python verification/g00_02/run_project_mutations.py --output /tmp/g00-02-mutations.json
```
