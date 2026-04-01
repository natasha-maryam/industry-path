import axios from "axios";
import type {
  RollbackResponse,
  VersionCommitPayload,
  VersionDiffResponse,
  VersionRecord,
  VersionRollbackPayload,
  VersionSnapshotPayload,
} from "../types/versioning";
import { API_BASE } from "../config/api";

const versioningApi = axios.create({
  baseURL: API_BASE,
});

type VersionHistoryResponse = {
  project_id: string;
  records: Array<Record<string, unknown>>;
};

const inferArtifactStatus = (path: unknown): "available" | "missing" => {
  if (typeof path !== "string" || path.trim().length === 0) {
    return "missing";
  }
  return "available";
};

const toVersionRecord = (record: Record<string, unknown>): VersionRecord => ({
  id: String(record.id ?? ""),
  project_id: String(record.project_id ?? ""),
  version_tag: String(record.version_tag ?? ""),
  commit_hash: String(record.commit_hash ?? ""),
  trigger_source: String(record.trigger_source ?? "Unknown Trigger"),
  summary: String(record.summary ?? ""),
  plant_graph_path: typeof record.plant_graph_path === "string" ? record.plant_graph_path : null,
  logic_path: typeof record.logic_path === "string" ? record.logic_path : null,
  io_mapping_path: typeof record.io_mapping_path === "string" ? record.io_mapping_path : null,
  simulation_results_path: typeof record.simulation_results_path === "string" ? record.simulation_results_path : null,
  runtime_state_path: typeof record.runtime_state_path === "string" ? record.runtime_state_path : null,
  created_at: String(record.created_at ?? new Date().toISOString()),
  created_by: typeof record.created_by === "string" ? record.created_by : "system",
  deployment_tag: typeof record.deployment_tag === "string" ? record.deployment_tag : null,
  rollback_available: Boolean(record.rollback_available ?? true),
  artifact_status: {
    plant_graph: inferArtifactStatus(record.plant_graph_path),
    control_logic: inferArtifactStatus(record.logic_path),
    io_mapping: inferArtifactStatus(record.io_mapping_path),
    simulation: inferArtifactStatus(record.simulation_results_path),
    runtime: inferArtifactStatus(record.runtime_state_path),
  },
});

export async function getVersionHistory(projectId: string): Promise<VersionRecord[]> {
  const response = await versioningApi.get<VersionHistoryResponse>("/versions/history", {
    params: { project_id: projectId },
  });
  const records = response.data.records ?? [];
  return records.map((item) => toVersionRecord(item));
}

export async function createVersionCommit(payload: VersionCommitPayload): Promise<VersionRecord> {
  const response = await versioningApi.post<Record<string, unknown>>("/versions/commit", payload);
  return toVersionRecord(response.data);
}

export async function createSnapshot(payload: VersionSnapshotPayload): Promise<VersionRecord> {
  const response = await versioningApi.post<Record<string, unknown>>("/versions/snapshot", payload);
  return toVersionRecord(response.data);
}

export async function rollbackVersion(payload: VersionRollbackPayload): Promise<RollbackResponse> {
  const response = await versioningApi.post<RollbackResponse>("/versions/rollback", payload);
  return response.data;
}

export async function diffVersions(projectId: string, versionA: string, versionB: string): Promise<VersionDiffResponse> {
  const response = await versioningApi.get<VersionDiffResponse>(`/versions/${encodeURIComponent(versionB)}`, {
    params: {
      project_id: projectId,
      compare_to: versionA,
    },
  });
  return response.data;
}

export async function getVersionById(projectId: string, versionId: string): Promise<VersionRecord> {
  const response = await versioningApi.get<Record<string, unknown>>(`/versions/${encodeURIComponent(versionId)}`, {
    params: { project_id: projectId },
  });
  return toVersionRecord(response.data);
}

export async function exportVersion(projectId: string, versionId: string): Promise<Blob> {
  const record = await getVersionById(projectId, versionId);
  const payload = JSON.stringify(record, null, 2);
  return new Blob([payload], { type: "application/json" });
}
