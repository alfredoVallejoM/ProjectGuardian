# 05 — Inteligencia de repositorios y reconciliación especificación/código

## Dos realidades distintas
`ArchitectureSpecified` procede de la constitución/contratos vigentes. `ArchitectureObserved` se deriva de fuente real, imports, interfaces, macros, features, generated code, tests, recursos y consumidores. Nunca adaptar la norma automáticamente a las limitaciones del código actual.

## Poblaciones de inventario
- SourceCut/SourceFile con Git object ID, versión, formato y procedencia;
- símbolos (funciones, métodos, tipos, impls, clases, traits, macros, generados, FFI);
- módulos, exports, feature configurations, build graph;
- API/ABI/wire schemas, serialización, versiones, consumers;
- tests escritos, fixtures, oráculos, VerificationSpecs, runners, receipts y recurso;
- capacidades/propiedades/contratos que no necesariamente coinciden con un archivo o función.

## Interfaces
`SourceAnalyzer.inspect(source_revision, analysis_profile) -> ObservedInventory`. Incluye `UnsupportedConstructs`, `FeatureCoverage`, `Comprehensiveness` y fuentes exactas. Una parte no comprendida bloquea `COMPLETE_SOURCE_COVERAGE`. `Crosswalk` muchos-a-muchos entre Capability, ImplementationUnit, API, Consumer y Evidence. PATH/SYMBOL no equivalen a CapabilityId.

## Adaptadores esperados
Git trees/commits; Rust (Cargo metadata, features, source/AST, generated), C++ (compile_commands, Clang AST/macros/ABI), Python (AST/imports/dinamismo), Lean (declaraciones, imports, compilation, axioms), esquemas/datos, proyectos multi-repo. La cobertura de features y código generado es normativa del perfil de origen; si falta, mantener HOLD.

## Diferencias detectables
MISSING_IMPLEMENTATION, PARTIAL_IMPLEMENTATION, ORPHAN_IMPLEMENTATION, DUPLICATE_AUTHORITY, UNDECLARED_DEPENDENCY, ARCHITECTURE_VIOLATION, PUBLIC_API_DRIFT, CONSUMER_GAP, FEATURE_GAP, TEST_GAP, SOURCE_COVERAGE_GAP, UNQUALIFIED_GENERALIZATION.

No todas son fallas definitivamente demostradas: registrar `ObservedFact`, `CandidateRelation`, `Finding`, `HOLD` y `AuthorizedDisposition` con provenance. Un código que existe no acredita automáticamente la propiedad descrita.

## Integración real
`IntegrationContract = producer + consumer + interface + input/output scope + failure semantics + resources + verification`. Cerrar un módulo mediante test unitario no satisface contrato que exige vertical E2E. Deberá ser rastreable y evaluado por scope/revision.

## Política anti-corrupción
Importar programas históricos sin cambiar IDs ni exagerar estados. Ningún proyecto adquiere obligaciones de otro por coincidencia semántica; `ApprovedSourceImport` obligatorio.


## Ampliación CCRR propuesta: testigos de realización

RealizationLink es un vínculo candidato, NO prueba de conformidad. RealizationWitness debe identificar contrato abstracto, código real, ruta pública, build/profile, representación de estados, invariantes, cobertura de dominio y evidencias. Función privada PASS no acredita wrapper público; AST parcial no implica cobertura total. Para algoritmo exigido, comprobar refinamiento de pasos, no solo igualdad de salida. La realización de una estructura compuesta exige sus bridges e integración real. [Contratos E2E](../revision-2026-10-19/02_E2E_ASSURANCE_AND_ADVERSARIAL_CONTRACTS.md). Estado: PROPUESTO, sin implementación.
