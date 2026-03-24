export type ArtifactStatus = "available" | "missing" | "unknown";

export type VersionRecord = {
  id: string;
  project_id: string;
  version_tag: string;
  commit_hash: string;
  trigger_source: string;
  summary: string;
  plant_graph_path?: string | null;
  logic_path?: string | null;
  io_mapping_path?: string | null;
  simulation_results_path?: string | null;
  runtime_state_path?: string | null;
  created_at: string;
  created_by?: string | null;
  deployment_tag?: string | null;
  rollback_available: boolean;
  artifact_status: {
    plant_graph: ArtifactStatus;
    control_logic: ArtifactStatus;
    io_mapping: ArtifactStatus;
    simulation: ArtifactStatus;
    runtime: ArtifactStatus;
  };
};

export type SnapshotRecord = VersionRecord;

export type VersionDiffResponse = {
  project_id: string;
  version_a: string;
  version_b: string;
  logic_diff: Record<string, string>;
  metadata_diff: Record<string, { from: unknown; to: unknown }>;
};

export type RollbackResponse = {
  project_id: string;
  rolled_back_to: string;
  restored_files: string[];
  rollback_commit: {
    status: string;
    project_id: string;
    version_tag: string;
    commit_hash: string;
    snapshot_path: string;
    trigger_source: string;
    summary?: string;
    artifact_status?: Record<string, string>;
    metadata_id?: string;
  };
};

export type VersionCommitPayload = {
  project_id: string;
  trigger_source: string;
  summary?: string;
};

export type VersionSnapshotPayload = VersionCommitPayload;

export type VersionRollbackPayload = {
  project_id: string;
  version_tag: string;
};
