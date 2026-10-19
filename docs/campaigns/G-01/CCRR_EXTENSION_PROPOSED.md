# G-01 — Ampliación contractual CCRR (PROPUESTA)

Autoridad: NO RATIFICADA. Todas las 12 obligaciones originales de architecture/campaigns.json se conservan, sin afirmar código, tests o certificación material.

## Objetivo y frontera

Añadir y reformular compromisos de forma versionada y conservadora mediante comandos semánticos.. Exclusión: No CRUD libre, no borrar ni rebajar obligaciones ratificadas.. Hito selfhost: SH-03. Interfaces: INT-01, INT-08. No PATCH normativo; enmienda tiene semántica distinta de refinamiento conservador.

## Matriz íntegra

Cada fila añade una condición de ingeniería candidata y conserva la falsación original. No es un nuevo identificador normativo.

| ID | Realización exigida originalmente | Refuerzo de garantía propuesto | Falsación original |
|---|---|---|---|
| G01-01 | ChangeSet con base_revision, actor, operaciones discriminadas e idempotencia | ChangeSet con pre/post tipados | Se modifica autoridad sin evento |
| G01-02 | AddObligation y AddCampaign sin editar codigo del motor por tipo/número | Añadir sin hardcoding | Incorporar campaña exige añadir if hardcoded |
| G01-03 | ExtendCampaign preserva membership, ámbito y obligaciones anteriores | Extender membership sin pérdidas | Ampliación elimina obligación ratificada |
| G01-04 | RefineObligation con linaje, criterio de implicación y autoridad | Refinar sin debilitar | Obligación más débil se declara refinamiento |
| G01-05 | GeneralizeContract conserva reglas en dominio antiguo y exige garantías nuevas | Generalizar sin perder dominio | Nueva capacidad pierde caso histórico |
| G01-06 | Supersede, retire y deprecate con disposition, fuente, impacto, decisión y compatibilidad | Retirar con linaje y autoridad | Se elimina una obligación sin linaje ni aprobación |
| G01-07 | Registro append-only y replay determinista por versión de intérprete | Replay por intérprete fijado | Replay produce programa distinto |
| G01-08 | ChangeSet lleva expected revision y conflicto de escrituras/dependencias | Concurrencia optimista real | Se acepta entrega basada en estado obsoleto |
| G01-09 | Estado de campaña y obligación derivado de eventos admitidos | Estado derivado de eventos | Editar status textual provoca cierre |
| G01-10 | Comando inválido no publica ningún cambio; rollback conceptual total | Atomicidad de batch | Parte de batch inválido persiste |
| G01-11 | Comparación de revisiones incluye obligaciones, consumos y normatividad | Diff de dominio y normatividad | Solo diff texto omite obligación borrada |
| G01-12 | Nueva revisión conserva certificado anterior pero no lo extiende sin evidencia | Certificado antiguo solo para corte antiguo | O13 hereda PASS automático de O1-O12 |

## Suficiencia e integración

La conjunción de hojas no acredita automáticamente la campaña. Generar RefinementCase con G objetivo, hijos D, bridges J, hipótesis A y PO para justificar A∧D∧J⇒G, comprobando además factibilidad. INT-01, INT-08 se ensaya sobre el propio ProjectGuardian con oráculo V0 y caso de mutación independiente.

Ataques de referencia: Refinar debilitando, omitir histórico, reusar certificado de campaña ampliada. Mantener UNKNOWN/HOLD cuando falte semántica o prueba, sin cambiar el contrato original.

## Criterio de cierre

Desarrollo terminado = todas las obligaciones originales y derivadas aplicables con implementación, pruebas, adversarios, verificadores e integración autoradas. Cierre material = además ejecución sobre candidato exacto, auditor independiente tras fin de bloque, recibos y autorización. La gramática/contrato específico de GSL-0 queda para discusión posterior.
