# CCRR — Núcleo matemático y contrato de justificación (propuesta transversal)

**Estado:** formalismo candidato, no formalizado mecanizadamente ni adoptado como constitución. Extiende, no sustituye, ProjectContract, soporte, cambios y evidencias.

## 1. Dos objetos y tres correspondencias

Para un proyecto P:
- N(P): compromisos declarados y aprobados, con identidad, ámbito, autoridad y temporalidad.
- A(P): arquitectura/modelos especificados.
- C(P): código, artefactos, build profiles y trazas observadas.
- E(P): evidencias y afirmaciones sobre propiedades concretas.
- H(P): cambios, revisiones y decisiones.

Nunca identificar N(P) con A(P) ni A(P) con C(P). La implementación observada no reescribe la constitución.

Las correspondencias de garantía son **traducción** (fuente admitida → contrato), **refinamiento suficiente** (componentes e integraciones → compromiso superior) y **realización** (código efectivo → estructura especificada). Cada una genera y consume pruebas de otro tipo.

## 2. Familias semánticas de obligación

Commitment[K,Scope] con K en:
- Existence: existencia, totalidad de operaciones y superficies de servicio.
- Behavior: pre/post, trazas, invariantes y errores.
- Constitution: owners, rutas, dependencias, permisos y modularidad.
- Execution: procedimiento algorítmico y presupuestos de recursos con modelo de coste.
- Development: eventos, hitos, auditoría, independencia, conservación temporal.
- Integration/Migration: compromisos relacionales sobre múltiples componentes o revisiones (relaciones n-arias, no colapsar a un único test).

Los tipos de K gobiernan las proyecciones observacionales y qué métodos de evidencia son admisibles. Un AST correcto no demuestra ninguna propiedad de comportamiento.

## 3. RefinementCase como unidad de garantía

Un refinamiento r = (G, D, J, A, S, PO, Provenance), donde:
- G: compromiso padre; D: fórmula positiva sobre hijos (AND/OR no intercambiables).
- J: invariantes de interacción, consumidores y ensamblaje.
- A: hipótesis explícitas de entorno.
- S: ámbito, milestone y revision; PO: obligación de prueba de suficiencia.
- Provenance: fuente de la elección y autoridad de modificación.

Condición de suficiencia:
    para toda realización w del ámbito, [A(w) y D(w) y J(w)] implica G(w).
Condición de factibilidad:
    existe w con A(w) y D(w) y J(w).
Condición de realización actual:
    el candidato concreto wc satisface A(wc), D(wc) y J(wc) bajo el perfil reclamado.

No se sustituye la implicación por el recuento de hijos PASS. Un solver UNSAT para A∧D∧J∧¬G solo es evidencia de la implicación cuando el solver/encoding son adecuados al dominio y el resultado está autentificado. UNKNOWN y timeout no son PASS. La factibilidad evita éxito por antecedente imposible.

**Teorema relativo:** si la implicación está justificada y una realización cumple el antecedente, cumple G. Inducción en un DAG de argumentos fundamentados permite componer; los ciclos sin evidencia terminal no bastan.

**Prueba adversaria esencial:** construir dos sistemas con idénticos estados de todos los hijos y distinta satisfacción de G. Entonces las etiquetas de los hijos son insuficientes para decidir G. Se necesita un puente/observación que discrimine.

## 4. RealizationWitness

witness = (abstract, concrete, binding, representation, invariant, routes, domain, progress, evidence, build_identity).

La relación R(c,a) liga estados concretos a abstractos; para cada operación pública cubierta, una transición concreta desde estados válidos debe tener transición abstracta correspondiente, estados finales relacionados y outputs observacionalmente compatibles. Separar dominio soportado, seguridad, terminación, efectos, coste y ruteo público. Probar función privada no acredita wrapper público. Métodos/construcciones no inspeccionados dejan UNKNOWN_SCOPE.

