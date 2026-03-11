from __future__ import annotations

import json
import logging

from models.logic import CompletedLogicModel, IOMappingChannel, IOMappingResult
from models.graph import PlantGraph
from services.project_service import project_service
from services.st_codegen_utils import st_codegen_utils


class IOMappingEngine:
    """Derive deterministic PLC IO channels from graph and completed logic model."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _classify(node_type: str) -> str | None:
        mapping = {
            "flow_transmitter": "AI",
            "level_transmitter": "AI",
            "pressure_transmitter": "AI",
            "differential_pressure_transmitter": "AI",
            "analyzer": "AI",
            "level_switch": "DI",
            "pump": "DO",
            "blower": "DO",
            "control_valve": "AO",
            "valve": "DO",
            "chemical_system_device": "DO",
        }
        return mapping.get(node_type)

    def build(self, project_id: str, graph: PlantGraph, model: CompletedLogicModel) -> IOMappingResult:
        channels: list[IOMappingChannel] = []
        slot = 1
        channel = 0

        for node in sorted(graph.nodes, key=lambda item: item.id):
            io_type = self._classify(node.node_type)
            if not io_type:
                continue
            channels.append(
                IOMappingChannel(
                    signal_tag=node.id,
                    normalized_signal_tag=st_codegen_utils.normalize_symbol(node.id),
                    io_type=io_type,
                    plc_slot=slot,
                    plc_channel=channel,
                    source="graph+logic",
                )
            )
            channel += 1
            if channel >= 16:
                slot += 1
                channel = 0

        # Persist deterministic snapshot even when DB mapping tables are unavailable.
        paths = project_service.workspace_paths(project_id)
        mapping_file = paths.io_mapping / "io_mapping.json"
        mapping_file.write_text(
            json.dumps(
                {
                    "project_id": project_id,
                    "channels": [item.model_dump() for item in channels],
                    "loop_count": len(model.loops),
                },
                indent=2,
            )
        )

        # TODO: Persist IO mapping into PostgreSQL once schema/table is added.
        result = IOMappingResult(project_id=project_id, channels=channels)
        self.logger.info("IO mapping generated: project=%s channels=%s", project_id, len(channels))
        return result


io_mapping_engine = IOMappingEngine()
