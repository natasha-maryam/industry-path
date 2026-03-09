import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Cog,
  Cpu,
  FileCog,
  FolderPlus,
  LoaderCircle,
  Rocket,
  RotateCcw,
  Trash2,
  Upload,
} from "lucide-react";
import { Toaster, toast } from "react-hot-toast";
import BottomPanels from "../components/BottomPanels";
import CommandBar, { type ToolbarAction } from "../components/CommandBar";
import DetailsPanel, { type RightTab } from "../components/DetailsPanel";
import GraphWorkspace from "../components/GraphWorkspace";
import ProjectNavigator from "../components/ProjectNavigator";
import {
  createProject,
  deleteProject,
  deployProject,
  generateLogic,
  getGraph,
  getMonitoring,
  getReplay,
  getTrace,
  listProjects,
  parseProject,
  runSimulation,
  uploadDocuments,
  type GraphEdge,
  type GraphNode,
  type Project,
} from "../services/api";
import "../styles/dashboard.css";

type EquipmentType = "Tank" | "Pump" | "Sensor" | "Valve";
type BottomView = "simulation" | "monitoring" | "logic";

type Equipment = {
  id: string;
  type: EquipmentType;
  status: string;
  motor?: string;
  signals: string[];
  logic: string;
};

const EMPTY_EQUIPMENT: Equipment = {
  id: "N/A",
  type: "Sensor",
  status: "unknown",
  motor: "N/A",
  signals: [],
  logic: "N/A",
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

export default function Dashboard() {
  const [activeAction, setActiveAction] = useState<ToolbarAction>("upload");
  const [selectedNode, setSelectedNode] = useState<string>("");
  const [activeTab, setActiveTab] = useState<RightTab>("Details");
  const [activeBottomView, setActiveBottomView] = useState<BottomView>("simulation");
  const [tracePath, setTracePath] = useState<string[]>([]);
  const [replayMode, setReplayMode] = useState<boolean>(false);
  const [replayPoint, setReplayPoint] = useState<number>(64);
  const [showLogic, setShowLogic] = useState<boolean>(false);
  const [generatedLogic, setGeneratedLogic] = useState<string>("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [graphEdges, setGraphEdges] = useState<GraphEdge[]>([]);
  const [simulationMetrics, setSimulationMetrics] = useState<Record<string, unknown>>({});
  const [monitoringSummary, setMonitoringSummary] = useState<Record<string, unknown> | null>(null);
  const [statusText, setStatusText] = useState<string>("Loading projects...");
  const [selectedUploadFiles, setSelectedUploadFiles] = useState<string[]>([]);
  const [isParsing, setIsParsing] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [showCreateProjectModal, setShowCreateProjectModal] = useState<boolean>(false);
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);
  const [projectForm, setProjectForm] = useState<{ name: string; description: string; status: "draft" | "active" | "archived" }>({
    name: "",
    description: "",
    status: "draft",
  });
  const uploadInputRef = useRef<HTMLInputElement | null>(null);

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
      signals: [],
      logic: "N/A",
    };
  }, [graphNodes, selectedNode]);

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
      setSelectedNode("");
      return;
    }

    const loadGraph = async (): Promise<void> => {
      try {
        const graph = await getGraph(selectedProjectId);
        setGraphNodes(graph.nodes);
        setGraphEdges(graph.edges);
        setSelectedNode(graph.nodes[0]?.id ?? "");
      } catch {
        setStatusText("Graph endpoint unavailable for selected project.");
      }
    };

    void loadGraph();
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
        setStatusText("Parsing batch in progress. Combining P&ID and control narrative...");
        await parseProject(selectedProjectId);
        const graph = await getGraph(selectedProjectId);
        setGraphNodes(graph.nodes);
        setGraphEdges(graph.edges);
        setStatusText("Project parse complete.");
        toast.success("Parse batch completed", {
          className: "industrial-toast",
          icon: <Cpu size={14} className="toast-icon" />,
        });
        setIsParsing(false);
      }

      if (action === "generate") {
        const artifact = await generateLogic(selectedProjectId);
        setGeneratedLogic(artifact.code);
        setShowLogic(true);
        setActiveBottomView("logic");
        setStatusText("Control logic generated and stored in project workspace.");
        toast.success("Control logic generated", {
          className: "industrial-toast",
          icon: <FileCog size={14} className="toast-icon" />,
        });
      }

      if (action === "simulate") {
        const simulation = await runSimulation(selectedProjectId);
        const metrics = simulation.metrics;
        setSimulationMetrics(typeof metrics === "object" && metrics ? (metrics as Record<string, unknown>) : {});
        setActiveBottomView("simulation");
        setStatusText("Simulation started for active project.");
        toast.success("Simulation run started", {
          className: "industrial-toast",
          icon: <Cog size={14} className="toast-icon" />,
        });
      }

      if (action === "deploy") {
        await deployProject(selectedProjectId);
        setStatusText("Deploy job accepted for active project.");
        toast.success("Deploy request accepted", {
          className: "industrial-toast",
          icon: <Rocket size={14} className="toast-icon" />,
        });
      }

      if (action === "monitor") {
        const summary = await getMonitoring(selectedProjectId);
        setMonitoringSummary(summary);
        const summarySimulation = summary.simulation;
        if (typeof summarySimulation === "object" && summarySimulation) {
          setSimulationMetrics(summarySimulation as Record<string, unknown>);
        }
        setActiveBottomView("monitoring");
        setStatusText("Monitoring summary refreshed for active project.");
        toast.success("Monitoring refreshed", {
          className: "industrial-toast",
          icon: <Activity size={14} className="toast-icon" />,
        });
      }

      if (action === "replay") {
        const replay = await getReplay(selectedProjectId);
        const timeline = replay.timeline;
        if (Array.isArray(timeline) && timeline.length > 0) {
          const latest = timeline[timeline.length - 1];
          if (typeof latest === "object" && latest) {
            setSimulationMetrics(latest as Record<string, unknown>);
          }
        }
        setReplayMode((value) => !value);
        setActiveTab("Replay");
        setStatusText("Replay dataset loaded for active project.");
        toast.success("Replay dataset loaded", {
          className: "industrial-toast",
          icon: <RotateCcw size={14} className="toast-icon" />,
        });
      }
    } catch {
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
        loadingAction={isParsing ? "parse" : isUploading ? "upload" : null}
        replayMode={replayMode}
        showLogic={showLogic}
        onAction={(action) => {
          void handleToolbarAction(action);
        }}
        onToggleLogic={() => {
          setShowLogic((value) => !value);
          setActiveBottomView("logic");
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

      <div className="main-shell">
        <aside className="left-panel">
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
        </aside>

        <section className="graph-shell">
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
        </section>

        <aside className="right-panel">
          <DetailsPanel
            activeTab={activeTab}
            replayPoint={replayPoint}
            selectedEquipment={selectedEquipment}
            tracePath={tracePath}
            onTabChange={setActiveTab}
          />
        </aside>
      </div>

      <BottomPanels
        activeView={activeBottomView}
        generatedLogic={generatedLogic}
        simulationMetrics={simulationMetrics}
        monitoringSummary={monitoringSummary ?? undefined}
        showLogic={showLogic}
        onViewChange={setActiveBottomView}
      />
    </div>
  );
}
