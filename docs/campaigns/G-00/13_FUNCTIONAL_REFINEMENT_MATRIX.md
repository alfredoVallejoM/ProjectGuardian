# G-00 — Las 120 cláusulas funcionales de las 12 obligaciones originales

Estas **120 cláusulas subordinadas** desarrollan las 12 obligaciones G00-01…G00-12; no se han creado 120 obligaciones históricas adicionales ni se han cambiado las 163 originales. Cada fila tiene comportamiento exigido, aceptación, falsación, owner y test contractual futuro. **Estado: diseño, no implementación ni ejecución.**

## G00-01 — 10 cláusulas

| Cláusula | Funcionalidad | Comportamiento exigido | Aceptación | Falsación | Test previsto |
|---|---|---|---|---|---|
| `G00-01-F01` | Identidades nominales | Implementar constructores distintos para ProjectId, EntityId, RevisionId y ContentDigest | Un parser devuelve instancias con discriminante correcto y rechaza intercambio entre clases | La misma cadena se acepta como el tipo de identificador equivocado | `G00-01-T01` |
| `G00-01-F02` | Namespace y clase | Asociar EntityId a ProjectId y EntityKind exactos | La igualdad de entidades exige namespace y clase además del valor | Una entidad de proyecto B equivale a otra de A por tener el mismo texto | `G00-01-T02` |
| `G00-01-F03` | Gramática estable | Validar longitud, alfabeto, prefijos y sintaxis de ID canónico | Una entrada fuera de la gramática devuelve InvalidIdentity con path y causa | Se admite ID vacío, path traversal o texto con delimitadores inseguros | `G00-01-T03` |
| `G00-01-F04` | Alias separado | Modelar Alias como referencia legible con ámbito y procedencia | Un alias resuelve solo cuando hay un candidato exacto en el ámbito | El primer alias duplicado gana por orden de diccionario | `G00-01-T04` |
| `G00-01-F05` | Renombrado conservador | Permitir cambiar nombre de presentación/ruta sin cambiar LogicalId | El mismo EntityId se mantiene tras el cambio de alias o ruta | El identificador canónico se regenera porque se movió el archivo | `G00-01-T05` |
| `G00-01-F06` | Revisión pinneada | Representar cada EntityRef con RevisionId obligatorio para evaluación normativa | La referencia resuelve a revisión exacta o produce error tipado | Una branch mutable se considera RevisionId certificable | `G00-01-T06` |
| `G00-01-F07` | Digest con algoritmo | Validar algoritmo, codificación y longitud de ContentDigest | Algoritmo y hex completo se conservan al serializar | Digest abreviado o algoritmo distinto se acepta como idéntico | `G00-01-T07` |
| `G00-01-F08` | Generación exterior | Recibir IDs generados como entrada y solo validarlos en domain | Ejecutar validadores con mismos inputs no usa hora ni RNG | El constructor puro invoca time o uuid internamente y cambia resultados | `G00-01-T08` |
| `G00-01-F09` | Roundtrip de tipos | Serializar y deserializar todos los ID sin perder kind ni project | El roundtrip conserva tipo nominal, valor y namespace | Todos los IDs se serializan como string sin tipo recuperable | `G00-01-T09` |
| `G00-01-F10` | Colisiones explícitas | Detectar IDs repetidos de distinta entidad en un mismo namespace y clase | Registrar DuplicateLogicalId sin fusionar obligaciones | La segunda entidad sobrescribe la primera | `G00-01-T10` |

**Owner(s):** `src/guardian/domain/identity.py`. **Documento de funcionamiento:** [Detalle](../../campaigns/G-00/01_IDS_AND_REFERENCES.md).

## G00-02 — 10 cláusulas

