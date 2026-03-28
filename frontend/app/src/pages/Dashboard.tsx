import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Cpu,
  FolderPlus,
  LoaderCircle,
  Trash2,
  Upload,
} from "lucide-react";
import { Toaster, toast } from "react-hot-toast";
import { Separator } from "react-resizable-panels";
import ActivityBar from "../components/ActivityBar";
import BottomPanel from "../components/BottomPanel";
import CodeExplorerPanel, { type GeneratedLogicFile, type STDiagnosticMarker, type STJumpLocation } from "../components/CodeExplorerPanel";
import CommandBar, { type ToolbarAction } from "../components/CommandBar";
import DetailsPanel, { type RightTab } from "../components/DetailsPanel";
import GraphWorkspace from "../components/GraphWorkspace";
import IOMappingTablePanel from "../components/IOMappingTablePanel";
import MainWorkspaceRouter from "../components/MainWorkspaceRouter";
import EngineeringDeterministicTable from "../components/plant/EngineeringDeterministicTable";
import RightControlLoopsTab from "../components/rightTabs/RightControlLoopsTab";
import RightDiagnosticsTab from "../components/rightTabs/RightDiagnosticsTab";
import RuntimeValidationPanel from "../components/RuntimeValidationPanel";
import SidebarModeProjects from "../components/SidebarModeProjects";
import SidebarModeSettings from "../components/SidebarModeSettings";
import SimulationValidationPanel from "../components/SimulationValidationPanel";
import VersionsWorkspace, { type VersionsWorkspaceSection } from "../components/versioning/VersionsWorkspace";
import WorkspaceActionPanel from "../components/WorkspaceActionPanel";
import type { RuntimeValidationPanelData } from "../components/RuntimeValidationPanel";
import { useWorkspaceContext } from "../context/WorkspaceContext";
import { mapSystemContextToPanelView } from "../intelligence/mapSystemContextToPanelView";
import { buildBehavior, buildImpact, buildSystemContext, type SystemContext, type SystemImpact } from "../intelligence/systemContext";
import {
  createSnapshot,
  diffVersions,
  exportVersion,
  getVersionHistory,
  rollbackVersion,
  getVersionById,
} from "../services/versioningApi";
import type { VersionDiffResponse, VersionRecord } from "../types/versioning";
import {
  applySnapshotTrigger,
  applyRuntimeInputForce,
  clearRuntimeInputForce,
  createProject,
  createPLCExport,
  getPLCExportReadiness,
  handoffPLCExportForDeployment,
  createInitialPipelineStatuses,
  deleteProject,
  deployDirectPLC,
  deployRuntimeControl,
  detectControlLoops,
  analyzeFault,
  getControlLoop,
  getControlLoops,
  getMonitoring,
  getProjectDocuments,
  getSystemContextForTag,
  getReplay,
  getRuntimeTags,
  getRuntimeState,
  getLatestRuntimeDeployment,
  generateLogic,
  generateIOMapping,
  getActiveProject,
  getLatestIOMapping,
  getPIDChanges,
  getRuntimeDiagnostics,
  getRuntimeForcedInputs,
  getSimulationAnalysis,
  getSimulationTrace,
  getLogic,
  loadDeterministicBehaviorCache,
  getEngineeringTable,
  getGraph,
  getTrace,
  listProjects,
  parseProject,
  applyPIDUpdate,
  runSimulation,
  runRuntimeEvaluationCycle,
  setActiveProject,
  startRuntimeControl,
  stopRuntimeControl,
  uploadDocuments,
  verifySTWorkspaceWithRetry,
  buildExportDownloadUrl,
  type IOMappingIssue,
  type IOMappingSummaryByType,
  type IOMappingTableRow,
  type PipelineStageKey,
  type RuntimeControlDeployResponse,
  type RuntimeStateResponse,
  type RuntimeEvaluationCycle,
  type RuntimeInputCatalogItem,
  type RuntimeSignalType,
  type SimulationTraceIssue,
  type SimulationTracePoint,
  type SimulationValidationPanelResponse,
  type ControlLoopRecord,
  type DirectPLCProtocol,
  type DirectPLCTargetRuntime,
  type FaultAnalysisResult,
  type STWorkspaceVerificationResponse,
  type PipelineStageStatusMap,
  type PIDReconcileSummary,
  type PLCExportResponse,
  type PLCExportVendor,
  type ExportReadinessSummary,
  type ExportSourceMode,
  type ExportDeploymentState,
  type EngineeringTableResponse,
  type EngineeringTableResponseRow,
  type ProjectDocument,
  type Project,
} from "../services/api";
import "../styles/dashboard.css";
import type { MainWorkspaceViewId, ModuleState, WorkspaceModuleId, WorkspacePanelState } from "../types/workspace";
import { MODULE_DEFAULT_STATE, MODULE_LABELS } from "../types/workspace";

type EquipmentType = "Tank" | "Pump" | "Sensor" | "Valve";
type BottomView = "simulation" | "monitoring" | "logic";
type CodePanelMode = "control_logic" | "generated_st" | "verification" | "version_diff";
type MonitoringPanelMode = "io_mapping" | "runtime" | "versions";
type ActivityMode = "projects" | "settings";
type SettingsNavItemId =
  | "general"
  | "project_settings"
  | "ai_connectors"
  | "runtime_connections"
  | "export_integrations";
type ProjectFeatureId = "versions" | "pid";

type UIShellState = {
  activeSidebarMode: ActivityMode;
  activeWorkspaceModule: WorkspaceModuleId;
  activeMainView: MainWorkspaceViewId;
  selectedRowId: string;
  activeRightTab: RightTab;
};

type ThinUIState = {
  activeSidebarMode: ActivityMode;
  activeView: MainWorkspaceViewId;
  selectedProject: string;
  selectedRow: string;
  activeTab: RightTab;
};

type NavigatorSelection = {
  type: "project" | "module" | "feature" | "node";
  id: string;
};

type ControlLoopModalState = {
  open: boolean;
  noLoop: boolean;
  loopId: string;
  sensor: string;
  process: string;
  actuator: string;
  controlPath: string;
  source: string;
  confidence: number | null;
};

type Equipment = {
  id: string;
  type: EquipmentType;
  status: string;
  motor?: string;
  signals: string[];
  logic: string;
  processUnit?: string;
  controlRole?: string;
  signalType?: string;
  instrumentRole?: string;
  powerRating?: string;
  connections: string[];
  controls: string[];
  measures: string[];
  controlPath: string[];
  metadataConfidence: Record<string, number>;
};

const EMPTY_EQUIPMENT: Equipment = {
  id: "N/A",
  type: "Sensor",
  status: "unknown",
  motor: "N/A",
  signals: [],
  logic: "N/A",
  processUnit: "N/A",
  controlRole: "N/A",
  signalType: "N/A",
  instrumentRole: "N/A",
  powerRating: "N/A",
  connections: [],
  controls: [],
  measures: [],
  controlPath: [],
  metadataConfidence: {},
};

const ACTION_PROGRESS_LABELS: Record<ToolbarAction, string> = {
  upload_documents: "Uploading Documents",
  parse_plant_model: "Parsing Plant Model",
  detect_control_loops: "Detecting Control Loops",
  generate_logic: "Generating Logic",
  generate_io_mapping: "Generating IO Mapping",
  run_simulation: "Running Simulation",
  export_logic: "Exporting Logic",
  deploy_runtime: "Deploying Runtime",
  start_monitoring: "Starting Monitoring",
  analyze_fault: "Analyzing Fault",
  replay_event: "Loading Replay Event",
  versions: "Loading Versions",
};

const ACTION_MODULE_MAP: Partial<Record<ToolbarAction, WorkspaceModuleId>> = {
  upload_documents: "documents",
  parse_plant_model: "plant_model",
  detect_control_loops: "control_loops",
  generate_logic: "control_logic",
  generate_io_mapping: "io_mapping",
  run_simulation: "simulation",
  deploy_runtime: "runtime",
  start_monitoring: "monitoring",
};

const toEquipmentType = (nodeType: string): EquipmentType => {
  const normalized = nodeType.toLowerCase();
  if (normalized === "tank") {
    return "Tank";
  }
  if (normalized === "pump") {
    return "Pump";
  }
  if (normalized === "valve") {
    return "Valve";
  }
  return "Sensor";
};

const normalizeGeneratedFilePath = (path: string): string => path.replace(/^\/+/, "").replace(/\\/g, "/").trim();

const parseGeneratedLogicFiles = (bundledCode: string): GeneratedLogicFile[] => {
  const code = bundledCode.trim();
  if (!code) {
    return [];
  }

  const markerPattern = /\(\*\s*=====\s*FILE:\s*(.+?)\s*=====\s*\*\)/g;
  const matches = [...code.matchAll(markerPattern)];
  if (matches.length === 0) {
    return [{ path: "main.st", content: code }];
  }

  return matches
    .map((current, index) => {
      const next = matches[index + 1];
      const start = (current.index ?? 0) + current[0].length;
      const end = next?.index ?? code.length;
      const path = normalizeGeneratedFilePath(current[1]?.trim() || `file_${index + 1}.st`);
      const content = code.slice(start, end).trim();
      return { path, content };
    })
    .filter((item, index, array) => array.findIndex((candidate) => candidate.path === item.path) === index);
};

const toWorkspaceVerifyTarget = (projectId: string): string => projectId;

