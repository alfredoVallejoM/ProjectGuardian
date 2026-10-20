# Contrato formal GSL-0 y auditoría de extracción textual Charloom

**Estado: PROPUESTA DE DISEÑO, NO RATIFICADA.** Esta ampliación empieza el diseño del contrato GSL-0 que el índice anterior dejó pendiente; ningún compilador ni crate Rust extraído está implementado/cualificado materialmente.

Documentos:
- [GSL-0: semántica y contratos formales de compilación](../specification/GSL0_FORMAL_COMPILER_CONTRACT_PROPOSED.md)
- [Charloom: auditoría del código real, APIs y límites](../architecture/CHARLOOM_TEXT_SOURCE_REUSE_AUDIT_2026_10_20.md)
- [CTK / GSL0: programa de extracción y bootstrap](../campaigns/GSL0_CHARLOOM_EXTRACTION_PROGRAM_PROPOSED.md)

Registros candidatos machine-readable:
- [Contrato de compilador GSL-0](../../architecture/gsl0_compiler_contract_candidate.json)
- [Perímetro de extracción Charloom](../../architecture/charloom_text_extraction_candidate.json)

Fuente Charloom fijada: 3de6e1ec205394b6ac9c232dd66b1550ffad2fd9. **No tomar src/generalization como crate estable**: su feature research-generalization está desactivada por defecto. Seleccionar CL-T y sólo estructuras genéricas CL-C02/C03 después de desacoplar ComputeStage/LayerStore; prohibida la dependencia Compute Master. No hay resultados materiales de Cargo.

CCRR/G-00 vigente como diseño propuesto, sin alteración de 163 obligaciones originales ni ratificación de ADR. El SourceMap y el IR son propios de Guardian: Charloom no decide qué es normativo, qué está completo ni qué se ratifica.

Estado del plan CTK: se puede iniciar auditoría de dependencias y diseño de crate; su publicación y uso productivo requieren Rust toolchain, material tests y recibos. Ninguna evaluación del candidato se utiliza como su único oráculo.
