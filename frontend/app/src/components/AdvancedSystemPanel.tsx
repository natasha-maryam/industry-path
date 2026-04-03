import { useCallback, useMemo, useState } from "react";
import {
  getAdvancedBottlenecks,
  getAdvancedLoops,
  getAdvancedTrace,
  runAdvancedAutoMap,
  type SystemBottleneck,
} from "../services/api";

type AdvancedSystemPanelProps = {
  projectId?: string;
  onSelectTag?: (tag: string) => void;
  onTracePath?: (path: string[]) => void;
};

const toLines = (value: string): string[] => {
  return value
    .split(/[\n,]+/)
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
};

export default function AdvancedSystemPanel({ projectId, onSelectTag, onTracePath }: AdvancedSystemPanelProps) {
  const [externalTagsInput, setExternalTagsInput] = useState<string>("");
  const [traceTagInput, setTraceTagInput] = useState<string>("");

  const [bottlenecks, setBottlenecks] = useState<SystemBottleneck[]>([]);
  const [loopsCount, setLoopsCount] = useState<number | null>(null);
  const [statusText, setStatusText] = useState<string>("Advanced system analysis idle.");
  const [errorText, setErrorText] = useState<string | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [lastPayload, setLastPayload] = useState<Record<string, unknown> | null>(null);

  const withBusy = useCallback(async (action: string, task: () => Promise<void>): Promise<void> => {
    setBusyAction(action);
    setErrorText(null);
    try {
      await task();
    } catch (err) {
      setErrorText(err instanceof Error ? err.message : `${action} failed.`);
    } finally {
      setBusyAction(null);
    }
  }, []);

  const handleAutoMap = useCallback(() => {
    void withBusy("Auto-map", async () => {
      const tags = toLines(externalTagsInput);
      if (tags.length === 0) {
        throw new Error("At least one external tag is required.");
      }
      const result = await runAdvancedAutoMap({ external_tags: tags });
      const count = Number(result.count ?? 0);
      setStatusText(`Auto-map completed: ${count} mapped.`);
      setLastPayload({ action: "auto_map", result });
    });
  }, [externalTagsInput, withBusy]);

  const handleTrace = useCallback(() => {
    void withBusy("Trace", async () => {
      const tag = traceTagInput.trim();
      if (!tag) {
        setErrorText("Trace tag is required.");
        return;
      }
      const trace = await getAdvancedTrace(tag, projectId, 6);
      const safePath = Array.isArray(trace.path) ? trace.path : [];
      onTracePath?.(safePath);
      onSelectTag?.(tag);
      setStatusText(`Trace computed for ${tag} (${safePath.length} nodes).`);
      setLastPayload({ action: "trace", trace: { ...trace, path: safePath } });
    });
  }, [onSelectTag, onTracePath, projectId, traceTagInput, withBusy]);

  const handleBottlenecks = useCallback(() => {
    void withBusy("Bottlenecks", async () => {
      const result = await getAdvancedBottlenecks(projectId, 10);
      const safeBottlenecks = Array.isArray(result.bottlenecks) ? result.bottlenecks : [];
      setBottlenecks(safeBottlenecks);
      if (safeBottlenecks[0]?.tag) {
        onSelectTag?.(safeBottlenecks[0].tag);
      }
      setStatusText(`Bottlenecks computed (${result.count}).`);
      setLastPayload({ action: "bottlenecks", count: result.count, top: safeBottlenecks.slice(0, 3) });
    });
  }, [onSelectTag, projectId, withBusy]);

  const handleLoops = useCallback(() => {
    void withBusy("Loops", async () => {
      const result = await getAdvancedLoops(projectId, 20);
      setLoopsCount(result.count);
      setStatusText(`Loop analysis completed (${result.count}). Uses analytical graph loops only.`);
      setLastPayload({ action: "loops", result });
    });
  }, [projectId, withBusy]);

  const bottleneckPreview = useMemo(() => bottlenecks.slice(0, 5), [bottlenecks]);

  return (
    <section className="mb-2 rounded border border-slate-300 bg-white p-2">
      <div className="mb-2 flex items-center justify-between gap-2">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-700">Advanced System Layer</h4>
        <span className="text-[11px] text-slate-500">{busyAction ? `${busyAction}...` : statusText}</span>
      </div>

      <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-2">
        <div className="space-y-1 rounded border border-slate-200 bg-slate-50 p-2">
          <p className="text-[11px] font-semibold text-slate-700">Auto-map External Tags</p>
          <textarea
            value={externalTagsInput}
            onChange={(event) => setExternalTagsInput(event.target.value)}
            placeholder="FT-101, LT-205, PUMP_A_RUN"
            className="h-20 w-full rounded border border-slate-300 bg-white p-2 text-[11px]"
          />
          <button type="button" className="command-btn" onClick={handleAutoMap}>
            {busyAction === "Auto-map" ? "Running..." : "Run Auto-map"}
          </button>
        </div>

        <div className="space-y-1 rounded border border-slate-200 bg-slate-50 p-2">
          <p className="text-[11px] font-semibold text-slate-700">Relational Analysis</p>
          <input
            value={traceTagInput}
            onChange={(event) => setTraceTagInput(event.target.value)}
            placeholder="Tag for trace"
            className="w-full rounded border border-slate-300 bg-white px-2 py-1 text-[11px]"
          />
          <div className="flex flex-wrap gap-2">
            <button type="button" className="command-btn" onClick={handleTrace}>Trace</button>
            <button type="button" className="command-btn" onClick={handleBottlenecks}>Bottlenecks</button>
            <button type="button" className="command-btn" onClick={handleLoops}>Loops (preview)</button>
          </div>
          <p className="text-[11px] text-slate-600">Loops: {loopsCount ?? "not run"}</p>
        </div>
      </div>

      {errorText ? <p className="mt-2 text-xs text-red-700">{errorText}</p> : null}

      {lastPayload ? (
        <div className="mt-2 rounded border border-slate-200 bg-slate-50 p-2">
          <p className="text-[11px] font-semibold text-slate-700">Latest response</p>
          <pre className="mt-1 max-h-28 overflow-auto text-[10px] text-slate-700">{JSON.stringify(lastPayload, null, 2)}</pre>
        </div>
      ) : null}

      {bottleneckPreview.length > 0 ? (
        <div className="mt-2 rounded border border-slate-200 bg-slate-50 p-2 text-[11px] text-slate-700">
          <p className="mb-1 font-semibold">Top bottlenecks</p>
          <div className="flex flex-wrap gap-1">
            {bottleneckPreview.map((item) => (
              <button
                key={item.tag}
                type="button"
                className="rounded border border-slate-300 bg-white px-2 py-0.5 hover:bg-slate-100"
                onClick={() => onSelectTag?.(item.tag)}
              >
                {item.tag} ({item.score})
              </button>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
