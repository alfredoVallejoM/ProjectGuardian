# PG-ADR-015 — Migracion contratada

**Estado:** PROPOSED_FOR_RATIFICATION · **Fuentes:** PROJECT-DISCUSSION-2026-10-16.

## Decisión propuesta
Preservacion dominio comportamiento leyes consumidores recursos.

## Alternativa descartada como diseño de referencia
Copiar codigo y test smoke.

## Fundamento y consecuencias
Paridad fuente/destino/oraculo. Los contratos concretos, tests y límites están desarrollados en `docs/specification/`; esta ADR no concede autoridad ni afirma código existente.

## Cambios y compatibilidad
Cualquier cambio posterior deberá tramitar `ChangeSet` sobre el snapshot constitucional previo, preservar revisión y linaje de obligaciones, calcular ImpactCone y obtener autorización de la autoridad normativa. No editar silenciosamente esta decisión como si siempre hubiese significado otra cosa.

## Condiciones para ratificarla
1. Verificar consistencia con las otras 29 ADR y los 34 requisitos.
2. Verificar que dispone de owner, interfaces y tests aplicables en las campañas G-10.
3. Registrar aprobador y revisión explícitos; hasta entonces mantiene estado PROPUESTO.

## Pruebas adversarias que deberá soportar
Una implementación que use la alternativa descartada y debilite el contrato no podrá recibir PASS sin procedimiento normativo de excepción o modificación autorizado. Los verificadores específicos se derivarán de las obligaciones vinculadas a esta ADR.

