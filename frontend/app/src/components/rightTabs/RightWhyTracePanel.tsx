import { useEffect, useMemo, useRef, useState } from "react";
import {
  getDeterministicBehaviorRows,
  getDeterministicWhyTrace,
  type DeterministicBehaviorRow,
  type DeterministicWhyNarrative,
  type DeterministicWhyStructureRankedChain,
  type DeterministicWhyTraceResponse,
} from "../../services/api";

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

type ResolvedWhyStructure = {
  ranked_upstream: DeterministicWhyStructureRankedChain[];
  ranked_downstream: DeterministicWhyStructureRankedChain[];
  merged_context: {
    parallel_upstream: string[];
    parallel_downstream: string[];
  };
};

const resolveWhyStructure = (payload: DeterministicWhyTraceResponse | null): ResolvedWhyStructure => {
  if (!payload) {
    return {
      ranked_upstream: [],
      ranked_downstream: [],
      merged_context: {
        parallel_upstream: [],
        parallel_downstream: [],
      },
    };
  }

  if (payload.structure) {
    return {
      ranked_upstream: payload.structure.ranked_upstream ?? [],
      ranked_downstream: payload.structure.ranked_downstream ?? [],
      merged_context: {
        parallel_upstream: payload.structure.merged_context?.parallel_upstream ?? [],
        parallel_downstream: payload.structure.merged_context?.parallel_downstream ?? [],
      },
    };
  }

  const debugChains = payload.debug?.chains;
  const mapChain = (chain: {
    nodes: string[];
    score: number;
    weak_links: { index: number; source: string; target: string; rel_type: string; confidence: number; reasons: string[] }[];
    broken: boolean;
    break_reason: string;
  }): DeterministicWhyStructureRankedChain => ({
    tags: chain.nodes ?? [],
    score: Number.isFinite(chain.score) ? chain.score : 0,
    depth: Math.max(0, (chain.nodes ?? []).length - 1),
    weak_links: chain.weak_links ?? [],
    broken: Boolean(chain.broken),
    break_reason: chain.broken ? (chain.break_reason ?? null) : null,
  });

  return {
    ranked_upstream: (debugChains?.ranked_upstream ?? []).map(mapChain),
    ranked_downstream: (debugChains?.ranked_downstream ?? []).map(mapChain),
    merged_context: {
      parallel_upstream: debugChains?.merged_context?.parallel_upstream_tags ?? [],
      parallel_downstream: debugChains?.merged_context?.parallel_downstream_tags ?? [],
    },
  };
};

const resolveWhyExplanation = (payload: DeterministicWhyTraceResponse | null): DeterministicWhyNarrative => {
  const source = payload?.explanation ?? payload?.narrative;
  return {
    summary: (source?.summary ?? "").trim() || "No summary available.",
    behavior: (source?.behavior ?? "").trim() || "No behavior explanation available.",
    upstream: (source?.upstream ?? "").trim() || "No upstream explanation available.",
    downstream: (source?.downstream ?? "").trim() || "No downstream explanation available.",
    state: (source?.state ?? "").trim() || "No state explanation available.",
    warnings: Array.isArray(source?.warnings) ? source!.warnings : [],
  };
};

