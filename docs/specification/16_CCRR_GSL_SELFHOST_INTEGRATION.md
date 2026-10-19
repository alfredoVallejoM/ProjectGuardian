# 16 — Integración propuesta CCRR, refinamientos, GSL futuro y autoverificación

**Estado de autoridad: PROPOSED_NOT_RATIFIED.** Este capítulo complementa 00–15, no los reemplaza. No hay código, tests ejecutados ni certificados producto de esta corrección.

## Objeto

Guardian debe conservar contratos, demostraciones de suficiencia, realización concreta y cualificación, no solo una colección de obligaciones y tests. La cadena es SOURCE → CONTRACT → REFINEMENT → WORK → REALIZATION → EVIDENCE → ADMISSION. Cada flecha tiene semántica y criterios de aceptación propios.

## Qué corrige respecto a la documentación inicial

La matriz global de arquitectura/traceability.json es responsabilidad gruesa: vincular PG-REQ a todas las obligaciones de una campaña NO implica cobertura semántica. architecture/ccrr_requirement_crosswalk_proposed.json ofrece vínculos selectivos y casos discriminantes para debatir, sin atribuirles prueba. La revisión de suficiencia debe crear facetas para cada compromiso superior, puentes de integración y ProofObligation por refinamiento.

Un refinamiento (G,D,J,A,PO) no equivale a una lista de subtareas: hace falta justificar que A∧D∧J implica G y que la realización concreta satisface A,D,J. Comprobar factibilidad evita inferencias vacías. El estado de cada PO es independiente del desarrollo de código.

La correspondencia con código requiere un RealizationWitness por estructura/operación: build/revisión, binding/ruta productiva, representación, invariante, dominio, propiedades de comportamiento, seguridad y recursos pertinentes. Un enlace de archivo no prueba funcionalidad; un test mock no prueba integración real; una función válida privada no acredita wrapper público.

El programa de evidencia separa afirmación, test authored, run material, proof y certificado por scope. Supone siempre la existencia de un procedimiento de confianza independiente para admitir verificadores y publicaciones.

## Dónde reside cada responsabilidad

G00 identidades/tipos/fuentes/autoridad; G01 evolución y transporte; G02 hipergrafo, relaciones y suficiencia semántica; G03 orientación; G04 paquetes; G05 conformidad; G06 evidencia/calificación; G07 adaptadores; G08 agente; G09 gobierno; G10 cobertura y preservación; G11 interfaces; G12 fiabilidad; G13 E2E. El programa G original, 163 obligaciones y 30 ADR siguen intactos; propuestas de extensión en docs/campaigns/CCRR_EXTENSION_INDEX.md.

## Lenguaje futuro

GSL será la posible superficie de autoría tipada del núcleo semántico, no un segundo dueño de ProjectContract. GSL-0 NO se diseña en esta revisión. Su semántica, gramática, versión, AST/IR y ratificación se discutirán después, tomando como restricciones las de docs/revision-2026-10-19/05_GSL0_DISCUSSION_BOUNDARY.md.

## Selfhost y confianza

SH-00…SH-12 constituyen hitos transversales que prueban cada función nueva sobre el propio repo. V0 externo conserva corpus/oráculos independientes. Guardar código V0 junto al repositorio es admisible solo si la versión usada por la auditoría está protegida fuera de los permisos del constructor. Selfhost en sombra no constituye certificación; publicación segura necesita Gatekeeper y trusted policy anteriores a cada candidata. main no aparecía protegida en la revisión del 19-10.

## Relación con cierres

Desarrollo completo = código, tests, adversarios, verificadores y bridges exigibles autorados e implementados, sin placeholders ni cambios de denominador. Cierre de campaña = además ejecución material, auditor independiente post-bloque, recibos y autoridad. La ausencia de proof suficiente para compromiso raíz queda explícita; ningún 100 % de tests reemplaza esa obligación.

## Referencias

- docs/revision-2026-10-19/INDEX.md
- architecture/ccrr_requirement_crosswalk_proposed.json
- architecture/ccrr_campaign_extensions_proposed.json
- docs/campaigns/CCRR_EXTENSION_INDEX.md
