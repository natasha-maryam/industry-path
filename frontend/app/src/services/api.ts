import axios from "axios";
export * from "./pipelineStatus";
export * from "./panelContracts";
import type {
  CopilotAsyncRunResponse,
  CopilotJobStatusResponse,
  CopilotProviderResponse,
  CopilotRunResponse,
  RuntimeValidationPanelResponse,
} from "./panelContracts";

export type Project = {
  id: string;
  name: string;
  industry: string;
  description: string | null;
  plc_runtime: string;
  owner: string;
  status: string;
  active_version: number;
  created_at: string;
  updated_at: string;
};

export type ProjectDocument = {
  id: string;
  project_id: string;
  original_name: string;
  stored_name: string;
  file_type: string;
  document_type: string;
  file_path: string;
  file_size: number | null;
  upload_status: string;
  uploaded_at: string;
};

export type PLCExportVendor = "siemens" | "rockwell" | "codesys" | "beckhoff" | "openplc" | "generic_st";

export type ExportSourceMode = "live" | "version";

export type ExportReadinessLevel = "success" | "warning" | "error";

export type ExportReadinessItem = {
  key: string;
  label: string;
  ready: boolean;
  level: ExportReadinessLevel;
  message: string;
};

export type ExportReadinessSummary = {
  project_id: string;
  vendor: PLCExportVendor;
  source_mode: ExportSourceMode;
  source_version_id?: string | null;
  checks: ExportReadinessItem[];
  warnings: string[];
  errors: string[];
  export_allowed: boolean;
  export_blocked: boolean;
  deploy_allowed: boolean;
  deploy_blocked: boolean;
  unresolved_physical_io_tags: string[];
  unresolved_internal_tags: string[];
  auto_resolved_derived_tags: string[];
  unknown_unclassified_tags: string[];
  export_blockers: string[];
  deploy_blockers: string[];
  generated_at: string;
};

export type ExportDeploymentState = "not_ready" | "ready_to_deploy" | "deployment_in_progress" | "deployed" | "failed";

export type ExportDeploymentHandoffResponse = {
  project_id: string;
  export_id: string;
  target_runtime: string;
  state: ExportDeploymentState;
  message: string;
  logs: string[];
  errors: string[];
  package_path?: string | null;
};

export type PLCExportResponse = {
  export_id: string;
  project_id: string;
  project_name: string;
  vendor: PLCExportVendor;
  source_mode?: ExportSourceMode;
  source_version_id?: string | null;
  generated_at: string;
  files: string[];
  download_url: string;
  package_path?: string;
  artifact_name?: string;
  logic_block_count?: number;
  tag_count?: number;
  readiness?: ExportReadinessSummary | null;
  package_preview?: string[];
};

export type PIDChangeEntry = {
  tag: string;
  details: string;
};

export type PIDTopologyChange = {
  edge_id: string;
  source: string;
  target: string;
  edge_type: string;
  change: "added" | "removed";
};

export type PIDConflict = {
  incoming_tag: string;
  existing_tag: string;
  similarity: number;
  reason: string;
};

export type PIDReconcileSummary = {
  project_id: string;
  generated_at: string;
  similarity_threshold: number;
  new_devices: PIDChangeEntry[];
  deprecated_devices: PIDChangeEntry[];
  topology_changes: PIDTopologyChange[];
  possible_conflicts: PIDConflict[];
  apply_ready: boolean;
};

