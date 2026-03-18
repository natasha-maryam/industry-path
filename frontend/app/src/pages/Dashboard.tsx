import { useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Cpu,
  FileCog,
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
import PlantGraphTable from "../components/PlantGraphTable";
import ProjectNavigator from "../components/ProjectNavigator";
import type { RuntimeValidationPanelData } from "../components/RuntimeValidationPanel";
import SnapshotManagerModal, { type SnapshotRecord } from "../components/SnapshotManagerModal";
import type { STVerificationIssueItem } from "../components/STVerificationPanel";
import {
  applySnapshotTrigger,
  applyRuntimeInputForce,
  canRunStage,
  clearRuntimeInputForce,
  createVersionSnapshotWithRetry,
  createProject,
  createInitialPipelineStatuses,
  deleteProject,
  deployRuntimeControlWithRetry,
  detectControlLoops,
  exportGeneratedLogicWithRetry,
  getRuntimeTags,
  generateLogic,
  generateIOMappingWithRetry,
  getLatestIOMapping,
  getRuntimeDiagnostics,
  getRuntimeForcedInputs,
  getSimulationAnalysis,
  getSimulationTrace,
  getMissingStagePrerequisites,
  getLogic,
  getPlantSignals,
  getGraph,
  getTrace,
  listProjects,
  parseProject,
  runSimulation,
  runRuntimeEvaluationCycle,
  startRuntimeControl,
  stopRuntimeControl,
  uploadDocuments,
  verifySTWorkspaceWithRetry,
  type GraphEdge,
  type GraphNode,
  type IOMappingIssue,
  type IOMappingSummaryByType,
  type IOMappingTableRow,
  type PipelineStageKey,
  type RuntimeControlDeployResponse,
  type RuntimeEvaluationCycle,
  type RuntimeInputCatalogItem,
  type RuntimeSignalType,
  type SimulationTraceIssue,
  type SimulationTracePoint,
  type SimulationValidationPanelResponse,
  type DiscoveredControlLoop,
  type STWorkspaceVerificationResponse,
  type PipelineStageStatusMap,
  type PlantSignalRow,
  type Project,
} from "../services/api";
import "../styles/dashboard.css";

type EquipmentType = "Tank" | "Pump" | "Sensor" | "Valve";
type BottomView = "simulation" | "monitoring" | "logic";
type CodePanelMode = "control_logic" | "generated_st" | "verification";
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
  const [activeAction, setActiveAction] = useState<ToolbarAction>("upload");
  const [selectedNode, setSelectedNode] = useState<string>("");
  const [activeTab, setActiveTab] = useState<RightTab>("Details");
  const [activeBottomView, setActiveBottomView] = useState<BottomView>("simulation");
  const [codePanelMode, setCodePanelMode] = useState<CodePanelMode>("control_logic");
  const [monitoringPanelMode, setMonitoringPanelMode] = useState<MonitoringPanelMode>("io_mapping");
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
  const [ioMappingFailedMessage, setIOMappingFailedMessage] = useState<string | null>(null);
  const [pipelineStatuses, setPipelineStatuses] = useState<PipelineStageStatusMap>(() => createInitialPipelineStatuses());
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [graphEdges, setGraphEdges] = useState<GraphEdge[]>([]);
  const [graphWorkspaceView, setGraphWorkspaceView] = useState<"graph" | "table">("graph");
  const [plantSignalRows, setPlantSignalRows] = useState<PlantSignalRow[]>([]);
  const [runtimeValidationData, setRuntimeValidationData] = useState<RuntimeValidationPanelData | null>(null);
  const [runtimeFailedMessage, setRuntimeFailedMessage] = useState<string | null>(null);
  const [isRuntimeActionBusy, setIsRuntimeActionBusy] = useState<boolean>(false);
  const [runtimeTelemetryTags, setRuntimeTelemetryTags] = useState<Record<string, unknown>>({});
  const [runtimeForceableInputs, setRuntimeForceableInputs] = useState<RuntimeInputCatalogItem[]>([]);
  const [forcedTagNames, setForcedTagNames] = useState<string[]>([]);
  const [runtimeDiagnostics, setRuntimeDiagnostics] = useState<RuntimeEvaluationCycle | null>(null);
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
  const [showCreateProjectModal, setShowCreateProjectModal] = useState<boolean>(false);
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);
  const [showSnapshotManagerModal, setShowSnapshotManagerModal] = useState<boolean>(false);
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
  const [snapshotRecords, setSnapshotRecords] = useState<SnapshotRecord[]>([]);
  const [isLoadingSnapshots, setIsLoadingSnapshots] = useState<boolean>(false);
  const [snapshotErrorMessage, setSnapshotErrorMessage] = useState<string | null>(null);
  const [projectForm, setProjectForm] = useState<{ name: string; description: string; status: "draft" | "active" | "archived" }>({
    name: "",
    description: "",
    status: "draft",
  });
  const uploadInputRef = useRef<HTMLInputElement | null>(null);
  const previousPipelineStatusesRef = useRef<PipelineStageStatusMap>(pipelineStatuses);

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
      setActiveTab("Versions");
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

  const ensurePrerequisites = (stage: PipelineStageKey): boolean => {
    if (canRunStage(pipelineStatuses, stage)) {
      return true;
    }

    const missingStages = getMissingStagePrerequisites(pipelineStatuses, stage);
    const missingLabels = missingStages.map((missingStage) => PIPELINE_STAGE_LABELS[missingStage]).join(", ");
    const blockedLabel = PIPELINE_STAGE_LABELS[stage];
    setStatusText(`${blockedLabel} blocked. Complete: ${missingLabels}.`);
    toast.error(`${blockedLabel} blocked: ${missingLabels}`, {
      className: "industrial-toast industrial-toast-error",
      icon: <AlertTriangle size={14} className="toast-icon toast-icon-error" />,
    });
    return false;
  };

  const isActionBlockedByPrerequisites = (action: ToolbarAction): boolean => {
    if (!selectedProjectId) {
      return action !== "upload";
    }

    if (action === "generate_st") {
      return !canRunStage(pipelineStatuses, "st_generation");
    }
    if (action === "io_mapping") {
      return !canRunStage(pipelineStatuses, "io_mapping");
    }
    if (action === "verify_st") {
      return !canRunStage(pipelineStatuses, "st_verification");
    }
    if (action === "deploy") {
      return !canRunStage(pipelineStatuses, "runtime_validation");
    }
    if (action === "simulate") {
      return !canRunStage(pipelineStatuses, "simulation_validation");
    }
    if (action === "versions") {
      return !canRunStage(pipelineStatuses, "version_snapshot");
    }
    if (action === "export_logic") {
      return !canRunStage(pipelineStatuses, "st_generation");
    }

    return false;
  };

  const disabledActions = useMemo<Partial<Record<ToolbarAction, boolean>>>(
    () => ({
      upload: false,
      parse: isActionBlockedByPrerequisites("parse"),
      generate_st: isActionBlockedByPrerequisites("generate_st"),
      io_mapping: isActionBlockedByPrerequisites("io_mapping"),
      verify_st: isActionBlockedByPrerequisites("verify_st"),
      versions: isActionBlockedByPrerequisites("versions"),
      export_logic: isActionBlockedByPrerequisites("export_logic"),
      simulate: isActionBlockedByPrerequisites("simulate"),
      deploy: isActionBlockedByPrerequisites("deploy"),
    }),
    [pipelineStatuses, selectedProjectId]
  );

  const loadingAction = useMemo<ToolbarAction | null>(() => {
    if (isParsing) {
      return "parse";
    }
    if (isUploading) {
      return "upload";
    }
    if (pipelineStatuses.st_generation === "running" && !isExportingLogic) {
      return "generate_st";
    }
    if (pipelineStatuses.io_mapping === "running") {
      return "io_mapping";
    }
    if (pipelineStatuses.st_verification === "running") {
      return "verify_st";
    }
    if (pipelineStatuses.version_snapshot === "running") {
      return "versions";
    }
    if (isExportingLogic) {
      return "export_logic";
    }
    return null;
  }, [activeAction, isExportingLogic, isParsing, isUploading, pipelineStatuses.io_mapping, pipelineStatuses.st_generation, pipelineStatuses.st_verification, pipelineStatuses.version_snapshot]);

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

  const loadSnapshots = async (projectId: string | null): Promise<void> => {
    setIsLoadingSnapshots(true);
    setSnapshotErrorMessage(null);
    try {
      if (!projectId) {
        setSnapshotRecords([]);
        return;
      }

      const now = Date.now();
      setSnapshotRecords([
        {
          id: `${projectId}-snap-1`,
          name: "Pre-Deploy Snapshot",
          trigger_source: "deployment",
          timestamp: new Date(now - 5 * 60 * 1000).toISOString(),
        },
        {
          id: `${projectId}-snap-2`,
          name: "Post-Simulation Snapshot",
          trigger_source: "simulation",
          timestamp: new Date(now - 22 * 60 * 1000).toISOString(),
        },
        {
          id: `${projectId}-snap-3`,
          name: "Validation Auto Snapshot",
          trigger_source: "auto_validation",
          timestamp: new Date(now - 48 * 60 * 1000).toISOString(),
        },
      ]);
    } catch {
      setSnapshotErrorMessage("Snapshot list could not be loaded.");
      setSnapshotRecords([]);
    } finally {
      setIsLoadingSnapshots(false);
    }
  };

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
        const projectList = await listProjects();

        setProjects(projectList);
        if (projectList.length > 0) {
          setSelectedProjectId(projectList[0].id);
          setStatusText(`Active project: ${projectList[0].name}`);
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
      setGraphNodes([]);
      setGraphEdges([]);
      setPlantSignalRows([]);
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
      setSimulationValidationData(null);
      setSimulationFailedMessage(null);
      setSimulationTrace([]);
      setSimulationIssues([]);
      setSelectedReplayTag("");
      setPipelineStatuses(createInitialPipelineStatuses());
      setShowLogic(false);
      return;
    }

    setPipelineStatuses(createInitialPipelineStatuses());

    const loadGraph = async (): Promise<void> => {
      try {
        const graph = await getGraph(selectedProjectId);
        setGraphNodes(graph.nodes);
        setGraphEdges(graph.edges);
        setSelectedNode(graph.nodes[0]?.id ?? "");
        if (graph.nodes.length > 0 || graph.edges.length > 0) {
          updatePipelineStage("plant_graph", "success");
        }
      } catch {
        setStatusText("Graph endpoint unavailable for selected project.");
      }
    };

    const loadPlantSignals = async (): Promise<void> => {
      try {
        const rows = await getPlantSignals(selectedProjectId);
        setPlantSignalRows(rows);
      } catch {
        setPlantSignalRows([]);
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
    void loadPlantSignals();
    void loadLatestIOMapping();
    void loadLatestSimulationTrace();
  }, [selectedProjectId]);

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

    if (action === "upload") {
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
      if (action === "parse") {
        setIsParsing(true);
        updatePipelineStage("extraction", "running");
        setStatusText("Parsing batch in progress. Combining P&ID and control narrative...");
        await parseProject(selectedProjectId);
        const graph = await getGraph(selectedProjectId);
        const signals = await getPlantSignals(selectedProjectId);
        setGraphNodes(graph.nodes);
        setGraphEdges(graph.edges);
        setPlantSignalRows(signals);
        setPipelineStatuses((previous) =>
          withDerivedPipelineStatuses({
            ...previous,
            extraction: "success",
            normalization: "success",
            plant_graph: "success",
            control_loop_discovery: "success",
            engineering_validation: "success",
            logic_completion: "success",
          })
        );
        setStatusText("Project parse complete.");
        toast.success("Parse batch completed", {
          className: "industrial-toast",
          icon: <Cpu size={14} className="toast-icon" />,
        });
        setIsParsing(false);
      }

      if (action === "generate_st") {
        if (!ensurePrerequisites("st_generation")) {
          return;
        }
        updatePipelineStage("st_generation", "running");
        setStatusText("Generating ST code...");
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
          if (!hasGeneratedCode) {
            setSTVerificationData(null);
            setSTDiagnosticsByFile({});
            setSTVerificationFailedMessage("No generated ST files available for verification.");
          }
          setShowLogic(true);
          setCodePanelMode("generated_st");
          setActiveBottomView("logic");
          if (hasGeneratedCode) {
            setStatusText("ST code generated. Review files in Generated ST panel.");
          } else {
            setStatusText("ST generation failed. No generated ST files returned.");
          }
        } catch {
          updatePipelineStage("st_generation", "failed");
          throw new Error("ST generation failed");
        }
      }

      if (action === "io_mapping") {
        if (!ensurePrerequisites("io_mapping")) {
          return;
        }
        setIsGeneratingIOMapping(true);
        setIOMappingFailedMessage(null);
        updatePipelineStage("io_mapping", "running");
        setStatusText("Generating IO mapping...");
        try {
          const mappingResult = await generateIOMappingWithRetry(selectedProjectId, {
            maxAttempts: 3,
            initialDelayMs: 700,
            backoffFactor: 2,
          });
          setIOMappingRows(mappingResult.rows);
          setIOMappingIssues(mappingResult.issues ?? []);
          setSelectedIOMappingTag(null);
          setIOMappingSummary(mappingResult.summary);
          setMonitoringPanelMode("io_mapping");
          setActiveBottomView("monitoring");
          updatePipelineStage("io_mapping", "success");
          setStatusText(`IO mapping generated (${mappingResult.total} channel mappings).`);
        } catch {
          updatePipelineStage("io_mapping", "failed");
          setIOMappingRows([]);
          setIOMappingIssues([]);
          setSelectedIOMappingTag(null);
          setIOMappingSummary(null);
          setIOMappingFailedMessage("IO mapping generation failed after retries.");
          setStatusText("IO mapping generation failed. Ensure backend endpoint is available.");
        } finally {
          setIsGeneratingIOMapping(false);
        }
      }

      if (action === "verify_st") {
        if (!ensurePrerequisites("st_verification")) {
          return;
        }
        setCodePanelMode("verification");
        setActiveBottomView("logic");
        updatePipelineStage("st_verification", "running");
        await runSTVerification(selectedProjectId);
      }

      if (action === "versions") {
        if (!ensurePrerequisites("version_snapshot")) {
          return;
        }
        setMonitoringPanelMode("versions");
        setActiveBottomView("monitoring");
        updatePipelineStage("version_snapshot", "running");
        setStatusText("Creating version snapshot...");
        try {
          const snapshot = await createVersionSnapshotWithRetry(selectedProjectId, {
            maxAttempts: 3,
            initialDelayMs: 700,
            backoffFactor: 2,
          });
          updatePipelineStage("version_snapshot", "success");
          setStatusText(`Version snapshot created: ${snapshot.snapshot_id}`);
        } catch {
          updatePipelineStage("version_snapshot", "failed");
          setStatusText("Version snapshot failed. Ensure backend endpoint is available.");
        }
      }

      if (action === "export_logic") {
        if (!ensurePrerequisites("st_generation")) {
          return;
        }
        setIsExportingLogic(true);
        setStatusText("Exporting generated logic files...");
        try {
          const exportResult = await exportGeneratedLogicWithRetry(selectedProjectId, {
            maxAttempts: 3,
            initialDelayMs: 700,
            backoffFactor: 2,
          });
          setStatusText(`Export ready: ${exportResult.files.length} file(s) from ${exportResult.output_root}`);
          toast.success(`Logic export ready (${exportResult.files.length} files)`, {
            className: "industrial-toast",
            icon: <FileCog size={14} className="toast-icon" />,
          });
        } catch {
          setStatusText("Logic export failed. Ensure backend logic-files endpoint is available.");
          toast.error("Logic export failed", {
            className: "industrial-toast industrial-toast-error",
            icon: <AlertTriangle size={14} className="toast-icon toast-icon-error" />,
          });
        } finally {
          setIsExportingLogic(false);
        }
      }

      if (action === "simulate") {
        if (!ensurePrerequisites("simulation_validation")) {
          return;
        }
        setSimulationFailedMessage(null);
        setActiveBottomView("simulation");
        updatePipelineStage("simulation_validation", "running");
        const simulation = await runSimulation(selectedProjectId);
        await refreshSimulationTraceData(selectedProjectId);
        const metrics = simulation.metrics;
        const scenarioValue = typeof metrics === "object" && metrics && Array.isArray((metrics as { scenarios?: unknown[] }).scenarios)
          ? ((metrics as { scenarios?: SimulationValidationPanelResponse["scenarios"] }).scenarios ?? [])
          : [];
        const passed = scenarioValue.filter((item) => item.status === "success").length;
        const failed = scenarioValue.filter((item) => item.status === "failed").length;
        const warning = scenarioValue.filter((item) => item.status === "warning").length;
        setSimulationValidationData({
          project_id: selectedProjectId,
          simulation_run_id: `sim-${Date.now()}`,
          validated_at: new Date().toISOString(),
          overall_status: failed > 0 ? "failed" : warning > 0 ? "warning" : "success",
          scenarios_passed: passed,
          scenarios_failed: failed,
          scenarios_warning: warning,
          scenarios: scenarioValue,
        });
        updatePipelineStage("simulation_validation", "success");
        setStatusText("Simulation started for active project.");
      }

      if (action === "deploy") {
        if (!ensurePrerequisites("runtime_validation")) {
          return;
        }
        setMonitoringPanelMode("runtime");
        setActiveBottomView("monitoring");
        setStatusText("Deploying project runtime...");
        await handleConfirmRuntimeDeploy();
      }

    } catch {
      if (action === "generate_st") {
        updatePipelineStage("st_generation", "failed");
      }
      if (action === "io_mapping") {
        updatePipelineStage("io_mapping", "failed");
      }
      if (action === "versions") {
        updatePipelineStage("version_snapshot", "failed");
      }
      if (action === "deploy") {
        updatePipelineStage("runtime_validation", "failed");
        setRuntimeFailedMessage("Runtime validation failed for this deployment.");
      }
      if (action === "simulate") {
        updatePipelineStage("simulation_validation", "failed");
        setSimulationFailedMessage("Simulation validation failed for this run.");
      }
      setStatusText(`Action failed: ${action}. Ensure backend API is running.`);
      toast.error(`Action failed: ${action}`, {
        className: "industrial-toast industrial-toast-error",
        icon: <AlertTriangle size={14} className="toast-icon toast-icon-error" />,
      });
      if (action === "parse") {
        setIsParsing(false);
      }
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
        description: projectForm.description.trim() || undefined,
        status: projectForm.status,
      });
      setProjects((value) => [...value, created]);
      setSelectedProjectId(created.id);
      setShowCreateProjectModal(false);
      setProjectForm({ name: "", description: "", status: "draft" });
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
  const layoutStorage = typeof window === "undefined" ? undefined : window.localStorage;
  const workspaceRowsLayout = useDefaultLayout({ id: "crosslayerx-workspace-rows", storage: layoutStorage });

  const handleLeftPanelToggle = (): void => {
    setIsLeftPanelCollapsed((value) => !value);
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
      const result = await deployRuntimeControlWithRetry(
        { project_id: selectedProjectId },
        {
          maxAttempts: 2,
          initialDelayMs: 800,
          backoffFactor: 2,
        }
      );

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

  const openControlLoopModal = (loop: DiscoveredControlLoop): void => {
    const processTag = loop.process_unit || "";
    const controlPath = [loop.sensor_tag, processTag, loop.actuator_tag].filter((item) => item.length > 0).join(" -> ");
    setControlLoopModal({
      open: true,
      noLoop: false,
      loopId: loop.loop_tag,
      sensor: loop.sensor_tag,
      process: processTag,
      actuator: loop.actuator_tag,
      controlPath,
      source: loop.source_reference || "",
      confidence: typeof loop.confidence === "number" ? loop.confidence : null,
    });
  };

  const openNoLoopModal = (): void => {
    setControlLoopModal({
      open: true,
      noLoop: true,
      loopId: "",
      sensor: "",
      process: "",
      actuator: "",
      controlPath: "",
      source: "",
      confidence: null,
    });
  };

  const selectBestLoopForRow = (row: PlantSignalRow, loops: DiscoveredControlLoop[]): DiscoveredControlLoop | null => {
    const normalizedTag = (row.tag || "").trim().toUpperCase();
    const targetLoopIds = new Set<string>([
      ...(row.loop_ids ?? []).map((item) => (item || "").trim().toUpperCase()),
      ...((row.loop_id ? [row.loop_id] : []).map((item) => (item || "").trim().toUpperCase())),
    ]);

    const exactTagLoops = loops.filter((loop) => {
      const sensor = (loop.sensor_tag || "").trim().toUpperCase();
      const actuator = (loop.actuator_tag || "").trim().toUpperCase();
      return sensor === normalizedTag || actuator === normalizedTag;
    });
    if (exactTagLoops.length > 0) {
      return exactTagLoops[0];
    }

    if (targetLoopIds.size > 0) {
      const idMatched = loops.filter((loop) => targetLoopIds.has((loop.loop_tag || "").trim().toUpperCase()));
      if (idMatched.length > 0) {
        return idMatched[0];
      }
    }

    const processMatched = loops.filter((loop) => (loop.process_unit || "").trim().toUpperCase() === normalizedTag);
    if (processMatched.length > 0) {
      return processMatched[0];
    }

    return null;
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
          {selectedUploadFiles.length > 0 ? (
            <span className="selected-files-inline" title={selectedUploadFiles.join(", ")}>
              Selected: {selectedUploadFiles.join(", ")}
            </span>
          ) : null}
        </div>
        <strong>{currentProject ? `${currentProject.name} (${currentProject.id})` : "No project selected"}</strong>
      </div>

      <SnapshotManagerModal
        open={showSnapshotManagerModal}
        snapshots={snapshotRecords}
        loading={isLoadingSnapshots}
        errorMessage={snapshotErrorMessage}
        onClose={() => setShowSnapshotManagerModal(false)}
        onRetry={() => {
          void loadSnapshots(selectedProjectId || null);
        }}
        onLoadSnapshot={(snapshot) => {
          setStatusText(`Loaded snapshot: ${snapshot.name}`);
          toast.success(`Loaded snapshot ${snapshot.name}`, {
            className: "industrial-toast",
          });
        }}
        onRollback={(snapshot) => {
          setStatusText(`Rollback prepared from ${snapshot.name}`);
          toast.success(`Rollback prepared: ${snapshot.name}`, {
            className: "industrial-toast",
          });
        }}
        onCompare={(snapshot) => {
          setStatusText(`Compare opened for ${snapshot.name}`);
          toast.success(`Compare opened: ${snapshot.name}`, {
            className: "industrial-toast",
          });
        }}
        onExport={(snapshot) => {
          setStatusText(`Export started for ${snapshot.name}`);
          toast.success(`Export started: ${snapshot.name}`, {
            className: "industrial-toast",
          });
        }}
      />

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
              Description
            </label>
            <textarea
              id="project-description"
              className="modal-textarea"
              placeholder="Optional project description"
              value={projectForm.description}
              onChange={(event) => setProjectForm((value) => ({ ...value, description: event.target.value }))}
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
          void uploadDocuments(selectedProjectId, files, inferredTypes)
            .then(() => {
              setStatusText(`Uploaded ${files.length} file(s) to active project.`);
              toast.success(`Uploaded ${files.length} file(s)`, {
                className: "industrial-toast",
                icon: <Upload size={14} className="toast-icon" />,
              });
            })
            .catch(() => {
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
            <div className={`main-shell ${isLeftPanelCollapsed ? "left-collapsed" : ""} ${isRightPanelExpanded ? "right-expanded" : ""}`}>
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
                      onSelectProject={setSelectedProjectId}
                      selectedNode={selectedNode}
                      onSelectNode={setSelectedNode}
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
                    <PlantGraphTable
                      rows={plantSignalRows}
                      selectedTag={selectedNode}
                      onSelectTag={(tag) => {
                        setSelectedNode(tag);
                        if (activeTab === "Trace") {
                          void handleTrace(tag);
                        }
                      }}
                      onTraceSignal={(row) => {
                        void handleTrace(row.tag);
                        setIsRightPanelExpanded(true);
                      }}
                      onOpenControlLoop={(row) => {
                        setSelectedNode(row.tag);
                        setActiveTab("Trace");
                        setIsRightPanelExpanded(true);
                        if (!selectedProjectId) {
                          setStatusText("No active project selected.");
                          return;
                        }
                        if (!row.loop_id && (!row.loop_ids || row.loop_ids.length === 0)) {
                          openNoLoopModal();
                          setStatusText("No control loop detected.");
                          return;
                        }
                        void detectControlLoops(selectedProjectId)
                          .then((loops) => {
                            const selectedLoop = selectBestLoopForRow(row, loops);
                            if (!selectedLoop) {
                              openNoLoopModal();
                              setStatusText("No control loop detected.");
                              return;
                            }
                            setTracePath([selectedLoop.sensor_tag, selectedLoop.process_unit || "PROCESS", selectedLoop.actuator_tag]);
                            openControlLoopModal(selectedLoop);
                            setStatusText(`Opened ${selectedLoop.loop_tag} (${selectedLoop.control_strategy || "ON_OFF"}).`);
                          })
                          .catch(() => {
                            openNoLoopModal();
                            setStatusText("No control loop detected.");
                          });
                      }}
                      onOpenIOMapping={(row) => {
                        setActiveBottomView("monitoring");
                        setMonitoringPanelMode("io_mapping");
                        setActiveTab("IO Mapping");
                        setIsRightPanelExpanded(true);
                        setSelectedIOMappingTag(row.tag);
                        setStatusText(`IO mapping focused on ${row.tag}${row.signal_type ? ` (${row.signal_type})` : ""}.`);
                      }}
                    />
                  )}
                </section>
              </div>

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
                    selectedEquipment={selectedEquipment}
                    selectedNodeId={selectedNode}
                    tracePath={tracePath}
                    ioMappingRows={selectedNodeIOMappingRows}
                    ioMappingIssues={ioMappingIssues}
                    selectedIOMappingTag={selectedIOMappingTag}
                    runtimeTelemetryTags={runtimeTelemetryTags}
                    forcedTagNames={forcedTagNames}
                    runtimeDiagnostics={runtimeDiagnostics}
                    onSelectIOMappingTag={(tag) => {
                      setSelectedIOMappingTag(tag);
                      setActiveBottomView("monitoring");
                      setMonitoringPanelMode("io_mapping");
                      setActiveTab("IO Mapping");
                    }}
                    onReplayPointChange={setReplayPoint}
                    onSelectedReplayTagChange={setSelectedReplayTag}
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
              runtimeFailedMessage={runtimeFailedMessage}
              runtimeActionLoading={isRuntimeActionBusy}
              runtimeForceableInputs={runtimeForceableInputs}
              forcedTagNames={forcedTagNames}
              simulationValidationData={simulationValidationData}
              simulationFailedMessage={simulationFailedMessage}
              onRetryIOMapping={() => {
                void handleToolbarAction("io_mapping");
              }}
              onGenerateIOMapping={() => {
                void handleToolbarAction("io_mapping");
              }}
              onAutoAssignIOMappingChannels={handleAutoAssignIOMappingChannels}
              onExportIOMappingCsv={handleExportIOMappingCsv}
              onValidateIOMapping={handleValidateIOMapping}
              onRetrySTVerification={() => {
                void handleToolbarAction("verify_st");
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
                void handleToolbarAction("simulate");
              }}
              showControlLogic={showLogic}
              isGeneratingST={pipelineStatuses.st_generation === "running" && activeAction === "generate_st"}
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
