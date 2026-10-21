# GSL0-LC02 — Obligación de preservación semántica V4 (fragmento finito)

**Tipo:** demostración matemática del algoritmo acotado de lowering V0 y especificación falsable del verificador. **No** es teorema Lean mecanizado, ratificación de GSL0, certificación de Guardian ni equivalencia de todo el lenguaje GSL.

## Dominio y semántica

Sea `V4={(0,0),(1,0),(0,1),(1,1)}`, respectivamente UNKNOWN, YES, NO, CONFLICT. Los bits expresan **soporte positivo y soporte negativo**, no credenciales ni verdad material certificada.

Para `a=(a+,a−)` y `b=(b+,b−)`:

- `¬a=(a−,a+)`.
- `a ∧ b=(a+∧b+,a−∨b−)`.
- `a ∨ b=(a+∨b+,a−∧b−)`.

El fragmento de expresiones fuente `F` es la gramática tipada de átomos nominales, las cuatro constantes, NOT, AND, OR y paréntesis. El AST se valida con límites deterministas y sin ejecución de Python procedente de la especificación. `L:F→FormulaIR` conserva la estructura de átomos, constantes y operadores.

## Teorema condicional: preservación por traducción

Para todo `e:F`, entorno total `ρ:Atoms(e)→V4` y límite de recursos suficiente:

`Eval_IR(L(e),ρ)=Eval_Source(e,ρ)`.

Demostración por inducción estructural:

1. **Constantes.** Los cuatro constructores se traducen a sus constantes IR homónimas. Ambos intérpretes devuelven el mismo par de bits.
2. **Átomo.** Un nombre `x` se traduce al átomo IR `x`. Ambos consultan `ρ(x)`. Si `x` falta, la evaluación falla cerrada; no se inventa UNKNOWN como testigo.
3. **NOT.** Por hipótesis de inducción, ambas interpretaciones del operando coinciden. Como ambas intercambian los bits, también coinciden las negaciones.
4. **AND.** Las interpretaciones de ambos operandos coinciden por inducción; ambas conjunciones calculan `(a+∧b+,a−∨b−)`.
5. **OR.** Idéntico razonamiento para `(a+∨b+,a−∧b−)`.

Queda demostrada la correspondencia matemática **respecto de la definición del lenguaje V0 elegido y sus dos intérpretes**, no que el código ejecutable esté probado por un asistente de demostración. La corrección del parser, runtime y representación se prueba materialmente mediante casos funcionales, adversarios y mutaciones.

## Teorema de exhaustividad finita del verificador

Sea `N = Atoms(Source) ∪ Atoms(IR)`, `n=|N|`. Si el manifiesto externo fija fuente/digest, el parser acepta el fragmento, los operadores están en el perfil y `4^n≤budget`, el verificador recorre explícitamente las `4^n` valuaciones. Un resultado FINITE_EQUIVALENT implica igualdad extensional de ambos intérpretes sobre **ese conjunto finito**. Una discrepancia produce `COUNTEREXAMPLE` con testigo; exceso de presupuesto produce `INCONCLUSIVE_RESOURCE_LIMIT`, jamás PASS.

Esta enumeración no demuestra propiedades para cuantificación abierta, observaciones del mundo, completitud del corpus histórico ni contratos con semántica diferida.

## Obligación adicional: no pérdida de declaraciones

`CoverageExpectation` debe llegar de un inventario **independiente y fijado externamente**. Antes de comparar expresiones, el verificador exige igualdad exacta de identidades de declaraciones y claves `(declaration,field,occurrence)` respecto al IR. Después exige una `FormulaGrounding` única por clave, dentro del origen de la declaración y del SourceBundle pinneado.

Sin inventario: INCONCLUSIVE_EXPECTED_COVERAGE; si hay pérdida o relación falsa: MISSING_BINDING; si la expresión es distinta: COUNTEREXAMPLE. Un digest reemitido por el candidato no sirve de oráculo.

No hay teorema de que el inventario de entrada coincida con todas las obligaciones humanas: esa conciliación corresponde a LC09/G00 y a fuentes de autoridad externas. Tampoco se promueven propiedades diferidas o POs UNPROVEN a satisfacción certificada.

## Evidencia ejecutable

Código: `src/guardian/spec_lang/v0.py`, `src/guardian/spec_lang/ir.py`, `src/guardian/domain/evidence_logic.py`.

Pruebas: `tests/spec_lang/test_v0.py`, `tests/spec_lang/test_lc01_lc02_semantic_audit.py`, `tests/oracles/v4_oracle.py`. Incluyen tablas de V4 sobre 16 pares, casos exhaustivos con 2 y 3 átomos, 96 expresiones generadas con semilla estable, mutaciones, IR regenerado, fraude de procedencia, pérdida de campos/declaraciones, límites de recursos y rechazo de ciclos.

El estado global de GSL-T05 sigue PARTIAL: LC03–LC08 deben extender y demostrar los puentes fuente GSL completa→AST tipado→IR.
