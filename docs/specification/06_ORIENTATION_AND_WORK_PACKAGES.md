# 06 — Project Orientation, contexto e instrucciones de trabajo

## Orientar no es despachar
`ProjectOrientation`: qué es un proyecto, alcance, constitución, arquitectura, fuentes, estado observado, campañas, evidencias, riesgos, bloqueos y trabajo elegible.
`ComponentOrientation`: responsabilidades, interfaces, consumidores, owners, invariantes, fuentes y limitaciones de un componente.
`WorkPackage`: contrato inmutable y completo de una unidad de trabajo que puede entregarse a humanos, un agente o varios.

## Paquete normativo versus presentación
El `WorkPackageManifest` contiene snapshot de Project/Constitution/Architecture/SourceUniverse, target refs, profile y milestone, RequiredObligationClosure, contratos de producers/consumers, falsaciones, verificadores exigidos, presupuestos, paths permitidos, autoridad de cambio, prohibited shortcuts, evidencia base y cierre exacto. Tiene identidad, versión y digest.
`ExplanationView` ofrece secuencia de pasos, conceptos, archivos por consultar y riesgos, pero nunca altera o elimina requisitos. Limitar tokens o fragmentar contexto no reduce RequiredObligationClosure.

## Compilador de encargos
Entrada `(project_revision, target, support_profile, milestone)`. Algoritmo:
1. Resolver revisión/autoridad y applicability YES/NO/UNKNOWN/CONFLICT.
2. Calcular cierre normativo (reglas, capacidades, propiedades, obligaciones, fuentes, consumidores, interfaces, tests, recursos, preservación histórica).
3. Resolver dependencias ALL/ANY/condicionales; bloquear incertidumbres obligatorias.
4. Identificar owners, rutas de modificación y permisos.
5. Vincular VerificationSpecs y criterios de falsación.
6. Generar manifest inmutable y vista navegable.
7. Validar de forma independiente el manifest contra el cierre calculado.

La falta de una obligación obliga a rechazar el paquete. Un padre solo puede cerrar al verificar los subtrabajos y sus contratos de integración.

## Consulta durante el trabajo
Un agente puede solicitar `orient`, `explain`, `dependencies`, `consumers`, `source`, `impact`, `gaps` y `propose_change`. Nuevas decisiones/obligaciones deben tramitarse, no incorporarse silenciosamente. Si cambia un contrato protegido, recalcular aplicabilidad del encargo previo antes de admitir su entrega.

## Estados de entrega
`WorkDelivery` afirma la cobertura implementada; Guardian reconstruye el cierre desde fuente normativa y compara source/test/artifact refs. `DEVELOPMENT_COMPLETE` implica obligaciones originales implementadas, adversarios y verificadores escritos. No implica que Cargo/Lean/pytest se hayan ejecutado. Auditoría independiente y cualificación material son dimensiones separadas.

## Contexto pequeño, verdad grande
El agente nunca necesita tener todo el grafo en prompt. Recibe un índice completo de obligaciones y recursos recuperables. La validación posterior usa el universo normativo completo, no el texto que cabía en su contexto. Reducción de tokens es optimización explicativa, no alteración contractual.


## Contrato CCRR adicional (propuesto)

El WorkPackage debe incluir no solo RequiredObligationClosure, sino además RefinementCases, sus proof obligations de suficiencia, bridges de integración y restricciones de realización. Descomponer en subpaquetes preserva el contrato padre y las obligaciones compartidas. Una explicación paginada puede omitir detalles de visualización, nunca reducir el cierre del manifiesto. El validador independiente reconstruye el cierre desde el ProjectContract, no desde la entrega del constructor. [Integraciones](../revision-2026-10-19/02_E2E_ASSURANCE_AND_ADVERSARIAL_CONTRACTS.md). Sin implementación ni ratificación.
