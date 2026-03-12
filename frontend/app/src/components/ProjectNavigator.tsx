import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  Boxes,
  ChevronDown,
  ChevronRight,
  CircleDot,
  Database,
  Folder,
  FolderOpen,
  Gauge,
  Plus,
  SlidersHorizontal,
  Trash2,
} from "lucide-react";

type ProjectItem = {
  id: string;
  name: string;
};

type GraphNode = {
  id: string;
  node_type: string;
};

type ProjectNavigatorProps = {
  projects: ProjectItem[];
  graphNodes: GraphNode[];
  selectedProjectId: string;
  onCreateProject: () => void;
  onRequestDeleteProject: (projectId: string) => void;
  onSelectProject: (projectId: string) => void;
  selectedNode: string;
  onSelectNode: (nodeId: string) => void;
};

export default function ProjectNavigator({
  projects,
  graphNodes,
  selectedProjectId,
  onCreateProject,
  onRequestDeleteProject,
  onSelectProject,
  selectedNode,
  onSelectNode,
}: ProjectNavigatorProps) {
  const [projectsExpanded, setProjectsExpanded] = useState(true);
  const [equipmentExpanded, setEquipmentExpanded] = useState(true);
  const [groupExpanded, setGroupExpanded] = useState<Record<string, boolean>>({});

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
      { key: "sensor", label: "Sensors" },
    ];

    const groups = groupOrder
      .map((group) => ({ group: group.label, nodes: byType.get(group.key) ?? [] }))
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
    if (groupName === "Sensors") {
      return <Activity className="tree-group-icon" size={13} />;
    }
    return <Boxes className="tree-group-icon" size={13} />;
  };

  return (
    <div>
      <h3 className="panel-title">Project Navigator</h3>
      <div className="project-header-row">
        <button className="tree-parent-btn" onClick={() => setProjectsExpanded((value) => !value)} type="button">
          <span className="tree-arrow-icon">{projectsExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}</span>
          <span className="tree-group-icon-wrap">{projectsExpanded ? <FolderOpen size={13} /> : <Folder size={13} />}</span>
          <span className="tree-parent">Projects</span>
        </button>
        <button className="project-add-btn" onClick={onCreateProject} type="button">
          <Plus size={12} />
          <span>New</span>
        </button>
      </div>
      {projectsExpanded ? (
        <ul className="tree-items">
          {projects.map((project) => (
            <li key={project.id}>
              <div className={`project-row ${selectedProjectId === project.id ? "active" : ""}`}>
                <button className="project-item" onClick={() => onSelectProject(project.id)} type="button">
                  <Folder size={12} className="tree-node-icon" />
                  {project.name}
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
      ) : null}

      <ul className="tree-group">
        <li>
          <button className="tree-parent-btn subheading" onClick={() => setEquipmentExpanded((value) => !value)} type="button">
            <span className="tree-arrow-icon">{equipmentExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}</span>
            <span className="tree-group-icon-wrap">
              <Boxes size={13} />
            </span>
            <span className="tree-parent">Parsed Equipment</span>
          </button>
        </li>

        {equipmentExpanded && parsedGroups.length === 0 ? (
          <li>
            <div className="tree-parent tree-empty">No Parsed Nodes Yet</div>
          </li>
        ) : null}

        {equipmentExpanded
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
                  const isActive = selectedNode === node;
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
      </ul>
    </div>
  );
}