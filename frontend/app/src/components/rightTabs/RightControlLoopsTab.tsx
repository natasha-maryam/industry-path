import { ChevronDown } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import type { ControlLoopRecord, EngineeringTableResponseRow, IOMappingTableRow, SimulationTracePoint } from "../../services/api";

type RightControlLoopsTabProps = {
  loops: ControlLoopRecord[];
  ioMappingRows?: IOMappingTableRow[];
  engineeringRows?: EngineeringTableResponseRow[];
  replayTrace?: SimulationTracePoint[];
  loading?: boolean;
  error?: string | null;
  selectedLoopTag?: string | null;
  onDetectLoops?: () => void;
  onSelectLoop: (loop: ControlLoopRecord) => void;
  onViewLoop: (loop: ControlLoopRecord) => void;
  onGenerateLogic: (loop: ControlLoopRecord) => void;
  onTraceLoop: (loop: ControlLoopRecord) => void;
  onNavigateToST?: (loop: ControlLoopRecord) => void;
  onNavigateToIO?: (loop: ControlLoopRecord) => void;
};

const toComparableToken = (value: string): string => value.toUpperCase().replace(/[^A-Z0-9]/g, "");

const toNumberOrNull = (value: unknown): number | null => {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string") {
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
};

type MappingPreview = {
  sensor: string;
  actuator: string;
  complete: boolean;
};

type ReplayPreview = {
  sensorSamples: number;
  actuatorSamples: number;
  latestSensor: string;
  latestActuator: string;
};

type NormalizedLoopRow = {
  source: ControlLoopRecord;
  loopId: string;
  sensor: string;
  actuator: string;
  process: string;
  controller: string | null;
  chain: string[];
  confidence: number;
  tuningConfidence: number;
  tuning: Record<string, unknown>;
};

const LOW_CONFIDENCE_THRESHOLD = 0.84;

const normalizeLoop = (loop: ControlLoopRecord): NormalizedLoopRow | null => {
  const loopId = loop.loop_id || loop.loop_tag || loop.id;
  const sensor = loop.sensor || loop.sensor_tag || "";
  const actuator = loop.actuator || loop.actuator_tag || "";
  const process = loop.process || loop.process_unit || "";
  const controller = loop.controller ?? loop.controller_tag ?? null;
  const chain = (loop.chain && loop.chain.length > 0 ? loop.chain : [sensor, controller || "PID", actuator, process]).filter((item) => Boolean(item && item.trim().length > 0));
  if (!loopId || !sensor || !actuator || !process || chain.length < 3) {
    return null;
  }
  return {
    source: loop,
    loopId,
    sensor,
    actuator,
    process,
    controller,
    chain,
    confidence: Number(loop.confidence || 0),
    tuningConfidence: Number(loop.tuning_confidence || 0),
    tuning: (loop.tuning as Record<string, unknown> | undefined) ?? {},
  };
};

const buildLoopHealth = (values: { current: string; setpoint: string; state: string }): "stable" | "unstable" | "inactive" => {
  const state = values.state.toLowerCase();
  if (state.includes("inactive") || state.includes("off") || state.includes("stop") || state.includes("disabled")) {
    return "inactive";
  }

  const currentNumeric = toNumberOrNull(values.current);
  const setpointNumeric = toNumberOrNull(values.setpoint);
  if (currentNumeric !== null && setpointNumeric !== null) {
    const tolerance = Math.max(Math.abs(setpointNumeric) * 0.05, 1);
    return Math.abs(currentNumeric - setpointNumeric) > tolerance ? "unstable" : "stable";
  }

  return "stable";
};

