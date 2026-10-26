# Disposición de las 120 cláusulas — revisión 55fe58a2

Esto es una matriz de revisión de contratos, no 120 certificaciones ni 120 fallos. Las filas sin falsación nueva conservan la implementación/evidencia histórica y su aceptación integral pendiente.

## G00-01 — Identidades

| Cláusula | Contrato | Trabajo de aceptación/corrección |
|---|---|---|
| G00-01-F01 | Identidades nominales | Cruzar tipos nominales en parsers y codecs sin coerción |
| G00-01-F02 | Namespace y clase | Mismo valor en proyectos y clases distintas no colapsa |
| G00-01-F03 | Gramática estable | Ejercitar todos los límites léxicos y los errores de entrada |
| G00-01-F04 | Alias separado | Permutar bindings ambiguos sin elegir el primero |
| G00-01-F05 | Renombrado conservador | Cambiar alias y ruta conservando la identidad lógica |
| G00-01-F06 | Revisión pinneada | Conservar revisión exacta tras codec y resolución |
| G00-01-F07 | Digest con algoritmo | Cambiar algoritmo, longitud y digest sin equivalencia falsa |
| G00-01-F08 | Generación exterior | Comprobar ausencia de tiempo, aleatoriedad y E/S |
| G00-01-F09 | Roundtrip de tipos | Roundtrip de todas las variantes, no solo strings |
| G00-01-F10 | Colisiones explícitas | Duplicados con cuerpos/linajes diferentes no sobrescriben |

## G00-02 — Proyecto

| Cláusula | Contrato | Trabajo de aceptación/corrección |
|---|---|---|
| G00-02-F01 | Identidad del proyecto | Renombrar sin cambiar ProjectId ni constitución |
| G00-02-F02 | Fuentes autorizadas | Allowlist y repositorio de autoridad no aceptan fuentes arbitrarias |
| G00-02-F03 | Tres modos | Ejercitar EMBEDDED/SIDECAR/FEDERATED de fuente a consumidor |
| G00-02-F04 | Selección explícita | Intercalar dos proyectos sin estado global |
| G00-02-F05 | Importaciones explícitas | Contextos de importación explícitos, sin autoaprobación |
| G00-02-F06 | Granularidad de import | Pruebas positivas y negativas por corte/ruta/entidad |
| G00-02-F07 | Versión de política | Misma referencia con otro cuerpo de política se rechaza |
| G00-02-F08 | Federación | Revisiones independientes por repositorio |
| G00-02-F09 | Alias no global | Mismos nombres humanos permanecen aislados |
| G00-02-F10 | Proyecto inmutable | Probar no mutación de estructuras e índices |

## G00-03 — Fuentes

| Cláusula | Contrato | Trabajo de aceptación/corrección |
|---|---|---|
| G00-03-F01 | Git inmutable | D01: rechazar subclase con commit main en validador y universo |
| G00-03-F02 | Documento versionado | D01: rechazar subclase documental sin versión |
| G00-03-F03 | Inclusiones | Cambiar include set exige revisión coherente; no reinterpretar historia |
| G00-03-F04 | Exclusiones justificadas | Reejecutar R02 por cada fuente/universo/acción y decisión exacta |
| G00-03-F05 | Fuentes ausentes | Mantener known_missing y MISSING en todos los informes |
| G00-03-F06 | Cortes solapados | Revisar alias materiales, baselines, ciclos y solapamientos de rutas |
| G00-03-F07 | Niveles de adquisición | IDENTIFIED/OBSERVED/RECONCILED no son equivalentes |
| G00-03-F08 | Fuente versus autoridad | Una fuente observada no se convierte en decisión |
| G00-03-F09 | Cobertura delimitada | No inferir completitud del conjunto ya registrado |
| G00-03-F10 | Metadatos de alcance | Mantener denominadores, exclusiones y límites en el servicio |

## G00-04 — Autoridad

| Cláusula | Contrato | Trabajo de aceptación/corrección |
|---|---|---|
| G00-04-F01 | Estados de decisión | Cubrir todos los estados y ausencia de aprobación externa |
| G00-04-F02 | Approval distinto | Cambiar cuerpo bajo misma ref no reutiliza aprobación |
| G00-04-F03 | Regla versionada | Regla sin ámbito/versión no entra como cumplida |
| G00-04-F04 | Hecho frente a norma | Observación no reescribe norma aprobada |
| G00-04-F05 | Contexto confiable | Contexto externo y acciones específicas, no JSON autoautenticado |
| G00-04-F06 | Precedencia autorizada | Supersesión por acción, ámbitos y revisiones exactos |
| G00-04-F07 | Sin prioridad temporal | Reordenar/fechar/rehash no selecciona ganador |
| G00-04-F08 | Dependientes de conflicto | Conservar población fijada y todos los dependientes pertinentes |
| G00-04-F09 | Scope de decisiones | Aislamiento de proyecto y de ámbito de aprobación |
| G00-04-F10 | Enmienda como propuesta | Enmienda no muta ni ratifica el contrato anterior |

