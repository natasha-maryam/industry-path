import { useEffect, useMemo, useRef, useState } from "react";
import { getDeterministicBehaviorRows, getDeterministicWhyTrace, type DeterministicBehaviorRow, type DeterministicWhyTraceResponse } from "../../services/api";

type RightWhyTracePanelProps = {
  tag: string;
  onClose?: () => void;
  onSelectTag?: (tag: string) => void;
};

type EnrichedTraceStep = {
  tag: string;
  depth: number;
  direction: string;
  type: string | null;
  subtype: string | null;
  value: string | null;
  state: string | null;
  setpoint: string | null;
  mode: string | null;
  behavior_summary: string;
};

const toText = (value: unknown): string => {
  if (value === null || value === undefined) {
    return "—";
  }
  const text = String(value).trim();
  return text.length > 0 ? text : "—";
};

export default function RightWhyTracePanel({ tag, onClose, onSelectTag }: RightWhyTracePanelProps) {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [payload, setPayload] = useState<DeterministicWhyTraceResponse | null>(null);
  const [rowsByTag, setRowsByTag] = useState<Record<string, DeterministicBehaviorRow>>({});
  const requestRef = useRef<number>(0);

  useEffect(() => {
    requestRef.current += 1;
    const requestId = requestRef.current;

    const load = async (): Promise<void> => {
      setLoading(true);
      setError(null);
      try {
        const whyPayload = await getDeterministicWhyTrace(tag, 4);
        if (requestRef.current !== requestId) {
          return;
        }
        setPayload(whyPayload);

        const stepTags = Array.from(new Set(whyPayload.steps.map((step) => step.tag).filter((value) => value && value.trim().length > 0)));
        if (stepTags.length === 0) {
          setRowsByTag({});
          return;
        }

        const rowsPayload = await getDeterministicBehaviorRows(stepTags);
        if (requestRef.current !== requestId) {
          return;
        }

        const nextByTag: Record<string, DeterministicBehaviorRow> = {};
        for (const row of rowsPayload.rows) {
          nextByTag[row.tag] = row;
        }
        setRowsByTag(nextByTag);
      } catch {
        if (requestRef.current !== requestId) {
          return;
        }
        setPayload(null);
        setRowsByTag({});
        setError(`Why trace unavailable for ${tag}.`);
      } finally {
        if (requestRef.current === requestId) {
          setLoading(false);
        }
      }
    };

    void load();
  }, [tag]);

  const steps = useMemo<EnrichedTraceStep[]>(() => {
    if (!payload) {
      return [];
    }

    return payload.steps.map((step) => {
      const row = rowsByTag[step.tag];
      const runtime = step.runtime_state ?? {};
      return {
        tag: step.tag,
        depth: step.depth,
        direction: step.direction,
        type: row?.type ?? null,
        subtype: row?.subtype ?? null,
        value: (runtime.current_value as string | null | undefined) ?? row?.current_value ?? null,
        state: (runtime.state as string | null | undefined) ?? row?.state ?? null,
        setpoint: (runtime.setpoint as string | null | undefined) ?? row?.setpoint ?? null,
        mode: (runtime.mode as string | null | undefined) ?? row?.mode ?? null,
        behavior_summary: step.behavior_summary,
      };
    });
  }, [payload, rowsByTag]);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-2">
        <div>
          <div className="panel-subtitle">Why Trace</div>
          <p className="text-[11px] text-slate-500 break-all">{tag}</p>
        </div>
        {onClose ? (
          <button type="button" className="command-btn" onClick={onClose}>
            Close Why
          </button>
        ) : null}
      </div>

      {loading ? <div className="monitor-frame p-3 text-[12px] leading-relaxed">Loading why trace...</div> : null}
      {error ? <div className="monitor-frame p-3 text-[12px] leading-relaxed text-red-700">{error}</div> : null}

      {!loading && !error && payload ? (
        <>
          <div className="monitor-frame space-y-1 p-3">
            <div className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">Summary</div>
            <p className="max-w-full whitespace-pre-wrap break-words text-[12px] leading-relaxed text-slate-700">{toText(payload.behavior_summary)}</p>
          </div>

          {!payload.available ? (
            <div className="monitor-frame p-3 text-[12px] leading-relaxed text-slate-600">No deterministic why-trace exists for this tag in the current snapshot.</div>
          ) : null}

          {steps.length === 0 ? (
            <div className="monitor-frame p-3 text-[12px] leading-relaxed text-slate-500">No trace steps available for this tag.</div>
          ) : (
            <div className="space-y-3">
              {steps.map((step, index) => (
                <button
                  key={`${step.tag}-${step.direction}-${step.depth}-${index}`}
                  type="button"
                  className="monitor-frame w-full space-y-2 p-3 text-left hover:bg-slate-50"
                  onClick={() => onSelectTag?.(step.tag)}
                >
                  <div className="flex items-start justify-between gap-3">
                    <span className="max-w-[65%] break-all text-xs font-semibold text-slate-800">{step.tag}</span>
                    <span className="shrink-0 text-[10px] uppercase tracking-wide text-slate-500">
                      d{step.depth} · {step.direction}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 gap-y-2 text-[11px] leading-relaxed text-slate-700 sm:grid-cols-2 sm:gap-x-4">
                    <p className="break-words"><span className="mr-1 text-slate-500">Type:</span><span className="font-medium text-slate-800">{toText(step.type)}</span></p>
                    <p className="break-words"><span className="mr-1 text-slate-500">Subtype:</span><span className="font-medium text-slate-800">{toText(step.subtype)}</span></p>
                    <p className="break-words"><span className="mr-1 text-slate-500">Value:</span><span className="font-medium text-slate-800">{toText(step.value)}</span></p>
                    <p className="break-words"><span className="mr-1 text-slate-500">State:</span><span className="font-medium text-slate-800">{toText(step.state)}</span></p>
                    <p className="break-words"><span className="mr-1 text-slate-500">Setpoint:</span><span className="font-medium text-slate-800">{toText(step.setpoint)}</span></p>
                    <p className="break-words"><span className="mr-1 text-slate-500">Mode:</span><span className="font-medium text-slate-800">{toText(step.mode)}</span></p>
                  </div>

                  <p className="whitespace-pre-wrap break-words text-[11px] leading-relaxed text-slate-700">{toText(step.behavior_summary)}</p>
                </button>
              ))}
            </div>
          )}
        </>
      ) : null}

      {!loading && !error && !payload ? <div className="monitor-frame p-3 text-[12px] leading-relaxed text-slate-500">No why-trace selected.</div> : null}
    </div>
  );
}
