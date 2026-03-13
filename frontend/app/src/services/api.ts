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
  equipment_type?: string | null;
  signal_type?: string | null;
  instrument_role?: string | null;
  control_role?: string | null;
  power_rating?: string | null;
  connected_to?: string[];
  controls?: string[];
  measures?: string[];
  control_path?: string[];
  signals?: string[];
  metadata?: Record<string, unknown>;
  metadata_confidence?: Record<string, number>;
};

export type GraphEdge = {
  id: string;
  source: string;
  target: string;
  edge_type: string;
  edge_class?: "process" | "monitoring";
  line_style?: "solid" | "dashed" | "dotted";
  edge_label?: string | null;
  semantic_kind?: string | null;
  process_flow_direction?: string | null;
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

export type ControlRule = {
  id: string;
  rule_group?: string;
  rule_type: string;
  display_text: string;
  source_tag: string | null;
  source_type?: string | null;
  condition_kind?: string | null;
  operator: string | null;
  threshold: string | null;
  threshold_name?: string | null;
  action: string;
  target_tag: string | null;
  target_type?: string | null;
  secondary_target_tag?: string | null;
  mode?: string | null;
  priority?: number;
  confidence: number;
  renderable?: boolean;
  unresolved_tokens?: string[];
  comments?: string[];
  source_page: number | null;
  section_heading: string | null;
  st_preview: string;
};

export type RejectedRuleCandidate = {
  candidate_id: string;
  rule_type: string;
  source_sentence: string;
  section_heading: string | null;
  source_page: number | null;
  reason: string;
};

export type LogicArtifact = {
  project_id: string;
  file_name: string;
  code: string;
  st_preview: string;
  run_id: string;
  project_version?: number | null;
  generator_version?: string | null;
  rules_count: number;
  warnings_count?: number;
  rules: ControlRule[];
  structured_rules: ControlRule[];
  final_rendered_rules?: ControlRule[];
  symbolic_rendered_rules?: ControlRule[];
  groups: Record<string, ControlRule[]>;
  rejected_candidates: RejectedRuleCandidate[];
  rejected_rules?: RejectedRuleCandidate[];
  warnings: string[];
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

export async function getLogic(projectId: string): Promise<LogicArtifact> {
  const response = await api.get<LogicArtifact>(`/projects/${projectId}/logic`);
  return response.data;
}

export async function getLogicRule(projectId: string, ruleId: string): Promise<ControlRule> {
  const response = await api.get<ControlRule>(`/projects/${projectId}/logic/rules/${ruleId}`);
  return response.data;
}

export async function getLogicRun(projectId: string, runId: string): Promise<LogicArtifact> {
  const response = await api.get<LogicArtifact>(`/projects/${projectId}/logic/runs/${runId}`);
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
