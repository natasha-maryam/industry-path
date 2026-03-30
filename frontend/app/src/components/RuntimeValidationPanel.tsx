import { useMemo } from "react";
import { AlertTriangle, CheckCircle2, LoaderCircle, PlayCircle, XCircle } from "lucide-react";
import type { PanelStatus, RuntimeSignalType, RuntimeValidationPanelResponse } from "../services/api";
import "../styles/runtime-validation-panel.css";

type RuntimeStepKey = "compile_st" | "build_runtime" | "apply_io" | "start_runtime";

type RuntimeStep = {
  key: RuntimeStepKey;
  label: string;
  status: PanelStatus;
  detail: string;
};

export type RuntimeFailureDiagnostic = {
  step: RuntimeStepKey;
  severity: "warning" | "error";
  message: string;
  detail?: string | null;
};

export type RuntimeValidationPanelData = RuntimeValidationPanelResponse & {
  runtime_state?: "running" | "stopped" | "failed" | "idle";
  deployed_at?: string;
  active_project?: string | null;
  runtime_project_dir?: string | null;
  steps_map?: Partial<Record<RuntimeStepKey, PanelStatus>>;
  step_messages?: Partial<Record<RuntimeStepKey, string>>;
  telemetry_tags?: Record<string, unknown>;
  errors?: string[];
};

type RuntimeValidationPanelProps = {
  data: RuntimeValidationPanelData | null;
  loading?: boolean;
  actionLoading?: boolean;
  failedMessage?: string | null;
  onDeploy?: () => void;
  onStart?: () => void;
  onStop?: () => void;
  forceableInputs?: Array<{
    tag: string;
    io_type: string;
    type: RuntimeSignalType;
    current_value: unknown;
    forced: boolean;
    forced_at: string | null;
  }>;
  onApplyInputForce?: (payload: { tag: string; value: unknown; type: RuntimeSignalType }) => Promise<void>;
  onClearInputForce?: (tag: string) => Promise<void>;
  onRefreshInputForceState?: () => Promise<void>;
  onRunEvaluationCycle?: () => Promise<void>;
  requiredPreviousStep?: string;
};

const STEP_LABELS: Record<RuntimeStepKey, string> = {
  compile_st: "compile_st",
  build_runtime: "build_runtime",
  apply_io: "apply_io",
  start_runtime: "start_runtime",
};

const statusIcon = (status: PanelStatus) => {
  if (status === "success") {
    return <CheckCircle2 size={14} />;
  }
  if (status === "failed") {
    return <XCircle size={14} />;
  }
  if (status === "running") {
    return <LoaderCircle size={14} className="runtime-validation-spin" />;
  }
  if (status === "warning") {
    return <AlertTriangle size={14} />;
  }
  return <PlayCircle size={14} />;
};

const statusLabel = (status: PanelStatus): string => {
  if (status === "success") {
    return "Success";
  }
  if (status === "failed") {
    return "Failed";
  }
  if (status === "running") {
    return "Running";
  }
  if (status === "warning") {
    return "Warning";
  }
  return "Idle";
};

const formatTimestamp = (value: string): string => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
};

const buildSteps = (data: RuntimeValidationPanelData): RuntimeStep[] => {
  const statusByKey: Record<RuntimeStepKey, PanelStatus> = {
    compile_st: data.steps_map?.compile_st ?? "idle",
    build_runtime: data.steps_map?.build_runtime ?? "idle",
    apply_io: data.steps_map?.apply_io ?? "idle",
    start_runtime: data.steps_map?.start_runtime ?? "idle",
  };

  return (Object.keys(STEP_LABELS) as RuntimeStepKey[]).map((key) => ({
    key,
    label: STEP_LABELS[key],
    status: statusByKey[key],
    detail: data.step_messages?.[key] ?? (statusByKey[key] === "success" ? `${STEP_LABELS[key]} completed` : `${STEP_LABELS[key]} pending or blocked`),
  }));
};

const deriveDiagnostics = (data: RuntimeValidationPanelData): RuntimeFailureDiagnostic[] => {
  const errors = data.errors ?? [];
  return errors.map((message) => ({
    step: "build_runtime",
    severity: "error",
    message,
    detail: null,
  }));
};

