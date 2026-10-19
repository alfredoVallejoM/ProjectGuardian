# Delta de decisiones respecto a las 30 ADR originales

**PROPUESTA DE REVISIÓN — SIN RATIFICACIÓN.** El programa G completo se mantiene. Esta tabla especifica qué decisiones anteriores se conservan y qué novedades necesitan un acto explícito.

| Tema | ADR existentes | Corrección o punto de discusión | Estado |
|---|---|---|---|
| Identidad y contrato | 002,003,004 | Introducir tipos de compromiso, RefinementCase y RealizationWitness con IDs estables; no colapsar entidades | PROPUESTO |
| Cambios normativos | 005,006,007,015 | Preservar obligaciones originales, transporte y enmienda distintos; no CRUD | CONSISTENTE, EXTENSIÓN PENDIENTE |
| Grafo y prueba | 008,009,010,011,012,013,014 | Distinguir enlace grueso / faceta / argumento suficiente / soporte de evidencia / claim | EXTENSIÓN PENDIENTE |
| Arquitectura tecnológica | 016,017,018,019 | Python tipado + monolito modular como candidato; spec_lang no debe duplicar domain/program/assurance | SIN CAMBIO PROPUESTO |
| Fuente y proyección | 020,021 | Decidir si la fuente GSL o el IR es primario al ratificar; mantener única autoridad actual | **DECISIÓN ABIERTA PARA GSL-0** |
| Escritura y confianza | 022,023,024 | Versiones antiguas de policy y verificadores; V0 independiente; barrier de main aún inexistente | EXTENSIÓN PENDIENTE |
| Paquetes | 025,026 | Conservar manifiesto completo; incluir puentes de suficiencia y sus PO | EXTENSIÓN PENDIENTE |
| Agentes y ergonomía | 027,028,029 | Cero/uno/varios agentes, SDK sin autoridad, no crear un archivo por obligación | CONSISTENTE |
| Autogobierno | 030 | Introducir SH-00…12 y root V0, evitar candidato auto-cualificado | EXTENSIÓN PENDIENTE |

## Decisiones diferidas al contrato específico GSL-0

Forma de autoría, gramática, AST, system typing, reglas denotacionales, versión de intérprete, output canónico, política de fuente histórica/IR, interfaces de lenguaje y métodos exactos de comprobación del compilador. Este documento NO los aprueba.

## Protocolo de ratificación

1. Contrastar fuente original de cada ADR y corpus histórico.
2. Clasificar en conserva/refina/enmienda/nueva decisión.
3. Registrar motivación, alternativas, obligaciones afectadas y riesgos.
4. Resolver contradicciones contra especificación G existente.
5. Ratificar con principal autorizado y revisión exacta; no confiar en fecha de edición.
6. Emitir ChangeSet y diff; ningún PROPOSED se transforma a RATIFIED por publicación del documento.

No alterar el texto de los 34 requisitos, 30 ADR o 163 obligaciones para reducir el número de decisiones pendientes.
