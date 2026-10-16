# 08 — Migraciones, equivalencias y conservación histórica

## Modelo
`MigrationContract(source_contract, target_contract, input_translation, output_observation, equivalence_relation, hypotheses, consumers, effects, resources, evidence)`. Una migración es algo más que mover código. Debe conservar comportamiento y garantías originales o registrar desviación normativamente autorizada.

`decode(F_new(encode(x))) ≃_Γ F_old(x)` para x en dominio histórico admitido, según relación explícita (igualdad, equivalencia observacional, isomorfismo etc.). No siempre comparabilidad de bytes; distinguir exactitud, fallos, estado, recursos, consumidores e interfaces.

## Matriz de preservación
- Domain preservation (incluye casos límite y characteristic/features).
- Behavioral results, errors, partial/unknown/resource exhaustion.
- Mathematical laws, hypotheses and witness authority.
- Architectural ownership, direct API/hot paths, allowed dependencies.
- Public consumers, adapters, ABI/serialization compatibility.
- Operational and mathematical effects/coeffects.
- Historical receipts and proof scopes.
- Novel generalized domain and new theorem/testing requirements.
- Retirement condition for old provider/adapter; no silent deletion.

## Disposiciones
PRESERVE, PROMOTE_CORE, KEEP_PROVIDER, ADAPTER_ONLY, WRAP, MOVE, GENERALIZE, REPLACE, SUPERSEDE, RETIRE, DEFER, ARCHIVE_ONLY, NOT_MIGRATABLE. No disposición puede encubrir pérdida de obligación. Cada una requiere Decision/SourceRefs/ImpactedConsumers/Tests/Scope.

## Diferenciar estado
SOURCE_PRESENT, PARTIAL_PROFILE, REFERENCE_ONLY, DESIGN_ONLY, IMPLEMENTED_CANDIDATE, QUALIFIED_IN_SCOPE, MIGRATION_CLOSED. Copiar una demo acotada no constituye migración de motor general. Tests dos mocks nuevos sin ejecutar fuente original no acreditan paridad.

## Evidencia previa
Recuperar receipts originales y dependencias protegidas. Un cambio SHA por archivos irrelevantes no obliga a reejecutar; alteraciones de contrato/código/verificador protegido invalidan claims afectados. Cono incompleto -> UNKNOWN_SCOPE/HOLD, nunca prueba inferida.

## Integración y cierre
Comparación entre source original, candidato, oráculo independiente, consumidores directos/orquestados y recursos en mismo perfil. Cierre de desarrollo distinto de cierre material. Si una generalización amplía D_old a D_new, preservar garantía anterior en D_old, añadir obligaciones sobre D_new y comprobar incompatibilidades.

