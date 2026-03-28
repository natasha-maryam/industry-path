import type { SystemContext, SystemImpact } from "./systemContext";

export type SystemContextPanelView = {
  tag: string;
  isa: {
    rawTag: string;
    loopId: string;
    deviceType: string;
    function: string;
    modifier: string;
    fullType: string;
  };
  process: {
    unit: string;
    area: string;
    equipment: string;
    service: string;
  };
  behaviorText: string;
  cause: string[];
  effect: string[];
  impact: string[];
  upstream: string[];
  downstream: string[];
  interlocks: Array<{ trigger: string; action: string }>;
  alarmTags: string[];
  trips: string[];
  permissives: string[];
  controlStrategy: string;
  controlMode: string;
  role: string;
  logicBlocks: string[];
  setpoints: unknown;
  runtimeState: string;
  runtimeMode: string;
  resolvedContext: SystemContext | null;
};

type MapOptions = {
  selectedTag: string;
  backendPayload?: unknown;
  fallbackContext?: SystemContext | null;
  fallbackBehavior?: string;
  fallbackImpact?: SystemImpact | null;
};

const asRecord = (value: unknown): Record<string, unknown> | null => {
  if (!value || typeof value !== "object") {
    return null;
  }
  return value as Record<string, unknown>;
};

const asString = (value: unknown, fallback = "—"): string => {
  if (typeof value !== "string") {
    return fallback;
  }
  const normalized = value.trim();
  return normalized.length > 0 ? normalized : fallback;
};

const asStringArray = (value: unknown): string[] => {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => (typeof item === "string" ? item.trim() : ""))
    .filter((item) => item.length > 0);
};

const uniqueStrings = (values: string[]): string[] => {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const value of values) {
    if (seen.has(value)) {
      continue;
    }
    seen.add(value);
    result.push(value);
  }
  return result;
};

const preferString = (primary: string | undefined, fallback: string | undefined): string | undefined => {
  return primary && primary.trim().length > 0 ? primary : fallback;
};

const preferArray = (primary: string[] | undefined, fallback: string[] | undefined): string[] => {
  const left = primary || [];
  const right = fallback || [];
  return left.length > 0 ? uniqueStrings(left.concat(right)) : uniqueStrings(right);
};

const preferInterlocks = (
  primary: Array<{ trigger: string; action: string }> | undefined,
  fallback: Array<{ trigger: string; action: string }> | undefined
): Array<{ trigger: string; action: string }> => {
  const left = primary || [];
  const right = fallback || [];
  const merged = left.length > 0 ? left.concat(right) : right;
  const seen = new Set<string>();
  const result: Array<{ trigger: string; action: string }> = [];
  for (const item of merged) {
    const trigger = (item?.trigger || "").trim();
    const action = (item?.action || "").trim();
    if (!trigger && !action) {
      continue;
    }
    const key = `${trigger}__${action}`;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    result.push({ trigger, action });
  }
  return result;
};

