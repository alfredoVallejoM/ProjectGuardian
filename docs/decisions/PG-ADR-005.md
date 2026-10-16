# PG-ADR-005 — Obligaciones inmutables

**Estado:** PROPOSED_FOR_RATIFICATION · **Fuentes:** PROJECT-DISCUSSION-2026-10-16.

## Decisión propuesta
No setter de completed ni edicion de ObligacionRevision aprobada.

## Alternativa descartada como diseño de referencia
CRUD directo editable.

## Fundamento y consecuencias
Todos los cambios requieren revisions y eventos. Los contratos concretos, tests y límites están desarrollados en `docs/specification/`; esta ADR no concede autoridad ni afirma código existente.

## Cambios y compatibilidad
Cualquier cambio posterior deberá tramitar `ChangeSet` sobre el snapshot constitucional previo, preservar revisión y linaje de obligaciones, calcular ImpactCone y obtener autorización de la autoridad normativa. No editar silenciosamente esta decisión como si siempre hubiese significado otra cosa.

## Condiciones para ratificarla
1. Verificar consistencia con las otras 29 ADR y los 34 requisitos.
2. Verificar que dispone de owner, interfaces y tests aplicables en las campañas G-01.
3. Registrar aprobador y revisión explícitos; hasta entonces mantiene estado PROPUESTO.

## Pruebas adversarias que deberá soportar
Una implementación que use la alternativa descartada y debilite el contrato no podrá recibir PASS sin procedimiento normativo de excepción o modificación autorizado. Los verificadores específicos se derivarán de las obligaciones vinculadas a esta ADR.

