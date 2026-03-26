import { useMemo } from "react";
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
  onEditStrategy: (loop: ControlLoopRecord) => void;
  onGenerateLogic: (loop: ControlLoopRecord) => void;
  onTraceLoop: (loop: ControlLoopRecord) => void;
  onSimulate: (loop: ControlLoopRecord) => void;
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
  onEditStrategy,
  onGenerateLogic,
  onTraceLoop,
  onSimulate,
  onNavigateToST,
  onNavigateToIO,
}: RightControlLoopsTabProps) {
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
    for (const loop of loops) {
      const sensorToken = toComparableToken(loop.sensor_tag || "");
      const actuatorToken = toComparableToken(loop.actuator_tag || "");
      const setpointToken = toComparableToken(loop.setpoint_tag || "");
      const outputToken = toComparableToken(loop.output_tag || "");

      const sensorRow = rowByTagToken.get(sensorToken);
      const actuatorRow = rowByTagToken.get(actuatorToken);
      const setpointRow = setpointToken ? rowByTagToken.get(setpointToken) : undefined;
      const outputRow = outputToken ? rowByTagToken.get(outputToken) : undefined;

      const current = String(sensorRow?.current_value ?? "—");
      const setpoint = String(setpointRow?.current_value ?? sensorRow?.setpoint ?? "—");
      const output = String(outputRow?.current_value ?? actuatorRow?.current_value ?? "—");
      const state = String(actuatorRow?.state ?? sensorRow?.state ?? "—");
      const status = buildLoopHealth({ current, setpoint, state });

      runtime.set(loop.loop_tag, { current, setpoint, output, state, status });
    }
    return runtime;
  }, [loops, rowByTagToken]);

  const loopMapping = useMemo(() => {
    const mapping = new Map<string, MappingPreview>();
    for (const loop of loops) {
      const sensorToken = toComparableToken(loop.sensor_tag || "");
      const actuatorToken = toComparableToken(loop.actuator_tag || "");
      const sensorCandidates = ioByTagToken.get(sensorToken) ?? [];
      const actuatorCandidates = ioByTagToken.get(actuatorToken) ?? [];

      const sensorInput = sensorCandidates.find((item) => item.io_type === "AI" || item.io_type === "DI") ?? sensorCandidates[0];
      const actuatorOutput = actuatorCandidates.find((item) => item.io_type === "AO" || item.io_type === "DO") ?? actuatorCandidates[0];

      mapping.set(loop.loop_tag, {
        sensor: sensorInput ? `${sensorInput.io_type} ${sensorInput.plc_id}/S${sensorInput.slot}/CH${sensorInput.channel}` : "missing",
        actuator: actuatorOutput ? `${actuatorOutput.io_type} ${actuatorOutput.plc_id}/S${actuatorOutput.slot}/CH${actuatorOutput.channel}` : "missing",
        complete: Boolean(sensorInput && actuatorOutput),
      });
    }
    return mapping;
  }, [ioByTagToken, loops]);

  const loopReplay = useMemo(() => {
    const previews = new Map<string, ReplayPreview>();
    for (const loop of loops) {
      const sensorToken = toComparableToken(loop.sensor_tag || "");
      const actuatorToken = toComparableToken(loop.actuator_tag || "");
      const sensorSamples = replayTrace.filter((item) => toComparableToken(item.tag || "") === sensorToken);
      const actuatorSamples = replayTrace.filter((item) => toComparableToken(item.tag || "") === actuatorToken);
      previews.set(loop.loop_tag, {
        sensorSamples: sensorSamples.length,
        actuatorSamples: actuatorSamples.length,
        latestSensor: sensorSamples.length > 0 ? String(sensorSamples[sensorSamples.length - 1].value) : "—",
        latestActuator: actuatorSamples.length > 0 ? String(actuatorSamples[actuatorSamples.length - 1].value) : "—",
      });
    }
    return previews;
  }, [loops, replayTrace]);

  const selectedLoop = loops.find((item) => item.loop_tag === selectedLoopTag) ?? null;
  const selectedLoopReplay = selectedLoop ? loopReplay.get(selectedLoop.loop_tag) : null;
  const selectedLoopRuntime = selectedLoop ? loopRuntime.get(selectedLoop.loop_tag) : null;
  const selectedLoopMapping = selectedLoop ? loopMapping.get(selectedLoop.loop_tag) : null;

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
      ) : loops.length === 0 ? (
        <div className="monitor-frame">
          <div>No control loops detected yet.</div>
          <button className="command-btn" type="button" onClick={onDetectLoops}>
            Detect Control Loops
          </button>
        </div>
      ) : (
        <div className="plant-table-wrap">
          <table className="plant-table" role="grid">
            <thead>
              <tr>
                <th>Loop ID</th>
                <th>Sensor</th>
                <th>Process</th>
                <th>Actuator</th>
                <th>Controller</th>
                <th>Loop Type</th>
                <th>Strategy</th>
                <th>Setpoint</th>
                <th>Output</th>
                <th>Sensor IO</th>
                <th>Actuator IO</th>
                <th>Mapping</th>
                <th>Current</th>
                <th>Loop State</th>
                <th>Confidence</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loops.map((loop) => {
                const mapping = loopMapping.get(loop.loop_tag) ?? { sensor: "missing", actuator: "missing", complete: false };
                const runtime = loopRuntime.get(loop.loop_tag) ?? {
                  current: "—",
                  setpoint: "—",
                  output: "—",
                  state: "—",
                  status: "inactive" as const,
                };
                return (
                  <tr
                    key={loop.id}
                    className={`${selectedLoopTag === loop.loop_tag ? "active" : ""} ${!mapping.complete ? "bg-amber-50" : ""}`}
                    onClick={() => onSelectLoop(loop)}
                  >
                    <td>{loop.loop_tag}</td>
                    <td>{loop.sensor_tag}</td>
                    <td>{loop.process_unit || ""}</td>
                    <td>{loop.actuator_tag}</td>
                    <td>{loop.controller_tag || ""}</td>
                    <td>{loop.loop_type}</td>
                    <td>{loop.control_strategy}</td>
                    <td>{loop.setpoint_tag || ""}</td>
                    <td>{loop.output_tag || ""}</td>
                    <td>{mapping.sensor}</td>
                    <td>{mapping.actuator}</td>
                    <td>{mapping.complete ? "mapped" : "missing"}</td>
                    <td>{runtime.current} / {runtime.setpoint} / {runtime.output}</td>
                    <td>{runtime.state}</td>
                    <td>
                      <span className="confidence-pill">{Number(loop.confidence || 0).toFixed(2)}</span>
                    </td>
                    <td>{runtime.status}</td>
                    <td>
                      <div className="plant-table-actions" onClick={(event) => event.stopPropagation()}>
                        <button className="command-btn" type="button" onClick={() => onViewLoop(loop)}>View Loop</button>
                        <button className="command-btn" type="button" onClick={() => onEditStrategy(loop)}>Edit Strategy</button>
                        <button className="command-btn" type="button" onClick={() => onGenerateLogic(loop)}>Generate Logic</button>
                        <button className="command-btn" type="button" onClick={() => onTraceLoop(loop)}>Trace Loop</button>
                        <button className="command-btn" type="button" onClick={() => onSimulate(loop)}>Simulate</button>
                        <button className="command-btn" type="button" onClick={() => onNavigateToST?.(loop)}>Open ST</button>
                        <button className="command-btn" type="button" onClick={() => onNavigateToIO?.(loop)}>Open IO</button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {selectedLoop ? (
        <div className="monitor-frame">
          <div className="panel-subtitle">Loop Integration</div>
          <div className="text-[11px] text-slate-700">ST mapping: PV={selectedLoop.sensor_tag}, SP={selectedLoop.setpoint_tag || `${selectedLoop.loop_tag}_SP`}, OUT={selectedLoop.output_tag || selectedLoop.actuator_tag}</div>
          <div className="text-[11px] text-slate-700">IO link: sensor {selectedLoopMapping?.sensor || "missing"} → actuator {selectedLoopMapping?.actuator || "missing"}</div>
          <div className="text-[11px] text-slate-700">Runtime: current {selectedLoopRuntime?.current || "—"}, setpoint {selectedLoopRuntime?.setpoint || "—"}, output {selectedLoopRuntime?.output || "—"}, state {selectedLoopRuntime?.state || "—"}</div>
          <div className="text-[11px] text-slate-700">Replay: sensor samples {selectedLoopReplay?.sensorSamples || 0} (latest {selectedLoopReplay?.latestSensor || "—"}), actuator samples {selectedLoopReplay?.actuatorSamples || 0} (latest {selectedLoopReplay?.latestActuator || "—"})</div>
        </div>
      ) : null}
    </>
  );
}
