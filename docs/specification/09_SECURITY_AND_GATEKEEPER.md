# 09 — Seguridad, permisos, frontera de confianza y Gatekeeper

## Modelo de amenazas
Un constructor puede editar código, tests y documentos candidatos, inventar resultados o recibir instrucciones maliciosas de fuentes. Puede ser accidental o adversario. Guardian protege la **admisión** y los certificados, no controla cualquier texto generado fuera de su perímetro.

## Separación real
Plano de trabajo: worktrees aislados, herramientas de agentes, código, tests y propuestas no confiables.
Plano de validación: runners y atestadores aislados.
Plano de gobierno: instalación protegida del Gatekeeper, constitución previa, política aprobada, credenciales, servicio de publicación. Un agente no tiene push directo ni escritura en políticas confiables.

## Permisos por capability
READ_SOURCE, READ_CONTRACT, PROPOSE_CHANGE, EDIT_CANDIDATE, SUBMIT_DELIVERY, SUBMIT_AUDIT, REQUEST_VALIDATION, APPROVE_ARCHITECTURE, AMEND_CONSTITUTION, ISSUE_QUALIFICATION, PUBLISH_CHANGE. Se verifican sobre principal autenticado, proyecto, ámbito, revisión y expiración; campo "role" redactado no es permiso.

## Gatekeeper
1. Identidad y revisión base (expected commit).
2. Cargar política protegida preexistente.
3. Verificar paths y autoridad de cambios.
4. Recompilar conjunto de obligaciones desde fuente normativa.
5. Analizar arquitectura, imports, propiedad y consumidores.
6. Evaluar falsaciones/tests/adversarios/resultados/exact candidate.
7. Verificar aprobaciones humanas y receipts de runners confiables.
8. Construir commit candidato sin modificar ref.
9. Publicar con compare-and-swap; recuperar/reconstruir índice.

Un cambio de policy/validator se revisa con versión protegida anterior, no la versión que propone. Seguridad no depende de prompt, hook local opcional ni SDK de agentes.

## Verificadores
`VerifierDescriptor` incluye ID, versión/digest, allowed claims, scope, validation contract, isolation/resource policy, trust status. Un extractor o plugin no crea autoridad matemática por instalarse. Subprocesos sin permisos excesivos, invocaciones no interpoladas a shell, red restringida según perfil, logs y evidencia autenticada.

## Casos adversarios
Obligación borrada, test quitado, política modificada, receipt ficticio, commit sustituido, cross-project source import, falsificación de rol, viejo certificado fuera de perfil, runner sin sandbox, test circular, rama modificada concurrentemente y prompt injection dentro de archivo fuente.

## Limitaciones
Administrador con bypass de branch protection forma parte de la trusted computing base. Usar reglas de repositorio y credenciales limitadas según entorno; no prometer seguridad absoluta. Si se permite push fuera de Guardian, el estado Git debe marcarse como cambios no admitidos al reimportarlo.


## Bootstrap del autogobierno y límite de confianza (propuesto)

V0 es oráculo externo fijado, distinto del candidato. Los cortes SH-00…SH-12 son evidencias de G existentes, no campañas que se autoaprueban. Antes de aceptar una modificación del Gatekeeper, ejecutar la política **anterior** instalada y verificadores independientes; candidato no controla permiso, runner, trusted policy ni credencial de escritura. La rama main observada no estaba protegida: sin impedir escritura directa de un constructor, registrar TRUST_GAP y abstenerse de declarar publicación segura. [Plan SH](../revision-2026-10-19/03_SELFHOST_V0_AND_SH00_SH12.md). Sin implementación ni ratificación.
