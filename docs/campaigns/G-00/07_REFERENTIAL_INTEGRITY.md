# G-00 / Integridad referencial, ámbitos y referencias externas

**Obligación primaria:** G00-08. **Owners:** \`domain/identity.py\`, \`domain/source.py\`, \`domain/project.py\`, validadores de entidades respectivas.

## Vista de resolución inmutable

\`ReadOnlyProjectView\` contiene \`project_id\`, \`program_revision_ref\`, tabla de entidades por kind/ID/revision, decisiones, constitución, catálogo de imports autorizados **como hechos de un contexto de confianza externo**, y mapa de alias de presentación. No debe mantener un puntero global mutable a "proyecto activo".

\`EntityRef\` exige \`project_id\`, \`EntityKind\`, \`LogicalId\` y \`RevisionId\`. \`SourceRef\` es otro tipo de referencia; nunca se resuelve mediante un \`EntityId\` genérico de forma implícita.

## Algoritmo de resolución

\`resolve(ref, view, expected_kind, import_grants)\`:
1. Validar sintaxis y tipo nominal del \`ref\`.
2. Comparar \`ProjectId\` de referencia y snapshot.
3. Si distinto, verificar la presencia de \`ApprovedSourceImport\` específico, scope y version. Ausencia => \`FORBIDDEN_CROSS_PROJECT_REF\`; aprobación textual no autenticada => \`REQUIRES_EXTERNAL_AUTHORITY\`.
4. Comprobar \`expected_kind\` y \`EntityKind\` observado, nunca equivalencia por nombre.
5. Comprobar que la revisión referida existe y que su raíz normativa está dentro del snapshot/revisión autorizada, o sea un histórico referenciado explícitamente.
6. Si el ref es alias, resolver a un candidato exacto; más de uno => \`AMBIGUOUS_ALIAS\`.
7. Verificar las restricciones específicas del campo (\`PropertyRef\` como propiedad; \`OwnerRef\` como owner; \`VerificationSpecRef\` como contrato de prueba).
8. Retornar \`ResolvedEntity\` o \`ResolutionIssue\` con path, referencia exacta y causa, sin alterar el snapshot.

\`validate_entity_graph_locally(entities,view)\` comprobará integridad de referencias del **snapshot recibido**, no hará BFS de todo un corpus remoto. El grafo tipado completo y su closure son G-02.

## Integridad relacional

- Relación Objective→Capability puede ser múltiple; si una Capability tiene dos objetivos no se duplica su identidad.
- Obligation→Property puede ser múltiple; una obligación no se reduce a único test.
- Campaign→Obligation es por referencias, no snapshots de copia editable.
- Declared SourceRef→Project debe estar permitido; un archivo de otra organización no es autoridad del proyecto por su URL.
- Una revisión antigua puede referenciarse como histórica, pero no usarse como \`CURRENT\` sin comparar la revisión autorizada.
- Si se detecta un ciclo genérico en objetivos/capacidades, no se rechaza por defecto: las restricciones de ciclos se aplican **solo a dependencias strict-DAG** de G-02.
- Cuando se pide equivalencia de alias y hay múltiples candidatos, no se elige por orden de diccionario ni por timestamp.

## Reglas de seguridad de paths y fuentes

La ruta de source se interpreta dentro del repositorio correspondiente, con separadores normalizados, sin prefijos absolutos, componentes \`..\` ni transformaciones de Unicode/case que generen colisiones no declaradas. Rutas de diferentes repos son independientes. El codec no debe convertir un locator HTTP arbitrario en \`SourceRef\` de autoridad Git sin resolverlo.

No ejecutar archivos, follow symlinks externos, acceder a red ni comprobar content hashes dentro de \`domain\`. Corresponde a SourceReader G-07 y al Gatekeeper G-09.

## Resultados tipados

\`RESOLVED\`, \`NOT_FOUND\`, \`KIND_MISMATCH\`, \`PROJECT_MISMATCH\`, \`REVISION_MISMATCH\`, \`AMBIGUOUS_ALIAS\`, \`UNAPPROVED_IMPORT\`, \`UNKNOWN_AUTHORITY\`, \`SOURCE_UNAVAILABLE\`, \`INVALID_PATH\`.

Cada error proporciona objeto referido y campo responsable; un resultado \`NOT_FOUND\` no es \`NOT_APPLICABLE\` de una obligación.

## Fixtures de falsación

1. Proyecto A con entity \`X\` de clase Capability y proyecto B con \`X\` Property: nunca resolver como misma entidad.
2. RevisionId de \`X\` no disponible en snapshot pero alias sí: no inferir latest revision.
3. Un ObligationRef a una CapabilityRef del mismo ID es \`KIND_MISMATCH\`.
4. Un import externo con grant para archivo único no autoriza otros archivos del repo.
5. Un source revision presente en un registro no verifica su contenido.
6. Rutas \`../other\`, absolutas y escape de namespace son rechazadas.
7. Doble alias en mismo ámbito queda \`AMBIGUOUS_ALIAS\`.
8. Dos referencias válidas a una misma propiedad desde campañas distintas no duplican su autoridad.
9. Un symlink no autoriza path fuera del repositorio.
10. Un catálogo de proyectos vacío produce errores explícitos, no fallback al primer proyecto registrado.