| Cláusula | Funcionalidad | Comportamiento exigido | Aceptación | Falsación | Test previsto |
|---|---|---|---|---|---|
| `G00-02-F01` | Identidad del proyecto | Definir ProjectDefinition con ID estable y metadatos separados | Renombrar display name no cambia ProjectId ni constitución | Cambiar nombre recrea proyecto y borra linaje | `G00-02-T01` |
| `G00-02-F02` | Fuentes autorizadas | Registrar repositorios y políticas de fuente por proyecto | Fuente fuera de allowlist da denegación o requerimiento de importación | Un repo arbitrario se convierte en fuente normativa | `G00-02-T02` |
| `G00-02-F03` | Tres modos | Representar EMBEDDED, SIDECAR y FEDERATED como descriptores válidos | Cada modo tiene sus campos obligatorios y no altera contrato central | SIDECAR se interpreta como fuente secundaria de verdad editable | `G00-02-T03` |
| `G00-02-F04` | Selección explícita | Requerir ProjectId en vistas y llamadas de dominio | Dos proyectos alternados mantienen estados y refs propios | Se usa un global current_project implícito | `G00-02-T04` |
| `G00-02-F05` | Importaciones explícitas | Exigir descriptor de importación aprobado para refs ajenas | Una importación sin alcance produce REQUIRES_APPROVAL | Contratos externos se incorporan por similitud textual | `G00-02-T05` |
| `G00-02-F06` | Granularidad de import | Restringir importación a cortes, rutas o contratos concedidos | Permiso para un SourceCut no concede todo otro repositorio | Importar un archivo autoriza todos los archivos del repo | `G00-02-T06` |
| `G00-02-F07` | Versión de política | Fijar constitution/policy revision en definición de proyecto | Las reglas se evalúan sobre revisión indicada, nunca latest accidental | Actualizar policy global cambia evaluación histórica sin revisión | `G00-02-T07` |
| `G00-02-F08` | Federación | Representar múltiples repositorios con identidades/cortes independientes | Una vista federada conserva commit y autoridad de cada fuente | Se aplica un único SHA como revisión de todos los repos | `G00-02-T08` |
| `G00-02-F09` | Alias no global | Permitir mismos nombres humanos en proyectos diferentes | El resolver distingue ProjectId y no mezcla alias | Los dos proyectos comparten una tabla autoritativa de nombres | `G00-02-T09` |
| `G00-02-F10` | Proyecto inmutable | Construir vista de proyecto read-only con entradas explícitas | Validar no modifica fuentes, contratos ni config | Validación cambia el registro del proyecto en memoria | `G00-02-T10` |

**Owner(s):** `src/guardian/domain/project.py`. **Documento de funcionamiento:** [Detalle](../../campaigns/G-00/02_PROJECT_TENANCY_AND_SOURCES.md).

## G00-03 — 10 cláusulas

| Cláusula | Funcionalidad | Comportamiento exigido | Aceptación | Falsación | Test previsto |
|---|---|---|---|---|---|
| `G00-03-F01` | Git inmutable | Modelar SourceCut Git con commit completo, repo, kind y path opcional | Branch sin resolución a corte fijo no vale para cierre de cobertura | main se almacena como commit inmutable | `G00-03-T01` |
| `G00-03-F02` | Documento versionado | Distinguir SourceRef documental con revisión/identidad de captura | Una cita se liga a documento y revisión, no solo título | Un nombre de documento sin corte se trata como versión completa | `G00-03-T02` |
| `G00-03-F03` | Inclusiones | Definir reglas explícitas de qué fuentes pertenecen al universo | Cambiar include set genera revisión de universo, no reinterpreta corte viejo | Todo archivo del mundo se presume incluido | `G00-03-T03` |
| `G00-03-F04` | Exclusiones justificadas | Exigir razón/autoridad al excluir fuentes de un universo comprometido | Una exclusión no documentada produce diagnóstico | Se excluye archivo problemático para declarar cobertura | `G00-03-T04` |
| `G00-03-F05` | Fuentes ausentes | Registrar known_missing y unavailable sin inventar contenido | La evaluación conserva SOURCE_MISSING y no afirma exhaustividad | Fuente no descargada se marca reconciled | `G00-03-T05` |
| `G00-03-F06` | Cortes solapados | Clasificar historia BASE/DELTA/SUPERSEDED/REFERENCE según scope | Dos cuts del mismo repo no se suman como poblaciones semánticas disjuntas | El número de archivos se duplica como capacidades | `G00-03-T06` |
| `G00-03-F07` | Niveles de adquisición | Separar IDENTIFIED, IDENTITY_VERIFIED, CONTENT_OBSERVED, SEMANTIC_RECONCILED | Un árbol remoto leído no se declara censo AST completo | Pointer de blob se trata como implementacion certificada | `G00-03-T07` |
| `G00-03-F08` | Fuente versus autoridad | Registrar observaciones sin convertirlas en decisiones ratificadas | Un README o comentario no altera constitution aprobada | Una instrucción en fichero fuente autoriza cambiar reglas | `G00-03-T08` |
| `G00-03-F09` | Cobertura delimitada | SourceUniverse incluye alcance y límites antes de reclamo de completeness | Universo con known_missing no permite claim de cobertura completa | Se declara 100% porque todas las filas ya registradas tienen ref | `G00-03-T09` |
| `G00-03-F10` | Metadatos de alcance | Representar feature/corpus/platform/time scope del inventario | Informe puede explicar qué universo quedó fuera | Una cifra de cobertura carece de denominador y exclusiones | `G00-03-T10` |