export default function RightWhyTracePanel({ tag, onClose, onSelectTag }: RightWhyTracePanelProps) {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [payload, setPayload] = useState<DeterministicWhyTraceResponse | null>(null);
  const [rowsByTag, setRowsByTag] = useState<Record<string, DeterministicBehaviorRow>>({});
  const [debugExpanded, setDebugExpanded] = useState<boolean>(true);
  const requestRef = useRef<number>(0);

  useEffect(() => {
    requestRef.current += 1;
    const requestId = requestRef.current;
    const selectedTagAtRequest = String(tag || "").trim();

    setPayload(null);
    setRowsByTag({});

    const load = async (): Promise<void> => {
      setLoading(true);
      setError(null);
      try {
        const whyPayload = await getDeterministicWhyTrace(selectedTagAtRequest, 4);
        if (requestRef.current !== requestId) {
          return;
        }

        const responseTag = String(whyPayload.tag || "").trim();
        const requestedTag = selectedTagAtRequest;
        const upstreamLen = whyPayload.structure?.ranked_upstream?.length ?? whyPayload.debug?.chains?.ranked_upstream?.length ?? 0;
        const downstreamLen = whyPayload.structure?.ranked_downstream?.length ?? whyPayload.debug?.chains?.ranked_downstream?.length ?? 0;
        console.debug("[WHY_UI_DEBUG]", {
          selected_tag: requestedTag,
          response_tag: responseTag,
          ranked_upstream_length: upstreamLen,
          ranked_downstream_length: downstreamLen,
        });

        if (responseTag !== requestedTag) {
          console.error("[WHY_UI_DEBUG] selected/response tag mismatch", { requestedTag, responseTag });
          setPayload(null);
          setRowsByTag({});
          setError(`Why trace tag mismatch. requested=${requestedTag} response=${responseTag}`);
          return;
        }

        const explanation = whyPayload.explanation ?? whyPayload.narrative;
        console.debug("[WHY_UI_NARRATIVE]", {
          selectedTag: requestedTag,
          responseTag,
          explanationPresent: Boolean(explanation),
          summaryLength: String(explanation?.summary ?? "").length,
          warningsCount: Array.isArray(explanation?.warnings) ? explanation!.warnings.length : 0,
        });

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
        setError(`Why trace unavailable for ${selectedTagAtRequest}.`);
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

  const resolvedStructure = useMemo<ResolvedWhyStructure>(() => resolveWhyStructure(payload), [payload]);
  const resolvedExplanation = useMemo<DeterministicWhyNarrative>(() => resolveWhyExplanation(payload), [payload]);
  const chainHealth = useMemo(() => {
    const allChains = [...resolvedStructure.ranked_upstream, ...resolvedStructure.ranked_downstream];
    const brokenCount = allChains.filter((item) => item.broken).length;
    const weakLinkCount = allChains.reduce((total, item) => total + (item.weak_links?.length ?? 0), 0);
    const zeroReason =
      payload?.structure?.diagnostics?.reason ||
      payload?.debug?.chains?.diagnostics?.zero_reason ||
      "";
    return {
      totalChains: allChains.length,
      brokenCount,
      weakLinkCount,
      healthyCount: Math.max(0, allChains.length - brokenCount),
      zeroReason,
    };
  }, [payload, resolvedStructure]);

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
            <div className="text-[9px] font-semibold text-slate-500">Summary</div>
            <p className="max-w-full whitespace-pre-wrap break-words text-[12px] leading-relaxed text-slate-700">{toText(resolvedExplanation.summary)}</p>
          </div>

          <div className="monitor-frame space-y-1 p-3">
            <div className="text-[9px] font-semibold text-slate-500">Behavior</div>
            <p className="max-w-full whitespace-pre-wrap break-words text-[12px] leading-relaxed text-slate-700">{toText(resolvedExplanation.behavior)}</p>
          </div>

          <div className="monitor-frame space-y-1 p-3">
            <div className="text-[9px] font-semibold text-slate-500">Upstream</div>
            <p className="max-w-full whitespace-pre-wrap break-words text-[12px] leading-relaxed text-slate-700">{toText(resolvedExplanation.upstream)}</p>
          </div>

          <div className="monitor-frame space-y-1 p-3">
            <div className="text-[9px] font-semibold text-slate-500">Downstream</div>
            <p className="max-w-full whitespace-pre-wrap break-words text-[12px] leading-relaxed text-slate-700">{toText(resolvedExplanation.downstream)}</p>
          </div>

          <div className="monitor-frame space-y-1 p-3">
            <div className="text-[9px] font-semibold text-slate-500">State</div>
            <p className="max-w-full whitespace-pre-wrap break-words text-[12px] leading-relaxed text-slate-700">{toText(resolvedExplanation.state)}</p>
          </div>

          {resolvedExplanation.warnings.length > 0 ? (
            <div className="monitor-frame space-y-2 border-amber-200 bg-amber-50/40 p-3">
              <div className="text-[9px] font-semibold text-amber-700">Warnings</div>
              <div className="space-y-1">
                {resolvedExplanation.warnings.map((warning, index) => (
                  <p key={`narrative-warning-${index}`} className="max-w-full whitespace-pre-wrap break-words text-[11px] leading-relaxed text-amber-800">
                    {warning}
                  </p>
                ))}
              </div>
            </div>
          ) : null}

          <div className="monitor-frame p-3">
            <div className="mb-2 flex items-center justify-between gap-2">
              <div className="text-[9px] font-semibold text-slate-500">Why Debug</div>
              <button type="button" className="command-btn" onClick={() => setDebugExpanded((value) => !value)}>
                {debugExpanded ? "Collapse" : "Expand"}
              </button>
            </div>

            {debugExpanded ? (
              <div className="space-y-3">
                <section className="rounded border border-slate-200 bg-slate-50 p-2">
                  <div className="mb-1 text-[9px] font-semibold text-slate-500">Role / Classification</div>
                  <div className="mb-1 inline-flex items-center rounded border border-blue-200 bg-blue-50 px-2 py-0.5 text-[11px] font-semibold text-blue-700">
                    {toText(payload.debug?.classification?.selected_tag_role)}
                  </div>
                  <p className="text-[11px] text-slate-600">{toText(payload.debug?.classification?.selected_tag_role_reason)}</p>
                </section>

                <section className="rounded border border-slate-200 bg-slate-50 p-2">
                  <div className="mb-2 text-[9px] font-semibold text-slate-500">Ranked Upstream Chains</div>
                  {resolvedStructure.ranked_upstream.length === 0 ? (
                    <p className="text-[11px] text-slate-500">No ranked upstream chains.</p>
                  ) : (
                    <div className="space-y-2">
                      {resolvedStructure.ranked_upstream.map((chain, index) => (
                        <div
                          key={`upstream-${index}`}
                          className={`rounded border bg-white p-2 ${chain.broken ? "border-amber-300" : "border-slate-200"}`}
                        >
                          <p className="break-all text-[11px] text-slate-800">{chain.tags.length ? chain.tags.join(" → ") : "—"}</p>
                          <p className="mt-1 text-[10px] text-slate-600">
                            score {toText(chain.score)} | depth {toText(chain.depth)} | broken {chain.broken ? "yes" : "no"} | weak links {chain.weak_links?.length ?? 0}
                          </p>
                          {chain.break_reason ? <p className="mt-1 text-[10px] text-slate-500">break reason: {chain.break_reason}</p> : null}
                          {(chain.weak_links ?? []).length > 0 ? (
                            <div className="mt-1 flex flex-wrap gap-1">
                              {(chain.weak_links ?? []).map((weak, weakIndex) => (
                                <span key={`up-weak-${index}-${weakIndex}`} className="rounded border border-amber-200 bg-amber-50 px-1.5 py-0.5 text-[10px] text-amber-800">
                                  {weak.source}→{weak.target} ({(weak.reasons ?? []).join(",") || "weak"})
                                </span>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  )}
                </section>

                <section className="rounded border border-slate-200 bg-slate-50 p-2">
                  <div className="mb-2 text-[9px] font-semibold text-slate-500">Ranked Downstream Chains</div>
                  {resolvedStructure.ranked_downstream.length === 0 ? (
                    <p className="text-[11px] text-slate-500">No ranked downstream chains.</p>
                  ) : (
                    <div className="space-y-2">
                      {resolvedStructure.ranked_downstream.map((chain, index) => (
                        <div
                          key={`downstream-${index}`}
                          className={`rounded border bg-white p-2 ${chain.broken ? "border-amber-300" : "border-slate-200"}`}
                        >
                          <p className="break-all text-[11px] text-slate-800">{chain.tags.length ? chain.tags.join(" → ") : "—"}</p>
                          <p className="mt-1 text-[10px] text-slate-600">
                            score {toText(chain.score)} | depth {toText(chain.depth)} | broken {chain.broken ? "yes" : "no"} | weak links {chain.weak_links?.length ?? 0}
                          </p>
                          {chain.break_reason ? <p className="mt-1 text-[10px] text-slate-500">break reason: {chain.break_reason}</p> : null}
                          {(chain.weak_links ?? []).length > 0 ? (
                            <div className="mt-1 flex flex-wrap gap-1">
                              {(chain.weak_links ?? []).map((weak, weakIndex) => (
                                <span key={`down-weak-${index}-${weakIndex}`} className="rounded border border-amber-200 bg-amber-50 px-1.5 py-0.5 text-[10px] text-amber-800">
                                  {weak.source}→{weak.target} ({(weak.reasons ?? []).join(",") || "weak"})
                                </span>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  )}
                </section>

                <section className="rounded border border-slate-200 bg-slate-50 p-2">
                  <div className="mb-1 text-[9px] font-semibold text-slate-500">Merged Context</div>
                  <div className="grid grid-cols-1 gap-1 text-[11px] text-slate-700">
                    <p className="break-all">parallel_upstream: {toText(resolvedStructure.merged_context.parallel_upstream.join(", "))}</p>
                    <p className="break-all">parallel_downstream: {toText(resolvedStructure.merged_context.parallel_downstream.join(", "))}</p>
                  </div>
                </section>

                <section className="rounded border border-slate-200 bg-slate-50 p-2">
                  <div className="mb-1 text-[9px] font-semibold text-slate-500">Chain Health</div>
                  <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[11px] text-slate-700">
                    <p>Total chains: {chainHealth.totalChains}</p>
                    <p>Healthy chains: {chainHealth.healthyCount}</p>
                    <p>Broken chains: {chainHealth.brokenCount}</p>
                    <p>Weak links: {chainHealth.weakLinkCount}</p>
                  </div>
                  {chainHealth.totalChains === 0 && chainHealth.zeroReason ? (
                    <p className="mt-1 text-[10px] text-slate-500">resolver diagnostic: {chainHealth.zeroReason}</p>
                  ) : null}
                </section>

                <section className="rounded border border-slate-200 bg-slate-50 p-2">
                  <div className="mb-1 text-[9px] font-semibold text-slate-500">Graph Summary</div>
                  <div className="grid grid-cols-1 gap-x-3 gap-y-1 text-[11px] text-slate-700 sm:grid-cols-2">
                    <p>Incoming edges: {toText(payload.debug?.graph?.incoming_edge_count)}</p>
                    <p>Outgoing edges: {toText(payload.debug?.graph?.outgoing_edge_count)}</p>
                    <p className="sm:col-span-2 break-all">Upstream: {toText((payload.debug?.graph?.normalized_upstream_tags ?? []).join(", "))}</p>
                    <p className="sm:col-span-2 break-all">Downstream: {toText((payload.debug?.graph?.normalized_downstream_tags ?? []).join(", "))}</p>
                  </div>
                </section>

                <section className="rounded border border-slate-200 bg-slate-50 p-2">
                  <div className="mb-1 text-[9px] font-semibold text-slate-500">Connected Edge Details</div>
                  {(payload.debug?.edges ?? []).length === 0 ? (
                    <p className="text-[11px] text-slate-500">No direct edges available.</p>
                  ) : (
                    <div className="max-h-44 overflow-auto rounded border border-slate-200 bg-white">
                      <table className="w-full table-fixed border-collapse text-[11px] text-slate-700">
                        <thead className="bg-slate-100 text-[9px] text-slate-500">
                          <tr>
                            <th className="border-b border-slate-200 px-2 py-1 text-left">Edge</th>
                            <th className="border-b border-slate-200 px-2 py-1 text-left">Type</th>
                            <th className="border-b border-slate-200 px-2 py-1 text-left">Confidence</th>
                            <th className="border-b border-slate-200 px-2 py-1 text-left">Source</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(payload.debug?.edges ?? []).map((edge, index) => (
                            <tr key={`${edge.source}-${edge.target}-${edge.rel_type}-${index}`}>
                              <td className="border-b border-slate-100 px-2 py-1 break-all">{edge.source} → {edge.target}</td>
                              <td className="border-b border-slate-100 px-2 py-1">{toText(edge.rel_type)}</td>
                              <td className="border-b border-slate-100 px-2 py-1">{toText(edge.confidence)}</td>
                              <td className="border-b border-slate-100 px-2 py-1">{edge.inferred ? `inferred:${edge.source_type}` : "explicit"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </section>

                <section className="rounded border border-slate-200 bg-slate-50 p-2">
                  <div className="mb-1 text-[9px] font-semibold text-slate-500">Neighbor Roles</div>
                  {(payload.debug?.neighbors ?? []).length === 0 ? (
                    <p className="text-[11px] text-slate-500">No immediate neighbors available.</p>
                  ) : (
                    <div className="max-h-36 space-y-1 overflow-auto text-[11px] text-slate-700">
                      {(payload.debug?.neighbors ?? []).map((neighbor) => (
                        <div key={neighbor.tag} className="flex flex-wrap items-center gap-2 rounded border border-slate-200 bg-white px-2 py-1">
                          <button type="button" className="font-semibold text-slate-800 hover:text-red-600" onClick={() => onSelectTag?.(neighbor.tag)}>
                            {neighbor.tag}
                          </button>
                          <span className="rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-[9px] text-slate-600">
                            {toText(neighbor.role)}
                          </span>
                          <span className="text-slate-500">{toText(neighbor.type)} / {toText(neighbor.subtype)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </section>
              </div>
            ) : null}
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
                    <span className="shrink-0 text-[9px] text-slate-500">
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
