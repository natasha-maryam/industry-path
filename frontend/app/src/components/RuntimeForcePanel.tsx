import { useEffect, useMemo, useState } from "react";
import { isAxiosError } from "axios";
import type { RuntimeSignalType } from "../services/api";
import "../styles/runtime-validation-panel.css";

type ForceableInput = {
  tag: string;
  io_type: string;
  type: RuntimeSignalType;
  current_value: unknown;
  forced: boolean;
  forced_at: string | null;
};

type RuntimeForcePanelProps = {
  title?: string;
  forceableInputs?: ForceableInput[];
  actionLoading?: boolean;
  validatedAt?: string;
  onApplyInputForce?: (payload: { tag: string; value: unknown; type: RuntimeSignalType }) => Promise<void>;
  onClearInputForce?: (tag: string) => Promise<void>;
  onRefreshInputForceState?: () => Promise<void>;
  onRunEvaluationCycle?: () => Promise<void>;
};

const formatTimestamp = (value: string): string => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
};

export default function RuntimeForcePanel({
  title = "Input Force Simulation",
  forceableInputs = [],
  actionLoading = false,
  validatedAt,
  onApplyInputForce,
  onClearInputForce,
  onRefreshInputForceState,
  onRunEvaluationCycle,
}: RuntimeForcePanelProps) {
  const [selectedForceTag, setSelectedForceTag] = useState<string>("");
  const [forceRawValue, setForceRawValue] = useState<string>("");
  const [forceBoolValue, setForceBoolValue] = useState<boolean>(false);
  const [forceBusy, setForceBusy] = useState<boolean>(false);
  const [forceMessage, setForceMessage] = useState<string>("");
  const [forceError, setForceError] = useState<string>("");
  const [lastForceUpdatedAt, setLastForceUpdatedAt] = useState<string | null>(null);

  const selectedForceInput = useMemo(
    () => forceableInputs.find((item) => item.tag === selectedForceTag) ?? null,
    [forceableInputs, selectedForceTag]
  );

  useEffect(() => {
    if (forceableInputs.length === 0) {
      setSelectedForceTag("");
      return;
    }
    if (!selectedForceTag || !forceableInputs.some((item) => item.tag === selectedForceTag)) {
      setSelectedForceTag(forceableInputs[0].tag);
    }
  }, [forceableInputs, selectedForceTag]);

  useEffect(() => {
    if (!selectedForceInput) {
      setForceRawValue("");
      setForceBoolValue(false);
      return;
    }
    if (selectedForceInput.type === "BOOL") {
      setForceBoolValue(Boolean(selectedForceInput.current_value));
    } else {
      setForceRawValue(String(selectedForceInput.current_value ?? ""));
    }
  }, [selectedForceInput?.tag, selectedForceInput?.type, selectedForceInput?.current_value]);

  const applyForceDisabled =
    forceBusy ||
    actionLoading ||
    !selectedForceInput ||
    !onApplyInputForce ||
    (selectedForceInput.type !== "BOOL" && forceRawValue.trim().length === 0);

  const handleApplyForce = async (): Promise<void> => {
    if (!selectedForceInput || !onApplyInputForce) {
      return;
    }

    let payloadValue: unknown = forceRawValue;
    if (selectedForceInput.type === "BOOL") {
      payloadValue = forceBoolValue;
    } else if (selectedForceInput.type === "INT") {
      const parsed = Number.parseInt(forceRawValue.trim(), 10);
      if (!Number.isFinite(parsed)) {
        setForceError("Invalid INT value.");
        setForceMessage("");
        return;
      }
      payloadValue = parsed;
    } else if (selectedForceInput.type === "REAL") {
      const parsed = Number.parseFloat(forceRawValue.trim());
      if (!Number.isFinite(parsed)) {
        setForceError("Invalid REAL value.");
        setForceMessage("");
        return;
      }
      payloadValue = parsed;
    }

    setForceBusy(true);
    setForceError("");
    setForceMessage("");
    try {
      await onApplyInputForce({
        tag: selectedForceInput.tag,
        value: payloadValue,
        type: selectedForceInput.type,
      });
      if (onRefreshInputForceState) {
        await onRefreshInputForceState();
      }
      const now = new Date().toISOString();
      setLastForceUpdatedAt(now);
      setForceMessage(`Force applied for ${selectedForceInput.tag}.`);
    } catch (error) {
      if (isAxiosError(error)) {
        const detail = error.response?.data?.detail;
        if (typeof detail === "string" && detail.trim()) {
          setForceError(detail);
        } else {
          setForceError("Apply force failed.");
        }
      } else {
        setForceError("Apply force failed.");
      }
    } finally {
      setForceBusy(false);
    }
  };

  const handleClearForce = async (): Promise<void> => {
    if (!selectedForceInput || !onClearInputForce) {
      return;
    }
    setForceBusy(true);
    setForceError("");
    setForceMessage("");
    try {
      await onClearInputForce(selectedForceInput.tag);
      if (onRefreshInputForceState) {
        await onRefreshInputForceState();
      }
      const now = new Date().toISOString();
      setLastForceUpdatedAt(now);
      setForceMessage(`Force cleared for ${selectedForceInput.tag}.`);
    } catch (error) {
      if (isAxiosError(error)) {
        const detail = error.response?.data?.detail;
        if (typeof detail === "string" && detail.trim()) {
          setForceError(detail);
        } else {
          setForceError("Clear force failed.");
        }
      } else {
        setForceError("Clear force failed.");
      }
    } finally {
      setForceBusy(false);
    }
  };

  return (
    <div className="runtime-force-panel">
      <h4>{title}</h4>
      {forceableInputs.length === 0 ? (
        <div className="runtime-validation-empty">No input tags available for force simulation.</div>
      ) : (
        <>
          <div className="runtime-force-grid">
            <label className="runtime-force-field">
              Input Tag
              <select value={selectedForceTag} onChange={(event) => setSelectedForceTag(event.target.value)}>
                {forceableInputs.map((item) => (
                  <option key={item.tag} value={item.tag}>
                    {item.tag}
                  </option>
                ))}
              </select>
            </label>
            <div className="runtime-force-field runtime-force-readout-wrap">
              <span className="runtime-force-field-label">Input State</span>
              <div className="runtime-force-readout">
                <span>Current: {String(selectedForceInput?.current_value ?? "-")}</span>
                <span>Type: {selectedForceInput?.type ?? "-"}</span>
              </div>
            </div>
            {selectedForceInput?.type === "BOOL" ? (
              <label className="runtime-force-field">
                Forced Value
                <select value={forceBoolValue ? "true" : "false"} onChange={(event) => setForceBoolValue(event.target.value === "true")}>
                  <option value="false">false</option>
                  <option value="true">true</option>
                </select>
              </label>
            ) : (
              <label className="runtime-force-field">
                Forced Value
                <input
                  type={selectedForceInput?.type === "STRING" ? "text" : "number"}
                  step={selectedForceInput?.type === "INT" ? "1" : "any"}
                  value={forceRawValue}
                  onChange={(event) => setForceRawValue(event.target.value)}
                  placeholder={
                    selectedForceInput?.type === "INT"
                      ? "Enter integer"
                      : selectedForceInput?.type === "REAL"
                        ? "Enter numeric value"
                        : "Enter text"
                  }
                />
              </label>
            )}
          </div>
          <div className="runtime-force-actions">
            <button className="command-btn" type="button" disabled={applyForceDisabled} onClick={() => void handleApplyForce()}>
              Apply Force
            </button>
            <button
              className="command-btn"
              type="button"
              disabled={forceBusy || actionLoading || !selectedForceInput || !onClearInputForce}
              onClick={() => void handleClearForce()}
            >
              Clear Force
            </button>
            <button
              className="command-btn"
              type="button"
              disabled={forceBusy || actionLoading || !onRunEvaluationCycle}
              onClick={() => {
                if (!onRunEvaluationCycle) {
                  return;
                }
                void onRunEvaluationCycle();
              }}
            >
              Run Evaluation Cycle
            </button>
          </div>
          <div className="runtime-force-status">
            <span>Status: {selectedForceInput?.forced ? "forced" : "not forced"}</span>
            <span>Last updated: {formatTimestamp(lastForceUpdatedAt || selectedForceInput?.forced_at || validatedAt || new Date().toISOString())}</span>
            {forceMessage ? <span className="runtime-force-ok">{forceMessage}</span> : null}
            {forceError ? <span className="runtime-force-error">{forceError}</span> : null}
          </div>
        </>
      )}
    </div>
  );
}