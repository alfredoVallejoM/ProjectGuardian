# G-00 / Identidades normativas, revisiones, digests y aliases

**Obligaciones:** G00-01 y G00-08. **Owner primario:** \`domain/identity.py\`. **No implementado.**

## Tipos independientes

| Tipo | Significado | Regla fundamental |
|---|---|---|
| \`ProjectId\` | Namespace del proyecto | No se reutiliza para identificar una obligación |
| \`EntityId\` | Identidad lógica estable por entidad y clase | Sobrevive cambio de nombre/ruta/campaña |
| \`RevisionId\` | Versión inmutable de una entidad o snapshot | No es un digest ni una rama |
| \`ContentDigest\` | Identidad de bytes bajo algoritmo | No prueba equivalencia de contrato |
| \`EntityKind\` | Clase semántica de la identidad | No puede inferirse por la etiqueta del campo |
| \`Alias\` | Nombre humano o ID histórico (p. ej. FC2-M0-OB-007) | No sustituye LogicalId ni asegura unicidad global |
| \`SourceRef\` | Referencia a fuente observada, independiente de su autoridad | No equivale a aprobación de la fuente |
| \`EntityRef\` | \`(project_id, kind, entity_id, revision_id)\` | Debe resolver en snapshot o producir diagnóstico |

Implementación Python propuesta: \`dataclass(frozen=True,slots=True)\` de envoltura para clases de ID. \`typing.NewType\` aislado no garantiza nominalidad en tiempo de ejecución, por lo que el parser deberá producir el tipo exacto y no aceptar intercambios implícitos. El alias puede permanecer como cadena Unicode de presentación, pero los IDs canónicos deberán seguir una gramática estable y explícita.

## Semántica de construcción y parsing

- \`parse_project_id(text)\` comprueba cadena, longitud, namespace y gramática; entrega \`ProjectId\` o \`InvalidIdentity\`.
- \`parse_entity_id(project,kind,text)\` valida identidad local; rechaza cambios de kind o project por conversión implícita.
- \`parse_revision_id(text)\` produce token opaco versionado. Un \`RevisionId\` no puede construirse a partir de branch name sin resolver el snapshot.
- \`parse_digest(algorithm,hex)\` valida algoritmo admitido, longitud exacta, alfabeto hexadecimal y normalización; rechaza truncamientos como si fueran hashes completos.
- \`attach_alias(identity,alias,source)\` registra una relación alias→entidad con procedencia; al encontrar dos candidatos no elige uno.
- \`resolve_entity(ref,snapshot)\` exige ProjectId, Kind y RevisionId existentes y exactos, salvo política especial de importación ya aprobada.
- \`encode_identity\` / \`decode_identity\` conservan tipo y valores en roundtrip, sin conversión implícita entre \`EntityId\` y \`RevisionId\`.

**Generación de IDs:** la aleatoriedad o el reloj se suministran desde la capa externa; el dominio valida, no consulta reloj ni RNG. Los UUID/IDs legibles podrán ratificarse en G-00 como formato concreto. Una propuesta que fije un timestamp como identidad lógica deberá rechazarse si no garantiza estabilidad en migraciones/renombres.

## Invariantes

\[
\text{ProjectId}\neq\text{EntityId}\neq\text{RevisionId}\neq\text{Digest}\neq\text{Alias}
\]

La igualdad de IDs requiere tipo, namespace y valor compatible; misma cadena textual en tipos distintos no implica igualdad. La igualdad de digest requiere algoritmo y bytes en el mismo dominio de serialización; igualdad de hash de artefactos no implica que dos sujetos matemáticos sean idénticos.

**Referencias flotantes:** podrán existir solicitudes de resolución por alias o HEAD *para navegación*, pero no forman parte de un contrato admitido o certificado hasta resolverse a revisión explícita.

## Errores con diagnósticos

\`EMPTY_ID\`, \`INVALID_ID_SYNTAX\`, \`WRONG_ID_KIND\`, \`WRONG_PROJECT\`, \`REVISION_REQUIRED\`, \`UNKNOWN_REVISION\`, \`AMBIGUOUS_ALIAS\`, \`UNSUPPORTED_DIGEST\`, \`DIGEST_MALFORMED\`, \`DUPLICATE_LOGICAL_ID\`, \`ORPHAN_REFERENCE\`.

Cada error incluye path JSON, valor rechazado seguro para logs, tipo esperado y causa. No se oculta error de tipo mediante conversión a \`str\`.

## Casos de aceptación

**Positivos:** roundtrip de cada tipo, un mismo alias en dos proyectos independientes, renombrado de carpeta conservando \`EntityId\`, un mismo objeto con dos \`RevisionId\`, referencias de revisión anteriores legibles sin sobrescribir.

**Negativos:** la misma cadena como \`ProjectId\` y \`EntityId\` nunca se intercambia; alias duplicado en mismo ámbito queda ambiguo; digest incompleto; referencia a revisión futura/inexistente; \`SourceRef\` sin corte inmutable no autoriza certificación; serialización que pierde \`kind\`.

**Propiedades generativas:** inyectividad de serialización por tipo; parse/encode/parse estable; ausencia de mutación de objetos congelados; resolución idéntica para el mismo snapshot; renombrado de ruta no altera referencia lógica.

## Fronteras

\`domain/identity.py\` posee wrappers, validadores y referencias. \`domain/source.py\` posee el significado de fuente; \`program/revision.py\` (G-01) posee historia de revisiones, \`adapters/git/reader.py\` (G-07) resuelve commits, \`persistence/canonicalization.py\` (G-06) fija digest de bytes. G-00 no debe implementar estas responsabilidades externas para "completar" identidades.
