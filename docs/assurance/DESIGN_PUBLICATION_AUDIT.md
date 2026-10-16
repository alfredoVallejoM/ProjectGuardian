# Comprobación de publicación de la especificación — ProjectGuardian

**Resultado observado:** `PASS_DESIGN_STATIC_REFERENTIAL_ONLY`.

**Candidato leído del GitHub:** `main` @ `20d1b3083f9da68b36cd89c99e342b72cde247be`.

Esta revisión es **solo de estructura, referencias y contenido documental**: no es una ejecución material de tests de la plataforma, no acredita implementación y no ratifica las ADR.

## Comprobaciones directas realizadas
- Lectura del HEAD remoto de GitHub y del árbol recursivo, `truncated=false`.
- 86 archivos presentes: 77 Markdown y 9 JSON; 0 archivos productivos en `src/` ni `clients/web/src/`.
- 16 capítulos de especificación, sin huecos de índice.
- 30 dosieres de ADR presentes, 30 propuestas registradas.
- 14 dosieres G-00…G-13 presentes, 163 obligaciones con ID único.
- Las obligaciones tienen aceptación, falsación, perfil de verificación y estado `SPECIFIED_NOT_IMPLEMENTED`.
- Correspondencia documental entre las 163 obligaciones de los 14 dosieres y el manifiesto de campañas, contrastada mediante lecturas GitHub.
- 34 requisitos enlazados al programa de campañas, 11 alias históricos ENG→G.
- 142 módulos/rutas en atlas de diseño, 16 del cliente gráfico TypeScript propuesto.
- 163 obligaciones tienen asignación prospectiva a módulos del atlas y a tests contractuales previstos; 0 test creado/ejecutado.
- Unicidad de IDs en requisitos, ADR, campañas, obligaciones y módulos; dependencias de campañas sin ciclos detectados.
- Las rutas de módulos propuestas por campañas y por obligaciones se encuentran en el atlas (o refieren directorios de tests/fixtures de diseño).
- 89 enlaces relativos de cinco índices principales comprobados contra el árbol Git, 0 rotos.

## Estado que NO queda demostrado
- No existe todavía un intérprete Guardian ni un Gatekeeper ejecutable.
- No se han ratificado decisiones ni hay credenciales de gobierno configuradas.
- No hay pruebas ejecutadas, migraciones cualificadas, recibos de runner ni certificaciones.
- Los enlaces de requisitos→campañas→obligaciones acreditan **cobertura organizativa propuesta**, no correspondencia semántica formal de cada requisito.
- La asignación de obligaciones a archivos son targets de diseño, no tareas materialmente implementadas.
- La conversación histórica se ha normalizado en documentos y registros, no archivado de forma literal/reconciliada como SourceUniverse certificado.
- Las 14 preguntas de decisión arquitectónica y 9 sesiones de revisión deben debatirse/ratificarse.

## Corrección adversaria ya aplicada
Durante la publicación se detectó que G-12 proponía módulos `persistence/git_repository.py`/`sqlite_projection.py` no respaldados por el atlas. Se separó semántica pura de eventos/replay (`persistence/`) de E/S externa (`adapters/git/`, `adapters/sqlite/`) y se actualizó la campaña.

Posteriormente se detectó la omisión del cliente gráfico. Se añadieron 16 responsabilidades en `clients/web/src/` como propuesta TypeScript y se reconciliaron G-11, el atlas y la trazabilidad. No se generaron esqueletos físicos.

## Uso correcto
Este informe es una inspección documental comprobada en el turno de publicación. No es un receipt criptográficamente autenticado por un runner del producto, porque Guardian todavía no existe. Su condición de revisión debe mantenerse separada de `DEVELOPMENT_COMPLETE`, `MATERIAL_PASS` o `CERTIFIED`.

En el siguiente debate, el documento `docs/architecture/07_ARCHITECTURE_REVIEW_SEQUENCE.md` determina el orden para especificar contratos por archivo sin abandonar ningún compromiso anterior.
