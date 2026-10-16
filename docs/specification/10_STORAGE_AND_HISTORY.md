# 10 — Persistencia, eventos, concurrencia y recuperación

## Una autoridad, muchas vistas
Registros JSON/JSONL versionados y decisiones en Git (embedded/sidecar/federated) son autoridad normativa. SQLite es proyección reconstruible para relaciones, búsqueda FTS5 y estados derivados. Un proyecto puede conservar registros originales mediante adaptador sin copiarlos a un segundo JSON editable.

## Modelo de cambio
`ChangeSet(project_id, base_revision, actor, operation, targets, preconditions, authorization, affected_cone, idempotency_key)` produce eventos inmutables. No registrar meras lecturas como mutaciones normativas. Diferenciar valid-time histórico de transaction-time de incorporación.

## Publicación sin transacción distribuida
Resolver expected commit; evaluar con policy protegida; crear archivos y commit candidato en entorno temporal; actualizar ref autorizada con CAS; reconstruir proyección. Si falla antes del ref, no se publica. Si falla SQLite tras Git, el índice se regenera. Escritura autoritativa serial por proyecto, análisis paralelo permitido.

## SQLite derivado
Tablas de índice: projects, entities, revisions, relations, relation_participants, source_refs, contracts, obligations, campaigns, support_profiles, verification_specs, validation_runs, claims, evidence_refs, qualifications, work_packages, audit_findings, events y source_fts. Claves externas, transacciones explícitas, revisiones indexadas. No dos escritores autoritativos.

## Snapshot y replay
`Replay(history, schema_interpretation) = exact_snapshot` como obligación de determinismo. Materializaciones y cachés invalidables por revisión y schema. Detección de drift de índice contra records. Recuperación ante fallos de proceso en cada etapa de la publicación. Idempotencia de eventos/comandos y comparación de schema versions.

## Escala y datos grandes
Lista de adyacencias y SQL para grafo local; no base distribuida obligatoria. Artefactos grandes por referencia a CAS externo con digest/tamaño/retención/identidad, sin referenciar /tmp volátil como autoridad. Cache por revision/SupportProfile, evaluación de impacto incremental; propiedades de recursos con pruebas de perfiles crecientes.

## Serialización
Canonicalización determinista de material firmable (RFC 8785 donde sea adecuado), números exactos en representaciones tipadas; digest identifica bytes, no leyes matemáticas. Firmas/autenticidad provienen de emisor de confianza y política de claves; SHA256 aislado no identifica al autor.

