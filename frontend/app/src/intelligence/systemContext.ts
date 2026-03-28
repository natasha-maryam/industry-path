import type {
  ControlLoopRecord,
  EngineeringTableResponseRow,
  GraphEdge,
  GraphNode,
  RuntimeEvaluationCycle,
} from "../services/api";

type RuntimeValidationSnapshot = {
  runtime_state?: string;
};

export type SystemContext = {
  tag: string;

  isa: {
    raw_tag: string;
    loop_id?: string;
    device_type?: string;
    function?: string;
    modifier?: string;
    full_type?: string;
  };

  process: {
    unit?: string;
    area?: string;
    equipment?: string;
    service?: string;
  };

  pid: {
    upstream_tags: string[];
    downstream_tags: string[];
    upstream_equipment: string[];
    downstream_equipment: string[];
    valves: string[];
    pumps: string[];
    instruments: string[];
    flow_direction?: string;
  };

  control: {
    role?: string;
    control_strategy?: string;
    control_mode?: string;
    setpoints?: unknown;
    control_inputs: string[];
    control_outputs: string[];
    loops: string[];
    logic_blocks: string[];
  };

  safety: {
    interlocks: Array<{ trigger: string; action: string }>;
    trips: string[];
    permissives: string[];
    alarm_tags: string[];
  };

  graph: {
    upstream: string[];
    downstream: string[];
    edges: GraphEdge[];
  };

  runtime: {
    state?: string;
    mode?: string;
    dependencies: string[];
    influences: string[];
  };
};

export type SystemImpact = {
  cause: string[];
  effect: string[];
  impact: string[];
};

type BuildSystemContextOptions = {
  tag: string;
  graphNodes: GraphNode[];
  graphEdges: GraphEdge[];
  narrativeText?: string;
  engineeringRows?: EngineeringTableResponseRow[];
  controlLoops?: ControlLoopRecord[];
  runtimeDiagnostics?: RuntimeEvaluationCycle | null;
  runtimeValidation?: RuntimeValidationSnapshot | null;
  runtimeTelemetryTags?: Record<string, unknown>;
};

const toComparableToken = (value: string): string => value.toUpperCase().replace(/[^A-Z0-9]/g, "");

const isSameTag = (left: string, right: string): boolean => {
  return toComparableToken(left) === toComparableToken(right);
};

const uniqueStrings = (values: string[]): string[] => {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const value of values) {
    const normalized = value.trim();
    if (!normalized || seen.has(normalized)) {
      continue;
    }
    seen.add(normalized);
    result.push(normalized);
  }
  return result;
};

const getEdgesForTag = (tag: string, graphEdges: GraphEdge[]): GraphEdge[] => {
  const token = toComparableToken(tag);
  return graphEdges.filter((edge) => toComparableToken(edge.source) === token || toComparableToken(edge.target) === token);
};

const inferRoleFromTag = (tag: string): string | undefined => {
  const normalized = toComparableToken(tag);
  if (!normalized) {
    return undefined;
  }
  if (normalized.includes("IT")) {
    return "sensor";
  }
  if (normalized.includes("CV")) {
    return "actuator";
  }
  if (normalized.includes("C")) {
    return "controller";
  }
  return undefined;
};

export function parseISATag(tag: string) {
  const match = tag.match(/^([A-Z]+)-?(\d+)?$/);

  const letters = match?.[1] || "";
  const loop = match?.[2];

  return {
    raw_tag: tag,
    loop_id: loop,
    device_type: letters[0],
    function: letters[1],
    modifier: letters.slice(2),
    full_type: letters,
  };
}

function detectRole(sentences: string[]): string | undefined {
  const text = sentences.join(" ").toLowerCase();
  if (text.includes("sensor") || text.includes("transmitter") || text.includes("measure")) {
    return "sensor";
  }
  if (text.includes("controller") || text.includes("pid") || text.includes("cascade")) {
    return "controller";
  }
  if (text.includes("valve") || text.includes("actuator") || text.includes("drive") || text.includes("pump")) {
    return "actuator";
  }
  return undefined;
}

