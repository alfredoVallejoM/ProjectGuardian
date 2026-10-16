# G-00 / Estados ortogonales, resultados tipados y falsas promociones

**Obligación:** G00-07. **Owners:** \`domain/outcomes.py\`, \`domain/qualification.py\` (solo modelos), \`domain/obligation.py\`.

## Requisito original

"Ningún estado de desarrollo, prueba o publicación se convierte en verdad matemática por un simple cambio de nombre o un booleano global". La implementación debe representar las dimensiones como tipos diferentes, preservar evidencias y no producir un \`completed: bool\` autoritativo.

## Ejes de estado

| Eje | Variantes | Fuente futura de autoridad |
|---|---|---|
| Source | \`UNSEEN\`, \`IDENTIFIED\`, \`RECONCILED\`, \`CONFLICTED\`, \`SOURCE_MISSING\` | Censo/reconciliación G-07/G-10 |
| NormativeDecision | \`PROPOSED\`, \`APPROVED\`, \`REJECTED\`, \`SUPERSEDED\` | Decision + approvals/G-09 |
| Commitment | \`CURRENT\`, \`FUTURE\`, \`CONDITIONAL\`, \`OPTIONAL\`, \`RESEARCH\` | CampaignRevision + Scope |
| Implementation | \`MISSING\`, \`PARTIAL\`, \`DEVELOPED\`, \`CANDIDATE\` | Delivery + code/source G-05 |
| Audit | \`NOT_REVIEWED\`, \`FINDINGS\`, \`PASS\`, \`HOLD\` | AuditRecord G-06 |
| Material | \`NOT_RUN\`, \`PASS\`, \`FAIL\`, \`BLOCKED\` | ValidationRun G-06 |
| Support | \`CURRENT\`, \`STALE\`, \`INVALIDATED\`, \`UNKNOWN_SCOPE\`, \`UNSUPPORTED\`, \`DISPUTED\` | SupportCone+evidence G-02/G-06 |
| Qualification | \`UNQUALIFIED\`, \`QUALIFIED_IN_SCOPE\`, \`DISPUTED\`, \`REVOKED\` | Qualification G-06 |
| Migration | \`UNCLASSIFIED\`, \`MAPPED\`, \`PARITY_PENDING\`, \`QUALIFIED\`, \`CLOSED\` | Preservation G-10 |

Una misma entidad puede tener Implementation=DEVELOPED, Audit=NOT_REVIEWED, Material=NOT_RUN y Qualification=UNQUALIFIED. No constituye inconsistencia.

## Contratos de tipo

- \`StatusAxis\` y cada enum del eje deben mantenerse diferenciados en el modelo serializado.
- \`StatusObservation\`: entity ref + axis + declared value + source/evidence refs + scope + revision + observer; **descripción** no concede autoridad.
- \`StatusProjection\`: valores deducidos por un mecanismo autorizado; G-00 valida estructura, G-01/G-06/G-10 construyen proyecciones con eventos/verificadores.
- \`Verdict\`: \`PASS\`, \`FAIL\`, \`UNKNOWN\`, \`CONFLICT\`, \`NOT_APPLICABLE\`; \`RuntimeErrorStatus\` por separado, incluyendo \`RESOURCE_LIMITED\`, \`INVALID_INPUT\`, \`NOT_RUN\`.
- \`DevelopmentComplete\` es predicado sobre todas las obligaciones de implementación del bloque, no un campo editable de una obligación.
- \`CampaignClosed\` necesita desarrollo completo + auditoría/material/integración/recibo, según policy, y nunca se deriva desde G-00 solo.

## Prohibiciones

1. \`Material.PASS ⇒ Qualification.QUALIFIED_IN_SCOPE\` es **falso** sin contrato de prueba y scope.
2. \`Implementation.DEVELOPED ⇒ Material.PASS\` es falso, pues puede no haberse ejecutado.
3. \`Source.RECONCILED ⇒ Implementation.DEVELOPED\` es falso.
4. \`Audit.PASS ⇒ Migration.CLOSED\` es falso si paridad no ejecutada.
5. \`Commitment.FUTURE ⇒ no aparece en visión de proyecto\` es falso; permanece visible, solo cambia exigibilidad.
6. \`Unknown ⇒ NotApplicable\` y \`Conflict ⇒ Fail\` no son conversiones implícitas.
7. No transformar \`Review.finding_count=0\` en PASS sin comprobar que el auditor cubrió todas las obligaciones originales y que la revisión fue autorizada.
8. No emitir certificado firmado desde un estado descrito o un valor de enum local.

## API propuestas

\`parse_status(axis,value)\` → \`TypedStatus | InvalidState\`.
\`validate_status_observation(observation,project_view)\` → \`StructuralValidation\`.
\`render_status_vector(observations)\` → \`StatusDescription\` con "not qualified" explícito.
\`check_illegal_promotion(from_axis,to_axis,basis)\` → diagnóstico para transiciones imposibles según modelo; delega evaluación material completa a G-06.

No habrá \`mark_complete\` o \`certify\` en \`domain/outcomes.py\`.

## Pruebas

- Comparar dos ejes con igual literal \`PASS\` no produce intercambiabilidad tipada.
- Serialización y roundtrip conservan axis y su enum específico.
- Test escrito y Material.NOT_RUN no satisfacen condición "campaña cerrada".
- Construir \`StatusObservation(qualification=QUALIFIED...)\` sin certificado se registra como afirmación no verificada, no estado canónico.
- Source.UNKNOWN y fuentes históricas incompletas quedan visibles en reporte.
- Un resultado \`RESOURCE_LIMITED\` no se equipara a \`NO\` científico ni a pass.
- Un cambio temporal que modifica Due exige ChangeSet aprobado, no cambio de StatusObservation.
- Auditoría de alcance parcial no implica cumplimiento de obligaciones no revisadas.
