# 02 — Ontología, estructuras de datos, identidades y estados

## Project Contract
`ProjectContractRevision = (SourceUniverse, NormativeSet, RelationGraph, ObservedImplementation, Assurance, History)`. El propósito y sus capacidades son distintos de las campañas; la relación entre especificación/implementación/evidencia es muchos-a-muchos.

## Entidades fundamentales
`Project`, `ProgramRevision`, `SourceUniverse`, `ConstitutionRule`, `Decision`, `Objective`, `Capability`, `Property`, `Obligation`, `ObligationRevision`, `CampaignRevision`, `ArchitectureRevision`, `Contract`, `SupportProfile`, `ImplementationUnit`, `API`, `Consumer`, `Verifier`, `VerificationSpec`, `ValidationRun`, `Evidence`, `Claim`, `Qualification`, `Certificate`, `ChangeSet`, `AuditFinding`, `WorkPackage`. Su autoridad proviene de su propietario canónico, no del índice o UI.

**Separaciones obligatorias:**
- Objetivo = qué se quiere alcanzar; capacidad = comportamiento; propiedad = garantía; obligación = compromiso exigible y criterio de verificación; implementación = realización; prueba escrita = especificación/material; ejecución = observación; claim = afirmación; certificado = resultado autorizado.
- `LogicalId` identifica entidad transversional; `RevisionId` fija su versión; `ContentDigest` fija bytes; `Alias` comunica nombres legibles. No hay equivalencia automática entre esas relaciones.
- Referencias `EntityRef(project_id, entity_id, revision_id)`; lo interproyecto necesita política de importación.

## ObligationRevision (contrato)
ID, versión, procedencia, enunciado, clase, ámbito, aplicabilidad estructurada, exigibilidad por hito, propiedades exigidas, aceptación positiva, falsaciones, VerificationSpec refs, fuentes históricas, arquitectura aplicable, consumidores, recursos, dependencias conjuntivas/alternativas, owner, exclusiones, linaje de refinamiento/generalización/sustitución. Nunca un `completed: bool` mutable de autoridad.

## CampaignRevision
ID estable, objetivo, `membership` de obligaciones por scope/hito, prerequisitos, contratos de interfaces, exclusiones, vértices consumidores, CompletionPolicy, evidencias exigidas, régimen de ampliación, revisión base. Un mismo `ObligationId` puede ser reutilizado por varias campañas; no duplicar autoridad.

## SupportProfile
Perfil tipado y abierto: candidate SHA, características/flags, plataforma, versión de compilador, corpus y fixtures, dominio matemático, representaciones, consumidores, runtime/toolchain, presupuestos, versión de política y alcance temporal. Las dimensiones matemáticas especializadas delegan predicados en verificadores admitidos.

`Applicable(o,S) ∈ {YES, NO, UNKNOWN, CONFLICT}`. `NO` requiere justificación; desconocido no equivale a falso. El cierre separa aprobada/aplicable/exigible.

## Ejes ortogonales de estado
- Fuente: UNSEEN/IDENTIFIED/RECONCILED/CONFLICTED/SOURCE_MISSING.
- Decisión: PROPOSED/APPROVED/REJECTED/SUPERSEDED.
- Compromiso: CURRENT/FUTURE/CONDITIONAL/OPTIONAL/RESEARCH.
- Implementación: MISSING/PARTIAL/DEVELOPED/CANDIDATE.
- Auditoría: NOT_REVIEWED/FINDINGS/PASS/HOLD.
- Material: NOT_RUN/PASS/FAIL/BLOCKED.
- Soporte: CURRENT/STALE/INVALIDATED/UNKNOWN_SCOPE/UNSUPPORTED/DISPUTED.
- Cualificación: UNQUALIFIED/QUALIFIED_IN_SCOPE/DISPUTED/REVOKED.
- Migración: UNCLASSIFIED/MAPPED/PARITY_PENDING/QUALIFIED/CLOSED.

Se derivan de eventos y evidence, no se editan manualmente para conceder autoridad.

## Modelo de ingeniería
Usar Python 3.12+, `dataclasses(frozen=True, slots=True)`, IDs nominales, enums y uniones discriminadas, `Protocol` en fronteras reales y validación JSON Schema del almacenamiento. Evitar grandes jerarquías `BaseEntity`, ORM como semántica y relaciones textuales sin versión.

