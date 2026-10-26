# G-00 integrado y GSL: publicación del candidato recuperado

Fecha: 2026-10-26. Base publicada: `627ee8d83b396bc1b573b41493718e04ee7a666b`.
Estado: IMPLEMENTED_CANDIDATE; no DEVELOPMENT_COMPLETE ni CAMPAIGN_CLOSED.

Se publica el candidato que había quedado en objetos Git no enlazados a main.
El árbol de producto recuperado es `3421babcf11fc7e65f4cfccee535b2bf5dc0a347`,
el de pruebas `88cf85c18a8c730dc3ea7d64ea354ecb6051d595`, el de herramientas
`61d60b0c50c98ccb7585ac1d43fe95fa4aeced31` y el de esquemas
`20dccbeb8cb30509428a03668c93be6de9161c1b`. El árbol normativo original
`0f675d7754efaefa96974e1630cbcd7721cabb9a` se conserva sin cambios.

## Código publicado

B03: borradores incompletos de seis modelos, revisión explícita y finalización
como PROPOSED, sin aprobación implícita.
B05: decisiones, aprobaciones, quorum, constituciones, reglas, conflictos,
precedencia por supersesión aprobada y enmiendas que siguen siendo propuestas.
B06: cuerpos exactos, VerificationSpec y ClauseRevision, adapters de proyecto y
fuentes; codecs v2 nominales y conservadores. Los esquemas v1 no se reinterpretan.
B07: nueve familias de predicados estructurales, presupuestos e informes que
conservan el conjunto esperado de reglas. Ningún resultado confiere admisión.

R01-R06: población y cuerpos de afirmaciones contrastados con pins externos;
exclusiones autorizadas por acción/universo/fuente/ámbito; coherencia de cuerpos
contextuales; referencias anidadas; contexto de envelopes; diagnósticos y testigos
acumulados canónicamente.

GSL: typecheck.py, elaboration.py y application/specification_service.py conectan
fuente fijada, frontend, resolución, tipado y elaboración al ContractIR del perfil
actual. Los mapas conservan spans físicos y las PO generadas permanecen UNPROVEN.
El resultado ELABORATED no es COMPILED, cualificación ni admisión. El V0 externo
contrasta la salida real sin participar en la elaboración.

## Evidencia y límites de esta publicación

La entrega anterior comunicó 1598 casos PASS y 28 mutaciones dirigidas detectadas.
Esos números son un resultado comunicado en la ejecución anterior, no una ejecución
nueva efectuada por crear este commit. No se genera un JUnit retrospectivo ni una
firma inventada. El readback de objetos confirma qué contenido se publica.
Las nuevas ejecuciones, cuando se realicen, deben registrarse separadamente.

La matriz de 58 APIs se recupera con su hash exacto del parche preservado. Sus
etiquetas IMPLEMENTED_LOCAL_CANDIDATE describen el estado de autoría histórica;
esta publicación no convierte ninguna fila en revisión independiente. El catálogo
B00 de formatos describe el perfil v1 original, no debe leerse como inventario
actual de todos los codecs v2. Se conserva para no romper su evidencia histórica.

## Pendientes que siguen abiertos

- B08: reconciliar suficiencia de 120 cláusulas, 36 adversarios y siete verticales;
  un enlace o un contador no cierra la condición semántica original.
- GSL: imports/módulos generales, corpus histórico, diff y emisión completa,
  incrementalidad y cualificación del programa total LC00-LC12.
- Python 3.12, análisis estático, revisión por otro actor, instalación protegida
  y recibo autenticado no se afirman como ejecutados o satisfechos.

No se abren ramas, no se usan GitHub Actions y no se ratifican decisiones.
