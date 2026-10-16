# 13 — Calidad, adversarios y pruebas de garantías

## Método
Tests unitarios verifican funciones; contract tests verifican interfaces, propiedades prueban invariantes generales; adversarios falsan; integración demuestra flujos reales; verificación formal/científica corresponde a dominio. Cada test se vincula a una obligación y alcance de soporte.

## Invariantes de propiedad
- Rechazo de ChangeSet => estado publicado permanece bit-a-bit igual.
- Replay de eventos válidos, bajo interpreter version fijada, da el mismo ProgramSnapshot.
- Cada entidad normativamente ratificada tiene linaje tras toda transformación admitida.
- Ningún nuevo requisito se acredita por certificado previo sin comprobar alcance/condiciones.
- Un paquete no puede omitir miembros de RequiredObligationClosure.
- Un cambio de implementación sin policy de enmienda no puede modificar Constitución/Decision/ObligationRevision.
- Un Claim QUALIFIED_IN_SCOPE implica evidencias suficientes, auténticas y CURRENT para el perfil.
- Dos proyectos no mezclan fuentes/autoridades sin ApprovedImport.
- Read DB reconstruida equivale a Git source; divergencias producen fail/rebuild.
- Completeness de fuente no se deriva de count de filas existentes si faltan fuentes.

## Banco adversario obligatorio
Eliminar obligación, cambiar a FUTURE, sustituir por versión débil, crear propiedad sin origen, omitir consumer, declarar test escrito como ejecutado, receipt con candidato distinto, runner falso, self-signed role, plugin always PASS, importación interproyecto, invalidación incompleta, evidencia innecesariamente invalidada, normalización de scope incorrecta, provider duplicates, feature ausente, code gen omitido, modificación de policy por candidato, trust boundary invertida, branch advance durante publish, crash tras Git previo a SQLite.

## Escenarios E2E
A crecer programa 12→17 obligaciones; B agente presenta implementación parcial; C tamper tests+policy; D migración fuente/destino/oráculo; E Lean teorema versus compile/axioms; F proyectos aislados; G monoagente; H A0–A4 handoffs; I ImpactCone preserva receipts irrelevantes e invalida afectados; J crash-recovery/concurrencia.
Cada escenario produce fixture, política, cambio, expected diagnostics, ejecución material y receipt; no pruebas simuladas.

## Gates
Design/Source coverage/Implementation/Adversarial/Material/Integration/Scientific/Migration son distintos. Ninguno implica automáticamente los demás. `NOT_RUN` no cuenta como PASS; ausencia de prueba no significa FAIL científico demostrado, sino bloqueo.

## Revisión adversaria
El constructor termina el bloque de obligaciones y las pruebas exigidas antes de solicitar auditor independiente. Hallazgo por documento, obligación, revisión exacta, contraejemplo, acción correctiva, estado; ciclo hasta corrección o HOLD legítimo. Auditor no modifica el código que audita y no cambia aceptación para permitir cierre.

## Presupuestos de escala
Pruebas con miles, decenas y cientos de miles de entidades en perfiles progresivos; identificar latencias de importación, query, closure, impact, replay, memoria y recursos. No declarar umbrales sin medición; al fijarlos se convierten en contratos versionados.

