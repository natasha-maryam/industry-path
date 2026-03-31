import type {
  ControlLoopRecord,
  EngineeringTableResponse,
  EngineeringTableResponseRow,
  GraphEdge,
  GraphNode,
  IOMappingIssue,
  IOMappingTableRow,
  PlantGraph,
  Project,
  PLCExportVendor,
  SimulationTraceIssue,
  SimulationTracePoint,
  ExportReadinessSummary,
} from "../services/api";
import type { SimulationValidationPanelResponse } from "../services/panelContracts";
import type { GeneratedLogicFile } from "../components/CodeExplorerPanel";

export const SANDBOX_DEMO_PROJECT_ID = "sandbox-demo";
export const SANDBOX_DEMO_PROJECT_VENDOR: PLCExportVendor = "generic_st";

export const SANDBOX_DEMO_PROJECT: Project = {
  id: SANDBOX_DEMO_PROJECT_ID,
  name: "Sandbox Demo Project",
  industry: "industrial-automation",
  description: "Preloaded demo project for sandbox mode.",
  plc_runtime: "beremiz",
  owner: "sandbox",
  status: "active",
  active_version: 1,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const node = (id: string, label: string, node_type: string, status: string): GraphNode => ({
  id,
  label,
  node_type,
  status,
  process_unit: null,
  equipment_type: null,
  instrument_role: null,
  control_role: null,
  signals: [],
});

const edge = (id: string, source: string, target: string, edge_type: string): GraphEdge => ({
  id,
  source,
  target,
  edge_type,
  edge_class: "process",
  line_style: "solid",
  edge_label: null,
});

export const SANDBOX_DEMO_GRAPH: PlantGraph = {
  project_id: SANDBOX_DEMO_PROJECT_ID,
  nodes: [
    node("n-equipment-1", "Pump Controller", "equipment", "ok"),
    node("n-sensor-1", "Flow Sensor", "sensor", "ok"),
    node("n-actuator-1", "Valve Actuator", "actuator", "ok"),
    node("n-controller-1", "PID Controller", "controller", "ok"),
  ],
  edges: [
    edge("e-1", "n-sensor-1", "n-controller-1", "signal"),
    edge("e-2", "n-controller-1", "n-actuator-1", "control"),
    edge("e-3", "n-actuator-1", "n-equipment-1", "process"),
  ],
};

const linkRef = (tag: string): { tag: string; provenance: "sentinel_fallback"; inferred: false } => ({
  tag,
  provenance: "sentinel_fallback",
  inferred: false,
});

// Keep this intentionally minimal: UI rendering code has many defaults.
const makeRow = (partial: Partial<EngineeringTableResponseRow> & { tag: string }): EngineeringTableResponseRow =>
  partial as EngineeringTableResponseRow;

export const SANDBOX_DEMO_ENGINEERING: EngineeringTableResponse = {
  project_id: SANDBOX_DEMO_PROJECT_ID,
  warnings: [],
  summary: {
    total_rows: 3,
    grounded_rows: 3,
    inferred_rows: 0,
    orphan_rows: 0,
    controlled_rows: 3,
    actuated_rows: 1,
    avg_confidence: 0.9,
    distinct_systems: 1,
    distinct_document_sources: 1,
  },
  rows: [
    makeRow({
      id: "row-1",
      tag: "FLOW_ACTUAL",
      type: "REAL",
      subtype: "process",
      description: "Measured flow rate",
      system: "pump_system",
      equipment: "flow_sensor_1",
      process_role: "sensor",
      measures: ["FLOW_RATE"],
      controls: [],
      controlled_by: [],
      signal_inputs: ["FLOW_ACTUAL"],
      signal_outputs: [],
      upstream: [],
      downstream: ["FLOW_SETPOINT"],
      upstream_links: [],
      downstream_links: [linkRef("FLOW_SETPOINT")],
      has_inferred_upstream: false,
      has_inferred_downstream: false,
      flow_path: ["FLOW_ACTUAL"],
      current_value: "12.3",
      state: "ok",
      setpoint: null,
      mode: "auto",
      unit: "m3/h",
      range_min: 0,
      range_max: 100,
      fail_state: null,
      power: null,
      document_source: ["pid_demo.pdf"],
      line_reference: ["L1"],
      confidence: 0.9,
      num_connections: 1,
      num_upstream: 0,
      num_downstream: 1,
      control_chain: [],
      flow_chain: ["FLOW_ACTUAL", "FLOW_SETPOINT"],
      is_orphan: false,
      is_controlled: false,
      is_actuated: false,
      warnings: [],
      grounded_fields: {},
      derived_fields: {},
      traceability: [],
    }),
    makeRow({
      id: "row-2",
      tag: "FLOW_SETPOINT",
      type: "REAL",
      subtype: "process",
      description: "Desired flow rate",
      system: "pump_system",
      equipment: "pid_controller_1",
      process_role: "controller",
      measures: [],
      controls: ["FLOW_CONTROL"],
      controlled_by: ["PID_OUTPUT"],
      signal_inputs: ["PID_OUTPUT"],
      signal_outputs: ["FLOW_SETPOINT"],
      upstream: ["PID_OUTPUT"],
      downstream: ["VALVE_COMMAND"],
      upstream_links: [linkRef("PID_OUTPUT")],
      downstream_links: [linkRef("VALVE_COMMAND")],
      has_inferred_upstream: false,
      has_inferred_downstream: false,
      flow_path: ["FLOW_SETPOINT"],
      current_value: "15.0",
      state: "ok",
      setpoint: "15.0",
      mode: "auto",
      unit: "m3/h",
      range_min: 0,
      range_max: 100,
      fail_state: null,
      power: null,
      document_source: ["pid_demo.pdf"],
      line_reference: ["L2"],
      confidence: 0.9,
      num_connections: 2,
      num_upstream: 1,
      num_downstream: 1,
      control_chain: ["FLOW_CONTROL"],
      flow_chain: ["FLOW_SETPOINT", "VALVE_COMMAND"],
      is_orphan: false,
      is_controlled: true,
      is_actuated: false,
      warnings: [],
      grounded_fields: {},
      derived_fields: {},
      traceability: [],
    }),
    makeRow({
      id: "row-3",
      tag: "VALVE_COMMAND",
      type: "REAL",
      subtype: "process",
      description: "Commanded valve position",
      system: "pump_system",
      equipment: "valve_actuator_1",
      process_role: "actuator",
      measures: [],
      controls: ["VALVE_CONTROL"],
      controlled_by: ["PID_OUTPUT"],
      signal_inputs: ["PID_OUTPUT"],
      signal_outputs: ["VALVE_COMMAND"],
      upstream: ["PID_OUTPUT"],
      downstream: [],
      upstream_links: [linkRef("PID_OUTPUT")],
      downstream_links: [],
      has_inferred_upstream: false,
      has_inferred_downstream: false,
      flow_path: ["VALVE_COMMAND"],
      current_value: "0.42",
      state: "ok",
      setpoint: null,
      mode: "auto",
      unit: "%",
      range_min: 0,
      range_max: 100,
      fail_state: null,
      power: null,
      document_source: ["pid_demo.pdf"],
      line_reference: ["L3"],
      confidence: 0.85,
      num_connections: 1,
      num_upstream: 1,
      num_downstream: 0,
      control_chain: ["VALVE_CONTROL"],
      flow_chain: ["VALVE_COMMAND"],
      is_orphan: false,
      is_controlled: true,
      is_actuated: true,
      warnings: [],
      grounded_fields: {},
      derived_fields: {},
      traceability: [],
    }),
  ],
};

export const SANDBOX_DEMO_CONTROL_LOOPS: ControlLoopRecord[] = [
  {
    id: "loop-1",
    project_id: SANDBOX_DEMO_PROJECT_ID,
    loop_tag: "FLOW_LOOP",
    sensor_tag: "FLOW_ACTUAL",
    actuator_tag: "VALVE_COMMAND",
    loop_type: "pid",
    control_strategy: "pid",
    status: "active",
    confidence: 0.9,
    created_at: new Date().toISOString(),
    controller_tag: "PID_CONTROLLER",
    chain: ["FLOW_ACTUAL", "PID_OUTPUT", "VALVE_COMMAND"],
  },
];

export const SANDBOX_DEMO_IO_MAPPING_ROWS: IOMappingTableRow[] = [
  {
    tag: "FLOW_ACTUAL",
    device_type: "sensor",
    signal_type: "REAL",
    io_type: "AI",
    plc_id: "plc-1",
    slot: 1,
    channel: 1,
    description: "Flow sensor input",
    equipment_id: "flow_sensor_1",
  },
  {
    tag: "VALVE_COMMAND",
    device_type: "actuator",
    signal_type: "REAL",
    io_type: "AO",
    plc_id: "plc-1",
    slot: 1,
    channel: 2,
    description: "Valve command output",
    equipment_id: "valve_actuator_1",
  },
];

export const SANDBOX_DEMO_IO_MAPPING_ISSUES: IOMappingIssue[] = [];

export const SANDBOX_DEMO_ST_FILES: GeneratedLogicFile[] = [
  {
    path: "main.st",
    content: `PROGRAM main
// Sandbox demo code. This is not meant to run on a real PLC.

VAR
  flow_sp : REAL := 15.0;
  flow_pv : REAL := 12.3;
END_VAR

// (demo) valve command derived from flow error
`,
  },
];

export const SANDBOX_DEMO_LOGIC_BUNDLED_CODE = `(* ===== FILE: main.st ===== *)
${SANDBOX_DEMO_ST_FILES[0]?.content ?? ""}`;

export const SANDBOX_DEMO_SIMULATION_TRACE: SimulationTracePoint[] = [
  { tag: "FLOW_ACTUAL", value: 10.8, time: 0 },
  { tag: "FLOW_ACTUAL", value: 12.3, time: 1 },
  { tag: "VALVE_COMMAND", value: 0.35, time: 1 },
  { tag: "VALVE_COMMAND", value: 0.42, time: 2 },
];

export const SANDBOX_DEMO_SIMULATION_ISSUES: SimulationTraceIssue[] = [];

export const SANDBOX_DEMO_SIMULATION_VALIDATION: SimulationValidationPanelResponse = {
  project_id: SANDBOX_DEMO_PROJECT_ID,
  simulation_run_id: "sim-demo-1",
  validated_at: new Date().toISOString(),
  overall_status: "success",
  scenarios_passed: 1,
  scenarios_failed: 0,
  scenarios_warning: 0,
  scenarios: [
    {
      scenario_id: "startup_sequence_demo",
      scenario_name: "startup_sequence",
      status: "success",
      cycle_time_ms: 1200,
      duration_s: 2.4,
      alarms_triggered: 0,
      message: "Demo simulation passed in sandbox.",
    },
  ],
};

export function buildSandboxExportPaywallReadiness(exportAllowed: boolean): ExportReadinessSummary {
  // This structure is used purely for UI gating/readiness sections.
  return {
    project_id: SANDBOX_DEMO_PROJECT_ID,
    vendor: "generic_st",
    source_mode: "live",
    source_version_id: null,
    checks: [],
    warnings: [],
    errors: [],
    export_allowed: exportAllowed,
    export_blocked: !exportAllowed,
    deploy_allowed: false,
    deploy_blocked: true,
    unresolved_physical_io_tags: [],
    unresolved_internal_tags: [],
    auto_resolved_derived_tags: [],
    unknown_unclassified_tags: [],
    export_blockers: [],
    deploy_blockers: [],
    generated_at: new Date().toISOString(),
  };
}

