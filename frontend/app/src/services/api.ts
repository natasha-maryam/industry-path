import axios from "axios";

export type Project = {
  id: string;
  name: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type GraphNode = {
  id: string;
  label: string;
  node_type: string;
  status: string;
  process_unit?: string | null;
  cluster_id?: string | null;
  cluster_order?: number | null;
  node_rank?: number | null;
};

export type GraphEdge = {
  id: string;
  source: string;
  target: string;
  edge_type: string;
  edge_class?: "process" | "monitoring";
  line_style?: "solid" | "dashed";
};

export type PlantGraph = {
  project_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
};

export type TraceResponse = {
  project_id: string;
  node_id: string;
  path: string[];
};

export type LogicArtifact = {
  project_id: string;
  file_name: string;
  code: string;
};

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api",
});

export async function listProjects(): Promise<Project[]> {
  const response = await api.get<Project[]>("/projects");
  return response.data;
}

export async function createProject(payload: { name: string; description?: string; status?: string }): Promise<Project> {
  const response = await api.post<Project>("/projects", payload);
  return response.data;
}

export async function updateProject(
  projectId: string,
  payload: { name?: string; description?: string; status?: string }
): Promise<Project> {
  const response = await api.put<Project>(`/projects/${projectId}`, payload);
  return response.data;
}

export async function deleteProject(projectId: string): Promise<void> {
  await api.delete(`/projects/${projectId}`);
}

export async function parseProject(projectId: string, fileIds: string[] = []): Promise<Record<string, unknown>> {
  const response = await api.post<Record<string, unknown>>(`/projects/${projectId}/parse`, { file_ids: fileIds });
  return response.data;
}

export async function uploadDocuments(
  projectId: string,
  files: File[],
  documentTypes: Array<"pid_pdf" | "control_narrative" | "unknown_document"> = []
): Promise<Record<string, unknown>> {
  const formData = new FormData();
  for (const [index, file] of files.entries()) {
    formData.append("files", file);
    if (documentTypes[index]) {
      formData.append("document_types", documentTypes[index]);
    }
  }

  const response = await api.post<Record<string, unknown>>(`/projects/${projectId}/upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function getGraph(projectId: string): Promise<PlantGraph> {
  const response = await api.get<PlantGraph>(`/projects/${projectId}/graph`);
  return response.data;
}

export async function getTrace(projectId: string, nodeId: string): Promise<TraceResponse> {
  const response = await api.get<TraceResponse>(`/projects/${projectId}/trace/${nodeId}`);
  return response.data;
}

export async function generateLogic(projectId: string, strategy = "default"): Promise<LogicArtifact> {
  const response = await api.post<LogicArtifact>(`/projects/${projectId}/logic/generate`, { strategy });
  return response.data;
}

export async function runSimulation(projectId: string): Promise<Record<string, unknown>> {
  const response = await api.post<Record<string, unknown>>(`/projects/${projectId}/simulation/run`);
  return response.data;
}

export async function deployProject(projectId: string): Promise<Record<string, unknown>> {
  const response = await api.post<Record<string, unknown>>(`/projects/${projectId}/deploy`);
  return response.data;
}

export async function getMonitoring(projectId: string): Promise<Record<string, unknown>> {
  const response = await api.get<Record<string, unknown>>(`/projects/${projectId}/monitoring/summary`);
  return response.data;
}

export async function getReplay(projectId: string): Promise<Record<string, unknown>> {
  const response = await api.get<Record<string, unknown>>(`/projects/${projectId}/replay`);
  return response.data;
}
