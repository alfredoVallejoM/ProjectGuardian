# Perfil de correspondencia del verificador V0 — revisión 2

Semántica de lenguaje: `gsl0/v4-0.1`, preservada. La revisión 2 cambia el contrato del informe, no ratifica una extensión del lenguaje.

`true` y `false` se interpretan respectivamente como YES y NO. `yes`, `no`, `unknown`, `conflict` conservan sus valores V4. Los comentarios `//` terminan en CR o LF y `/*…*/` no se anidan. Los identificadores son ASCII; las cadenas y la fuente conservan UTF-8. El lexer productivo y el lexer del verificador son implementaciones distintas contrastadas por fixtures. Ninguno ejecuta código del proyecto.

Las expresiones de verificación son constantes, átomos, NOT, AND, OR y paréntesis. Construcciones fuera del fragmento no se convierten silenciosamente en átomos. Los resultados de cada dimensión son CHECKED, NOT_CHECKED o MISMATCH; el resultado de enumeración puede ser finito equivalente, contraejemplo, inválido o inconcluso.

1. El origen de una declaración se recalcula a partir de la cabecera literal y su cierre, independientemente del mapa que aporta el candidato.
2. La población fuente se compara con la del IR y con CoverageExpectation externa; borrar IDs del candidato y de su inventario derivado no puede ocultar declaraciones presentes en los bytes originales.
3. Cada campo V4 se liga a su ocurrencia completa y a su declaración; la equivalencia se evalúa contra todas las valoraciones dentro del presupuesto permitido.
4. Los otros campos se contrastan por tipos y formas admitidas: strings, enums de clase, referencias nominales locales y source_item. La correspondencia de una referencia no demuestra que su entidad exista ni que su autoridad haya sido admitida.
5. Un campo SOURCE_ITEM sigue ligado a la fuente fijada; un source_cut `context` no es una branch mutable.
6. Los fragmentos sin cabeceras completas pueden recibir equivalencia V4, pero no una aceptación de correspondencia del contrato.
7. Los resultados finitos no descargan propiedades diferidas, pruebas de suficiencia ni condiciones externas de autoridad.

`acceptable` es una propiedad de compatibilidad restringida a las dimensiones efectivamente comprobadas y debe leerse con el informe. `full_contract_equivalent` no puede ser verdadero mientras referencia/historia permanezcan NOT_CHECKED. Ningún valor del informe concede admisión normativa.

Las etapas C00–C14 del ABI publicado se conservan sin renumeración; el documento inicial C00–C13 se mantiene histórico y no redefine retrospectivamente las evidencias de estos cortes.
