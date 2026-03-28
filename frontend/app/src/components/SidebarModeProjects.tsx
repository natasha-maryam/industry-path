import type { WorkspaceModuleId } from "../types/workspace";
import ProjectNavigator from "./ProjectNavigator";

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

type ProjectFeatureId = "versions";

type NavigatorSelection = {
  type: "project" | "module" | "feature" | "node";
  id: string;
};

type SidebarModeProjectsProps = {
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
  activeFeature: ProjectFeatureId | null;
  onSelectFeature: (feature: ProjectFeatureId) => void;
};

export default function SidebarModeProjects(props: SidebarModeProjectsProps) {
  return <ProjectNavigator {...props} />;
}
