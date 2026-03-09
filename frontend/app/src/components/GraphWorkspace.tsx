import { useMemo, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  type Edge,
  MarkerType,
  type Node,
  type NodeMouseHandler,
} from "reactflow";
import "reactflow/dist/style.css";

type GraphWorkspaceProps = {
  graphNodes: Array<{
    id: string;
    label: string;
    node_type: string;
    process_unit?: string | null;
    cluster_id?: string | null;
    cluster_order?: number | null;
    node_rank?: number | null;
  }>;
  graphEdges: Array<{
    id: string;
    source: string;
    target: string;
    edge_type: string;
    edge_class?: "process" | "monitoring";
    line_style?: "solid" | "dashed";
  }>;
  replayMode: boolean;
  replayPoint: number;
  selectedNode: string;
  tracePath: string[];
  onNodeSelect: (nodeId: string) => void;
  onReplayPointChange: (value: number) => void;
  onTraceNode: (nodeId: string) => void;
};

type PlantKind = "pump" | "tank" | "sensor" | "valve";

type PlantNode = {
  id: string;
  label: string;
  kind: PlantKind;
  x: number;
  y: number;
};

const KIND_COLOR: Record<PlantKind, string> = {
  pump: "var(--pump)",
  tank: "var(--tank)",
  sensor: "var(--sensor)",
  valve: "var(--valve)",
};

const toPlantKind = (nodeType: string): PlantKind => {
  const normalized = nodeType.toLowerCase();
  if (normalized === "pump") {
    return "pump";
  }
  if (normalized === "tank" || normalized === "basin" || normalized === "clarifier" || normalized === "process_unit") {
    return "tank";
  }
  if (normalized === "valve" || normalized === "control_valve") {
    return "valve";
  }
  return "sensor";
};

const SENSOR_TYPES = new Set([
  "analyzer",
  "flow_transmitter",
  "level_transmitter",
  "pressure_transmitter",
  "differential_pressure_transmitter",
  "level_switch",
  "sensor",
]);

const isSensorNode = (nodeType: string): boolean => SENSOR_TYPES.has(nodeType.toLowerCase());

const inferEdgeClass = (edge: { edge_class?: string; line_style?: string; edge_type: string }): "process" | "monitoring" => {
  if (edge.edge_class === "monitoring" || edge.line_style === "dashed") {
    return "monitoring";
  }
  if (["MEASURES", "MONITORS", "SIGNAL_TO"].includes(edge.edge_type)) {
    return "monitoring";
  }
  return "process";
};

const makeReplayColor = (id: string, replayPoint: number): string => {
  const modulo = (replayPoint + id.length) % 3;
  if (modulo === 0) {
    return "var(--ok)";
  }
  if (modulo === 1) {
    return "var(--warn)";
  }
  return "var(--fault)";
};