function detectStrategy(sentences: string[]): string | undefined {
  const text = sentences.join(" ").toLowerCase();
  if (text.includes("cascade")) {
    return "cascade";
  }
  if (text.includes("feedforward")) {
    return "feedforward";
  }
  if (text.includes("on/off") || text.includes("on off")) {
    return "on_off";
  }
  if (text.includes("pid") || text.includes("proportional")) {
    return "pid";
  }
  return undefined;
}

function detectMode(sentences: string[]): string | undefined {
  const text = sentences.join(" ").toLowerCase();
  if (text.includes("auto")) {
    return "auto";
  }
  if (text.includes("manual")) {
    return "manual";
  }
  if (text.includes("remote")) {
    return "remote";
  }
  return undefined;
}

function extractTagTokens(sentences: string[]): string[] {
  const tokenPattern = /\b[A-Z]{1,5}-?\d{0,4}\b/g;
  return uniqueStrings(
    sentences.flatMap((sentence) => {
      const matches = sentence.match(tokenPattern);
      return matches ?? [];
    })
  );
}

function extractInputs(sentences: string[]): string[] {
  return extractTagTokens(sentences);
}

function extractOutputs(sentences: string[]): string[] {
  return extractTagTokens(sentences);
}

function extractLoops(sentences: string[]): string[] {
  const loopPattern = /\b(?:LOOP|L)\s*-?\s*(\d{1,5})\b/gi;
  return uniqueStrings(
    sentences.flatMap((sentence) => {
      const matches = [...sentence.matchAll(loopPattern)];
      return matches.map((match) => `L-${match[1]}`);
    })
  );
}

function extractLogic(sentences: string[]): string[] {
  return uniqueStrings(
    sentences
      .map((sentence) => sentence.trim())
      .filter((sentence) => sentence.length > 0)
      .slice(0, 8)
  );
}

function extractSetpoints(sentences: string[]): unknown {
  const setpointPattern = /(?:SP|SETPOINT)\s*[:=]?\s*(-?\d+(?:\.\d+)?)/gi;
  const values = uniqueStrings(
    sentences.flatMap((sentence) => {
      const matches = [...sentence.matchAll(setpointPattern)];
      return matches.map((match) => match[1]);
    })
  );
  return values.length > 0 ? values : undefined;
}

export function getNarrativeContext(tag: string, narrative: string) {
  const sentences = narrative.split(".").map((sentence) => sentence.trim()).filter((sentence) => sentence.length > 0);
  const tagToken = toComparableToken(tag);
  const relevant = sentences.filter((sentence) => toComparableToken(sentence).includes(tagToken));

  return {
    role: detectRole(relevant),
    control_strategy: detectStrategy(relevant),
    control_mode: detectMode(relevant),
    control_inputs: extractInputs(relevant),
    control_outputs: extractOutputs(relevant),
    loops: extractLoops(relevant),
    logic_blocks: extractLogic(relevant),
    setpoints: extractSetpoints(relevant),
  };
}

export function getGraphContext(tag: string, graphEdges: GraphEdge[], fallback?: { upstream?: string[]; downstream?: string[] }) {
  const edges = getEdgesForTag(tag, graphEdges);

  if (import.meta.env.DEV) {
    console.log("GRAPH EDGES:", edges);
  }

  const upstream = uniqueStrings(
    edges
      .filter((edge) => isSameTag(edge.target, tag))
      .map((edge) => edge.source)
      .concat(fallback?.upstream || [])
  );
  const downstream = uniqueStrings(
    edges
      .filter((edge) => isSameTag(edge.source, tag))
      .map((edge) => edge.target)
      .concat(fallback?.downstream || [])
  );

  return {
    upstream,
    downstream,
    edges,
  };
}

