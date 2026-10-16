# Matriz de trazabilidad de requisitos → campañas

**34 requisitos, 14 campañas, 163 obligaciones y 121 módulos de diseño.** Este documento se deriva de los registros JSON; no prueba implementación ni cobertura científica total.

| Requisito | Descripción | Campañas | Obligaciones ligadas en los dosieres |
|---|---|---|---:|
| `PG-REQ-01` | Independencia | G-00, G-07 | 24 |
| `PG-REQ-02` | Generalidad | G-00, G-07, G-13 | 36 |
| `PG-REQ-03` | Contrato integral | G-00, G-02, G-10 | 36 |
| `PG-REQ-04` | No debilitamiento | G-01, G-09, G-10 | 36 |
| `PG-REQ-05` | Evolucion abierta | G-01, G-13 | 24 |
| `PG-REQ-06` | Identidad historica | G-00, G-01 | 24 |
| `PG-REQ-07` | Fuentes trazables | G-07, G-10 | 24 |
| `PG-REQ-08` | Estados ortogonales | G-00, G-06 | 24 |
| `PG-REQ-09` | Aplicabilidad contextual | G-00, G-02, G-10 | 36 |
| `PG-REQ-10` | Arquitectura vinculante | G-00, G-05, G-09 | 36 |
| `PG-REQ-11` | Grafo multidimensional | G-02 | 12 |
| `PG-REQ-12` | Cobertura verificable | G-10 | 12 |
| `PG-REQ-13` | Orientacion | G-03, G-11 | 22 |
| `PG-REQ-14` | Trabajo compilado | G-04 | 12 |
| `PG-REQ-15` | Implementacion real | G-05, G-06 | 24 |
| `PG-REQ-16` | Integracion | G-05, G-06, G-13 | 36 |
| `PG-REQ-17` | Auditoria adversaria | G-06, G-13 | 24 |
| `PG-REQ-18` | Evidencia autentica | G-06, G-09 | 24 |
| `PG-REQ-19` | Continuidad certificados | G-06, G-10 | 24 |
| `PG-REQ-20` | Impacto incremental | G-02, G-06, G-10 | 36 |
| `PG-REQ-21` | Migracion conservadora | G-10 | 12 |
| `PG-REQ-22` | Investigacion abierta | G-00, G-01, G-10 | 36 |
| `PG-REQ-23` | Monoagente | G-08, G-13 | 23 |
| `PG-REQ-24` | Multiagente | G-08, G-13 | 23 |
| `PG-REQ-25` | Independencia proveedor | G-07, G-08 | 23 |
| `PG-REQ-26` | Proteccion gobierno | G-09 | 12 |
| `PG-REQ-27` | Interoperabilidad | G-11 | 12 |
| `PG-REQ-28` | Explicabilidad | G-02, G-03, G-05, G-11 | 46 |
| `PG-REQ-29` | Persistencia continuidad | G-01, G-03, G-12 | 32 |
| `PG-REQ-30` | Extensibilidad fisica | G-01, G-07, G-12 | 34 |
| `PG-REQ-31` | Aislamiento | G-00, G-07, G-13 | 36 |
| `PG-REQ-32` | Certificacion honesta | G-06, G-10 | 24 |
| `PG-REQ-33` | Publicacion segura | G-09, G-12 | 22 |
| `PG-REQ-34` | Autogobierno | G-09, G-13 | 24 |

Las cifras de obligaciones por requisito **pueden solaparse**: no se suman. Los enlaces actuales son de responsabilidad de diseño de campaña, no verificación semántica individual. Falta cerrar durante desarrollo los enlaces específicos REQ→GXX-nn→ImplementationUnit→VerificationSpec→Run/Evidence y los SourceUniverse autenticados.
