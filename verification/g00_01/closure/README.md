# G00-01: cierre técnico de desarrollo

Fecha: 29 de octubre de 2026. Candidato aceptado: `f33c700d1bb2310662e7bc58b511f8b17ef6a6cc`.

**DEVELOPMENT_CLOSED.** Se acepta el desarrollo de las diez cláusulas, ocho APIs y tres adversarios de G00-01, junto con la conexión del padre. Se permite activar G00-02; no se cierran G00-02…12 ni la campaña G-00. Esta es una revisión adversaria del constructor, no un auditor independiente ni una ratificación de decisiones de diseño. B09 permanece separado.

## Evidencia material conservada y comprobación nueva

Los dos recibos anteriores contienen 1.974 casos cada uno, todos con setup/call/teardown aprobados, cero omisiones, deselecciones, XFAIL/XPASS o errores de colección. Comparten colección y 150 entradas estables. Los 52 módulos de la segunda ejecución proceden de una instalación aislada y coinciden en bytes con las fuentes fijadas. Los árboles completos de src (52 archivos), tests/fixtures (68) y schemas (5) declarados en la ejecución coinciden con los árboles del commit leídos nuevamente en GitHub.

La revisión actual **no vuelve a ejecutar esos 1.974 casos**. Reconstruye sus dos streams JSON exactos y comprueba hashes, población, fases, procedencia de módulos, enlaces y veinte mutaciones dirigidas. Añade una ejecución real de 67 regresiones de identidad y 34 controles del expediente: **101 PASS**. Estos contadores no se suman al resultado histórico.

Los recibos son observaciones sin firma, no autenticación del ejecutor. El expediente conserva sus rutas e invocaciones históricas; no pretende que una ruta histórica exista en otra máquina.

## Hallazgos corregidos del expediente

C01: API-005 enlazaba el mismo test como positivo y negativo. El control lo rechazó. Se mantiene el positivo y se enlazan dos negativos distintos ya ejecutados: payload nominal inválido y metaclase hostil. No se cambia ningún test productivo ni su expectativa.

C02: el resumen histórico fijaba el acta local previa (`e9944bd0…`); el acta publicada tenía otro hash (`da8fa2bb…`) por sus metadatos de publicación. Se reconstruyó el blob publicado `8481c8e806ba127b50da0c3dd6b6808607ad9606`, se verificaron sus 25 selectores en ambos recibos y se conservó la genealogía explícita en ACCEPTANCE.json. No se reemplaza un pin externo por una afirmación del candidato.

Los controles adversarios eliminan/duplican casos y cláusulas, introducen SKIP o fallo de fase, deselección, ejecución parcial, módulo ajeno, digest distinto, enlace no ejecutado, falsación ausente, mutación interrumpida, cambios de originales y promociones a firmado/independiente. Todos deben producir HOLD. Un pin correcto por sí solo no reemplaza estas comprobaciones.

## Juicio semántico del padre

F01–F03: wrappers exactos y valores anidados revalidados preservan clase, proyecto y gramática. F04–F05: alias y localización no son identidad; procedencia y ambigüedad quedan explícitas. F06: el cuerpo sale de la población real del snapshot, no de un cache manipulable, sin latest o placeholder. F07: digest conserva algoritmo y longitud. F08: generación queda fuera del dominio puro. F09: codecs preservan discriminantes y rechazan omisiones. F10: colisiones no sobrescriben ni fusionan linajes.

La conexión alias -> codec -> resolver se prueba sobre registros reales. El contraejemplo de un cache que conserva la referencia pero sustituye el cuerpo está cubierto. Las adaptaciones de API-005/006 y los errores específicos de imports en API-008 están documentados, sin cambiar las especificaciones originales. Una prueba finita no es un teorema universal; el juicio acepta el contrato del perfil implementado, no cualquier sistema posible.

## Reproducción del expediente

```sh
python verification/g00_01/closure/audit_receipts.py \
  --package verification/g00_01/closure/PAIRED_RECEIPTS.json.xz.b64 \
  --acceptance verification/g00_01/ACCEPTANCE.json \
  --pins verification/g00_01/closure/PINS.json
python -m pytest -q verification/g00_01/closure/test_dossier.py
```

Las tres partes son almacenamiento textual sin pérdida. `reconstruct()` recupera exactamente los JSON de los recibos originales; los hashes esperados están en PINS.json. No contienen código ejecutable ni sustituyen las filas por un contador. Los pins deben seleccionarse desde un commit fijado: el comprobador no autentica su propio archivo PINS.

## Límites y reutilización

Python 3.12, comprobador estático, auditor distinto, firma y runner protegido siguen NOT_RUN/no establecidos. La documentación histórica completa no estuvo toda materializada; no se atribuye aceptación de 120/58/36/7 al PASS de la suite. Los tests publicados de V0/constitución/codecs son regresión de consumidores, no cierre de sus obligaciones.

Este commit de cierre no altera src, tests, schemas ni architecture. Por ello conserva el perímetro del candidato ejecutado. Cambios posteriores requieren analizar impacto y ejecutar regresiones; no heredan automáticamente estos 1.974 PASS. Una regresión de identidad reabre G00-01.
