# B00 / GSL0-LC00..LC02 — cierre parcial de entregables técnicos

Fecha: 2026-10-24. Base: `9fcc6cb0be8bccdc8729b9c4828fb14c3bce71c7`.
Estado: `PARTIAL_TECHNICAL_HANDOFF_VALIDATED`. No es cierre de B00, de G-00,
de LC00 completo ni de GSL-0. No se añaden aprobaciones ni campañas canónicas.

## Entregables efectivamente terminados

1. **Perfil técnico candidato fijado.** `verification/initial_milestone_profile.json`
   fija las versiones, las 15 etapas C00-C14, los estados, los tipos nominales,
   los ocho tipos de declaración IR, sus campos requeridos y tipos de referencia.
   Conserva los pins de las fuentes originales y el denominador 12/120/58/36/7.
   Es el perfil implementado que se propone aceptar; no recorta el lenguaje ni
   sustituye decisiones originales pendientes. El documento inicial C00-C13 se
   conserva histórico; el ABI de 15 etapas coincide con el manifiesto JSON.
2. **Aceptación ejecutable del perfil.** `tools/check_initial_milestone.py` contrasta
   el perfil fijado externamente, el runtime y el JUnit real. Hay 18 condiciones
   subordinadas a LC00/01/02 enlazadas a 24 funciones de prueba. Detecta deriva de
   versiones, campos o referencias y pruebas ausentes, fallidas u omitidas.
   Un PASS valida coincidencia de perfil y ejecución, no suficiencia de todos los
   refinamientos originales ni autenticidad del JUnit. El ejecutor debe producir
   ese JUnit sobre el candidato cuyo árbol de archivos registre.
3. **V0 externo para el fragmento finito.** `verification/external_v0/worker.py`
   usa exclusivamente la biblioteca estándar. No importa Guardian, sus tipos,
   su lexer/parser ni su VM. Recibe bytes UTF-8, una expectativa fijada por el
   operador y fórmulas IR como JSON. El operador, no el candidato, selecciona los
   IDs y los spans. Una implementación de tablas interpreta la fuente y otra
   mediante bits interpreta el IR; enumera todas las valoraciones admitidas.
4. **Lanzamiento con versión fijada.** `tools/run_external_v0.py` exige el SHA-256
   del worker y de la expectativa. Verifica y ejecuta el buffer de código ya leído
   con Python `-I -S`, desde un directorio temporal; no vuelve a abrir el worker
   tras comprobar su hash. Un cambio de worker, fuente o expectativa bloquea la
   ejecución positiva. Hay límites de entrada, profundidad, población, átomos,
   valoraciones por fórmula y agregado, además de timeout del proceso.

## Frontera que NO se ha cerrado mediante una abreviatura

El worker externo devuelve `PINNED_FORMULAS_ONLY`. Nunca afirma equivalencia
completa de un contrato. Correspondencia de declaraciones, integridad de
referencias, cobertura histórica y admisión permanecen `NOT_CHECKED`.
El V0 interno remediado sigue siendo necesario para comparar declaraciones y
campos completos: NO se sustituye por el worker externo. La prueba de integración
muestra que un scope alterado puede conservar la equivalencia de fórmula, pero
el verificador de contrato lo rechaza y ninguno emite una cualificación global.

La expectativa externa debe proceder del operador/revisor, no generarse desde
el mapa del candidato como supuesto oráculo independiente. Un hash que el propio
candidato suministra junto al artefacto no constituye confianza. Los hashes del
handoff identifican bytes; no autentican al autor ni son firmas.

La separación de procesos ha sido ejecutada localmente. La instalación bajo
cuenta/permisos externos protegidos, la revisión por otro actor y su aprobación
siguen pendientes. `-I -S` no es un sandbox de sistema operativo. No se simula
la instalación de G-09 ni se confunden controles locales con una raíz de confianza.

## Reconciliación de salida original de B00

| Entregable original | Estado tras este cambio | Pendiente exacto |
|---|---|---|
| Preservar las doce obligaciones y sus refinamientos | Base fijada conservada | No equivale a suficiencia semántica |
| Dictamen de suficiencia de las 120 cláusulas respecto a sus padres | OPEN | Dictamen íntegro y tratamiento explícito de enmiendas |
| Fijar APIs y envelopes | PARTIAL | Perfil actual fijado; reconciliar las 58 APIs y envelopes generales |
| Ratificar o mantener HOLD de decisiones | EXTERNAL_DECISION | 24 DD y ADR superiores sin aprobaciones nuevas |
| Congelar snapshot normativo aprobado | NOT_CLOSED | Perfil técnico candidato fijado, no aprobación normativa |
| Preparar V0 externo | PARTIAL | Ejecutor finito externo listo; ampliar correspondencia y proteger instalación |

Por tanto, sí se cierran estos entregables técnicos concretos. B00/LC00 globales
siguen abiertos por causas identificadas, no por una espera vaga de certificación.
LC01 conserva su IR productivo; LC02 dispone ahora además de ejecución externa
real del fragmento. LC04-LC09 no se proclaman implementados con estas herramientas.

## Evidencia ejecutada

Python 3.13.5. Base intacta: 691 PASS. Suite con los nuevos controles: **780 PASS,
0 FAIL, 0 SKIP**; 89 casos nuevos. Perfil: 18 condiciones, 24 funciones enlazadas,
780 casos en el JUnit real, PASS. `compileall` sobre src/tests/tools/worker PASS.
Las 16 mutaciones semánticas dirigidas previas vuelven a ser detectadas; no se
consideran errores de colección, timeout o skip como detección válida.

Los positivos y ataques se ejecutan también como procesos aislados. Incluyen
worker modificado antes de ejecutarlo, pins alterados, población de fórmulas
reducida/ampliada, spans falsos, comentarios, constantes true/false, Unicode,
profundidad y presupuesto agregado. Una prueba introduce un paquete guardian
hostil en PYTHONPATH y comprueba que no se importa.

No se ha ejecutado revisión independiente, Python 3.12 ni análisis estático de
tipos. No hay atestación firmada. Los contadores describen casos de prueba, no
porcentajes de obligaciones completadas.

## Reproducción

Ejecutar la suite del checkout y emitir JUnit:

```sh
python -m pytest -q --junitxml=initial-milestone.xml
python tools/check_initial_milestone.py --root . \
  --profile verification/initial_milestone_profile.json \
  --expected-profile-sha256 <HASH_FIJADO_POR_EL_OPERADOR> \
  --junit initial-milestone.xml
```

El hash de distribución del perfil figura en `INITIAL_PROFILE_SHA256.txt`.
La expectativa V0 tiene schema `guardian.external-v0-expectation/v1`, profile,
source_sha256, expressions [{id,start,end}] y limits {max_atoms,max_valuations,
max_total_valuations}. El candidato contiene schema
`guardian.external-v0-candidate/v1` y formulas [{id,formula}]; cada fórmula tiene
op, name y args. La expectativa NO es un campo del candidato.

```sh
python -I -S tools/run_external_v0.py \
  --worker /ruta/externa/worker.py --expected-worker-sha256 <HASH_EXTERNO> \
  --source fuente.gsl --expectation expectativa.json \
  --expected-expectation-sha256 <HASH_DE_EXPECTATIVA_EXTERNO> \
  --candidate formulas-candidatas.json
```

Mantener launcher, worker y pins bajo el control de quien verifica. El creador
del candidato no debe poder sustituirlos. El código de producción en `src/`
y los registros originales de `architecture/` no se modifican en este corte.
