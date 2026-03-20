import { createContext, useContext, useMemo, useState, type PropsWithChildren } from "react";
import type { GraphEdge, GraphNode } from "../services/api";

type WorkspaceContextValue = {
  activeProjectId: string;
  setActiveProjectId: (projectId: string) => void;
  plantGraph: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
  setPlantGraph: (graph: { nodes: GraphNode[]; edges: GraphEdge[] }) => void;
};

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export function WorkspaceProvider({ children }: PropsWithChildren) {
  const [activeProjectId, setActiveProjectId] = useState<string>("");
  const [plantGraph, setPlantGraph] = useState<{ nodes: GraphNode[]; edges: GraphEdge[] }>({
    nodes: [],
    edges: [],
  });

  const value = useMemo<WorkspaceContextValue>(
    () => ({
      activeProjectId,
      setActiveProjectId,
      plantGraph,
      setPlantGraph,
    }),
    [activeProjectId, plantGraph]
  );

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspaceContext(): WorkspaceContextValue {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error("useWorkspaceContext must be used within a WorkspaceProvider");
  }
  return context;
}