const runtimeStateToPanelStatus = (state: RuntimeValidationPanelData["runtime_state"]): PanelStatus => {
  if (state === "running") {
    return "success";
  }
  if (state === "stopped") {
    return "warning";
  }
  if (state === "failed") {
    return "failed";
  }
  return "idle";
};

export default function RuntimeValidationPanel({
  data,
  loading = false,
  actionLoading = false,
  failedMessage = null,
  onStart,
  onStop,
  requiredPreviousStep = "IO Mapping",
}: RuntimeValidationPanelProps) {
  const steps = useMemo<RuntimeStep[]>(() => (data ? buildSteps(data) : []), [data]);
  const diagnostics = useMemo<RuntimeFailureDiagnostic[]>(() => (data ? deriveDiagnostics(data) : []), [data]);
  const runtimeStatus = runtimeStateToPanelStatus(data?.runtime_state);
  const tags = data?.telemetry_tags ?? {};
  const tagEntries = Object.entries(tags);
  if (loading) {
    return <section className="runtime-validation-panel runtime-validation-state">Loading runtime control state...</section>;
  }

  if (failedMessage) {
    return (
      <section className="runtime-validation-panel runtime-validation-state error">
        <span>{failedMessage}</span>
      </section>
    );
  }

  if (!data) {
    return (
      <section className="runtime-validation-panel runtime-validation-state">
        <div>No runtime control results yet. Complete {requiredPreviousStep} first.</div>
      </section>
    );
  }

  return (
    <section className="runtime-validation-panel">
      <header className="runtime-validation-header">
        <div className="runtime-validation-title-row">
          <h3>Runtime Control</h3>
          <span className={`runtime-validation-status ${runtimeStatus}`}>
            {statusIcon(runtimeStatus)}
            {statusLabel(runtimeStatus)}
          </span>
        </div>
        <div className="runtime-validation-meta-grid">
          <span>Project: {data.active_project || data.project_id}</span>
          <span>Deployment: {formatTimestamp(data.deployed_at || data.validated_at)}</span>
          <span>State: {data.runtime_state || "idle"}</span>
        </div>
        <div className="runtime-control-actions">
          <button className="command-btn" onClick={onStart} type="button" disabled={!onStart || actionLoading}>Start</button>
          <button className="command-btn" onClick={onStop} type="button" disabled={!onStop || actionLoading}>Stop</button>
        </div>
      </header>

      <div className="runtime-validation-content">
        <article className="runtime-validation-card">
          <h4>Deployment Steps</h4>
          <ol className="runtime-validation-step-list">
            {steps.map((step) => (
              <li key={step.key} className={`runtime-validation-step ${step.status}`}>
                <div className={`runtime-validation-step-icon ${step.status}`}>{statusIcon(step.status)}</div>
                <div className="runtime-validation-step-body">
                  <div className="runtime-validation-step-row">
                    <strong>{step.label}</strong>
                    <span className={`runtime-validation-chip ${step.status}`}>{statusLabel(step.status)}</span>
                  </div>
                  <p>{step.detail}</p>
                </div>
              </li>
            ))}
          </ol>
        </article>

        <article className="runtime-validation-card">
          <h4>Telemetry</h4>
          {tagEntries.length > 0 ? (
            <div className="monitor-frame">
              <pre className="monitor-json">
                {tagEntries
                  .slice(0, 24)
                  .map(([key, value]) => `${key}: ${String(value)}`)
                  .join("\n")}
              </pre>
            </div>
          ) : (
            <div className="runtime-validation-empty">No runtime tags available. GET /runtime/tags is ready; WebSocket live stream can use /runtime/stream.</div>
          )}

          {diagnostics.length > 0 ? (
            <ul className="runtime-validation-diagnostics">
              {diagnostics.map((diagnostic, index) => (
                <li key={`${diagnostic.step}-${index}`}>
                  <span className={`runtime-validation-severity ${diagnostic.severity}`}>{diagnostic.severity.toUpperCase()}</span>
                  <div>
                    <strong>{STEP_LABELS[diagnostic.step]}</strong>
                    <p>{diagnostic.message}</p>
                  </div>
                </li>
              ))}
            </ul>
          ) : null}
        </article>
      </div>
    </section>
  );
}
