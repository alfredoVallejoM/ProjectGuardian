# Autoauditoría adversaria — G00-B02 y GSL0-LC03

**Sujeto:** candidato local 21-10-2026. **Carácter:** revisión adversaria del propio constructor, NO auditor distinto ni receipt de raíz confiable. Los contratos originales y el censo de pruebas se mantuvieron inmutables.

| ID | Superficie | Contraejemplo | Acción/estado |
|---|---|---|---|
| B02-R01 | SourceUniverse | ExclusionRef apunta a una decisión pero se interpreta como aprobada sin autenticación | **Corregido:** `EXCLUSION_AUTHORITY_UNVERIFIED` salvo contexto confiable externo explícito; nunca se firma o ratifica aquí |
| B02-R02 | SourceHistory | DELTA-A depende de DELTA-B, y B de A; ningún BASE | **Corregido:** `HISTORICAL_CYCLE` + `HISTORICAL_BASE_MISSING` |
| B02-R08 | Cross-project exclusion | La exclusión de una fuente importada exige decisión del proyecto destino, no del proyecto fuente | **Corregido:** `EXCLUSION_WRONG_PROJECT` y prueba de permiso importado con aprobación local |
| B02-R03 | Projects | Dos proyectos comparten human alias/repo path | **Comprobado:** `ProjectId` evita fusión y la lectura foreign requiere permiso |
| B02-R04 | Import grants | Un permiso del archivo X se intenta usar para Y | **Comprobado:** exige mismo SourceRef, repo y path exactos |
| B02-R05 | Coverage | Missing o dos commits relacionados se cuentan como cobertura completa | **Comprobado:** missing explícito; `eligible_for_complete_claim=false`; NO fuente de certificados |
| B02-R06 | Acquisitions | Se intenta compilar una fuente `IDENTIFIED`, no observada | **Corregido:** application rechaza con `GSL_SOURCE_NOT_OBSERVED` |
| B02-R07 | Cross-layer | Bundle recompone digest pero difiere del cut observado en universo | **Comprobado:** `GSL_SOURCE_DIGEST_MISMATCH` |
| LC03-R01 | Lexer | `}` o `)` dentro de string/comentario cierra CST | **Comprobado:** los tokens son atómicos; Yield preserva bytes |
| LC03-R02 | Markdown | Fence `gsl example`, HTML comment o cierre mixto se toma como normativo | **Corregido:** excluye ejemplos/comentarios y exige marcador de cierre homogéneo |
| LC03-R03 | AST | Paréntesis excesivamente profundos disparan recursión arbitraria | **Corregido:** límite estructural explícito y rechazo tipado |
| LC03-R04 | Frontend status | Se construye `FrontendAnalysis(COMPILED)` sin haber resuelto/tipado/elaborado | **Corregido:** constructor rechaza estado prohibido |
| LC03-R05 | CST | Se construye CST con gaps entre hijos o delimitadores incoherentes | **Corregido:** `__post_init__` exige intervalos contiguos y pareja correcta |
| LC03-R06 | Semántica | `analyze_source` produce AST sintáctico, pero un contrato histórico omite una obligación | **HOLD:** cobertura histórica independiente/LC09, no falsear `COMPILED` |

## Bloqueos externos o posteriores

1. Ningún revisor distinto disponible en este corte: `HOLD_INDEPENDENT_AUDIT`.
2. Ratificación de ADR, sintaxis y pertenencia normativa: `HOLD_EXTERNAL_RATIFICATION`.
3. B06 para resolución real de entidades y B05 para autoridad local/conflictos.
4. LC04/LC05/LC06 para imports tipados, resolución, type checking y semántica AST→IR.
5. LC09 para corpus histórico integral y LC12 para cualificación.

**Conclusión de alcance:** el bloque técnico B02/LC03 tiene implementación de sus operaciones y pruebas directas, pero no concede `G00_CAMPAIGN_CLOSED`, `GSL0_CAMPAIGN_CLOSED`, `MATERIAL_QUALIFIED`, `REFINEMENT_SUFFICIENT` o `RATIFIED`.
