import { useEffect, useRef, useState } from "react";
import type { Equipment } from "./types";
import type { SystemContext } from "../../intelligence/systemContext";

type RightDetailsTabProps = {
  selectedEquipment: Equipment;
  systemContext?: SystemContext | null;
  behaviorExplanation?: string;
  whyFocusToken?: number;
};

export default function RightDetailsTab({
  selectedEquipment,
  systemContext = null,
  behaviorExplanation = "",
  whyFocusToken = 0,
}: RightDetailsTabProps) {
  const ctx = systemContext;
  const whySectionRef = useRef<HTMLDivElement | null>(null);
  const [isWhyFocused, setIsWhyFocused] = useState<boolean>(false);

  const cleanItems = (values: string[]): string[] => {
    const seen = new Set<string>();
    const result: string[] = [];
    for (const value of values) {
      const normalized = value.trim();
      const lower = normalized.toLowerCase();
      if (!normalized || lower === "n/a" || lower === "none" || normalized === "-" || normalized === "—") {
        continue;
      }
      if (seen.has(normalized)) {
        continue;
      }
      seen.add(normalized);
      result.push(normalized);
    }
    return result;
  };

  const asReadableText = (value?: string): string => {
    const normalized = (value || "").trim();
    if (!normalized || normalized === "—" || normalized.toLowerCase() === "n/a" || normalized.toLowerCase() === "none") {
      return "Not specified";
    }
    return normalized;
  };

  useEffect(() => {
    if (!whyFocusToken) {
      return;
    }
    whySectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    setIsWhyFocused(true);
    const timer = window.setTimeout(() => setIsWhyFocused(false), 1300);
    return () => {
      window.clearTimeout(timer);
    };
  }, [whyFocusToken]);

  const resolvedWhyText = behaviorExplanation || "No engineering explanation available for this tag yet.";
  const tagId = ctx?.tag || selectedEquipment.id;
  const controlInputs = cleanItems((ctx?.control.control_inputs || []).concat(ctx?.runtime.dependencies || []));
  const controlOutputs = cleanItems((ctx?.control.control_outputs || []).concat(ctx?.runtime.influences || []));
  const logicBlocks = cleanItems(ctx?.control.logic_blocks || []);
  const interlocks = ctx?.safety.interlocks || [];
  const alarmTags = cleanItems(ctx?.safety.alarm_tags || []);
  const upstreamPath = cleanItems((ctx?.graph.upstream || []).concat(ctx?.pid.upstream_tags || []));
  const downstreamPath = cleanItems((ctx?.graph.downstream || []).concat(ctx?.pid.downstream_tags || []));

  const summaryFromBehavior = resolvedWhyText
    .replace(/\s+/g, " ")
    .trim()
    .split(/(?<=[.!?])\s+/)
    .filter((line) => line.length > 0)
    .slice(0, 2)
    .join(" ");

  const generatedSummaryParts = [
    `${tagId} is mapped to ${ctx?.process.equipment || ctx?.process.area || ctx?.process.unit || "the current process area"}.`,
    downstreamPath.length
      ? `It influences downstream elements including ${downstreamPath.slice(0, 3).join(", ")}${downstreamPath.length > 3 ? ", and others" : ""}.`
      : "No downstream influence path is currently detected.",
  ];
  const summaryText = summaryFromBehavior || generatedSummaryParts.join(" ");

  return (
    <>
      <dl className="kv kv-technical">
        <dt>Equipment</dt>
        <dd>{ctx?.tag || selectedEquipment.id}</dd>
        <dt>Type</dt>
        <dd>{ctx?.isa.full_type || selectedEquipment.type}</dd>
        <dt>Loop</dt>
        <dd>{ctx?.isa.loop_id || "N/A"}</dd>
        <dt>Device Type</dt>
        <dd>{ctx?.isa.device_type || "N/A"}</dd>
        <dt>Function</dt>
        <dd>{ctx?.isa.function || "N/A"}</dd>
        <dt>Status</dt>
        <dd>{selectedEquipment.status}</dd>
        <dt>Process Unit</dt>
        <dd>{ctx?.process.unit || selectedEquipment.processUnit || "N/A"}</dd>
        <dt>Area</dt>
        <dd>{ctx?.process.area || "N/A"}</dd>
        <dt>Service</dt>
        <dd>{ctx?.process.service || "N/A"}</dd>
        <dt>Control Role</dt>
        <dd>{ctx?.control.role || selectedEquipment.controlRole || "N/A"}</dd>
        <dt>Strategy</dt>
        <dd>{ctx?.control.control_strategy || "N/A"}</dd>
        <dt>Mode</dt>
        <dd>{ctx?.control.control_mode || ctx?.runtime.mode || "N/A"}</dd>
        <dt>Signal Type</dt>
        <dd>{selectedEquipment.signalType ?? "N/A"}</dd>
        <dt>Instrument Role</dt>
        <dd>{selectedEquipment.instrumentRole ?? "N/A"}</dd>
        <dt>Power Rating</dt>
        <dd>{selectedEquipment.powerRating ?? "N/A"}</dd>
      </dl>

      <div className="panel-subtitle">Connections</div>
      <ul className="trace-chain">
        {(selectedEquipment.connections.length ? selectedEquipment.connections : ["No known process connections"]).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <div ref={whySectionRef} className={`why-panel ${isWhyFocused ? "focused" : ""}`}>
        <div className="panel-subtitle">WHY / Behavior</div>
        <div className="why-section">
          <div className="why-section-title">Summary</div>
          <p className="why-summary">{summaryText}</p>
        </div>

        <div className="why-section">
          <div className="why-section-title">Inputs</div>
          {controlInputs.length > 0 ? (
            <div className="why-chip-list">
              {controlInputs.map((item) => (
                <span className="why-chip" key={`input-${item}`}>
                  {item}
                </span>
              ))}
            </div>
          ) : (
            <div className="why-empty">No control inputs detected</div>
          )}
        </div>

        <div className="why-section">
          <div className="why-section-title">Outputs</div>
          {controlOutputs.length > 0 ? (
            <div className="why-chip-list">
              {controlOutputs.map((item) => (
                <span className="why-chip" key={`output-${item}`}>
                  {item}
                </span>
              ))}
            </div>
          ) : (
            <div className="why-empty">No control outputs detected</div>
          )}
        </div>

        <div className="why-section why-key-values">
          <div className="why-section-title">Control Strategy</div>
          <div>{asReadableText(ctx?.control.control_strategy)}</div>
          <div className="why-section-title">Role</div>
          <div>{asReadableText(ctx?.control.role)}</div>
          <div className="why-section-title">Mode</div>
          <div>{asReadableText(ctx?.control.control_mode || ctx?.runtime.mode)}</div>
        </div>

        <div className="why-section">
          <div className="why-section-title">Logic Blocks</div>
          {logicBlocks.length > 0 ? (
            <ul className="why-stack-list">
              {logicBlocks.map((item) => (
                <li key={`logic-${item}`}>{item}</li>
              ))}
            </ul>
          ) : (
            <div className="why-empty">No logic blocks detected</div>
          )}
        </div>

        <div className="why-section">
          <div className="why-section-title">Interlocks</div>
          {interlocks.length > 0 ? (
            <ul className="why-stack-list">
              {interlocks.map((item, index) => (
                <li key={`interlock-${index}`}>{`${item.trigger} -> ${item.action}`}</li>
              ))}
            </ul>
          ) : (
            <div className="why-empty">No interlocks detected</div>
          )}
        </div>

        <div className="why-section">
          <div className="why-section-title">Alarms</div>
          {alarmTags.length > 0 ? (
            <ul className="why-stack-list">
              {alarmTags.map((item) => (
                <li key={`alarm-${item}`}>{item}</li>
              ))}
            </ul>
          ) : (
            <div className="why-empty">No alarms detected</div>
          )}
        </div>

        <div className="why-section">
          <div className="why-section-title">Influence Paths</div>
          <div className="why-path-block">
            <div className="why-path-title">Upstream Path</div>
            {upstreamPath.length > 0 ? (
              <div className="why-chip-list">
                {upstreamPath.map((item) => (
                  <span className="why-chip" key={`upstream-${item}`}>
                    {item}
                  </span>
                ))}
              </div>
            ) : (
              <div className="why-empty">No upstream path detected</div>
            )}
          </div>
          <div className="why-path-block">
            <div className="why-path-title">Downstream Path</div>
            {downstreamPath.length > 0 ? (
              <div className="why-chip-list">
                {downstreamPath.map((item) => (
                  <span className="why-chip" key={`downstream-${item}`}>
                    {item}
                  </span>
                ))}
              </div>
            ) : (
              <div className="why-empty">No downstream path detected</div>
            )}
          </div>
        </div>
      </div>

      <div className="panel-subtitle">Control Path</div>
      <ul className="trace-chain">
        {(selectedEquipment.controlPath.length ? selectedEquipment.controlPath : ["No control path available"]).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <div className="panel-subtitle">Controls</div>
      <ul className="trace-chain">
        {(selectedEquipment.controls.length ? selectedEquipment.controls : ["No control targets available"]).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <div className="panel-subtitle">Measures</div>
      <ul className="trace-chain">
        {(selectedEquipment.measures.length ? selectedEquipment.measures : ["No measurement targets available"]).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <div className="panel-subtitle">Inference Confidence</div>
      <ul className="trace-chain">
        {Object.entries(selectedEquipment.metadataConfidence).length ? (
          Object.entries(selectedEquipment.metadataConfidence)
            .sort((left, right) => right[1] - left[1])
            .slice(0, 5)
            .map(([key, value]) => <li key={key}>{`${key}: ${(value * 100).toFixed(0)}%`}</li>)
        ) : (
          <li>No confidence scores available</li>
        )}
      </ul>
    </>
  );
}
