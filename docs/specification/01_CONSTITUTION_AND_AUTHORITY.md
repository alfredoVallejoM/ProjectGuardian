# 01 — Constitución, autoridad y garantías vinculantes

## Jerarquía y clases de afirmaciones
Distinguir hechos observados, decisiones ratificadas, contratos exigibles, deducciones verificadas, propuestas e información desconocida. Fuentes Git demuestran hechos sobre bytes/revisiones, no se convierten automáticamente en autoridad normativa. Una decisión aprobada no se anula por un resumen posterior. Las contradicciones se registran como `ConflictRecord`.

Autoridades **disjuntas**: Guardian gobierna la integridad general; cada proyecto conserva la constitución de sus matemáticas/arquitectura. El proyecto puede estar en modo embebido, sidecar o federado, manteniendo un owner canónico por dato. Una importación entre proyectos es un `ApprovedSourceImport`, nunca deducción por analogía.

## Invariantes constitucionales
- `CONS-01 Identity`: LogicalId ≠ RevisionId ≠ ContentDigest ≠ Alias. Un nombre o hash no constituye equivalencia matemática.
- `CONS-02 Non-erasure`: toda obligación ratificada conserva linaje, alcance y disposición; no se borra con edición o renumeración.
- `CONS-03 Non-weakening`: refinar o generalizar requiere relación de conservación demostrable o decisión de modificación autorizada.
- `CONS-04 Boundary`: cada contrato/propiedad tiene owner y frontera aprobados; código observado no redefine la arquitectura exigible.
- `CONS-05 Applicability`: falta de información no implica que una obligación no se aplique.
- `CONS-06 Non-promotion`: SOURCE_PRESENT/TEST_AUTHORED/TEST_EXECUTED/QUALIFIED_IN_SCOPE son dimensiones distintas.
- `CONS-07 Evidence`: claim + perfil + fuentes + política + recibo verificable; no autoridad proveniente de narrativa.
- `CONS-08 Lifecycle`: certificación de revisión anterior no demuestra cierre de revisión nueva.
- `CONS-09 Support`: invalidación conforme a dependencias realmente protegidas, nunca SHA global ciego.
- `CONS-10 Independence`: autor, auditor y runner conservan niveles de autoridad separados; modo monoagente no inventa independencia.
- `CONS-11 Gatekeeper`: código candidato no cambia las reglas que lo evalúan; publicación fuera del plano confiable prohibida.
- `CONS-12 Extensibility`: adicionar campañas, obligaciones y owners no requiere reescribir código central salvo introducir capacidad general legítima.

## Jerarquía de cambios
1. `OPERATIONAL_CHANGE`: reordenar y presentar trabajo sin cambiar contratos.
2. `IMPLEMENTATION_DECISION`: seleccionar algoritmo compatible.
3. `ARCHITECTURE_CHANGE`: modifica fronteras, ownership o dependencias; requiere impacto y decisión aprobada.
4. `CONTRACT_REFINEMENT`: precisa, prueba que preserva el ámbito anterior.
5. `CONTRACT_GENERALIZATION`: expande dominio con obligaciones de conservación y nuevas garantías.
6. `NORMATIVE_REPLACEMENT`: cambio de contrato con disposición, linaje y autorización externa.
7. `CONSTITUTIONAL_AMENDMENT`: cambio de regla protegida evaluado con la versión normativa anterior.

Ningún agente puede ratificar sus propuestas por escribir `APPROVED` o `RATIFIED`. Los permisos deben verificarse mediante identidad fuera del contenido no confiable. Las decisiones no resolubles automáticamente devuelven `UNKNOWN`, `CONFLICT` o `REQUIRES_APPROVAL`.

## Política de autorrevisión
La constitución del Guardian rige su propio código: una actualización del Gatekeeper pasa por el ejecutable/política preexistente, tests de no-regresión, revisión independiente y autorización cuando se modifique la semántica de admisión. Los cambios de normas, esquemas de autoridad o validadores normativos son superficie protegida.

## Límites honestos
La garantía se refiere a la **admisión** dentro de un perímetro efectivo de credenciales y pruebas confiables. No puede impedir que un agente produzca textos falsos fuera de ese perímetro ni decidir matemáticamente cualquier equivalencia.