**Owner(s):** `src/guardian/domain/source.py`. **Documento de funcionamiento:** [Detalle](../../campaigns/G-00/02_PROJECT_TENANCY_AND_SOURCES.md).

## G00-04 — 10 cláusulas

| Cláusula | Funcionalidad | Comportamiento exigido | Aceptación | Falsación | Test previsto |
|---|---|---|---|---|---|
| `G00-04-F01` | Estados de decisión | Distinguir PROPOSED, APPROVED, REJECTED y SUPERSEDED en DecisionRevision | El parser conserva estado y no presupone aprobación | Una propuesta se toma como norma ratificada | `G00-04-T01` |
| `G00-04-F02` | Approval distinto | Modelar ApprovalRef separado de texto de decisión | Un registro autodenominado aprobado sin contexto confiable no concede autoridad | Un campo approver textual basta para ratificar | `G00-04-T02` |
| `G00-04-F03` | Regla versionada | RuleRevision especifica ID, kind, scope, predicate, autoridad y versión | Regla inválida no entra al evaluador como obligación cumplida | Una norma sin scope se aplica universalmente | `G00-04-T03` |
| `G00-04-F04` | Hecho frente a norma | Separar source observation de contractual decision | El código observado no redefine requisito aprobado | El último commit corrige automáticamente la especificación | `G00-04-T04` |
| `G00-04-F05` | Contexto confiable | AuthorityContext debe recibirse explícitamente de frontera externa | Ausencia de contexto emite UNKNOWN_AUTHORITY o REQUIRES_APPROVAL | JSON presentado por agente autentica al principal | `G00-04-T05` |
| `G00-04-F06` | Precedencia autorizada | Aplicar supersession ratificada solo dentro de ámbito y revisión | La regla antigua persiste como histórica pero no se sobreescribe | Una decisión posterior sin aprobación reemplaza la anterior | `G00-04-T06` |
| `G00-04-F07` | Sin prioridad temporal | No elegir una de dos fuentes conflictivas solo por fecha | Detectar conflicto sin preferencia heurística | El documento más reciente gana por defecto | `G00-04-T07` |
| `G00-04-F08` | Dependientes de conflicto | Emitir ConflictRecord e identificar reglas/claims afectados | El conflicto bloquea solo el ámbito pertinente y se conserva | La UI oculta un conflicto para cerrar el proyecto | `G00-04-T08` |
| `G00-04-F09` | Scope de decisiones | Validar que decision/policy pertenecen al proyecto y ámbito | Decisión de proyecto ajeno requiere importación y autoridad | Una regla externa gobierna proyecto sin permiso | `G00-04-T09` |
| `G00-04-F10` | Enmienda como propuesta | Construir AmendmentRequest sin mutar policy protegida | La enmienda permanece pendiente de aceptación externa | Evaluador constitucional ratifica su propia modificación | `G00-04-T10` |

**Owner(s):** `src/guardian/domain/authority.py`, `src/guardian/domain/constitution.py`, `src/guardian/constitution/authority_resolution.py`. **Documento de funcionamiento:** [Detalle](../../campaigns/G-00/03_CONSTITUTION_AUTHORITY_CONFLICTS.md).

## G00-05 — 10 cláusulas

