import type { GraphEdge, GraphNode } from "../services/api";

export type WorkspaceModuleId =
  | "plant_model"
  | "control_loops"
  | "io_mapping"
  | "control_logic"
  | "simulation"
  | "runtime"
  | "monitoring"
  | "diagnostics";

export type RightPanelTabId = "Details" | "Signals" | "Trace" | "Replay" | "IO Mapping" | "Control Loops" | "Diagnostics" | "Versions" | "P&ID Changes";

export type TopToolbarActionId =
  | "upload_documents"
  | "parse_plant_model"
  | "detect_control_loops"
  | "generate_logic"
  | "generate_io_mapping"
  | "export_logic"
  | "deploy_runtime"
  | "start_monitoring"
  | "analyze_fault"
  | "replay_event";

export type ModuleRunState = "idle" | "running" | "success" | "failed";

export type ModuleState = {
  state: ModuleRunState;
  message?: string;
  updatedAt?: string;
};

export type WorkspacePanelState = {
  activeModule: WorkspaceModuleId;
  activeRightTab: RightPanelTabId;
  activeBottomView: "simulation" | "monitoring" | "logic";
  codePanelMode: "control_logic" | "generated_st" | "verification" | "version_diff";
  monitoringPanelMode: "io_mapping" | "runtime" | "versions";
};

export type PlantGraphState = {
  nodes: GraphNode[];
  edges: GraphEdge[];
};

export const MODULE_LABELS: Record<WorkspaceModuleId, string> = {
  plant_model: "Plant Model",
  control_loops: "Control Loops",
  io_mapping: "IO Mapping",
  control_logic: "Control Logic",
  simulation: "Simulation",
  runtime: "Runtime",
  monitoring: "Monitoring",
  diagnostics: "Diagnostics",
};

export const MODULE_DEFAULT_STATE: Record<WorkspaceModuleId, ModuleState> = {
  plant_model: { state: "idle" },
  control_loops: { state: "idle" },
  io_mapping: { state: "idle" },
  control_logic: { state: "idle" },
  simulation: { state: "idle" },
  runtime: { state: "idle" },
  monitoring: { state: "idle" },
  diagnostics: { state: "idle" },
};
