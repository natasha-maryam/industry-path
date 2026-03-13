import { useEffect, useMemo, useState } from "react";
import ELK from "elkjs/lib/elk.bundled.js";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  type Edge,
  MarkerType,
  type Node,
  type NodeMouseHandler,
} from "reactflow";
import { Tooltip } from "react-tooltip";
import "reactflow/dist/style.css";
import "react-tooltip/dist/react-tooltip.css";

type GraphWorkspaceProps = {
  graphNodes: Array<{
    id: string;
    label: string;
    node_type: string;
    status: string;
    process_unit?: string | null;
    cluster_id?: string | null;
    cluster_order?: number | null;
    node_rank?: number | null;
    control_role?: string | null;
    signal_type?: string | null;
    instrument_role?: string | null;
    power_rating?: string | null;
    connected_to?: string[];
    controls?: string[];
    measures?: string[];
    control_path?: string[];
    metadata?: Record<string, unknown>;
    metadata_confidence?: Record<string, number>;
  }>;
  graphEdges: Array<{
    id: string;
    source: string;
    target: string;
    edge_type: string;
    edge_label?: string | null;
    semantic_kind?: string | null;
    edge_class?: "process" | "monitoring";
    line_style?: "solid" | "dashed" | "dotted";
  }>;
  replayMode: boolean;
  replayPoint: number;
  selectedNode: string;
  tracePath: string[];
  onNodeSelect: (nodeId: string) => void;
  onReplayPointChange: (value: number) => void;
  onTraceNode: (nodeId: string) => void;
};

type PlantKind = "pump" | "tank" | "sensor" | "valve" | "controller";

type PlantNode = {
  id: string;
  label: string;
  nodeType: string;
  processUnit?: string | null;
  controlRole?: string | null;
  signalType?: string | null;
  instrumentRole?: string | null;
  powerRating?: string | null;
  connectedTo: string[];
  controls: string[];
  measures: string[];
  controlPath: string[];
  kind: PlantKind;
};

const KIND_COLOR: Record<PlantKind, string> = {
  pump: "var(--pump)",
  tank: "var(--tank)",
  sensor: "var(--sensor)",
  valve: "var(--valve)",
  controller: "var(--controller)",
};

