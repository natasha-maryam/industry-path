export type PanelStatus = "idle" | "running" | "success" | "failed" | "warning";

export type VerificationSeverity = "info" | "warning" | "error";

export type STGenerationPanelResponse = {
  project_id: string;
  run_id: string;
  generated_at: string;
  generator_version: string;
  file_name: string;
  language: "st";
  status: PanelStatus;
  rule_count: number;
  warnings: string[];
  st_code: string;
};

export type STVerificationCheck = {
  check_id: string;
  check_name: string;
  status: PanelStatus;
  severity: VerificationSeverity;
  message: string;
  line_number: number | null;
  suggestion: string | null;
};

export type STVerificationPanelResponse = {
  project_id: string;
  run_id: string;
  verified_at: string;
  overall_status: PanelStatus;
  checks_passed: number;
  checks_failed: number;
  checks_warning: number;
  checks: STVerificationCheck[];
};

export type IOMappingEntry = {
  mapping_id: string;
  source_tag: string;
  source_type: "ai" | "ao" | "di" | "do";
  plc_address: string;
  data_type: "bool" | "int" | "real" | "string";
  status: PanelStatus;
  confidence: number;
  notes: string | null;
};

export type IOMappingPanelResponse = {
  project_id: string;
  run_id: string;
  mapped_at: string;
  overall_status: PanelStatus;
  mapped_count: number;
  unmapped_count: number;
  coverage_percent: number;
  mappings: IOMappingEntry[];
};

export type RuntimeValidationCheck = {
  check_id: string;
  check_name: string;
  status: PanelStatus;
  expected_value: string;
  actual_value: string;
  tolerance: string | null;
  message: string;
};

export type RuntimeValidationPanelResponse = {
  project_id: string;
  run_id: string;
  validated_at: string;
  overall_status: PanelStatus;
  checks_passed: number;
  checks_failed: number;
  checks_warning: number;
  checks: RuntimeValidationCheck[];
};

export type SimulationScenarioResult = {
  scenario_id: string;
  scenario_name: string;
  status: PanelStatus;
  cycle_time_ms: number;
  duration_s: number;
  alarms_triggered: number;
  message: string;
};

export type SimulationValidationPanelResponse = {
  project_id: string;
  simulation_run_id: string;
  validated_at: string;
  overall_status: PanelStatus;
  scenarios_passed: number;
  scenarios_failed: number;
  scenarios_warning: number;
  scenarios: SimulationScenarioResult[];
};

export type VersionSnapshotArtifact = {
  artifact_type: "logic" | "graph" | "io_mapping" | "simulation" | "runtime";
  artifact_path: string;
  checksum_sha256: string;
};

export type VersionSnapshot = {
  snapshot_id: string;
  version_number: number;
  created_at: string;
  created_by: string;
  summary: string;
  status: PanelStatus;
  artifacts: VersionSnapshotArtifact[];
};

export type VersionHistoryPanelResponse = {
  project_id: string;
  current_version: number;
  total_snapshots: number;
  snapshots: VersionSnapshot[];
};