# G-00 — Decisiones de diseño que debemos ratificar antes de autoría

**24 decisiones técnicas subordinadas** a ADR preexistentes. No sustituyen PG-ADR-001…030 ni son ratificaciones automáticas. Se discuten por contrato, verificadores y consecuencias; todo cambio de alcance necesita su decisión autónoma.

| ID | Tema | Propuesta | ADR matriz | Obligación | Falsación |
|---|---|---|---|---|---|
| `G00-DD-001` | Identity runtime wrappers | Frozen nominal value objects for ProjectId EntityId RevisionId and Digest, not plain strings/NewType alone | `PG-ADR-004` | G00-01 | A cast from ProjectId to RevisionId must fail at runtime |
| `G00-DD-002` | Canonical ID grammar | ASCII constrained canonical tokens with scoped project/kind; human aliases can be Unicode | `PG-ADR-004` | G00-01 | Malicious path-like or empty identifier rejected |
| `G00-DD-003` | Revision pinning | EntityRef always pins RevisionId; browser navigation by HEAD resolved outside normative domain | `PG-ADR-004` | G00-01, G00-08 | Reference without revision cannot be qualified |
| `G00-DD-004` | Digest separation | Store algorithm and exact byte digest; do not treat digest as logical entity identity | `PG-ADR-004` | G00-01 | Equal bytes do not imply same owner or authority |
| `G00-DD-005` | Alias ambiguity | Alias resolution is scoped and can return ambiguous; never first result wins | `PG-ADR-004` | G00-01, G00-08 | Two alias matches emit AMBIGUOUS_ALIAS |
| `G00-DD-006` | Project authority modes | EMBEDDED/SIDECAR/FEDERATED storage modes with one normative owner per datum | `PG-ADR-001` | G00-02 | Federated views retain independent Git revisions |
| `G00-DD-007` | Foreign source import | ApprovedImport must scope source and contract; G00 accepts only external trust context | `PG-ADR-001` | G00-02, G00-03, G00-08 | A file grant does not authorize whole repository |
| `G00-DD-008` | Source cut ontology | Separate immutable Git cuts, versioned documents and approved decisions; no branch-only authority | `PG-ADR-002` | G00-03 | Pinned tree does not assert AST complete |
| `G00-DD-009` | Source completeness | Known missing and exclusions visible in SourceUniverse; no global coverage by current records alone | `PG-ADR-012` | G00-03 | Incomplete source inventory prevents complete claim |
| `G00-DD-010` | ProjectContract aggregate | Composed immutable references to versioned entities; no giant mutable Project object | `PG-ADR-002` | G00-05 | Shared Property retains single ID across capabilities/campaigns |
| `G00-DD-011` | Obligation non-completion flag | ObligationRevision owns requirement not execution status | `PG-ADR-003` | G00-05, G00-07 | Changing a status field cannot certify obligation |
| `G00-DD-012` | Scope AST | Typed Atom/All/Any/Not plus trusted verifiers; no embedded project scripts | `PG-ADR-010` | G00-06 | Project-supplied eval code rejected |
| `G00-DD-013` | Four-valued applicability | Belnap-style evidence pair YES/NO/UNKNOWN/CONFLICT with witnesses | `PG-ADR-010` | G00-06 | UNKNOWN and CONFLICT not converted to NO |
| `G00-DD-014` | Vacuous applicability | Empty ALL/ANY rejected unless explicit approved TRUE/FALSE constant | `PG-ADR-010` | G00-06 | An empty required predicate cannot auto-PASS |
| `G00-DD-015` | Milestone independence | Applicability separate from ratification and temporal exigibility | `PG-ADR-011` | G00-05, G00-06, G00-07 | Future obligation remains visible but not automatically due |
| `G00-DD-016` | Authority input | G00 evaluator receives AuthorityContext from external trusted boundary; no self-signing | `PG-ADR-023` | G00-04, G00-10 | Textual role RATIFIED cannot grant authority |
| `G00-DD-017` | Partial precedence | Observed source fact and ratified norm are incomparable types; approved scoped supersession only | `PG-ADR-003` | G00-04, G00-11 | Latest source text does not override constitutional rule |
| `G00-DD-018` | Conflict localization | ConflictRecord stores both witnesses, scope intersection, affected claims | `PG-ADR-010` | G00-11 | Disjoint conflicts do not block unrelated components |
| `G00-DD-019` | Pure rule registry | Trusted versioned RuleEvaluatorRegistry contains only pure registered functions | `PG-ADR-018` | G00-10 | Project plugin cannot execute arbitrary code as policy |
| `G00-DD-020` | Status axes | Source/Decision/Commitment/Implementation/Audit/Material/Support/Qualification/Migration distinct | `PG-ADR-011` | G00-07 | Implementation.DEVELOPED does not yield Material.PASS |
| `G00-DD-021` | Schema versions and features | Reader blocks unknown normative feature; informational extensions only in declared namespace | `PG-ADR-004` | G00-09 | Old schema reader cannot ignore new normative rule |
| `G00-DD-022` | Deterministic budgets | Bounded pure evaluation returns RESOURCE_LIMITED with unexamined rules | `PG-ADR-018` | G00-06, G00-10 | Budget exhaustion does not produce PASS |
| `G00-DD-023` | Typed diagnostics | Stable error codes with path, rule, revision, witness and remediation | `PG-ADR-003` | G00-08, G00-09, G00-10 | Invalid input distinguished from failed property |
| `G00-DD-024` | G00 trust bootstrap | Until G-09 is real use externally controlled reviewer/policy, never fake attested Gatekeeper | `PG-ADR-023` | G00-04, G00-10, G00-12 | G00 development may finish yet cannot self-certify trusted publication |

## Procedimiento de decisión
1. Revisar obligación G00-XX original y cláusulas detalladas relacionadas.
2. Evaluar si la propuesta es un refinamiento de la decisión superior o introduce una obligación nueva.
3. Identificar interfaces, módulos, consumidores y tests afectados.
4. Ratificar, mantener HOLD o proponer una enmienda; dejar evidencia y revisión explícitas.
5. No cambiar la condición de cierre con una 'simplificación' que la haga cumplir sin código real.

## Aspectos de implementación pendientes
Cada decisión aprobada deberá quedar conectada a los contratos de API, JSON Schema, casos adversarios y, cuando exista, a los módulos reales. Las propuestas no conceden permisos ni actualizan el estado de ejecución material.
