# G00-B04 — ámbitos, aplicabilidad y testigos integrados

Fecha: 2026-10-24. Base: `1da717ffefb1fa3fa5e7d1a12dcb9e8746318d9a`.
Estado: `IMPLEMENTED_AND_LOCALLY_TESTED_CANDIDATE` del bloque B04.
Objetivo del programa: terminar G-00. No se amplía el alcance de GSL ni se
reescribe la especificación original para acomodar el código.

## 1. Se subsana primero la deuda de regresión completa

Se reconstruyeron los árboles exactos de código, pruebas y esquemas del padre:
`src=a76e144bf214fa1b7d5c849f18c832233a159942`,
`tests=f79ac61f80ea69ec198cdb462150f9bdef3e94ef`,
`schemas=d983ab5c47f6b15a03beda1bdc8ff1276e3de2d9`.
La base completa da **1071 PASS, cero FAIL y cero SKIP**. Incluye los 196 casos
de esquemas/reconciliación/V0 externo no reejecutados en la entrega anterior.
No se ha sumado su resultado histórico: se ejecutaron en esta revisión.

La suite final con B04 da **1214 PASS, cero FAIL y cero SKIP**: 1071 regresiones
más 143 casos nuevos. La suite completa se repitió sobre el wheel instalado en
un directorio aislado: 1214 PASS, con los 29 módulos Guardian importados desde
esa instalación. Python 3.13.5. compileall PASS.

## 2. Alcance funcional de G00-06-F01…F10

| Cláusula | Implementación y falsación |
|---|---|
| F01 | SupportProfile con contexto nominal fijado, dimensiones tipadas, registry versionado y extensiones informativas. Ausencia significa desconocimiento, no falso. |
| F02 | Atom/All/Any/Not y constantes explícitas; operadores igualdad/pertenencia/rango/presencia registrados. Rechaza vacíos, scripts, ciclos y profundidad excesiva. |
| F03 | ApplicabilityResult con V4, testigos positivos/negativos, contexto y diagnósticos; codec versionado conserva ambos soportes. |
| F04 | AND usa la tabla de soporte especificada; resultados y testigos comprobados contra tabla independiente. |
| F05 | OR/NOT conservan incertidumbre y contradicción. ScopeConflict retiene ambos testigos aunque el compuesto termine en YES o NO. |
| F06 | Ausencia de un miembro solo produce NO con dimensión completa y testigo de exhaustividad; un bool complete sin testigo se rechaza. |
| F07 | inspect_due calcula aplicabilidad sin modificar due, milestone ni aprobación. FUTURE aplicable sigue siendo FUTURE. |
| F08 | VerifierPredicate consume observación externa con misma versión/input digest/contexto. Sin ella devuelve UNKNOWN y no ejecuta callbacks. |
| F09 | Presupuesto explícito de pasos, nodos, profundidad, hechos y testigos; agotarlo devuelve RESOURCE_LIMITED sin valor de aplicabilidad. |
| F10 | Cada testigo conserva proyecto, revisión, perfil, universo y política; la ruta productiva comprueba fuente observada. No se acepta evidencia extranjera implícita. |

Las siete APIs 031…037 se materializan en `domain/scope.py`. API038 se amplía
con perfil, hechos, cuerpo ScopeRevision y presupuesto manteniendo la llamada
histórica de dos argumentos. El catálogo conserva sus 58 IDs y diferencia
40 nombres presentes de una declaración de 40 APIs completas.

## 3. Arquitectura y ruta productiva

`domain/scope.py` posee tipos, AST y evaluación pura. Reutiliza el álgebra V4,
no crea otro evaluador constitucional. `domain/scope_codec.py` serializa el
resultado de aplicabilidad, no todos los registros de dominio de B06.

`ScopeRevision` es un cuerpo real registrado en RecordSnapshot. El resolver
existente lo devuelve por identidad/revisión exactas. La obligación no toma
un scope implícito ni un anchor sin cuerpo como si estuviera implementado.

`application.contract_service.inspect_contract_applicability` conecta:

