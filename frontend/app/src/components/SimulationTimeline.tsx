import { useMemo } from "react";
import { Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SimulationTraceIssue, SimulationTracePoint } from "../services/api";

type SimulationTimelineProps = {
  trace: SimulationTracePoint[];
  issues?: SimulationTraceIssue[];
  selectedTag?: string;
  onSelectedTagChange?: (tag: string) => void;
  replayPoint: number;
  onReplayPointChange?: (point: number) => void;
};

const toNumeric = (value: SimulationTracePoint["value"]): number => {
  if (typeof value === "number") {
    return value;
  }
  const parsed = Number(value);
  if (Number.isFinite(parsed)) {
    return parsed;
  }
  const normalized = String(value).toLowerCase();
  if (normalized === "true") {
    return 1;
  }
  if (normalized === "false") {
    return 0;
  }
  return 0;
};

export default function SimulationTimeline({
  trace,
  issues = [],
  selectedTag = "",
  onSelectedTagChange,
  replayPoint,
  onReplayPointChange,
}: SimulationTimelineProps) {

  const tags = useMemo<string[]>(() => {
    const unique = new Set<string>();
    for (const item of trace) {
      if (item.tag) {
        unique.add(item.tag);
      }
    }
    return [...unique].sort((left, right) => left.localeCompare(right));
  }, [trace]);

  const activeTag = selectedTag || tags[0] || "";

  const chartData = useMemo<Array<{ time: number; value: number }>>(() => {
    if (!activeTag) {
      return [];
    }
    return trace
      .filter((item) => item.tag === activeTag)
      .map((item) => ({
        time: item.time,
        value: toNumeric(item.value),
      }));
  }, [activeTag, trace]);

  const maxIndex = chartData.length > 0 ? chartData.length - 1 : 0;
  const clampedReplayIndex = Math.min(Math.max(replayPoint, 0), maxIndex);
  const activeSample = chartData[clampedReplayIndex] ?? null;
  const activeIssues = issues.filter((issue) => issue.tag === activeTag);

  return (
    <div className="monitor-frame">
      <div className="io-summary-header">
        <h4>Simulation Timeline</h4>
        <span>{activeTag || "No signal selected"}</span>
      </div>

      {trace.length === 0 ? (
        <div className="runtime-validation-empty">No trace samples available yet. Run Evaluation Cycle to capture timeline data.</div>
      ) : null}

      {tags.length > 0 ? (
        <select
          className="modal-input"
          value={activeTag}
          onChange={(event) => {
            onSelectedTagChange?.(event.target.value);
            onReplayPointChange?.(0);
          }}
        >
          {tags.map((tag) => (
            <option key={tag} value={tag}>
              {tag}
            </option>
          ))}
        </select>
      ) : null}

      <div style={{ width: "100%", height: 180 }}>
        <ResponsiveContainer>
          <LineChart data={chartData}>
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="value" stroke="var(--primary)" strokeWidth={2} dot={false} isAnimationActive={false} />
            {activeSample ? <ReferenceLine x={activeSample.time} stroke="var(--primary-strong)" /> : null}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <input
        type="range"
        min={0}
        max={Math.max(maxIndex, 0)}
        value={clampedReplayIndex}
        onChange={(event) => onReplayPointChange?.(Number(event.target.value))}
      />

      <div className="kv kv-technical">
        <div>time: {activeSample ? `${activeSample.time} ms` : "-"}</div>
        <div>value: {activeSample ? String(activeSample.value) : "-"}</div>
        <div>issues: {activeIssues.length}</div>
      </div>

      {activeIssues.length > 0 ? (
        <ul className="trace-chain">
          {activeIssues.map((issue, index) => (
            <li key={`${issue.tag}-${issue.issue}-${index}`}>{`${issue.tag}: ${issue.issue.replace("_", " ")}`}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
