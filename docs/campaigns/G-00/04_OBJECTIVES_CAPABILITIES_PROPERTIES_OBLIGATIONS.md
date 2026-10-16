# G-00 / Ontología completa de objetivos, capacidades, propiedades y obligaciones

**Obligación primaria:** G00-05; también G00-07/08. **Owners:** \`domain/objective.py\`, \`capability.py\`, \`property.py\`, \`obligation.py\`, \`architecture.py\`, \`campaign.py\`.

## Por qué separar estas entidades

Una tarea de implementación no representa por sí misma lo que el proyecto debe garantizar. Una funcionalidad puede tener varios contratos, propiedades y realizaciones; una propiedad puede ser exigida por múltiples capacidades; una obligación puede pertenecer a varias campañas. La topología es muchos-a-muchos.

| Tipo | Pregunta esencial | Debe referir |
|---|---|---|
| \`ObjectiveRevision\` | ¿Qué resultado global se persigue? | Propósito, criterios y límites; fuentes/decisiones |
| \`CapabilityRevision\` | ¿Qué comportamiento debe ser posible? | Owner, contexto, contratos de inputs/outputs, propiedades |
| \`PropertyRevision\` | ¿Qué garantía exige el comportamiento? | Enunciado, hipótesis, ámbito, evidencia exigida |
| \`ObligationRevision\` | ¿Qué compromiso se debe cumplir y cómo? | Propiedad/objetivo de origen, aceptación, falsación, verificación, hito |
| \`ArchitectureRevision\` | ¿Qué fronteras y propietarios permiten implementarlo? | Owners, componentes, interfaces, dependencias autorizadas/prohibidas |
| \`CampaignRevision\` | ¿Cuándo se agrupan/exigen estas obligaciones? | Membership por scope/hito y ClosurePolicy |
| \`ImplementationUnit\` | ¿Dónde está realizada una capacidad? | Símbolos/archivos, código y consumidor (G-05/G-07 completan) |
| \`VerificationSpec\` | ¿Qué prueba se necesita? | Propiedad, método, ámbito y falsaciones (G-06 completa) |
| \`Claim\` | ¿Qué afirmación quisiéramos acreditar? | Sujeto, propiedad y perfil, no PASS automático |

**Un tipo referenciado por G-00 no implica que G-00 implemente todas las operaciones de sus campañas consumidoras.** G-00 define los contratos y validadores locales necesarios para evitar mezcla de identidades.

## ObjectiveRevision

Campos: LogicalId, RevisionId, propósito verificable, exclusions, source refs, decision refs, related capability refs, lifecycle normative-state. Una descripción "crear mejor software" sin criterio permite \`PROPOSED_GOAL\` pero no basta como obligación ejecutable.

Funciones: \`define_objective\`, \`validate_objective\`, \`link_capability_to_objective\` (validación de referencia local, persistencia G-01). No cambia source/authority.

## CapabilityRevision

Campos: ID, revisión, SemanticOwnerRef, behavior contract, input/output kind references, domain/applicability, required property refs, contract_version, source_refs, declared exclusions. Múltiples algoritmos/providers pueden realizar una sola capability. Owner semántico no es el mismo que módulo o crate.

Funciones: \`define_capability\`, \`validate_capability\`, \`check_capability_property_refs\`; resultados no certifican realización.

## PropertyRevision

Campos: ID, revisión, enunciado, ámbitos, hipótesis, forbidden claims, VerificationSpec refs, source normative refs y \`assertion_kind\`. La propiedad es independiente de su test y del código que la realiza.

Funciones: \`define_property\`, \`validate_property\`; no generar automáticamente teoremas ni pasar \`PROVED\`.

## ObligationRevision

Campos mínimos exactos:
- \`obligation_id\`, \`revision_id\`, \`kind\`, \`statement\`.
- \`applicability\` y \`commitment_scope\` / due milestones.
- \`required_property_refs\`, \`acceptance_contract\`, \`falsification_contract\`.
- \`verification_spec_refs\`, \`source_refs\`, \`authority_ref\`.
- \`architecture_rule_refs\`, \`consumer_contract_refs\`, \`resource_contract_refs\`.
- \`prerequisite_expr\` (ALL/ANY/conditional según sintaxis admitida).
- \`owner_ref\`, \`exclusions\`, \`lineage_refs\`.

No contiene \`completed: bool\`, \`verified: bool\` ni \`migrated: bool\` como campos de autoridad editables. Puede describir que el contrato requiere determinada evidencia; la evidencia real y su validez se almacenan fuera.

Funciones: \`define_obligation\`, \`validate_obligation\`, \`check_obligation_source\`, \`inspect_obligation_contract\`. Refinamiento/sustitución material y publicación corresponden a G-01/G-09.

## CampaignRevision

Una campaña referencia obligaciones por ID+revisión; sus membership pueden ser incondicionales, condicionales o explícitamente alternativas con política. Un requisito compartido se cuenta una vez para la entidad, aunque varias campañas lo exijan. El concepto \`DUE_NOW\` debe distinguirse de \`APPROVED_FUTURE\`; no mover exigibilidad por decisión del constructor.

G-00 define \`CampaignRevision\`, \`Membership\` y validaciones de campos/referencias/alcance en un snapshot en memoria. G-01 controla cambios de membership y G-10 calcula cobertura avanzada.

## ArchitectureRevision

G-00 posee **el tipo normativo** de componentes, owners, interfaces, allowed/required/forbidden dependencies y sus revisiones; no explora imports del código real (G-05/G-07). Una arquitectura sin módulos de implementación todavía puede estar correctamente especificada. Lo contrario, módulos observados con nombres coincidentes, no demuestra que el diseño esté completo.

## Contratos many-to-many y alcance

Una sola prueba puede ser relevante para varias propiedades; una sola obligación puede exigir varias pruebas; una misma fuente puede explicar varias capacidades. G-00 valida que los ID_refs posean tipos y proyectos correctos. La gramática n-aria del grafo, las proyecciones de owners y SupportCone se implementan en G-02. No simular la ausencia del grafo con un "un archivo por obligación".

## Errores de dominio

\`EMPTY_STATEMENT\`, \`MISSING_OBJECTIVE_SOURCE\`, \`INVALID_CAPABILITY_OWNER\`, \`PROPERTY_NOT_FOUND\`, \`REQUIRED_ACCEPTANCE_MISSING\`, \`FALSIFICATION_MISSING\`, \`UNKNOWN_VERIFICATION_PROFILE\`, \`MIXED_SCOPE\`, \`AMBIGUOUS_MEMBERSHIP\`, \`ORPHAN_REFERENCE\`, \`UNTRUSTED_APPROVAL\`, \`DUPLICATE_LOGICAL_ID\`.

No todos los campos son obligatorios para \`PROPOSED_DRAFT\`, pero para exigir una obligación admitida la validación debe identificar exactamente los requisitos normativos que faltan. No transformar borradores incompletos en obligaciones READY para ejecución.

## Pruebas de aceptación

- Una capacidad con dos propiedades diferentes no colapsa su cumplimiento en un único booleano.
- Dos capacidades pueden exigir la misma propiedad con ID compartido sin duplicar esa propiedad.
- Una obligación puede aparecer en dos campañas sin duplicar su autoridad ni cambiar el ámbito.
- Una implementación observada solo apunta a una capacidad, no modifica su contrato.
- Un \`VerificationSpec\` sin \`ValidationRun\` no produce estado material aprobado.
- \`Objective\` con fuente aprobada y capability pendiente es válido como planificación.
- Un \`Capability\` con comportamiento restringido no reemplaza automáticamente un contrato general anterior.
- Obligation sin falsaciones cuando el perfil las exige recibe diagnóstico.
- Un contrato de investigación no se promociona a compromiso current sin decisión.
- Un contrato con referencia a property/campaign de otro proyecto se rechaza sin import aprobado.
- Una campaña con todos sus members documentados pero con fuente no cubierta no afirma \`SOURCE_COVERAGE_PASS\`.

**Regla constitucional:** diseño de entidades = definición de información, no prueba de su realización. La separación deberá mantenerse en tipos, funciones y cualquier API posterior.