| Cláusula | Funcionalidad | Comportamiento exigido | Aceptación | Falsación | Test previsto |
|---|---|---|---|---|---|
| `G00-05-F01` | Objetivo autónomo | ObjectiveRevision contiene propósito, fuentes y exclusiones sin ser task | Una capacidad puede derivar de un objetivo sin heredar estado completo | Objetivo equivale a campaign ticket | `G00-05-T01` |
| `G00-05-F02` | Capacidad funcional | CapabilityRevision describe comportamiento, contexto y owner | Una capacidad existe como contrato aunque no haya código | Crear archivo vacio marca capacidad IMPLEMENTED | `G00-05-T02` |
| `G00-05-F03` | Propiedad independiente | PropertyRevision declara garantía, hipótesis y ámbito | Una propiedad comparte capacidades sin duplicar su identidad | Una prueba registrada se transforma en Property | `G00-05-T03` |
| `G00-05-F04` | Obligación exigible | ObligationRevision tiene statement, applicability, due, source, authority | El validador separa obligación aprobada de borrador | Un TODO sin fuente se acepta como obligación ratificada | `G00-05-T04` |
| `G00-05-F05` | Aceptación y falsación | Obligation registra acceptance, falsification y verification requirements | Una obligación normativa sin aceptación exigida es diagnosticada | La aceptación se reduce a existe test | `G00-05-T05` |
| `G00-05-F06` | Verification separada | VerificationSpecRef es contrato; ValidationRun no se crea al definir obligación | Spec sin ejecución mantiene NOT_RUN | Una función test_ en un archivo acredita PASS | `G00-05-T06` |
| `G00-05-F07` | Arquitectura normativa | ArchitectureRevision separa component owner y dependencias del código observado | Import real no se considera norma ratificada | El diseño se reescribe para coincidir con import actual | `G00-05-T07` |
| `G00-05-F08` | Campaign membership | CampaignRevision referencia IDs de obligaciones por scope/hito | Una misma obligación en dos campañas conserva ID y revisión | Copiar texto a nueva campaña crea nueva autoridad paralela | `G00-05-T08` |
| `G00-05-F09` | Muchos-a-muchos | Permitir objetivos/capacidades/propiedades/obligaciones con referencias múltiples | Doble owner/productor no fuerza jerarquía uno-a-uno inventada | Se rechaza legítimo uso compartido de propiedad | `G00-05-T09` |
| `G00-05-F10` | Investigación separada | Research/Future/Optional no son Current sin decisión | Un objetivo de investigación se visualiza sin exigirse como desarrollo actual | Un constructor mueve CURRENT a RESEARCH para ocultar falta | `G00-05-T10` |

**Owner(s):** `src/guardian/domain/objective.py`, `src/guardian/domain/capability.py`, `src/guardian/domain/property.py`, `src/guardian/domain/obligation.py`, `src/guardian/domain/campaign.py`. **Documento de funcionamiento:** [Detalle](../../campaigns/G-00/04_OBJECTIVES_CAPABILITIES_PROPERTIES_OBLIGATIONS.md).

## G00-06 — 10 cláusulas

| Cláusula | Funcionalidad | Comportamiento exigido | Aceptación | Falsación | Test previsto |
|---|---|---|---|---|---|
| `G00-06-F01` | Perfil multidimensional | SupportProfile con project, revision, milestone, features, domain y resources tipados | Dimensiones no especificadas se registran desconocidas | Campo ausente equivale a falso | `G00-06-T01` |
| `G00-06-F02` | AST acotado | ScopeExpression usa Atom, ALL, ANY, NOT, True/False explícitos | No se acepta eval de código ni operadores no registrados | Se ejecuta Python arbitrario de un contrato | `G00-06-T02` |
| `G00-06-F03` | Cuatro valores | ApplicabilityResult distingue YES NO UNKNOWN CONFLICT como par de evidencias | Los cuatro casos tienen roundtrip y testigos distintos | Conflicto se convierte en unknown | `G00-06-T03` |
| `G00-06-F04` | Conjunción precisa | AND usa truth-support intersection y false-support union | AND(YES,UNKNOWN)=UNKNOWN y AND(YES,NO)=NO | AND desconocido produce YES por identidad vacía | `G00-06-T04` |
| `G00-06-F05` | Disyunción y negación | OR y NOT siguen álgebra de soporte y preservan conflictos internos | OR(NO,UNKNOWN)=UNKNOWN y NOT(CONFLICT)=CONFLICT | NOT UNKNOWN se convierte en YES | `G00-06-T05` |
| `G00-06-F06` | Dimension completa | NO por ausencia solo cuando dimensión declara conjunto exhaustivo | Feature ausente en lista incompleta da UNKNOWN | Feature X no listado se considera NO | `G00-06-T06` |
| `G00-06-F07` | Due separado | Applicability distinto de compromiso temporal y ratificación | Obligación FUTURE aplicable no es CURRENT sin cambio autorizado | Constructor altera milestone para cerrar | `G00-06-T07` |
| `G00-06-F08` | Predicado externo | VerifierPredicate sin verificador/observación confiable devuelve UNKNOWN | Desconocido no ejecuta plugin ni confiere PASS | Script ajeno devuelve PASS sin admisión | `G00-06-T08` |
| `G00-06-F09` | Presupuesto explícito | StepBudget limita profundidad/nodos/pasos y reporta recurso insuficiente | Agotamiento produce ResourceLimited con diagnóstico | Análisis parcial declara completo | `G00-06-T09` |
| `G00-06-F10` | Testigos scoped | YES y NO referencian fuentes y revisiones del mismo perfil | Una evidencia de proyecto B no se usa automáticamente en A | Una afirmación sin scope se acepta universalmente | `G00-06-T10` |