const mergeContexts = (backend: SystemContext | null, fallback: SystemContext | null): SystemContext | null => {
  if (!backend && !fallback) {
    return null;
  }
  if (!backend) {
    return fallback;
  }
  if (!fallback) {
    return backend;
  }

  return {
    tag: preferString(backend.tag, fallback.tag) || fallback.tag,
    isa: {
      raw_tag: preferString(backend.isa.raw_tag, fallback.isa.raw_tag) || fallback.isa.raw_tag,
      loop_id: preferString(backend.isa.loop_id, fallback.isa.loop_id),
      device_type: preferString(backend.isa.device_type, fallback.isa.device_type),
      function: preferString(backend.isa.function, fallback.isa.function),
      modifier: preferString(backend.isa.modifier, fallback.isa.modifier),
      full_type: preferString(backend.isa.full_type, fallback.isa.full_type),
    },
    process: {
      unit: preferString(backend.process.unit, fallback.process.unit),
      area: preferString(backend.process.area, fallback.process.area),
      equipment: preferString(backend.process.equipment, fallback.process.equipment),
      service: preferString(backend.process.service, fallback.process.service),
    },
    pid: {
      upstream_tags: preferArray(backend.pid.upstream_tags, fallback.pid.upstream_tags),
      downstream_tags: preferArray(backend.pid.downstream_tags, fallback.pid.downstream_tags),
      upstream_equipment: preferArray(backend.pid.upstream_equipment, fallback.pid.upstream_equipment),
      downstream_equipment: preferArray(backend.pid.downstream_equipment, fallback.pid.downstream_equipment),
      valves: preferArray(backend.pid.valves, fallback.pid.valves),
      pumps: preferArray(backend.pid.pumps, fallback.pid.pumps),
      instruments: preferArray(backend.pid.instruments, fallback.pid.instruments),
      flow_direction: preferString(backend.pid.flow_direction, fallback.pid.flow_direction),
    },
    control: {
      role: preferString(backend.control.role, fallback.control.role),
      control_strategy: preferString(backend.control.control_strategy, fallback.control.control_strategy),
      control_mode: preferString(backend.control.control_mode, fallback.control.control_mode),
      setpoints: backend.control.setpoints ?? fallback.control.setpoints,
      control_inputs: preferArray(backend.control.control_inputs, fallback.control.control_inputs),
      control_outputs: preferArray(backend.control.control_outputs, fallback.control.control_outputs),
      loops: preferArray(backend.control.loops, fallback.control.loops),
      logic_blocks: preferArray(backend.control.logic_blocks, fallback.control.logic_blocks),
    },
    safety: {
      interlocks: preferInterlocks(backend.safety.interlocks, fallback.safety.interlocks),
      trips: preferArray(backend.safety.trips, fallback.safety.trips),
      permissives: preferArray(backend.safety.permissives, fallback.safety.permissives),
      alarm_tags: preferArray(backend.safety.alarm_tags, fallback.safety.alarm_tags),
    },
    graph: {
      upstream: preferArray(backend.graph.upstream, fallback.graph.upstream),
      downstream: preferArray(backend.graph.downstream, fallback.graph.downstream),
      edges: (backend.graph.edges && backend.graph.edges.length > 0 ? backend.graph.edges : fallback.graph.edges) || [],
    },
    runtime: {
      state: preferString(backend.runtime.state, fallback.runtime.state),
      mode: preferString(backend.runtime.mode, fallback.runtime.mode),
      dependencies: preferArray(backend.runtime.dependencies, fallback.runtime.dependencies),
      influences: preferArray(backend.runtime.influences, fallback.runtime.influences),
    },
  };
};

const extractBackendContext = (payload: unknown): SystemContext | null => {
  const root = asRecord(payload);
  if (!root) {
    return null;
  }
  const nested = asRecord(root.system_context) || asRecord(root.context) || asRecord(asRecord(root.why_engine)?.system_context) || root;

  const tag = asString(nested.tag || root.tag, "");
  if (!tag) {
    return null;
  }

  const isa = asRecord(nested.isa) || {};
  const process = asRecord(nested.process) || {};
  const pid = asRecord(nested.pid) || {};
  const control = asRecord(nested.control) || {};
  const safety = asRecord(nested.safety) || {};
  const graph = asRecord(nested.graph) || {};
  const runtime = asRecord(nested.runtime) || {};

  const interlocksRaw = Array.isArray(safety.interlocks) ? safety.interlocks : [];
  const interlocks = interlocksRaw
    .map((item) => {
      const row = asRecord(item);
      if (!row) {
        return null;
      }
      return {
        trigger: asString(row.trigger, "-"),
        action: asString(row.action, "-"),
      };
    })
    .filter((item): item is { trigger: string; action: string } => Boolean(item));

  return {
    tag,
    isa: {
      raw_tag: asString(isa.raw_tag || tag, tag),
      loop_id: asString(isa.loop_id, "") || undefined,
      device_type: asString(isa.device_type, "") || undefined,
      function: asString(isa.function, "") || undefined,
      modifier: asString(isa.modifier, "") || undefined,
      full_type: asString(isa.full_type, "") || undefined,
    },
    process: {
      unit: asString(process.unit, "") || undefined,
      area: asString(process.area, "") || undefined,
      equipment: asString(process.equipment, "") || undefined,
      service: asString(process.service, "") || undefined,
    },
    pid: {
      upstream_tags: asStringArray(pid.upstream_tags),
      downstream_tags: asStringArray(pid.downstream_tags),
      upstream_equipment: asStringArray(pid.upstream_equipment),
      downstream_equipment: asStringArray(pid.downstream_equipment),
      valves: asStringArray(pid.valves),
      pumps: asStringArray(pid.pumps),
      instruments: asStringArray(pid.instruments),
      flow_direction: asString(pid.flow_direction, "") || undefined,
    },
    control: {
      role: asString(control.role, "") || undefined,
      control_strategy: asString(control.control_strategy, "") || undefined,
      control_mode: asString(control.control_mode, "") || undefined,
      setpoints: control.setpoints,
      control_inputs: asStringArray(control.control_inputs),
      control_outputs: asStringArray(control.control_outputs),
      loops: asStringArray(control.loops),
      logic_blocks: asStringArray(control.logic_blocks),
    },
    safety: {
      interlocks,
      trips: asStringArray(safety.trips),
      permissives: asStringArray(safety.permissives),
      alarm_tags: asStringArray(safety.alarm_tags),
    },
    graph: {
      upstream: asStringArray(graph.upstream),
      downstream: asStringArray(graph.downstream),
      edges: Array.isArray(graph.edges) ? (graph.edges as SystemContext["graph"]["edges"]) : [],
    },
    runtime: {
      state: asString(runtime.state, "") || undefined,
      mode: asString(runtime.mode, "") || undefined,
      dependencies: asStringArray(runtime.dependencies),
      influences: asStringArray(runtime.influences),
    },
  };
};

