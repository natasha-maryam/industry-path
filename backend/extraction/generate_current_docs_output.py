from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.pipeline import RawDocumentChunk
from services.entity_classification_service import entity_classification_service
from services.graph_build_service import graph_build_service
from services.narrative_rule_extraction_service import narrative_rule_extraction_service
from services.relationship_inference_service import relationship_inference_service
from services.tag_normalization_service import tag_normalization_service


def build_from_docs_samples() -> dict[str, object]:
    docs_root = Path(__file__).resolve().parents[2] / "docs"
    pid_text_file = docs_root / "test-uploads" / "PUMP-301_to_TANK-401_VALVE-201.txt"
    narrative_file = ROOT / "tests" / "fixtures" / "narrative_sample.txt"

    pid_text = pid_text_file.read_text(errors="ignore") if pid_text_file.exists() else ""
    narrative_text = narrative_file.read_text(errors="ignore") if narrative_file.exists() else ""

    chunks = []
    chunks.extend(
        [
            RawDocumentChunk(
                file_id="sample-pid-1",
                file_name=pid_text_file.name,
                document_type="pid_pdf",
                page_number=1,
                text=line,
                section="pid_page_1",
            )
            for line in pid_text.splitlines()
            if line.strip()
        ]
    )
    chunks.extend(
        [
            RawDocumentChunk(
                file_id="sample-narrative-1",
                file_name=narrative_file.name,
                document_type="control_narrative",
                page_number=1,
                text=line,
                section="narrative",
            )
            for line in narrative_text.splitlines()
            if line.strip()
        ]
    )

    from models.pipeline import DetectedTag

    detected_tags = []
    for chunk in chunks:
        for item in tag_normalization_service.detect_tags(chunk.text):
            detected_tags.append(
                DetectedTag(
                    normalized_tag=item["normalized_tag"],
                    raw_tag=item["raw_tag"],
                    family=item["family"],
                    canonical_type=item["canonical_type"],
                    source_file_id=chunk.file_id,
                    source_file_name=chunk.file_name,
                    source_page=chunk.page_number,
                    source_text=chunk.text,
                    confidence=0.9 if chunk.document_type == "pid_pdf" else 0.82,
                )
            )

    entities = entity_classification_service.build_entities(detected_tags)
    entities = entity_classification_service.assign_process_units(entities, narrative_text)

    narrative_chunks = [chunk for chunk in chunks if chunk.document_type == "control_narrative"]
    rule_bundle = narrative_rule_extraction_service.extract_rules(narrative_chunks)
    relationships, low, warnings = relationship_inference_service.infer(
        entities=entities,
        rule_bundle=rule_bundle,
        pid_chunks=[chunk for chunk in chunks if chunk.document_type == "pid_pdf"],
    )

    nodes, edges = graph_build_service.build(entities, relationships)
    return {
        "nodes": nodes,
        "edges": [
            {
                **edge,
                "confidence": next(
                    (
                        rel.confidence_score
                        for rel in relationships
                        if rel.source_entity == edge["source"] and rel.target_entity == edge["target"] and rel.relationship_type == edge["edge_type"]
                    ),
                    0.7,
                ),
                "explanation": next(
                    (
                        rel.explanation
                        for rel in relationships
                        if rel.source_entity == edge["source"] and rel.target_entity == edge["target"] and rel.relationship_type == edge["edge_type"]
                    ),
                    "Rule inferred relationship",
                ),
            }
            for edge in edges
        ],
        "warnings": warnings,
        "low_confidence_suggestions": [item.model_dump() for item in low],
    }


if __name__ == "__main__":
    payload = build_from_docs_samples()
    output_path = Path(__file__).resolve().parents[2] / "docs" / "test-outputs"
    output_path.mkdir(parents=True, exist_ok=True)
    destination = output_path / "current_docs_pipeline_output.json"
    destination.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {destination}")
