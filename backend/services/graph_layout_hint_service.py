from __future__ import annotations

import logging

from models.pipeline import ClusterAssignment, EngineeringEntity, ProcessUnit


class GraphLayoutHintService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def assign(self, entities: list[EngineeringEntity], process_units: list[ProcessUnit]) -> list[EngineeringEntity]:
        order = {
            "INFLUENT-PUMP-STATION": 1,
            "SCREENING-UNIT-1": 2,
            "GRIT-REMOVAL-1": 3,
            "AERATION-BASIN-AREA": 4,
            "CLARIFIER-AREA": 5,
            "SLUDGE-HANDLING-AREA": 6,
            "CHEMICAL-FEED-SKID": 7,
            "BLOWER-PACKAGE": 8,
            "AIR-HEADER-1": 9,
        }

        unit_to_cluster: dict[str, ClusterAssignment] = {}
        for unit in process_units:
            cluster_id = f"cluster_{unit.id.lower().replace('-', '_')}"
            cluster_name = unit.name
            unit_to_cluster[unit.id] = ClusterAssignment(
                entity_id=unit.id,
                process_unit=unit.id,
                cluster_id=cluster_id,
                cluster_name=cluster_name,
                cluster_order=order.get(unit.id, 99),
                node_rank=0,
                preferred_direction="LR",
            )

        for index, entity in enumerate(sorted(entities, key=lambda item: item.id)):
            process_unit = entity.process_unit or "UNASSIGNED"
            assignment = unit_to_cluster.get(process_unit)
            if assignment is None:
                cluster_id = "cluster_unassigned"
                cluster_name = "Unassigned"
                cluster_order = 99
            else:
                cluster_id = assignment.cluster_id
                cluster_name = assignment.cluster_name
                cluster_order = assignment.cluster_order

            entity.cluster_id = cluster_id
            entity.cluster_name = cluster_name
            entity.cluster_order = cluster_order
            entity.node_rank = index
            entity.preferred_direction = "LR"

        self.logger.info("Graph layout hints assigned for %s entities", len(entities))
        return entities


graph_layout_hint_service = GraphLayoutHintService()
