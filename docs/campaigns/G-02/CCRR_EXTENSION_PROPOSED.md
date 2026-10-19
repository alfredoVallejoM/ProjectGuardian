# G-02 — Contrato de extensión CCRR

**DISEÑO PROPUESTO, no ratificado ni ejecutado.** 12 obligaciones originales intactas. Autoridad histórica: architecture/campaigns.json y docs/campaigns/G-02.md.

## Objeto y límites

Representar conocimiento y ejecutar consultas de dependencias, arquitectura, soporte y lagunas.. No inferir pruebas matemáticas de enlaces informativos ni imponer aciclicidad global.. Hito de autoaplicación: SH-04. Integración: INT-02/03/08. Prerrequisitos originales: G-00, G-01.

## Matriz de revisión exhaustiva por obligación

| ID original | Implementación original | Refuerzo/puente propuesto | Falsación original |
|---|---|---|---|
| G02-01 | GraphNode y RelationRevision por proyecto, revisión y fuente | Enlace informativo no equivale a prueba | Relación une clases incompatibles |
| G02-02 | Participant con role y occurrence en relaciones multiargumento | N-aridad sin pérdida de participantes | Se pierden participantes al proyectar |
| G02-03 | Reglas de tipo, cardinalidad, provenance y autoridad por relation type | Relation type con autoridad | Arista arbitraria adquiere autoridad |
| G02-04 | Proyección matemática y detector de owners canónicos incompatibles | Owner semántico único | Dos owners de mismo contrato pasan desapercibidos |
| G02-05 | Proyección de deps permitidas, necesarias, prohibidas y consumidores | Dependencias especificadas vs observadas | Import prohibido recibe conformidad |
| G02-06 | DAG de prerequisitos, orden topológico y SCC ante ciclos estrictos | Ciclos de ejecución vs prueba | Ciclo estricto se despacha como ejecutable |
| G02-07 | AST tipado de soporte AND/OR y applicability contextual | ALL/ANY y guard tipados | OR se trata como AND o viceversa |
| G02-08 | Cierre de soporte por claim perfil revisión y relaciones admisibles | SupportCone solo de evidencia admitida | Referencia documental se usa como prueba |
| G02-09 | Proyección inversa y invalidación incremental hasta punto fijo | ImpactCone por dependencias protegidas | Certificado de consumidor afectado sigue CURRENT |
| G02-10 | Diagnósticos estructurados de faltas de implementación, test, evidencia, fuente, scope | Gap de suficiencia visible | Obligación sin soporte desaparece de informe |
| G02-11 | SQLite graph views reproducen nodos/relaciones exactos de fuente normativa | Proyección reconstruible | Projection diverge from canonical Git |
| G02-12 | Adversarios de tipos, scope, ciclos, resource limits, grandes grafos y explanation | Contraejemplos con presupuesto | Se declara cobertura total cuando búsqueda agota presupuesto |

## Suficiencia y realización

El contrato superior G de esta campaña solo se acredita con una prueba de A∧D∧J⇒G, factibilidad y realización material de premisas pertinentes; una matriz de trazabilidad o un porcentaje de tests no lo justifica. Los contratos INT-02/03/08 llevan los puentes entre módulos/campañas. Los bindings de código identifican rutas y versiones reales; UNKNOWN no equivale a PASS.

## Falsación E2E de campaña

Todas las hojas PASS y objetivo FALSE; premisa imposible; ciclo autofundamentado. Ejecutar también la falsación original de cada fila y un caso positivo. En SH-04 someter una parte auténtica de ProjectGuardian a la capacidad obtenida y contrastar con V0 u otro oráculo independiente.

## Salida de autoría y cualificación

DEVELOPMENT_COMPLETE exige 12 obligaciones implementadas, junto con pruebas, adversarios, verificadores y puentes exigidos escritos y sin placeholders. CAMPAIGN_CLOSED exige además auditoría independiente tras finalizar bloque de constructor, ejecución material por perfil, recibo auténtico y permiso de admisión. GSL-0 sigue pendiente de definición específica.
