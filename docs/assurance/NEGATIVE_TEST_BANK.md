# Banco transversal de falsaciones de ProjectGuardian

**24 casos normativos previstos; ninguno ejecutado todavía.** Las campañas especifican adversarios adicionales por obligación.

| ID | Cambio adversario | Resultado obligatorio | Responsable diseñado |
|---|---|---|---|
| N01 | Omitir una obligación de paquete | Rechaza WorkPackage incompleto | `src/guardian/work/package_compiler.py` |
| N02 | Reclasificar CURRENT→FUTURE para cerrar | Bloqueo por cambio normativo | `src/guardian/program/campaign_membership.py` |
| N03 | Implementación unaria de contrato n-ario | Rechazo de cumplimiento | `src/guardian/knowledge/reconciliation.py` |
| N04 | Duplicar dueño matemático | Conflicto explícito | `src/guardian/graph/consistency.py` |
| N05 | TEST_AUTHORED→SCIENTIFIC_PASS | No se promociona | `src/guardian/assurance/qualification.py` |
| N06 | Receipt con commit diferente | STALE/INVALIDATED | `src/guardian/assurance/receipt_validation.py` |
| N07 | Confundir soporte ALL y ANY | Rechazo de evaluación | `src/guardian/graph/support.py` |
| N08 | Unit tests sin producer-consumer | Integration pendiente | `src/guardian/assurance/integration_assurance.py` |
| N09 | Constructor modifica policy y se evalúa a sí mismo | Rechazo con policy anterior | `src/guardian/governance/protected_policy.py` |
| N10 | Plugin always PASS no registrado | Ignorar para claims certificados | `src/guardian/governance/admission.py` |
| N11 | Commit HEAD cambiado durante publicación | CAS falla; revalidación | `src/guardian/governance/publication.py` |
| N12 | Cae actualización SQLite después de Git | Proyección se reconstruye | `src/guardian/persistence/recovery.py` |
| N13 | Importar fuente de otro proyecto por similitud | SOURCE_UNAUTHORIZED | `src/guardian/knowledge/provenance.py` |
| N14 | Eliminar test para producir PASS | Detectar drift de VerificationSpec | `src/guardian/assurance/verification_specs.py` |
| N15 | Macros/features sin expandir en analizador | UNKNOWN_SCOPE no coverage completa | `src/guardian/adapters/source_code/rust/analyzer.py` |
| N16 | Autorevisión como independiente | HOLD independence | `src/guardian/assurance/adversarial_review.py` |
| N17 | Cono de evidencia no registrado | UNKNOWN_SCOPE | `src/guardian/assurance/invalidation.py` |
| N18 | Cambio documental independiente fuerza full retest | Detectar sobre-invalidación | `src/guardian/graph/impact.py` |
| N19 | Agente inventa su identidad de aprobador | Permiso denegado | `src/guardian/governance/permissions.py` |
| N20 | Resumen breve suprime obligación | Manifest conserva closure completo | `src/guardian/work/context_selection.py` |
| N21 | Alta de campaña obliga editar núcleo | Violación de extensibilidad | `src/guardian/program/commands.py` |
| N22 | Teorema Lean listado sin compilación | No se acredita prueba | `src/guardian/adapters/source_code/lean/analyzer.py` |
| N23 | Dos mocks sustituyen el oráculo histórico | No se acredita paridad | `src/guardian/assurance/migration_assurance.py` |
| N24 | Timeout interpretado como PASS material | Rechazo de run | `src/guardian/adapters/runners/process_runner.py` |

Estos ataques deben convertirse en fixtures directos, mutaciones, pruebas de integración y recibos materiales; no basta con documentarlos. La revisión de autoridad de un test/protocolo requiere enmienda explícita.