**Owner(s):** `src/guardian/domain/scope.py`, `src/guardian/constitution/evaluator.py`. **Documento de funcionamiento:** [Detalle](../../campaigns/G-00/05_SCOPE_AND_APPLICABILITY.md).

## G00-07 — 10 cláusulas

| Cláusula | Funcionalidad | Comportamiento exigido | Aceptación | Falsación | Test previsto |
|---|---|---|---|---|---|
| `G00-07-F01` | Ejes nominales | StatusAxis Source/Decision/Commitment/Implementation/Audit/Material/Support/Qualification/Migration | Los nueve ejes son distinguibles en parse y serialización | Un PASS de Audit se trata como Material.PASS | `G00-07-T01` |
| `G00-07-F02` | Fuente separada | Source IDENTIFIED no implica SEMANTIC_RECONCILED | Status Source no altera code status | Git tree leído se declara implementación | `G00-07-T02` |
| `G00-07-F03` | Decisión y compromiso | PROPOSED/APPROVED y CURRENT/FUTURE se modelan por separado | No convertir future en current mediante observación textual | Decision PROPOSED activa CURRENT sin aprobación | `G00-07-T03` |
| `G00-07-F04` | Implementación y ejecución | DEVELOPED y NOT_RUN son compatibles sin falsedad | Un test escrito no cambia Material a PASS | Estado de compilación no ejecutada se considera PASS | `G00-07-T04` |
| `G00-07-F05` | Auditoría propia | Audit PASS requiere AuditRecord posterior y política de independencia | Definir estado Audit no concede dictamen auditado | Constructor se autocalifica auditor independiente | `G00-07-T05` |
| `G00-07-F06` | Soporte/qualification | Support CURRENT y QualifiedInScope dependen de evidencia futura no del estado escrito | G00 no dispone de método issue_certificate | StatusObservation produce certificado | `G00-07-T06` |
| `G00-07-F07` | Migración independiente | Migration CLOSED no se deduce de un resultado unitario | MIGRATION_PARITY_PENDING permanece separado | Un smoke test cierra migración histórica | `G00-07-T07` |
| `G00-07-F08` | Observación no autoridad | StatusObservation guarda fuente, revisión, actor y ámbito | Una observación no se convierte en StatusProjection confiable | Se escribe completed true para saltar gates | `G00-07-T08` |
| `G00-07-F09` | No confundir NOT_RUN | Material.NOT_RUN distinto de FAIL y de SUCCESS | Reporte indica ausencia de ejecución material | NOT_RUN se borra del informe por conveniencia | `G00-07-T09` |
| `G00-07-F10` | Renderer honesto | Estado vectorial presenta todas dimensiones requeridas con límites | Un resumen deja visible evidencia pendiente | Solo se muestra verde DONE aunque QUALIFIED=UNQUALIFIED | `G00-07-T10` |

**Owner(s):** `src/guardian/domain/outcomes.py`. **Documento de funcionamiento:** [Detalle](../../campaigns/G-00/06_ORTHOGONAL_STATUS_AND_OUTCOMES.md).

## G00-08 — 10 cláusulas