export default function GraphWorkspace({
  graphNodes,
  graphEdges,
  replayMode,
  replayPoint,
  selectedNode,
  tracePath,
  onNodeSelect,
  onReplayPointChange,
  onTraceNode,
}: GraphWorkspaceProps) {
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; nodeId: string } | null>(null);

  const traceSet = useMemo(() => new Set(tracePath), [tracePath]);

  const sourceNodes: PlantNode[] = useMemo(() => {
    const processNodes = graphNodes.filter((node) => !isSensorNode(node.node_type));
    const sensorNodes = graphNodes.filter((node) => isSensorNode(node.node_type));
    const positions = new Map<string, { x: number; y: number }>();

    const clusters = new Map<string, typeof processNodes>();
    for (const node of processNodes) {
      const key = node.cluster_id ?? node.process_unit ?? "cluster_unassigned";
      const existing = clusters.get(key) ?? [];
      existing.push(node);
      clusters.set(key, existing);
    }

    const orderedClusters = Array.from(clusters.entries()).sort((a, b) => {
      const minA = Math.min(...a[1].map((node) => node.cluster_order ?? 999));
      const minB = Math.min(...b[1].map((node) => node.cluster_order ?? 999));
      return minA - minB;
    });

    orderedClusters.forEach(([_, nodes], clusterIndex) => {
      const orderedNodes = [...nodes].sort((a, b) => {
        const rankA = a.node_rank ?? 999;
        const rankB = b.node_rank ?? 999;
        if (rankA !== rankB) {
          return rankA - rankB;
        }
        return a.label.localeCompare(b.label);
      });

      orderedNodes.forEach((node, nodeIndex) => {
        positions.set(node.id, {
          x: 140 + clusterIndex * 260,
          y: 90 + nodeIndex * 140,
        });
      });
    });

    const monitoringEdges = graphEdges.filter((edge) => inferEdgeClass(edge) === "monitoring");
    const offsetByTarget = new Map<string, number>();

    sensorNodes.forEach((sensor, index) => {
      const targetId = monitoringEdges.find((edge) => edge.source === sensor.id)?.target;
      const targetPos = targetId ? positions.get(targetId) : undefined;

      if (targetId && targetPos) {
        const offset = offsetByTarget.get(targetId) ?? 0;
        positions.set(sensor.id, {
          x: targetPos.x + 190,
          y: targetPos.y + offset,
        });
        offsetByTarget.set(targetId, offset + 46);
      } else {
        positions.set(sensor.id, {
          x: 980,
          y: 90 + index * 95,
        });
      }
    });

    return graphNodes.map((node) => {
      const pos = positions.get(node.id) ?? { x: 120, y: 120 };
      return {
        id: node.id,
        label: node.label,
        kind: toPlantKind(node.node_type),
        x: pos.x,
        y: pos.y,
      };
    });
  }, [graphEdges, graphNodes]);

  const nodes = useMemo<Node[]>(() => {
    return sourceNodes.map((item) => {
      const isTraceNode = traceSet.has(item.id);
      const hasTrace = traceSet.size > 0;
      const borderColor = isTraceNode ? "var(--primary)" : KIND_COLOR[item.kind];
      const baseColor = replayMode ? makeReplayColor(item.id, replayPoint) : "#f8fafc";
      const opacity = hasTrace && !isTraceNode ? 0.28 : 1;
      const selectedBorder = selectedNode === item.id ? "0 0 0 1px #2f3942 inset" : "none";

      return {
        id: item.id,
        position: { x: item.x, y: item.y },
        draggable: false,
        data: { label: item.label },
        style: {
          border: `2px solid ${borderColor}`,
          borderRadius: 6,
          width: 128,
          padding: "4px 6px",
          fontWeight: 600,
          fontSize: 11,
          letterSpacing: "0.01em",
          textTransform: "uppercase",
          background: baseColor,
          boxShadow: selectedBorder,
          opacity,
        },
      };
    });
  }, [replayMode, replayPoint, selectedNode, sourceNodes, traceSet]);

  const edges = useMemo<Edge[]>(() => {
      const sourceEdges: Edge[] = graphEdges.map((edge) => {
      const edgeClass = inferEdgeClass(edge);
      const dashed = edgeClass === "monitoring";
      const stroke = dashed ? "#6d7682" : "#39424c";
      return ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.edge_type,
      style: dashed ? { strokeDasharray: "7 5", strokeWidth: 1.5, stroke } : { strokeWidth: 2, stroke },
      markerEnd: { type: MarkerType.ArrowClosed, color: stroke },
    });
    });

    const hasTrace = traceSet.size > 0;

    return sourceEdges.map((edge) => {
      const isTraceEdge = traceSet.has(edge.source) && traceSet.has(edge.target);
      if (!hasTrace) {
        return edge;
      }

      return {
        ...edge,
        style: {
          ...(edge.style ?? {}),
          stroke: isTraceEdge ? "var(--primary)" : "#808080",
          strokeWidth: isTraceEdge ? 2.6 : 1.2,
          opacity: isTraceEdge ? 1 : 0.25,
        },
      };
    });
  }, [graphEdges, traceSet]);

  const handleNodeClick: NodeMouseHandler = (_, node) => {
    onNodeSelect(node.id);
    setContextMenu(null);
  };

  const handleNodeContextMenu: NodeMouseHandler = (event, node) => {
    event.preventDefault();
    onNodeSelect(node.id);
    setContextMenu({ x: event.clientX, y: event.clientY, nodeId: node.id });
  };

  return (
    <>
      <div className="graph-canvas" onClick={() => setContextMenu(null)}>
        <ReactFlow
          fitView
          nodes={nodes}
          edges={edges}
          onNodeClick={handleNodeClick}
          onNodeContextMenu={handleNodeContextMenu}
        >
          <Background color="#d3d9df" gap={20} />
          <Controls />
          <MiniMap />
        </ReactFlow>

        {contextMenu ? (
          <div className="node-context-menu" style={{ left: contextMenu.x, top: contextMenu.y }}>
            <button className="node-context-btn" onClick={() => onTraceNode(contextMenu.nodeId)} type="button">
              Trace Signal
            </button>
            <button className="node-context-btn" type="button">
              Trace Control Logic
            </button>
            <button className="node-context-btn" type="button">
              View Details
            </button>
          </div>
        ) : null}
      </div>

      {replayMode ? (
        <div className="replay-strip">
          <div className="replay-row">
            <span>Replay Timeline</span>
            <span>{`12:${String(Math.floor(replayPoint / 2)).padStart(2, "0")}:34`}</span>
          </div>
          <input
            className="replay-slider"
            max={120}
            min={0}
            onChange={(event) => onReplayPointChange(Number(event.target.value))}
            type="range"
            value={replayPoint}
          />
        </div>
      ) : null}
    </>
  );
}