const toPlantKind = (nodeType: string): PlantKind => {
  const normalized = nodeType.toLowerCase();
  if (normalized.includes("controller")) {
    return "controller";
  }
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

const inferEdgeClass = (edge: { edge_class?: string; line_style?: string; edge_type: string }): "process" | "monitoring" => {
  if (edge.edge_class === "monitoring" || edge.line_style === "dashed") {
    return "monitoring";
  }
  if (["MEASURES", "MONITORS", "SIGNAL_TO"].includes(edge.edge_type)) {
    return "monitoring";
  }
  return "process";
};

const humanizeEdgeLabel = (edge: { edge_label?: string | null; edge_type: string }): string => {
  if (edge.edge_label && edge.edge_label.trim()) {
    return edge.edge_label;
  }
  return edge.edge_type.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase());
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
  const elk = useMemo(() => new ELK(), []);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; nodeId: string } | null>(null);
  const [layoutPositions, setLayoutPositions] = useState<Record<string, { x: number; y: number }>>({});

  const traceSet = useMemo(() => new Set(tracePath), [tracePath]);

  const sourceNodes: PlantNode[] = useMemo(() => {
    return graphNodes.map((node) => {
      return {
        id: node.id,
        label: node.label,
        nodeType: node.node_type,
        processUnit: node.process_unit,
        controlRole: node.control_role,
        signalType: node.signal_type,
        instrumentRole: node.instrument_role,
        powerRating: node.power_rating,
        connectedTo: node.connected_to ?? [],
        controls: node.controls ?? [],
        measures: node.measures ?? [],
        controlPath: node.control_path ?? [],
        kind: toPlantKind(node.node_type),
      };
    });
  }, [graphNodes]);

  useEffect(() => {
    let cancelled = false;

    const runLayout = async () => {
      if (!sourceNodes.length) {
        if (!cancelled) {
          setLayoutPositions({});
        }
        return;
      }

      const nodeIds = new Set(sourceNodes.map((node) => node.id));
      const layoutGraph = {
        id: "plant-root",
        layoutOptions: {
          "elk.algorithm": "layered",
          "elk.direction": "RIGHT",
          "elk.spacing.nodeNode": "80",
          "elk.spacing.edgeNode": "40",
        },
        children: sourceNodes.map((node) => ({ id: node.id, width: 144, height: 44 })),
        edges: graphEdges
          .filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target))
          .map((edge) => ({ id: edge.id, sources: [edge.source], targets: [edge.target] })),
      };

      try {
        const result = await elk.layout(layoutGraph);
        const next: Record<string, { x: number; y: number }> = {};
        for (const child of result.children ?? []) {
          if (!child.id) {
            continue;
          }
          next[child.id] = { x: child.x ?? 0, y: child.y ?? 0 };
        }
        if (!cancelled) {
          setLayoutPositions(next);
        }
      } catch {
        const fallback: Record<string, { x: number; y: number }> = {};
        sourceNodes.forEach((node, index) => {
          fallback[node.id] = {
            x: 120 + (index % 5) * 220,
            y: 90 + Math.floor(index / 5) * 120,
          };
        });
        if (!cancelled) {
          setLayoutPositions(fallback);
        }
      }
    };

    void runLayout();
    return () => {
      cancelled = true;
    };
  }, [elk, graphEdges, sourceNodes]);

  const nodes = useMemo<Node[]>(() => {
    return sourceNodes.map((item) => {
      const isTraceNode = traceSet.has(item.id);
      const hasTrace = traceSet.size > 0;
      const borderColor = isTraceNode ? "var(--primary)" : KIND_COLOR[item.kind];
      const baseColor = replayMode ? makeReplayColor(item.id, replayPoint) : "#f8fafc";
      const opacity = hasTrace && !isTraceNode ? 0.28 : 1;
      const selectedBorder = selectedNode === item.id ? "0 0 0 1px #2f3942 inset" : "none";
      const position = layoutPositions[item.id] ?? { x: 120, y: 120 };

      const tooltip = [
        `Tag: ${item.label}`,
        `Type: ${item.nodeType}`,
        `Process Unit: ${item.processUnit ?? "N/A"}`,
        `Role: ${item.controlRole ?? "N/A"}`,
        `Signal: ${item.signalType ?? "N/A"}`,
        `Instrument: ${item.instrumentRole ?? "N/A"}`,
        `Power: ${item.powerRating ?? "N/A"}`,
        `Controls: ${item.controls.length ? item.controls.join(", ") : "N/A"}`,
        `Measures: ${item.measures.length ? item.measures.join(", ") : "N/A"}`,
        `Control Path: ${item.controlPath.length ? item.controlPath.join(" | ") : "N/A"}`,
        `Connected To: ${item.connectedTo.length ? item.connectedTo.join(", ") : "N/A"}`,
      ].join("\n");

      return {
        id: item.id,
        position,
        draggable: false,
        data: {
          label: <div data-tooltip-id="plant-node-tooltip" data-tooltip-content={tooltip}>{item.label}</div>,
        },
        style: {
          border: `2px solid ${borderColor}`,
          borderRadius: 6,
          width: 128,
          padding: "4px 6px",
          fontWeight: 600,
          fontSize: 11,
          letterSpacing: "0.01em",
          textTransform: "none",
          background: baseColor,
          boxShadow: selectedBorder,
          opacity,
        },
      };
    });
  }, [layoutPositions, replayMode, replayPoint, selectedNode, sourceNodes, traceSet]);

  const edges = useMemo<Edge[]>(() => {
      const sourceEdges: Edge[] = graphEdges.map((edge) => {
      const edgeClass = inferEdgeClass(edge);
      const semantic = edge.semantic_kind ?? (edgeClass === "monitoring" ? "measurement_signal" : "process_flow");
      const styleType = edge.line_style ?? (semantic === "control_signal" ? "dashed" : semantic === "measurement_signal" ? "dotted" : "solid");
      const stroke = semantic === "control_signal" ? "#1E88E5" : semantic === "measurement_signal" ? "#43A047" : "#333333";
      const strokeDasharray = styleType === "dashed" ? "6 4" : styleType === "dotted" ? "2 2" : undefined;
      return ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: humanizeEdgeLabel(edge),
      labelStyle: { fontSize: 10, fontWeight: 600, fill: "#4f5964" },
      style: strokeDasharray ? { strokeDasharray, strokeWidth: 1.6, stroke } : { strokeWidth: 2, stroke },
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
        <Tooltip id="plant-node-tooltip" place="top" className="plant-tooltip" />

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