# Distribución de responsabilidades CCRR sobre G-00…G-13

**Propuesto / no ratificado / ningún código ni prueba material existente.** Las catorce campañas y las 163 obligaciones originales conservan IDs y autoridad. SH-00…SH-12 son cortes de evidencia transversal, no nuevas campañas.

## Propiedad semántica única

| Contexto | Propietario de significado | No puede decidir por sí mismo |
|---|---|---|
| domain | IDs, scopes, obligaciones, propiedades y revisiones | Que el código satisface un contrato |
| constitution | precedencia, estados normativos y conflicto | Autenticidad de identidades remotas |
| program | cambios, transporte y ley de refinamiento | Calificación de pruebas materiales |
| graph | relaciones n-arias, cierres, soporte e impacto | Que un enlace documental constituye prueba |
| knowledge | fuentes, inventario, análisis de realidad | Modificar la especificación para acomodar código |
| work | paquetización, orientación, subtareas | Rebajar contrato del padre |
| assurance | VerificationSpec, Evidence, Claim y Qualification | Redefinir la semántica del refinamiento |
| governance | permisos, admisión, trusted policy, publicación | Considerar fiable al candidato sin validar |
| adapters | observaciones de Git/Python/Rust/C++/Lean y runners | Conceder automáticamente autoridad normativa |
| interfaces | CLI/API/MCP/UI con los mismos servicios | Implementar segundo evaluador normativo |
| spec_lang (candidato) | sintaxis, resolución, elaboración y source map | Ser segunda fuente de autoridad del proyecto |

La ubicación física final de spec_lang y la semántica concreta GSL-0 **quedan pendientes de deliberación**. No crear archivos por cumplir un atlas numérico.

## Secuencia de materialización

| Tramo | Trabajo | Evidencia exigida para cierre |
|---|---|---|
| A | B00/G00: corpus y V0 | fuente completa para ámbito congelado y oráculos ejecutables |
| B | G00 B01–B06: identidad, proyectos, fuentes, reglas | comparadores V0 y pruebas de identidad/autoridad |
| C | G00 B07–B09: evaluador y suites | pruebas G00 de autoría, auditoría, material según perfil |
| D | G01 + G02: evolución, grafo, refinamientos | cambios conservadores, contraejemplo de suficiencia |
| E | G03 + G04: orientación, paquetes | closure original recalculado por validador independiente |
| F | G07 + G05: adaptadores y código real | rutas públicas/configuraciones y límites de observación |
| G | G06 + G10: evidencia y migración | receipts authenticados, no silent regression |
| H | G09: Gatekeeper | instalación protegida, identidad y publicación controlada |
| I | G11 + G08: CLI/API/MCP/agentes | paridad y no autoridad de agentes |
| J | G12 + G13: recuperación, escala y pilotos | reconstrucción y suficiencia E2E externa |

Los prerequisitos G originales son condiciones de **cierre**; se permiten prototipos aislados anteriores, sin promoverlos a autoridad.

## Contratos de integración intercampaña

INT-01 fuente a contrato: G00,G01,G07,G10; mutación fuente omitida.
INT-02 contrato a refinamiento: G00,G02,G04; todas hojas PASS, padre FAIL.
INT-03 refinamiento a paquete: G02,G03,G04; bridge perdido durante resumen.
INT-04 especificación a código: G05,G07,G10; implementación correcta inalcanzable desde API.
INT-05 código a evidencia: G05,G06,G07; mock usado como evidencia productiva.
INT-06 evidencia a admisión: G06,G09,G12; candidato cambia su policy.
INT-07 agente y manifest: G03,G04,G08,G11; handoff omite requisito.
INT-08 cambio e invalidación: G01,G02,G06,G10,G12; evidencia afectada reusable o irrelevante invalidada.

Cada contrato tiene dueño semántico y varias implementaciones; el seguimiento E2E no reemplaza las pruebas locales.

## Método de autoría y cierre

El constructor recupera todas las obligaciones originales del bloque y sus refinamientos, desarrolla código y artefactos de test/adversario y presenta candidato exacto. **Después de completar la autoría** interviene el auditor independiente; produce findings por obligación y documento, constructor corrige; el runner comprueba materialmente y el Gatekeeper admite cuando exista autoridad protegida. DEVELOPMENT_COMPLETE y CAMPAIGN_CLOSED permanecen separados.

No abrir ramas no autorizadas, no GitHub Actions como precondición. main es la referencia de publicación; worktrees pueden aislar candidatos. La ausencia actual de protección de main es TRUST_GAP para publicación fuerte.

## Ready for implementation

Una campaña está lista para implementar su bloque cuando tiene: fuentes delimitadas, obligaciones originales preservadas, interfaces/estados/errores concretos, condición de suficiencia de descomposición, integraciones y consumidores, estrategia de prueba/adversarios, dueños de arquitectura, decisions ratificadas o HOLD explícito, y criterios de cierre separados. No se exige prueba del software antes de desarrollarlo, pero tampoco se admiten supuestos materiales ocultos.