| Cláusula | Funcionalidad | Comportamiento exigido | Aceptación | Falsación | Test previsto |
|---|---|---|---|---|---|
| `G00-08-F01` | Ref completa | EntityRef contiene project, kind, logical_id, revision | Faltante revision en contrato normativo se rechaza | Se acepta referencia latest flotante | `G00-08-T01` |
| `G00-08-F02` | Comprobación de clase | Resolver verifica expected_kind antes de devolver entidad | ObligationId no resuelve como Capability | El mismo texto sustituye a tipos distintos | `G00-08-T02` |
| `G00-08-F03` | Snapshot exacto | Resolver solo encuentra revisiones admitidas y referidas | Revision histórica existe solo como historical y no current | Resolver elige último documento | `G00-08-T03` |
| `G00-08-F04` | Alias ambiguo | Alias con dos candidatos produce AmbiguousAlias | No se elige por orden de inserción | Duplicación de alias colapsa entidades | `G00-08-T04` |
| `G00-08-F05` | No ciclos genéricos | No aplicar aciclicidad universal a ontología | Ciclo legítimo de relaciones no se rechaza como dependencia ejecutiva | Todo ciclo matemático es considerado fallo | `G00-08-T05` |
| `G00-08-F06` | Grant scoped | Referencia de otro proyecto exige permiso/import explícito por corte | Import grant limitado no autoriza repo completo | Cualquier link externo es autorizado | `G00-08-T06` |
| `G00-08-F07` | Path seguro | Validar GitSourcePath relativo y sin traversal/absolutos | ../ y rutas absolutas se rechazan | Ruta escapa root del repo | `G00-08-T07` |
| `G00-08-F08` | Huérfanos | Detectar referencias no existentes con diagnóstico de causa | OrphanRef no produce fallback a entidad genérica | Falta ref y se crea objeto placeholder ratificado | `G00-08-T08` |
| `G00-08-F09` | SourceRef separado | EntityRef y SourceRef tienen resolvers/contextos diferentes | URL arbitraria no es Git immutable source | Se trata SourcePath como EntityId | `G00-08-T09` |
| `G00-08-F10` | Lectura sin mutación | Reference resolver no altera snapshot ni índices nominales | Mismo View+Ref da mismo outcome sin side effects | Resolver crea automáticamente una nueva revision | `G00-08-T10` |

**Owner(s):** `src/guardian/domain/identity.py`, `src/guardian/domain/source.py`. **Documento de funcionamiento:** [Detalle](../../campaigns/G-00/07_REFERENTIAL_INTEGRITY.md).

## G00-09 — 10 cláusulas

| Cláusula | Funcionalidad | Comportamiento exigido | Aceptación | Falsación | Test previsto |
|---|---|---|---|---|---|
| `G00-09-F01` | Envelope de esquema | Cada registro contiene schema version y discriminante de tipo | Roundtrip mantiene schema+record_type | Un objeto sin version se admite con default normativo | `G00-09-T01` |
| `G00-09-F02` | Normative features | Registrar required_normative_features y bloquear desconocidas | Desconocida da UNSUPPORTED_NORMATIVE_FEATURE | Un lector viejo ignora nueva obligación | `G00-09-T02` |
| `G00-09-F03` | Enum cerrado | Variantes de estado/kind desconocidas se rechazan | Unknown enum no se transforma en status UNKNOWN de otro eje | Variante desconocida se mapea a primer enum | `G00-09-T03` |
| `G00-09-F04` | Missing null empty | Distinguir ausencia, null y lista vacía cuando semánticamente diferentes | Acceptance omitida no se convierte en lista validada | Un None equivale a array de pruebas vacío | `G00-09-T04` |
| `G00-09-F05` | Roundtrip tipado | Encode/decode preserva IDs tipos revision y source refs | Import+export produce mismo contrato tipado | Se pierden project IDs | `G00-09-T05` |
| `G00-09-F06` | Exactitud numérica | Números enteros grandes usan formato exacto establecido | Roundtrip preserva big integers | Se redondea un ID numérico o resource bound | `G00-09-T06` |
| `G00-09-F07` | JSON estricto | Rechazar NaN/infinito donde el contrato exige serialización canónica | Invalid numeric syntax produce DecodeError | NaN se usa para invalidar comparaciones | `G00-09-T07` |
| `G00-09-F08` | Campos informativos | Extensiones no normativas solo dentro de espacio permitido | Desconocido informativo no cambia evaluación | Campo extra cambia decisión de cierre | `G00-09-T08` |
| `G00-09-F09` | Compatibilidad | Comparar versiones y features; cambios semánticos requieren migración | Lector antiguo bloquea cambio de meaning | Schema viejo acepta campos de nueva regla ignorándolos | `G00-09-T09` |
| `G00-09-F10` | Versión fijada | Schema registry se pasa como argumento/revisión sin buscar latest | Mismo descriptor resulta misma validación | Codec cambia comportamiento por update remoto | `G00-09-T10` |

**Owner(s):** `src/guardian/persistence/schema_registry.py`. **Documento de funcionamiento:** [Detalle](../../campaigns/G-00/08_SCHEMAS_VERSIONING_AND_SERIALIZATION.md).