## G00-05 — Compromisos

| Cláusula | Contrato | Trabajo de aceptación/corrección |
|---|---|---|
| G00-05-F01 | Objetivo autónomo | Objetivo no hereda estado de task |
| G00-05-F02 | Capacidad funcional | Archivo vacío no acredita capacidad |
| G00-05-F03 | Propiedad independiente | Compartir propiedad sin duplicación ni prueba fabricada |
| G00-05-F04 | Obligación exigible | Borrador completo solo produce PROPOSED; comprobar authority |
| G00-05-F05 | Aceptación y falsación | Acceptance y falsification significativas y explícitas |
| G00-05-F06 | Verification separada | VerificationSpec no genera ValidationRun |
| G00-05-F07 | Arquitectura normativa | Imports observados no reformulan dependencias permitidas |
| G00-05-F08 | Campaign membership | Misma obligación y revisión compartidas entre campañas |
| G00-05-F09 | Muchos-a-muchos | Relaciones múltiples legítimas con resolver real |
| G00-05-F10 | Investigación separada | Research/Future no pasan a Current por evaluación de scope |

## G00-06 — Aplicabilidad

| Cláusula | Contrato | Trabajo de aceptación/corrección |
|---|---|---|
| G00-06-F01 | Perfil multidimensional | Dimensión ausente permanece desconocida |
| G00-06-F02 | AST acotado | Aridades, operadores, ciclos y callbacks no admitidos |
| G00-06-F03 | Cuatro valores | Preservar los cuatro valores y ambos testigos |
| G00-06-F04 | Conjunción precisa | Tabla completa AND con testigos |
| G00-06-F05 | Disyunción y negación | OR/NOT conservan conflictos internos aunque final sea decisivo |
| G00-06-F06 | Dimensión completa | Ausencia solo implica NO con testigo de completitud |
| G00-06-F07 | Due separado | Aplicabilidad no activa hito ni aprobación |
| G00-06-F08 | Predicado externo | Sin observación fijada no ejecutar ni aceptar verificador |
| G00-06-F09 | Presupuesto explícito | Presupuesto exacto y reglas/nodos pendientes visibles |
| G00-06-F10 | Testigos scoped | Proyecto/revisión/perfil/fuente se cotejan también en codecs |

## G00-07 — Estados

| Cláusula | Contrato | Trabajo de aceptación/corrección |
|---|---|---|
| G00-07-F01 | Ejes nominales | Matriz cruzada de los nueve ejes en parse/encode/decode |
| G00-07-F02 | Fuente separada | Estado de fuente no modifica implementación |
| G00-07-F03 | Decisión y compromiso | PROPOSED y FUTURE no conceden Current |
| G00-07-F04 | Implementación y ejecución | DEVELOPED puede coexistir con NOT_RUN |
| G00-07-F05 | Auditoría propia | Label Audit PASS no autentica revisión independiente |
| G00-07-F06 | Soporte y cualificación | No emitir certificado desde G00 por observar status |
| G00-07-F07 | Migración independiente | Prueba unitaria no cierra paridad de migración |
| G00-07-F08 | Observación no autoridad | Conservar procedencia y scope; no admitir completed editable |
| G00-07-F09 | No confundir NOT_RUN | Distinguir NOT_RUN, FAIL, PASS y SKIP |
| G00-07-F10 | Renderer honesto | Mostrar nueve dimensiones y límites en consumidores |

## G00-08 — Referencias

| Cláusula | Contrato | Trabajo de aceptación/corrección |
|---|---|---|
| G00-08-F01 | Ref completa | Referencia normativa requiere revisión explícita |
| G00-08-F02 | Comprobación de clase | Expected_kind no se deduce del texto |
| G00-08-F03 | Snapshot exacto | Histórico no se convierte en current ni latest |
| G00-08-F04 | Alias ambiguo | No first-result-wins |
| G00-08-F05 | No ciclos genéricos | Permitir ciclos de relación legítimos sin imponer DAG universal |
| G00-08-F06 | Grant scoped | Importar una entidad no concede recorrido transitivo |
| G00-08-F07 | Path seguro | Absolutos/traversal y rutas normalizadas |
| G00-08-F08 | Huérfanos | Recorrer referencias anidadas; anchor no fabrica cuerpo |
| G00-08-F09 | SourceRef separado | Fuentes se resuelven por catálogo de cortes |
| G00-08-F10 | Lectura sin mutación | Misma consulta conserva snapshot e índices |

