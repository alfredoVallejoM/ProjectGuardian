# ProjectGuardian

Infraestructura independiente para custodiar obligaciones, arquitectura y garantías.
Guardian distingue lo exigido, lo implementado y lo acreditado por ámbito.
Producir código, pruebas o documentos no concede autoridad normativa.

## Estado actual — 29 de octubre de 2026

**Única obligación activa: G00-01 — identidades tipadas.** La aceptación avanza
secuencialmente: G00-01 → G00-02 → … → G00-12. No se abre la siguiente mientras
queden pendientes de implementación, integración, aceptación o publicación de
la activa. El código posterior se conserva, pero no cuenta como obligación cerrada.

El objetivo sigue siendo toda la primera campaña: **12 padres, 120 cláusulas,
58 APIs, 36 adversarios y siete verticales**. B00…B09 son bloques de G-00;
no son campañas nuevas. GSL no sustituye este objetivo. CTK-01 queda fuera de alcance.

### G00-01: reparaciones publicadas y fallos revisados

El candidato secuencial deja de estar únicamente en un parche local. Se publican
cinco módulos corregidos: identidad, referencias, base de registros, adaptador
de codec y consumidor de identidad del contexto GSL. Se conservan las firmas
públicas, el formato identity/v1 y los tests y originales normativos anteriores.

La misma batería de 94 casos da **44 PASS / 50 FAIL** sobre la base sin reparar
`f86e5bd1`, y **94 PASS** sobre el candidato. Los 50 fallos eran condiciones de
la versión anterior, no fallos actuales de esa batería. Incluyen parametrizaciones;
no son cincuenta defectos independientes.

La nueva ejecución seleccionada da **1.030 PASS, cero FAIL/ERROR/SKIP**, con los
94 casos nuevos ya incluidos. Se comprobaron setup/call/teardown, 84 entradas
estables y 45 módulos Guardian con bytes coincidentes. **20/20 mutaciones dirigidas
detectadas**. Entorno: Python 3.13.5, pytest 9.0.2. Es autoauditoría, no otro revisor.

**No es el checkout íntegro ni el paquete completo instalado. G00-01 todavía no
se declara cerrado; G00-02 permanece bloqueado como siguiente objetivo.** La
publicación resuelve la entrega del parche, no la regresión completa pendiente.
Python 3.12, tipado estático, revisión independiente y runner protegido no se
presentan como realizados.

[Revisión de fallos y reparaciones](verification/g00_01/REVIEW_2026_10_29.md) ·
[Matriz de diez cláusulas, ocho APIs y tres adversarios](verification/g00_01/ACCEPTANCE.json) ·
[Ejecución nueva y selección exacta](verification/g00_01/REPLAY_2026_10_29.json) ·
[Entradas fijadas](verification/g00_01/INPUTS_2026_10_29.json) ·
[Mutaciones](verification/g00_01/MUTATIONS_2026_10_29.json) ·
[Salida de tests](verification/g00_01/TESTS_2026_10_29.txt).

### Reproducción local

```sh
python -m pytest -q tests/g00_01
PYTHONHASHSEED=731 python verification/g00_01/run_selected.py \
  --root . --manifest verification/g00_01/INPUTS_2026_10_29.json \
  --output /tmp/g00-01-replay.json
python tools/run_g00_01_mutations.py --output /tmp/g00-01-mutations.json
```

El observador fija una selección explícita. No convierte tests ausentes en PASS
ni autentica su propio recibo. Los hashes de logs locales no son firmas ni una
prueba de que un ejecutor externo sea confiable.

## Estado acumulado, sin cerrar obligaciones por presencia de archivos

Los bloques productivos existentes incluyen identidades, proyectos y fuentes,
compromisos y borradores, ámbitos V4, autoridad y constitución, resolución exacta,
codecs nominales y evaluador estructural. Sus grandes componentes ya están escritos,
pero su aceptación por obligación se revisa ahora en el orden indicado.

**G00_DEVELOPMENT_COMPLETE y G00_CAMPAIGN_CLOSED no están acreditados.** El control
B08 existe, pero no reemplaza la suficiencia semántica de cada cláusula ni las
postcondiciones completas de cada API. B09 sigue requiriendo revisión y
cualificación separadas. Los estados históricos de architecture/ no se reescriben.

Cada obligación conserva: contrato original → operación productiva → positivo →
falsación → consumidor → ejecución → límites. El padre necesita además justificar
la conexión entre sus cláusulas. Un contador de tests no concede ese juicio.

## Evidencia anterior preservada

El [registro de avance anterior](verification/completion/obligation_evidence.json)
conserva el inventario 12/120/58/36/7 y el tramo de fuentes de G00-03. No es el plan
integral de aceptación ni un certificado; sus diez pares ejecutados no implican
que el resto esté sin implementar. La [matriz activa de G00-01](verification/g00_01/ACCEPTANCE.json)
lo complementa sin reescribir evidencia histórica.

[G00-03: metadatos y contratos de fuentes](docs/audit/2026_10_27_G00_03_ACCEPTANCE.md) ·
[Remediación A01–A03/D01/G01/G02](docs/audit/2026_10_26_G00_GSL_REMEDIATION.md) ·
[Revisión que reprodujo esos fallos](docs/audit/2026_10_26_G00_GSL_DEEP_REVIEW.md) ·
[Núcleo integrado publicado](docs/implementation/G00_COMPLETION_CANDIDATE.md) ·
[Reconciliación inicial B00](docs/closure/B00_LC00_RECONCILIATION_AND_EXTERNAL_CORRESPONDENCE.md).

114, 961, 887, 1598 y los demás resultados históricos pertenecen a sus candidatos
y selecciones. No se suman al 1.030 ni acreditan automáticamente código cambiado.
Un cambio documental ajeno al perímetro de código probado no invalida su evidencia,
pero tampoco amplía el ámbito de esa evidencia.

## GSL: consumidor coordinado, no nuevo frente de ampliación

Existe fuente → extracción/lexer/CST/AST → resolución del perfil actual → tipado
→ ContractIR, con mapas, obligaciones de prueba pendientes, diff y emisión canónica.
Las actualizaciones utilizan reconstrucción completa, sin caché. Los V0 autónomos
no participan en la construcción del IR. Compilar no acredita realización en
código, suficiencia del corpus ni admisión normativa.

Imports/módulos generales, reconciliación del corpus, dependencias externas y
aceptación global LC00…LC12 siguen pendientes. En esta entrega solo se reparan
consumidores de identidades de G00-01; no se amplía el lenguaje.

[Diff](docs/implementation/GSL0_C12_STRUCTURAL_DIFF.md) ·
[Emisión/reconstrucción y B08](docs/implementation/G00_B08_GSL_EMISSION_REBUILD.md).

## Fuentes autoritativas y reglas de trabajo

[Índice](docs/README.md) · [G-00](docs/campaigns/G-00/INDEX.md) ·
[Programa B00…B09](docs/campaigns/G-00/12_IMPLEMENTATION_PROGRAM_AND_EXIT_GATES.md) ·
[Cláusulas](architecture/g00_functional_refinement.json) ·
[APIs](architecture/g00_api_contracts.json) ·
[Pruebas y adversarios](architecture/g00_validation_plan.json) ·
[14 campañas y 163 obligaciones](architecture/campaigns.json).

Se conservan originales y tests históricos. No se inventan aprobaciones ni se
confunde revisión del constructor con revisión independiente. Sin ramas nuevas
no autorizadas ni GitHub Actions. Sin reloj, red o filesystem en las operaciones
puras del dominio, ni callbacks del proyecto utilizados como normas de confianza.