export function getPIDContext(
  tag: string,
  graphEdges: GraphEdge[],
  graphNodes: GraphNode[],
  fallback?: { upstream_tags?: string[]; downstream_tags?: string[] }
) {
  const edges = getEdgesForTag(tag, graphEdges);
  const upstream_tags = uniqueStrings(
    edges
      .filter((edge) => isSameTag(edge.target, tag))
      .map((edge) => edge.source)
      .concat(fallback?.upstream_tags || [])
  );
  const downstream_tags = uniqueStrings(
    edges
      .filter((edge) => isSameTag(edge.source, tag))
      .map((edge) => edge.target)
      .concat(fallback?.downstream_tags || [])
  );
  const nodeByToken = new Map(graphNodes.map((node) => [toComparableToken(node.id), node]));

  const upstreamNodes = upstream_tags.map((item) => nodeByToken.get(toComparableToken(item))).filter((item): item is GraphNode => Boolean(item));
  const downstreamNodes = downstream_tags.map((item) => nodeByToken.get(toComparableToken(item))).filter((item): item is GraphNode => Boolean(item));

  const classifyTags = (nodes: GraphNode[], test: (node: GraphNode) => boolean): string[] => uniqueStrings(nodes.filter(test).map((node) => node.id));

  const flowEdge = edges.find((edge) => edge.process_flow_direction && edge.process_flow_direction.trim().length > 0);

  return {
    upstream_tags,
    downstream_tags,
    upstream_equipment: uniqueStrings(upstreamNodes.map((node) => node.id)),
    downstream_equipment: uniqueStrings(downstreamNodes.map((node) => node.id)),
    valves: classifyTags([...upstreamNodes, ...downstreamNodes], (node) => (node.node_type || "").toLowerCase().includes("valve")),
    pumps: classifyTags([...upstreamNodes, ...downstreamNodes], (node) => (node.node_type || "").toLowerCase().includes("pump")),
    instruments: classifyTags([...upstreamNodes, ...downstreamNodes], (node) => {
      const normalized = (node.node_type || "").toLowerCase();
      return normalized.includes("sensor") || normalized.includes("instrument") || normalized.includes("transmitter");
    }),
    flow_direction: flowEdge?.process_flow_direction || undefined,
  };
}

const buildSafetyContext = (
  tag: string,
  narrativeContext: ReturnType<typeof getNarrativeContext>,
  runtimeDiagnostics: RuntimeEvaluationCycle | null | undefined,
  controlLoops: ControlLoopRecord[]
): SystemContext["safety"] => {
  const alarms = Object.entries(runtimeDiagnostics?.alarms || {})
    .filter(([, active]) => Boolean(active))
    .map(([alarmTag]) => alarmTag);

  const loopTrips = controlLoops
    .filter((loop) => [loop.sensor_tag, loop.actuator_tag, loop.controller_tag || ""].some((loopTag) => toComparableToken(loopTag) === toComparableToken(tag)))
    .map((loop) => loop.loop_tag)
    .filter((loopTag) => loopTag.trim().length > 0);

  return {
    interlocks: narrativeContext.logic_blocks
      .filter((line) => /interlock|if|unless|permit/i.test(line))
      .map((line) => ({ trigger: line, action: "control action" })),
    trips: uniqueStrings(loopTrips),
    permissives: uniqueStrings(narrativeContext.logic_blocks.filter((line) => /permissive|permit/i.test(line))),
    alarm_tags: uniqueStrings(alarms),
  };
};

const buildRuntimeContext = (
  graph: SystemContext["graph"],
  control: SystemContext["control"],
  runtimeValidation: RuntimeValidationSnapshot | null | undefined,
  runtimeTelemetryTags: Record<string, unknown> | undefined,
  fallback?: { dependencies?: string[]; influences?: string[] }
): SystemContext["runtime"] => {
  const telemetryKeys = Object.keys(runtimeTelemetryTags || {});
  const dependencies = uniqueStrings([...graph.upstream, ...control.control_inputs, ...(fallback?.dependencies || [])].filter((item) => item.length > 0));
  const influences = uniqueStrings([...graph.downstream, ...control.control_outputs, ...(fallback?.influences || [])].filter((item) => item.length > 0));

  const inferredMode =
    control.control_mode ||
    (telemetryKeys.some((key) => key.toLowerCase().includes("manual")) ? "manual" : undefined) ||
    (telemetryKeys.some((key) => key.toLowerCase().includes("auto")) ? "auto" : undefined);

  return {
    state: runtimeValidation?.runtime_state,
    mode: inferredMode,
    dependencies,
    influences,
  };
};