## G00-10 — 10 cláusulas

| Cláusula | Funcionalidad | Comportamiento exigido | Aceptación | Falsación | Test previsto |
|---|---|---|---|---|---|
| `G00-10-F01` | Entrada explícita | Evaluador recibe constitution, view, fact set, profile, authority y budget | Sin datos de contexto se devuelve error explícito | Evaluador lee variables de entorno | `G00-10-T01` |
| `G00-10-F02` | Prevalidación | Verificar tipos, versiones, regla y proyecto antes de ejecutar predicados | Entrada estructural inválida no se trata como FAIL científico | Malformed schema da PASS | `G00-10-T02` |
| `G00-10-F03` | Cobertura de reglas | Enumerar todas reglas obligatorias conocidas y listarlas en report | Regla no soportada queda UNKNOWN_UNEVALUATED | Se omite regla desconocida del denominador | `G00-10-T03` |
| `G00-10-F04` | Aplicabilidad previa | Evaluar ScopeExpression con testigos antes de rule predicate | NOT_APPLICABLE requiere NO probado | UNKNOWN se ignora y el total es PASS | `G00-10-T04` |
| `G00-10-F05` | Precedencia | Resolver decisiones solo con AuthorityContext externo y scoped | Propuesta contradictoria no adquiere autoridad | Último documento gana | `G00-10-T05` |
| `G00-10-F06` | Predicados puros | Despachar RuleKind a función trusted registrada y determinista | Mismo input genera mismo diagnóstico | Un callback externo cambia resultados | `G00-10-T06` |
| `G00-10-F07` | Sin scripts | Rechazar predicado arbitrario en JSON de proyecto | El runtime no ejecuta eval/exec en policy | Script del proyecto es cargado como norma | `G00-10-T07` |
| `G00-10-F08` | Límites de evaluación | Contar reglas, profundidad y pasos; identificar no examinadas | ResourceLimited nunca es PASS | Timeout se trata como cumplimiento | `G00-10-T08` |
| `G00-10-F09` | Diagnóstico por regla | Reportar RuleEvaluation con ID, verdict, scope, motivos y testigos | Una violación no oculta otras reglas | Solo devuelve true | `G00-10-T09` |
| `G00-10-F10` | Determinismo completo | Evaluación ordena resultados e inputs y no muta hechos | Permutar entrada produce misma salida estable | Se altera FactSet o dicta resultado según reloj | `G00-10-T10` |

**Owner(s):** `src/guardian/constitution/evaluator.py`. **Documento de funcionamiento:** [Detalle](../../campaigns/G-00/09_PURE_EVALUATOR.md).

## G00-11 — 10 cláusulas

| Cláusula | Funcionalidad | Comportamiento exigido | Aceptación | Falsación | Test previsto |
|---|---|---|---|---|---|
| `G00-11-F01` | Tipos de afirmación | Distinguir observed fact, normative rule, decision, proposed inference | Hecho no sobreescribe obligación sin enmienda | Código observado define política nueva | `G00-11-T01` |
| `G00-11-F02` | Intersección de scopes | Comprobar si afirmaciones incompatibles aplican al mismo perfil | Scopes disjuntos no se bloquean entre sí | Todo desacuerdo textual es CONFLICT global | `G00-11-T02` |
| `G00-11-F03` | Coexistencia legítima | Permitir dos decisiones históricas en cortes distintos sin conflicto vigente | La precedencia temporal se explica por revisiones autorizadas | Se borra historia para resolver | `G00-11-T03` |
| `G00-11-F04` | Conflicto con testigos | ConflictRecord incluye ambas afirmaciones, fuentes y perfiles | El informe no pierde uno de los witness refs | Conflicto con evidencia positiva y negativa se llama UNKNOWN | `G00-11-T04` |
| `G00-11-F05` | No latest-wins | Nunca preferir automáticamente fecha, SHA, orden de registro | Resolver sin política explícita devuelve Conflict/Unknown | El último archivo se impone | `G00-11-T05` |
| `G00-11-F06` | Supersesión con autoridad | Decisión ratificada de sustitución resuelve dentro del scope | Sin aprobación no se retira regla anterior | Texto SUPERSEDED sin autoridad basta | `G00-11-T06` |
| `G00-11-F07` | Bloqueo localizado | Identificar obligaciones/claims dependientes de conflicto | Componentes independientes no se marcan fail global | Un conflicto pequeño impide orientación de todo el proyecto | `G00-11-T07` |
| `G00-11-F08` | No ocultar conflictos | Un PASS parcial conserva lista de conflictos pendientes | Report completo lista reglas en disputa | Se descarta contradicción al agregar resultados | `G00-11-T08` |
| `G00-11-F09` | Orden reproducible | Ordenar conflictos por ids y paths para diagnósticos estables | Permutación de fuentes no altera ConflictRecord | Hash/set iteration cambia qué claim se bloquea | `G00-11-T09` |
| `G00-11-F10` | Aislamiento de autoridad | Conflictos entre proyectos aislados no se fusionan sin import autorizado | Norma proyecto A no compite con B automáticamente | Similaridades entre repos crean mismo conflicto normativo | `G00-11-T10` |

