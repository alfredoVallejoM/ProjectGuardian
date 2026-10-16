# 04 — Evolución abierta de contratos, obligaciones y campañas

## Principio
Un proyecto no es un plan cerrado para siempre. Debe admitir nuevas obligaciones, campañas, propiedades, owners y contratos a lo largo de meses/años. Cada modificación es una operación explícita `ChangeSet` sobre una revisión inmutable `P_r`; nunca CRUD libre que reescribe obligaciones ratificadas.

`P_(r+1) = Apply(P_r, Δ_r)` si y solo si el cambio satisface la constitución y las autorizaciones. Un cambio rechazado no modifica estado publicado.

## Vocabulario operativo
`AddObjective, AddCapability, AddProperty, AddObligation, AddCampaign, ExtendCampaign, RefineObligation, GeneralizeContract, SupersedeObligation, AddRelation, ChangeArchitecture, AttachEvidence, RecordFinding, ReopenScope, RevokeQualification, ChangeCommitment, ProposeConstitutionAmendment`.

Cada operación define precondiciones, principal/autoridad exigidos, transformaciones, efectos, postcondiciones, invalidaciones, trazabilidad y tipo de prueba. Una campaña o requisito adicional no requiere tocar el código del núcleo. Un perfil normativo desconocido nunca se ignora silenciosamente.

## Refinar, ampliar, sustituir
- Refinar una propiedad P con P' exige demostrar P' ⇒ P sobre el ámbito histórico o solicitar cambio normativo; no basta declaración de un agente.
- Generalizar el dominio mantiene la equivalencia de obligaciones antiguas sobre D_old y añade requisitos sobre el nuevo dominio.
- Superseder obliga a registrar `lineage`, decisión aprobada, mapeo de consumidores, compatibilidad y razón.
- Reabrir no borra el certificado histórico; marca estado/invalidation con causas.
- `CURRENT/FUTURE/OPTIONAL/RESEARCH` es dimensión de compromiso versionada; el constructor no mueve un requisito CURRENT a FUTURE para cerrar una campaña.

## Cambio tras certificación
Una campaña r con 12/12 cualificadas puede añadir o13 en r+1. El certificado de r permanece como hecho histórico y solo soporta r+1 si los conos siguen aplicables; o13 no se hereda. Si una obligación revela defecto en claim histórico, invalidar/revocar el soporte afectado.

## Transacciones y concurrencia
Cambios fijan base_revision, idempotency_key y authorized principal. Read-set normativo y write-set determinan colisiones, además de ImpactCone. Un único proceso de admisión por proyecto verifica revision Git actual, publica con CAS y reconstruye índice SQLite. Dos autores pueden preparar candidatos en paralelo, pero no alterar la autoridad publicada sin reconciliación.

## Esquemas y evolución de software
La estructura persistente lleva version y required_normative_features. Un lector que no comprende una característica normativa bloquea la admisión, no la omite. Versiones de schema compatibles solo cuando significado y garantía se preservan; cambios de semántica requieren migración y pruebas.

## Invariantes verificables
Non-erasure, replay deterministic, no partial commit, history preserved, no unearned certification on new obligations, no self-ratification, reader-old-normative-fail-closed, valid ownership, traceable supersession. Properties testing con secuencias aleatorias de comandos.

