import { useEffect, useMemo, useRef, useState } from "react";
import { getDeterministicBehaviorRows, getDeterministicWhyTrace, type DeterministicBehaviorRow, type DeterministicWhyTraceResponse } from "../../services/api";

type RightWhyTracePanelProps = {
  tag: string;
  onClose?: () => void;
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

export default function RightWhyTracePanel({ tag, onClose }: RightWhyTracePanelProps) {
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
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div>
          <div className="panel-subtitle">Why Trace</div>
          <p className="text-[11px] text-slate-500">{tag}</p>
        </div>
        {onClose ? (
          <button type="button" className="command-btn" onClick={onClose}>
            Close Why
          </button>
        ) : null}
      </div>

      {loading ? <div className="monitor-frame">Loading why trace...</div> : null}
      {error ? <div className="monitor-frame text-red-700">{error}</div> : null}

      {!loading && !error && payload ? (
        <>
          <div className="monitor-frame">
            <div className="text-[10px] uppercase tracking-wide text-slate-500">Summary</div>
            <p className="text-xs text-slate-700">{toText(payload.behavior_summary)}</p>
          </div>

          {steps.length === 0 ? (
            <div className="monitor-frame text-slate-500">No trace steps available for this tag.</div>
          ) : (
            <div className="space-y-2">
              {steps.map((step, index) => (
                <div key={`${step.tag}-${step.direction}-${step.depth}-${index}`} className="monitor-frame">
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <span className="text-xs font-semibold text-slate-800">{step.tag}</span>
                    <span className="text-[10px] uppercase tracking-wide text-slate-500">
                      d{step.depth} · {step.direction}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[11px] text-slate-700">
                    <p>Type: {toText(step.type)}</p>
                    <p>Subtype: {toText(step.subtype)}</p>
                    <p>Value: {toText(step.value)}</p>
                    <p>State: {toText(step.state)}</p>
                    <p>Setpoint: {toText(step.setpoint)}</p>
                    <p>Mode: {toText(step.mode)}</p>
                  </div>

                  <p className="mt-1 text-[11px] text-slate-700">{toText(step.behavior_summary)}</p>
                </div>
              ))}
            </div>
          )}
        </>
      ) : null}

      {!loading && !error && !payload ? <div className="monitor-frame text-slate-500">No why-trace selected.</div> : null}
    </div>
  );
}
