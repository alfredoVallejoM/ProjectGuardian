# G-00 / Project, aislamiento, SourceRef y SourceUniverse

**Obligaciones:** G00-02, G00-03, G00-08. **Owners:** \`domain/project.py\`, \`domain/source.py\`. **No implementado.**

## Un proyecto es un universo de autoridad independiente

\`ProjectDefinition\` = \`ProjectId\`, display name, descripción/purpose refs, \`source_policy_ref\`, \`constitution_ref\`, repos autorizados y modalidad de almacenamiento. Su nombre y localización no definen la identidad de sus contratos. El owner de decisiones se determina por reglas del proyecto, no porque Guardian conozca un nombre de repositorio.

Un \`ProjectRegistryView\` inmutable resuelve una sola namespace a la vez. Toda operación lleva \`ProjectId\` explícito; se prohíbe un \`current_project\` global mutable. Varias sesiones paralelas sobre proyectos distintos no comparten registro de obligaciones.

## Modos declarativos de instalación

| Modo | Autoridad normativa prevista | Condición |
|---|---|---|
| EMBEDDED | Registros Guardian admitidos dentro del repo gestionado | Los cambios ocurren mediante la autoridad de ese proyecto |
| SIDECAR | Repositorio separado de gobierno que referencia código externo | Mantener exactos los commits fuente y permisos |
| FEDERATED | Conjunto de repositorios/cortes con autoridad designada por clase de dato | No inferir "mismo HEAD" para repositorios diferentes |

G-00 define y valida **el descriptor del modo**. Crear worktrees, sincronizar ramas, exportar documentos y hacer commits corresponde a G-07/G-09/G-12. Ningún modo constituye por sí mismo aprobación del contenido observado.

## SourceCut y SourceRef

\`SourceRef\` distingue:
- Git source: proveedor, repositorio identificado, commit completo, Git object kind/blob/tree, path normalizado, símbolo opcional, digest del objeto cuando haya sido observado.
- Documento versionado: URI admitida/revisión/corte, hash de contenido si se tiene, sección o rango y captura explícita.
- Decisión humana: DecisionRef, autoridad que la ha ratificado, evidencia de autenticación **a verificar externamente**; propuesta no equivale a ratificación.
- Fuente externa: locator + política de importación y estado de confianza, sin atribuirle autoridad automáticamente.

Separar \`source_identified\`, \`identity_verified\`, \`content_observed\`, \`semantically_reconciled\`, \`coverage_qualified\`. Pinned Git tree no implica censo exhaustivo de símbolos; un documento de intención no implica código.

## SourceUniverseRevision

Campos fundamentales: \`universe_id\`, \`revision_id\`, \`project_id\`, lista de SourceCut refs, reglas de inclusión y exclusión, justificación y aprobación para exclusiones, perfiles de corpus/feature, ventanas/revisiones cubiertas, cobertura objetivo, límites y \`known_missing\`.

\`validate_source_universe\` comprobará:
1. Identidad completa de cada corte, pertenencia al proyecto o import autorizado.
2. Referencias a corte fijo, no a branch mutable sin resolver.
3. Rutas normalizadas, sin traversal ni alias de path usados como prueba de contenido.
4. Inclusiones/exclusiones explícitas, sin contradicción sin resolver.
5. Delimitación real de universo (no listado vacío interpretado como totalidad).
6. Cortes de una misma historia marcados como SUPERSEDED/DELTA/BASE según fuente, sin sumarlos como corpus disjunto por defecto.
7. Fuentes no obtenibles representadas \`SOURCE_MISSING\` con razón, nunca inventadas.
8. \`coverage_claim\` solo como estructura de afirmación futura, no un certificado emitido por G-00.

## Cross-project import

\`SourcePolicy\` indica fuentes permitidas. Toda referencia a repo externo que pretende adquirir autoridad en el proyecto requiere \`ApprovedSourceImport\` con proyecto fuente/destino, corte, ámbito permitido y decisión externa validable. G-00 comprueba que exista descriptor **estructural**; G-09 autenticará el actor/approval y G-07 leerá material real.

Ejemplo: el Guardian puede gestionar Formal Core y Charloom, pero un contrato de Charloom no se incorpora a Formal Core por similitud del término "efecto". Un resumen de un agente no convierte esa relación en fuente aceptada.

## Contratos de operación y resultados

\`define_project(definition)\` → \`ValidProject | DomainErrors\`.
\`check_source_membership(project,ref,imports)\` → \`ALLOWED | DENIED | UNKNOWN | REQUIRES_APPROVAL\`.
\`validate_universe(universe,project,source_catalog)\` → \`SourceUniverseValidation\` con errores, causas y fuentes no verificadas.
\`source_coverage_descriptor(universe)\` → alcance conocido y requisitos pendientes, **nunca** \`SOURCE_COVERAGE_PASS\` sin G-07/G-10.

## Pruebas exigidas

- Dos proyectos con iguales aliases/document names mantienen namespaces diferentes.
- Proyecto FEDERATED con dos repos Git no colapsa commits independientes.
- Fuente externa sin import aprobado se rechaza.
- Inclusión y exclusión incompatibles producen CONFLICT.
- Dos cortes histórico superpuestos no se suman como "total" sin delta.
- Un branch name en lugar de SHA no es identity inmutable de SourceCut.
- \`known_missing\` continúa visible aunque todos los SourceRef cargados se validen.
- Cambiar \`display_name\` no altera \`ProjectId\`.
- El mismo SourceRef en otro proyecto es hecho observado, no autoridad compartida.

**Límite:** G-00 no ejecuta análisis Git, no certifica cobertura de origen, no firma aprobaciones y no instala Guardian. Debe bloquear lógicamente las inferencias de autoridad que no puede probar, sin fingir capacidades todavía no implementadas.