## G00-09 — Esquemas

| Cláusula | Contrato | Trabajo de aceptación/corrección |
|---|---|---|
| G00-09-F01 | Envelope de esquema | Tipo+versión obligatorios, sin defaults normativos |
| G00-09-F02 | Normative features | Desconocido normativo falla en reader viejo |
| G00-09-F03 | Enum cerrado | No coerción de enum a otro eje |
| G00-09-F04 | Missing null empty | Ausencia/null/vacío se preservan según contrato |
| G00-09-F05 | Roundtrip tipado | Todos los tipos raíz y contexto interno frente a envoltura |
| G00-09-F06 | Exactitud numérica | Enteros grandes exactos en rango y límite |
| G00-09-F07 | JSON estricto | NaN/Infinity/claves duplicadas y payload hostil |
| G00-09-F08 | Campos informativos | Solo info.* permitido y sin efecto normativo |
| G00-09-F09 | Compatibilidad | Reconciliar v1/v2 y semántica de migración explícita |
| G00-09-F10 | Versión fijada | Registro versionado inyectado, no latest remoto |

## G00-10 — Evaluador

| Cláusula | Contrato | Trabajo de aceptación/corrección |
|---|---|---|
| G00-10-F01 | Entrada explícita | Entradas completas y separadas de E/S/clock |
| G00-10-F02 | Prevalidación | Comparar cuerpos fijados, no solo igualdad de refs |
| G00-10-F03 | Cobertura de reglas | Regla ausente/desconocida permanece en denominador |
| G00-10-F04 | Aplicabilidad previa | NO exige testigo; UNKNOWN no excluye |
| G00-10-F05 | Precedencia | Solo supersesión aprobada y scoped |
| G00-10-F06 | Predicados puros | Registro trusted, sin callbacks de candidato |
| G00-10-F07 | Sin scripts | JSON no ejecuta scripts de proyecto |
| G00-10-F08 | Límites de evaluación | Presupuesto global y no examinadas, sin PASS parcial |
| G00-10-F09 | Diagnóstico por regla | FAIL/CONFLICT/UNKNOWN simultáneos conservan testigos |
| G00-10-F10 | Determinismo completo | Permutar registros y hechos con varios fallos preserva informe |

## G00-11 — Conflictos

| Cláusula | Contrato | Trabajo de aceptación/corrección |
|---|---|---|
| G00-11-F01 | Tipos de afirmación | Separar hechos/normas/propuestas/inferencias |
| G00-11-F02 | Intersección de scopes | Intersección para perfil, no bloqueo global de desacuerdo textual |
| G00-11-F03 | Coexistencia legítima | Historia distinta no se borra ni se declara conflicto corriente |
| G00-11-F04 | Conflicto con testigos | Conservar las dos afirmaciones y fuentes |
| G00-11-F05 | No latest-wins | Fecha/SHA/orden no confieren prioridad |
| G00-11-F06 | Supersesión con autoridad | No retirar regla por etiqueta SUPERSEDED |
| G00-11-F07 | Bloqueo localizado | Bloquear únicamente dependientes en ámbito |
| G00-11-F08 | No ocultar conflictos | Conjunto completo debe contrastarse con pins externos |
| G00-11-F09 | Orden reproducible | Permutar afirmaciones conserva resultado y testigos |
| G00-11-F10 | Aislamiento de autoridad | Mismo nombre de otro proyecto no fusiona autoridad |

## G00-12 — Aceptación

| Cláusula | Contrato | Trabajo de aceptación/corrección |
|---|---|---|
| G00-12-F01 | Pruebas de identidad | Reconciliar falsación por cláusula y no existencia de tipo |
| G00-12-F02 | Pruebas de fuentes | Añadir D01 y ramas de adquisición, imports e historia |
| G00-12-F03 | Pruebas de autoridad | Reejecutar acciones, quorum, independencia y conflictos |
| G00-12-F04 | Pruebas de ontología | Ejercitar relaciones compartidas y borradores incompletos |
| G00-12-F05 | Tablas de aplicabilidad | Tablas independientes y testigos de composición |
| G00-12-F06 | Estados ortogonales | No promover DEVELOPED/NOT_RUN/UNQUALIFIED |
| G00-12-F07 | Pruebas de schemas | Roundtrip/contextos/versiones/números/payload hostil |
| G00-12-F08 | Evaluador puro | Pureza, orden de hechos y presupuesto agregado |
| G00-12-F09 | Escenario de dos proyectos | Dos proyectos y autoridad distinta con mismas etiquetas |
| G00-12-F10 | Mutaciones y gates | A01/A02/A03: contrato API, diagnóstico exacto y código realmente importado |
