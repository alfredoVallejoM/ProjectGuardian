# G-00 / Esquemas versionados y compatibilidad normativa

**Obligación primaria:** G00-09. **Owner:** \`persistence/schema_registry.py\` (contrato inicial de lectura/registro; migraciones de estados persistidos completas G-01/G-12), con modelos de \`domain\`.

## Propósito

Definir representaciones persistentes tipadas que permitan compartir información entre Python, CLI, API y herramientas externas, sin permitir que lectores antiguos eliminen obligaciones que todavía no comprenden.

La validación JSON Schema se complementa con validaciones cruzadas de referencias, autoridad, scope y cambios de versiones. Un payload JSON válido no equivale a proyecto constitucionalmente válido.

## Envoltorio normativo común

Una entidad persistente de diseño tendrá, al menos:

\`\`\`json
{
  "schema": "guardian/obligation-revision/v1",
  "record_type": "OBLIGATION_REVISION",
  "project_id": "PROJECT_ID",
  "logical_id": "OBLIGATION_ID",
  "revision_id": "REVISION_ID",
  "required_normative_features": ["scope.four-valued.v1"],
  "payload": {
    "statement": "REQUIRED_CONTRACT_STATEMENT",
    "applicability_ref": "SCOPE_EXPRESSION_REF",
    "acceptance": ["ACCEPTANCE_CONTRACT_REF"]
  }
}
\`\`\`

Es un contrato **ilustrativo de diseño**, no un JSON Schema de producción ni un registro aprobado. Los campos concretos se codificarán en esquemas versionados cuando se implemente G-00.

## Validación por capas

| Capa | Qué comprueba | Qué no demuestra |
|---|---|---|
| Sintaxis JSON | Codificación de bytes y parse seguro | Identidades o verdades matemáticas |
| JSON Schema | Campos y tipos, discriminantes y \`additionalProperties\` | Referencias a otros objetos existentes |
| Versión/feature | Si el lector comprende lo normativo | Que una fuente sea auténtica |
| Modelo de dominio | Invariantes internos y referencias disponibles | Contenido de un Git blob aún no leído |
| Evaluador constitucional | Normas aplicables al snapshot en memoria | Certificación de un runner externo |
| Gatekeeper futuro | Permisos y publicación protegida | Validez universal de teoremas |

\`required_normative_features\` es un conjunto declarado de semánticas que el lector **debe** entender. Una etiqueta informativa desconocida puede preservarse para roundtrip; una característica normativa desconocida produce \`UNSUPPORTED_NORMATIVE_FEATURE\` y bloquea admisión.

## Políticas de compatibilidad

- Una versión nueva con campo estrictamente informativo puede ser compatible si el lector conserva su interpretación y no lo toma como autorización.
- Una variante nueva de enum de estados o tipo normativo desconocido debe producir resultado \`UNSUPPORTED_VARIANT\`.
- Cambios de meaning o de predicates normativos requieren versión incompatible y migración revisada.
- Un campo faltante que es obligatorio en una versión no se rellena con defaults permisivos.
- \`null\`, campo omitido y conjunto vacío tienen semánticas diferentes cuando el contrato lo requiere.
- \`source_refs\` no puede reescribirse al importar registros sin traza.
- Una igualdad de digest JSON no significa equivalencia de sujetos o de SourceUniverse sin scope.

## Serialización de tipos

Representar IDs con discriminante/tipo, no strings desnudos intercambiables; incluir ProjectId/kind en EntityRef. Los enteros exactos que exceden límites JSON interoperables se codifican como strings tipados u otro contrato exacto explícito. Valores NaN/infinito se rechazan en campos normativos que requieren canonicalización reproducible. Los textos Unicode conservan identidad, sin inferir aliases matemáticos.

La canonicalización de digests y atestaciones podrá adoptar RFC 8785, pero su motor y validación criptográfica pertenecen a G-06/G-12. G-00 exige que el contrato de entrada sea inequívoco y pueda serializarse sin pérdida.

## Funciones propuestas

- \`read_schema_descriptor(schema_id,version,known_registry)\` → \`KnownSchema | UnknownSchema\`.
- \`validate_envelope(envelope,reader_features)\` → \`SchemaValidation\`, con \`UNSUPPORTED_NORMATIVE_FEATURE\` si corresponde.
- \`decode_record(payload,known_types)\` → \`TypedDomainRecord | DecodeError\`.
- \`encode_record(record)\` → \`CanonicalReadyRecord\` sin calcular hash autoritativo.
- \`check_reader_compatibility(writer_schema,reader_schema,features)\` → \`Compatible | RequiresMigration | Unsupported\`.
- \`validate_schema_refs(record,view)\` → diagnósticos de integridad referencial del snapshot.

No implementar en G-00 una base de datos de migraciones, el replay histórico, la transacción Git ni el editor de esquemas. Se implementará el registro mínimo que permite leer/validar los contratos fundacionales.

## Casos de prueba

1. Documentos de cada tipo roundtrip sin perder discriminator.
2. \`required_normative_features = ["unknown-law.v9"]\` produce BLOCK y no se ignora.
3. \`additionalProperties\` informativas permitidas bajo namespace declarado; desconocidos normativos prohibidos.
4. Campo obligatorio omitido produce error con JSON path.
5. \`null\` no se confunde con \`[]\` en \`acceptance\`.
6. Enum desconocido no se convierte en el primer enum válido ni en \`UNKNOWN\` de otro eje.
7. SourceRef sin project identity se rechaza.
8. Un entero grande conserva exactitud tras ida/vuelta.
9. JSON con NaN no se acepta como registro normativo.
10. Migración de schema que cambia garantía se clasifica como \`RequiresMigration\` y no se aplica sin autorización.
11. Una versión anterior válida conserva su interpretación; un lector nuevo no retroactivamente cambia los contratos ratificados en su revisión.
