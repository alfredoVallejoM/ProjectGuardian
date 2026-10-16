# 07 — Conformidad, auditoría, evidencia y certificados

## Entidades, autoridades y distinciones
`VerificationSpec` define qué probar; `TestArtifact` es código de prueba; `ValidationRun` indica ejecución material; `EvidenceRecord` registra observación; `Claim` afirma una propiedad; `QualificationRecord/Certificate` determina si un conjunto de evidencias soporta el claim bajo una política, revisión y SupportProfile.

No equivalencias: test escrito ≠ test ejecutado ≠ coverage ⇒ claim científicamente demostrado. Un PASS estructural no implica formalización matemática ni migración cerrada.

## Matriz de verificación
Structural dependency/ownership; functional positive/negative; adversarial mutations; integration real producer-consumer; scientific proof or independent oracle; migration source-target parity; resources; security/trust. Una propiedad puede exigir `ALL` de múltiples evidencias o `ANY` de rutas certificadas independientes. Los perfiles definen policy/requirements, no un booleano decidido por agente.

## Estados
`DEVELOPMENT_COMPLETE`: todas las obligaciones originales de código+tests+verificadores implementadas en fuente; ejecución material distinta.
`ADVERSARIAL_PASS`: revisión independiente si política lo requiere, por obligación y por documento, sobre candidato exacto.
`MATERIAL_PASS`: runners ejecutados, receipts reales.
`INTEGRATION_PASS`: componentes/consumidores reales conectados.
`QUALIFIED_IN_SCOPE`: garantías de dominio respaldadas.
`MIGRATION_CLOSED`: paridad y compatibilidad históricas, más disposición de origen.

## AuditRecord
ObligationRef, CandidateRevision, NormativeSnapshot, ReviewedArtifacts, IndependentReviewer, FalsificationCases, Findings, Witnesses, RequiredCorrections, DefectsByDocument, VerdictPerObligation, EvidenceRefs, HoldReasons. Un auditor no cierra diez obligaciones con "todo PASS" sin soporte individual. Si trabaja un solo agente no se inventa independencia; solicitar revisión autorizada si exigida.

## Validación material
Runner como proceso externo aislado: exact Candidate SHA, toolchain/verifier version, args, env, flags, budgets, fixtures, outputs, provenance, execution status, signal/timeouts y receipt. Un JSON redactado por modelo no es ejecución. Receipt autenticado requiere identidad confiable del emisor, no solo checksum. Usar estándares de atestaciones interoperables cuando sea apropiado, sin inventar protocolo criptográfico.

## Support and invalidation
`SupportProfile` circunscribe domain/platform/features/corpus/consumers/toolchain. `CURRENT/STALE/INVALIDATED/UNKNOWN_SCOPE/UNSUPPORTED/DISPUTED` son diferentes.
`ProtectedCone(e)` incluye inputs realmente leídos: código, config, includes, features, generated, test/oracle, verifier, schema y entorno. Reuse solo cuando equivalencia de inputs/scope está justificada. Cambio en documentación no protegida no obliga al retest global; cambio relevante o cono histórico incompleto exige nueva evaluación.

## Certificaciones honestas
SOURCE_COVERAGE, SPECIFICATION_COVERAGE, IMPLEMENTATION_COVERAGE, MATERIAL_VALIDATION, INTEGRATION, RESOURCE, SCIENTIFIC, MIGRATION. Cada certificado contiene ProjectRevision, SourceUniverse, Claim, Scope, Evidence, VerifierPolicy, Limitations. No denominadores creados por la comodidad del reporte: listar UNKNOWN/CONFLICT y fuentes sin reconciliar.

## ExplainState
Resultado = Verdict + Scope + SupportPaths + Gaps + Evidence + PolicyRevision. Los caminos informativos se distinguen de prueba/soporte. Debe ser posible explicar qué falta exactamente para cerrar cualquier obligación o campaña.

