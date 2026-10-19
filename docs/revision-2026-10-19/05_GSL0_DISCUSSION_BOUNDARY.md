# GSL-0 — Frontera de diseño PENDIENTE (no es la especificación del lenguaje)

**DESIGN_NOT_RATIFIED.** Este documento no contiene gramática, compilador aprobado ni teoremas GSL-0 concluidos. Se preserva la discusión para DESPUÉS de corregir la planificación G-00…G-13.

## Necesidades que tendrá que satisfacer el diseño posterior

1. Identidades, revisiones, fuentes y autoridades sin ambigüedad.
2. Tipos separados de objetivo, capacidad, propiedad, obligación, realización, evidencia y claim.
3. Contratos con ámbito y aplicabilidad YES/NO/UNKNOWN/CONFLICT.
4. Documentación actual importable de forma progresiva, sin inventar autoridad ni cambiar corpus original.
5. Un solo contrato admitido por revisión: evitar dos fuentes normativas GSL/JSON.
6. AST/IR con source maps y diagnóstico de huecos; compilación determinista y semántica de constructores declarada.
7. Separar PARSE_OK, TYPE_OK, SEMANTICALLY_VALID, REFINEMENT_PROVEN y MATERIAL_QUALIFIED.
8. No ocultar obligación de suficiencia de un refinamiento.
9. V0 externo y pruebas adversarias de pérdida de cláusulas y de cambio de cuantificadores, ámbito y modalidad.
10. No aceptar constructores normativos desconocidos; soporte de esquemas versionados.
11. Prohibición de self-approval mediante parser, formato o interfaz de editor.
12. Independencia del núcleo respecto al SDK de agentes; compilación y verificación accesibles por CLI/API/MCP.

## Decisiones abiertas para la próxima conversación

- GSL0-D01: modalidad de autoría principal y relación Markdown/GSL.
- GSL0-D02: si el IR canónico es autoridad primaria o artefacto compilado ligado a fuentes ratificadas.
- GSL0-D03: fragmento semántico mínimo y sistema de tipos.
- GSL0-D04: gramática, AST, desambiguación, parser y diagnóstico.
- GSL0-D05: semántica denotacional de predicados y condiciones de ámbito.
- GSL0-D06: versión de compilador y políticas de compatibilidad.
- GSL0-D07: oráculos, models finitos y demostración de preservación semántica.
- GSL0-D08: traducción/importación histórica y gestión de UNKNOWN.
- GSL0-D09: dependencias entre fuentes GSL y ProjectContract ratificado.
- GSL0-D10: responsabilidad física de spec_lang en el atlas existente.
- GSL0-D11: redacción ergonómica y salida de documentación legible.
- GSL0-D12: contrato específico de compilación y gates de GSL-0.

Ninguna de estas decisiones ha sido tomada por el mero hecho de enumerarla. No modificar contratos históricos, ADR ni programa original sin ratificación explícita.