**Owner(s):** `src/guardian/constitution/precedence.py`. **Documento de funcionamiento:** [Detalle](../../campaigns/G-00/03_CONSTITUTION_AUTHORITY_CONFLICTS.md).

## G00-12 — 10 cláusulas

| Cláusula | Funcionalidad | Comportamiento exigido | Aceptación | Falsación | Test previsto |
|---|---|---|---|---|---|
| `G00-12-F01` | Pruebas de identidad | Escribir tests tipados de IDs aliases revisiones y roundtrips | Mutación que confunde EntityId/RevisionId falla test | Solo comprobar que tipo existe | `G00-12-T01` |
| `G00-12-F02` | Pruebas de fuentes | Cubrir cortes no fijos, known_missing, importaciones y ScopeUniverse | Fuente faltante impide afirmar complete | Todos los SourceRef se aceptan | `G00-12-T02` |
| `G00-12-F03` | Pruebas de autoridad | Proponer/ratificar/precedencia con y sin trusted context | Auto-aprobación de texto se detecta | Solo probar decisión feliz | `G00-12-T03` |
| `G00-12-F04` | Pruebas de ontología | Construir proyecto multiobjective/multicapability y relaciones compartidas | Propiedad compartida no se duplica ni se autocertifica | Modelo solo permite relación uno-a-uno | `G00-12-T04` |
| `G00-12-F05` | Tablas de aplicabilidad | Cubrir 4 valores y AND OR NOT con testigos | Truth table ejecutada coincide con contrato | UNKNOWN y NO pasan indistintos | `G00-12-T05` |
| `G00-12-F06` | Estados ortogonales | Testear combinaciones DEVELOPED/NOT_RUN/UNQUALIFIED | No existe promoción automática de ejes | Un flag completed controla todos estados | `G00-12-T06` |
| `G00-12-F07` | Pruebas de schemas | Cubrir versions, normative features, invalid types, roundtrip y payload hostil | Lectores viejos rechazan nueva norma no comprendida | Se aceptan enums desconocidos | `G00-12-T07` |
| `G00-12-F08` | Evaluador puro | Ejecutar misma entrada permutada y con budget variable | Determinismo, no IO, reporte de reglas no examinadas | Falla una norma y reporte oculta otras | `G00-12-T08` |
| `G00-12-F09` | Escenario de dos proyectos | Integrar en memoria dos proyectos, imports explícitos y constituciones separadas | Ninguna autoridad se mezcla por nombre | Project B hereda decision de A | `G00-12-T09` |
| `G00-12-F10` | Mutaciones y gates | Banco adversario muta source/status/rule/reference/predicate y compara resultado esperado | Al menos una mutación por familia dispara diagnóstico correcto | Una mutación de regla ratificada queda PASS | `G00-12-T10` |

**Owner(s):** `src/guardian/constitution/invariants.py`. **Documento de funcionamiento:** [Detalle](../../campaigns/G-00/11_TESTS_AND_ADVERSARIAL_MATRIX.md).

## Reglas para desarrollar los tests
Los nombres G00-XX-TYY son identificadores lógicos; no hay obligación de un archivo físico por cada test. Para cada cláusula se debe crear una prueba que falsifique el comportamiento original (o una property test generativa equivalente), además de las pruebas positivas y de integración que el perfil exija. Un test que solo construye el objeto sin ejercer su invariante no satisface la obligación.

## Alcance de autoridad
El JSON `architecture/g00_functional_refinement.json` es la propuesta estructurada. Al ratificar, debe revisarse que las cláusulas sean refinamientos legítimos de las 12 obligaciones originales. Toda exigencia realmente nueva se tramita como `AddObligation` aprobado, no se disimula como precisión editorial.
