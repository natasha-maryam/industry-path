import { useEffect, useMemo, useState, type ComponentType } from "react";
import { Activity, AlertTriangle, Boxes, ChevronDown, ChevronRight, CircleDot, Cpu, Database, FileText, Folder, FolderOpen, Gauge, Network, Radar, Plus, SlidersHorizontal, Trash2 } from "lucide-react";
import type { WorkspaceModuleId } from "../types/workspace";

type ProjectItem = {
  id: string;
  name: string;
  industry?: string;
  status?: string;
};

type GraphNode = {
  id: string;
  node_type: string;
};

type NavigatorSelection = {
  type: "project" | "module" | "feature" | "node";
  id: string;
};

type ProjectNavigatorProps = {
  projects: ProjectItem[];
  graphNodes: GraphNode[];
  selectedProjectId: string;
  activeSelection: NavigatorSelection | null;
  onCreateProject: () => void;
  onRequestDeleteProject: (projectId: string) => void;
  onSelectProject: (projectId: string) => void;
  selectedNode: string;
  onSelectNode: (nodeId: string) => void;
  activeModule: WorkspaceModuleId;
  onSelectModule: (moduleId: WorkspaceModuleId) => void;
  activeFeature: "versions" | null;
  onSelectFeature: (feature: "versions") => void;
};

const WORKSPACE_MODULES: Array<{ id: WorkspaceModuleId; label: string; icon: ComponentType<{ size?: number; className?: string }> }> = [
  { id: "documents", label: "Documents", icon: FileText },
  { id: "plant_model", label: "Plant Model", icon: Network },
  { id: "control_loops", label: "Control Loops", icon: Boxes },
  { id: "control_logic", label: "Control Logic", icon: Cpu },
  { id: "io_mapping", label: "IO Mapping", icon: SlidersHorizontal },
  { id: "simulation", label: "Simulation", icon: Activity },
  { id: "runtime", label: "Runtime", icon: Radar },
  { id: "monitoring", label: "Monitoring", icon: Radar },
  { id: "diagnostics", label: "Diagnostics", icon: AlertTriangle },
];

const PROJECT_FEATURES: Array<{ id: "versions"; label: string; icon: ComponentType<{ size?: number; className?: string }> }> = [
  { id: "versions", label: "Versions", icon: Activity },
];

