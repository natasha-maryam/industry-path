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
import { Group, Panel, Separator, useDefaultLayout } from "react-resizable-panels";
import BottomPanels from "../components/BottomPanels";
import type { GeneratedLogicFile, STDiagnosticMarker, STJumpLocation } from "../components/CodeExplorerPanel";
import CommandBar, { type ToolbarAction } from "../components/CommandBar";
import DetailsPanel, { type RightTab } from "../components/DetailsPanel";
import GraphWorkspace from "../components/GraphWorkspace";
import EngineeringTable from "../components/plant/EngineeringTable";
import ProjectNavigator from "../components/ProjectNavigator";
import type { RuntimeValidationPanelData } from "../components/RuntimeValidationPanel";
import type { STVerificationIssueItem } from "../components/STVerificationPanel";
import { useWorkspaceContext } from "../context/WorkspaceContext";
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
  createInitialPipelineStatuses,
  deleteProject,
  deployDirectPLC,
  deployRuntimeControl,
  detectControlLoops,
  analyzeFault,
  getControlLoop,
  getControlLoops,
  getMonitoring,
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
  type EngineeringTableResponse,
  type EngineeringTableResponseRow,
  type Project,
} from "../services/api";
import "../styles/dashboard.css";
import type { ModuleState, WorkspaceModuleId, WorkspacePanelState } from "../types/workspace";
import { MODULE_DEFAULT_STATE } from "../types/workspace";

type EquipmentType = "Tank" | "Pump" | "Sensor" | "Valve";
type BottomView = "simulation" | "monitoring" | "logic";
type CodePanelMode = "control_logic" | "generated_st" | "verification" | "version_diff";
type MonitoringPanelMode = "io_mapping" | "runtime" | "versions";

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

