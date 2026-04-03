import { useState } from "react";
import { applyOverride, removeOverride } from "./simulationApi";

type Props = {
  onStatus?: (message: string) => void;
};

export default function SimulationEngine({ onStatus }: Props) {
  const [overrideId, setOverrideId] = useState("");
  const [overrideValue, setOverrideValue] = useState("");

  const handleOverride = async (): Promise<void> => {
    if (!overrideId.trim()) return;
    let value: unknown = overrideValue;
    const numeric = Number(overrideValue);
    if (!Number.isNaN(numeric) && overrideValue.trim() !== "") {
      value = numeric;
    }
    try {
      await applyOverride({ id: overrideId.trim(), value });
      onStatus?.(`Override applied to ${overrideId.trim()}`);
      setOverrideValue("");
    } catch (error) {
      onStatus?.(error instanceof Error ? error.message : "Override failed");
    }
  };

  return (
    <section className="workspace-documents-list-panel">
      <div className="workspace-documents-list-header">
        <h3>Simulation Overrides</h3>
        <p>Apply what-if values to tags from the centralized unified store.</p>
      </div>
      <div className="settings-grid">
        <label className="settings-line">
          <span>Tag ID</span>
          <input value={overrideId} onChange={(event) => setOverrideId(event.target.value)} />
        </label>
        <label className="settings-line">
          <span>Override Value</span>
          <input value={overrideValue} onChange={(event) => setOverrideValue(event.target.value)} />
        </label>
      </div>
      <div className="modal-actions">
        <button type="button" className="command-btn primary" onClick={() => void handleOverride()}>
          Apply Override
        </button>
        <button
          type="button"
          className="command-btn"
          onClick={() => {
            if (!overrideId.trim()) return;
            void removeOverride(overrideId.trim())
              .then(() => onStatus?.(`Override removed for ${overrideId.trim()}`))
              .catch((error) => onStatus?.(error instanceof Error ? error.message : "Remove override failed"));
          }}
        >
          Remove Override
        </button>
      </div>
    </section>
  );
}