export default function ProjectNavigator({
  projects,
  graphNodes,
  selectedProjectId,
  activeSelection,
  onCreateProject,
  onRequestDeleteProject,
  onSelectProject,
  selectedNode,
  onSelectNode,
  activeModule,
  onSelectModule,
  activeFeature,
  onSelectFeature,
}: ProjectNavigatorProps) {
  const [projectsExpanded, setProjectsExpanded] = useState(true);
  const [workspaceExpanded, setWorkspaceExpanded] = useState(true);
  const [modulesExpanded, setModulesExpanded] = useState(true);
  const [featuresExpanded, setFeaturesExpanded] = useState(true);
  const [equipmentExpanded, setEquipmentExpanded] = useState(true);
  const [groupExpanded, setGroupExpanded] = useState<Record<string, boolean>>({});

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedProjectId) ?? null,
    [projects, selectedProjectId]
  );
  const hasSelectedProject = Boolean(selectedProject);

  const toHumanHeading = (value: string): string =>
    value
      .replace(/[_-]+/g, " ")
      .trim()
      .replace(/\s+/g, " ")
      .toLowerCase()
      .replace(/\b\w/g, (letter) => letter.toUpperCase());

  const parsedGroups = useMemo(() => {
    const byType = new Map<string, string[]>();
    for (const node of graphNodes) {
      const key = node.node_type.toLowerCase();
      const existing = byType.get(key) ?? [];
      existing.push(node.id);
      byType.set(key, existing);
    }

    const groupOrder: Array<{ key: string; label: string }> = [
      { key: "tank", label: "Tanks" },
      { key: "pump", label: "Pumps" },
      { key: "valve", label: "Valves" },
      { key: "blower", label: "Blowers" },
      { key: "instrument", label: "Instruments" },
      { key: "sensor", label: "Instruments" },
    ];

    const grouped = new Map<string, string[]>();
    for (const group of groupOrder) {
      const nodes = byType.get(group.key) ?? [];
      if (nodes.length === 0) {
        continue;
      }
      const existing = grouped.get(group.label) ?? [];
      grouped.set(group.label, [...existing, ...nodes]);
    }

    const groups = [...grouped.entries()]
      .map(([group, nodes]) => ({ group, nodes }))
      .filter((group) => group.nodes.length > 0);

    for (const [key, nodes] of byType.entries()) {
      if (groupOrder.some((group) => group.key === key)) {
        continue;
      }
      if (nodes.length > 0) {
        groups.push({ group: toHumanHeading(key), nodes });
      }
    }

    return groups;
  }, [graphNodes]);

  useEffect(() => {
    setGroupExpanded((previous) => {
      const next: Record<string, boolean> = {};
      for (const section of parsedGroups) {
        next[section.group] = previous[section.group] ?? true;
      }
      return next;
    });
  }, [parsedGroups]);

  const toggleGroup = (groupName: string): void => {
    setGroupExpanded((previous) => ({
      ...previous,
      [groupName]: !(previous[groupName] ?? true),
    }));
  };

  const groupIcon = (groupName: string) => {
    if (groupName === "Tanks") {
      return <Database className="tree-group-icon" size={13} />;
    }
    if (groupName === "Pumps") {
      return <Gauge className="tree-group-icon" size={13} />;
    }
    if (groupName === "Valves") {
      return <SlidersHorizontal className="tree-group-icon" size={13} />;
    }
    if (groupName === "Blowers") {
      return <Gauge className="tree-group-icon" size={13} />;
    }
    if (groupName === "Instruments") {
      return <Activity className="tree-group-icon" size={13} />;
    }
    return <Boxes className="tree-group-icon" size={13} />;
  };

  return (
    <div>
      <h3 className="panel-title">Projects</h3>

      <section className="navigator-section" aria-label="Project navigator">
        <div className="project-header-row">
          <button className="tree-parent-btn" onClick={() => setProjectsExpanded((value) => !value)} type="button">
            <span className="tree-arrow-icon">{projectsExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}</span>
            <span className="tree-group-icon-wrap">{projectsExpanded ? <FolderOpen size={13} /> : <Folder size={13} />}</span>
            <span className="tree-parent">Project Navigator</span>
          </button>
          <button className="project-add-btn" onClick={onCreateProject} type="button">
            <Plus size={12} />
            <span>New</span>
          </button>
        </div>

        {projectsExpanded ? (
          <>
            {projects.length > 0 ? (
              <ul className="tree-items project-list-items">
                {projects.map((project) => (
                  <li key={project.id}>
                    <div className={`project-row ${activeSelection?.type === "project" && activeSelection.id === project.id ? "active" : ""}`}>
                      <button
                        className="project-item"
                        onClick={() => {
                          onSelectProject(project.id);
                        }}
                        type="button"
                        aria-current={activeSelection?.type === "project" && activeSelection.id === project.id ? "page" : undefined}
                      >
                        <Folder size={12} className="tree-node-icon" />
                        <span>{project.name}</span>
                      </button>
                      <button
                        aria-label={`Delete ${project.name}`}
                        className="project-delete-btn"
                        onClick={(event) => {
                          event.stopPropagation();
                          onRequestDeleteProject(project.id);
                        }}
                        type="button"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="tree-parent tree-empty">No projects yet. Create one to start.</div>
            )}

            <div className="project-selector-wrap">
              <label className="project-selector-label" htmlFor="active-project-selector">
                Active Project
              </label>
              <select
                id="active-project-selector"
                className="project-selector-input"
                value={selectedProjectId}
                onChange={(event) => onSelectProject(event.target.value)}
                disabled={projects.length === 0}
              >
                <option value="">Select project</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>
          </>
        ) : null}
      </section>

      <section className="navigator-section" aria-label="Project workspace">
        <ul className="tree-group">
          <li>
            <button className="tree-parent-btn" onClick={() => setWorkspaceExpanded((value) => !value)} type="button">
              <span className="tree-arrow-icon">{workspaceExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}</span>
              <span className="tree-group-icon-wrap">
                <Boxes size={13} />
              </span>
              <span className="tree-parent">Project Workspace</span>
            </button>
          </li>

          {workspaceExpanded ? (
            <>
              <li>
                <button className="tree-parent-btn subheading" onClick={() => setModulesExpanded((value) => !value)} type="button">
                  <span className="tree-arrow-icon">{modulesExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}</span>
                  <span className="tree-group-icon-wrap">
                    <Boxes size={13} />
                  </span>
                  <span className="tree-parent">Workspace Modules</span>
                </button>
              </li>

              {modulesExpanded
                ? WORKSPACE_MODULES.map((module) => {
                    const Icon = module.icon;
                    return (
                      <li key={module.id}>
                        <button
                          className={`tree-item ${activeSelection?.type === "module" && activeSelection.id === module.id ? "active" : ""} ${!hasSelectedProject ? "disabled" : ""}`}
                          onClick={() => onSelectModule(module.id)}
                          type="button"
                          disabled={!hasSelectedProject}
                        >
                          <Icon size={11} className="tree-node-icon" />
                          {module.label}
                        </button>
                      </li>
                    );
                  })
                : null}

              <li>
                <button className="tree-parent-btn subheading" onClick={() => setFeaturesExpanded((value) => !value)} type="button">
                  <span className="tree-arrow-icon">{featuresExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}</span>
                  <span className="tree-group-icon-wrap">
                    <Cpu size={13} />
                  </span>
                  <span className="tree-parent">Project Features</span>
                </button>
              </li>

              {featuresExpanded
                ? PROJECT_FEATURES.map((feature) => {
                    const Icon = feature.icon;
                    return (
                      <li key={feature.id}>
                        <button
                          className={`tree-item ${activeSelection?.type === "feature" && activeSelection.id === feature.id ? "active" : ""} ${!hasSelectedProject ? "disabled" : ""}`}
                          onClick={() => onSelectFeature(feature.id)}
                          type="button"
                          disabled={!hasSelectedProject}
                        >
                          <Icon size={11} className="tree-node-icon" />
                          {feature.label}
                        </button>
                      </li>
                    );
                  })
                : null}

              <li>
                <button className="tree-parent-btn subheading" onClick={() => setEquipmentExpanded((value) => !value)} type="button">
                  <span className="tree-arrow-icon">{equipmentExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}</span>
                  <span className="tree-group-icon-wrap">
                    <Boxes size={13} />
                  </span>
                  <span className="tree-parent">Parsed Equipment</span>
                </button>
              </li>

              {equipmentExpanded && !hasSelectedProject ? (
                <li>
                  <div className="tree-parent tree-empty">Select a project to view parsed assets.</div>
                </li>
              ) : null}

              {equipmentExpanded && hasSelectedProject && parsedGroups.length === 0 ? (
                <li>
                  <div className="tree-parent tree-empty">No parsed equipment yet.</div>
                </li>
              ) : null}

              {equipmentExpanded && hasSelectedProject
                ? parsedGroups.map((section) => (
                    <li key={section.group}>
                      <button className="tree-parent-btn subheading" onClick={() => toggleGroup(section.group)} type="button">
                        <span className="tree-arrow-icon">
                          {groupExpanded[section.group] ?? true ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                        </span>
                        <span className="tree-group-icon-wrap">{groupIcon(section.group)}</span>
                        <span className="tree-parent">{section.group}</span>
                      </button>
                      {groupExpanded[section.group] ?? true ? (
                        <ul className="tree-items">
                          {section.nodes.map((node) => {
                            const isActive = activeSelection?.type === "node" && activeSelection.id === node;
                            return (
                              <li key={node}>
                                <button
                                  className={`tree-item ${isActive ? "active" : ""}`}
                                  onClick={() => onSelectNode(node)}
                                  type="button"
                                >
                                  <CircleDot size={11} className="tree-node-icon" />
                                  {node}
                                </button>
                              </li>
                            );
                          })}
                        </ul>
                      ) : null}
                    </li>
                  ))
                : null}
            </>
          ) : null}
        </ul>
      </section>
    </div>
  );
}