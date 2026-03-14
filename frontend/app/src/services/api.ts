import axios from "axios";
export * from "./pipelineStatus";
export * from "./panelContracts";

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

export type VerifySTOptions = {
  maxAttempts?: number;
  initialDelayMs?: number;
  backoffFactor?: number;
};

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

export type IOMappingGenerationResult = {
  project_id: string;
  rows: IOMappingTableRow[];
  summary: IOMappingSummaryByType;
  total: number;
};

export type GenerateIOMappingOptions = {
  maxAttempts?: number;
  initialDelayMs?: number;
  backoffFactor?: number;
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

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api",
});

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
    project_id: payload.project_id,
    rows,
    summary,
    total: rows.length,
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

export async function verifySTLogic(projectId: string): Promise<STVerificationServiceResponse> {
  const response = await api.post<STValidationReport>(`/projects/${projectId}/logic/validate-logic`);
  return adaptSTVerificationResponse(response.data);
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
  const response = await api.post<IOMappingGenerationApiResponse>(`/projects/${projectId}/logic/generate-io-mapping`);
  return adaptIOMappingGenerationResponse(response.data);
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
