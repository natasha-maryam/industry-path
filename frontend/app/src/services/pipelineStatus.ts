export const PIPELINE_STAGE_KEYS = [
  "extraction",
  "normalization",
  "plant_graph",
  "control_loop_discovery",
  "engineering_validation",
  "logic_completion",
  "st_generation",
  "st_verification",
  "io_mapping",
  "runtime_validation",
  "simulation_validation",
  "version_snapshot",
] as const;

export const PIPELINE_STAGE_STATES = ["idle", "running", "success", "failed", "warning", "blocked"] as const;

export type PipelineStageKey = (typeof PIPELINE_STAGE_KEYS)[number];
export type PipelineStageState = (typeof PIPELINE_STAGE_STATES)[number];

export type PipelineStageStatusMap = Record<PipelineStageKey, PipelineStageState>;

export type PipelinePrerequisiteMap = Partial<Record<PipelineStageKey, PipelineStageKey[]>>;

export type PipelineStatusModel = {
  projectId: string;
  runId?: string | null;
  statuses: PipelineStageStatusMap;
  updatedAt?: string | null;
};

export type MockPipelineStagePayload = {
  stage?: string;
  name?: string;
  key?: string;
  status?: string;
  state?: string;
};

export type MockPipelineApiResponse = {
  project_id?: string;
  projectId?: string;
  run_id?: string | null;
  runId?: string | null;
  updated_at?: string | null;
  updatedAt?: string | null;
  statuses?: Partial<Record<string, string>>;
  stages?: MockPipelineStagePayload[];
};

const STAGE_KEY_ALIASES: Record<string, PipelineStageKey> = {
  extraction: "extraction",
  normalization: "normalization",
  plant_graph: "plant_graph",
  plantgraph: "plant_graph",
  control_loop_discovery: "control_loop_discovery",
  controlloopdiscovery: "control_loop_discovery",
  engineering_validation: "engineering_validation",
  engineeringvalidation: "engineering_validation",
  logic_completion: "logic_completion",
  logiccompletion: "logic_completion",
  st_generation: "st_generation",
  stgeneration: "st_generation",
  st_verification: "st_verification",
  stverification: "st_verification",
  io_mapping: "io_mapping",
  iomapping: "io_mapping",
  runtime_validation: "runtime_validation",
  runtimevalidation: "runtime_validation",
  simulation_validation: "simulation_validation",
  simulationvalidation: "simulation_validation",
  version_snapshot: "version_snapshot",
  versionsnapshot: "version_snapshot",
};

const STAGE_STATE_ALIASES: Record<string, PipelineStageState> = {
  idle: "idle",
  queued: "idle",
  pending: "idle",
  running: "running",
  in_progress: "running",
  inprogress: "running",
  success: "success",
  succeeded: "success",
  completed: "success",
  failed: "failed",
  error: "failed",
  warning: "warning",
  warn: "warning",
  blocked: "blocked",
  skipped: "blocked",
};

const normalizeToken = (value: string): string => value.toLowerCase().replace(/[^a-z0-9]/g, "");

const toPipelineStageKey = (value: string | undefined): PipelineStageKey | null => {
  if (!value) {
    return null;
  }

  const normalized = normalizeToken(value);
  const aliasMatch = STAGE_KEY_ALIASES[normalized];
  if (aliasMatch) {
    return aliasMatch;
  }

  const directMatch = PIPELINE_STAGE_KEYS.find((key) => normalizeToken(key) === normalized);
  return directMatch ?? null;
};

export const toPipelineStageState = (value: string | undefined): PipelineStageState => {
  if (!value) {
    return "idle";
  }

  const normalized = normalizeToken(value);
  return STAGE_STATE_ALIASES[normalized] ?? "idle";
};

export const createInitialPipelineStatuses = (initialState: PipelineStageState = "idle"): PipelineStageStatusMap =>
  PIPELINE_STAGE_KEYS.reduce((accumulator, stage) => {
    accumulator[stage] = initialState;
    return accumulator;
  }, {} as PipelineStageStatusMap);

export const PIPELINE_PREREQUISITES: PipelinePrerequisiteMap = {
  normalization: ["extraction"],
  plant_graph: ["normalization"],
  control_loop_discovery: ["plant_graph"],
  engineering_validation: ["control_loop_discovery"],
  logic_completion: ["engineering_validation"],
  st_generation: ["logic_completion"],
  st_verification: ["st_generation"],
  io_mapping: ["st_verification"],
  runtime_validation: ["io_mapping"],
  simulation_validation: ["runtime_validation"],
  version_snapshot: ["simulation_validation"],
};

export const isStageSuccessful = (statuses: PipelineStageStatusMap, stage: PipelineStageKey): boolean =>
  statuses[stage] === "success";

export const getMissingStagePrerequisites = (
  statuses: PipelineStageStatusMap,
  stage: PipelineStageKey,
  prerequisiteMap: PipelinePrerequisiteMap = PIPELINE_PREREQUISITES
): PipelineStageKey[] => {
  const prerequisites = prerequisiteMap[stage] ?? [];
  return prerequisites.filter((requiredStage) => !isStageSuccessful(statuses, requiredStage));
};

export const canRunStage = (
  statuses: PipelineStageStatusMap,
  stage: PipelineStageKey,
  prerequisiteMap: PipelinePrerequisiteMap = PIPELINE_PREREQUISITES
): boolean => getMissingStagePrerequisites(statuses, stage, prerequisiteMap).length === 0;

export const applySnapshotTrigger = (statuses: PipelineStageStatusMap): PipelineStageStatusMap => {
  return { ...statuses };
};

export const adaptMockPipelineStatusResponse = (
  payload: MockPipelineApiResponse,
  fallbackProjectId = "mock-project"
): PipelineStatusModel => {
  const statuses = createInitialPipelineStatuses();

  if (payload.statuses) {
    for (const [rawStageKey, rawState] of Object.entries(payload.statuses)) {
      const stageKey = toPipelineStageKey(rawStageKey);
      if (!stageKey) {
        continue;
      }
      statuses[stageKey] = toPipelineStageState(rawState);
    }
  }

  if (payload.stages) {
    for (const stage of payload.stages) {
      const stageKey = toPipelineStageKey(stage.stage ?? stage.name ?? stage.key);
      if (!stageKey) {
        continue;
      }
      statuses[stageKey] = toPipelineStageState(stage.status ?? stage.state);
    }
  }

  return {
    projectId: payload.project_id ?? payload.projectId ?? fallbackProjectId,
    runId: payload.run_id ?? payload.runId ?? null,
    statuses,
    updatedAt: payload.updated_at ?? payload.updatedAt ?? null,
  };
};

export const createMockPipelineStatusResponse = (
  overrides: Partial<MockPipelineApiResponse> = {},
  statusOverrides: Partial<Record<PipelineStageKey, PipelineStageState>> = {}
): MockPipelineApiResponse => ({
  project_id: "mock-project",
  run_id: "mock-run-001",
  updated_at: new Date().toISOString(),
  statuses: {
    extraction: "success",
    normalization: "success",
    plant_graph: "running",
    control_loop_discovery: "idle",
    engineering_validation: "idle",
    logic_completion: "idle",
    st_generation: "idle",
    st_verification: "idle",
    io_mapping: "idle",
    runtime_validation: "idle",
    simulation_validation: "idle",
    version_snapshot: "idle",
    ...statusOverrides,
  },
  ...overrides,
});