export default function Dashboard() {
  const { activeProjectId: selectedProjectId, setActiveProjectId: setSelectedProjectId, plantGraph, setPlantGraph } = useWorkspaceContext();
  const graphNodes = plantGraph.nodes;
  const graphEdges = plantGraph.edges;

  const [activeAction, setActiveAction] = useState<ToolbarAction>("upload_documents");
  const [selectedNode, setSelectedNode] = useState<string>("");
  const [panelState, setPanelState] = useState<WorkspacePanelState>({
    activeModule: "plant_model",
    activeRightTab: "Details",
    activeBottomView: "simulation",
    codePanelMode: "control_logic",
    monitoringPanelMode: "io_mapping",
  });
  const activeTab = panelState.activeRightTab;
  const activeBottomView = panelState.activeBottomView;
  const codePanelMode = panelState.codePanelMode;
  const monitoringPanelMode = panelState.monitoringPanelMode;

  const setActiveTab = (tab: RightTab): void => {
    setPanelState((previous) => ({ ...previous, activeRightTab: tab }));
    if (tab === "Versions") {
      setMonitoringPanelMode("versions");
      setActiveBottomView("monitoring");
      if (selectedProjectId) {
        void refreshVersionHistory(selectedProjectId);
      }
    }
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
  };
  const [tracePath, setTracePath] = useState<string[]>([]);
  const [replayMode] = useState<boolean>(false);
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
  const [exportResult, setExportResult] = useState<PLCExportResponse | null>(null);
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
  const [graphWorkspaceView, setGraphWorkspaceView] = useState<"graph" | "table">("graph");
  const [engineeringTableData, setEngineeringTableData] = useState<EngineeringTableResponse | null>(null);
  const [engineeringTableLoading, setEngineeringTableLoading] = useState<boolean>(false);
  const [engineeringTableError, setEngineeringTableError] = useState<string | null>(null);
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
  const rightResizeStartRef = useRef<{ startX: number; startWidth: number } | null>(null);

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
      setPanelState((previous) => ({ ...previous, activeModule: "control_loops", activeRightTab: "Control Loops" }));
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
      setIsRightPanelExpanded(true);
      return;
    }
    if (stage === "runtime_validation") {
      setMonitoringPanelMode("runtime");
      setActiveBottomView("monitoring");
      setActiveTab("Diagnostics");
      setIsRightPanelExpanded(true);
      return;
    }
    if (stage === "simulation_validation") {
      setActiveBottomView("simulation");
      setActiveTab("Diagnostics");
      setIsRightPanelExpanded(true);
      return;
    }
    if (stage === "version_snapshot") {
      setMonitoringPanelMode("versions");
      setActiveBottomView("monitoring");
      setActiveTab("Diagnostics");
      setIsRightPanelExpanded(true);
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

    for (const stage of toastableStages) {
      const prevState = previous[stage];
      const nextState = pipelineStatuses[stage];
      if (prevState === nextState) {
        continue;
      }

      syncWorkspaceForStage(stage);

      const toastId = `pipeline-${stage}`;
      const label = PIPELINE_STAGE_LABELS[stage];

      if (nextState === "running") {
        toast.loading(`${label} running...`, {
          id: toastId,
          className: "industrial-toast",
          icon: <LoaderCircle size={14} className="toast-icon" />,
        });
      } else if (nextState === "success") {
        toast.success(`${label} completed`, {
          id: toastId,
          className: "industrial-toast",
          icon: <CheckCircle2 size={14} className="toast-icon" />,
        });
      } else if (nextState === "failed") {
        toast.error(`${label} failed`, {
          id: toastId,
          className: "industrial-toast industrial-toast-error",
          icon: <AlertTriangle size={14} className="toast-icon toast-icon-error" />,
        });
      } else if (nextState === "warning") {
        toast(`${label} completed with warnings`, {
          id: toastId,
          className: "industrial-toast",
          icon: <AlertTriangle size={14} className="toast-icon" />,
        });
      } else {
        toast.dismiss(toastId);
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
      export_logic: !selectedProjectId,
      deploy_runtime: !selectedProjectId,
      start_monitoring: !selectedProjectId,
      analyze_fault: !selectedProjectId,
      replay_event: !selectedProjectId,
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
    if (pipelineStatuses.runtime_validation === "running") {
      return "deploy_runtime";
    }
    if (isRuntimeActionBusy) {
      return "start_monitoring";
    }
    return null;
  }, [isExportingLogic, isParsing, isRuntimeActionBusy, isUploading, pipelineStatuses.io_mapping, pipelineStatuses.runtime_validation, pipelineStatuses.st_generation]);

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
        updatePipelineStage("st_verification", "failed");
        if (!options.silent) {
          setStatusText(`ST verification failed with ${verification.summary.error_count} error(s).`);
        }
        return;
      }

      if (verification.status === "passed_with_warnings") {
        updatePipelineStage("st_verification", "warning");
        if (!options.silent) {
          setStatusText(`ST verification passed with warnings (${verification.summary.warning_count}).`);
        }
        return;
      }

      updatePipelineStage("st_verification", "success");
      if (!options.silent) {
        setStatusText("ST verification passed.");
      }
    } catch {
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
      setPipelineStatuses(createInitialPipelineStatuses());
      setShowLogic(false);
      return;
    }

    setPipelineStatuses(createInitialPipelineStatuses());
    setRuntimeValidationData(null);
    setRuntimeFailedMessage(null);
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
        setEngineeringTableData(data);
      } catch {
        setEngineeringTableData(null);
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
          updatePipelineStage("io_mapping", "success");
        }
      } catch {
        setIOMappingRows([]);
        setIOMappingIssues([]);
        setSelectedIOMappingTag(null);
        setIOMappingSummary(null);
      }
    };

    const loadLatestSimulationTrace = async (): Promise<void> => {
      try {
        const [tracePayload, analysisPayload] = await Promise.all([getSimulationTrace(selectedProjectId), getSimulationAnalysis(selectedProjectId)]);
        const traceRows = tracePayload.trace ?? [];
        setSimulationTrace(traceRows);
        setSimulationIssues(analysisPayload.issues ?? []);
        if (traceRows.length === 0) {
          setSelectedReplayTag("");
        }
      } catch {
        setSimulationTrace([]);
        setSimulationIssues([]);
        setSelectedReplayTag("");
      }
    };

    void loadGraph();
    void loadEngineeringTable();
    void loadLatestIOMapping();
    void loadLatestSimulationTrace();
    void refreshControlLoops(selectedProjectId);
    void loadPersistedRuntimeState();
    void refreshVersionHistory(selectedProjectId);
    void refreshPIDChanges();
  }, [refreshControlLoops, refreshPIDChanges, refreshVersionHistory, selectedProjectId]);

  useEffect(() => {
    if (!selectedProjectId || (activeTab !== "Replay" && activeTab !== "Diagnostics")) {
      return;
    }
    const refresh = async (): Promise<void> => {
      try {
        const [tracePayload, analysisPayload] = await Promise.all([getSimulationTrace(selectedProjectId), getSimulationAnalysis(selectedProjectId)]);
        const traceRows = tracePayload.trace ?? [];
        setSimulationTrace(traceRows);
        setSimulationIssues(analysisPayload.issues ?? []);
        if (traceRows.length === 0) {
          setSelectedReplayTag("");
        }
      } catch {
        setSimulationTrace([]);
        setSimulationIssues([]);
      }
    };
    void refresh();
  }, [activeTab, selectedProjectId]);

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
      setModuleState("plant_model", { state: "running", message: "Awaiting file selection", updatedAt: new Date().toISOString() });
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

      if (action === "export_logic") {
        setShowExportDialog(true);
        setExportResult(null);
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
        setPanelState((previous) => ({ ...previous, activeModule: "diagnostics", activeRightTab: "Diagnostics" }));
        setStatusText(`Fault analysis complete for ${analysis.alarm || resolvedTag}.`);
        setIsFaultAnalysisLoading(false);
      }

      if (action === "replay_event") {
        setIsExportingLogic(true);
        setModuleState("simulation", { state: "running", message: "Loading replay event", updatedAt: new Date().toISOString() });
        const replay = await getReplay(selectedProjectId);
        setModuleState("simulation", { state: "success", message: "Replay data refreshed", updatedAt: new Date().toISOString() });
        setPanelState((previous) => ({ ...previous, activeModule: "simulation", activeRightTab: "Replay" }));
        setStatusText(`Replay event loaded (${Object.keys(replay).length} fields).`);
        setIsExportingLogic(false);
      }

    } catch {
      const actionToModule: Partial<Record<ToolbarAction, WorkspaceModuleId>> = {
        parse_plant_model: "plant_model",
        detect_control_loops: "control_loops",
        generate_logic: "control_logic",
        generate_io_mapping: "io_mapping",
        export_logic: "control_logic",
        deploy_runtime: "runtime",
        start_monitoring: "monitoring",
        analyze_fault: "diagnostics",
        replay_event: "simulation",
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

  const handleGeneratePLCExport = async (): Promise<void> => {
    if (!selectedProjectId) {
      return;
    }
    setIsExportingLogic(true);
    setExportResult(null);
    try {
      const result = await createPLCExport(selectedProjectId, exportVendor);
      setExportResult(result);
      setStatusText(`Export created for ${result.project_name} (${result.vendor}).`);
      toast.success(`Export ready: ${result.vendor}`, { className: "industrial-toast" });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Export failed";
      setStatusText("PLC export generation failed.");
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setIsExportingLogic(false);
    }
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
      }

      setProjects((value) => [...value, created]);
      setSelectedProjectId(created.id);
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

  const handleTrace = async (nodeId: string): Promise<void> => {
    setSelectedNode(nodeId);
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
  };

  const handleEngineeringTraceSignal = (row: EngineeringTableResponseRow): void => {
    void handleTrace(row.tag);
    setIsRightPanelExpanded(true);
  };

  const handleEngineeringOpenControlLoop = (row: EngineeringTableResponseRow): void => {
    const loopMatch = controlLoops.find(
      (loop) => loop.loop_tag === row.tag || loop.sensor_tag === row.tag || loop.controller_tag === row.tag || loop.actuator_tag === row.tag
    );

    setActiveTab("Control Loops");
    setIsRightPanelExpanded(true);

    if (loopMatch) {
      setSelectedControlLoopTag(loopMatch.loop_tag);
      setSelectedNode(loopMatch.sensor_tag || row.tag);
      return;
    }

    setSelectedControlLoopTag(row.tag);
    setSelectedNode(row.tag);
    setStatusText(`No explicit control loop found for ${row.tag}.`);
  };

  const handleEngineeringOpenIOMapping = (row: EngineeringTableResponseRow): void => {
    setSelectedIOMappingTag(row.tag);
    setSelectedNode(row.tag);
    setMonitoringPanelMode("io_mapping");
    setActiveBottomView("monitoring");
    setActiveTab("IO Mapping");
    setIsRightPanelExpanded(true);
  };

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
  const activeModuleState = moduleStates[panelState.activeModule];
  const layoutStorage = typeof window === "undefined" ? undefined : window.localStorage;
  const workspaceRowsLayout = useDefaultLayout({ id: "crosslayerx-workspace-rows", storage: layoutStorage });

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
    setActiveModule(moduleId);
    if (moduleId === "plant_model") {
      setActiveTab("Details");
      setIsRightPanelExpanded(true);
      return;
    }
    if (moduleId === "control_loops") {
      setActiveTab("Control Loops");
      setIsRightPanelExpanded(true);
      return;
    }
    if (moduleId === "io_mapping") {
      setMonitoringPanelMode("io_mapping");
      setActiveBottomView("monitoring");
      setActiveTab("IO Mapping");
      setIsRightPanelExpanded(true);
      return;
    }
    if (moduleId === "control_logic") {
      setCodePanelMode("control_logic");
      setActiveBottomView("logic");
      setIsRightPanelExpanded(true);
      return;
    }
    if (moduleId === "simulation") {
      setActiveBottomView("simulation");
      setActiveTab("Replay");
      setIsRightPanelExpanded(true);
      return;
    }
    if (moduleId === "runtime") {
      setMonitoringPanelMode("runtime");
      setActiveBottomView("monitoring");
      setActiveTab("Diagnostics");
      setIsRightPanelExpanded(true);
      return;
    }
    if (moduleId === "monitoring") {
      setMonitoringPanelMode("runtime");
      setActiveBottomView("monitoring");
      setActiveTab("Signals");
      setIsRightPanelExpanded(true);
      return;
    }
    setActiveTab("Diagnostics");
    setIsRightPanelExpanded(true);
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

  const refreshSimulationTraceData = async (projectId?: string): Promise<void> => {
    const activeProjectId = projectId || selectedProjectId;
    if (!activeProjectId) {
      setSimulationTrace([]);
      setSimulationIssues([]);
      setSelectedReplayTag("");
      return;
    }
    try {
      const [tracePayload, analysisPayload] = await Promise.all([getSimulationTrace(activeProjectId), getSimulationAnalysis(activeProjectId)]);
      const traceRows = tracePayload.trace ?? [];
      setSimulationTrace(traceRows);
      setSimulationIssues(analysisPayload.issues ?? []);
      if (traceRows.length === 0) {
        setSelectedReplayTag("");
      }
    } catch {
      setSimulationTrace([]);
      setSimulationIssues([]);
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
    traceControlLoopPath(loop);
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

  return (
    <div className="dashboard">
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3200,
          className: "industrial-toast",
        }}
      />

      <CommandBar
        activeAction={activeAction}
        loadingAction={loadingAction}
        disabledActions={disabledActions}
        onAction={(action) => {
          void handleToolbarAction(action);
        }}
      />

      <div className="project-status-line">
        <div className="status-left">
          {isParsing || isUploading ? (
            <span className="activity-chip">
              <LoaderCircle size={12} className="activity-spinner" />
              {isParsing ? "Parsing in progress" : "Uploading files"}
            </span>
          ) : null}
          <span>{statusText}</span>
          {activeModuleState?.message ? <span className="selected-files-inline">{`${activeModuleState.state.toUpperCase()}: ${activeModuleState.message}`}</span> : null}
          {selectedUploadFiles.length > 0 ? (
            <span className="selected-files-inline" title={selectedUploadFiles.join(", ")}>
              Selected: {selectedUploadFiles.join(", ")}
            </span>
          ) : null}
        </div>
        <strong>{currentProject ? `${currentProject.name} (${currentProject.id})` : "No project selected"}</strong>
      </div>

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
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <h3>Export Logic</h3>
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
            </select>

            {exportResult ? (
              <div className="monitor-frame" style={{ marginTop: "0.6rem" }}>
                <div>Export ID: <span className="value-mono">{exportResult.export_id}</span></div>
                <div>Vendor: {exportResult.vendor}</div>
                <div>Artifact: {exportResult.artifact_name || "Generated package"}</div>
                <div>Generated: {new Date(exportResult.generated_at).toLocaleString()}</div>
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

            <div className="modal-actions">
              <button className="command-btn" onClick={() => setShowExportDialog(false)} type="button">
                Close
              </button>
              <button className="command-btn primary" onClick={() => { void handleGeneratePLCExport(); }} type="button" disabled={isExportingLogic}>
                {isExportingLogic ? "Generating..." : "Generate Export"}
              </button>
            </div>
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
          setModuleState("plant_model", { state: "running", message: "Uploading documents", updatedAt: new Date().toISOString() });
          void uploadDocuments(selectedProjectId, files, inferredTypes)
            .then(() => {
              setModuleState("plant_model", { state: "success", message: `Uploaded ${files.length} file(s)`, updatedAt: new Date().toISOString() });
              setStatusText(`Uploaded ${files.length} file(s) to active project.`);
              toast.success(`Uploaded ${files.length} file(s)`, {
                className: "industrial-toast",
                icon: <Upload size={14} className="toast-icon" />,
              });
            })
            .catch(() => {
              setModuleState("plant_model", { state: "failed", message: "Document upload failed", updatedAt: new Date().toISOString() });
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
        <Group
          id="crosslayerx-workspace-rows"
          orientation="vertical"
          defaultLayout={workspaceRowsLayout.defaultLayout}
          onLayoutChanged={workspaceRowsLayout.onLayoutChanged}
        >
          <Panel id="workspace-top" defaultSize="74%" minSize="42%">
            <div
              className={`main-shell ${isLeftPanelCollapsed ? "left-collapsed" : ""} ${isRightPanelExpanded ? "right-expanded" : ""}`}
              style={{
                ["--right-panel-width" as string]: `${isRightPanelExpanded ? rightPanelWidth : 38}px`,
              }}
            >
              <div className="main-shell-content">
                <aside className={`left-panel ${isLeftPanelCollapsed ? "collapsed" : ""}`}>
                  <button
                    className="side-panel-toggle left"
                    type="button"
                    aria-label={isLeftPanelCollapsed ? "Expand navigator panel" : "Collapse navigator panel"}
                    onClick={handleLeftPanelToggle}
                  >
                    {isLeftPanelCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
                  </button>

                  {!isLeftPanelCollapsed ? (
                    <ProjectNavigator
                      projects={projects}
                      graphNodes={graphNodes}
                      selectedProjectId={selectedProjectId}
                      onCreateProject={() => {
                        setShowCreateProjectModal(true);
                      }}
                      onRequestDeleteProject={(projectId) => {
                        const target = projects.find((project) => project.id === projectId) ?? null;
                        setProjectToDelete(target);
                      }}
                      onSelectProject={(projectId) => {
                        void setActiveProject(projectId)
                          .catch(() => null)
                          .finally(() => {
                            setSelectedProjectId(projectId);
                          });
                      }}
                      selectedNode={selectedNode}
                      onSelectNode={setSelectedNode}
                      activeModule={panelState.activeModule}
                      onSelectModule={handleModuleSelect}
                    />
                  ) : null}
                </aside>

                <section className="graph-shell">
                  <div className="plant-view-toggle">
                    <button
                      className={`command-btn ${graphWorkspaceView === "graph" ? "active" : ""}`}
                      type="button"
                      onClick={() => setGraphWorkspaceView("graph")}
                    >
                      Graph View
                    </button>
                    <button
                      className={`command-btn ${graphWorkspaceView === "table" ? "active" : ""}`}
                      type="button"
                      onClick={() => setGraphWorkspaceView("table")}
                    >
                      Table View
                    </button>
                  </div>

                  {graphWorkspaceView === "graph" ? (
                    <GraphWorkspace
                      graphEdges={graphEdges}
                      graphNodes={graphNodes}
                      replayMode={replayMode}
                      replayPoint={replayPoint}
                      selectedNode={selectedNode}
                      tracePath={tracePath}
                      onNodeSelect={setSelectedNode}
                      onReplayPointChange={setReplayPoint}
                      onTraceNode={(nodeId) => {
                        void handleTrace(nodeId);
                      }}
                    />
                  ) : (
                    <EngineeringTable
                      rows={engineeringTableData?.rows ?? []}
                      loading={engineeringTableLoading}
                      error={engineeringTableError}
                      onTraceSignal={handleEngineeringTraceSignal}
                      onOpenControlLoop={handleEngineeringOpenControlLoop}
                      onOpenIOMapping={handleEngineeringOpenIOMapping}
                      onRowSelect={(row: EngineeringTableResponseRow) => {
                        setSelectedNode(row.tag);
                        if (activeTab === "Trace") {
                          void handleTrace(row.tag);
                        }
                      }}
                    />
                  )}
                </section>
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
                    activeTab={activeTab}
                    replayPoint={replayPoint}
                    selectedReplayTag={selectedReplayTag}
                    replayTrace={simulationTrace}
                    replayIssues={simulationIssues}
                    controlLoops={controlLoops}
                    controlLoopsLoading={isControlLoopsLoading}
                    controlLoopsError={controlLoopsError}
                    selectedControlLoopTag={selectedControlLoopTag}
                    selectedEquipment={selectedEquipment}
                    selectedNodeId={selectedNode}
                    tracePath={tracePath}
                    ioMappingRows={selectedNodeIOMappingRows}
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
                    onOpenVersionsWorkspace={() => {
                      setMonitoringPanelMode("versions");
                      setActiveBottomView("monitoring");
                      setActiveTab("Versions");
                    }}
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
                    onTabChange={setActiveTab}
                  />
                ) : null}
              </aside>
            </div>
          </Panel>

          <Separator className="panel-resize-handle panel-resize-handle-horizontal" />

          <Panel id="workspace-bottom" defaultSize="26%" minSize="14%" maxSize="58%">
            <BottomPanels
              activeView={activeBottomView}
              codePanelMode={codePanelMode}
              monitoringPanelMode={monitoringPanelMode}
              controlLogicCode={controlLogicCode}
              generatedSTCode={generatedLogic}
              generatedSTFiles={generatedSTFiles}
              selectedSTFilePath={selectedSTFilePath}
              onSelectSTFile={setSelectedSTFilePath}
              stDiagnosticsByFile={stDiagnosticsByFile}
              stJumpLocation={stJumpLocation}
              logicWarnings={logicWarnings}
              logicValidationIssues={logicValidationIssues}
              stVerificationData={stVerificationData}
              isVerifyingST={isVerifyingST}
              stVerificationFailedMessage={stVerificationFailedMessage}
              onSelectVerificationIssue={(issue: STVerificationIssueItem) => {
                if (issue.file) {
                  const normalizedFile = normalizeVerifierFilePath(issue.file);
                  setSelectedSTFilePath(normalizedFile);
                  setSTJumpLocation({
                    file: normalizedFile,
                    line: issue.line ?? 1,
                    column: issue.column ?? 1,
                    nonce: Date.now(),
                  });
                  setCodePanelMode("generated_st");
                  setActiveBottomView("logic");
                }
              }}
              ioMappingRows={ioMappingRows}
              selectedIOMappingTag={selectedIOMappingTag}
              onSelectIOMappingTag={setSelectedIOMappingTag}
              ioMappingSummary={ioMappingSummary}
              isGeneratingIOMapping={isGeneratingIOMapping}
              ioMappingFailedMessage={ioMappingFailedMessage}
              runtimeValidationData={runtimeValidationData}
              runtimeLoading={isRuntimeStateLoading}
              runtimeFailedMessage={runtimeFailedMessage}
              runtimeActionLoading={isRuntimeActionBusy}
              runtimeForceableInputs={runtimeForceableInputs}
              forcedTagNames={forcedTagNames}
              simulationValidationData={simulationValidationData}
              simulationFailedMessage={simulationFailedMessage}
              onRetryIOMapping={() => {
                void handleToolbarAction("generate_io_mapping");
              }}
              onGenerateIOMapping={() => {
                void handleToolbarAction("generate_io_mapping");
              }}
              onAutoAssignIOMappingChannels={handleAutoAssignIOMappingChannels}
              onExportIOMappingCsv={handleExportIOMappingCsv}
              onValidateIOMapping={handleValidateIOMapping}
              onRetrySTVerification={() => {
                void handleToolbarAction("generate_logic");
              }}
              onRetryRuntime={() => {
                void handleConfirmRuntimeDeploy();
              }}
              onRuntimeStart={() => {
                void handleRuntimeStart();
              }}
              onRuntimeStop={() => {
                void handleRuntimeStop();
              }}
              onRuntimeApplyForce={handleApplyRuntimeInputForce}
              onRuntimeClearForce={handleClearRuntimeInputForce}
              onRuntimeRefreshForceState={refreshRuntimeForceState}
              onRuntimeRunEvaluationCycle={handleRunRuntimeEvaluationCycle}
              onRetrySimulation={() => {
                void handleToolbarAction("replay_event");
              }}
              versions={versions}
              selectedVersion={selectedVersion}
              selectedVersionTags={selectedVersionTags}
              versionDiff={versionDiff}
              versionsLoading={versioningLoading}
              versionsError={versioningError}
              versionBusyAction={versionBusyAction}
              versionSettings={versioningSettings}
              onVersionSelect={(version) => {
                setSelectedVersion(version);
              }}
              onVersionToggleCompareSelection={handleVersionToggleCompareSelection}
              onVersionCreateSnapshot={() => {
                void handleVersionCreateSnapshot();
              }}
              onVersionLoadSnapshot={(version) => {
                void handleVersionLoadSnapshot(version);
              }}
              onVersionRollback={(version) => {
                void handleVersionRollback(version);
              }}
              onVersionCompare={() => {
                void handleVersionCompare();
              }}
              onVersionExport={(version) => {
                void handleVersionExport(version);
              }}
              onVersionSettingsChange={setVersioningSettings}
              showControlLogic={showLogic}
              isGeneratingST={pipelineStatuses.st_generation === "running" && activeAction === "generate_logic"}
              isGenerating={pipelineStatuses.logic_completion === "running"}
              onViewChange={(view) => {
                setActiveBottomView(view);
                if (view === "logic") {
                  setShowLogic(true);
                  if (!controlLogicCode.trim() && selectedProjectId) {
                    void getLogic(selectedProjectId)
                      .then((artifact) => {
                        const code = artifact.code || artifact.st_preview || "";
                        const validationIssues = (artifact.st_validation?.issues ?? []).map((issue) => {
                          const location = issue.line ? `${issue.file}:${issue.line}` : issue.file;
                          return `${location} [${issue.rule}] ${issue.message}`;
                        });
                        if (code.trim()) {
                          setControlLogicCode(code);
                          setGeneratedLogic(code);
                          const files = parseGeneratedLogicFiles(code);
                          setGeneratedSTFiles(files);
                          const mainFile = files.find((item) => item.path.toLowerCase() === "main.st");
                          setSelectedSTFilePath((current) => current || mainFile?.path || files[0]?.path || null);
                          setLogicWarnings(artifact.warnings ?? []);
                          setLogicValidationIssues(validationIssues);
                          setShowLogic(true);
                        }
                      })
                      .catch(() => {
                        setStatusText("No stored logic found for selected project yet.");
                      });
                  }
                }
              }}
            />
          </Panel>
        </Group>
      </div>
    </div>
  );
}