export function buildSystemContext(options: BuildSystemContextOptions): SystemContext {
  const {
    tag,
    graphNodes,
    graphEdges,
    narrativeText = "",
    engineeringRows = [],
    controlLoops = [],
    runtimeDiagnostics,
    runtimeValidation,
    runtimeTelemetryTags,
  } = options;

  const isa = parseISATag(tag);
  const controlFromNarrative = getNarrativeContext(tag, narrativeText);

  const node = graphNodes.find((item) => toComparableToken(item.id) === toComparableToken(tag));
  const engineeringRow = engineeringRows.find((item) => toComparableToken(item.tag) === toComparableToken(tag));

  const rowUpstream = engineeringRow?.upstream ?? [];
  const rowDownstream = engineeringRow?.downstream ?? [];
  const graph = getGraphContext(tag, graphEdges, {
    upstream: rowUpstream,
    downstream: rowDownstream,
  });
  const pid = getPIDContext(tag, graphEdges, graphNodes, {
    upstream_tags: rowUpstream,
    downstream_tags: rowDownstream,
  });

  const controlLoopsForTag = controlLoops.filter((loop) => {
    return [loop.sensor_tag, loop.actuator_tag, loop.controller_tag || "", loop.loop_tag].some(
      (candidate) => toComparableToken(candidate) === toComparableToken(tag)
    );
  });

  const control: SystemContext["control"] = {
    role: node?.control_role || controlFromNarrative.role || inferRoleFromTag(tag) || inferRoleFromTag(isa.full_type || ""),
    control_strategy: controlLoopsForTag[0]?.control_strategy || controlFromNarrative.control_strategy,
    control_mode: controlFromNarrative.control_mode,
    setpoints: controlFromNarrative.setpoints,
    control_inputs: uniqueStrings([
      ...controlFromNarrative.control_inputs,
      ...(engineeringRow?.controlled_by ?? []),
      ...(engineeringRow?.signal_inputs ?? []),
    ]),
    control_outputs: uniqueStrings([
      ...controlFromNarrative.control_outputs,
      ...(engineeringRow?.controls ?? []),
      ...(engineeringRow?.signal_outputs ?? []),
    ]),
    loops: uniqueStrings([...controlFromNarrative.loops, ...controlLoopsForTag.map((loop) => loop.loop_tag)]),
    logic_blocks: uniqueStrings(controlFromNarrative.logic_blocks),
  };

  const process: SystemContext["process"] = {
    unit: node?.process_unit || engineeringRow?.system || undefined,
    area: node?.cluster_id || undefined,
    equipment: engineeringRow?.equipment || node?.id || undefined,
    service: engineeringRow?.description || undefined,
  };

  const safety = buildSafetyContext(tag, controlFromNarrative, runtimeDiagnostics, controlLoops);
  const runtime = buildRuntimeContext(graph, control, runtimeValidation, runtimeTelemetryTags, {
    dependencies: rowUpstream,
    influences: rowDownstream,
  });

  const ctx: SystemContext = {
    tag,
    isa,
    process,
    pid,
    control,
    safety,
    graph,
    runtime,
  };

  if (import.meta.env.DEV) {
    console.log("SYSTEM CONTEXT:", ctx);
  }

  return ctx;
}

export function buildBehavior(ctx: SystemContext) {
  return `
${ctx.tag} is a ${ctx.isa.full_type || "device"} acting as a ${ctx.control.role || "device"}.

It receives input from ${ctx.graph.upstream.join(", ") || "no upstream"}.

It affects ${ctx.graph.downstream.join(", ") || "no downstream"}.

Control strategy: ${ctx.control.control_strategy || "not defined"}.

Logic:
${ctx.control.logic_blocks.join("; ") || "none"}

Interlocks:
${ctx.safety?.interlocks?.map((item) => item.trigger + " -> " + item.action).join("; ") || "none"}

Alarms:
${ctx.safety?.alarm_tags?.join(", ") || "none"}
  `.trim();
}

export function buildImpact(ctx: SystemContext): SystemImpact {
  return {
    cause: ctx.graph.upstream,
    effect: ctx.graph.downstream,
    impact: uniqueStrings([...ctx.graph.downstream, ...(ctx.safety?.alarm_tags || [])]),
  };
}