const normalizeVerifierFilePath = (filePath: string): string => {
  const normalized = normalizeGeneratedFilePath(filePath);
  return normalized.startsWith("control_logic/") ? normalized.replace(/^control_logic\//, "") : normalized;
};

const toComparableToken = (value: string): string => value.toUpperCase().replace(/[^A-Z0-9]/g, "");

const resolveTraceTag = (candidate: string, trace: SimulationTracePoint[]): string => {
  const candidateToken = toComparableToken(candidate || "");
  if (!candidateToken) {
    return "";
  }
  const match = trace.find((item) => toComparableToken(item.tag || "") === candidateToken);
  return match?.tag || "";
};

const identityKeyForEngineeringRow = (row: EngineeringTableResponseRow): string => {
  return row.id?.trim() || row.tag.trim();
};

const arrayEquals = (left: readonly string[], right: readonly string[]): boolean => {
  if (left === right) {
    return true;
  }
  if (left.length !== right.length) {
    return false;
  }
  for (let index = 0; index < left.length; index += 1) {
    if (left[index] !== right[index]) {
      return false;
    }
  }
  return true;
};

const shallowRecordEquals = (left: Record<string, unknown>, right: Record<string, unknown>): boolean => {
  if (left === right) {
    return true;
  }
  const leftKeys = Object.keys(left);
  const rightKeys = Object.keys(right);
  if (leftKeys.length !== rightKeys.length) {
    return false;
  }
  for (const key of leftKeys) {
    if (!(key in right)) {
      return false;
    }
    if (left[key] !== right[key]) {
      return false;
    }
  }
  return true;
};

const traceabilityEquals = (
  left: EngineeringTableResponseRow["traceability"],
  right: EngineeringTableResponseRow["traceability"]
): boolean => {
  if (left === right) {
    return true;
  }
  if (left.length !== right.length) {
    return false;
  }
  for (let index = 0; index < left.length; index += 1) {
    const leftItem = left[index];
    const rightItem = right[index];
    if (!rightItem) {
      return false;
    }
    if (
      leftItem.source_type !== rightItem.source_type ||
      leftItem.source_id !== rightItem.source_id ||
      leftItem.excerpt !== rightItem.excerpt ||
      leftItem.confidence !== rightItem.confidence
    ) {
      return false;
    }
  }
  return true;
};

const engineeringRowEquals = (left: EngineeringTableResponseRow, right: EngineeringTableResponseRow): boolean => {
  return (
    left.id === right.id &&
    left.tag === right.tag &&
    left.type === right.type &&
    left.subtype === right.subtype &&
    left.description === right.description &&
    left.system === right.system &&
    left.equipment === right.equipment &&
    left.process_role === right.process_role &&
    left.current_value === right.current_value &&
    left.state === right.state &&
    left.setpoint === right.setpoint &&
    left.mode === right.mode &&
    left.unit === right.unit &&
    left.range_min === right.range_min &&
    left.range_max === right.range_max &&
    left.fail_state === right.fail_state &&
    left.power === right.power &&
    left.confidence === right.confidence &&
    left.num_connections === right.num_connections &&
    left.num_upstream === right.num_upstream &&
    left.num_downstream === right.num_downstream &&
    left.is_orphan === right.is_orphan &&
    left.is_controlled === right.is_controlled &&
    left.is_actuated === right.is_actuated &&
    arrayEquals(left.measures, right.measures) &&
    arrayEquals(left.controls, right.controls) &&
    arrayEquals(left.controlled_by, right.controlled_by) &&
    arrayEquals(left.signal_inputs, right.signal_inputs) &&
    arrayEquals(left.signal_outputs, right.signal_outputs) &&
    arrayEquals(left.upstream, right.upstream) &&
    arrayEquals(left.downstream, right.downstream) &&
    arrayEquals(left.flow_path, right.flow_path) &&
    arrayEquals(left.document_source, right.document_source) &&
    arrayEquals(left.line_reference, right.line_reference) &&
    arrayEquals(left.control_chain, right.control_chain) &&
    arrayEquals(left.flow_chain, right.flow_chain) &&
    arrayEquals(left.warnings, right.warnings) &&
    shallowRecordEquals(left.grounded_fields, right.grounded_fields) &&
    shallowRecordEquals(left.derived_fields, right.derived_fields) &&
    traceabilityEquals(left.traceability, right.traceability)
  );
};

const warningEquals = (left: EngineeringTableResponse["warnings"], right: EngineeringTableResponse["warnings"]): boolean => {
  if (left === right) {
    return true;
  }
  if (left.length !== right.length) {
    return false;
  }
  for (let index = 0; index < left.length; index += 1) {
    const leftWarning = left[index];
    const rightWarning = right[index];
    if (!rightWarning) {
      return false;
    }
    if (
      leftWarning.code !== rightWarning.code ||
      leftWarning.severity !== rightWarning.severity ||
      leftWarning.message !== rightWarning.message ||
      !arrayEquals(leftWarning.affected_tags, rightWarning.affected_tags)
    ) {
      return false;
    }
  }
  return true;
};

const summaryEquals = (left: EngineeringTableResponse["summary"], right: EngineeringTableResponse["summary"]): boolean => {
  return (
    left.total_rows === right.total_rows &&
    left.grounded_rows === right.grounded_rows &&
    left.inferred_rows === right.inferred_rows &&
    left.orphan_rows === right.orphan_rows &&
    left.controlled_rows === right.controlled_rows &&
    left.actuated_rows === right.actuated_rows &&
    left.avg_confidence === right.avg_confidence &&
    left.distinct_systems === right.distinct_systems &&
    left.distinct_document_sources === right.distinct_document_sources
  );
};

const mergeEngineeringTableData = (
  previous: EngineeringTableResponse | null,
  incoming: EngineeringTableResponse
): EngineeringTableResponse => {
  if (!previous) {
    return incoming;
  }

  const previousByIdentity = new Map(previous.rows.map((row) => [identityKeyForEngineeringRow(row), row]));
  let rowRefsChanged = incoming.rows.length !== previous.rows.length;

  const mergedRows = incoming.rows.map((incomingRow) => {
    const existing = previousByIdentity.get(identityKeyForEngineeringRow(incomingRow));
    if (!existing) {
      rowRefsChanged = true;
      return incomingRow;
    }
    if (engineeringRowEquals(existing, incomingRow)) {
      return existing;
    }
    rowRefsChanged = true;
    return incomingRow;
  });

  const hasSummaryChange = !summaryEquals(previous.summary, incoming.summary);
  const hasWarningChange = !warningEquals(previous.warnings, incoming.warnings);

  if (!rowRefsChanged && !hasSummaryChange && !hasWarningChange) {
    return previous;
  }

  return {
    ...incoming,
    rows: mergedRows,
    summary: hasSummaryChange ? incoming.summary : previous.summary,
    warnings: hasWarningChange ? incoming.warnings : previous.warnings,
  };
};

const PIPELINE_STAGE_LABELS: Record<PipelineStageKey, string> = {
  extraction: "Extraction",
  normalization: "Normalization",
  plant_graph: "Plant graph",
  control_loop_discovery: "Control loop discovery",
  engineering_validation: "Engineering validation",
  logic_completion: "Logic completion",
  st_generation: "ST generation",
  st_verification: "ST verification",
  io_mapping: "IO mapping",
  runtime_validation: "Runtime control",
  simulation_validation: "Simulation validation",
  version_snapshot: "Version snapshot",
};

type PipelineToastCopy = {
  running?: string;
  success?: string;
  failed?: string;
  warning?: string;
};

export default function Dashboard() {
  const { activeProjectId: selectedProjectId, setActiveProjectId: setSelectedProjectId, plantGraph, setPlantGraph } = useWorkspaceContext();
  const graphNodes = plantGraph.nodes;

  const [activeAction, setActiveAction] = useState<ToolbarAction>("upload_documents");
  const [selectedNode, setSelectedNode] = useState<string>("");
  const [selectedSystemContextPayload, setSelectedSystemContextPayload] = useState<Record<string, unknown> | null>(null);
  const [systemContextLoading, setSystemContextLoading] = useState<boolean>(false);
  const [systemContextError, setSystemContextError] = useState<string | null>(null);
  const [uiShell, setUIShell] = useState<UIShellState>({
    activeSidebarMode: "projects",
    activeWorkspaceModule: "plant_model",
    activeMainView: "table",
    selectedRowId: "",
    activeRightTab: "Details",
  });
  const [activeSettingsItem, setActiveSettingsItem] = useState<SettingsNavItemId>("general");
  const [activeProjectFeature, setActiveProjectFeature] = useState<ProjectFeatureId | null>(null);
  const [navigatorSelection, setNavigatorSelection] = useState<NavigatorSelection | null>({ type: "module", id: "plant_model" });
  const [panelState, setPanelState] = useState<WorkspacePanelState>({
    activeModule: "plant_model",
    activeRightTab: "Details",
    activeBottomView: "simulation",
    codePanelMode: "control_logic",
    monitoringPanelMode: "io_mapping",
  });
  const activeActivity = uiShell.activeSidebarMode;
  const selectedRow = uiShell.selectedRowId;
  const activeMainView = uiShell.activeMainView;
  const activeModule = panelState.activeModule;
  const activeTab = panelState.activeRightTab;
  const activeBottomView = panelState.activeBottomView;
  const codePanelMode = panelState.codePanelMode;
  const monitoringPanelMode = panelState.monitoringPanelMode;
  const uiState = useMemo<ThinUIState>(
    () => ({
      activeSidebarMode: activeActivity,
      activeView: activeMainView,
      selectedProject: selectedProjectId,
      selectedRow,
      activeTab,
    }),
    [activeActivity, activeMainView, selectedProjectId, selectedRow, activeTab]
  );

  const setActiveTab = (tab: RightTab): void => {
    setPanelState((previous) => ({ ...previous, activeRightTab: tab }));
    setUIShell((previous) => ({ ...previous, activeRightTab: tab }));
    if (tab === "P&ID Changes" && selectedProjectId) {
      void refreshPIDChanges();
    }
  };

  const setActiveBottomView = (view: BottomView): void => {
    setPanelState((previous) => ({ ...previous, activeBottomView: view }));
  };

  const setCodePanelMode = (mode: CodePanelMode): void => {
    setPanelState((previous) => ({ ...previous, codePanelMode: mode }));
  };

  const setMonitoringPanelMode = (mode: MonitoringPanelMode): void => {
    setPanelState((previous) => ({ ...previous, monitoringPanelMode: mode }));
  };

  const setActiveModule = (moduleId: WorkspaceModuleId): void => {
    setPanelState((previous) => ({ ...previous, activeModule: moduleId }));
    setUIShell((previous) => ({ ...previous, activeWorkspaceModule: moduleId }));
  };

  const setActiveSidebarMode = (mode: ActivityMode): void => {
    setUIShell((previous) => ({ ...previous, activeSidebarMode: mode }));
  };

  const setActiveMainView = (view: MainWorkspaceViewId): void => {
    setUIShell((previous) => ({ ...previous, activeMainView: view }));
  };

  const setSelectedRowId = (rowId: string): void => {
    setUIShell((previous) => ({ ...previous, selectedRowId: rowId }));
  };

  const refreshProjectDocuments = useCallback(async (projectId: string | null): Promise<void> => {
    if (!projectId) {
      return;
    }

    try {
      const documents = await getProjectDocuments(projectId);
      setProjectDocumentsById((previous) => ({ ...previous, [projectId]: documents }));
    } catch {
      setProjectDocumentsById((previous) => ({ ...previous, [projectId]: [] }));
    }
  }, []);

  const handleSettingsNavSelect = (item: SettingsNavItemId): void => {
    setActiveSettingsItem(item);
    if (item === "project_settings") {
      setActiveProjectFeature("versions");
      setMonitoringPanelMode("versions");
      setActiveBottomView("monitoring");
      setActiveModule("monitoring");
      setActiveMainView("monitoring");
      return;
    }
    if (item === "runtime_connections") {
      setActiveProjectFeature(null);
      setMonitoringPanelMode("runtime");
      setActiveBottomView("monitoring");
      setActiveTab("Diagnostics");
      setActiveModule("runtime");
      setActiveMainView("monitoring");
      return;
    }
    if (item === "export_integrations") {
      setActiveProjectFeature(null);
      setCodePanelMode("control_logic");
      setActiveBottomView("logic");
      setActiveModule("control_logic");
      setActiveMainView("logic");
      return;
    }
    setActiveProjectFeature(null);
    setActiveTab("Details");
    setActiveModule("plant_model");
    setActiveMainView("graph");
  };

  const handleProjectFeatureSelect = (feature: ProjectFeatureId): void => {
    setNavigatorSelection({ type: "feature", id: feature });
    setActiveProjectFeature(feature);
    setMonitoringPanelMode("versions");
    setActiveBottomView("monitoring");
    setActiveMainView("monitoring");
    if (feature === "pid" && selectedProjectId) {
      void refreshPIDChanges();
    }
  };


  const [tracePath, setTracePath] = useState<string[]>([]);
  const [replayPoint, setReplayPoint] = useState<number>(64);
  const [showLogic, setShowLogic] = useState<boolean>(false);
  const [controlLogicCode, setControlLogicCode] = useState<string>("");
  const [generatedLogic, setGeneratedLogic] = useState<string>("");
  const [generatedSTFiles, setGeneratedSTFiles] = useState<GeneratedLogicFile[]>([]);
  const [selectedSTFilePath, setSelectedSTFilePath] = useState<string | null>(null);
  const [stDiagnosticsByFile, setSTDiagnosticsByFile] = useState<Record<string, STDiagnosticMarker[]>>({});
  const [stJumpLocation, setSTJumpLocation] = useState<STJumpLocation | null>(null);
  const [logicWarnings, setLogicWarnings] = useState<string[]>([]);
  const [logicValidationIssues, setLogicValidationIssues] = useState<string[]>([]);
  const [stVerificationData, setSTVerificationData] = useState<STWorkspaceVerificationResponse | null>(null);
  const [isVerifyingST, setIsVerifyingST] = useState<boolean>(false);
  const [stVerificationFailedMessage, setSTVerificationFailedMessage] = useState<string | null>(null);
  const [ioMappingRows, setIOMappingRows] = useState<IOMappingTableRow[]>([]);
  const [ioMappingIssues, setIOMappingIssues] = useState<IOMappingIssue[]>([]);
  const [selectedIOMappingTag, setSelectedIOMappingTag] = useState<string | null>(null);
  const [ioMappingSummary, setIOMappingSummary] = useState<IOMappingSummaryByType | null>(null);
  const [isGeneratingIOMapping, setIsGeneratingIOMapping] = useState<boolean>(false);
  const [isExportingLogic, setIsExportingLogic] = useState<boolean>(false);
  const [pidChanges, setPIDChanges] = useState<PIDReconcileSummary | null>(null);
  const [pidChangesLoading, setPIDChangesLoading] = useState<boolean>(false);
  const [pidChangesError, setPIDChangesError] = useState<string | null>(null);
  const [pidApplying, setPIDApplying] = useState<boolean>(false);
  const [pidAcceptedConflicts, setPIDAcceptedConflicts] = useState<boolean>(false);
  const [pidCreatingSnapshot, setPIDCreatingSnapshot] = useState<boolean>(false);
  const [showExportDialog, setShowExportDialog] = useState<boolean>(false);
  const [showDirectPLCDeployDialog, setShowDirectPLCDeployDialog] = useState<boolean>(false);
  const [exportVendor, setExportVendor] = useState<PLCExportVendor>("siemens");
  const [exportSourceMode, setExportSourceMode] = useState<ExportSourceMode>("live");
  const [exportSourceVersionTag, setExportSourceVersionTag] = useState<string | null>(null);
  const [exportReadiness, setExportReadiness] = useState<ExportReadinessSummary | null>(null);
  const [exportReadinessLoading, setExportReadinessLoading] = useState<boolean>(false);
  const [exportReadinessError, setExportReadinessError] = useState<string | null>(null);
  const [exportResult, setExportResult] = useState<PLCExportResponse | null>(null);
  const [deploymentTargetRuntime, setDeploymentTargetRuntime] = useState<string>("openplc");
  const [exportDeploymentState, setExportDeploymentState] = useState<ExportDeploymentState>("not_ready");
  const [exportDeploymentMessage, setExportDeploymentMessage] = useState<string>("Export package not prepared.");
  const [exportDeploymentLogs, setExportDeploymentLogs] = useState<string[]>([]);
  const [, setExportDeploymentErrors] = useState<string[]>([]);
  const [exportDeploymentBusy, setExportDeploymentBusy] = useState<boolean>(false);
  const [exportDeploymentAction, setExportDeploymentAction] = useState<"prepare" | "deploy" | null>(null);
  const [directDeployBusy, setDirectDeployBusy] = useState<boolean>(false);
  const [directDeployResult, setDirectDeployResult] = useState<string>("");
  const [directDeployForm, setDirectDeployForm] = useState<{
    plcAddress: string;
    protocol: DirectPLCProtocol;
    targetRuntime: DirectPLCTargetRuntime;
    ioConfiguration: string;
  }>({
    plcAddress: "",
    protocol: "opc_ua",
    targetRuntime: "openplc",
    ioConfiguration: "",
  });
  const [ioMappingFailedMessage, setIOMappingFailedMessage] = useState<string | null>(null);
  const [pipelineStatuses, setPipelineStatuses] = useState<PipelineStageStatusMap>(() => createInitialPipelineStatuses());
  const [moduleStates, setModuleStates] = useState<Record<WorkspaceModuleId, ModuleState>>(MODULE_DEFAULT_STATE);
  const [projects, setProjects] = useState<Project[]>([]);
  const [controlLoops, setControlLoops] = useState<ControlLoopRecord[]>([]);
  const [isControlLoopsLoading, setIsControlLoopsLoading] = useState<boolean>(false);
  const [controlLoopsError, setControlLoopsError] = useState<string | null>(null);
  const [selectedControlLoopTag, setSelectedControlLoopTag] = useState<string | null>(null);
  const [engineeringTableData, setEngineeringTableData] = useState<EngineeringTableResponse | null>(null);
  const [engineeringTableLoading, setEngineeringTableLoading] = useState<boolean>(false);
  const [engineeringTableError, setEngineeringTableError] = useState<string | null>(null);
  const [liveEngineeringRows, setLiveEngineeringRows] = useState<EngineeringTableResponseRow[]>([]);
  const [liveEngineeringRowsFilteredCount, setLiveEngineeringRowsFilteredCount] = useState<number>(0);
  const [liveEngineeringRowsLoading, setLiveEngineeringRowsLoading] = useState<boolean>(false);
  const [behaviorRefreshKey, setBehaviorRefreshKey] = useState<number>(0);
  const [selectedEngineeringTag, setSelectedEngineeringTag] = useState<string | null>(null);
  const [selectedEngineeringRow, setSelectedEngineeringRow] = useState<EngineeringTableResponseRow | null>(null);
  const [selectedWhyTraceTag, setSelectedWhyTraceTag] = useState<string | null>(null);
  const [whyFocusToken, setWhyFocusToken] = useState<number>(0);
  const [unsTableRowsOverride, setUnsTableRowsOverride] = useState<EngineeringTableResponseRow[] | null>(null);
  const [productionAuthToken, setProductionAuthToken] = useState<string>("");
  const [runtimeValidationData, setRuntimeValidationData] = useState<RuntimeValidationPanelData | null>(null);
  const [isRuntimeStateLoading, setIsRuntimeStateLoading] = useState<boolean>(false);
  const [runtimeFailedMessage, setRuntimeFailedMessage] = useState<string | null>(null);
  const [isRuntimeActionBusy, setIsRuntimeActionBusy] = useState<boolean>(false);
  const [runtimeTelemetryTags, setRuntimeTelemetryTags] = useState<Record<string, unknown>>({});
  const [runtimeForceableInputs, setRuntimeForceableInputs] = useState<RuntimeInputCatalogItem[]>([]);
  const [forcedTagNames, setForcedTagNames] = useState<string[]>([]);
  const [runtimeDiagnostics, setRuntimeDiagnostics] = useState<RuntimeEvaluationCycle | null>(null);
  const [faultAnalysis, setFaultAnalysis] = useState<FaultAnalysisResult | null>(null);
  const [faultAnalysisTag, setFaultAnalysisTag] = useState<string | null>(null);
  const [faultAnalysisInputMessage, setFaultAnalysisInputMessage] = useState<string | null>(null);
  const [isFaultAnalysisLoading, setIsFaultAnalysisLoading] = useState<boolean>(false);
  const [faultAnalysisError, setFaultAnalysisError] = useState<string | null>(null);
  const [simulationValidationData, setSimulationValidationData] = useState<SimulationValidationPanelResponse | null>(null);
  const [simulationFailedMessage, setSimulationFailedMessage] = useState<string | null>(null);
  const [simulationTrace, setSimulationTrace] = useState<SimulationTracePoint[]>([]);
  const [simulationIssues, setSimulationIssues] = useState<SimulationTraceIssue[]>([]);
  const [selectedReplayTag, setSelectedReplayTag] = useState<string>("");
  const [statusText, setStatusText] = useState<string>("Loading projects...");
  const [selectedUploadFiles, setSelectedUploadFiles] = useState<string[]>([]);
  const [projectDocumentsById, setProjectDocumentsById] = useState<Record<string, ProjectDocument[]>>({});
  const [isParsing, setIsParsing] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isLeftPanelCollapsed, setIsLeftPanelCollapsed] = useState<boolean>(false);
  const [isRightPanelExpanded, setIsRightPanelExpanded] = useState<boolean>(false);
  const [rightPanelWidth, setRightPanelWidth] = useState<number>(() => {
    if (typeof window === "undefined") {
      return 300;
    }
    const parsed = Number.parseInt(window.localStorage.getItem("crosslayerx-right-panel-width") || "", 10);
    if (Number.isFinite(parsed)) {
      return Math.min(760, Math.max(260, parsed));
    }
    return 300;
  });
  const [showCreateProjectModal, setShowCreateProjectModal] = useState<boolean>(false);
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);
  const [controlLoopModal, setControlLoopModal] = useState<ControlLoopModalState>({
    open: false,
    noLoop: false,
    loopId: "",
    sensor: "",
    process: "",
    actuator: "",
    controlPath: "",
    source: "",
    confidence: null,
  });
  const [versions, setVersions] = useState<VersionRecord[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<VersionRecord | null>(null);
  const [selectedVersionTags, setSelectedVersionTags] = useState<string[]>([]);
  const [versionDiff, setVersionDiff] = useState<VersionDiffResponse | null>(null);
  const [versioningLoading, setVersioningLoading] = useState<boolean>(false);
  const [versioningError, setVersioningError] = useState<string | null>(null);
  const [versionBusyAction, setVersionBusyAction] = useState<"snapshot" | "rollback" | "compare" | "export" | null>(null);
  const [versioningSettings, setVersioningSettings] = useState({
    enableAutoVersioning: true,
    autoSnapshotOnDeploy: true,
    enableDatabaseVersioning: true,
    maxSnapshotsStored: 100,
    snapshotRetentionDays: 90,
    gitRepositoryLocation: "backend-controlled",
  });
  const [projectForm, setProjectForm] = useState<{
    name: string;
    industry: string;
    description: string;
    plcRuntime: "beremiz" | "codesys" | "siemens" | "other";
    owner: string;
    status: "draft" | "active" | "archived";
    importFiles: File[];
  }>({
    name: "",
    industry: "Process Manufacturing",
    description: "",
    plcRuntime: "beremiz",
    owner: "system",
    status: "draft",
    importFiles: [],
  });
  const uploadInputRef = useRef<HTMLInputElement | null>(null);
  const previousPipelineStatusesRef = useRef<PipelineStageStatusMap>(pipelineStatuses);
  const suppressInitialPipelineWorkspaceSyncRef = useRef<boolean>(true);
  const pendingPipelineToastCopyRef = useRef<Partial<Record<PipelineStageKey, PipelineToastCopy>>>({});
  const behaviorHydrationSignatureRef = useRef<string>("");
  const rightResizeStartRef = useRef<{ startX: number; startWidth: number } | null>(null);
  const exportReadinessRequestIdRef = useRef<number>(0);
  const systemContextRequestIdRef = useRef<number>(0);

  const queuePipelineToastCopy = useCallback((stage: PipelineStageKey, copy: PipelineToastCopy): void => {
    pendingPipelineToastCopyRef.current = {
      ...pendingPipelineToastCopyRef.current,
      [stage]: {
        ...pendingPipelineToastCopyRef.current[stage],
        ...copy,
      },
    };
  }, []);

  const setModuleState = (moduleId: WorkspaceModuleId, state: ModuleState): void => {
    setModuleStates((previous) => ({ ...previous, [moduleId]: state }));
  };

  const refreshControlLoops = useCallback(
    async (projectId: string, options?: { showLoading?: boolean }): Promise<ControlLoopRecord[]> => {
      const showLoading = options?.showLoading ?? true;
      if (showLoading) {
        setIsControlLoopsLoading(true);
      }
      setControlLoopsError(null);
      try {
        const loops = await getControlLoops(projectId);
        setControlLoops(loops);
        setSelectedControlLoopTag((current) => {
          if (current && loops.some((loop) => loop.loop_tag === current)) {
            return current;
          }
          return loops[0]?.loop_tag ?? null;
        });
        return loops;
      } catch {
        setControlLoops([]);
        setSelectedControlLoopTag(null);
        setControlLoopsError("Control loops could not be loaded.");
        return [];
      } finally {
        if (showLoading) {
          setIsControlLoopsLoading(false);
        }
      }
    },
    []
  );

  const runControlLoopDetection = useCallback(async (): Promise<void> => {
    if (!selectedProjectId) {
      setStatusText("Select or create a project first.");
      return;
    }

    setIsControlLoopsLoading(true);
    setControlLoopsError(null);
    setModuleState("control_loops", { state: "running", message: "Detecting control loops", updatedAt: new Date().toISOString() });
    setStatusText("Detecting control loops...");

    try {
      await detectControlLoops(selectedProjectId);
      const loops = await refreshControlLoops(selectedProjectId, { showLoading: false });
      const message = loops.length > 0 ? `Detected ${loops.length} control loop(s)` : "No control loops detected in the current graph";
      setModuleState("control_loops", {
        state: "success",
        message,
        updatedAt: new Date().toISOString(),
      });
      setActiveModule("control_loops");
      setActiveTab("Control Loops");
      setStatusText(`${message}.`);
    } catch {
      setControlLoopsError("Control loop detection failed.");
      setModuleState("control_loops", { state: "failed", message: "Control loop detection failed", updatedAt: new Date().toISOString() });
      setStatusText("Control loop detection failed.");
    } finally {
      setIsControlLoopsLoading(false);
    }
  }, [refreshControlLoops, selectedProjectId]);

  const withDerivedPipelineStatuses = (statuses: PipelineStageStatusMap): PipelineStageStatusMap => {
    const nextStatuses = { ...statuses };
    if (nextStatuses.logic_completion === "success" && nextStatuses.plant_graph === "success") {
      nextStatuses.io_mapping = "success";
    }
    return applySnapshotTrigger(nextStatuses);
  };

  const updatePipelineStage = (stage: PipelineStageKey, state: PipelineStageStatusMap[PipelineStageKey]): void => {
    setPipelineStatuses((previous) => withDerivedPipelineStatuses({ ...previous, [stage]: state }));
  };

  const syncWorkspaceForStage = (stage: PipelineStageKey): void => {
    if (stage === "logic_completion") {
      setShowLogic(true);
      setCodePanelMode("control_logic");
      setActiveBottomView("logic");
      return;
    }
    if (stage === "st_generation") {
      setShowLogic(true);
      setCodePanelMode("generated_st");
      setActiveBottomView("logic");
      return;
    }
    if (stage === "st_verification") {
      setShowLogic(true);
      setCodePanelMode("verification");
      setActiveBottomView("logic");
      return;
    }
    if (stage === "io_mapping") {
      setMonitoringPanelMode("io_mapping");
      setActiveBottomView("monitoring");
      setActiveTab("IO Mapping");
      return;
    }
    if (stage === "runtime_validation") {
      setMonitoringPanelMode("runtime");
      setActiveBottomView("monitoring");
      setActiveTab("Diagnostics");
      return;
    }
    if (stage === "simulation_validation") {
      setActiveBottomView("simulation");
      setActiveTab("Diagnostics");
      return;
    }
    if (stage === "version_snapshot") {
      setMonitoringPanelMode("versions");
      setActiveBottomView("monitoring");
      setActiveTab("Diagnostics");
    }
  };

  useEffect(() => {
    const previous = previousPipelineStatusesRef.current;
    const toastableStages: PipelineStageKey[] = [
      "st_generation",
      "st_verification",
      "io_mapping",
      "runtime_validation",
      "simulation_validation",
      "version_snapshot",
    ];

    const hasStatusChanges = toastableStages.some((stage) => previous[stage] !== pipelineStatuses[stage]);
    if (suppressInitialPipelineWorkspaceSyncRef.current && hasStatusChanges && !loadingAction) {
      previousPipelineStatusesRef.current = pipelineStatuses;
      suppressInitialPipelineWorkspaceSyncRef.current = false;
      return;
    }

    if (!hasStatusChanges) {
      previousPipelineStatusesRef.current = pipelineStatuses;
      return;
    }

    suppressInitialPipelineWorkspaceSyncRef.current = false;

    for (const stage of toastableStages) {
      const prevState = previous[stage];
      const nextState = pipelineStatuses[stage];
      if (prevState === nextState) {
        continue;
      }

      syncWorkspaceForStage(stage);

      const toastId = `pipeline-${stage}`;
      const label = PIPELINE_STAGE_LABELS[stage];
      const customCopy = pendingPipelineToastCopyRef.current[stage];

      if (nextState === "running") {
        toast.loading(customCopy?.running ?? `${label} running...`, {
          id: toastId,
          className: "industrial-toast",
          icon: <LoaderCircle size={14} className="toast-icon" />,
        });
      } else if (nextState === "success") {
        toast.success(customCopy?.success ?? `${label} completed`, {
          id: toastId,
          className: "industrial-toast",
          icon: <CheckCircle2 size={14} className="toast-icon" />,
        });
      } else if (nextState === "failed") {
        toast.error(customCopy?.failed ?? `${label} failed`, {
          id: toastId,
          className: "industrial-toast industrial-toast-error",
          icon: <AlertTriangle size={14} className="toast-icon toast-icon-error" />,
        });
      } else if (nextState === "warning") {
        toast(customCopy?.warning ?? `${label} completed with warnings`, {
          id: toastId,
          className: "industrial-toast",
          icon: <AlertTriangle size={14} className="toast-icon" />,
        });
      } else {
        toast.dismiss(toastId);
      }

      if (customCopy) {
        delete pendingPipelineToastCopyRef.current[stage];
      }
    }

    previousPipelineStatusesRef.current = pipelineStatuses;
  }, [pipelineStatuses]);

  const disabledActions = useMemo<Partial<Record<ToolbarAction, boolean>>>(
    () => ({
      upload_documents: false,
      parse_plant_model: !selectedProjectId,
      detect_control_loops: !selectedProjectId,
      generate_logic: !selectedProjectId,
      generate_io_mapping: !selectedProjectId,
      run_simulation: !selectedProjectId,
      export_logic: !selectedProjectId,
      deploy_runtime: !selectedProjectId,
      start_monitoring: !selectedProjectId,
      analyze_fault: !selectedProjectId,
      replay_event: !selectedProjectId,
      versions: !selectedProjectId,
    }),
    [selectedProjectId]
  );

  const loadingAction = useMemo<ToolbarAction | null>(() => {
    if (isParsing) {
      return "parse_plant_model";
    }
    if (isUploading) {
      return "upload_documents";
    }
    if (pipelineStatuses.st_generation === "running" && !isExportingLogic) {
      return "generate_logic";
    }
    if (isExportingLogic) {
      return "export_logic";
    }
    if (pipelineStatuses.io_mapping === "running") {
      return "generate_io_mapping";
    }
    if (pipelineStatuses.simulation_validation === "running") {
      return "run_simulation";
    }
    if (pipelineStatuses.runtime_validation === "running") {
      return "deploy_runtime";
    }
    if (isRuntimeActionBusy) {
      return "start_monitoring";
    }
    if (isControlLoopsLoading) {
      return "detect_control_loops";
    }
    if (isFaultAnalysisLoading) {
      return "analyze_fault";
    }
    if (versioningLoading) {
      return "versions";
    }
    return null;
  }, [
    isControlLoopsLoading,
    isExportingLogic,
    isFaultAnalysisLoading,
    isParsing,
    isRuntimeActionBusy,
    isUploading,
    pipelineStatuses.io_mapping,
    pipelineStatuses.runtime_validation,
    pipelineStatuses.simulation_validation,
    pipelineStatuses.st_generation,
    versioningLoading,
  ]);

  const directPLCFeatureEnabled = useMemo<boolean>(() => {
    const flag = String(import.meta.env.VITE_DIRECT_PLC_DEPLOYMENT_ENABLED || "false").toLowerCase();
    return ["1", "true", "yes", "on"].includes(flag);
  }, []);

  const directPLCSafetyGates = useMemo(
    () => ({
      syntax_validation_passed: pipelineStatuses.st_verification === "success",
      logic_verification_passed: pipelineStatuses.logic_completion === "success",
      io_validation_passed: pipelineStatuses.io_mapping === "success",
      simulation_test_passed: pipelineStatuses.simulation_validation === "success",
    }),
    [pipelineStatuses.io_mapping, pipelineStatuses.logic_completion, pipelineStatuses.simulation_validation, pipelineStatuses.st_verification]
  );

  const directPLCCanSubmit = useMemo(
    () =>
      directPLCFeatureEnabled &&
      directPLCSafetyGates.syntax_validation_passed &&
      directPLCSafetyGates.logic_verification_passed &&
      directPLCSafetyGates.io_validation_passed &&
      directPLCSafetyGates.simulation_test_passed,
    [directPLCFeatureEnabled, directPLCSafetyGates]
  );

  const runSTVerification = async (projectId: string, options: { silent?: boolean } = {}): Promise<void> => {
    setIsVerifyingST(true);
    setSTVerificationFailedMessage(null);
    try {
      const verification = await verifySTWorkspaceWithRetry(toWorkspaceVerifyTarget(projectId), {
        maxAttempts: 3,
        initialDelayMs: 700,
        backoffFactor: 2,
      });
      setSTVerificationData(verification);

      const diagnostics: Record<string, STDiagnosticMarker[]> = {};
      const validationIssues: string[] = [];
      for (const fileResult of verification.files) {
        const normalizedFilePath = normalizeVerifierFilePath(fileResult.file);
        diagnostics[normalizedFilePath] = [
          ...fileResult.errors.map((item) => ({
            line: item.line || 1,
            column: item.column || 1,
            severity: "error" as const,
            code: item.code,
            message: item.message,
          })),
          ...fileResult.warnings.map((item) => ({
            line: item.line || 1,
            column: item.column || 1,
            severity: "warning" as const,
            code: item.code,
            message: item.message,
          })),
        ];

        for (const item of fileResult.errors) {
          const location = item.line ? `${fileResult.file}:${item.line}` : fileResult.file;
          validationIssues.push(`${location} [${item.code}] ${item.message}`);
        }
        for (const item of fileResult.warnings) {
          const location = item.line ? `${fileResult.file}:${item.line}` : fileResult.file;
          validationIssues.push(`${location} [${item.code}] ${item.message}`);
        }
      }

      setSTDiagnosticsByFile(diagnostics);
      setLogicValidationIssues(validationIssues);

      if (verification.status === "failed") {
        if (options.silent) {
          queuePipelineToastCopy("st_verification", { failed: "Saved ST verification failed during refresh" });
        }
        updatePipelineStage("st_verification", "failed");
        if (!options.silent) {
          setStatusText(`ST verification failed with ${verification.summary.error_count} error(s).`);
        }
        return;
      }

      if (verification.status === "passed_with_warnings") {
        if (options.silent) {
          queuePipelineToastCopy("st_verification", { warning: "Saved ST verification refreshed with warnings" });
        }
        updatePipelineStage("st_verification", "warning");
        if (!options.silent) {
          setStatusText(`ST verification passed with warnings (${verification.summary.warning_count}).`);
        }
        return;
      }

      if (options.silent) {
        queuePipelineToastCopy("st_verification", { success: "Saved ST verification refreshed" });
      }
      updatePipelineStage("st_verification", "success");
      if (!options.silent) {
        setStatusText("ST verification passed.");
      }
    } catch {
      if (options.silent) {
        queuePipelineToastCopy("st_verification", { failed: "Saved ST verification failed during refresh" });
      }
      updatePipelineStage("st_verification", "failed");
      setSTVerificationData(null);
      setSTDiagnosticsByFile({});
      setSTVerificationFailedMessage("ST verification endpoint failed after retries.");
      if (!options.silent) {
        setStatusText("ST verification failed. Ensure backend /verify-st endpoint is available.");
      }
    } finally {
      setIsVerifyingST(false);
    }
  };

  const refreshVersionHistory = useCallback(
    async (projectId: string | null): Promise<void> => {
      if (!projectId) {
        setVersions([]);
        setSelectedVersion(null);
        setSelectedVersionTags([]);
        setVersionDiff(null);
        return;
      }

      setVersioningLoading(true);
      setVersioningError(null);
      try {
        const history = await getVersionHistory(projectId);
        setVersions(history);
        setSelectedVersion((current) => {
          if (current && history.some((item) => item.version_tag === current.version_tag)) {
            return history.find((item) => item.version_tag === current.version_tag) || history[0] || null;
          }
          return history[0] || null;
        });
      } catch {
        setVersions([]);
        setSelectedVersion(null);
        setVersioningError("Version history could not be loaded.");
      } finally {
        setVersioningLoading(false);
      }
    },
    []
  );

  const refreshPIDChanges = useCallback(async (): Promise<void> => {
    setPIDChangesLoading(true);
    setPIDChangesError(null);
    try {
      const changes = await getPIDChanges();
      setPIDChanges(changes);
      setPIDAcceptedConflicts(false);
    } catch {
      setPIDChanges(null);
      setPIDChangesError("P&ID changes could not be loaded for the active project.");
    } finally {
      setPIDChangesLoading(false);
    }
  }, []);

  const handleVersionCreateSnapshot = useCallback(async (): Promise<void> => {
    if (!selectedProjectId) {
      return;
    }
    setVersionBusyAction("snapshot");
    try {
      await createSnapshot({
        project_id: selectedProjectId,
        trigger_source: "Manual Snapshot",
        summary: "Manual snapshot requested from Versions workspace.",
      });
      toast.success("Snapshot created", { className: "industrial-toast" });
      await refreshVersionHistory(selectedProjectId);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Snapshot creation failed.";
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setVersionBusyAction(null);
    }
  }, [refreshVersionHistory, selectedProjectId]);

  const handleVersionLoadSnapshot = useCallback(async (version: VersionRecord): Promise<void> => {
    if (!selectedProjectId) {
      return;
    }
    try {
      const loaded = await getVersionById(selectedProjectId, version.version_tag);
      setSelectedVersion(loaded);
      setMonitoringPanelMode("versions");
      setActiveBottomView("monitoring");
      setStatusText(`Loaded snapshot metadata ${loaded.version_tag}.`);
      toast.success(`Loaded ${loaded.version_tag}`, { className: "industrial-toast" });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Load snapshot failed.";
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    }
  }, [selectedProjectId]);

  const handleVersionRollback = useCallback(async (version: VersionRecord): Promise<void> => {
    if (!selectedProjectId) {
      return;
    }
    if (!version.rollback_available) {
      return;
    }

    const confirmed = window.confirm(`Rollback project to ${version.version_tag}? This creates a new rollback commit event.`);
    if (!confirmed) {
      return;
    }

    setVersionBusyAction("rollback");
    try {
      await rollbackVersion({ project_id: selectedProjectId, version_tag: version.version_tag });
      toast.success(`Rollback completed: ${version.version_tag}`, { className: "industrial-toast" });
      await refreshVersionHistory(selectedProjectId);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Rollback failed.";
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setVersionBusyAction(null);
    }
  }, [refreshVersionHistory, selectedProjectId]);

  const handleVersionCompare = useCallback(async (): Promise<void> => {
    if (!selectedProjectId) {
      return;
    }
    if (selectedVersionTags.length !== 2) {
      toast("Select exactly 2 versions to compare.", { className: "industrial-toast" });
      return;
    }

    const [versionA, versionB] = selectedVersionTags;
    setVersionBusyAction("compare");
    try {
      const diff = await diffVersions(selectedProjectId, versionA, versionB);
      setVersionDiff(diff);
      setCodePanelMode("version_diff");
      setActiveBottomView("logic");
      toast.success(`Compared ${versionA} vs ${versionB}`, { className: "industrial-toast" });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Version compare failed.";
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setVersionBusyAction(null);
    }
  }, [selectedProjectId, selectedVersionTags]);

  const handleVersionExport = useCallback(async (version: VersionRecord): Promise<void> => {
    if (!selectedProjectId) {
      return;
    }
    setVersionBusyAction("export");
    try {
      const blob = await exportVersion(selectedProjectId, version.version_tag);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${selectedProjectId}_${version.version_tag}_metadata.json`;
      anchor.click();
      URL.revokeObjectURL(url);
      toast.success(`Exported ${version.version_tag}`, { className: "industrial-toast" });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Export failed.";
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setVersionBusyAction(null);
    }
  }, [selectedProjectId]);

  const handleVersionToggleCompareSelection = useCallback((versionTag: string): void => {
    setSelectedVersionTags((current) => {
      const has = current.includes(versionTag);
      if (has) {
        return current.filter((item) => item !== versionTag);
      }
      if (current.length >= 2) {
        return [current[1], versionTag];
      }
      return [...current, versionTag];
    });
  }, []);

  const selectedEquipment = useMemo<Equipment>(() => {
    const node = graphNodes.find((item) => item.id === selectedNode);
    if (!node) {
      return EMPTY_EQUIPMENT;
    }

    return {
      id: node.id,
      type: toEquipmentType(node.node_type),
      status: node.status || "unknown",
      motor: "N/A",
      signals: node.signals ?? [],
      logic: "N/A",
      processUnit: node.process_unit ?? "N/A",
      controlRole: node.control_role ?? "N/A",
      signalType: node.signal_type ?? "N/A",
      instrumentRole: node.instrument_role ?? "N/A",
      powerRating: node.power_rating ?? "N/A",
      connections: node.connected_to ?? [],
      controls: node.controls ?? [],
      measures: node.measures ?? [],
      controlPath: node.control_path ?? [],
      metadataConfidence: node.metadata_confidence ?? {},
    };
  }, [graphNodes, selectedNode]);

  const fallbackSystemContext = useMemo<SystemContext | null>(() => {
    const tag = selectedNode.trim();
    if (!tag) {
      return null;
    }

    const controlNarrativeText = [controlLogicCode, generatedLogic].filter((item) => item.trim().length > 0).join("\n");

    return buildSystemContext({
      tag,
      graphNodes,
      graphEdges: plantGraph.edges,
      narrativeText: controlNarrativeText,
      engineeringRows: engineeringTableData?.rows ?? [],
      controlLoops,
      runtimeDiagnostics,
      runtimeValidation: runtimeValidationData,
      runtimeTelemetryTags,
    });
  }, [
    selectedNode,
    controlLogicCode,
    generatedLogic,
    graphNodes,
    plantGraph.edges,
    engineeringTableData?.rows,
    controlLoops,
    runtimeDiagnostics,
    runtimeValidationData,
    runtimeTelemetryTags,
  ]);

  const fallbackBehaviorExplanation = useMemo<string>(() => {
    return fallbackSystemContext ? buildBehavior(fallbackSystemContext) : "No selected tag context.";
  }, [fallbackSystemContext]);

  const fallbackImpactSummary = useMemo<SystemImpact | null>(() => {
    return fallbackSystemContext ? buildImpact(fallbackSystemContext) : null;
  }, [fallbackSystemContext]);

  const selectedTagEmbeddedPayload = useMemo<Record<string, unknown> | null>(() => {
    const tag = selectedNode.trim();
    if (!tag) {
      return null;
    }

    const graphNode = graphNodes.find((item) => toComparableToken(item.id) === toComparableToken(tag));
    const engineeringRow = (engineeringTableData?.rows || []).find((item) => toComparableToken(item.tag) === toComparableToken(tag));

    const nodeMetadata = graphNode?.metadata && typeof graphNode.metadata === "object" ? (graphNode.metadata as Record<string, unknown>) : null;
    const rowRecord = engineeringRow as unknown as Record<string, unknown> | undefined;

    const embedded =
      (rowRecord?.system_context as Record<string, unknown> | undefined) ||
      (rowRecord?.why_engine as Record<string, unknown> | undefined) ||
      (rowRecord?.behavior as Record<string, unknown> | undefined) ||
      nodeMetadata?.system_context ||
      nodeMetadata?.why_engine ||
      nodeMetadata?.behavior ||
      null;

    if (!embedded || typeof embedded !== "object") {
      return null;
    }

    return embedded as Record<string, unknown>;
  }, [selectedNode, graphNodes, engineeringTableData?.rows]);

  useEffect(() => {
    const tag = selectedNode.trim();
    if (!tag || !selectedProjectId) {
      setSelectedSystemContextPayload(null);
      setSystemContextLoading(false);
      setSystemContextError(null);
      return;
    }

    const requestId = systemContextRequestIdRef.current + 1;
    systemContextRequestIdRef.current = requestId;
    setSelectedSystemContextPayload(null);
    setSystemContextLoading(true);
    setSystemContextError(null);

    if (import.meta.env.DEV) {
      console.debug("[system-context] selectedTag", { projectId: selectedProjectId, tag });
    }

    void getSystemContextForTag(tag)
      .then((payload) => {
        if (requestId !== systemContextRequestIdRef.current) {
          return;
        }
        setSelectedSystemContextPayload(payload);
        if (import.meta.env.DEV) {
          console.debug("[system-context] fetched payload", payload);
        }
      })
      .catch((error: unknown) => {
        if (requestId !== systemContextRequestIdRef.current) {
          return;
        }
        const message = error instanceof Error ? error.message : "System context load failed.";
        setSelectedSystemContextPayload(null);
        setSystemContextError(message);
        if (import.meta.env.DEV) {
          console.debug("[system-context] fetch error", { message, error });
        }
      })
      .finally(() => {
        if (requestId === systemContextRequestIdRef.current) {
          setSystemContextLoading(false);
        }
      });
  }, [selectedNode, selectedProjectId]);

  const selectedSystemContextPanel = useMemo(() => {
    return mapSystemContextToPanelView({
      selectedTag: selectedNode,
      backendPayload: selectedSystemContextPayload || selectedTagEmbeddedPayload,
      fallbackContext: fallbackSystemContext,
      fallbackBehavior: fallbackBehaviorExplanation,
      fallbackImpact: fallbackImpactSummary,
    });
  }, [
    selectedNode,
    selectedSystemContextPayload,
    selectedTagEmbeddedPayload,
    fallbackSystemContext,
    fallbackBehaviorExplanation,
    fallbackImpactSummary,
  ]);

  useEffect(() => {
    if (import.meta.env.DEV) {
      console.debug("[system-context] mapped panel model", selectedSystemContextPanel);
      console.log("WHY DATA:", selectedSystemContextPanel.resolvedContext);
    }
  }, [selectedSystemContextPanel]);

  const selectedSystemContext = selectedSystemContextPanel.resolvedContext;
  const selectedBehaviorExplanation = selectedSystemContextPanel.behaviorText;
  const selectedImpactSummary: SystemImpact = {
    cause: selectedSystemContextPanel.cause,
    effect: selectedSystemContextPanel.effect,
    impact: selectedSystemContextPanel.impact,
  };

  const refreshSimulationTraceData = useCallback(async (projectId?: string): Promise<void> => {
    const activeProjectId = projectId || selectedProjectId;
    if (!activeProjectId) {
      setSimulationValidationData(null);
      setSimulationTrace([]);
      setSimulationIssues([]);
      setSelectedReplayTag("");
      return;
    }
    try {
      const [tracePayload, analysisPayload, monitoringSummary] = await Promise.all([
        getSimulationTrace(activeProjectId),
        getSimulationAnalysis(activeProjectId).catch(() => null),
        getMonitoring(activeProjectId).catch(() => null),
      ]);
      const traceRows = tracePayload.trace ?? [];
      const monitoringSimulation =
        monitoringSummary && typeof monitoringSummary === "object" && monitoringSummary.simulation && typeof monitoringSummary.simulation === "object"
          ? (monitoringSummary.simulation as Record<string, unknown>)
          : null;
      const issues = monitoringSimulation ? toSimulationIssueList(monitoringSimulation.issues) : analysisPayload?.issues ?? [];
      const panelData = mapSimulationMetricsToPanelData(activeProjectId, monitoringSimulation ?? { issues });

      setSimulationValidationData(panelData);
      setSimulationTrace(traceRows);
      setSimulationIssues(issues);
      if (traceRows.length === 0) {
        setSelectedReplayTag("");
      }
    } catch {
      setSimulationValidationData(null);
      setSimulationTrace([]);
      setSimulationIssues([]);
      setSelectedReplayTag("");
    }
  }, [selectedProjectId]);

  const selectedNodeIOMappingRows = useMemo<IOMappingTableRow[]>(() => {
    if (!selectedNode || ioMappingRows.length === 0) {
      return ioMappingRows;
    }

    const selectedToken = toComparableToken(selectedNode);
    if (!selectedToken) {
      return ioMappingRows;
    }

    const signalTokens = new Set<string>(
      [selectedEquipment.id, ...selectedEquipment.signals]
        .map((item) => toComparableToken(item || ""))
        .filter((item) => item.length > 0)
    );

    const filtered = ioMappingRows.filter((row) => {
      const tagToken = toComparableToken(row.tag || "");
      const equipmentToken = toComparableToken(row.equipment_id || "");

      if (equipmentToken && equipmentToken === selectedToken) {
        return true;
      }
      if (tagToken && (tagToken === selectedToken || tagToken.startsWith(selectedToken))) {
        return true;
      }
      return signalTokens.has(tagToken);
    });

    return filtered;
  }, [ioMappingRows, selectedEquipment.id, selectedEquipment.signals, selectedNode]);

  useEffect(() => {
    const initProjects = async (): Promise<void> => {
      try {
        const [projectList, activeProject] = await Promise.all([listProjects(), getActiveProject().catch(() => null)]);

        setProjects(projectList);
        if (projectList.length > 0) {
          const activeId = activeProject?.id && projectList.some((item) => item.id === activeProject.id) ? activeProject.id : projectList[0].id;
          const active = projectList.find((item) => item.id === activeId) ?? projectList[0];
          setSelectedProjectId(active.id);
          setStatusText(`Active project: ${active.name}`);
        } else {
          setSelectedProjectId("");
          setStatusText("No projects yet. Click + New to create one.");
        }
      } catch {
        setStatusText("Backend unavailable. Start FastAPI server for project-scoped mode.");
      }
    };

    void initProjects();
  }, []);

  useEffect(() => {
    if (!selectedProjectId) {
      setPlantGraph({ nodes: [], edges: [] });
      setEngineeringTableData(null);
      setEngineeringTableError(null);
      setSelectedWhyTraceTag(null);
      setUnsTableRowsOverride(null);
      setSelectedNode("");
      setControlLogicCode("");
      setGeneratedLogic("");
      setGeneratedSTFiles([]);
      setSelectedSTFilePath(null);
      setSTDiagnosticsByFile({});
      setSTJumpLocation(null);
      setLogicWarnings([]);
      setLogicValidationIssues([]);
      setSTVerificationData(null);
      setSTVerificationFailedMessage(null);
      setIsVerifyingST(false);
      setIOMappingRows([]);
      setIOMappingIssues([]);
      setSelectedIOMappingTag(null);
      setIOMappingSummary(null);
      setIOMappingFailedMessage(null);
      setIsGeneratingIOMapping(false);
      setRuntimeValidationData(null);
      setRuntimeFailedMessage(null);
      setRuntimeTelemetryTags({});
      setRuntimeForceableInputs([]);
      setForcedTagNames([]);
      setRuntimeDiagnostics(null);
      setFaultAnalysis(null);
      setFaultAnalysisTag(null);
      setFaultAnalysisInputMessage(null);
      setIsFaultAnalysisLoading(false);
      setFaultAnalysisError(null);
      setSimulationValidationData(null);
      setSimulationFailedMessage(null);
      setSimulationTrace([]);
      setSimulationIssues([]);
      setControlLoops([]);
      setIsControlLoopsLoading(false);
      setControlLoopsError(null);
      setSelectedControlLoopTag(null);
      setSelectedReplayTag("");
      setVersions([]);
      setSelectedVersion(null);
      setSelectedVersionTags([]);
      setVersionDiff(null);
      setVersioningError(null);
      setPIDChanges(null);
      setPIDChangesError(null);
      setPIDAcceptedConflicts(false);
      setSelectedSystemContextPayload(null);
      setSystemContextLoading(false);
      setSystemContextError(null);
      setPipelineStatuses(createInitialPipelineStatuses());
      setShowLogic(false);
      setUIShell((previous) => ({
        ...previous,
        activeWorkspaceModule: "plant_model",
        activeMainView: "table",
        selectedRowId: "",
        activeRightTab: "Details",
      }));
      return;
    }

    setPipelineStatuses(createInitialPipelineStatuses());
    setRuntimeValidationData(null);
    setRuntimeFailedMessage(null);
    setSelectedWhyTraceTag(null);
    setUnsTableRowsOverride(null);
    setRuntimeTelemetryTags({});
    setRuntimeForceableInputs([]);
    setForcedTagNames([]);
    setRuntimeDiagnostics(null);

    const loadPersistedRuntimeState = async (): Promise<void> => {
      // Runtime panel React state is transient UI state; durable engineering runtime state is rehydrated from backend persistence per project.
      setIsRuntimeStateLoading(true);
      setRuntimeFailedMessage(null);
      try {
        const [runtimeState, latestDeployment, tags, forcedInputs, diagnosticsPayload] = await Promise.all([
          getRuntimeState(selectedProjectId),
          getLatestRuntimeDeployment(selectedProjectId),
          getRuntimeTags().catch(() => ({} as Record<string, unknown>)),
          getRuntimeForcedInputs(selectedProjectId).catch(() => null),
          getRuntimeDiagnostics(selectedProjectId).catch(() => null),
        ]);

        const merged = {
          ...runtimeState,
          deployment: runtimeState.deployment ?? latestDeployment.deployment ?? null,
        };

        setRuntimeTelemetryTags(tags);
        setRuntimeValidationData(mapPersistedRuntimeState(merged, tags));

        if (forcedInputs) {
          setRuntimeForceableInputs(forcedInputs.input_catalog ?? []);
          setForcedTagNames((forcedInputs.forced_inputs ?? []).map((item) => item.tag));
          if (forcedInputs.diagnostics) {
            setRuntimeDiagnostics(forcedInputs.diagnostics);
          }
        }
        if (diagnosticsPayload?.diagnostics) {
          setRuntimeDiagnostics(diagnosticsPayload.diagnostics);
        }
      } catch {
        setRuntimeValidationData(null);
        setRuntimeFailedMessage("Runtime state could not be rehydrated for this project.");
      } finally {
        setIsRuntimeStateLoading(false);
      }
    };

    const loadGraph = async (): Promise<void> => {
      try {
        const graph = await getGraph(selectedProjectId);
        setPlantGraph({ nodes: graph.nodes, edges: graph.edges });
        setSelectedNode(graph.nodes[0]?.id ?? "");
        if (graph.nodes.length > 0 || graph.edges.length > 0) {
          updatePipelineStage("plant_graph", "success");
        }
      } catch {
        setStatusText("Graph endpoint unavailable for selected project.");
      }
    };

    const loadEngineeringTable = async (): Promise<void> => {
      setEngineeringTableLoading(true);
      setEngineeringTableError(null);
      try {
        const data = await getEngineeringTable({
          project_id: selectedProjectId,
          include_inferred: true,
          max_flow_depth: 4,
        });
        setEngineeringTableData((previous) => mergeEngineeringTableData(previous, data));
      } catch {
        setEngineeringTableError("Engineering table endpoint unavailable for selected project.");
      } finally {
        setEngineeringTableLoading(false);
      }
    };

    const loadLatestIOMapping = async (): Promise<void> => {
      try {
        const mapping = await getLatestIOMapping(selectedProjectId);
        setIOMappingRows(mapping.rows);
        setIOMappingIssues(mapping.issues ?? []);
        setSelectedIOMappingTag(null);
        setIOMappingSummary(mapping.summary);
        setIOMappingFailedMessage(null);
        if (mapping.rows.length > 0) {
          queuePipelineToastCopy("io_mapping", { success: "Saved IO mapping loaded" });
          updatePipelineStage("io_mapping", "success");
        }
      } catch {
        setIOMappingRows([]);
        setIOMappingIssues([]);
        setSelectedIOMappingTag(null);
        setIOMappingSummary(null);
      }
    };

    void loadGraph();
    void loadEngineeringTable();
    void loadLatestIOMapping();
    void refreshSimulationTraceData(selectedProjectId);
    void refreshControlLoops(selectedProjectId);
    void loadPersistedRuntimeState();
    void refreshProjectDocuments(selectedProjectId);
    void refreshVersionHistory(selectedProjectId);
    void refreshPIDChanges();
  }, [refreshControlLoops, refreshPIDChanges, refreshProjectDocuments, refreshSimulationTraceData, refreshVersionHistory, selectedProjectId]);

  useEffect(() => {
    if (!selectedProjectId || (activeTab !== "Replay" && activeTab !== "Diagnostics")) {
      return;
    }
    void refreshSimulationTraceData(selectedProjectId);
  }, [activeTab, refreshSimulationTraceData, selectedProjectId]);

  useEffect(() => {
    if (!selectedProjectId) {
      behaviorHydrationSignatureRef.current = "";
      return;
    }

    const rows = engineeringTableData?.rows ?? [];
    if (rows.length === 0) {
      return;
    }

    const signature = `${selectedProjectId}:${rows.length}:${plantGraph.edges.length}`;
    if (behaviorHydrationSignatureRef.current === signature) {
      return;
    }
    behaviorHydrationSignatureRef.current = signature;

    let cancelled = false;
    void (async () => {
      try {
        await loadDeterministicBehaviorCache({
          rows,
          edges: plantGraph.edges,
        });
        if (!cancelled) {
          setBehaviorRefreshKey((value) => value + 1);
        }
      } catch {
        if (!cancelled) {
          setStatusText("Deterministic behavior cache hydration failed for this project.");
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [selectedProjectId, engineeringTableData, plantGraph.edges]);

  useEffect(() => {
    if (simulationTrace.length === 0) {
      setSelectedReplayTag("");
      return;
    }

    const candidates = [selectedNode, ...(selectedEquipment.signals ?? [])].filter((item) => Boolean(item));
    for (const candidate of candidates) {
      const resolved = resolveTraceTag(candidate, simulationTrace);
      if (resolved) {
        setSelectedReplayTag((current) => (current === resolved ? current : resolved));
        return;
      }
    }

    if (!selectedReplayTag || !simulationTrace.some((row) => row.tag === selectedReplayTag)) {
      setSelectedReplayTag(simulationTrace[0]?.tag || "");
    }
  }, [selectedNode, selectedEquipment.signals, simulationTrace, selectedReplayTag]);

  useEffect(() => {
    if (!selectedProjectId) {
      return;
    }

    const loadLatestLogic = async (): Promise<void> => {
      try {
        const artifact = await getLogic(selectedProjectId);
        const code = (artifact.code || artifact.st_preview || "").trim();
        const validationIssues = (artifact.st_validation?.issues ?? []).map((issue) => {
          const location = issue.line ? `${issue.file}:${issue.line}` : issue.file;
          return `${location} [${issue.rule}] ${issue.message}`;
        });
        setLogicWarnings(artifact.warnings ?? []);
        setLogicValidationIssues(validationIssues);
        if (code.length > 0) {
          setControlLogicCode(code);
          setGeneratedLogic(code);
          const files = parseGeneratedLogicFiles(code);
          setGeneratedSTFiles(files);
          const mainFile = files.find((item) => item.path.toLowerCase() === "main.st");
          setSelectedSTFilePath((current) => current || mainFile?.path || files[0]?.path || null);
          setShowLogic(true);
          queuePipelineToastCopy("st_generation", { success: "Saved logic loaded" });
          queuePipelineToastCopy("st_verification", { running: "Refreshing saved ST verification..." });
          setPipelineStatuses((previous) =>
            withDerivedPipelineStatuses({
              ...previous,
              logic_completion: "success",
              st_generation: "success",
              st_verification: "running",
            })
          );
          await runSTVerification(selectedProjectId, { silent: true });
        } else {
          setControlLogicCode("");
          setGeneratedLogic("");
          setGeneratedSTFiles([]);
          setSelectedSTFilePath(null);
          setSTDiagnosticsByFile({});
          setSTJumpLocation(null);
          setLogicWarnings([]);
          setLogicValidationIssues([]);
          setSTVerificationData(null);
          setSTVerificationFailedMessage(null);
          setShowLogic(false);
        }
      } catch {
        setControlLogicCode("");
        setGeneratedLogic("");
        setGeneratedSTFiles([]);
        setSelectedSTFilePath(null);
        setSTDiagnosticsByFile({});
        setSTJumpLocation(null);
        setLogicWarnings([]);
        setLogicValidationIssues([]);
        setSTVerificationData(null);
        setSTVerificationFailedMessage(null);
        setShowLogic(false);
      }
    };

    void loadLatestLogic();
  }, [selectedProjectId]);

  const handleToolbarAction = async (action: ToolbarAction): Promise<void> => {
    setActiveAction(action);

    if (action === "upload_documents") {
      if (!selectedProjectId) {
        setStatusText("Select or create a project first.");
        toast.error("No active project selected", {
          className: "industrial-toast industrial-toast-error",
          icon: <AlertTriangle size={14} className="toast-icon toast-icon-error" />,
        });
        return;
      }
      uploadInputRef.current?.click();
      setStatusText("Select one or more project documents to upload.");
      setModuleState("documents", { state: "running", message: "Awaiting file selection", updatedAt: new Date().toISOString() });
      return;
    }

    if (!selectedProjectId) {
      setStatusText("Select or create a project first.");
      toast.error("Select a project before running actions", {
        className: "industrial-toast industrial-toast-error",
        icon: <AlertTriangle size={14} className="toast-icon toast-icon-error" />,
      });
      return;
    }

    try {
      if (action === "parse_plant_model") {
        setIsParsing(true);
        setModuleState("plant_model", { state: "running", message: "Parsing plant model", updatedAt: new Date().toISOString() });
        setStatusText("Parsing plant model...");
        await parseProject(selectedProjectId);

        try {
          const graph = await getGraph(selectedProjectId);
          setPlantGraph({ nodes: graph.nodes, edges: graph.edges });
          setSelectedNode(graph.nodes[0]?.id ?? "");
          if (graph.nodes.length > 0 || graph.edges.length > 0) {
            updatePipelineStage("plant_graph", "success");
          }
        } catch {
          setStatusText("Parse completed, but graph reload failed. Try refreshing the project view.");
        }

        setModuleState("plant_model", { state: "success", message: "Plant model parsed", updatedAt: new Date().toISOString() });
        setStatusText("Plant model parse complete.");
        await refreshVersionHistory(selectedProjectId);
        toast.success("Parse batch completed", {
          className: "industrial-toast",
          icon: <Cpu size={14} className="toast-icon" />,
        });
        setIsParsing(false);
      }

      if (action === "detect_control_loops") {
        await runControlLoopDetection();
      }

      if (action === "generate_logic") {
        setModuleState("control_logic", { state: "running", message: "Generating control logic", updatedAt: new Date().toISOString() });
        updatePipelineStage("st_generation", "running");
        setStatusText("Generating logic...");
        try {
          const artifact = await generateLogic(selectedProjectId);
          const generatedCode = artifact.code || artifact.st_preview || "";
          const hasGeneratedCode = generatedCode.trim().length > 0;
          setSTDiagnosticsByFile({});
          setSTJumpLocation(null);
          setGeneratedLogic(generatedCode);
          const files = parseGeneratedLogicFiles(generatedCode);
          setGeneratedSTFiles(files);
          const mainFile = files.find((item) => item.path.toLowerCase() === "main.st");
          setSelectedSTFilePath((current) => current || mainFile?.path || files[0]?.path || null);
          const validationIssues = (artifact.st_validation?.issues ?? []).map((issue) => {
            const location = issue.line ? `${issue.file}:${issue.line}` : issue.file;
            return `${location} [${issue.rule}] ${issue.message}`;
          });
          setLogicWarnings(artifact.warnings ?? []);
          setLogicValidationIssues(validationIssues);
          updatePipelineStage("logic_completion", "success");
          updatePipelineStage("st_generation", hasGeneratedCode ? "success" : "failed");
          setModuleState("control_logic", {
            state: hasGeneratedCode ? "success" : "failed",
            message: hasGeneratedCode ? "Logic generated" : "No logic returned",
            updatedAt: new Date().toISOString(),
          });
          if (!hasGeneratedCode) {
            setSTVerificationData(null);
            setSTDiagnosticsByFile({});
            setSTVerificationFailedMessage("No generated ST files available for verification.");
          }
          setShowLogic(true);
          setCodePanelMode("generated_st");
          setActiveBottomView("logic");
          await refreshVersionHistory(selectedProjectId);
          if (hasGeneratedCode) {
            setStatusText("ST code generated. Review files in Generated ST panel.");
          } else {
            setStatusText("ST generation failed. No generated ST files returned.");
          }
        } catch {
          updatePipelineStage("st_generation", "failed");
          setModuleState("control_logic", { state: "failed", message: "Logic generation failed", updatedAt: new Date().toISOString() });
          throw new Error("ST generation failed");
        }
      }

      if (action === "generate_io_mapping") {
        setIsGeneratingIOMapping(true);
        setIOMappingFailedMessage(null);
        setModuleState("io_mapping", { state: "running", message: "Generating IO mapping", updatedAt: new Date().toISOString() });
        updatePipelineStage("io_mapping", "running");
        setStatusText("Generating IO mapping...");
        try {
          const mappingResult = await generateIOMapping(selectedProjectId);
          setIOMappingRows(mappingResult.rows);
          setIOMappingIssues(mappingResult.issues ?? []);
          setSelectedIOMappingTag(null);
          setIOMappingSummary(mappingResult.summary);
          setMonitoringPanelMode("io_mapping");
          setActiveBottomView("monitoring");
          setActiveModule("io_mapping");
          updatePipelineStage("io_mapping", "success");
          setModuleState("io_mapping", { state: "success", message: `Mapped ${mappingResult.total} channels`, updatedAt: new Date().toISOString() });
          setStatusText(`IO mapping generated (${mappingResult.total} channel mappings).`);
          await refreshVersionHistory(selectedProjectId);
        } catch {
          updatePipelineStage("io_mapping", "failed");
          setIOMappingRows([]);
          setIOMappingIssues([]);
          setSelectedIOMappingTag(null);
          setIOMappingSummary(null);
          setIOMappingFailedMessage("IO mapping generation failed after retries.");
          setModuleState("io_mapping", { state: "failed", message: "IO mapping generation failed", updatedAt: new Date().toISOString() });
          setStatusText("IO mapping generation failed. Ensure backend endpoint is available.");
        } finally {
          setIsGeneratingIOMapping(false);
        }
      }

      if (action === "run_simulation") {
        updatePipelineStage("simulation_validation", "running");
        setModuleState("simulation", { state: "running", message: "Running simulation", updatedAt: new Date().toISOString() });
        setActiveMainView("simulation");
        setActiveBottomView("simulation");
        setActiveTab("Replay");
        setStatusText("Running simulation...");
        try {
          await runSimulation(selectedProjectId);
          const analysis = await getSimulationAnalysis(selectedProjectId);
          await refreshSimulationTraceData(selectedProjectId);
          const hasIssues = (analysis.issues ?? []).length > 0;
          updatePipelineStage("simulation_validation", hasIssues ? "warning" : "success");
          setModuleState("simulation", {
            state: hasIssues ? "failed" : "success",
            message: hasIssues ? "Simulation completed with issues" : "Simulation completed",
            updatedAt: new Date().toISOString(),
          });
          setStatusText(hasIssues ? "Simulation completed with issues. Review diagnostics." : "Simulation completed.");
        } catch {
          updatePipelineStage("simulation_validation", "failed");
          setModuleState("simulation", { state: "failed", message: "Simulation failed", updatedAt: new Date().toISOString() });
          setStatusText("Simulation failed.");
        }
      }

      if (action === "versions") {
        setActiveProjectFeature("versions");
        setMonitoringPanelMode("versions");
        setActiveBottomView("monitoring");
        setActiveModule("monitoring");
        setActiveMainView("monitoring");
        await refreshVersionHistory(selectedProjectId);
        setStatusText("Versions workspace opened.");
      }

      if (action === "export_logic") {
        setShowExportDialog(true);
        setExportResult(null);
        setExportReadiness(null);
        setExportReadinessLoading(false);
        setExportReadinessError(null);
        setExportDeploymentLogs([]);
        setExportDeploymentErrors([]);
        setExportDeploymentBusy(false);
        setExportDeploymentAction(null);
        setExportDeploymentState("not_ready");
        setExportDeploymentMessage("Validating export readiness...");
        setExportSourceMode(selectedVersion ? "version" : "live");
        setExportSourceVersionTag(selectedVersion?.version_tag ?? versions[0]?.version_tag ?? null);
        setStatusText("Select PLC vendor target to export active project logic.");
      }

      if (action === "deploy_runtime") {
        setShowDirectPLCDeployDialog(true);
        setDirectDeployResult("");
        setStatusText("Configure Deploy PLC request and pass all safety gates before submitting.");
      }

      if (action === "start_monitoring") {
        setModuleState("monitoring", { state: "running", message: "Starting monitoring", updatedAt: new Date().toISOString() });
        const monitoringSummary = await getMonitoring(selectedProjectId);
        setModuleState("monitoring", { state: "success", message: "Monitoring started", updatedAt: new Date().toISOString() });
        setActiveModule("monitoring");
        setMonitoringPanelMode("runtime");
        setActiveBottomView("monitoring");
        setStatusText(`Monitoring started (${Object.keys(monitoringSummary).length} signals summarized).`);
      }

      if (action === "analyze_fault") {
        const selectedTag = (selectedNode || selectedReplayTag || "").trim();
        const activeAlarms = Object.entries(runtimeDiagnostics?.alarms || {})
          .filter(([, active]) => Boolean(active))
          .map(([alarm]) => alarm)
          .filter((alarm) => Boolean((alarm || "").trim()));
        const recentChangedAlarm = [...(runtimeDiagnostics?.changed_alarms || [])]
          .reverse()
          .find((item) => Boolean((item?.tag || "").trim()));
        const mostRecentAlarmTag = (recentChangedAlarm?.tag || activeAlarms[0] || "").trim();

        let resolvedTag = "";
        let contextMessage = "";

        if (selectedTag) {
          resolvedTag = selectedTag;
          contextMessage = `Analyzing fault for ${resolvedTag}`;
        } else if (mostRecentAlarmTag) {
          resolvedTag = mostRecentAlarmTag;
          contextMessage = `No alarm selected. Analyzing most recent alarm: ${resolvedTag}`;
        }

        if (!resolvedTag) {
          setFaultAnalysis(null);
          setFaultAnalysisTag(null);
          setFaultAnalysisInputMessage(null);
          setFaultAnalysisError("No alarm tag available. Select a signal or ensure an active alarm exists.");
          setStatusText("Analyze Fault requires an alarm tag context.");
          return;
        }

        setIsFaultAnalysisLoading(true);
        setFaultAnalysisError(null);
        setFaultAnalysisTag(resolvedTag);
        setFaultAnalysisInputMessage(contextMessage);
        setModuleState("diagnostics", { state: "running", message: "Analyzing runtime faults", updatedAt: new Date().toISOString() });
        setStatusText(contextMessage);
        const analysis = await analyzeFault(resolvedTag, selectedProjectId, resolvedTag);
        setFaultAnalysis(analysis);
        setFaultAnalysisTag(analysis.alarm || resolvedTag);
        setTracePath(analysis.path || []);
        setSelectedNode(analysis.path?.[0] || selectedNode);
        setModuleState("diagnostics", { state: "success", message: "Fault analysis complete", updatedAt: new Date().toISOString() });
        setActiveModule("diagnostics");
        setActiveTab("Diagnostics");
        setStatusText(`Fault analysis complete for ${analysis.alarm || resolvedTag}.`);
        setIsFaultAnalysisLoading(false);
      }

      if (action === "replay_event") {
        setIsExportingLogic(true);
        setModuleState("simulation", { state: "running", message: "Loading replay event", updatedAt: new Date().toISOString() });
        const replay = await getReplay(selectedProjectId);
        setModuleState("simulation", { state: "success", message: "Replay data refreshed", updatedAt: new Date().toISOString() });
        setActiveModule("simulation");
        setActiveTab("Replay");
        setActiveMainView("graph");
        setStatusText(`Replay event loaded (${Object.keys(replay).length} fields).`);
        setIsExportingLogic(false);
      }

    } catch {
      const actionToModule: Partial<Record<ToolbarAction, WorkspaceModuleId>> = {
        parse_plant_model: "plant_model",
        detect_control_loops: "control_loops",
        generate_logic: "control_logic",
        generate_io_mapping: "io_mapping",
        run_simulation: "simulation",
        export_logic: "control_logic",
        deploy_runtime: "runtime",
        start_monitoring: "monitoring",
        analyze_fault: "diagnostics",
        replay_event: "simulation",
        versions: "monitoring",
      };
      const targetModule = actionToModule[action];
      if (targetModule) {
        setModuleState(targetModule, { state: "failed", message: `Action failed: ${action}`, updatedAt: new Date().toISOString() });
      }
      if (action === "analyze_fault") {
        setFaultAnalysis(null);
        setFaultAnalysisError("Fault analysis failed.");
        setIsFaultAnalysisLoading(false);
      }
      if (action === "detect_control_loops") {
        setControlLoopsError("Control loop detection failed.");
        setIsControlLoopsLoading(false);
      }
      setStatusText(`Action failed: ${action}. Ensure backend API is running.`);
      toast.error(`Action failed: ${action}`, {
        className: "industrial-toast industrial-toast-error",
        icon: <AlertTriangle size={14} className="toast-icon toast-icon-error" />,
      });
      if (action === "parse_plant_model") {
        setIsParsing(false);
      }
      if (action === "replay_event") {
        setIsExportingLogic(false);
      }
    }
  };

  const refreshExportReadiness = useCallback(async (): Promise<void> => {
    const requestId = exportReadinessRequestIdRef.current + 1;
    exportReadinessRequestIdRef.current = requestId;

    if (!selectedProjectId) {
      setExportReadiness(null);
      setExportReadinessLoading(false);
      setExportReadinessError("Select a project to validate export readiness.");
      setExportDeploymentState("not_ready");
      setExportDeploymentMessage("Export package not prepared.");
      setExportDeploymentBusy(false);
      setExportDeploymentAction(null);
      console.info("[export.modal] readiness_state", {
        requestId,
        exportAllowed: false,
        exportBlocked: true,
        deploymentReadiness: "not_ready",
        blockerReasons: ["Select a project to validate export readiness."],
      });
      return;
    }

    const sourceVersion =
      exportSourceMode === "version"
        ? exportSourceVersionTag ?? selectedVersion?.version_tag ?? versions[0]?.version_tag ?? null
        : null;

    setExportReadinessLoading(true);
    setExportReadinessError(null);
    setExportDeploymentErrors([]);
    setExportDeploymentLogs([]);
    setExportDeploymentBusy(false);
    setExportDeploymentAction(null);
    setExportDeploymentMessage("Validating export readiness...");
    try {
      const readiness = await getPLCExportReadiness({
        project_id: selectedProjectId,
        vendor: exportVendor,
        source_mode: exportSourceMode,
        source_version_id: sourceVersion,
      });
      if (requestId !== exportReadinessRequestIdRef.current) {
        console.info("[export.modal] readiness_state", {
          requestId,
          ignored: true,
          reason: "stale_refresh_response",
        });
        return;
      }

      const blockerReasons = readiness.checks.filter((item) => !item.ready && item.level === "error").map((item) => item.message);
      const deploymentReadinessState = readiness.deploy_allowed ? "ready_to_deploy" : "not_ready";
      setExportReadiness(readiness);
      setExportDeploymentState(deploymentReadinessState);
      setExportDeploymentMessage(
        readiness.deploy_allowed
          ? "Deployment readiness passed."
          : "Deployment checks loaded."
      );
      console.info("[export.modal] readiness_state", {
        requestId,
        exportAllowed: readiness.export_allowed,
        deployAllowed: readiness.deploy_allowed,
        exportBlocked: readiness.export_blocked,
        deploymentReadiness: deploymentReadinessState,
        sourceMode: readiness.source_mode,
        sourceVersionId: readiness.source_version_id,
        unresolvedPhysicalTags: readiness.unresolved_physical_io_tags?.length ?? 0,
        unresolvedInternalTags: readiness.unresolved_internal_tags?.length ?? 0,
        exportAllowedReason: readiness.export_allowed ? "Core export prerequisites satisfied" : readiness.export_blockers?.join("; "),
        deployBlockedReason: readiness.deploy_allowed ? "none" : readiness.deploy_blockers?.join("; "),
        blockerReasons,
      });
    } catch (error) {
      if (requestId !== exportReadinessRequestIdRef.current) {
        console.info("[export.modal] readiness_state", {
          requestId,
          ignored: true,
          reason: "stale_refresh_error",
        });
        return;
      }

      const message = error instanceof Error ? error.message : "Export readiness check failed";
      setExportReadiness(null);
      setExportReadinessError(message);
      setExportDeploymentState("not_ready");
      setExportDeploymentMessage("Readiness validation failed.");
      console.info("[export.modal] readiness_state", {
        requestId,
        exportAllowed: false,
        deployAllowed: false,
        exportBlocked: true,
        deploymentReadiness: "not_ready",
        blockerReasons: [message],
      });
    } finally {
      if (requestId === exportReadinessRequestIdRef.current) {
        setExportReadinessLoading(false);
      }
    }
  }, [exportSourceMode, exportSourceVersionTag, exportVendor, selectedProjectId, selectedVersion?.version_tag, versions]);

  const exportReadinessSections = useMemo<{
    blockingPhysical: string[];
    autoResolvedDerived: string[];
    internalNonBlocking: string[];
    unknownUnclassified: string[];
  }>(() => {
    if (!exportReadiness) {
      return {
        blockingPhysical: [],
        autoResolvedDerived: [],
        internalNonBlocking: [],
        unknownUnclassified: [],
      };
    }

    const checksByKey = new Map(exportReadiness.checks.map((check) => [check.key, check]));
    return {
      blockingPhysical: Array.from(new Set([...(exportReadiness.deploy_blockers ?? [])])).filter((item): item is string => Boolean(item)),
      autoResolvedDerived: ["derived_auto_resolved"]
        .map((key) => checksByKey.get(key)?.message)
        .filter((item): item is string => Boolean(item)),
      internalNonBlocking: ["mapping_warnings_non_physical", "internal_control_non_blocking"]
        .map((key) => checksByKey.get(key)?.message)
        .filter((item): item is string => Boolean(item)),
      unknownUnclassified: ["unknown_unclassified"]
        .map((key) => checksByKey.get(key)?.message)
        .filter((item): item is string => Boolean(item)),
    };
  }, [exportReadiness]);

  const readinessWarningMessages = useMemo<string[]>(() => {
    if (!exportReadiness) {
      return [];
    }
    const combined = [
      ...(exportReadiness.warnings ?? []),
      ...(exportReadiness.deploy_blockers ?? []),
      ...(exportReadiness.unresolved_physical_io_tags ?? []).map((tag) => `Unresolved physical IO: ${tag}`),
      ...(exportReadiness.unresolved_internal_tags ?? []).map((tag) => `Unresolved internal tag: ${tag}`),
    ];
    return Array.from(new Set(combined)).filter(Boolean);
  }, [exportReadiness]);

  const exportSourceSelectionBlocked = exportSourceMode === "version" && !exportSourceVersionTag;

  const generateExportDisabledReason = useMemo<string | null>(() => {
    if (isExportingLogic) {
      return "Export generation in progress.";
    }
    if (exportSourceSelectionBlocked) {
      return "Select a saved version before exporting.";
    }
    if (!selectedProjectId) {
      return "Select a project to generate export.";
    }
    return null;
  }, [exportSourceSelectionBlocked, isExportingLogic, selectedProjectId]);

  const prepareHandoffDisabledReason = useMemo<string | null>(() => {
    if (exportDeploymentBusy) {
      return "Deployment action in progress.";
    }
    if (!selectedProjectId) {
      return "Select a project before preparing handoff.";
    }
    if (!exportResult) {
      return "Generate export package first.";
    }
    if (!deploymentTargetRuntime.trim()) {
      return "Select target runtime before handoff.";
    }
    return null;
  }, [
    deploymentTargetRuntime,
    exportDeploymentBusy,
    exportResult,
    selectedProjectId,
  ]);

  const triggerRuntimeDeployDisabledReason = useMemo<string | null>(() => {
    if (exportDeploymentBusy) {
      return "Deployment action in progress.";
    }
    if (!selectedProjectId) {
      return "Select a project before runtime deploy.";
    }
    if (!exportResult) {
      return "Generate export package first.";
    }
    if (!deploymentTargetRuntime.trim()) {
      return "Select target runtime before deploy.";
    }
    if (exportDeploymentState === "deployment_in_progress") {
      return "Runtime deployment already in progress.";
    }
    return null;
  }, [
    deploymentTargetRuntime,
    exportDeploymentBusy,
    exportDeploymentState,
    exportResult,
    selectedProjectId,
  ]);

  const deploymentActionBlockers = useMemo<string[]>(() => {
    return readinessWarningMessages;
  }, [
    readinessWarningMessages,
  ]);

  const canGenerateExport = !generateExportDisabledReason;
  const canPrepareHandoff = !prepareHandoffDisabledReason;
  const canTriggerRuntimeDeploy = !triggerRuntimeDeployDisabledReason;

  useEffect(() => {
    if (!showExportDialog) {
      return;
    }
    console.info("[export.modal] deployment_state", {
      deploymentState: exportDeploymentState,
      deploymentMessage: exportDeploymentMessage,
      exportReadinessState: exportReadiness?.export_allowed ? "allowed" : "blocked",
      deployReadinessState: exportReadiness?.deploy_allowed ? "allowed" : "blocked",
      deploymentReadinessState: exportDeploymentState,
      blockerReasons: deploymentActionBlockers,
      generateExportDisabledReason,
      prepareHandoffDisabledReason,
      triggerRuntimeDeployDisabledReason,
      canGenerateExport,
      canPrepareHandoff,
      canTriggerRuntimeDeploy,
      isReadinessLoading: exportReadinessLoading,
      isDeploymentBusy: exportDeploymentBusy,
    });
  }, [
    exportReadiness,
    canGenerateExport,
    canPrepareHandoff,
    canTriggerRuntimeDeploy,
    deploymentActionBlockers,
    exportDeploymentBusy,
    exportDeploymentMessage,
    exportDeploymentState,
    exportReadinessLoading,
    generateExportDisabledReason,
    prepareHandoffDisabledReason,
    showExportDialog,
    triggerRuntimeDeployDisabledReason,
  ]);

  useEffect(() => {
    if (!showExportDialog) {
      return;
    }
    void refreshExportReadiness();
  }, [refreshExportReadiness, showExportDialog]);

  const handleGeneratePLCExport = async (): Promise<void> => {
    if (!selectedProjectId) {
      return;
    }
    if (!selectedProjectId) {
      toast.error("Select a project before generating export.", { className: "industrial-toast industrial-toast-error" });
      return;
    }

    const sourceVersion =
      exportSourceMode === "version"
        ? exportSourceVersionTag ?? selectedVersion?.version_tag ?? versions[0]?.version_tag ?? null
        : null;

    setIsExportingLogic(true);
    setExportResult(null);
    try {
      const result = await createPLCExport(selectedProjectId, exportVendor, {
        source_mode: exportSourceMode,
        source_version_id: sourceVersion,
      });
      setExportResult(result);
      setStatusText(`Export created for ${result.project_name} (${result.vendor}).`);
      const deployAllowedAfterExport = Boolean(exportReadiness?.deploy_allowed);
      setExportDeploymentState(deployAllowedAfterExport ? "ready_to_deploy" : "not_ready");
      setExportDeploymentMessage(
        deployAllowedAfterExport
          ? "Export package ready for deployment handoff."
          : "Export package ready for testing workflow."
      );
      setExportDeploymentLogs([]);
      setExportDeploymentErrors([]);
      toast.success(`Export ready: ${result.vendor}`, { className: "industrial-toast" });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Export failed";
      setStatusText("PLC export generation failed.");
      setExportDeploymentState("failed");
      setExportDeploymentMessage("Export generation failed.");
      setExportDeploymentErrors([message]);
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setIsExportingLogic(false);
    }
  };

  const executeExportDeploymentHandoff = async (triggerRuntimeDeploy: boolean): Promise<void> => {
    if (!selectedProjectId || !exportResult) {
      return;
    }

    setExportDeploymentBusy(true);
    setExportDeploymentAction(triggerRuntimeDeploy ? "deploy" : "prepare");
    setExportDeploymentState(triggerRuntimeDeploy ? "deployment_in_progress" : exportDeploymentState);
    try {
      const response = await handoffPLCExportForDeployment({
        project_id: selectedProjectId,
        export_id: exportResult.export_id,
        target_runtime: deploymentTargetRuntime,
        runtime_config: {
          source_mode: exportResult.source_mode ?? "live",
          source_version_id: exportResult.source_version_id ?? null,
          export_vendor: exportResult.vendor,
        },
        trigger_runtime_deploy: triggerRuntimeDeploy,
      });
      setExportDeploymentState(response.state);
      setExportDeploymentMessage(response.message);
      setExportDeploymentLogs(response.logs ?? []);
      setExportDeploymentErrors(response.errors ?? []);
      console.info("[export.modal] deployment_state", {
        triggerRuntimeDeploy,
        responseState: response.state,
        blockerReasons: response.errors ?? [],
      });
      if (response.state === "deployed") {
        toast.success("Runtime deployment completed from export package.", { className: "industrial-toast" });
      } else if (response.state === "ready_to_deploy") {
        toast.success("Export package handed off for deployment.", { className: "industrial-toast" });
      } else if (response.state === "not_ready") {
        toast("Deployment handoff is not ready.", { className: "industrial-toast" });
      } else if (response.state === "failed") {
        toast.error("Deployment handoff failed.", { className: "industrial-toast industrial-toast-error" });
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Deployment handoff failed";
      setExportDeploymentState("failed");
      setExportDeploymentMessage("Deployment handoff failed.");
      setExportDeploymentErrors([message]);
      console.info("[export.modal] deployment_state", {
        triggerRuntimeDeploy,
        responseState: "failed",
        blockerReasons: [message],
      });
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setExportDeploymentBusy(false);
      setExportDeploymentAction(null);
    }
  };

  const handleExportDeploymentHandoff = async (triggerRuntimeDeploy: boolean): Promise<void> => {
    if (!selectedProjectId || !exportResult) {
      return;
    }

    const disabledReason = triggerRuntimeDeploy ? triggerRuntimeDeployDisabledReason : prepareHandoffDisabledReason;
    if (disabledReason) {
      console.info("[export.modal] deploy_action_blocked", {
        triggerRuntimeDeploy,
        blockerReasons: [disabledReason],
        exportReadinessState: exportReadiness?.export_allowed ? "allowed" : "blocked",
        deploymentReadinessState: exportDeploymentState,
      });
      toast(disabledReason, { className: "industrial-toast" });
      return;
    }

    await executeExportDeploymentHandoff(triggerRuntimeDeploy);
  };

  const handlePIDReviewConflicts = (): void => {
    const count = pidChanges?.possible_conflicts.length ?? 0;
    setStatusText(count > 0 ? `Review ${count} possible tag conflicts before apply.` : "No conflicts detected.");
  };

  const handlePIDApplyUpdate = async (): Promise<void> => {
    setPIDApplying(true);
    try {
      await applyPIDUpdate({ allow_conflicts: pidAcceptedConflicts });
      if (selectedProjectId) {
        try {
          const graph = await getGraph(selectedProjectId);
          setPlantGraph({ nodes: graph.nodes, edges: graph.edges });
        } catch {
          // graph refresh best-effort
        }
        await refreshVersionHistory(selectedProjectId);
      }
      await refreshPIDChanges();
      setStatusText("P&ID reconciliation update applied.");
      toast.success("P&ID update applied", { className: "industrial-toast" });
    } catch (error) {
      const message = error instanceof Error ? error.message : "P&ID apply failed";
      setStatusText("P&ID reconciliation apply failed.");
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setPIDApplying(false);
    }
  };

  const handlePIDCreateSnapshot = async (): Promise<void> => {
    if (!selectedProjectId) {
      return;
    }
    setPIDCreatingSnapshot(true);
    try {
      await createSnapshot({
        project_id: selectedProjectId,
        trigger_source: "P&ID Reconciliation",
        summary: "Manual snapshot after P&ID reconciliation review.",
      });
      await refreshVersionHistory(selectedProjectId);
      toast.success("Version snapshot created", { className: "industrial-toast" });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Snapshot creation failed";
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setPIDCreatingSnapshot(false);
    }
  };

  const handleDirectPLCDeploy = async (): Promise<void> => {
    if (!selectedProjectId) {
      return;
    }

    setDirectDeployBusy(true);
    setDirectDeployResult("");
    try {
      const response = await deployDirectPLC({
        project_id: selectedProjectId,
        connection: {
          plc_address: directDeployForm.plcAddress,
          protocol: directDeployForm.protocol,
          target_runtime: directDeployForm.targetRuntime,
          io_configuration: directDeployForm.ioConfiguration,
        },
        safety: directPLCSafetyGates,
      });
      setDirectDeployResult(response.message);
      if (response.status === "accepted") {
        toast.success("Direct PLC deployment scaffold accepted", { className: "industrial-toast" });
      } else if (response.status === "blocked") {
        toast("Direct PLC deployment blocked by safety gates", { className: "industrial-toast" });
      } else {
        toast("Direct PLC deployment scaffold is disabled", { className: "industrial-toast" });
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Direct PLC deployment request failed";
      setDirectDeployResult(message);
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setDirectDeployBusy(false);
    }
  };

  const handleCreateProject = async (): Promise<void> => {
    if (!projectForm.name.trim()) {
      setStatusText("Project name is required.");
      return;
    }

    try {
      const created = await createProject({
        name: projectForm.name.trim(),
        industry: projectForm.industry.trim() || "general",
        description: projectForm.description.trim() || undefined,
        plc_runtime: projectForm.plcRuntime,
        owner: projectForm.owner.trim() || "system",
        status: projectForm.status,
        active_version: 1,
      });
      await setActiveProject(created.id);

      if (projectForm.importFiles.length > 0) {
        const inferredTypes = projectForm.importFiles.map((file) => {
          const lowered = file.name.toLowerCase();
          if (
            lowered.includes("pid") ||
            lowered.includes("p&id") ||
            lowered.includes("p_and_i") ||
            lowered.includes("p and i") ||
            lowered.includes("p_i_d") ||
            lowered.includes("p-i-d")
          ) {
            return "pid_pdf" as const;
          }
          if (lowered.includes("narrative") || lowered.includes("control")) {
            return "control_narrative" as const;
          }
          return "unknown_document" as const;
        });
        await uploadDocuments(created.id, projectForm.importFiles, inferredTypes);
        await refreshProjectDocuments(created.id);
      }

      setProjects((value) => [...value, created]);
      setSelectedProjectId(created.id);
      setActiveModule("documents");
      setActiveMainView("table");
      setShowCreateProjectModal(false);
      setProjectForm({
        name: "",
        industry: "Process Manufacturing",
        description: "",
        plcRuntime: "beremiz",
        owner: "system",
        status: "draft",
        importFiles: [],
      });
      setStatusText(`Created project: ${created.name}`);
      toast.success(`Project created: ${created.name}`, {
        className: "industrial-toast",
        icon: <FolderPlus size={14} className="toast-icon" />,
      });
    } catch {
      setStatusText("Could not create project. Check backend availability.");
      toast.error("Project creation failed", {
        className: "industrial-toast industrial-toast-error",
        icon: <AlertTriangle size={14} className="toast-icon toast-icon-error" />,
      });
    }
  };

  const handleTrace = useCallback(async (nodeId: string): Promise<void> => {
    setSelectedWhyTraceTag(null);
    setSelectedNode(nodeId);
    setSelectedRowId(nodeId);
    if (!selectedProjectId) {
      setTracePath([]);
      setActiveTab("Trace");
      return;
    }

    try {
      const trace = await getTrace(selectedProjectId, nodeId);
      setTracePath(trace.path);
    } catch {
      setTracePath([]);
    }
    setActiveTab("Trace");
  }, [selectedProjectId]);

  const handleEngineeringRowSelect = useCallback(
    (row: EngineeringTableResponseRow): void => {
      setSelectedNode(row.tag);
      setSelectedRowId(row.id?.trim() || row.tag);
      setSelectedEngineeringTag(row.tag);
      setSelectedEngineeringRow(row);
      if (activeTab === "Trace") {
        void handleTrace(row.tag);
      }
    },
    [activeTab, handleTrace]
  );

  const handleEngineeringOpenWhyTrace = useCallback((row: EngineeringTableResponseRow): void => {
    setSelectedNode(row.tag);
    setSelectedRowId(row.id?.trim() || row.tag);
    setSelectedWhyTraceTag(null);
    setActiveModule("plant_model");
    setActiveTab("Why");
    setIsRightPanelExpanded(true);
    setWhyFocusToken((value) => value + 1);
  }, []);

  const handleCloseWhyTrace = useCallback((): void => {
    setSelectedWhyTraceTag(null);
  }, []);

  const confirmDeleteProject = async (): Promise<void> => {
    if (!projectToDelete) {
      return;
    }

    try {
      await deleteProject(projectToDelete.id);
      const updated = projects.filter((project) => project.id !== projectToDelete.id);
      setProjects(updated);

      if (selectedProjectId === projectToDelete.id) {
        const nextProjectId = updated[0]?.id ?? "";
        if (nextProjectId) {
          await setActiveProject(nextProjectId).catch(() => null);
        }
        setSelectedProjectId(nextProjectId);
      }

      setProjectToDelete(null);
      setStatusText(`Deleted project: ${projectToDelete.name}`);
      toast.success(`Deleted: ${projectToDelete.name}`, {
        className: "industrial-toast",
        icon: <Trash2 size={14} className="toast-icon" />,
      });
    } catch {
      setStatusText("Could not delete project. Please try again.");
      toast.error("Project deletion failed", {
        className: "industrial-toast industrial-toast-error",
        icon: <AlertTriangle size={14} className="toast-icon toast-icon-error" />,
      });
    }
  };

  const currentProject = projects.find((project) => project.id === selectedProjectId);
  const selectedControlLoop = selectedControlLoopTag ? controlLoops.find((item) => item.loop_tag === selectedControlLoopTag) ?? null : null;
  const resolvedEngineeringRowsForWorkspace =
    liveEngineeringRows.length > 0 ? liveEngineeringRows : unsTableRowsOverride ?? engineeringTableData?.rows ?? [];
  const resolvedEngineeringRowsSource = liveEngineeringRows.length > 0 ? "deterministic_behavior" : unsTableRowsOverride ? "uns_override" : "engineering_table_response";
  const resolvedEngineeringFilteredCount =
    liveEngineeringRows.length > 0 ? liveEngineeringRowsFilteredCount : resolvedEngineeringRowsForWorkspace.length;
  const currentProjectDocuments = selectedProjectId ? projectDocumentsById[selectedProjectId] ?? [] : [];
  const hasUploadedDocuments = currentProjectDocuments.length > 0;
  const hasParsedPlantModel = graphNodes.length > 0 || resolvedEngineeringRowsForWorkspace.length > 0;
  const hasGeneratedLogic = generatedSTFiles.length > 0 || generatedLogic.trim().length > 0;
  const hasIOMapping = ioMappingRows.length > 0;
  const hasSimulationResults = simulationTrace.length > 0 || Boolean(simulationValidationData);

  useEffect(() => {
    if (!selectedEngineeringTag) {
      setSelectedEngineeringRow(null);
      return;
    }

    const nextSelectedRow = resolvedEngineeringRowsForWorkspace.find((row) => row.tag === selectedEngineeringTag) ?? null;
    if (!nextSelectedRow) {
      setSelectedEngineeringTag(null);
      setSelectedEngineeringRow(null);
      return;
    }

    setSelectedEngineeringRow(nextSelectedRow);
  }, [resolvedEngineeringRowsForWorkspace, selectedEngineeringTag]);

  useEffect(() => {
    console.log("COPILOT_SELECTED_TAG_STATE", selectedEngineeringTag);
  }, [selectedEngineeringTag]);

  useEffect(() => {
    setSelectedEngineeringTag(null);
    setSelectedEngineeringRow(null);
  }, [selectedProjectId]);

  useEffect(() => {
    setIsRightPanelExpanded(false);
  }, [selectedProjectId]);

  const currentProgressPanel = useMemo(() => {
    const runningModuleEntry = Object.entries(moduleStates).find(([, moduleState]) => moduleState.state === "running") as
      | [WorkspaceModuleId, ModuleState]
      | undefined;

    if (!loadingAction && !runningModuleEntry) {
      return null;
    }

    const [runningModuleId, moduleState] = runningModuleEntry ?? [null, null];
    const moduleId = loadingAction ? ACTION_MODULE_MAP[loadingAction] ?? runningModuleId : runningModuleId;
    const title = loadingAction
      ? ACTION_PROGRESS_LABELS[loadingAction]
      : moduleId
        ? MODULE_LABELS[moduleId]
        : "Processing";

    const detailLines = [
      statusText,
      moduleState?.message,
      selectedUploadFiles.length > 0 ? `Selected files: ${selectedUploadFiles.join(", ")}` : null,
      currentProject ? `Project: ${currentProject.name}` : "No project selected",
    ].filter((value): value is string => Boolean(value));

    return {
      action: loadingAction,
      moduleId,
      title,
      detailLines,
    };
  }, [currentProject, loadingAction, moduleStates, selectedUploadFiles, statusText]);
  const handleLeftPanelToggle = (): void => {
    setIsLeftPanelCollapsed((value) => !value);
  };

  const handleRightPanelResizeStart = (event: React.MouseEvent<HTMLDivElement>): void => {
    if (!isRightPanelExpanded) {
      return;
    }

    rightResizeStartRef.current = { startX: event.clientX, startWidth: rightPanelWidth };
    let latestWidth = rightPanelWidth;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";

    const onMouseMove = (moveEvent: MouseEvent): void => {
      const active = rightResizeStartRef.current;
      if (!active) {
        return;
      }
      const delta = active.startX - moveEvent.clientX;
      const viewportBound = Math.max(360, Math.floor(window.innerWidth * 0.55));
      const nextWidth = Math.min(Math.min(760, viewportBound), Math.max(260, active.startWidth + delta));
      latestWidth = nextWidth;
      setRightPanelWidth(nextWidth);
    };

    const onMouseUp = (): void => {
      rightResizeStartRef.current = null;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      window.localStorage.setItem("crosslayerx-right-panel-width", String(latestWidth));
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
  };

  const handleModuleSelect = (moduleId: WorkspaceModuleId): void => {
    setNavigatorSelection({ type: "module", id: moduleId });
    setActiveSidebarMode("projects");
    setActiveProjectFeature(null);
    setActiveModule(moduleId);
    if (moduleId === "documents") {
      setActiveMainView("table");
      return;
    }
    if (moduleId === "plant_model") {
      setActiveMainView("table");
      return;
    }
    if (moduleId === "control_loops") {
      setActiveMainView("table");
      return;
    }
    if (moduleId === "io_mapping") {
      setMonitoringPanelMode("io_mapping");
      setActiveBottomView("monitoring");
      setActiveMainView("table");
      return;
    }
    if (moduleId === "control_logic") {
      setCodePanelMode("control_logic");
      setActiveBottomView("logic");
      setActiveMainView("logic");
      return;
    }
    if (moduleId === "simulation") {
      setActiveBottomView("simulation");
      setActiveMainView("simulation");
      return;
    }
    if (moduleId === "runtime") {
      setMonitoringPanelMode("runtime");
      setActiveBottomView("monitoring");
      setActiveMainView("monitoring");
      return;
    }
    if (moduleId === "monitoring") {
      setMonitoringPanelMode("runtime");
      setActiveBottomView("monitoring");
      setActiveMainView("monitoring");
      return;
      return;
    setActiveMainView("monitoring");
    }
  };

  const handleAutoAssignIOMappingChannels = (): void => {
    if (ioMappingRows.length === 0) {
      return;
    }

    const priority: Record<string, number> = { DI: 1, DO: 2, AI: 3, AO: 4 };
    const counters: Record<string, number> = { DI: 0, DO: 0, AI: 0, AO: 0 };

    const reassigned = [...ioMappingRows]
      .sort((left, right) => {
        const l = priority[left.io_type.toUpperCase()] ?? 99;
        const r = priority[right.io_type.toUpperCase()] ?? 99;
        if (l !== r) {
          return l - r;
        }
        return left.tag.localeCompare(right.tag);
      })
      .map((row) => {
        const key = row.io_type.toUpperCase();
        const index = counters[key] ?? 0;
        counters[key] = index + 1;
        const baseSlot = key === "DI" ? 1 : key === "DO" ? 2 : key === "AI" ? 3 : key === "AO" ? 4 : 10;
        return {
          ...row,
          slot: baseSlot + Math.floor(index / 16),
          channel: (index % 16) + 1,
        };
      });

    setIOMappingRows(reassigned);
    setStatusText("IO mapping channels auto-assigned deterministically.");
  };

  const handleExportIOMappingCsv = (): void => {
    if (ioMappingRows.length === 0) {
      return;
    }

    const header = ["Tag", "Type", "IO", "PLC", "Slot", "Channel"];
    const rows = ioMappingRows.map((row) => [row.tag, row.device_type, row.io_type, row.plc_id, String(row.slot), String(row.channel)]);
    const csv = [header, ...rows]
      .map((line) => line.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(","))
      .join("\n");

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `io_mapping_${selectedProjectId || "project"}.csv`;
    link.click();
    URL.revokeObjectURL(url);
    setStatusText("IO mapping CSV exported.");
  };

  const handleValidateIOMapping = (): void => {
    if (ioMappingRows.length === 0) {
      setStatusText("No IO mapping rows to validate.");
      return;
    }

    const duplicateTags = new Set<string>();
    const seen = new Set<string>();
    for (const row of ioMappingRows) {
      const key = row.tag.trim().toUpperCase();
      if (!key) {
        continue;
      }
      if (seen.has(key)) {
        duplicateTags.add(key);
      }
      seen.add(key);
    }

    const invalidRows = ioMappingRows.filter((row) => !["AI", "AO", "DI", "DO"].includes(row.io_type.toUpperCase()));
    const overflowRows = ioMappingRows.filter((row) => row.channel < 1 || row.channel > 16);

    const issueCount = duplicateTags.size + invalidRows.length + overflowRows.length;
    if (issueCount > 0) {
      setStatusText(`IO mapping validation found ${issueCount} issue(s).`);
      return;
    }

    setStatusText("IO mapping validation passed.");
  };

  const mapRuntimeControlResult = (
    result: RuntimeControlDeployResponse,
    tags: Record<string, unknown>
  ): RuntimeValidationPanelData => {
    const toPanelStatus = (status: "passed" | "failed"): "success" | "failed" => (status === "passed" ? "success" : "failed");
    const requiredStepNames = ["compile_st", "build_runtime", "apply_io", "start_runtime"] as const;

    const stepMap: Partial<Record<(typeof requiredStepNames)[number], "idle" | "running" | "success" | "failed" | "warning">> = {};
    const stepMessages: Partial<Record<(typeof requiredStepNames)[number], string>> = {};

    for (const stepName of requiredStepNames) {
      const found = result.steps.find((step) => step.name === stepName);
      stepMap[stepName] = found ? toPanelStatus(found.status) : "idle";
      stepMessages[stepName] = found?.message || `${stepName} not executed.`;
    }

    return {
      project_id: result.project_id,
      run_id: `runtime-control-${Date.now()}`,
      validated_at: new Date().toISOString(),
      overall_status: result.status === "passed" ? "success" : "failed",
      checks_passed: result.steps.filter((step) => step.status === "passed").length,
      checks_failed: result.steps.filter((step) => step.status === "failed").length,
      checks_warning: 0,
      checks: result.steps.map((step, index) => ({
        check_id: `runtime-control-step-${index + 1}`,
        check_name: step.name,
        status: toPanelStatus(step.status),
        expected_value: "passed",
        actual_value: step.status,
        tolerance: null,
        message: step.message,
      })),
      runtime_state: result.runtime_status?.status || (result.status === "failed" ? "failed" : "idle"),
      deployed_at: new Date().toISOString(),
      active_project: result.project_id,
      runtime_project_dir: result.runtime_project_dir,
      steps_map: stepMap,
      step_messages: stepMessages,
      telemetry_tags: tags,
      errors: result.errors,
    };
  };

  const mapPersistedRuntimeState = (runtimeState: RuntimeStateResponse, tags: Record<string, unknown>): RuntimeValidationPanelData | null => {
    const deployment = runtimeState.deployment ?? null;
    if (!deployment) {
      return null;
    }

    const deployPassed = deployment.validation_status === "passed";
    const startStatus: "idle" | "running" | "success" | "failed" | "warning" =
      runtimeState.runtime_state === "running" ? "success" : runtimeState.runtime_state === "failed" ? "failed" : "warning";

    const checks = [
      {
        check_name: "compile_st",
        status: deployPassed ? "success" : "failed",
        message: deployPassed ? "Compiled ST metadata restored from persisted deployment state." : "Compilation previously failed.",
      },
      {
        check_name: "build_runtime",
        status: deployPassed ? "success" : "failed",
        message: deployPassed ? "Build metadata restored from persisted deployment state." : "Runtime build previously failed.",
      },
      {
        check_name: "apply_io",
        status: deployPassed ? "success" : "failed",
        message: deployPassed ? "IO bindings restored from persisted deployment state." : "IO apply previously failed.",
      },
      {
        check_name: "start_runtime",
        status: startStatus,
        message:
          runtimeState.runtime_state === "running"
            ? "Live runtime process is active."
            : runtimeState.runtime_state === "failed"
              ? "Live runtime process is in failed state."
              : "Deployment is persisted; runtime is currently not active.",
      },
    ] as const;

    return {
      project_id: runtimeState.project_id,
      run_id: `runtime-persisted-${deployment.id}`,
      validated_at: deployment.updated_at,
      overall_status: runtimeState.runtime_state === "failed" || !deployPassed ? "failed" : "success",
      checks_passed: checks.filter((item) => item.status === "success").length,
      checks_failed: checks.filter((item) => item.status === "failed").length,
      checks_warning: checks.filter((item) => item.status === "warning").length,
      checks: checks.map((item, index) => ({
        check_id: `runtime-persisted-check-${index + 1}`,
        check_name: item.check_name,
        status: item.status,
        expected_value: "success",
        actual_value: item.status,
        tolerance: null,
        message: item.message,
      })),
      runtime_state: runtimeState.runtime_state,
      deployed_at: deployment.updated_at,
      active_project: runtimeState.project_id,
      runtime_project_dir: deployment.artifact_path || null,
      steps_map: {
        compile_st: checks[0].status,
        build_runtime: checks[1].status,
        apply_io: checks[2].status,
        start_runtime: checks[3].status,
      },
      step_messages: {
        compile_st: checks[0].message,
        build_runtime: checks[1].message,
        apply_io: checks[2].message,
        start_runtime: checks[3].message,
      },
      telemetry_tags: tags,
      errors: deployment.last_error ? [deployment.last_error] : [],
    };
  };

  const toSimulationIssueList = (value: unknown): SimulationTraceIssue[] => {
    if (!Array.isArray(value)) {
      return [];
    }

    return value.flatMap((item) => {
      if (!item || typeof item !== "object") {
        return [];
      }

      const row = item as Record<string, unknown>;
      const tag = typeof row.tag === "string" ? row.tag.trim() : "";
      const issue = typeof row.issue === "string" ? row.issue.trim() : "";

      if (!tag && !issue) {
        return [];
      }

      return [{ tag: tag || "unknown", issue: issue || "unspecified_issue" }];
    });
  };

  const toSimulationScenarioStatus = (value: unknown): "idle" | "running" | "success" | "failed" | "warning" => {
    if (value === "running" || value === "success" || value === "failed" || value === "warning") {
      return value;
    }
    if (value === "completed" || value === "passed" || value === "pass") {
      return "success";
    }
    if (value === "error" || value === "fail") {
      return "failed";
    }
    return "idle";
  };

  const mapSimulationMetricsToPanelData = (
    projectId: string,
    metricsSource: unknown,
    validatedAt?: string
  ): SimulationValidationPanelResponse | null => {
    if (!metricsSource || typeof metricsSource !== "object") {
      return null;
    }

    const metrics = metricsSource as Record<string, unknown>;
    const issues = toSimulationIssueList(metrics.issues);
    const rawScenarios = Array.isArray(metrics.scenarios) ? metrics.scenarios : [];

    const scenarios = rawScenarios.flatMap((scenario, index) => {
      if (!scenario || typeof scenario !== "object") {
        return [];
      }

      const row = scenario as Record<string, unknown>;
      const scenarioId = typeof row.scenario_id === "string" && row.scenario_id.trim().length > 0 ? row.scenario_id : `simulation-scenario-${index + 1}`;
      const scenarioName =
        typeof row.scenario_name === "string" && row.scenario_name.trim().length > 0 ? row.scenario_name : `Scenario ${index + 1}`;

      return [{
        scenario_id: scenarioId,
        scenario_name: scenarioName,
        status: toSimulationScenarioStatus(row.status),
        cycle_time_ms: typeof row.cycle_time_ms === "number" ? row.cycle_time_ms : 0,
        duration_s: typeof row.duration_s === "number" ? row.duration_s : 0,
        alarms_triggered: typeof row.alarms_triggered === "number" ? row.alarms_triggered : issues.length,
        message:
          typeof row.message === "string" && row.message.trim().length > 0
            ? row.message
            : issues.length > 0
              ? `Trace analysis found ${issues.length} issue(s).`
              : "Trace analysis completed.",
      }];
    });

    const normalizedScenarios =
      scenarios.length > 0
        ? scenarios
        : issues.length > 0
          ? [{
              scenario_id: "trace_stability",
              scenario_name: "Signal Stability Check",
              status: "warning" as const,
              cycle_time_ms: 100,
              duration_s: 3,
              alarms_triggered: issues.length,
              message: `Trace analysis found ${issues.length} issue(s).`,
            }]
          : [];

    if (normalizedScenarios.length === 0) {
      return null;
    }

    const scenariosPassed = normalizedScenarios.filter((scenario) => scenario.status === "success").length;
    const scenariosFailed = normalizedScenarios.filter((scenario) => scenario.status === "failed").length;
    const scenariosWarning = normalizedScenarios.filter((scenario) => scenario.status === "warning").length;

    const overallStatus: "idle" | "running" | "success" | "failed" | "warning" =
      scenariosFailed > 0
        ? "failed"
        : normalizedScenarios.some((scenario) => scenario.status === "running")
          ? "running"
          : scenariosWarning > 0 || issues.length > 0
            ? "warning"
            : "success";

    return {
      project_id: projectId,
      simulation_run_id: `simulation-${Date.now()}`,
      validated_at: validatedAt || new Date().toISOString(),
      overall_status: overallStatus,
      scenarios_passed: scenariosPassed,
      scenarios_failed: scenariosFailed,
      scenarios_warning: scenariosWarning,
      scenarios: normalizedScenarios,
    };
  };

  const refreshRuntimeTags = async (): Promise<void> => {
    try {
      const tags = await getRuntimeTags();
      setRuntimeTelemetryTags(tags);
      setRuntimeValidationData((current) => (current ? { ...current, telemetry_tags: tags } : current));
    } catch {
      setStatusText("Runtime tags refresh failed.");
    }
  };

  const refreshRuntimeForceState = async (): Promise<void> => {
    if (!selectedProjectId) {
      setRuntimeForceableInputs([]);
      setForcedTagNames([]);
      return;
    }

    try {
      const response = await getRuntimeForcedInputs(selectedProjectId);
      setRuntimeForceableInputs(response.input_catalog ?? []);
      setForcedTagNames((response.forced_inputs ?? []).map((item) => item.tag));
      if (response.diagnostics) {
        setRuntimeDiagnostics(response.diagnostics);
      }
    } catch {
      setRuntimeForceableInputs([]);
      setForcedTagNames([]);
    }
  };

  const refreshRuntimeDiagnostics = async (): Promise<void> => {
    if (!selectedProjectId) {
      setRuntimeDiagnostics(null);
      return;
    }
    try {
      const response = await getRuntimeDiagnostics(selectedProjectId);
      setRuntimeDiagnostics(response.diagnostics ?? null);
    } catch {
      setRuntimeDiagnostics(null);
    }
  };

  const handleApplyRuntimeInputForce = async (payload: { tag: string; value: unknown; type: RuntimeSignalType }): Promise<void> => {
    if (!selectedProjectId) {
      throw new Error("No active project selected");
    }
    await applyRuntimeInputForce(selectedProjectId, payload);
    await Promise.all([refreshRuntimeForceState(), refreshRuntimeTags(), refreshRuntimeDiagnostics(), refreshSimulationTraceData(selectedProjectId)]);
    setStatusText(`Forced input applied for ${payload.tag}.`);
  };

  const handleClearRuntimeInputForce = async (tag: string): Promise<void> => {
    if (!selectedProjectId) {
      throw new Error("No active project selected");
    }
    await clearRuntimeInputForce(selectedProjectId, tag);
    await Promise.all([refreshRuntimeForceState(), refreshRuntimeTags(), refreshRuntimeDiagnostics(), refreshSimulationTraceData(selectedProjectId)]);
    setStatusText(`Forced input cleared for ${tag}.`);
  };

  const handleRunRuntimeEvaluationCycle = async (): Promise<void> => {
    if (!selectedProjectId) {
      return;
    }
    await runRuntimeEvaluationCycle(selectedProjectId, "manual_debug");
    await Promise.all([refreshRuntimeTags(), refreshRuntimeForceState(), refreshRuntimeDiagnostics(), refreshSimulationTraceData(selectedProjectId)]);
    setStatusText("Runtime evaluation cycle completed.");
  };

  const handleConfirmRuntimeDeploy = async (): Promise<void> => {
    if (!selectedProjectId) {
      return;
    }

    setIsRuntimeActionBusy(true);
    setRuntimeFailedMessage(null);
    updatePipelineStage("runtime_validation", "running");
    setMonitoringPanelMode("runtime");
    setActiveBottomView("monitoring");

    try {
      const result = await deployRuntimeControl({ project_id: selectedProjectId });

      let tags: Record<string, unknown> = {};
      try {
        tags = await getRuntimeTags();
      } catch {
        tags = {};
      }

      const panelData = mapRuntimeControlResult(result, tags);
      setRuntimeValidationData(panelData);
      setRuntimeTelemetryTags(tags);
      await Promise.all([refreshRuntimeForceState(), refreshRuntimeDiagnostics()]);
      const failedChecks = panelData.checks_failed > 0 || panelData.overall_status === "failed";
      updatePipelineStage("runtime_validation", failedChecks ? "failed" : "success");
      if (!failedChecks) {
        await refreshVersionHistory(selectedProjectId);
      }
      setStatusText(failedChecks ? "Runtime deployment failed. Review runtime step diagnostics." : "Runtime deployment passed. Runtime is active.");
    } catch {
      updatePipelineStage("runtime_validation", "failed");
      setRuntimeValidationData(null);
      setRuntimeFailedMessage("Runtime deployment failed. Check runtime dependencies and generated ST files.");
      setStatusText("Runtime deployment failed.");
    } finally {
      setIsRuntimeActionBusy(false);
    }
  };

  const handleRuntimeStart = async (): Promise<void> => {
    setIsRuntimeActionBusy(true);
    try {
      const result = await startRuntimeControl();
      setRuntimeValidationData((current) =>
        current
          ? {
              ...current,
              runtime_state: result.status === "passed" ? "running" : "failed",
              deployed_at: new Date().toISOString(),
            }
          : current
      );
      await Promise.all([refreshRuntimeTags(), refreshRuntimeForceState(), refreshRuntimeDiagnostics()]);
      setStatusText(result.step?.message || result.message || "Runtime start requested.");
    } catch {
      setStatusText("Runtime start failed.");
    } finally {
      setIsRuntimeActionBusy(false);
    }
  };

  const handleRuntimeStop = async (): Promise<void> => {
    setIsRuntimeActionBusy(true);
    try {
      const result = await stopRuntimeControl();
      setRuntimeValidationData((current) =>
        current
          ? {
              ...current,
              runtime_state: result.status === "passed" ? "stopped" : "failed",
            }
          : current
      );
      await refreshRuntimeTags();
      await Promise.all([refreshRuntimeForceState(), refreshRuntimeDiagnostics()]);
      setStatusText(result.step?.message || result.message || "Runtime stop requested.");
    } catch {
      setStatusText("Runtime stop failed.");
    } finally {
      setIsRuntimeActionBusy(false);
    }
  };

  useEffect(() => {
    if (!selectedProjectId || monitoringPanelMode !== "runtime") {
      return;
    }

    void Promise.all([refreshRuntimeTags(), refreshRuntimeForceState(), refreshRuntimeDiagnostics()]);
    const timer = window.setInterval(() => {
      void Promise.all([refreshRuntimeTags(), refreshRuntimeForceState(), refreshRuntimeDiagnostics()]);
    }, 3000);

    return () => {
      window.clearInterval(timer);
    };
  }, [monitoringPanelMode, selectedProjectId]);

  const traceControlLoopPath = (loop: ControlLoopRecord): void => {
    const path = [loop.sensor_tag, loop.controller_tag || "", loop.actuator_tag, loop.process_unit || ""].filter((item) => item.trim().length > 0);
    setTracePath(path);
  };

  const openControlLoopModal = (loop: ControlLoopRecord): void => {
    const processTag = loop.process_unit || "";
    const controlPath = [loop.sensor_tag, loop.controller_tag || "", loop.actuator_tag, processTag].filter((item) => item.length > 0).join(" -> ");
    setControlLoopModal({
      open: true,
      noLoop: false,
      loopId: loop.loop_tag,
      sensor: loop.sensor_tag,
      process: processTag,
      actuator: loop.actuator_tag,
      controlPath,
      source: loop.status || "",
      confidence: typeof loop.confidence === "number" ? loop.confidence : null,
    });
  };

  const handleControlLoopSelect = (loop: ControlLoopRecord): void => {
    setSelectedControlLoopTag(loop.loop_tag);
    setSelectedNode(loop.sensor_tag);
    setSelectedWhyTraceTag(loop.sensor_tag);
    traceControlLoopPath(loop);
    setIsRightPanelExpanded(true);
  };

  const handleControlLoopView = async (loop: ControlLoopRecord): Promise<void> => {
    try {
      const details = await getControlLoop(loop.loop_tag, selectedProjectId || undefined);
      setSelectedControlLoopTag(details.loop_tag);
      openControlLoopModal(details);
      traceControlLoopPath(details);
      setActiveTab("Control Loops");
      setIsRightPanelExpanded(true);
    } catch {
      setStatusText(`Unable to load loop details for ${loop.loop_tag}.`);
    }
  };

  const handleControlLoopEditStrategy = (loop: ControlLoopRecord): void => {
    const nextStrategy = window.prompt("Update control strategy", loop.control_strategy || "PID");
    if (!nextStrategy) {
      return;
    }
    setControlLoops((previous) =>
      previous.map((item) => (item.id === loop.id ? { ...item, control_strategy: nextStrategy.trim() || item.control_strategy } : item))
    );
    setStatusText(`Strategy updated locally for ${loop.loop_tag}.`);
  };

  const handleControlLoopGenerateLogic = async (_loop: ControlLoopRecord): Promise<void> => {
    await handleToolbarAction("generate_logic");
  };

  const handleControlLoopNavigateToST = (loop: ControlLoopRecord): void => {
    const candidateTags = [loop.sensor_tag, loop.actuator_tag, loop.controller_tag || "", loop.setpoint_tag || "", loop.output_tag || ""]
      .map((item) => item.trim())
      .filter((item) => item.length > 0);

    const targetFile = generatedSTFiles.find((file) => {
      const contentToken = toComparableToken(file.content || "");
      return candidateTags.some((tag) => contentToken.includes(toComparableToken(tag)));
    });

    setActiveBottomView("logic");
    setCodePanelMode("generated_st");
    setSelectedSTFilePath(targetFile?.path ?? generatedSTFiles[0]?.path ?? null);
    setStatusText(`Loop ${loop.loop_tag} linked to ST ${targetFile?.path ?? "bundle"}.`);
  };

  const handleControlLoopNavigateToIO = (loop: ControlLoopRecord): void => {
    setSelectedControlLoopTag(loop.loop_tag);
    setSelectedNode(loop.sensor_tag);
    setSelectedIOMappingTag(loop.actuator_tag || loop.sensor_tag);
    setActiveTab("IO Mapping");
    setActiveBottomView("monitoring");
    setMonitoringPanelMode("io_mapping");
    setIsRightPanelExpanded(true);
  };

  const handleControlLoopTrace = (loop: ControlLoopRecord): void => {
    handleControlLoopSelect(loop);
    setActiveTab("Trace");
    setIsRightPanelExpanded(true);
  };

  const handleControlLoopSimulate = async (_loop: ControlLoopRecord): Promise<void> => {
    if (!selectedProjectId) {
      return;
    }
    try {
      await runSimulation(selectedProjectId);
      await refreshSimulationTraceData(selectedProjectId);
      await refreshVersionHistory(selectedProjectId);
      setActiveTab("Replay");
      setActiveBottomView("simulation");
      setStatusText("Simulation completed for selected loop context.");
    } catch {
      setStatusText("Simulation failed for selected loop context.");
    }
  };

  const getProgressLinesForModules = (...moduleIds: WorkspaceModuleId[]): string[] => {
    if (!currentProgressPanel?.moduleId) {
      return [];
    }
    return moduleIds.includes(currentProgressPanel.moduleId) ? currentProgressPanel.detailLines : [];
  };

  const documentsWorkspaceView = (
    <div className="workspace-module-stack">
      <WorkspaceActionPanel
        eyebrow="Project documents"
        title={currentProject ? `${currentProject.name} documents` : "Documents"}
        description={
          selectedProjectId
            ? "Upload source documents here. These files become the basis for parsing the plant model and the downstream engineering steps."
            : "Select or create a project to upload source documents."
        }
        actionLabel="Upload Documents"
        onAction={() => {
          void handleToolbarAction("upload_documents");
        }}
        actionDisabled={Boolean(disabledActions.upload_documents)}
        actionLoading={loadingAction === "upload_documents"}
        progressLines={getProgressLinesForModules("documents")}
      />

      <div className="workspace-documents-list-panel">
        {currentProjectDocuments.length > 0 ? (
          <div className="workspace-documents-list">
            {currentProjectDocuments.map((document) => (
              <div key={document.id} className="workspace-documents-list-item">
                <span className="workspace-documents-file-name">{document.original_name}</span>
                <span className="workspace-documents-file-meta">{document.document_type.replace(/_/g, " ")}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="workspace-placeholder-panel">
            <h3>No documents uploaded yet</h3>
            <p>Upload P&amp;ID files, narratives, or other source documents to start the engineering flow.</p>
          </div>
        )}
      </div>
    </div>
  );

  const plantModelWorkspaceView = (
    <div className="workspace-module-stack">
      <WorkspaceActionPanel
        eyebrow="Plant model"
        title={hasParsedPlantModel ? "Plant model ready" : hasUploadedDocuments ? "Parse the plant model" : "Upload documents first"}
        description={
          hasParsedPlantModel
            ? "The plant model is available in the workspace. You can re-run parsing after document changes."
            : hasUploadedDocuments
              ? "Your source documents are uploaded. Parse them to build the plant graph and engineering table."
              : "This project does not have uploaded documents yet. Start by uploading source files from the Documents module."
        }
        actionLabel={hasUploadedDocuments ? "Parse Plant Model" : "Upload Documents"}
        onAction={() => {
          void handleToolbarAction(hasUploadedDocuments ? "parse_plant_model" : "upload_documents");
        }}
        actionDisabled={Boolean(disabledActions[hasUploadedDocuments ? "parse_plant_model" : "upload_documents"])}
        actionLoading={loadingAction === (hasUploadedDocuments ? "parse_plant_model" : "upload_documents")}
        progressLines={getProgressLinesForModules("documents", "plant_model")}
      />

      {hasParsedPlantModel ? (
        <EngineeringDeterministicTable
          projectId={selectedProjectId}
          reloadKey={behaviorRefreshKey}
          loading={engineeringTableLoading}
          error={engineeringTableError}
          onRowSelect={handleEngineeringRowSelect}
          onOpenWhyTrace={handleEngineeringOpenWhyTrace}
          externalSelectedTag={selectedEngineeringTag ?? selectedControlLoop?.sensor_tag ?? selectedNode}
          highlightedTags={selectedControlLoop ? [selectedControlLoop.sensor_tag, selectedControlLoop.actuator_tag] : []}
          onRowsResolved={(payload) => {
            setLiveEngineeringRows(payload.rows);
            setLiveEngineeringRowsFilteredCount(payload.filteredRows);
          }}
          onLoadingStateChange={setLiveEngineeringRowsLoading}
        />
      ) : (
        <div className="workspace-placeholder-panel">
          <h3>Plant model not parsed</h3>
          <p>Choose the trigger above to upload documents or parse the active project using the same existing endpoints.</p>
        </div>
      )}
    </div>
  );

  const controlLoopsWorkspaceView = (
    <div className="workspace-module-stack">
      <WorkspaceActionPanel
        eyebrow="Control loops"
        title={hasParsedPlantModel ? "Detect control loops" : "Plant model required"}
        description={
          hasParsedPlantModel
            ? "Run control loop detection for the active project. The same detection endpoint used in the top bar is now triggered here."
            : "Parse the plant model before detecting loops so the engineering graph has the required source data."
        }
        actionLabel={hasParsedPlantModel ? "Detect Control Loops" : "Parse Plant Model"}
        onAction={() => {
          void handleToolbarAction(hasParsedPlantModel ? "detect_control_loops" : "parse_plant_model");
        }}
        actionDisabled={Boolean(disabledActions[hasParsedPlantModel ? "detect_control_loops" : "parse_plant_model"])}
        actionLoading={loadingAction === (hasParsedPlantModel ? "detect_control_loops" : "parse_plant_model")}
        progressLines={getProgressLinesForModules("plant_model", "control_loops")}
      />

      {hasParsedPlantModel ? (
        <RightControlLoopsTab
          loops={controlLoops}
          ioMappingRows={ioMappingRows}
          engineeringRows={resolvedEngineeringRowsForWorkspace}
          replayTrace={simulationTrace}
          loading={isControlLoopsLoading}
          error={controlLoopsError}
          selectedLoopTag={selectedControlLoopTag}
          onSelectLoop={handleControlLoopSelect}
          onDetectLoops={() => {
            void runControlLoopDetection();
          }}
          onViewLoop={(loop) => {
            void handleControlLoopView(loop);
          }}
          onEditStrategy={handleControlLoopEditStrategy}
          onGenerateLogic={(loop) => {
            void handleControlLoopGenerateLogic(loop);
          }}
          onTraceLoop={handleControlLoopTrace}
          onSimulate={(loop) => {
            void handleControlLoopSimulate(loop);
          }}
          onNavigateToST={handleControlLoopNavigateToST}
          onNavigateToIO={handleControlLoopNavigateToIO}
        />
      ) : (
        <div className="workspace-placeholder-panel">
          <h3>Control loop detection is not ready</h3>
          <p>Parse the plant model first, then run loop detection from the trigger above.</p>
        </div>
      )}
    </div>
  );

  const ioMappingWorkspaceView = (
    <div className="workspace-module-stack">
      <WorkspaceActionPanel
        eyebrow="IO mapping"
        title={!hasParsedPlantModel ? "Plant model required" : !hasGeneratedLogic ? "Logic generation required" : "Generate IO mapping"}
        description={
          !hasParsedPlantModel
            ? "Parse the plant model before generating IO mapping."
            : !hasGeneratedLogic
              ? "Generate logic first so IO mapping can resolve against the latest control artifacts."
              : "Generate or refresh IO mapping for the active project."
        }
        actionLabel={!hasParsedPlantModel ? "Parse Plant Model" : !hasGeneratedLogic ? "Generate Logic" : "Generate IO Mapping"}
        onAction={() => {
          void handleToolbarAction(!hasParsedPlantModel ? "parse_plant_model" : !hasGeneratedLogic ? "generate_logic" : "generate_io_mapping");
        }}
        actionDisabled={Boolean(disabledActions[!hasParsedPlantModel ? "parse_plant_model" : !hasGeneratedLogic ? "generate_logic" : "generate_io_mapping"])}
        actionLoading={loadingAction === (!hasParsedPlantModel ? "parse_plant_model" : !hasGeneratedLogic ? "generate_logic" : "generate_io_mapping")}
        progressLines={getProgressLinesForModules("plant_model", "control_logic", "io_mapping")}
      />

      {hasIOMapping ? (
        <IOMappingTablePanel
          rows={ioMappingRows}
          selectedTag={selectedIOMappingTag}
          onSelectRow={setSelectedIOMappingTag}
          loading={isGeneratingIOMapping}
          failedMessage={ioMappingFailedMessage}
          onRetry={() => {
            void handleToolbarAction("generate_io_mapping");
          }}
          onAutoAssignChannels={handleAutoAssignIOMappingChannels}
          onExportCsv={handleExportIOMappingCsv}
          onValidateMapping={handleValidateIOMapping}
          forcedTags={forcedTagNames}
        />
      ) : (
        <div className="workspace-placeholder-panel">
          <h3>No IO mapping generated yet</h3>
          <p>Use the trigger above once the plant model and control logic are ready.</p>
        </div>
      )}
    </div>
  );

  const logicWorkspaceView = (
    <div className="workspace-module-stack">
      <WorkspaceActionPanel
        eyebrow="Control logic"
        title={!hasParsedPlantModel ? "Plant model required" : "Generate control logic"}
        description={
          !hasParsedPlantModel
            ? "Parse the plant model before generating control logic."
            : "Generate or refresh ST logic for the active project using the same endpoint that was previously on the top bar."
        }
        actionLabel={!hasParsedPlantModel ? "Parse Plant Model" : "Generate Logic"}
        onAction={() => {
          void handleToolbarAction(!hasParsedPlantModel ? "parse_plant_model" : "generate_logic");
        }}
        actionDisabled={Boolean(disabledActions[!hasParsedPlantModel ? "parse_plant_model" : "generate_logic"])}
        actionLoading={loadingAction === (!hasParsedPlantModel ? "parse_plant_model" : "generate_logic")}
        progressLines={getProgressLinesForModules("plant_model", "control_logic")}
      />

      {generatedSTFiles.length > 0 || generatedLogic.trim().length > 0 ? (
        <CodeExplorerPanel
          files={generatedSTFiles}
          bundledCode={generatedLogic}
          selectedFilePath={selectedSTFilePath}
          onSelectFile={setSelectedSTFilePath}
          diagnosticsByFile={stDiagnosticsByFile}
          jumpToLocation={stJumpLocation}
          loading={pipelineStatuses.st_generation === "running"}
          requiredPreviousStep="Generate ST"
        />
      ) : (
        <div className="workspace-placeholder-panel">
          <h3>No logic artifact available yet</h3>
          <p>Generate logic from the trigger above to populate the ST workspace.</p>
        </div>
      )}
    </div>
  );

  const simulationWorkspaceView = (
    <div className="workspace-module-stack">
      <WorkspaceActionPanel
        eyebrow="Simulation"
        title={!hasParsedPlantModel ? "Plant model required" : "Run simulation"}
        description={
          !hasParsedPlantModel
            ? "Parse the plant model before running the simulation flow."
            : "Run the existing simulation endpoint for the active project from here instead of the removed top bar button."
        }
        actionLabel={!hasParsedPlantModel ? "Parse Plant Model" : "Run Simulation"}
        onAction={() => {
          void handleToolbarAction(!hasParsedPlantModel ? "parse_plant_model" : "run_simulation");
        }}
        actionDisabled={Boolean(disabledActions[!hasParsedPlantModel ? "parse_plant_model" : "run_simulation"])}
        actionLoading={loadingAction === (!hasParsedPlantModel ? "parse_plant_model" : "run_simulation")}
        progressLines={getProgressLinesForModules("plant_model", "simulation")}
      />

      {hasSimulationResults ? (
        <SimulationValidationPanel
          data={simulationValidationData}
          actionLoading={isRuntimeActionBusy}
          failedMessage={simulationFailedMessage}
          forceableInputs={runtimeForceableInputs}
          onApplyInputForce={handleApplyRuntimeInputForce}
          onClearInputForce={handleClearRuntimeInputForce}
          onRefreshInputForceState={refreshRuntimeForceState}
          onRunEvaluationCycle={handleRunRuntimeEvaluationCycle}
          onRetry={() => {
            void handleToolbarAction("run_simulation");
          }}
          requiredPreviousStep="Runtime Check"
        />
      ) : (
        <div className="workspace-placeholder-panel">
          <h3>No simulation run yet</h3>
          <p>Run a simulation from the trigger above to populate this workspace.</p>
        </div>
      )}
    </div>
  );

  const runtimeAction = activeModule === "monitoring" ? "start_monitoring" : "deploy_runtime";
  const diagnosticsWorkspaceView = (
    <div className="workspace-module-stack">
      <section className="workspace-documents-list-panel">
        <div className="workspace-documents-list-header">
          <h3>Diagnostics</h3>
          <p>Runtime diagnostics, impact context, and fault analysis for the active project.</p>
        </div>
        <RightDiagnosticsTab
          diagnostics={runtimeDiagnostics}
          systemContext={selectedSystemContext}
          impactSummary={selectedImpactSummary}
          simulationIssues={simulationIssues}
          faultAnalysis={faultAnalysis}
          analyzedTag={faultAnalysisTag}
          inputMessage={faultAnalysisInputMessage}
          loading={isFaultAnalysisLoading}
          error={faultAnalysisError}
        />
      </section>
    </div>
  );

  const versionsWorkspaceView = (
    <VersionsWorkspace
      activeSection={(activeProjectFeature === "pid" ? "pid" : "history") as VersionsWorkspaceSection}
      versions={versions}
      selectedVersion={selectedVersion}
      selectedVersionTags={selectedVersionTags}
      diff={versionDiff}
      loading={versioningLoading}
      errorMessage={versioningError}
      busyAction={versionBusyAction}
      settings={versioningSettings}
      pidChanges={pidChanges}
      pidChangesLoading={pidChangesLoading}
      pidChangesError={pidChangesError}
      pidApplying={pidApplying}
      pidSnapshotCreating={pidCreatingSnapshot}
      pidAcceptedConflicts={pidAcceptedConflicts}
      onSelectVersion={setSelectedVersion}
      onToggleCompareSelection={handleVersionToggleCompareSelection}
      onCreateSnapshot={() => {
        void handleVersionCreateSnapshot();
      }}
      onLoadSnapshot={(version) => {
        void handleVersionLoadSnapshot(version);
      }}
      onRollback={(version) => {
        void handleVersionRollback(version);
      }}
      onCompare={() => {
        void handleVersionCompare();
      }}
      onExport={(version) => {
        void handleVersionExport(version);
      }}
      onSettingsChange={setVersioningSettings}
      onRefreshPIDChanges={() => {
        void refreshPIDChanges();
      }}
      onPIDAcceptChanges={() => setPIDAcceptedConflicts((value) => !value)}
      onPIDReviewConflicts={handlePIDReviewConflicts}
      onPIDApplyUpdate={() => {
        void handlePIDApplyUpdate();
      }}
      onPIDCreateSnapshot={() => {
        void handlePIDCreateSnapshot();
      }}
    />
  );

  const runtimeWorkspaceView = (
    <div className="workspace-module-stack">
      <WorkspaceActionPanel
        eyebrow={activeModule === "monitoring" ? "Monitoring" : "Runtime"}
        title={!hasIOMapping ? "IO mapping required" : activeModule === "monitoring" ? "Start monitoring" : "Deploy runtime"}
        description={
          !hasIOMapping
            ? "Generate IO mapping before deploying or starting runtime monitoring."
            : activeModule === "monitoring"
              ? "Start monitoring using the same endpoint previously exposed in the top bar."
              : "Deploy runtime for the active project from this middle-panel trigger."
        }
        actionLabel={!hasIOMapping ? "Generate IO Mapping" : activeModule === "monitoring" ? "Start Monitoring" : "Deploy Runtime"}
        onAction={() => {
          void handleToolbarAction(!hasIOMapping ? "generate_io_mapping" : runtimeAction);
        }}
        actionDisabled={Boolean(disabledActions[!hasIOMapping ? "generate_io_mapping" : runtimeAction])}
        actionLoading={loadingAction === (!hasIOMapping ? "generate_io_mapping" : runtimeAction)}
        progressLines={getProgressLinesForModules("io_mapping", "runtime", "monitoring")}
      />

      {runtimeValidationData || runtimeFailedMessage ? (
        <RuntimeValidationPanel
          data={runtimeValidationData}
          loading={isRuntimeStateLoading}
          actionLoading={isRuntimeActionBusy}
          failedMessage={runtimeFailedMessage}
          onDeploy={() => {
            void handleConfirmRuntimeDeploy();
          }}
          onStart={() => {
            void handleRuntimeStart();
          }}
          onStop={() => {
            void handleRuntimeStop();
          }}
          forceableInputs={runtimeForceableInputs}
          onApplyInputForce={handleApplyRuntimeInputForce}
          onClearInputForce={handleClearRuntimeInputForce}
          onRefreshInputForceState={refreshRuntimeForceState}
          onRunEvaluationCycle={handleRunRuntimeEvaluationCycle}
          requiredPreviousStep="IO Mapping"
        />
      ) : (
        <div className="workspace-placeholder-panel">
          <h3>Runtime has not been started yet</h3>
          <p>Deploy runtime or start monitoring from the trigger above once IO mapping is available.</p>
        </div>
      )}
    </div>
  );

  const monitoringWorkspaceView = activeProjectFeature === "versions" || activeProjectFeature === "pid"
    ? versionsWorkspaceView
    : activeModule === "diagnostics"
      ? diagnosticsWorkspaceView
      : runtimeWorkspaceView;

  return (
    <div className="dashboard">
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3200,
          className: "industrial-toast",
        }}
      />

      <CommandBar />

      {showCreateProjectModal ? (
        <div className="modal-backdrop" onClick={() => setShowCreateProjectModal(false)}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <h3>Create Project</h3>
            <label className="modal-label" htmlFor="project-name">
              Project Name
            </label>
            <input
              id="project-name"
              className="modal-input"
              placeholder="Plant A"
              value={projectForm.name}
              onChange={(event) => setProjectForm((value) => ({ ...value, name: event.target.value }))}
            />

            <label className="modal-label" htmlFor="project-description">
              Industry Type
            </label>
            <input
              id="project-industry"
              className="modal-input"
              placeholder="Oil & Gas"
              value={projectForm.industry}
              onChange={(event) => setProjectForm((value) => ({ ...value, industry: event.target.value }))}
            />

            <label className="modal-label" htmlFor="project-description">
              Plant Description
            </label>
            <textarea
              id="project-description"
              className="modal-textarea"
              placeholder="Optional project description"
              value={projectForm.description}
              onChange={(event) => setProjectForm((value) => ({ ...value, description: event.target.value }))}
            />

            <label className="modal-label" htmlFor="project-files">
              Import Documents
            </label>
            <input
              id="project-files"
              className="modal-input"
              type="file"
              multiple
              onChange={(event) => {
                const files = event.target.files ? Array.from(event.target.files) : [];
                setProjectForm((value) => ({ ...value, importFiles: files }));
              }}
            />

            <label className="modal-label" htmlFor="project-runtime">
              Select PLC Runtime
            </label>
            <select
              id="project-runtime"
              className="modal-input"
              value={projectForm.plcRuntime}
              onChange={(event) =>
                setProjectForm((value) => ({
                  ...value,
                  plcRuntime: event.target.value as "beremiz" | "codesys" | "siemens" | "other",
                }))
              }
            >
              <option value="beremiz">Beremiz</option>
              <option value="codesys">CODESYS</option>
              <option value="siemens">Siemens S7</option>
              <option value="other">Other</option>
            </select>

            <label className="modal-label" htmlFor="project-owner">
              Project Owner
            </label>
            <input
              id="project-owner"
              className="modal-input"
              placeholder="system"
              value={projectForm.owner}
              onChange={(event) => setProjectForm((value) => ({ ...value, owner: event.target.value }))}
            />

            <label className="modal-label" htmlFor="project-status">
              Status
            </label>
            <select
              id="project-status"
              className="modal-input"
              value={projectForm.status}
              onChange={(event) =>
                setProjectForm((value) => ({
                  ...value,
                  status: event.target.value as "draft" | "active" | "archived",
                }))
              }
            >
              <option value="draft">draft</option>
              <option value="active">active</option>
              <option value="archived">archived</option>
            </select>

            <div className="modal-actions">
              <button className="command-btn" onClick={() => setShowCreateProjectModal(false)} type="button">
                Cancel
              </button>
              <button
                className="command-btn primary"
                onClick={() => {
                  void handleCreateProject();
                }}
                type="button"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {showExportDialog ? (
        <div className="modal-backdrop" onClick={() => setShowExportDialog(false)}>
          <div className="modal-card export-modal" onClick={(event) => event.stopPropagation()}>
            <div className="export-modal-header">
              <h3>Export Logic</h3>
            </div>
            <div className="export-modal-body">
            <label className="modal-label" htmlFor="export-source-mode">Export Source</label>
            <select
              id="export-source-mode"
              className="modal-input"
              value={exportSourceMode}
              onChange={(event) => {
                const mode = event.target.value as ExportSourceMode;
                setExportSourceMode(mode);
                if (mode === "live") {
                  setExportSourceVersionTag(null);
                } else {
                  setExportSourceVersionTag((current) => current ?? selectedVersion?.version_tag ?? versions[0]?.version_tag ?? null);
                }
              }}
            >
              <option value="live">Live Current State</option>
              <option value="version">Saved Snapshot / Version</option>
            </select>

            {exportSourceMode === "version" ? (
              <>
                <label className="modal-label" htmlFor="export-source-version">Version</label>
                <select
                  id="export-source-version"
                  className="modal-input"
                  value={exportSourceVersionTag ?? ""}
                  onChange={(event) => setExportSourceVersionTag(event.target.value || null)}
                >
                  {versions.length === 0 ? <option value="">No saved versions</option> : null}
                  {versions.map((version) => (
                    <option key={version.id} value={version.version_tag}>
                      {version.version_tag} • {new Date(version.created_at).toLocaleString()}
                    </option>
                  ))}
                </select>
              </>
            ) : null}

            <label className="modal-label" htmlFor="export-vendor">Target Vendor</label>
            <select
              id="export-vendor"
              className="modal-input"
              value={exportVendor}
              onChange={(event) => setExportVendor(event.target.value as PLCExportVendor)}
            >
              <option value="siemens">Siemens TIA Portal</option>
              <option value="rockwell">Rockwell Studio 5000</option>
              <option value="codesys">Codesys</option>
              <option value="beckhoff">TwinCAT</option>
              <option value="openplc">OpenPLC</option>
              <option value="generic_st">Generic Structured Text</option>
            </select>

            <div className="modal-actions" style={{ marginTop: "0.4rem" }}>
              <button
                className={`command-btn ${exportReadinessLoading ? "is-loading" : ""}`}
                type="button"
                onClick={() => void refreshExportReadiness()}
                disabled={exportReadinessLoading}
              >
                {exportReadinessLoading ? (
                  <>
                    <span className="btn-loader" aria-hidden="true" />
                    Validating...
                  </>
                ) : (
                  "Refresh Readiness"
                )}
              </button>
            </div>

            <div className="monitor-frame" style={{ marginTop: "0.6rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: "0.5rem" }}>
                <strong>Export Readiness</strong>
                <span>
                  {!exportReadiness
                    ? "Pending"
                    : exportReadiness.export_allowed
                      ? (exportReadiness.warnings.length > 0 ? "Allowed with warnings" : "Ready for export")
                      : "Blocked"}
                </span>
              </div>
              {exportReadinessError ? <div style={{ color: "#ef4444" }}>{exportReadinessError}</div> : null}
              {exportReadiness ? (
                <>
                  <div className="modal-label">Core readiness</div>
                  <div>Plant model: {exportReadiness.checks.find((item) => item.key === "plant_model")?.ready ? "ready" : "not ready"}</div>
                  <div>ST logic: {exportReadiness.checks.find((item) => item.key === "st_logic")?.ready ? "ready" : "not ready"}</div>
                  <div>Export target: {exportReadiness.checks.find((item) => item.key === "target_vendor")?.ready ? "ready" : "not ready"}</div>
                  <div className="export-note">Derived alarm/limit/internal control tags do not require direct hardware IO mapping if their parent field signal is already mapped.</div>
                  {exportReadinessSections.autoResolvedDerived.length > 0 ? (
                    <div style={{ color: "#8a6b21", fontSize: "0.74rem", marginTop: "0.2rem" }}>
                      <strong>Auto-resolved derived tags</strong>
                      {exportReadinessSections.autoResolvedDerived.map((message, index) => (
                        <div key={`derived-${message}-${index}`} className="value-mono">• {message}</div>
                      ))}
                    </div>
                  ) : null}
                  {exportReadinessSections.internalNonBlocking.length > 0 ? (
                    <div style={{ color: "#8a6b21", fontSize: "0.74rem", marginTop: "0.2rem" }}>
                      <strong>Export warnings</strong>
                      {exportReadinessSections.internalNonBlocking.map((message, index) => (
                        <div key={`internal-${message}-${index}`} className="value-mono">• {message}</div>
                      ))}
                    </div>
                  ) : null}
                  {exportReadinessSections.unknownUnclassified.length > 0 ? (
                    <div style={{ color: "#9c5b2b", fontSize: "0.74rem", marginTop: "0.2rem" }}>
                      <strong>Unknown/unclassified tags</strong>
                      {exportReadinessSections.unknownUnclassified.map((message, index) => (
                        <div key={`unknown-${message}-${index}`} className="value-mono">• {message}</div>
                      ))}
                    </div>
                  ) : null}
                </>
              ) : null}
            </div>

            {exportResult ? (
              <div className="monitor-frame" style={{ marginTop: "0.6rem" }}>
                <div>Export ID: <span className="value-mono">{exportResult.export_id}</span></div>
                <div>Vendor: {exportResult.vendor}</div>
                <div>Source: {exportResult.source_mode === "version" ? `version ${exportResult.source_version_id || "(unknown)"}` : "live current state"}</div>
                <div>Artifact: {exportResult.artifact_name || "Generated package"}</div>
                <div>Generated: {new Date(exportResult.generated_at).toLocaleString()}</div>
                <div>Blocks: {exportResult.logic_block_count ?? 0} • Tags: {exportResult.tag_count ?? 0}</div>
                {exportResult.package_preview && exportResult.package_preview.length > 0 ? (
                  <div style={{ marginTop: "0.4rem" }}>
                    <strong>Package Preview</strong>
                    <div style={{ maxHeight: "6rem", overflow: "auto" }}>
                      {exportResult.package_preview.slice(0, 20).map((file) => (
                        <div key={file} className="value-mono">{file}</div>
                      ))}
                    </div>
                  </div>
                ) : null}
                <button
                  className="command-btn primary"
                  type="button"
                  onClick={() => {
                    window.open(buildExportDownloadUrl(exportResult.export_id), "_blank", "noopener,noreferrer");
                  }}
                >
                  Download Export Package
                </button>
              </div>
            ) : null}

            <div className="monitor-frame" style={{ marginTop: "0.6rem" }}>
              <strong>Deployment Readiness</strong>
              <div>Status: Ready for testing workflow</div>
              <div>{exportDeploymentMessage}</div>
              <label className="modal-label" htmlFor="export-deploy-runtime" style={{ marginTop: "0.45rem", marginBottom: "0.45rem", display: "block" }}>Target Runtime</label>
              <select
                id="export-deploy-runtime"
                className="modal-input"
                value={deploymentTargetRuntime}
                onChange={(event) => setDeploymentTargetRuntime(event.target.value)}
              >
                <option value="openplc">OpenPLC</option>
                <option value="beremiz">Beremiz</option>
                <option value="codesys">Codesys</option>
                <option value="siemens">Siemens</option>
                <option value="other">Other</option>
              </select>
              {exportDeploymentLogs.length > 0 ? (
                <div style={{ maxHeight: "5.5rem", overflow: "auto", marginTop: "0.35rem" }}>
                  {exportDeploymentLogs.slice(-10).map((item, index) => (
                    <div key={`${item}-${index}`} className="value-mono">{item}</div>
                  ))}
                </div>
              ) : null}
              <div className="modal-actions" style={{ marginTop: "0.4rem" }}>
                <div style={{ flex: 1 }}>
                  <button
                    className={`command-btn ${exportDeploymentBusy && exportDeploymentAction === "prepare" ? "is-loading" : ""}`}
                    type="button"
                    disabled={!canPrepareHandoff}
                    onClick={() => {
                      void handleExportDeploymentHandoff(false);
                    }}
                  >
                    {exportDeploymentBusy && exportDeploymentAction === "prepare" ? (
                      <>
                        <span className="btn-loader" aria-hidden="true" />
                        Preparing...
                      </>
                    ) : (
                      "Prepare Handoff"
                    )}
                  </button>
                  {prepareHandoffDisabledReason && !(exportDeploymentBusy && exportDeploymentAction === "prepare") ? (
                    <div style={{ color: "#7a2a2a", fontSize: "0.72rem", marginTop: "0.2rem" }}>{prepareHandoffDisabledReason}</div>
                  ) : null}
                </div>
                <div style={{ flex: 1 }}>
                  <button
                    className={`command-btn primary ${exportDeploymentBusy && exportDeploymentAction === "deploy" ? "is-loading" : ""}`}
                    type="button"
                    disabled={!canTriggerRuntimeDeploy}
                    onClick={() => {
                      void handleExportDeploymentHandoff(true);
                    }}
                  >
                    {exportDeploymentBusy && exportDeploymentAction === "deploy" ? (
                      <>
                        <span className="btn-loader" aria-hidden="true" />
                        Deploying...
                      </>
                    ) : (
                      "Trigger Runtime Deploy"
                    )}
                  </button>
                  {triggerRuntimeDeployDisabledReason && !(exportDeploymentBusy && exportDeploymentAction === "deploy") ? (
                    <div style={{ color: "#7a2a2a", fontSize: "0.72rem", marginTop: "0.2rem" }}>{triggerRuntimeDeployDisabledReason}</div>
                  ) : null}
                </div>
              </div>
            </div>

            </div>

            <div className="modal-actions export-modal-footer">
              <button className="command-btn" onClick={() => setShowExportDialog(false)} type="button">
                Close
              </button>
              <button
                className={`command-btn primary ${isExportingLogic ? "is-loading" : ""}`}
                onClick={() => {
                  void handleGeneratePLCExport();
                }}
                type="button"
                disabled={!canGenerateExport}
              >
                {isExportingLogic ? (
                  <>
                    <span className="btn-loader" aria-hidden="true" />
                    Generating...
                  </>
                ) : (
                  "Generate Export"
                )}
              </button>
            </div>
            {generateExportDisabledReason && !isExportingLogic ? (
              <div style={{ color: "#7a2a2a", fontSize: "0.72rem", margin: "0 1rem 0.65rem" }}>{generateExportDisabledReason}</div>
            ) : null}
          </div>
        </div>
      ) : null}

      {showDirectPLCDeployDialog ? (
        <div className="modal-backdrop" onClick={() => setShowDirectPLCDeployDialog(false)}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <h3>Deploy PLC</h3>
            <p className="modal-help-text">
              Direct PLC Deployment Layer scaffold is feature-flagged and disabled by default.
            </p>

            <label className="modal-label" htmlFor="direct-plc-address">PLC Address</label>
            <input
              id="direct-plc-address"
              className="modal-input"
              placeholder="192.168.1.100"
              value={directDeployForm.plcAddress}
              onChange={(event) => setDirectDeployForm((value) => ({ ...value, plcAddress: event.target.value }))}
            />

            <label className="modal-label" htmlFor="direct-plc-protocol">Protocol</label>
            <select
              id="direct-plc-protocol"
              className="modal-input"
              value={directDeployForm.protocol}
              onChange={(event) =>
                setDirectDeployForm((value) => ({
                  ...value,
                  protocol: event.target.value as DirectPLCProtocol,
                }))
              }
            >
              <option value="opc_ua">OPC UA</option>
              <option value="modbus_tcp">Modbus TCP</option>
              <option value="ethernet_ip">EtherNet/IP</option>
              <option value="profinet">Profinet</option>
              <option value="mqtt_industrial">MQTT Industrial</option>
            </select>

            <label className="modal-label" htmlFor="direct-plc-runtime">Target Runtime</label>
            <select
              id="direct-plc-runtime"
              className="modal-input"
              value={directDeployForm.targetRuntime}
              onChange={(event) =>
                setDirectDeployForm((value) => ({
                  ...value,
                  targetRuntime: event.target.value as DirectPLCTargetRuntime,
                }))
              }
            >
              <option value="openplc">OpenPLC</option>
              <option value="beremiz">Beremiz</option>
              <option value="codesys">Codesys</option>
              <option value="siemens_s7">Siemens S7</option>
              <option value="beckhoff_twincat">Beckhoff TwinCAT</option>
              <option value="custom">Custom</option>
            </select>

            <label className="modal-label" htmlFor="direct-plc-io-config">IO Configuration</label>
            <textarea
              id="direct-plc-io-config"
              className="modal-textarea"
              rows={4}
              placeholder='{"mapping": []}'
              value={directDeployForm.ioConfiguration}
              onChange={(event) => setDirectDeployForm((value) => ({ ...value, ioConfiguration: event.target.value }))}
            />

            <div className="monitor-frame" style={{ marginTop: "0.5rem" }}>
              <div>Syntax Validation: {directPLCSafetyGates.syntax_validation_passed ? "Passed" : "Required"}</div>
              <div>Logic Verification: {directPLCSafetyGates.logic_verification_passed ? "Passed" : "Required"}</div>
              <div>IO Validation: {directPLCSafetyGates.io_validation_passed ? "Passed" : "Required"}</div>
              <div>Simulation Test: {directPLCSafetyGates.simulation_test_passed ? "Passed" : "Required"}</div>
              <div>Feature Flag: {directPLCFeatureEnabled ? "Enabled" : "Disabled"}</div>
            </div>

            {directDeployResult ? <p className="modal-help-text">{directDeployResult}</p> : null}

            <div className="modal-actions">
              <button className="command-btn" onClick={() => setShowDirectPLCDeployDialog(false)} type="button">
                Close
              </button>
              <button
                className="command-btn primary"
                type="button"
                disabled={directDeployBusy || !directPLCCanSubmit || !directDeployForm.plcAddress.trim()}
                onClick={() => {
                  void handleDirectPLCDeploy();
                }}
              >
                {directDeployBusy ? "Submitting..." : "Deploy PLC"}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {projectToDelete ? (
        <div className="modal-backdrop" onClick={() => setProjectToDelete(null)}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <h3>Delete Project</h3>
            <p className="modal-help-text">
              Are you sure you want to delete <strong>{projectToDelete.name}</strong>? This action cannot be undone.
            </p>
            <div className="modal-actions">
              <button className="command-btn" onClick={() => setProjectToDelete(null)} type="button">
                Cancel
              </button>
              <button
                className="command-btn danger"
                onClick={() => {
                  void confirmDeleteProject();
                }}
                type="button"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {controlLoopModal.open ? (
        <div className="modal-backdrop" onClick={() => setControlLoopModal((value) => ({ ...value, open: false }))}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <h3>Control Loop</h3>
            {controlLoopModal.noLoop ? (
              <p className="modal-help-text">No control loop detected</p>
            ) : (
              <dl className="kv">
                <dt>Loop ID</dt>
                <dd>{controlLoopModal.loopId}</dd>
                <dt>Path</dt>
                <dd>{`${controlLoopModal.sensor} → ${controlLoopModal.process} → ${controlLoopModal.actuator}`}</dd>
                <dt>Control Path</dt>
                <dd>{controlLoopModal.controlPath}</dd>
                <dt>Source</dt>
                <dd>{controlLoopModal.source || "N/A"}</dd>
                <dt>Confidence</dt>
                <dd>{controlLoopModal.confidence !== null ? controlLoopModal.confidence.toFixed(2) : "N/A"}</dd>
              </dl>
            )}
            <div className="modal-actions">
              <button
                className="command-btn"
                onClick={() => setControlLoopModal((value) => ({ ...value, open: false }))}
                type="button"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      ) : null}

      <input
        ref={uploadInputRef}
        hidden
        multiple
        type="file"
        onChange={(event) => {
          const selectedFiles = event.target.files;
          if (!selectedFiles || selectedFiles.length === 0 || !selectedProjectId) {
            return;
          }

          const files = Array.from(selectedFiles);
          setSelectedUploadFiles(files.map((file) => file.name));
          const inferredTypes = files.map((file) => {
            const lowered = file.name.toLowerCase();
            if (
              lowered.includes("pid") ||
              lowered.includes("p&id") ||
              lowered.includes("p_and_i") ||
              lowered.includes("p and i") ||
              lowered.includes("p_i_d") ||
              lowered.includes("p-i-d")
            ) {
              return "pid_pdf" as const;
            }
            if (lowered.includes("narrative") || lowered.includes("control")) {
              return "control_narrative" as const;
            }
            return "unknown_document" as const;
          });

          setIsUploading(true);
          setModuleState("documents", { state: "running", message: "Uploading documents", updatedAt: new Date().toISOString() });
          void uploadDocuments(selectedProjectId, files, inferredTypes)
            .then(async () => {
              await refreshProjectDocuments(selectedProjectId);
              setModuleState("documents", { state: "success", message: `Uploaded ${files.length} file(s)`, updatedAt: new Date().toISOString() });
              setStatusText(`Uploaded ${files.length} file(s) to active project.`);
              toast.success(`Uploaded ${files.length} file(s)`, {
                className: "industrial-toast",
                icon: <Upload size={14} className="toast-icon" />,
              });
            })
            .catch(() => {
              setModuleState("documents", { state: "failed", message: "Document upload failed", updatedAt: new Date().toISOString() });
              setStatusText("Upload failed. Ensure backend server is running and accepts multipart uploads.");
              toast.error("Upload failed", {
                className: "industrial-toast industrial-toast-error",
                icon: <AlertTriangle size={14} className="toast-icon toast-icon-error" />,
              });
            })
            .finally(() => {
              setIsUploading(false);
              event.target.value = "";
            });
        }}
      />

      <div className="workspace-shell">
        <div
          className={`main-shell ${isLeftPanelCollapsed ? "left-collapsed" : ""} ${isRightPanelExpanded ? "right-expanded" : ""}`}
          style={{
            ["--right-panel-width" as string]: `${isRightPanelExpanded ? rightPanelWidth : 38}px`,
          }}
        >
              <div className="main-shell-content">
                <aside className={`left-panel ${isLeftPanelCollapsed ? "collapsed" : ""}`}>
                  <div className="left-shell">
                    <ActivityBar
                      activeActivity={uiState.activeSidebarMode}
                      isSidebarCollapsed={isLeftPanelCollapsed}
                      onSelectActivity={(activity) => {
                        setActiveSidebarMode(activity);
                        if (activity === "settings") {
                          setActiveSettingsItem("general");
                        }
                        if (isLeftPanelCollapsed) {
                          setIsLeftPanelCollapsed(false);
                        }
                      }}
                      onOpenSidebar={() => setIsLeftPanelCollapsed(false)}
                    />

                    <div className={`primary-sidebar ${isLeftPanelCollapsed ? "collapsed" : ""}`}>
                      {!isLeftPanelCollapsed ? (
                        <button
                          className="side-panel-toggle left"
                          type="button"
                          aria-label="Collapse navigator panel"
                          onClick={handleLeftPanelToggle}
                        >
                          <ChevronLeft size={14} />
                        </button>
                      ) : null}

                      {!isLeftPanelCollapsed ? (
                        activeActivity === "projects" ? (
                          <SidebarModeProjects
                            projects={projects}
                            graphNodes={graphNodes}
                            selectedProjectId={uiState.selectedProject}
                            activeSelection={navigatorSelection}
                            onCreateProject={() => {
                              setShowCreateProjectModal(true);
                            }}
                            onRequestDeleteProject={(projectId) => {
                              const target = projects.find((project) => project.id === projectId) ?? null;
                              setProjectToDelete(target);
                            }}
                            onSelectProject={(projectId) => {
                              setNavigatorSelection({ type: "project", id: projectId });
                              void setActiveProject(projectId)
                                .catch(() => null)
                                .finally(() => {
                                  setSelectedProjectId(projectId);
                                });
                            }}
                            selectedNode={selectedNode}
                            onSelectNode={(nodeId) => {
                              setNavigatorSelection({ type: "node", id: nodeId });
                              setSelectedNode(nodeId);
                              setSelectedRowId(nodeId);
                            }}
                            activeModule={panelState.activeModule}
                            onSelectModule={handleModuleSelect}
                            activeFeature={activeProjectFeature}
                            onSelectFeature={handleProjectFeatureSelect}
                          />
                        ) : (
                          <SidebarModeSettings activeItem={activeSettingsItem} onSelectItem={handleSettingsNavSelect} />
                        )
                      ) : null}
                    </div>
                  </div>
                </aside>

                <MainWorkspaceRouter
                  activeView={uiState.activeView}
                  hasProject={Boolean(selectedProjectId)}
                  graphView={(
                    <GraphWorkspace
                      graphNodes={graphNodes.map((node) => ({
                        ...node,
                        label: node.id,
                      }))}
                      graphEdges={plantGraph.edges}
                      replayMode={activeTab === "Replay"}
                      replayPoint={replayPoint}
                      selectedNode={selectedNode}
                      tracePath={tracePath}
                      onNodeSelect={(nodeId) => {
                        setSelectedNode(nodeId);
                        setSelectedRowId(nodeId);
                      }}
                      onReplayPointChange={setReplayPoint}
                      onTraceNode={(nodeId) => {
                        void handleTrace(nodeId);
                      }}
                    />
                  )}
                  tableView={activeModule === "documents" ? documentsWorkspaceView : activeModule === "control_loops" ? controlLoopsWorkspaceView : activeModule === "io_mapping" ? ioMappingWorkspaceView : plantModelWorkspaceView}
                  logicView={logicWorkspaceView}
                  simulationView={simulationWorkspaceView}
                  monitoringView={monitoringWorkspaceView}
                />
              </div>

              <div
                className="panel-resize-handle panel-resize-handle-vertical right-panel-resize-handle"
                role="separator"
                aria-orientation="vertical"
                aria-label="Resize right panel"
                onMouseDown={handleRightPanelResizeStart}
              />

              <aside className={`right-panel ${isRightPanelExpanded ? "expanded" : "collapsed"}`}>
                <button
                  className="side-panel-toggle right"
                  type="button"
                  aria-label={isRightPanelExpanded ? "Collapse right panel" : "Expand right panel"}
                  onClick={() => setIsRightPanelExpanded((value) => !value)}
                >
                  {isRightPanelExpanded ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
                </button>

                {isRightPanelExpanded ? (
                  <DetailsPanel
                    activeTab={uiState.activeTab}
                    replayPoint={replayPoint}
                    selectedReplayTag={selectedReplayTag}
                    replayTrace={simulationTrace}
                    replayIssues={simulationIssues}
                    controlLoops={controlLoops}
                    engineeringRowsForLoops={resolvedEngineeringRowsForWorkspace}
                    controlLoopsLoading={isControlLoopsLoading}
                    controlLoopsError={controlLoopsError}
                    selectedControlLoopTag={selectedControlLoopTag}
                    selectedEquipment={selectedEquipment}
                    systemContext={selectedSystemContext}
                    behaviorExplanation={selectedBehaviorExplanation}
                    impactSummary={selectedImpactSummary}
                    systemContextLoading={systemContextLoading}
                    systemContextError={selectedSystemContext ? null : systemContextError}
                    whyFocusToken={whyFocusToken}
                    selectedNodeId={selectedNode}
                    tracePath={tracePath}
                    whyTraceTag={selectedWhyTraceTag}
                    ioMappingRows={selectedNodeIOMappingRows}
                    controlLoopIOMappingRows={ioMappingRows}
                    ioMappingIssues={ioMappingIssues}
                    selectedIOMappingTag={selectedIOMappingTag}
                    runtimeTelemetryTags={runtimeTelemetryTags}
                    forcedTagNames={forcedTagNames}
                    runtimeDiagnostics={runtimeDiagnostics}
                    faultAnalysis={faultAnalysis}
                    faultAnalysisTag={faultAnalysisTag}
                    faultAnalysisInputMessage={faultAnalysisInputMessage}
                    faultAnalysisLoading={isFaultAnalysisLoading}
                    faultAnalysisError={faultAnalysisError}
                    onSelectIOMappingTag={(tag) => {
                      setSelectedIOMappingTag(tag);
                      setActiveBottomView("monitoring");
                      setMonitoringPanelMode("io_mapping");
                      setActiveTab("IO Mapping");
                    }}
                    onReplayPointChange={setReplayPoint}
                    onCloseWhyTrace={handleCloseWhyTrace}
                    onSelectedReplayTagChange={setSelectedReplayTag}
                    onSelectControlLoop={handleControlLoopSelect}
                    onDetectControlLoops={() => {
                      void runControlLoopDetection();
                    }}
                    onViewControlLoop={(loop) => {
                      void handleControlLoopView(loop);
                    }}
                    onEditControlLoopStrategy={handleControlLoopEditStrategy}
                    onGenerateControlLoopLogic={(loop) => {
                      void handleControlLoopGenerateLogic(loop);
                    }}
                    onTraceControlLoop={handleControlLoopTrace}
                    onSimulateControlLoop={(loop) => {
                      void handleControlLoopSimulate(loop);
                    }}
                    onNavigateControlLoopToST={handleControlLoopNavigateToST}
                    onNavigateControlLoopToIO={handleControlLoopNavigateToIO}
                    pidChanges={pidChanges}
                    pidChangesLoading={pidChangesLoading}
                    pidChangesError={pidChangesError}
                    pidApplying={pidApplying}
                    pidSnapshotCreating={pidCreatingSnapshot}
                    pidAcceptedConflicts={pidAcceptedConflicts}
                    onPIDAcceptChanges={() => setPIDAcceptedConflicts((value) => !value)}
                    onPIDReviewConflicts={handlePIDReviewConflicts}
                    onPIDApplyUpdate={() => {
                      void handlePIDApplyUpdate();
                    }}
                    onPIDCreateSnapshot={() => {
                      void handlePIDCreateSnapshot();
                    }}
                    projectId={selectedProjectId}
                    engineeringRows={resolvedEngineeringRowsForWorkspace}
                    engineeringRowsSource={resolvedEngineeringRowsSource}
                    engineeringFilteredRowsCount={resolvedEngineeringFilteredCount}
                    engineeringRowsLoading={liveEngineeringRowsLoading}
                    productionAuthToken={productionAuthToken}
                    onProductionAuthTokenChange={setProductionAuthToken}
                    onWorkspaceRowsUpdate={setUnsTableRowsOverride}
                    onWorkspaceSelectTag={(tag) => {
                      setSelectedNode(tag);
                      setSelectedRowId(tag);
                    }}
                    onWorkspaceTracePath={(path) => {
                      setTracePath(path);
                      if (path[0]) {
                        setSelectedNode(path[0]);
                        setSelectedRowId(path[0]);
                      }
                      setSelectedWhyTraceTag(null);
                      setActiveTab("Trace");
                      setIsRightPanelExpanded(true);
                    }}
                    onTraceStepSelect={(tag) => {
                      setSelectedNode(tag);
                      setSelectedRowId(tag);
                      void handleTrace(tag);
                      setActiveTab("Trace");
                      setIsRightPanelExpanded(true);
                    }}
                    onTabChange={setActiveTab}
                  />
                ) : null}
              </aside>
        </div>
      </div>

      <div className="workspace-status-bar" role="status" aria-live="polite">
        <span>{currentProject ? `Project: ${currentProject.name}` : "Project: none"}</span>
        <span>Module: {uiShell.activeWorkspaceModule.replace(/_/g, " ")}</span>
        <span>Row: {uiState.selectedRow || "none"}</span>
        <span>Connection: {isRuntimeStateLoading ? "syncing" : "ready"}</span>
      </div>

      <BottomPanel
        projectId={selectedProjectId}
        selectedTag={selectedEngineeringTag}
        selectedRow={selectedEngineeringRow}
        engineeringRows={resolvedEngineeringRowsForWorkspace}
        graphSummary={activeMainView === "graph" && graphNodes.length > 0 ? {
          nodeCount: graphNodes.length,
          edgeCount: plantGraph.edges.length,
        } : null}
      />
    </div>
  );
}