La correspondencia de método requerido no se reduce a igualdad de resultado: un requisito de heap, índice invertido o algoritmo concreto precisa testigo de proceso y estructura. La correspondencia de recursos necesita workload, hardware, unidades y estadística/cotas fijadas; un benchmark favorable no certifica una cota universal.

La realización completa de una capacidad es un testigo de la composición real de sus operaciones e integraciones, no un conjunto de nombres de símbolos.

## 5. Evolución y transporte

Una transformación Δ:P→Q lleva una traducción de compromisos τΔ:O(P)→Form+(O(Q)) y puente de observación πΔ:B(Q)→B(P) cuando existe y está justificado. Para compromisos protegidos:
    [[τΔ(o)]]Q ⊆ πΔ^{-1}([[o]]P)
y además las realizaciones conformes de Q satisfacen τΔ(o). Entonces πΔ(A(Q))⊆A(P).

Transformaciones conservadoras componen observacionalmente; para garantizar también retención sintáctica de las fórmulas transportadas se exige preservación de consecuencias protegidas por la traducción posterior. No suponer que toda enmienda es conservadora; la retirada autorizada conserva historia pero cambia el contrato.

Diferencial ∂Δ registra obligaciones nacidas, transportes, realización, soporte afectado y autoridad. No es una resta de ficheros. La comparación incremental debe igualar una reconstrucción completa dentro de un modelo definido.

## 6. EvidenceJudgment y cierre

Juicio Evidence ⊢[Claim,Revision,Scope,Policy] Qualification. El tipo de evidencia debe coincidir con el tipo de afirmación:
- prueba formal admitida ≠ prueba empírica;
- test escrito ≠ run material;
- resultado de herramienta ≠ validez de todo el programa;
- structural trace link ≠ refinamiento suficiente.

El juicio de cualificación utiliza una derivación fundamentada, verificadores admitidos y condiciones de autoridad. No se admite ciclo autojustificante sin hojas verificadas. Scope, sujeto exacto y versiones de política forman parte de su semántica.

El cierre de desarrollo exige implementación de obligaciones originales y derivadas, verificadores y adversarios **autorados**; la cualificación material exige recibos reales y revisión según política. Estados separados en toda API.

## 7. Reglas de composición de confianza

Solo promover un verificador cuando una versión o raíz anterior protegida/independiente justifica su admisión. Comparar resultados en modelos finitos y contra oráculos externos no basta para demostrar corrección universal, pero identifica fallos. La cadena de confianza debe hacer explícita la base inicial y las hipótesis de cada comprobador.

## 8. Programa de pruebas formales

CCRR-P01 identidad y tipado de compromisos; P02 generación fundamentada y cierre mínimo en universo positivo finito; P03 conjunción/disyunción y alternativas; P04 suficiencia de refinamientos y contraejemplo global; P05 factibilidad; P06 simulación y cobertura de rutas; P07 composición de testigos; P08 conservación bajo transporte; P09 no circularidad probatoria; P10 alcance/independencia de evidencia; P11 preservación de compilación GSL→IR (contrato todavía pendiente); P12 rechazo de enmiendas bajo política del candidato; P13 igualdad entre cálculo incremental y recomputación completa.

Cada P lleva modelos finitos positivos/negativos, contraejemplos a generalizaciones inválidas y un enunciado explícito de qué parte queda solo propuesta. NO afirmar sorryAx=0, demostraciones Lean compiladas o gates PASS antes de ejecutarlos.

## 9. Consecuencias para el código

Dueños semánticos sin duplicaciones: domain conoce tipos; program/refinement conoce el significado de refinamiento; graph conoce relaciones y cierres; assurance conoce evidencia y cualificación; governance decide admisión; spec_lang (propuesto) interpreta sintaxis sin autoridad propia; work crea paquetes sin editar obligaciones; adapters observan sistemas heterogéneos. MCP/CLI/UI son clientes, no motores de verdad.
