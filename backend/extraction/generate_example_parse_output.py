from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.pipeline import RawDocumentChunk
from services.entity_classification_service import entity_classification_service
from services.graph_build_service import graph_build_service
from services.narrative_rule_extraction_service import narrative_rule_extraction_service
from services.relationship_inference_service import relationship_inference_service
from services.tag_normalization_service import tag_normalization_service


def run_example() -> dict[str, object]:
    fixture = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "narrative_sample.txt"
    text = fixture.read_text(errors="ignore")

    chunks = [
        RawDocumentChunk(
            file_id="fixture-narrative-1",
            file_name=fixture.name,
            document_type="control_narrative",
            page_number=1,
            text=line,
            section="fixture",
        )
        for line in text.splitlines()
        if line.strip()
    ]

    detected_tags = []
    for chunk in chunks:
        for item in tag_normalization_service.detect_tags(chunk.text):
            detected_tags.append(
                {
                    "normalized_tag": item["normalized_tag"],
                    "raw_tag": item["raw_tag"],
                    "family": item["family"],
                    "canonical_type": item["canonical_type"],
                    "source_file_id": chunk.file_id,
                    "source_file_name": chunk.file_name,
                    "source_page": chunk.page_number,
                    "source_text": chunk.text,
                    "confidence": 0.85,
                }
            )

    from models.pipeline import DetectedTag

    entities = entity_classification_service.build_entities([DetectedTag(**item) for item in detected_tags])
    entities = entity_classification_service.assign_process_units(entities, text)

    rule_bundle = narrative_rule_extraction_service.extract_rules(chunks)
    relationships, low_relationships, warnings = relationship_inference_service.infer(entities, rule_bundle, pid_chunks=[])
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
                    "Heuristic relationship.",
                ),
            }
            for edge in edges
        ],
        "warnings": warnings,
        "low_confidence_suggestions": [item.model_dump() for item in low_relationships],
    }


if __name__ == "__main__":
    payload = run_example()
    output_path = Path(__file__).resolve().parents[2] / "docs" / "test-outputs"
    output_path.mkdir(parents=True, exist_ok=True)
    destination = output_path / "example_parse_output.json"
    destination.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {destination}")