const extractBehaviorText = (payload: unknown, fallback: string): string => {
  const root = asRecord(payload);
  if (!root) {
    return fallback;
  }

  const systemContext = asRecord(root.system_context) || asRecord(asRecord(root.why_engine)?.system_context);
  const explanation = asRecord(root.explanation) || asRecord(root.narrative) || asRecord(asRecord(root.why_engine)?.explanation);
  const behavior =
    asString(root.behavior, "") ||
    asString(root.why, "") ||
    asString(root.explanation, "") ||
    asString(systemContext?.behavior, "") ||
    asString(root.behavior_summary, "") ||
    asString(explanation?.behavior, "") ||
    asString(explanation?.summary, "");

  return behavior || fallback;
};

const extractImpact = (payload: unknown, fallback: SystemImpact | null, ctx: SystemContext | null): SystemImpact => {
  const root = asRecord(payload);
  const impactRecord = asRecord(root?.impact) || asRecord(root?.cause_effect) || asRecord(asRecord(root?.why_engine)?.impact);

  const cause = uniqueStrings(
    asStringArray(impactRecord?.cause).concat(fallback?.cause || []).concat(ctx?.graph.upstream || [])
  );
  const effect = uniqueStrings(
    asStringArray(impactRecord?.effect).concat(fallback?.effect || []).concat(ctx?.graph.downstream || [])
  );
  const impact = uniqueStrings(
    asStringArray(impactRecord?.impact)
      .concat(fallback?.impact || [])
      .concat(ctx?.safety.alarm_tags || [])
      .concat(ctx?.graph.downstream || [])
  );

  return {
    cause,
    effect,
    impact,
  };
};

export function mapSystemContextToPanelView(options: MapOptions): SystemContextPanelView {
  const fallbackContext = options.fallbackContext || null;
  const backendContext = extractBackendContext(options.backendPayload);
  const resolvedContext = mergeContexts(backendContext, fallbackContext);
  const selectedTag = asString(options.selectedTag, "-");

  const impact = extractImpact(options.backendPayload, options.fallbackImpact || null, resolvedContext);
  const behaviorText = extractBehaviorText(
    options.backendPayload,
    options.fallbackBehavior || "No engineering explanation available for this tag yet."
  );

  return {
    tag: resolvedContext?.tag || selectedTag,
    isa: {
      rawTag: resolvedContext?.isa.raw_tag || selectedTag,
      loopId: resolvedContext?.isa.loop_id || "—",
      deviceType: resolvedContext?.isa.device_type || "—",
      function: resolvedContext?.isa.function || "—",
      modifier: resolvedContext?.isa.modifier || "—",
      fullType: resolvedContext?.isa.full_type || "—",
    },
    process: {
      unit: resolvedContext?.process.unit || "—",
      area: resolvedContext?.process.area || "—",
      equipment: resolvedContext?.process.equipment || "—",
      service: resolvedContext?.process.service || "—",
    },
    behaviorText,
    cause: impact.cause,
    effect: impact.effect,
    impact: impact.impact,
    upstream: resolvedContext?.graph.upstream || [],
    downstream: resolvedContext?.graph.downstream || [],
    interlocks: resolvedContext?.safety.interlocks || [],
    alarmTags: resolvedContext?.safety.alarm_tags || [],
    trips: resolvedContext?.safety.trips || [],
    permissives: resolvedContext?.safety.permissives || [],
    controlStrategy: resolvedContext?.control.control_strategy || "—",
    controlMode: resolvedContext?.control.control_mode || resolvedContext?.runtime.mode || "—",
    role: resolvedContext?.control.role || "—",
    logicBlocks: resolvedContext?.control.logic_blocks || [],
    setpoints: resolvedContext?.control.setpoints,
    runtimeState: resolvedContext?.runtime.state || "—",
    runtimeMode: resolvedContext?.runtime.mode || "—",
    resolvedContext,
  };
}
