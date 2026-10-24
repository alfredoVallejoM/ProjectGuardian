# G00-B03 / B06 / GSL0-LC04 — registros y resolución de contenido

Fecha: 2026-10-24. Base: `19c6cf31b5b686362568cf2b3aaed538504b127c`.
Estado: `IMPLEMENTED_BOUNDED_REFERENCE_SLICE`. No cierre de bloques completos,
G-00, GSL-0, ratificación ni auditoría independiente. Las fuentes originales
normativas de `architecture/` no se modifican.

## Implementación productiva

Se añaden seis clases nominales inmutables: ObjectiveRevision, CapabilityRevision,
PropertyRevision, ObligationRevision, CampaignRevision y ArchitectureRevision.
Comparten invariantes de identidad, procedencia, ámbito y declaración de autoridad,
no sus significados. Objetivo no es tarea; capacidad no es archivo; propiedad no
es prueba ejecutada. Una obligación no tiene completed/verified/migrated.

Las obligaciones preservan aceptación, falsación, verificación, propiedades,
exigibilidad, hito, owner, exclusiones, prerrequisitos y referencias a consumidores,
recursos y arquitectura. ALL/ANY/CONDITIONAL no admiten colecciones vacías
implícitamente verdaderas. Campañas y capacidades comparten referencias sin
copiar ni duplicar la entidad. La arquitectura normativa no se sustituye por
imports observados. APPROVED exige referencia de autoridad, pero no autentica al
aprobador: normatively_admitted permanece falso. El perfil exige registros
completos; el ciclo general de borradores incompletos sigue pendiente.

`domain/references.py` posee el único algoritmo de contenido. Las APIs canónicas
identity.resolve_entity y identity.validate_references son fachadas finas.
RecordSnapshot indexa cuerpos por proyecto/kind/ID/revisión, con índices read-only;
rechaza duplicados y varias revisiones actuales. No hay fallback a latest. Las
revisiones históricas se declaran explícitamente y no se promocionan a actuales.

Un anchor solo declara presencia: resolver su contenido devuelve
REFERENCED_CONTENT_UNAVAILABLE. Las pruebas mantienen visibles los cuerpos
pendientes de Scope, VerificationSpec y Constitution; no los simulan mediante
objetos vacíos. SourceCut usa otro catálogo. Los ciclos Objective/Capability son
legítimos: no se impone un DAG global a la ontología.

EntityImport exige ApprovedSourceImport, corte material exacto, conjunto finito
de revisiones y snapshot del proveedor. Cada cuerpo debe proceder de esa fuente.
Permisos con contenido, historia o cuts incompatibles generan conflicto sin
first-wins. TrustedEntityImports es contexto externo suministrado, no autenticación.
Leer un registro importado no concede traversal transitivo de sus referencias.

build_record_snapshot conecta los cuerpos con B02 y sus fuentes incluidas.
inspect_contract devuelve el registro exacto, referencias y faltas; mantiene
NOT_EVALUATED/NOT_CHECKED para ámbito y cualificación. API038 inspect_due describe
exigibilidad e hito, no calcula todavía aplicabilidad por SupportProfile.

## LC04 acotado: fuentes y registros reales

resolve_analyses recibe resultados LC03 fijados por CompileContext. Primero
registra declaraciones por clase/nombre, luego enlaza referencias adelantadas.
Los símbolos sin declaración local requieren cuerpos exactos en RecordSnapshot;
los extranjeros requieren también EntityImport explícito. La fuente del binding
debe coincidir con la procedencia del cuerpo. El enlace conserva posiciones UTF-8.

Se mantiene la gramática actual de referencias con una cadena; revisiones y
proyectos externos se fijan mediante SymbolBinding. No se introduce una sintaxis
nueva de dos/tres argumentos que el V0 actual no entiende. Los tipos por campo
proceden del contrato IR existente; no se crea un segundo evaluador normativo.

Resultado: REFERENCES_RESOLVED o REJECTED, nunca COMPILED ni TYPECHECKED. Resolver
una declaración local prueba su identidad en la unidad sintáctica, no la existencia
de un contrato de dominio realizado. Source_item conserva sus ítems no verificados:
resolver el pin de la fuente no prueba cobertura de su catálogo histórico.

Se acotan población de fuentes/declaraciones/bindings y nodos de expresiones.
No están implementados aquí sintaxis de import, módulos arbitrarios, ordenación
de dependencias, tipado general o lowering. Los descriptores inyectados no se
presentan como sustitutos de esas funcionalidades pendientes de LC04–LC06.

## Autoauditoría y mutaciones

Seis falsaciones fallaban en el primer candidato: binding con procedencia ajena;
Source nominal sin pin material; diagnóstico sin propietario; escape del presupuesto
mediante declaraciones vacías; colección mutable en resultado; metadatos nominales
incompatibles. Se corrigieron sin borrar las pruebas. Hay ataques adicionales a
presupuestos de expresiones y shadowing extranjero/local. Esto es autoauditoría,
no dictamen de un actor independiente.

Se detectan 12/12 mutaciones nuevas y 16/16 anteriores por fallos de aserción.
No se cuentan timeouts, errores de colección ni SKIP como detecciones. Las ejecuciones
se hicieron en subconjuntos y se unieron por ID único: 28 ataques dirigidos, no
una campaña exhaustiva. Ver los dos registros B03_*MUTATIONS.json.

## Ejecución: selección reproducida, no suite global

Python 3.13.5: **875 PASS, 0 FAIL, 0 SKIP**; 780 casos previos reconstruidos y
95 nuevos. La misma selección instalada en wheel aislado pasa 875 casos; los
27 módulos Guardian importados proceden de esa instalación. compileall PASS.
El árbol fuente de partida se reconstruyó exactamente como
`63227f0ab16813b97334066c61225a8e6332b01c`.

**No se ha reejecutado la suite íntegra de 976 casos del padre**. La copia local
no contiene los 196 casos de su última entrega de esquemas/reconciliación/V0
contractual. Se preservan sus archivos remotos; su resultado histórico no se
atribuye al candidato nuevo. El gate del checkout íntegro permanece NOT_RUN.
Los tests seleccionados y los nuevos se identifican mediante hashes en el registro
de ejecución. No se anuncia un total completo del repositorio como ejecutado.

Se conserva la población de 58 APIs: diez firmas nuevas y una descripción histórica
corregida (API057 exige view, no realiza inspección válida sin ella).
Hay 33 nombres de operación presentes en sus owners: el contador no demuestra
33 APIs completas. El cotejo AST de las 58 firmas pasa. El manifiesto B00 recibe
el nuevo hash de la tabla y conserva sus fuentes y pruebas exigidas; el gate B00
íntegro no se presenta como ejecutado en esta copia parcial. Los formatos y
codecs generales de los nuevos registros siguen pendientes de B06.

## Pendientes exactos

B03: borradores generales y admisión; B04: scope/aplicabilidad; B05: autoridad y
conflictos; B06: los restantes cuerpos y codecs; LC04: imports/módulos completos;
LC05/06: tipado y elaboración; LC09: cobertura histórica. Además: ejecutar checkout
íntegro, Python 3.12, análisis estático de tipos, auditor distinto e instalación
protegida. La ausencia de G-09 no bloquea desarrollo puro ni autoriza a simularlo.