SourceUniverse/B02 -> obligación/B03 -> ScopeRevision/B06 -> evaluación/B04.

Comprueba la coincidencia de snapshot, universo, política y registro de tipos;
las fuentes de los hechos deben estar observadas y pertenecer al corte recibido.
La inspección conserva explícitamente los cuerpos que siguen ausentes, por
ejemplo VerificationSpec; no fabrica objetos ni declara integridad global.

El resultado separa aplicabilidad, exigibilidad declarada y admisión. Un resultado
COMPLETE significa que terminó la evaluación, no que una obligación esté cumplida.
`normatively_due` sigue sin determinar mientras no se compruebe aprobación.

## 4. Testigos y contradicción interna

Las operaciones V4 propagan los testigos que contribuyen al resultado. Además,
retienen ScopeConflict con soporte positivo y negativo para cada contradicción
interna. AND(CONFLICT,NO)=NO y OR(CONFLICT,YES)=YES no borran esas contradicciones.
No se realiza cortocircuito que oculte el conflicto de otro operando. El codec
preserva también las contradicciones retenidas.

Las constantes True/False necesitan una autorización contextual suministrada.
El constructor no autentica esa autorización: lo mismo que los hechos, es una
entrada del contexto de confianza externo. Tampoco se ofrece un mecanismo de
importación automática de testigos extranjeros ni se infiere autoridad por URI.

## 5. Autoauditoría y pruebas de comportamiento

Cinco pruebas adversarias fallaron en el primer candidato y se conservaron:
las dos composiciones de conflicto que ocultaban evidencia, una traza extranjera,
un schema hostil que ejecutaba igualdad y un informe completo con nodos pendientes.
Tras corregirlos, las cinco pasan. Esta es autoauditoría, no auditor independiente.

La suite nueva incluye los 16 pares de tablas AND/OR, negación, los cuatro valores
y sus codecs; 64 asignaciones sobre tres dimensiones con cinco expresiones
compuestas; permutaciones de hechos; límites exactos y un paso insuficiente;
características extensibles, fuentes limitadas, presupuestos y la integración
real con obligaciones actuales, futuras y de investigación.

Doce mutantes B04 dirigidos fueron detectados por fallos de aserción; cero
supervivientes y cero ejecuciones inválidas. Las dieciséis mutaciones Q previas
se reejecutaron y también se detectaron. Son 28 ataques dirigidos, no una campaña
exhaustiva ni una revisión por un actor distinto. El runner nuevo no cuenta
colección rota, timeout, SKIP o una excepción ajena como detección válida.

## 6. Trazabilidad, ejecución y límites de cierre

`verification/b04/scope_manifest.json` enlaza las diez cláusulas, ocho contratos
API y los cinco adversarios ADV-16…ADV-20 a pruebas ejecutadas y a sus fronteras.
El registro B00 se actualiza solo como proyección; architecture/ no se modifica.
El control de perfil inicial y el de reconciliación B00 pasan contra el JUnit
actual. Este último sigue en modo external-readback: los originales normativos
se leyeron en GitHub y se preservan por árbol base; no se afirma un gate local de
bytes originales que no estaban todos materializados. La suite de tests sí está
íntegra y fue verificada frente al árbol Git original antes de añadir B04.

No se ha ejecutado Python 3.12, un comprobador estático de tipos, una instalación
externa protegida ni un auditor independiente. No se ratifican decisiones.

## 7. Lo que sigue para terminar G-00

B05: modelos de reglas/decisiones/constitución, contexto de autoridad, conflictos,
precedencia parcial y propuestas de enmienda. B06: cuerpos restantes y codecs
versionados completos. B07: evaluador constitucional puro que componga lo anterior
sin perder reglas ni testigos. B08: completar la matriz de 120 contratos, 36 ataques
y siete verticales integrales. B03 conserva además su flujo general de borradores
pendiente. B09 aporta la revisión y cualificación exigidas, no más alcance implícito.

La implementación de B04 no certifica el conjunto G-00. El siguiente bloque debe
aprovechar este motor de ámbitos y el resolver ya construido, no duplicarlos.