export default function RightControlLoopsTab({
  loops,
  ioMappingRows = [],
  engineeringRows = [],
  replayTrace = [],
  loading = false,
  error = null,
  selectedLoopTag = null,
  onDetectLoops,
  onSelectLoop,
  onViewLoop,
  onGenerateLogic,
  onTraceLoop,
  onNavigateToST,
  onNavigateToIO,
}: RightControlLoopsTabProps) {
  const [openMenuLoopId, setOpenMenuLoopId] = useState<string | null>(null);
  const [showLowConfidence, setShowLowConfidence] = useState<boolean>(false);
  const [expandedLoopIds, setExpandedLoopIds] = useState<Record<string, boolean>>({});
  const openMenuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!openMenuLoopId) {
      return undefined;
    }

    const handlePointerDown = (event: MouseEvent): void => {
      if (openMenuRef.current && event.target instanceof Node && !openMenuRef.current.contains(event.target)) {
        setOpenMenuLoopId(null);
      }
    };

    const handleEscape = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        setOpenMenuLoopId(null);
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [openMenuLoopId]);

  const rowByTagToken = useMemo(() => {
    const map = new Map<string, EngineeringTableResponseRow>();
    for (const row of engineeringRows) {
      const token = toComparableToken(row.tag || "");
      if (token) {
        map.set(token, row);
      }
    }
    return map;
  }, [engineeringRows]);

  const normalizedLoops = useMemo(() => loops.map((loop) => normalizeLoop(loop)).filter((loop): loop is NormalizedLoopRow => Boolean(loop)), [loops]);

  const visibleLoops = useMemo(
    () => normalizedLoops.filter((loop) => showLowConfidence || loop.confidence >= LOW_CONFIDENCE_THRESHOLD),
    [normalizedLoops, showLowConfidence]
  );

  const selectedLoop = useMemo(() => {
    const selected = visibleLoops.find((item) => item.loopId === selectedLoopTag);
    if (selected) {
      return selected;
    }
    return visibleLoops[0] ?? null;
  }, [selectedLoopTag, visibleLoops]);

  const toggleLoopExpanded = (loopId: string): void => {
    setExpandedLoopIds((current) => ({ ...current, [loopId]: !current[loopId] }));
  };

  const ioByTagToken = useMemo(() => {
    const map = new Map<string, IOMappingTableRow[]>();
    for (const row of ioMappingRows) {
      const token = toComparableToken(row.tag || "");
      if (!token) {
        continue;
      }
      const existing = map.get(token) ?? [];
      existing.push(row);
      map.set(token, existing);
    }
    return map;
  }, [ioMappingRows]);

  const loopRuntime = useMemo(() => {
    const runtime = new Map<string, { current: string; setpoint: string; output: string; state: string; status: "stable" | "unstable" | "inactive" }>();
    for (const loop of normalizedLoops) {
      const source = loop.source;
      const sensorToken = toComparableToken(loop.sensor || "");
      const actuatorToken = toComparableToken(loop.actuator || "");
      const setpointToken = toComparableToken(source.setpoint_tag || "");
      const outputToken = toComparableToken(source.output_tag || "");

      const sensorRow = rowByTagToken.get(sensorToken);
      const actuatorRow = rowByTagToken.get(actuatorToken);
      const setpointRow = setpointToken ? rowByTagToken.get(setpointToken) : undefined;
      const outputRow = outputToken ? rowByTagToken.get(outputToken) : undefined;

      const current = String(sensorRow?.current_value ?? "—");
      const setpoint = String(setpointRow?.current_value ?? sensorRow?.setpoint ?? "—");
      const output = String(outputRow?.current_value ?? actuatorRow?.current_value ?? "—");
      const state = String(actuatorRow?.state ?? sensorRow?.state ?? "—");
      const status = buildLoopHealth({ current, setpoint, state });

      runtime.set(loop.loopId, { current, setpoint, output, state, status });
    }
    return runtime;
  }, [normalizedLoops, rowByTagToken]);

  const loopMapping = useMemo(() => {
    const mapping = new Map<string, MappingPreview>();
    for (const loop of normalizedLoops) {
      const sensorToken = toComparableToken(loop.sensor || "");
      const actuatorToken = toComparableToken(loop.actuator || "");
      const sensorCandidates = ioByTagToken.get(sensorToken) ?? [];
      const actuatorCandidates = ioByTagToken.get(actuatorToken) ?? [];

      const sensorInput = sensorCandidates.find((item) => item.io_type === "AI" || item.io_type === "DI") ?? sensorCandidates[0];
      const actuatorOutput = actuatorCandidates.find((item) => item.io_type === "AO" || item.io_type === "DO") ?? actuatorCandidates[0];

      mapping.set(loop.loopId, {
        sensor: sensorInput ? `${sensorInput.io_type} ${sensorInput.plc_id}/S${sensorInput.slot}/CH${sensorInput.channel}` : "missing",
        actuator: actuatorOutput ? `${actuatorOutput.io_type} ${actuatorOutput.plc_id}/S${actuatorOutput.slot}/CH${actuatorOutput.channel}` : "missing",
        complete: Boolean(sensorInput && actuatorOutput),
      });
    }
    return mapping;
  }, [ioByTagToken, normalizedLoops]);

  const loopReplay = useMemo(() => {
    const previews = new Map<string, ReplayPreview>();
    for (const loop of normalizedLoops) {
      const sensorToken = toComparableToken(loop.sensor || "");
      const actuatorToken = toComparableToken(loop.actuator || "");
      const sensorSamples = replayTrace.filter((item) => toComparableToken(item.tag || "") === sensorToken);
      const actuatorSamples = replayTrace.filter((item) => toComparableToken(item.tag || "") === actuatorToken);
      previews.set(loop.loopId, {
        sensorSamples: sensorSamples.length,
        actuatorSamples: actuatorSamples.length,
        latestSensor: sensorSamples.length > 0 ? String(sensorSamples[sensorSamples.length - 1].value) : "—",
        latestActuator: actuatorSamples.length > 0 ? String(actuatorSamples[actuatorSamples.length - 1].value) : "—",
      });
    }
    return previews;
  }, [normalizedLoops, replayTrace]);

  const selectedLoopReplay = selectedLoop ? loopReplay.get(selectedLoop.loopId) : null;
  const selectedLoopRuntime = selectedLoop ? loopRuntime.get(selectedLoop.loopId) : null;
  const selectedLoopMapping = selectedLoop ? loopMapping.get(selectedLoop.loopId) : null;

  return (
    <>
      <div className="panel-subtitle">Detected Control Loops</div>
      {loading ? (
        <div className="monitor-frame">Loading control loops...</div>
      ) : error ? (
        <div className="monitor-frame">
          <div>{error}</div>
          <button className="command-btn" type="button" onClick={onDetectLoops}>
            Detect Control Loops
          </button>
        </div>
      ) : normalizedLoops.length === 0 ? (
        <div className="monitor-frame">
          <div>No validated control loops found yet</div>
          <button className="command-btn" type="button" onClick={onDetectLoops}>
            Detect Control Loops
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between rounded border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] text-slate-600">
            <div>
              Showing {visibleLoops.length} of {normalizedLoops.length} validated loop candidates
            </div>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={showLowConfidence} onChange={(event) => setShowLowConfidence(event.target.checked)} />
              Show low-confidence loops
            </label>
          </div>

          {visibleLoops.length === 0 ? (
            <div className="monitor-frame">
              <div>No validated control loops found yet</div>
              <div className="text-[11px] text-slate-500">All detected loops are currently below the default confidence threshold.</div>
            </div>
          ) : (
            <div className="space-y-2">
              {visibleLoops.map((loop) => {
                const source = loop.source;
                const mapping = loopMapping.get(loop.loopId) ?? { sensor: "missing", actuator: "missing", complete: false };
                const runtime = loopRuntime.get(loop.loopId) ?? {
                  current: "—",
                  setpoint: "—",
                  output: "—",
                  state: "—",
                  status: "inactive" as const,
                };
                const loopActions = [
                  { label: "View Loop", onClick: () => onViewLoop(source) },
                  { label: "Generate Logic", onClick: () => onGenerateLogic(source) },
                  { label: "Trace Loop", onClick: () => onTraceLoop(source) },
                  ...(onNavigateToST ? [{ label: "Open ST", onClick: () => onNavigateToST(source) }] : []),
                  ...(onNavigateToIO ? [{ label: "Open IO", onClick: () => onNavigateToIO(source) }] : []),
                ];
                const isMenuOpen = openMenuLoopId === loop.loopId;
                const isExpanded = expandedLoopIds[loop.loopId] ?? false;
                const hasTuning = loop.tuningConfidence > 0 || Object.keys(loop.tuning).length > 0;
                return (
                  <div
                    key={loop.loopId}
                    className={`rounded border px-3 py-2 ${selectedLoopTag === loop.loopId ? "border-red-300 bg-red-50" : !mapping.complete ? "border-amber-200 bg-amber-50" : "border-slate-200 bg-white"}`}
                    onClick={() => onSelectLoop(source)}
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-[11px] font-semibold text-slate-800">{loop.loopId}</span>
                          <span className="rounded-full border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-[9px] text-slate-600">Conf {loop.confidence.toFixed(2)}</span>
                          {hasTuning ? <span className="rounded-full border border-amber-200 bg-amber-50 px-1.5 py-0.5 text-[9px] font-medium text-amber-800">Tuning {loop.tuningConfidence.toFixed(2)}</span> : null}
                        </div>
                        <div className="mt-1 flex flex-wrap items-center gap-1 text-[11px] text-slate-700">
                          <span className="font-medium text-slate-900">{loop.sensor}</span>
                          <span className="text-slate-400">→</span>
                          <span className="rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-900">{loop.controller || "PID"}</span>
                          <span className="text-slate-400">→</span>
                          <span className="font-medium text-slate-900">{loop.actuator}</span>
                          <span className="text-slate-400">→</span>
                          <span className="font-medium text-slate-900">{loop.process}</span>
                        </div>
                        <div className="mt-1 flex flex-wrap gap-3 text-[10px] text-slate-500">
                          <span>IO {mapping.sensor} → {mapping.actuator}</span>
                          <span>Runtime {runtime.current} / {runtime.setpoint} / {runtime.output}</span>
                          <span className="capitalize">State {runtime.status}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2" onClick={(event) => event.stopPropagation()}>
                        {hasTuning ? (
                          <button className="command-btn" type="button" onClick={() => toggleLoopExpanded(loop.loopId)}>
                            {isExpanded ? "Hide tuning" : "Show tuning"}
                          </button>
                        ) : null}
                        <div className="table-row-menu" ref={isMenuOpen ? openMenuRef : null}>
                          <button
                            className={`command-btn table-row-menu-trigger ${isMenuOpen ? "active" : ""}`}
                            type="button"
                            aria-haspopup="menu"
                            aria-expanded={isMenuOpen}
                            onClick={(event) => {
                              event.stopPropagation();
                              setOpenMenuLoopId((current) => (current === loop.loopId ? null : loop.loopId));
                            }}
                          >
                            Actions
                            <ChevronDown size={11} />
                          </button>
                          {isMenuOpen ? (
                            <div className="table-row-menu-popover" role="menu">
                              {loopActions.map((action) => (
                                <button
                                  key={action.label}
                                  className="command-btn table-row-menu-item"
                                  type="button"
                                  role="menuitem"
                                  onClick={(event) => {
                                    event.stopPropagation();
                                    setOpenMenuLoopId(null);
                                    action.onClick();
                                  }}
                                >
                                  {action.label}
                                </button>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      </div>
                    </div>

                    {isExpanded ? (
                      <div className="mt-2 rounded border border-slate-200 bg-slate-50 p-2 text-[10px] text-slate-700">
                        <div className="grid gap-1 md:grid-cols-2">
                          <div>Mode: {String(loop.tuning.mode ?? "—")}</div>
                          <div>Source refs: {Array.isArray(loop.tuning.source_references) ? loop.tuning.source_references.join(", ") || "—" : "—"}</div>
                          <div>Kp: {String(loop.tuning.kp ?? "—")}</div>
                          <div>Ki: {String(loop.tuning.ki ?? "—")}</div>
                          <div>Kd: {String(loop.tuning.kd ?? "—")}</div>
                          <div>Reset: {String(loop.tuning.reset_time ?? "—")}</div>
                          <div>PB: {String(loop.tuning.proportional_band ?? "—")}</div>
                          <div>Behavior: {Array.isArray(loop.tuning.behavior_terms) ? loop.tuning.behavior_terms.join(", ") || "—" : "—"}</div>
                        </div>
                      </div>
                    ) : null}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {selectedLoop ? (
        <div className="monitor-frame">
          <div className="panel-subtitle">Loop Integration</div>
          <div className="text-[11px] text-slate-700">ST mapping: PV={selectedLoop.sensor}, SP={selectedLoop.source.setpoint_tag || `${selectedLoop.loopId}_SP`}, OUT={selectedLoop.source.output_tag || selectedLoop.actuator}</div>
          <div className="text-[11px] text-slate-700">Control path: {selectedLoop.chain.join(" -> ")}</div>
          <div className="text-[11px] text-slate-700">IO link: sensor {selectedLoopMapping?.sensor || "missing"} → actuator {selectedLoopMapping?.actuator || "missing"}</div>
          <div className="text-[11px] text-slate-700">Runtime: current {selectedLoopRuntime?.current || "—"}, setpoint {selectedLoopRuntime?.setpoint || "—"}, output {selectedLoopRuntime?.output || "—"}, state {selectedLoopRuntime?.state || "—"}</div>
          <div className="text-[11px] text-slate-700">Replay: sensor samples {selectedLoopReplay?.sensorSamples || 0} (latest {selectedLoopReplay?.latestSensor || "—"}), actuator samples {selectedLoopReplay?.actuatorSamples || 0} (latest {selectedLoopReplay?.latestActuator || "—"})</div>
        </div>
      ) : null}
    </>
  );
}
