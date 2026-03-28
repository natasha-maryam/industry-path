import SimulationTimeline from "../SimulationTimeline";
import type { SimulationTraceIssue, SimulationTracePoint } from "../../services/api";

type RightReplayTabProps = {
  replayPoint: number;
  selectedTag?: string;
  replayTrace?: SimulationTracePoint[];
  replayIssues?: SimulationTraceIssue[];
  onSelectedTagChange?: (tag: string) => void;
  onReplayPointChange?: (point: number) => void;
};

export default function RightReplayTab({
  replayPoint,
  selectedTag = "",
  replayTrace = [],
  replayIssues = [],
  onSelectedTagChange,
  onReplayPointChange,
}: RightReplayTabProps) {
  const effectiveTag = selectedTag || replayTrace[0]?.tag || "";
  const sampleCount = effectiveTag ? replayTrace.filter((item) => item.tag === effectiveTag).length : 0;
  const hasTrace = replayTrace.length > 0;
  const replayTimeMs = effectiveTag
    ? replayTrace.filter((item) => item.tag === effectiveTag)[Math.min(Math.max(replayPoint, 0), Math.max(sampleCount - 1, 0))]?.time ?? null
    : null;

  return (
    <>
      <SimulationTimeline
        trace={replayTrace}
        issues={replayIssues}
        selectedTag={effectiveTag}
        onSelectedTagChange={onSelectedTagChange}
        replayPoint={replayPoint}
        onReplayPointChange={onReplayPointChange}
      />

      <dl className="kv kv-technical">
        <dt>Trace</dt>
        <dd className="value-mono">{hasTrace ? "1" : "0"}</dd>
        <dt>Samples</dt>
        <dd className="value-mono">{sampleCount}</dd>
        <dt>Detected Issues</dt>
        <dd className="value-mono">{replayIssues.length}</dd>
        <dt>Replay Time</dt>
        <dd className="value-mono">{replayTimeMs === null ? "-" : `${replayTimeMs} ms`}</dd>
      </dl>
    </>
  );
}