export type PIDApplyUpdateResponse = {
  project_id: string;
  applied_at: string;
  nodes_count: number;
  edges_count: number;
  validation_status: string;
  commit_triggered: boolean;
  summary: string;
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

export type PlantSignalRow = {
  tag: string;
  type: string;
  signal_type?: string | null;
  process_unit?: string | null;
  connected_to?: string[];
  control_targets?: string[];
  controlling_signals?: string[];
  control_path?: string[];
  loop_ids?: string[];
  loop_id?: string | null;
  relationship_types?: string[];
  confidence?: number | null;
  source?: string | null;
  source_details?: string[];
};

export type EngineeringTraceabilityItem = {
  source_type: string;
  source_id: string;
  excerpt?: string | null;
  confidence?: number | null;
};

export type EngineeringLinkReference = {
  tag: string;
  provenance: "explicit" | "inferred_from_topology" | "inferred_from_behavioral_chain" | "inferred_from_context" | "sentinel_fallback";
  inferred: boolean;
};

export type EngineeringTableWarning = {
  code: string;
  severity: string;
  message: string;
  affected_tags: string[];
};

export type EngineeringTableSummary = {
  total_rows: number;
  grounded_rows: number;
  inferred_rows: number;
  orphan_rows: number;
  controlled_rows: number;
  actuated_rows: number;
  avg_confidence: number;
  distinct_systems: number;
  distinct_document_sources: number;
};

export type EngineeringTableResponseRow = {
  id: string;
  tag: string;
  type: string;
  subtype: string | null;
  description: string | null;
  system: string | null;
  equipment: string | null;
  process_role: string | null;
  measures: string[];
  controls: string[];
  controlled_by: string[];
  signal_inputs: string[];
  signal_outputs: string[];
  upstream: string[];
  downstream: string[];
  upstream_links: EngineeringLinkReference[];
  downstream_links: EngineeringLinkReference[];
  has_inferred_upstream: boolean;
  has_inferred_downstream: boolean;
  flow_path: string[];
  current_value: string | null;
  state: string | null;
  setpoint: string | null;
  mode: string | null;
  unit: string | null;
  range_min: number | null;
  range_max: number | null;
  fail_state: string | null;
  power: string | null;
  document_source: string[];
  line_reference: string[];
  confidence: number;
  num_connections: number;
  num_upstream: number;
  num_downstream: number;
  control_chain: string[];
  flow_chain: string[];
  is_orphan: boolean;
  is_controlled: boolean;
  is_actuated: boolean;
  warnings: string[];
  grounded_fields: Record<string, unknown>;
  derived_fields: Record<string, unknown>;
  traceability: EngineeringTraceabilityItem[];
};

export type EngineeringTableResponse = {
  project_id: string;
  rows: EngineeringTableResponseRow[];
  warnings: EngineeringTableWarning[];
  summary: EngineeringTableSummary;
};

export type FinalValidationDiagnostics = {
  total_tags: number;
  rejected_tags: number;
  total_relationships: number;
  rejected_relationships: number;
  total_loops: number;
  rejected_loops: number;
  inferred_links: number;
  duplicate_edges_removed: number;
  duplicate_loops_removed: number;
};

export type FinalTagOutput = Omit<EngineeringTableResponseRow, "equipment"> & {
  equipment: string;
  upstream: string[];
  downstream: string[];
};

export type FinalLoopOutput = {
  loop_id: string;
  sensor: string;
  actuator: string;
  process: string;
  chain: string[];
  confidence: number;
  tuning_confidence: number;
  controller?: string | null;
  sensor_tag?: string;
  actuator_tag?: string;
  process_node?: string;
  controller_tag?: string | null;
  name?: string;
  support?: string[];
  support_count?: number;
  tuning?: Record<string, unknown>;
};

export type ParseUnifiedModel = Record<string, unknown> & {
  tags: FinalTagOutput[];
  tag_rows: FinalTagOutput[];
  rejected_tag_rows: EngineeringTableResponseRow[];
  control_loops: FinalLoopOutput[];
  rejected_control_loops: FinalLoopOutput[];
  final_validation_diagnostics: FinalValidationDiagnostics;
};

export type ParseBatchResponse = {
  project_id: string;
  parse_job_id: string;
  parse_batch_id: string;
  parsed_at: string;
  documents_seen: number;
  documents: string[];
  document_types: string[];
  entities_count: number;
  nodes_count: number;
  edges_count: number;
  final_validation_diagnostics: FinalValidationDiagnostics;
  unified_model: ParseUnifiedModel;
  warnings: string[];
  summary: string;
};

export type DeterministicBehaviorRow = EngineeringTableResponseRow & {
  behavior_card: string;
  behavior_summary: string;
  cause_chain: string[];
  effect_chain: string[];
  impact_summary: string;
  behavior_confidence: number;
  state_snapshot_id: string;
  why_trace_available: boolean;
};

export type DeterministicBehaviorRowsResponse = {
  snapshot_id: string;
  rows: DeterministicBehaviorRow[];
  count: number;
};

export type DeterministicWhyTraceStep = {
  depth: number;
  direction: "self" | "upstream" | "downstream";
  tag: string;
  edge_type: string | null;
  runtime_state: Record<string, unknown> | null;
  behavior_summary: string;
};

export type DeterministicWhyTraceDebugClassification = {
  selected_tag_role: string;
  selected_tag_role_reason?: string;
  classification_inputs?: {
    type?: string | null;
    subtype?: string | null;
    description?: string | null;
    equipment?: string | null;
    system?: string | null;
    process_role?: string | null;
  };
};

export type DeterministicWhyTraceDebugGraph = {
  selected_tag: string;
  incoming_edge_count: number;
  outgoing_edge_count: number;
  normalized_upstream_tags: string[];
  normalized_downstream_tags: string[];
};

export type DeterministicWhyTraceDebugEdge = {
  source: string;
  target: string;
  rel_type: string;
  confidence: number;
  inferred: boolean;
  source_type: string;
};

export type DeterministicWhyTraceDebugNeighbor = {
  tag: string;
  role: string;
  type: string | null;
  subtype: string | null;
};

export type DeterministicWhyTraceDebugWeakLink = {
  index: number;
  source: string;
  target: string;
  rel_type: string;
  confidence: number;
  reasons: string[];
};

export type DeterministicWhyTraceDebugChainEdge = {
  source: string;
  target: string;
  rel_type: string;
  confidence: number;
  source_type: string;
};

export type DeterministicWhyTraceDebugRankedChain = {
  nodes: string[];
  edges: DeterministicWhyTraceDebugChainEdge[];
  score: number;
  broken: boolean;
  break_reason: string;
  weak_links: DeterministicWhyTraceDebugWeakLink[];
};

export type DeterministicWhyTraceDebugMergedContext = {
  parallel_upstream_tags: string[];
  parallel_downstream_tags: string[];
  parallel_context_tags: string[];
};

export type DeterministicWhyTraceDebugChains = {
  ranked_upstream: DeterministicWhyTraceDebugRankedChain[];
  ranked_downstream: DeterministicWhyTraceDebugRankedChain[];
  merged_context: DeterministicWhyTraceDebugMergedContext;
  diagnostics?: {
    requested_tag?: string;
    selected_tag?: string;
    exists_in_nodes?: boolean;
    incoming_count?: number;
    outgoing_count?: number;
    upstream_candidate_paths?: number;
    downstream_candidate_paths?: number;
    ranked_upstream_returned?: number;
    ranked_downstream_returned?: number;
    zero_reason?: string;
  };
};

export type DeterministicWhyStructureRankedChain = {
  tags: string[];
  score: number;
  depth: number;
  weak_links: DeterministicWhyTraceDebugWeakLink[];
  broken: boolean;
  break_reason: string | null;
};

export type DeterministicWhyStructureMergedContext = {
  parallel_upstream: string[];
  parallel_downstream: string[];
};

export type DeterministicWhyStructure = {
  chains?: {
    ranked_upstream: DeterministicWhyStructureRankedChain[];
    ranked_downstream: DeterministicWhyStructureRankedChain[];
    merged_context: {
      parallel_upstream_tags: string[];
      parallel_downstream_tags: string[];
      parallel_context_tags: string[];
    };
  };
  ranked_upstream: DeterministicWhyStructureRankedChain[];
  ranked_downstream: DeterministicWhyStructureRankedChain[];
  merged_context: DeterministicWhyStructureMergedContext;
  diagnostics?: {
    reason?: string;
    ranked_upstream_count?: number;
    ranked_downstream_count?: number;
  };
};

export type DeterministicWhyNarrative = {
  summary: string;
  behavior: string;
  upstream: string;
  downstream: string;
  state: string;
  warnings: string[];
};

export type DeterministicWhyTraceDebug = {
  classification?: DeterministicWhyTraceDebugClassification;
  graph?: DeterministicWhyTraceDebugGraph;
  edges?: DeterministicWhyTraceDebugEdge[];
  neighbors?: DeterministicWhyTraceDebugNeighbor[];
  chains?: DeterministicWhyTraceDebugChains;
};

export type DeterministicWhyTraceResponse = {
  tag: string;
  available: boolean;
  snapshot_id: string;
  behavior_card?: string;
  behavior_summary?: string;
  runtime_state?: Record<string, unknown> | null;
  steps: DeterministicWhyTraceStep[];
  debug?: DeterministicWhyTraceDebug;
  structure?: DeterministicWhyStructure;
  engine?: {
    cache_hit?: boolean;
    cache_key?: string;
    rows_count?: number;
    edges_count?: number;
  };
  explanation?: DeterministicWhyNarrative;
  narrative?: DeterministicWhyNarrative;
};

export type UNSRow = {
  tag: string;
  type?: string;
  subtype?: string | null;
  equipment?: string | null;
  current_value?: string | null;
  state?: string | null;
  setpoint?: string | null;
  mode?: string | null;
  controls?: string[];
  upstream?: string[];
  downstream?: string[];
  behavior_card?: string | null;
};

export type SystemTraceStep = {
  tag: string;
  depth: number;
  direction: "self" | "upstream" | "downstream";
  edge_type: string | null;
};

export type SystemTraceResponse = {
  tag: string;
  project_id: string | null;
  path: string[];
  steps: SystemTraceStep[];
};

export type SystemBottleneck = {
  tag: string;
  in_degree: number;
  out_degree: number;
  score: number;
};

export type SavedEngineeringView = {
  id: string;
  project_id: string;
  name: string;
  query: string | null;
  script: string | null;
  created_at: string;
};

export type SavedEngineeringViewVersion = {
  id: string;
  view_id: string;
  project_id: string;
  notes: string | null;
  created_at: string;
};

export type SavedEngineeringViewDiff = {
  before_version_id: string;
  after_version_id: string;
  summary: {
    added: number;
    removed: number;
    changed: number;
  };
  added: Array<{ tag: string; after: Record<string, unknown> }>;
  removed: Array<{ tag: string; before: Record<string, unknown> }>;
  changed: Array<{
    tag: string;
    fields: Array<{ field: string; before: unknown; after: unknown }>;
    before: Record<string, unknown>;
    after: Record<string, unknown>;
  }>;
};

export type TagIntelligenceRow = {
  tag: string;
  tag_type: string | null;
  equipment: string | null;
  sources: string[];
  inbound_count: number;
  outbound_count: number;
  relation_count: number;
  is_unused: boolean;
  is_orphan: boolean;
  conflicts: string[];
};

export type TagIntelligencePayload = {
  project_id?: string | null;
  category: "all" | "unused" | "orphans" | "conflicts" | string;
  search: string;
  rows: TagIntelligenceRow[];
  summary: {
    total: number;
    unused: number;
    orphans: number;
    conflicts: number;
  };
  timestamp?: string;
};

export type ProductionHealthResponse = {
  status: string;
  services: {
    redis?: {
      enabled?: boolean;
    };
    connectors?: {
      healthy?: number;
      total?: number;
    };
    metrics?: Record<string, unknown>;
  };
  timestamp: string;
};

export type ProductionAuditEvent = {
  event_type: string;
  actor: string;
  details: Record<string, unknown>;
  created_at: string;
};

export type TraceResponse = {
  project_id: string;
  node_id: string;
  path: string[];
};

export type SimulationTracePoint = {
  tag: string;
  value: number | boolean | string;
  time: number;
};

export type SimulationTraceIssue = {
  tag: string;
  issue: string;
};

export type SimulationTraceResponse = {
  project_id: string;
  trace: SimulationTracePoint[];
};

export type SimulationAnalysisResponse = {
  project_id: string;
  issues: SimulationTraceIssue[];
};

export type DiscoveredControlLoop = {
  id?: string;
  project_id?: string;
  loop_tag: string;
  sensor_tag: string;
  actuator_tag: string;
  process_unit?: string | null;
  controller_tag?: string | null;
  control_strategy?: string;
  loop_type?: string;
  setpoint_tag?: string | null;
  output_tag?: string | null;
  status?: string;
  confidence: number;
  source_reference?: string | null;
  created_at?: string;
};

export type ControlLoopRecord = {
  id: string;
  project_id: string;
  loop_tag: string;
  sensor_tag: string;
  actuator_tag: string;
  process_unit?: string | null;
  controller_tag?: string | null;
  loop_type: string;
  control_strategy: string;
  setpoint_tag?: string | null;
  output_tag?: string | null;
  status: string;
  confidence: number;
  created_at: string;
  loop_id?: string;
  sensor?: string;
  actuator?: string;
  process?: string;
  controller?: string | null;
  chain?: string[];
  tuning_confidence?: number;
  tuning?: Record<string, unknown>;
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

export type STValidationIssue = {
  file: string;
  rule: string;
  message: string;
  severity: string;
  line?: number | null;
};

export type STValidationReport = {
  project_id: string;
  valid: boolean;
  issues: STValidationIssue[];
  parser_backend?: string;
};

export type STVerificationParseResult = {
  file: string;
  parsed: boolean;
  ast_valid: boolean;
  issue_count: number;
};

export type STVerificationFileSyntaxIssue = {
  file: string;
  rule: string;
  message: string;
  severity: "warning" | "error";
  line: number | null;
  hard_fail: boolean;
};

export type STVerificationHardFailCondition = {
  code: string;
  message: string;
  file: string | null;
  triggered: boolean;
};

export type STVerificationSummary = {
  project_id: string;
  verified_at: string;
  parser_backend: string;
  overall_status: "success" | "failed" | "warning";
  parsed_file_count: number;
  ast_validation_result: "pass" | "fail" | "warning";
  checks_passed: number;
  checks_failed: number;
  checks_warning: number;
  has_hard_fail: boolean;
};

export type STVerificationPanelPayload = {
  project_id: string;
  run_id: string;
  verified_at: string;
  overall_status: "idle" | "running" | "success" | "failed" | "warning";
  checks_passed: number;
  checks_failed: number;
  checks_warning: number;
  parsed_file_count: number;
  ast_validation_result: "pass" | "fail" | "warning";
  checks: Array<{
    check_id: string;
    check_name: string;
    status: "idle" | "running" | "success" | "failed" | "warning";
    severity: "info" | "warning" | "error";
    message: string;
    line_number: number | null;
    suggestion: string | null;
    file?: string | null;
  }>;
  errors: Array<{
    file: string;
    message: string;
    severity: "info" | "warning" | "error";
    line?: number | null;
    code?: string | null;
  }>;
};

export type STVerificationServiceResponse = {
  parse_results: STVerificationParseResult[];
  file_level_issues: STVerificationFileSyntaxIssue[];
  summary: STVerificationSummary;
  hard_fail_conditions: STVerificationHardFailCondition[];
  panel: STVerificationPanelPayload;
};

export type STWorkspaceVerifyRequest = {
  workspace_path: string;
};

export type STWorkspaceVerificationIssue = {
  line: number;
  column: number;
  code: string;
  message: string;
};

export type STWorkspaceVerificationFileResult = {
  file: string;
  status: "passed" | "warnings" | "failed";
  errors: STWorkspaceVerificationIssue[];
  warnings: STWorkspaceVerificationIssue[];
};

export type STWorkspaceVerificationSummary = {
  files_checked: number;
  error_count: number;
  warning_count: number;
};

export type STWorkspaceVerificationResponse = {
  status: "passed" | "passed_with_warnings" | "failed";
  summary: STWorkspaceVerificationSummary;
  files: STWorkspaceVerificationFileResult[];
};

export type VerifySTOptions = {
  maxAttempts?: number;
  initialDelayMs?: number;
  backoffFactor?: number;
};

export type VerifySTWorkspaceOptions = VerifySTOptions;

export type IOMappingTableRow = {
  tag: string;
  device_type: string;
  signal_type: string;
  io_type: string;
  plc_id: string;
  slot: number;
  channel: number;
  description: string;
  equipment_id: string;
};

export type IOMappingSummaryByType = {
  AI: number;
  AO: number;
  DI: number;
  DO: number;
};

export type IOMappingGenerationChannel = {
  signal_tag: string;
  normalized_signal_tag?: string | null;
  io_type: "AI" | "AO" | "DI" | "DO" | string;
  plc_slot: number;
  plc_channel: number;
  source?: string;
};

export type IOMappingGenerationApiResponse = {
  project_id: string;
  channels: IOMappingGenerationChannel[];
};

export type IOMappingIssue = {
  code: string;
  severity: "warning" | "error";
  message: string;
  tag?: string | null;
};

export type IOMappingEngineResponse = {
  project_id?: string;
  version_id?: string | null;
  version_number?: number | null;
  generated_at?: string;
  is_active?: boolean;
  status: "passed" | "passed_with_warnings" | "failed";
  summary: {
    total_signals: number;
    warning_count: number;
    error_count: number;
  };
  rows: Array<{
    tag: string;
    device_type: string;
    signal_type: string;
    io_type: string;
    plc_id: string;
    slot: number;
    channel: number;
    description: string;
  }>;
  issues: IOMappingIssue[];
};

export type IOMappingGenerationResult = {
  status: "passed" | "passed_with_warnings" | "failed";
  project_id: string;
  version_id?: string | null;
  version_number?: number | null;
  generated_at?: string;
  is_active?: boolean;
  rows: IOMappingTableRow[];
  summary: IOMappingSummaryByType;
  validation_summary: {
    total_signals: number;
    warning_count: number;
    error_count: number;
  };
  issues: IOMappingIssue[];
  total: number;
};

export type GenerateIOMappingOptions = {
  maxAttempts?: number;
  initialDelayMs?: number;
  backoffFactor?: number;
};

export type RuntimeDeployRequest = {
  project_id: string;
  workspace_path: string;
  runtime_config: {
    target_runtime: string;
    ip_address: string;
    protocol: string;
    port?: number;
  };
};

export type RuntimeDeployResponse = {
  status: "passed" | "failed";
  summary: {
    files_loaded: number;
    io_points_bound: number;
    runtime_target: string;
    project_name: string;
    loaded_program_name?: string | null;
    openplc_integration_mode?: "active" | "partial";
  };
  steps: Array<{
    name: "runtime_connected" | "project_uploaded" | "logic_loaded" | "io_applied" | "runtime_started";
    status: "passed" | "failed";
    message: string;
  }>;
  errors: string[];
  warnings: string[];
};

export type DirectPLCProtocol = "opc_ua" | "modbus_tcp" | "ethernet_ip" | "profinet" | "mqtt_industrial";
export type DirectPLCTargetRuntime = "openplc" | "beremiz" | "codesys" | "siemens_s7" | "beckhoff_twincat" | "custom";

export type DirectPLCDeployRequest = {
  project_id: string;
  connection: {
    plc_address: string;
    protocol: DirectPLCProtocol;
    target_runtime: DirectPLCTargetRuntime;
    io_configuration: string;
  };
  safety: {
    syntax_validation_passed: boolean;
    logic_verification_passed: boolean;
    io_validation_passed: boolean;
    simulation_test_passed: boolean;
  };
};

export type DirectPLCDeployResponse = {
  status: "disabled" | "blocked" | "accepted" | "failed";
  message: string;
  audit: {
    id: string;
    project_id: string;
    requested_at: string;
    feature_flag_enabled: boolean;
    status: "disabled" | "blocked" | "accepted" | "failed";
    warnings: string[];
    errors: string[];
  };
};

export type DeployRuntimeOptions = {
  maxAttempts?: number;
  initialDelayMs?: number;
  backoffFactor?: number;
};

export type RuntimeControlStepName = "compile_st" | "generate_c" | "build_runtime" | "apply_io" | "start_runtime";

export type RuntimeControlStep = {
  name: RuntimeControlStepName;
  status: "passed" | "failed";
  message: string;
  detail?: Record<string, unknown>;
};

export type RuntimeControlDeployRequest = {
  project_id: string;
};

export type RuntimeControlDeployResponse = {
  status: "passed" | "failed";
  project_id: string;
  runtime: string;
  runtime_project_dir: string | null;
  steps: RuntimeControlStep[];
  errors: string[];
  dependency_report?: {
    ok: boolean;
    dependencies: Record<string, string | null>;
    missing: string[];
  };
  runtime_status?: {
    status: "running" | "stopped";
    project_dir: string | null;
    pid: number | null;
    runtime_binary: string;
  };
};

export type RuntimeControlActionResponse = {
  status: "passed" | "failed";
  message?: string;
  runtime_project_dir?: string;
  step?: {
    name: string;
    status: "passed" | "failed";
    message: string;
    detail?: Record<string, unknown>;
  };
};

export type RuntimeDeploymentRecord = {
  id: string;
  project_id: string;
  target_runtime: string;
  protocol: string;
  plc_address?: string | null;
  io_config_json: Array<Record<string, unknown>>;
  deploy_status: string;
  validation_status: string;
  deployed_version?: string | null;
  artifact_path?: string | null;
  last_error?: string | null;
  started_at: string;
  updated_at: string;
};

export type RuntimeStateResponse = {
  project_id: string;
  runtime_state: "running" | "stopped" | "failed" | "idle";
  deployment?: RuntimeDeploymentRecord | null;
  live_runtime?: Record<string, unknown>;
};

export type RuntimeDeploymentLatestResponse = {
  project_id: string;
  deployment?: RuntimeDeploymentRecord | null;
  timestamp: string;
};

export type RuntimeTelemetryTagsResponse = Record<string, unknown>;

export type RuntimeSignalType = "BOOL" | "INT" | "REAL" | "STRING";

export type RuntimeForcedInputState = {
  tag: string;
  value: unknown;
  type: RuntimeSignalType;
  forced: boolean;
  forced_at: string | null;
};

export type RuntimeInputCatalogItem = {
  tag: string;
  io_type: string;
  type: RuntimeSignalType;
  current_value: unknown;
  forced: boolean;
  forced_at: string | null;
};

export type RuntimeForceInputRequest = {
  tag: string;
  value: unknown;
  type?: RuntimeSignalType;
};

export type RuntimeForceInputResponse = {
  success: boolean;
  message: string;
  project_id: string;
  forced: RuntimeForcedInputState;
  changed_signals?: Array<{ tag: string; previous: unknown; current: unknown }>;
  changed_alarms?: Array<{ tag: string; previous: unknown; current: unknown }>;
  changed_health_checks?: Array<{ name: string; previous: unknown; current: unknown }>;
  evaluation_cycle?: RuntimeEvaluationCycle;
  timestamp: string;
};

export type RuntimeHealthCheckItem = {
  name: string;
  status: "healthy" | "warning" | "unhealthy";
  message: string;
};

export type RuntimeEvaluationCycle = {
  project_id: string;
  reason: string;
  evaluated_at: string;
  forced_tag: string | null;
  forced_value: unknown;
  evaluated_blocks: string[];
  alarms: Record<string, boolean>;
  health_checks: RuntimeHealthCheckItem[];
  changed_signals: Array<{ tag: string; previous: unknown; current: unknown }>;
  changed_alarms: Array<{ tag: string; previous: unknown; current: unknown }>;
  changed_health_checks: Array<{ name: string; previous: unknown; current: unknown }>;
  signal_state_updated: boolean;
};

export type RuntimeDiagnosticsResponse = {
  success: boolean;
  project_id: string;
  diagnostics: RuntimeEvaluationCycle;
  timestamp: string;
};

export type FaultTimelinePoint = {
  tag: string;
  timestamp: string;
  value: number | string | boolean;
  source: string;
};

export type FaultAnalysisResult = {
  alarm: string;
  root_cause: string;
  path: string[];
  timeline: FaultTimelinePoint[];
  confidence: number;
  affected_devices: string[];
  loop_id?: string | null;
  actuator_tag?: string | null;
  control_strategy?: string | null;
};

export type RuntimeForcedInputsResponse = {
  success: boolean;
  message: string;
  project_id: string;
  forced_inputs: RuntimeForcedInputState[];
  input_catalog: RuntimeInputCatalogItem[];
  diagnostics?: RuntimeEvaluationCycle;
  timestamp: string;
};

export type VersionSnapshotServiceResponse = {
  project_id: string;
  snapshot_id: string;
  created_at: string;
  artifacts: string[];
  backend: string;
};

export type CreateVersionSnapshotOptions = {
  maxAttempts?: number;
  initialDelayMs?: number;
  backoffFactor?: number;
};

export type LogicFilesServiceResponse = {
  project_id: string;
  output_root: string;
  files: string[];
};

export type ExportLogicOptions = {
  maxAttempts?: number;
  initialDelayMs?: number;
  backoffFactor?: number;
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
  st_validation?: STValidationReport | null;
};

const resolveApiBaseUrl = (): string => {
  const explicitBase = (import.meta.env.VITE_API_BASE as string | undefined)?.trim();
  if (explicitBase) {
    return explicitBase.replace(/\/$/, "");
  }

  const legacyBase = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
  if (legacyBase) {
    return legacyBase.replace(/\/$/, "");
  }

  if (typeof window !== "undefined") {
    return "/api";
  }

  return "http://127.0.0.1:8000/api";
};

const resolveWsBaseUrl = (): string => {
  const explicitWsBase = (import.meta.env.VITE_WS_BASE as string | undefined)?.trim();
  if (explicitWsBase) {
    return explicitWsBase.replace(/\/$/, "");
  }

  const apiBase = resolveApiBaseUrl();
  if (/^https?:\/\//i.test(apiBase)) {
    return apiBase.replace(/^http:\/\//i, "ws://").replace(/^https:\/\//i, "wss://").replace(/\/$/, "");
  }

  if (typeof window !== "undefined") {
    if (window.location.port === "5173") {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      return `${protocol}//${window.location.hostname}:8000`;
    }
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}`;
  }

  return "ws://127.0.0.1:8000";
};

const api = axios.create({
  baseURL: resolveApiBaseUrl(),
});

const getErrorMessage = (error: unknown, fallback: string): string => {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
    if (error.message) {
      return error.message;
    }
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
};

const unwrapData = <T>(responseData: unknown, fallback: T): T => {
  if (responseData && typeof responseData === "object" && "data" in responseData) {
    return (responseData as { data: T }).data;
  }
  return fallback;
};

const HARD_FAIL_RULES = new Set([
  "missing_end_if",
  "missing_end_program",
  "malformed_case",
  "parse_failure",
  "empty_template_section",
]);

const delay = async (ms: number): Promise<void> => {
  await new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
};

const normalizeSeverity = (severity: string | undefined): "warning" | "error" => (severity === "warning" ? "warning" : "error");

const toPanelSeverity = (severity: "warning" | "error"): "warning" | "error" => severity;

const inferSignalType = (ioType: string): string => {
  const normalized = ioType.toUpperCase();
  if (normalized === "AI" || normalized === "AO") {
    return "analog";
  }
  if (normalized === "DI" || normalized === "DO") {
    return "digital";
  }
  return "";
};

const inferEquipmentId = (tag: string): string => {
  const match = tag.match(/([A-Za-z]+\d+)/);
  return match ? match[1].toUpperCase() : "UNASSIGNED";
};

const inferDeviceType = (tag: string): string => {
  const token = tag.split("_")[0] ?? "";
  if (!token) {
    return "Unknown";
  }

  if (/^P\d+/i.test(token)) {
    return "Pump";
  }
  if (/^V\d+/i.test(token)) {
    return "Valve";
  }
  if (/^(LT|PT|FT|TT|AT)\d+/i.test(token)) {
    return "Sensor";
  }
  return "Controller";
};

const adaptIOMappingGenerationResponse = (payload: IOMappingGenerationApiResponse): IOMappingGenerationResult => {
  const rows: IOMappingTableRow[] = payload.channels.map((channel) => {
    const ioType = String(channel.io_type || "").toUpperCase();
    const tag = channel.signal_tag || channel.normalized_signal_tag || "UNNAMED_TAG";
    return {
      tag,
      device_type: inferDeviceType(tag),
      signal_type: inferSignalType(ioType),
      io_type: ioType,
      plc_id: "PLC-01",
      slot: channel.plc_slot,
      channel: channel.plc_channel,
      description: `Auto-mapped from ${tag}`,
      equipment_id: inferEquipmentId(tag),
    };
  });

  const summary: IOMappingSummaryByType = { AI: 0, AO: 0, DI: 0, DO: 0 };
  for (const row of rows) {
    const ioType = row.io_type.toUpperCase() as keyof IOMappingSummaryByType;
    if (ioType in summary) {
      summary[ioType] += 1;
    }
  }

  return {
    status: "passed",
    project_id: payload.project_id,
    rows,
    summary,
    validation_summary: {
      total_signals: rows.length,
      warning_count: 0,
      error_count: 0,
    },
    issues: [],
    total: rows.length,
  };
};

const adaptIOMappingEngineResponse = (payload: IOMappingEngineResponse, projectId: string): IOMappingGenerationResult => {
  const rows: IOMappingTableRow[] = payload.rows.map((row) => ({
    tag: row.tag,
    device_type: row.device_type,
    signal_type: row.signal_type,
    io_type: row.io_type,
    plc_id: row.plc_id,
    slot: row.slot,
    channel: row.channel,
    description: row.description,
    equipment_id: inferEquipmentId(row.tag),
  }));

  const summary: IOMappingSummaryByType = { AI: 0, AO: 0, DI: 0, DO: 0 };
  for (const row of rows) {
    const ioType = row.io_type.toUpperCase() as keyof IOMappingSummaryByType;
    if (ioType in summary) {
      summary[ioType] += 1;
    }
  }

  return {
    status: payload.status,
    project_id: payload.project_id || projectId,
    version_id: payload.version_id ?? null,
    version_number: payload.version_number ?? null,
    generated_at: payload.generated_at,
    is_active: payload.is_active ?? true,
    rows,
    summary,
    validation_summary: payload.summary,
    issues: payload.issues,
    total: rows.length,
  };
};

const adaptRuntimeDeployResponse = (
  payload: RuntimeDeployResponse,
  projectId: string
): RuntimeValidationPanelResponse => {
  const stepToCheckName: Record<string, string> = {
    runtime_connected: "Runtime Connected",
    project_uploaded: "Project Uploaded",
    logic_loaded: "Logic Loaded",
    io_applied: "IO Applied",
    runtime_started: "Runtime Started",
  };

  const checks: RuntimeValidationPanelResponse["checks"] = payload.steps.map((step, index) => ({
    check_id: `runtime-step-${index + 1}`,
    check_name: stepToCheckName[step.name] || step.name,
    status: step.status === "passed" ? "success" : "failed",
    expected_value: "passed",
    actual_value: step.status,
    tolerance: null,
    message: step.message,
  }));

  const checksPassed = checks.filter((item) => item.status === "success").length;
  const checksFailed = checks.filter((item) => item.status === "failed").length;
  const checksWarning = 0;

  return {
    project_id: projectId,
    run_id: `runtime-${Date.now()}`,
    validated_at: new Date().toISOString(),
    overall_status: payload.status === "passed" ? "success" : "failed",
    checks_passed: checksPassed,
    checks_failed: checksFailed,
    checks_warning: checksWarning,
    checks,
  };
};

const toAstResult = (issues: STVerificationFileSyntaxIssue[]): "pass" | "fail" | "warning" => {
  if (issues.some((issue) => issue.severity === "error")) {
    return "fail";
  }
  if (issues.some((issue) => issue.severity === "warning")) {
    return "warning";
  }
  return "pass";
};

const toOverallStatus = (issues: STVerificationFileSyntaxIssue[]): "success" | "failed" | "warning" => {
  if (issues.some((issue) => issue.severity === "error")) {
    return "failed";
  }
  if (issues.some((issue) => issue.severity === "warning")) {
    return "warning";
  }
  return "success";
};

const adaptSTVerificationResponse = (payload: STValidationReport): STVerificationServiceResponse => {
  const verifiedAt = new Date().toISOString();

  const fileLevelIssues: STVerificationFileSyntaxIssue[] = payload.issues.map((issue) => {
    const rule = issue.rule || "parse_failure";
    const ruleToken = rule.toLowerCase();
    const hardFail = HARD_FAIL_RULES.has(ruleToken) || normalizeSeverity(issue.severity) === "error";
    return {
      file: issue.file || "main.st",
      rule,
      message: issue.message,
      severity: normalizeSeverity(issue.severity),
      line: issue.line ?? null,
      hard_fail: hardFail,
    };
  });

  const files = new Set<string>(["main.st"]);
  for (const issue of fileLevelIssues) {
    files.add(issue.file);
  }

  const parseResults: STVerificationParseResult[] = [...files].map((file) => {
    const fileIssues = fileLevelIssues.filter((issue) => issue.file === file);
    const parseFailure = fileIssues.some((issue) => HARD_FAIL_RULES.has(issue.rule.toLowerCase()));
    const astValid = !fileIssues.some((issue) => issue.severity === "error");
    return {
      file,
      parsed: !parseFailure,
      ast_valid: astValid,
      issue_count: fileIssues.length,
    };
  });

  const hardFailConditions: STVerificationHardFailCondition[] = fileLevelIssues
    .filter((issue) => issue.hard_fail)
    .map((issue) => ({
      code: issue.rule,
      message: issue.message,
      file: issue.file,
      triggered: true,
    }));

  const checksFailed = fileLevelIssues.filter((issue) => issue.severity === "error").length;
  const checksWarning = fileLevelIssues.filter((issue) => issue.severity === "warning").length;
  const checksPassed = Math.max(0, parseResults.length - checksFailed - checksWarning);
  const astValidationResult = toAstResult(fileLevelIssues);
  const overallStatus = toOverallStatus(fileLevelIssues);

  const summary: STVerificationSummary = {
    project_id: payload.project_id,
    verified_at: verifiedAt,
    parser_backend: payload.parser_backend ?? "regex",
    overall_status: overallStatus,
    parsed_file_count: parseResults.length,
    ast_validation_result: astValidationResult,
    checks_passed: checksPassed,
    checks_failed: checksFailed,
    checks_warning: checksWarning,
    has_hard_fail: hardFailConditions.length > 0,
  };

  const panel: STVerificationPanelPayload = {
    project_id: payload.project_id,
    run_id: `verify-${Date.now()}`,
    verified_at: verifiedAt,
    overall_status: overallStatus,
    parsed_file_count: summary.parsed_file_count,
    ast_validation_result: summary.ast_validation_result,
    checks_passed: summary.checks_passed,
    checks_failed: summary.checks_failed,
    checks_warning: summary.checks_warning,
    checks: fileLevelIssues.map((issue, index) => ({
      check_id: `check-${index + 1}`,
      check_name: issue.rule,
      status: issue.severity === "error" ? "failed" : "warning",
      severity: toPanelSeverity(issue.severity),
      message: issue.message,
      line_number: issue.line,
      suggestion: null,
      file: issue.file,
    })),
    errors: fileLevelIssues.map((issue) => ({
      file: issue.file,
      message: issue.message,
      severity: toPanelSeverity(issue.severity),
      line: issue.line,
      code: issue.rule,
    })),
  };

  return {
    parse_results: parseResults,
    file_level_issues: fileLevelIssues,
    summary,
    hard_fail_conditions: hardFailConditions,
    panel,
  };
};

export async function listProjects(): Promise<Project[]> {
  const response = await api.get<Project[]>("/projects");
  return response.data;
}

export async function createProject(payload: {
  name: string;
  industry: string;
  description?: string;
  plc_runtime?: string;
  owner?: string;
  status?: string;
  active_version?: number;
}): Promise<Project> {
  const response = await api.post<Project>("/projects", payload);
  return response.data;
}

export async function updateProject(
  projectId: string,
  payload: { name?: string; industry?: string; description?: string; plc_runtime?: string; owner?: string; status?: string; active_version?: number }
): Promise<Project> {
  const response = await api.put<Project>(`/projects/${projectId}`, payload);
  return response.data;
}

export async function getActiveProject(): Promise<Project | null> {
  const response = await api.get<Project | null>("/projects/active/current");
  return response.data;
}

export async function setActiveProject(projectId: string): Promise<Project> {
  const response = await api.put<Project>("/projects/active", { project_id: projectId });
  return response.data;
}

export async function deleteProject(projectId: string): Promise<void> {
  await api.delete(`/projects/${projectId}`);
}

export async function getPLCExportReadiness(payload: {
  project_id: string;
  vendor: PLCExportVendor;
  source_mode?: ExportSourceMode;
  source_version_id?: string | null;
}): Promise<ExportReadinessSummary> {
  const response = await api.post<ExportReadinessSummary>("/export/readiness", {
    project_id: payload.project_id,
    vendor: payload.vendor,
    source_mode: payload.source_mode ?? "live",
    source_version_id: payload.source_version_id ?? null,
  });
  return response.data;
}

export async function createPLCExport(
  projectId: string,
  vendor: PLCExportVendor,
  options: { source_mode?: ExportSourceMode; source_version_id?: string | null } = {}
): Promise<PLCExportResponse> {
  const response = await api.post<PLCExportResponse>("/export", {
    project_id: projectId,
    vendor,
    source_mode: options.source_mode ?? "live",
    source_version_id: options.source_version_id ?? null,
  });
  return response.data;
}

export async function handoffPLCExportForDeployment(payload: {
  project_id: string;
  export_id: string;
  target_runtime: string;
  runtime_config?: Record<string, unknown>;
  trigger_runtime_deploy?: boolean;
}): Promise<ExportDeploymentHandoffResponse> {
  const response = await api.post<ExportDeploymentHandoffResponse>("/export/deploy-handoff", {
    project_id: payload.project_id,
    export_id: payload.export_id,
    target_runtime: payload.target_runtime,
    runtime_config: payload.runtime_config ?? {},
    trigger_runtime_deploy: Boolean(payload.trigger_runtime_deploy),
  });
  return response.data;
}

export async function reconcilePID(payload: {
  dataset: Array<{
    tag: string;
    label?: string;
    node_type?: string;
    status?: string;
    process_unit?: string | null;
    connected_to?: string[];
    controls?: string[];
    measures?: string[];
  }>;
  similarity_threshold?: number;
}): Promise<PIDReconcileSummary> {
  const response = await api.post<PIDReconcileSummary>("/pid/reconcile", payload);
  return response.data;
}

export async function getPIDChanges(): Promise<PIDReconcileSummary> {
  const response = await api.get<PIDReconcileSummary>("/pid/changes");
  return response.data;
}

export async function applyPIDUpdate(payload: {
  allow_conflicts?: boolean;
  force_apply_on_validation_warnings?: boolean;
} = {}): Promise<PIDApplyUpdateResponse> {
  const response = await api.post<PIDApplyUpdateResponse>("/pid/apply-update", payload);
  return response.data;
}

export function buildExportDownloadUrl(exportId: string): string {
  const base = (import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api").replace(/\/$/, "");
  return `${base}/exports/${encodeURIComponent(exportId)}/download`;
}

export async function parseProject(projectId: string, fileIds: string[] = []): Promise<ParseBatchResponse> {
  const response = await api.post<ParseBatchResponse>(`/projects/${projectId}/parse`, { file_ids: fileIds });
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

export async function getProjectDocuments(projectId: string): Promise<ProjectDocument[]> {
  const response = await api.get<ProjectDocument[]>(`/projects/${projectId}/upload`);
  return response.data;
}

export async function getGraph(projectId: string): Promise<PlantGraph> {
  const response = await api.get<PlantGraph>(`/projects/${projectId}/graph`);
  return response.data;
}

export async function getPlantSignals(projectId: string): Promise<PlantSignalRow[]> {
  const response = await api.get<PlantSignalRow[]>(`/projects/${projectId}/plant-signals`);
  return response.data;
}

export async function getEngineeringTable(payload: {
  project_id: string;
  file_ids?: string[];
  include_inferred?: boolean;
  max_flow_depth?: number;
}): Promise<EngineeringTableResponse> {
  const response = await api.post<EngineeringTableResponse>("/plant-model/engineering-table", payload);
  return response.data;
}

export async function getTrace(projectId: string, nodeId: string): Promise<TraceResponse> {
  const response = await api.get<TraceResponse>(`/projects/${projectId}/trace/${nodeId}`);
  return response.data;
}

export async function detectControlLoops(projectId: string): Promise<ControlLoopRecord[]> {
  const response = await api.post<ControlLoopRecord[]>(`/control-loops/detect`, { project_id: projectId });
  return response.data;
}

export async function getControlLoops(projectId?: string): Promise<ControlLoopRecord[]> {
  const response = await api.get<ControlLoopRecord[]>(`/control-loops`, {
    params: projectId ? { project_id: projectId } : undefined,
  });
  return response.data;
}

export async function getControlLoop(loopTag: string, projectId?: string): Promise<ControlLoopRecord> {
  const response = await api.get<ControlLoopRecord>(`/control-loops/${encodeURIComponent(loopTag)}`, {
    params: projectId ? { project_id: projectId } : undefined,
  });
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

export async function verifySTLogic(projectId: string): Promise<STVerificationServiceResponse> {
  const response = await api.post<STValidationReport>(`/projects/${projectId}/logic/validate-logic`);
  return adaptSTVerificationResponse(response.data);
}

export async function verifySTWorkspace(request: STWorkspaceVerifyRequest): Promise<STWorkspaceVerificationResponse> {
  const response = await api.post<STWorkspaceVerificationResponse>("/verify-st", request);
  return response.data;
}

export async function verifySTWorkspaceWithRetry(
  workspacePathOrProjectId: string,
  options: VerifySTWorkspaceOptions = {}
): Promise<STWorkspaceVerificationResponse> {
  const maxAttempts = options.maxAttempts ?? 3;
  const initialDelayMs = options.initialDelayMs ?? 700;
  const backoffFactor = options.backoffFactor ?? 2;

  let attempt = 0;
  let delayMs = initialDelayMs;
  let lastError: unknown = null;

  while (attempt < maxAttempts) {
    attempt += 1;
    try {
      return await verifySTWorkspace({ workspace_path: workspacePathOrProjectId });
    } catch (error) {
      lastError = error;
      if (attempt >= maxAttempts) {
        throw error;
      }
      await delay(delayMs);
      delayMs = Math.max(initialDelayMs, Math.floor(delayMs * backoffFactor));
    }
  }

  throw lastError instanceof Error ? lastError : new Error("Workspace ST verification failed after retries");
}

export async function verifySTLogicWithRetry(
  projectId: string,
  options: VerifySTOptions = {}
): Promise<STVerificationServiceResponse> {
  const maxAttempts = options.maxAttempts ?? 3;
  const initialDelayMs = options.initialDelayMs ?? 700;
  const backoffFactor = options.backoffFactor ?? 2;

  let attempt = 0;
  let delayMs = initialDelayMs;
  let lastError: unknown = null;

  while (attempt < maxAttempts) {
    attempt += 1;
    try {
      return await verifySTLogic(projectId);
    } catch (error) {
      lastError = error;
      if (attempt >= maxAttempts) {
        throw error;
      }
      await delay(delayMs);
      delayMs = Math.max(initialDelayMs, Math.floor(delayMs * backoffFactor));
    }
  }

  throw lastError instanceof Error ? lastError : new Error("ST verification failed after retries");
}

export async function generateIOMapping(projectId: string): Promise<IOMappingGenerationResult> {
  const response = await api.post<IOMappingEngineResponse | IOMappingGenerationApiResponse>(`/projects/${projectId}/io-mapping/generate`);
  if ("channels" in response.data) {
    return adaptIOMappingGenerationResponse(response.data);
  }
  return adaptIOMappingEngineResponse(response.data, projectId);
}

export async function getLatestIOMapping(projectId: string): Promise<IOMappingGenerationResult> {
  const response = await api.get<IOMappingEngineResponse>(`/projects/${projectId}/io-mapping/latest`);
  return adaptIOMappingEngineResponse(response.data, projectId);
}

export async function generateIOMappingWithRetry(
  projectId: string,
  options: GenerateIOMappingOptions = {}
): Promise<IOMappingGenerationResult> {
  const maxAttempts = options.maxAttempts ?? 3;
  const initialDelayMs = options.initialDelayMs ?? 700;
  const backoffFactor = options.backoffFactor ?? 2;

  let attempt = 0;
  let delayMs = initialDelayMs;
  let lastError: unknown = null;

  while (attempt < maxAttempts) {
    attempt += 1;
    try {
      return await generateIOMapping(projectId);
    } catch (error) {
      lastError = error;
      if (attempt >= maxAttempts) {
        throw error;
      }
      await delay(delayMs);
      delayMs = Math.max(initialDelayMs, Math.floor(delayMs * backoffFactor));
    }
  }

  throw lastError instanceof Error ? lastError : new Error("IO mapping generation failed after retries");
}

export async function createVersionSnapshot(projectId: string): Promise<VersionSnapshotServiceResponse> {
  const response = await api.post<VersionSnapshotServiceResponse>(`/projects/${projectId}/logic/version-snapshot`);
  return response.data;
}

export async function createVersionSnapshotWithRetry(
  projectId: string,
  options: CreateVersionSnapshotOptions = {}
): Promise<VersionSnapshotServiceResponse> {
  const maxAttempts = options.maxAttempts ?? 3;
  const initialDelayMs = options.initialDelayMs ?? 700;
  const backoffFactor = options.backoffFactor ?? 2;

  let attempt = 0;
  let delayMs = initialDelayMs;
  let lastError: unknown = null;

  while (attempt < maxAttempts) {
    attempt += 1;
    try {
      return await createVersionSnapshot(projectId);
    } catch (error) {
      lastError = error;
      if (attempt >= maxAttempts) {
        throw error;
      }
      await delay(delayMs);
      delayMs = Math.max(initialDelayMs, Math.floor(delayMs * backoffFactor));
    }
  }

  throw lastError instanceof Error ? lastError : new Error("Version snapshot failed after retries");
}

export async function exportGeneratedLogic(projectId: string): Promise<LogicFilesServiceResponse> {
  const response = await api.get<LogicFilesServiceResponse>(`/logic-files`, {
    params: { project_id: projectId },
  });
  return response.data;
}

export async function exportGeneratedLogicWithRetry(
  projectId: string,
  options: ExportLogicOptions = {}
): Promise<LogicFilesServiceResponse> {
  const maxAttempts = options.maxAttempts ?? 3;
  const initialDelayMs = options.initialDelayMs ?? 700;
  const backoffFactor = options.backoffFactor ?? 2;

  let attempt = 0;
  let delayMs = initialDelayMs;
  let lastError: unknown = null;

  while (attempt < maxAttempts) {
    attempt += 1;
    try {
      return await exportGeneratedLogic(projectId);
    } catch (error) {
      lastError = error;
      if (attempt >= maxAttempts) {
        throw error;
      }
      await delay(delayMs);
      delayMs = Math.max(initialDelayMs, Math.floor(delayMs * backoffFactor));
    }
  }

  throw lastError instanceof Error ? lastError : new Error("Logic export failed after retries");
}

export async function runSimulation(projectId: string): Promise<Record<string, unknown>> {
  const response = await api.post<Record<string, unknown>>(`/projects/${projectId}/simulation/run`);
  return response.data;
}

export async function getSimulationTrace(projectId: string): Promise<SimulationTraceResponse> {
  const response = await api.get<SimulationTraceResponse>(`/projects/${projectId}/simulation/trace`);
  return response.data;
}

export async function getSimulationAnalysis(projectId: string): Promise<SimulationAnalysisResponse> {
  const response = await api.get<SimulationAnalysisResponse>(`/projects/${projectId}/simulation/analysis`);
  return response.data;
}

export async function resetSimulationTrace(projectId: string): Promise<{ project_id: string; status: string; trace: SimulationTracePoint[] }> {
  const response = await api.post<{ project_id: string; status: string; trace: SimulationTracePoint[] }>(
    `/projects/${projectId}/simulation/simulation-trace/reset`
  );
  return response.data;
}

export async function runSimulationTraceCycle(
  projectId: string
): Promise<{ project_id: string; status: string; samples: number; trace: SimulationTracePoint[]; issues: SimulationTraceIssue[] }> {
  const response = await api.post<{ project_id: string; status: string; samples: number; trace: SimulationTracePoint[]; issues: SimulationTraceIssue[] }>(
    `/projects/${projectId}/simulation/simulation-trace/run`
  );
  return response.data;
}

export async function deployProject(projectId: string): Promise<Record<string, unknown>> {
  const response = await api.post<Record<string, unknown>>(`/projects/${projectId}/deploy`);
  return response.data;
}

export async function deployRuntime(payload: RuntimeDeployRequest): Promise<RuntimeValidationPanelResponse> {
  const response = await api.post<RuntimeDeployResponse>("/deploy-runtime", payload);
  return adaptRuntimeDeployResponse(response.data, payload.project_id);
}

export async function deployRuntimeWithRetry(
  payload: RuntimeDeployRequest,
  options: DeployRuntimeOptions = {}
): Promise<RuntimeValidationPanelResponse> {
  const maxAttempts = options.maxAttempts ?? 2;
  const initialDelayMs = options.initialDelayMs ?? 800;
  const backoffFactor = options.backoffFactor ?? 2;

  let attempt = 0;
  let delayMs = initialDelayMs;
  let lastError: unknown = null;

  while (attempt < maxAttempts) {
    attempt += 1;
    try {
      return await deployRuntime(payload);
    } catch (error) {
      lastError = error;
      if (attempt >= maxAttempts) {
        throw error;
      }
      await delay(delayMs);
      delayMs = Math.max(initialDelayMs, Math.floor(delayMs * backoffFactor));
    }
  }

  throw lastError instanceof Error ? lastError : new Error("Runtime deployment failed after retries");
}

export async function deployRuntimeControl(payload: RuntimeControlDeployRequest): Promise<RuntimeControlDeployResponse> {
  const response = await api.post<RuntimeControlDeployResponse>("/runtime/deploy", payload);
  return response.data;
}

export async function deployDirectPLC(payload: DirectPLCDeployRequest): Promise<DirectPLCDeployResponse> {
  const response = await api.post<DirectPLCDeployResponse>("/direct-plc/deploy", payload);
  return response.data;
}

export async function deployRuntimeControlWithRetry(
  payload: RuntimeControlDeployRequest,
  options: DeployRuntimeOptions = {}
): Promise<RuntimeControlDeployResponse> {
  const maxAttempts = options.maxAttempts ?? 2;
  const initialDelayMs = options.initialDelayMs ?? 800;
  const backoffFactor = options.backoffFactor ?? 2;

  let attempt = 0;
  let delayMs = initialDelayMs;
  let lastError: unknown = null;

  while (attempt < maxAttempts) {
    attempt += 1;
    try {
      return await deployRuntimeControl(payload);
    } catch (error) {
      lastError = error;
      if (attempt >= maxAttempts) {
        throw error;
      }
      await delay(delayMs);
      delayMs = Math.max(initialDelayMs, Math.floor(delayMs * backoffFactor));
    }
  }

  throw lastError instanceof Error ? lastError : new Error("Runtime control deployment failed after retries");
}

export async function startRuntimeControl(): Promise<RuntimeControlActionResponse> {
  const response = await api.post<RuntimeControlActionResponse>("/runtime/start");
  return response.data;
}

export async function stopRuntimeControl(): Promise<RuntimeControlActionResponse> {
  const response = await api.post<RuntimeControlActionResponse>("/runtime/stop");
  return response.data;
}

export async function restartRuntimeControl(): Promise<RuntimeControlActionResponse> {
  const response = await api.post<RuntimeControlActionResponse>("/runtime/restart");
  return response.data;
}

export async function getRuntimeTags(): Promise<RuntimeTelemetryTagsResponse> {
  const response = await api.get<RuntimeTelemetryTagsResponse>("/runtime/tags");
  return response.data;
}

export async function getRuntimeState(projectId: string): Promise<RuntimeStateResponse> {
  const response = await api.get<RuntimeStateResponse>("/runtime/state", {
    params: { project_id: projectId },
  });
  return response.data;
}

export async function getLatestRuntimeDeployment(projectId: string): Promise<RuntimeDeploymentLatestResponse> {
  const response = await api.get<RuntimeDeploymentLatestResponse>("/runtime/deployments/latest", {
    params: { project_id: projectId },
  });
  return response.data;
}

export async function applyRuntimeInputForce(projectId: string, payload: RuntimeForceInputRequest): Promise<RuntimeForceInputResponse> {
  const response = await api.post<RuntimeForceInputResponse>(`/runtime/${projectId}/force-input`, payload);
  return response.data;
}

export async function clearRuntimeInputForce(projectId: string, tag: string): Promise<RuntimeForceInputResponse> {
  const response = await api.post<RuntimeForceInputResponse>(`/runtime/${projectId}/clear-force`, { tag });
  return response.data;
}

export async function getRuntimeForcedInputs(projectId: string): Promise<RuntimeForcedInputsResponse> {
  const response = await api.get<RuntimeForcedInputsResponse>(`/runtime/${projectId}/forced-inputs`);
  return response.data;
}

export async function runRuntimeEvaluationCycle(projectId: string, reason = "manual_debug"): Promise<RuntimeForceInputResponse> {
  const response = await api.post<RuntimeForceInputResponse>(`/runtime/${projectId}/run-evaluation-cycle`, { reason });
  return response.data;
}

export async function getRuntimeDiagnostics(projectId: string): Promise<RuntimeDiagnosticsResponse> {
  const response = await api.get<RuntimeDiagnosticsResponse>(`/runtime/${projectId}/diagnostics`);
  return response.data;
}

export async function analyzeFault(alarmTag: string, projectId?: string, selectedTag?: string): Promise<FaultAnalysisResult> {
  const response = await api.post<FaultAnalysisResult>("/analyze_fault", {
    alarm_tag: alarmTag,
    project_id: projectId,
    selected_tag: selectedTag,
  });
  return response.data;
}

export function createRuntimeTelemetrySocket(): WebSocket {
  const wsBase = resolveWsBaseUrl();
  return new WebSocket(`${wsBase}/runtime/stream`);
}

export async function getDeterministicBehaviorRows(tags?: string[]): Promise<DeterministicBehaviorRowsResponse> {
  const cleanTags = (tags ?? []).map((tag) => tag.trim()).filter((tag) => tag.length > 0);
  const response = await api.get<{ data: DeterministicBehaviorRowsResponse }>("/behavior/rows", {
    params: cleanTags.length > 0 ? { tags: cleanTags.join(",") } : undefined,
  });
  return unwrapData(response.data, { snapshot_id: "snapshot-00000000", rows: [], count: 0 });
}

export async function loadDeterministicBehaviorCache(payload: {
  rows: EngineeringTableResponseRow[];
  edges: Array<Record<string, unknown>>;
}): Promise<{ snapshot_id: string; rows_loaded: number; edges_loaded: number; recomputed: number }> {
  const response = await api.post<{ data: { snapshot_id: string; rows_loaded: number; edges_loaded: number; recomputed: number } }>(
    "/behavior/load",
    {
      rows: payload.rows,
      edges: payload.edges,
    }
  );
  return response.data.data;
}

export async function getDeterministicWhyTrace(tag: string, maxDepth = 4): Promise<DeterministicWhyTraceResponse> {
  const normalizedTag = tag.trim();
  if (!normalizedTag) {
    throw new Error("tag is required");
  }
  const response = await api.get<{ data: DeterministicWhyTraceResponse }>(`/behavior/why/${encodeURIComponent(normalizedTag)}`, {
    params: { max_depth: maxDepth },
  });
  return unwrapData(response.data, {
    tag: normalizedTag,
    available: false,
    snapshot_id: "snapshot-00000000",
    steps: [],
  });
}

export async function getSystemContextForTag(tag: string, maxDepth = 4): Promise<Record<string, unknown> | null> {
  const normalizedTag = tag.trim();
  if (!normalizedTag) {
    return null;
  }

  // Backend exposes deterministic why-trace at GET /api/behavior/why/{tag} only.
  // Avoid probing legacy /behavior/system-context, /behavior/context, /system-context
  // (they are not registered here and caused noisy 404s in the network tab).
  try {
    const whyTrace = await getDeterministicWhyTrace(normalizedTag, maxDepth);
    return {
      tag: whyTrace.tag,
      available: whyTrace.available,
      system_context: (whyTrace as unknown as Record<string, unknown>).system_context ?? null,
      behavior: whyTrace.explanation?.behavior || whyTrace.behavior_summary || whyTrace.behavior_card || "",
      impact: (whyTrace as unknown as Record<string, unknown>).impact ?? null,
      trace: {
        steps: whyTrace.steps,
        structure: whyTrace.structure,
      },
      diagnostics: whyTrace.debug?.chains?.diagnostics ?? null,
      why_engine: whyTrace,
    };
  } catch {
    return null;
  }
}

const toBehaviorSocketUrl = (wsBase: string): string => {
  const socketPath = wsBase.endsWith("/api") ? "/ws/behavior" : "/api/ws/behavior";
  return `${wsBase}${socketPath}`;
};

export function getBehaviorSocketCandidateUrls(): string[] {
  const urls: string[] = [];

  const primaryWsBase = resolveWsBaseUrl();
  urls.push(toBehaviorSocketUrl(primaryWsBase));

  const apiBase = resolveApiBaseUrl();
  if (/^https?:\/\//i.test(apiBase)) {
    const directWsBase = apiBase.replace(/^http:\/\//i, "ws://").replace(/^https:\/\//i, "wss://").replace(/\/$/, "");
    urls.push(toBehaviorSocketUrl(directWsBase));
  }

  if (typeof window !== "undefined" && window.location.port === "5173") {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const hostFallback = `${protocol}//${window.location.hostname}:8000`;
    urls.push(`${hostFallback}/api/ws/behavior`);
  }

  return Array.from(new Set(urls));
}

export function createBehaviorSocket(url?: string): WebSocket {
  if (url) {
    return new WebSocket(url);
  }
  const wsBase = resolveWsBaseUrl();
  return new WebSocket(toBehaviorSocketUrl(wsBase));
}

export async function loadUNSModel(rows: UNSRow[], edges: Array<Record<string, unknown>>): Promise<Record<string, unknown>> {
  const response = await api.post<{ data: Record<string, unknown> }>("/uns/load", { rows, edges });
  return response.data.data;
}

export async function queryUNS(query: string): Promise<UNSRow[]> {
  const normalizedQuery = query.trim();
  if (!normalizedQuery) {
    throw new Error("Query is required.");
  }
  const response = await api.post<{ data: { rows: UNSRow[] } }>("/uns/query", { query: normalizedQuery });
  return unwrapData(response.data, { rows: [] }).rows ?? [];
}

export async function runUNSScript(script: string): Promise<Record<string, unknown>> {
  const normalizedScript = script.trim();
  if (!normalizedScript) {
    throw new Error("Script is required.");
  }
  const response = await api.post<{ data: Record<string, unknown> }>("/uns/script", { script: normalizedScript });
  return unwrapData(response.data, {});
}

export async function mapUNSTag(tag: string, mapping: Record<string, unknown>): Promise<Record<string, unknown>> {
  const response = await api.post<{ data: Record<string, unknown> }>("/uns/map", { tag, mapping });
  return response.data.data;
}

export async function setUNSConnector(
  connectorType: "opcua" | "mqtt" | "api",
  metadata: Record<string, unknown>
): Promise<Record<string, unknown>> {
  if (!["opcua", "mqtt", "api"].includes(connectorType)) {
    throw new Error("connector_type must be one of: opcua, mqtt, api");
  }
  const response = await api.post<{ data: Record<string, unknown> }>("/uns/connector", {
    connector_type: connectorType,
    metadata,
  });
  return unwrapData(response.data, {});
}

export async function getUNSRows(): Promise<UNSRow[]> {
  const response = await api.get<{ data: { rows: UNSRow[] } }>("/uns/rows");
  return unwrapData(response.data, { rows: [] }).rows ?? [];
}

export function createUNSSocket(): WebSocket {
  const wsBase = resolveWsBaseUrl();
  return new WebSocket(`${wsBase}/ws/uns`);
}

export async function connectAdvancedOPCUA(payload: {
  endpoint: string;
  security_policy?: string;
  auth_mode?: string;
  username?: string;
}): Promise<Record<string, unknown>> {
  if (!payload.endpoint.trim()) {
    throw new Error("OPC UA endpoint is required.");
  }
  try {
    const response = await api.post<{ data: Record<string, unknown> }>("/system-layer/connect/opcua", payload);
    return unwrapData(response.data, {});
  } catch (error) {
    const message = getErrorMessage(error, "OPC UA connector request failed.");
    if (message.toLowerCase().includes("asyncua is not installed")) {
      throw new Error("OPC UA connector is unavailable on the server (missing asyncua dependency). Contact backend admin to enable OPC UA support.");
    }
    throw new Error(message);
  }
}

export async function connectAdvancedMQTT(payload: {
  host: string;
  port?: number;
  client_id?: string;
  topic?: string;
}): Promise<Record<string, unknown>> {
  if (!payload.host.trim()) {
    throw new Error("MQTT host is required.");
  }
  const response = await api.post<{ data: Record<string, unknown> }>("/system-layer/connect/mqtt", payload);
  return unwrapData(response.data, {});
}

export async function connectAdvancedAPI(payload: {
  endpoint: string;
  method?: string;
  headers?: Record<string, string>;
}): Promise<Record<string, unknown>> {
  if (!payload.endpoint.trim()) {
    throw new Error("API endpoint is required.");
  }
  const response = await api.post<{ data: Record<string, unknown> }>("/system-layer/connect/api", payload);
  return unwrapData(response.data, {});
}

export async function runAdvancedAutoMap(payload: { external_tags: string[]; threshold?: number }): Promise<Record<string, unknown>> {
  if (!payload.external_tags.length) {
    throw new Error("At least one external tag is required.");
  }
  const response = await api.post<{ data: Record<string, unknown> }>("/system-layer/auto-map", payload);
  return unwrapData(response.data, {});
}

export async function getAdvancedTrace(tag: string, projectId?: string, maxDepth = 6): Promise<SystemTraceResponse> {
  const normalizedTag = tag.trim();
  if (!normalizedTag) {
    throw new Error("Trace tag is required.");
  }
  const response = await api.get<{ data: SystemTraceResponse }>(`/system-layer/trace/${encodeURIComponent(tag)}`, {
    params: {
      project_id: projectId,
      max_depth: maxDepth,
    },
  });
  return unwrapData(response.data, {
    tag: normalizedTag,
    project_id: projectId ?? null,
    path: [],
    steps: [],
  });
}

export async function getAdvancedLoops(projectId?: string, limit = 20): Promise<{ loops: string[][]; count: number; note?: string }> {
  const response = await api.get<{ data: { loops: string[][]; count: number; note?: string } }>("/system-layer/loops", {
    params: {
      project_id: projectId,
      limit,
    },
  });
  return unwrapData(response.data, { loops: [], count: 0 });
}

export async function getAdvancedBottlenecks(projectId?: string, limit = 10): Promise<{ bottlenecks: SystemBottleneck[]; count: number }> {
  const response = await api.get<{ data: { bottlenecks: SystemBottleneck[]; count: number } }>("/system-layer/bottlenecks", {
    params: {
      project_id: projectId,
      limit,
    },
  });
  return unwrapData(response.data, { bottlenecks: [], count: 0 });
}

export async function createSavedView(payload: {
  project_id: string;
  name: string;
  query?: string;
  script?: string;
}): Promise<SavedEngineeringView> {
  if (!payload.project_id.trim()) {
    throw new Error("project_id is required");
  }
  if (!payload.name.trim()) {
    throw new Error("name is required");
  }
  const response = await api.post<{ data: SavedEngineeringView }>("/views", payload);
  return unwrapData(response.data, {
    id: "",
    project_id: payload.project_id,
    name: payload.name,
    query: payload.query ?? null,
    script: payload.script ?? null,
    created_at: new Date().toISOString(),
  });
}

export async function listSavedViews(projectId: string): Promise<SavedEngineeringView[]> {
  if (!projectId.trim()) {
    return [];
  }
  const response = await api.get<{ data: { views: SavedEngineeringView[] } }>("/views", {
    params: { project_id: projectId },
  });
  return unwrapData(response.data, { views: [] }).views ?? [];
}

export async function createSavedViewVersion(payload: {
  view_id: string;
  snapshot: Record<string, unknown> | Array<Record<string, unknown>>;
  notes?: string;
}): Promise<SavedEngineeringViewVersion> {
  if (!payload.view_id.trim()) {
    throw new Error("view_id is required");
  }
  const response = await api.post<{ data: SavedEngineeringViewVersion }>(`/views/${encodeURIComponent(payload.view_id)}/versions`, {
    snapshot: payload.snapshot,
    notes: payload.notes,
  });
  return unwrapData(response.data, {
    id: "",
    view_id: payload.view_id,
    project_id: "",
    notes: payload.notes ?? null,
    created_at: new Date().toISOString(),
  });
}

export async function listSavedViewVersions(viewId: string): Promise<SavedEngineeringViewVersion[]> {
  if (!viewId.trim()) {
    return [];
  }
  const response = await api.get<{ data: { versions: SavedEngineeringViewVersion[] } }>(`/views/${encodeURIComponent(viewId)}/versions`);
  return unwrapData(response.data, { versions: [] }).versions ?? [];
}

export async function diffSavedViewVersions(beforeVersionId: string, afterVersionId: string): Promise<SavedEngineeringViewDiff> {
  if (!beforeVersionId.trim() || !afterVersionId.trim()) {
    throw new Error("Two version ids are required.");
  }
  const response = await api.post<{ data: SavedEngineeringViewDiff }>("/views/diff", {
    before_version_id: beforeVersionId,
    after_version_id: afterVersionId,
  });
  return unwrapData(response.data, {
    before_version_id: beforeVersionId,
    after_version_id: afterVersionId,
    summary: { added: 0, removed: 0, changed: 0 },
    added: [],
    removed: [],
    changed: [],
  });
}

const buildBearerHeader = (token?: string): Record<string, string> | undefined => {
  const normalized = (token ?? "").trim();
  if (!normalized) {
    return undefined;
  }
  return {
    Authorization: `Bearer ${normalized}`,
  };
};

export async function getProductionHealth(token?: string): Promise<ProductionHealthResponse> {
  const response = await api.get<ProductionHealthResponse>("/production/health", {
    headers: buildBearerHeader(token),
  });
  return response.data;
}

export async function getProductionAuditLogs(limit = 50, token?: string): Promise<ProductionAuditEvent[]> {
  const response = await api.get<{ data: { events: ProductionAuditEvent[] } }>("/production/audit", {
    params: {
      limit,
    },
    headers: buildBearerHeader(token),
  });
  return response.data.data.events;
}

export async function getTagIntelligence(params: {
  projectId?: string;
  category?: "all" | "unused" | "orphans" | "conflicts";
  search?: string;
}): Promise<TagIntelligencePayload> {
  const response = await api.get<{ data: TagIntelligencePayload }>("/tag-intelligence", {
    params: {
      project_id: params.projectId,
      category: params.category ?? "all",
      search: params.search ?? "",
    },
  });
  return unwrapData(response.data, {
    project_id: params.projectId ?? null,
    category: params.category ?? "all",
    search: params.search ?? "",
    rows: [],
    summary: {
      total: 0,
      unused: 0,
      orphans: 0,
      conflicts: 0,
    },
  });
}

export async function exportTagIntelligenceCsv(params: {
  projectId?: string;
  category?: "all" | "unused" | "orphans" | "conflicts";
  search?: string;
}): Promise<Blob> {
  try {
    const response = await api.get<Blob>("/tag-intelligence/export/csv", {
      params: {
        project_id: params.projectId,
        category: params.category ?? "all",
        search: params.search ?? "",
      },
      responseType: "blob",
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "CSV export failed."));
  }
}

export async function exportTagIntelligenceJson(params: {
  projectId?: string;
  category?: "all" | "unused" | "orphans" | "conflicts";
  search?: string;
}): Promise<Blob> {
  try {
    const response = await api.get<Blob>("/tag-intelligence/export/json", {
      params: {
        project_id: params.projectId,
        category: params.category ?? "all",
        search: params.search ?? "",
      },
      responseType: "blob",
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "JSON export failed."));
  }
}

export async function getMonitoring(projectId: string): Promise<Record<string, unknown>> {
  const response = await api.get<Record<string, unknown>>(`/projects/${projectId}/monitoring/summary`);
  return response.data;
}

export async function getReplay(projectId: string): Promise<Record<string, unknown>> {
  const response = await api.get<Record<string, unknown>>(`/projects/${projectId}/replay`);
  return response.data;
}

export async function exportSimulationArtifact(projectId: string): Promise<Record<string, unknown>> {
  const response = await api.get<Record<string, unknown>>(`/projects/${projectId}/export/simulation`);
  return response.data;
}

export async function exportPlantArtifact(projectId: string): Promise<Record<string, unknown>> {
  const response = await api.get<Record<string, unknown>>(`/projects/${projectId}/export/plant`);
  return response.data;
}

export async function exportSignalsArtifact(projectId: string): Promise<Record<string, unknown>> {
  const response = await api.get<Record<string, unknown>>(`/projects/${projectId}/export/signals`);
  return response.data;
}

export async function exportIOMappingArtifact(projectId: string): Promise<Record<string, unknown>> {
  const response = await api.get<Record<string, unknown>>(`/projects/${projectId}/export/io`);
  return response.data;
}

export async function exportEngineeringBundle(projectId: string): Promise<Blob> {
  const response = await api.get<Blob>(`/projects/${projectId}/export/bundle`, {
    responseType: "blob",
  });
  return response.data;
}

export async function runCopilotCommand(payload: {
  command: string;
  provider?: string;
  context?: Record<string, unknown>;
}): Promise<CopilotRunResponse> {
  try {
    const response = await api.post<string>(
      "/copilot/run",
      {
        command: payload.command,
        provider: payload.provider ?? "openai",
        context: payload.context ?? {},
      },
      {
        transformResponse: [(data) => data],
      }
    );

    const raw = response.data;
    if (typeof raw === "string") {
      try {
        return JSON.parse(raw) as CopilotRunResponse;
      } catch {
        return {
          success: false,
          command: payload.command,
          provider: payload.provider ?? "openai",
          mode: "ai_fallback",
          prompt: null,
          warnings: ["Backend returned invalid JSON. Raw response captured."],
          result: {
            raw_response: raw,
          },
          timestamp: new Date().toISOString(),
        };
      }
    }

    if (raw && typeof raw === "object") {
      return raw as unknown as CopilotRunResponse;
    }

    return {
      success: false,
      command: payload.command,
      provider: payload.provider ?? "openai",
      mode: "ai_fallback",
      prompt: null,
      warnings: ["Copilot response was empty."],
      result: {},
      timestamp: new Date().toISOString(),
    };
  } catch (error) {
    throw new Error(getErrorMessage(error, "Copilot request failed."));
  }
}

export async function runCopilotCommandAsync(payload: {
  command: string;
  provider?: string;
  context?: Record<string, unknown>;
}): Promise<CopilotAsyncRunResponse> {
  try {
    const response = await api.post<CopilotAsyncRunResponse>("/copilot/run_async", {
      command: payload.command,
      provider: payload.provider ?? "openai",
      context: payload.context ?? {},
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Copilot async request failed."));
  }
}

export async function getCopilotJobStatus(jobId: string): Promise<CopilotJobStatusResponse> {
  try {
    const response = await api.get<CopilotJobStatusResponse>(`/copilot/status/${jobId}`);
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Copilot job status request failed."));
  }
}

export async function registerCopilotProvider(payload: {
  name: string;
  systemPrompt?: string;
  mockResponse?: string;
  metadata?: Record<string, unknown>;
}): Promise<CopilotProviderResponse> {
  try {
    const response = await api.post<CopilotProviderResponse>("/copilot/provider", {
      name: payload.name,
      system_prompt: payload.systemPrompt,
      mock_response: payload.mockResponse,
      metadata: payload.metadata ?? {},
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, "Copilot provider registration failed."));
  }
}
