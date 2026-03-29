from __future__ import annotations

from collections.abc import Callable

from models.document_pipeline import DocumentParsingPipelineResult
from services.final_validation_service import final_validation_service
from services.semantic_behavior_layer import semantic_behavior_layer
from services.structured_extraction_layer import structured_extraction_layer
from services.validation_control_loop_layer import validation_control_loop_layer


StageCallback = Callable[[str, str, float], None]


def parse_documents_pipeline(
    files: list[dict],
    resolve_file_path,
    *,
    stage_callback: StageCallback | None = None,
) -> DocumentParsingPipelineResult:
    if stage_callback is not None:
        stage_callback("layer_1_structured_extraction", "Segmenting documents and running deterministic extraction pipelines", 25)
    structured = structured_extraction_layer.process(files, resolve_file_path)

    if stage_callback is not None:
        stage_callback("layer_2_semantic_behavior", "Normalizing intents, building behavior chains, and cross-validating relationships", 60)
    semantic = semantic_behavior_layer.process(structured)

    if stage_callback is not None:
        stage_callback("layer_3_validation_control_loop", "Validating graph, detecting strict loops, and extracting tuning data", 90)
    validation = validation_control_loop_layer.process(structured, semantic)

    if stage_callback is not None:
        stage_callback("layer_4_final_validation", "Rejecting invalid rows, resolving graph conflicts, and preparing final validated response objects", 97)
    final_validation = final_validation_service.process(structured, semantic, validation)

    warnings = [*structured.warnings, *semantic.warnings, *validation.warnings, *final_validation.warnings]
    return DocumentParsingPipelineResult(
        structured_extraction=structured,
        semantic_behavior=semantic,
        validation_control_loop=validation,
        final_validation=final_validation,
        warnings=warnings,
    )
