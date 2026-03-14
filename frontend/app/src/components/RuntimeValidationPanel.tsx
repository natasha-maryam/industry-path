import { useMemo } from "react";
import { AlertTriangle, CheckCircle2, LoaderCircle, PlayCircle, XCircle } from "lucide-react";
import type { PanelStatus, RuntimeValidationPanelResponse } from "../services/api";
import "../styles/runtime-validation-panel.css";

type RuntimeStepKey = "project_creation" | "st_import" | "io_binding" | "runtime_start" | "deployment_readiness";

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
  project_creation_status?: PanelStatus;
  st_import_status?: PanelStatus;
  io_binding_status?: PanelStatus;
  runtime_start_status?: PanelStatus;
  deployment_readiness_status?: PanelStatus;
  diagnostics?: RuntimeFailureDiagnostic[];
};

type RuntimeValidationPanelProps = {
  data: RuntimeValidationPanelData | null;
  loading?: boolean;
  failedMessage?: string | null;
  onRetry?: () => void;
  requiredPreviousStep?: string;
};

const STEP_LABELS: Record<RuntimeStepKey, string> = {
  project_creation: "Project Creation",
  st_import: "ST Import",
  io_binding: "IO Binding",
  runtime_start: "Runtime Start",
  deployment_readiness: "Deployment Readiness",
};

const normalizeText = (value: string): string => value.toLowerCase();

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

const inferStepStatusFromChecks = (data: RuntimeValidationPanelData, key: RuntimeStepKey): PanelStatus => {
  const checks = data.checks ?? [];

  if (key === "project_creation") {
    return data.project_id ? "success" : "failed";
  }

  if (key === "deployment_readiness") {
    return data.overall_status;
  }

  const predicates: Record<Exclude<RuntimeStepKey, "project_creation" | "deployment_readiness">, (name: string) => boolean> = {
    st_import: (name) => name.includes("st") && (name.includes("import") || name.includes("load")),
    io_binding: (name) => name.includes("io") && (name.includes("binding") || name.includes("map")),
    runtime_start: (name) => name.includes("runtime") || name.includes("openplc") || name.includes("start"),
  };

  const predicate = predicates[key as Exclude<RuntimeStepKey, "project_creation" | "deployment_readiness">];
  const matching = checks.filter((check) => predicate(normalizeText(check.check_name)));

  if (matching.length === 0) {
    return "idle";
  }
  if (matching.some((check) => check.status === "failed")) {
    return "failed";
  }
  if (matching.some((check) => check.status === "warning")) {
    return "warning";
  }
  if (matching.some((check) => check.status === "running")) {
    return "running";
  }
  if (matching.every((check) => check.status === "success")) {
    return "success";
  }
  return "idle";
};

const buildSteps = (data: RuntimeValidationPanelData): RuntimeStep[] => {
  const statusByKey: Record<RuntimeStepKey, PanelStatus> = {
    project_creation: data.project_creation_status ?? inferStepStatusFromChecks(data, "project_creation"),
    st_import: data.st_import_status ?? inferStepStatusFromChecks(data, "st_import"),
    io_binding: data.io_binding_status ?? inferStepStatusFromChecks(data, "io_binding"),
    runtime_start: data.runtime_start_status ?? inferStepStatusFromChecks(data, "runtime_start"),
    deployment_readiness: data.deployment_readiness_status ?? inferStepStatusFromChecks(data, "deployment_readiness"),
  };

  return (Object.keys(STEP_LABELS) as RuntimeStepKey[]).map((key) => ({
    key,
    label: STEP_LABELS[key],
    status: statusByKey[key],
    detail: statusByKey[key] === "success" ? `${STEP_LABELS[key]} completed` : `${STEP_LABELS[key]} pending or blocked`,
  }));
};

const deriveDiagnostics = (data: RuntimeValidationPanelData): RuntimeFailureDiagnostic[] => {
  if (data.diagnostics && data.diagnostics.length > 0) {
    return data.diagnostics;
  }

  const fromChecks: RuntimeFailureDiagnostic[] = data.checks
    .filter((check) => check.status === "failed" || check.status === "warning")
    .map((check) => {
      const checkName = normalizeText(check.check_name);
      const step: RuntimeStepKey = checkName.includes("io")
        ? "io_binding"
        : checkName.includes("st")
          ? "st_import"
          : checkName.includes("runtime") || checkName.includes("openplc") || checkName.includes("start")
            ? "runtime_start"
            : "deployment_readiness";

      return {
        step,
        severity: check.status === "failed" ? "error" : "warning",
        message: check.message,
        detail: `Expected: ${check.expected_value} | Actual: ${check.actual_value}${check.tolerance ? ` | Tolerance: ${check.tolerance}` : ""}`,
      };
    });

  if (fromChecks.length > 0) {
    return fromChecks;
  }

  if (data.overall_status === "failed") {
    return [
      {
        step: "deployment_readiness",
        severity: "error",
        message: "OpenPLC deployment readiness failed",
        detail: "One or more runtime checks did not pass.",
      },
    ];
  }

  return [];
};

export default function RuntimeValidationPanel({
  data,
  loading = false,
  failedMessage = null,
  onRetry,
  requiredPreviousStep = "ST Verification + IO Mapping",
}: RuntimeValidationPanelProps) {
  const steps = useMemo<RuntimeStep[]>(() => (data ? buildSteps(data) : []), [data]);
  const diagnostics = useMemo<RuntimeFailureDiagnostic[]>(() => (data ? deriveDiagnostics(data) : []), [data]);

  if (loading) {
    return <section className="runtime-validation-panel runtime-validation-state">Validating runtime load into OpenPLC...</section>;
  }

  if (failedMessage) {
    return (
      <section className="runtime-validation-panel runtime-validation-state error">
        <span>{failedMessage}</span>
        <button className="runtime-validation-retry-btn" onClick={onRetry} type="button" disabled={!onRetry}>
          Retry
        </button>
      </section>
    );
  }

  if (!data) {
    return <section className="runtime-validation-panel runtime-validation-state">No runtime validation results yet. Complete {requiredPreviousStep} first.</section>;
  }

  return (
    <section className="runtime-validation-panel">
      <header className="runtime-validation-header">
        <div className="runtime-validation-title-row">
          <h3>Runtime Validation</h3>
          <span className={`runtime-validation-status ${data.overall_status}`}>
            {statusIcon(data.overall_status)}
            {statusLabel(data.overall_status)}
          </span>
        </div>
        <div className="runtime-validation-meta-grid">
          <span>Project: {data.project_id}</span>
          <span>Checked: {formatTimestamp(data.validated_at)}</span>
          <span>
            Checks: {data.checks_passed} pass / {data.checks_warning} warn / {data.checks_failed} fail
          </span>
        </div>
      </header>

      {data.overall_status === "warning" ? (
        <div className="runtime-validation-warning">Runtime validation completed with warnings. Review diagnostics; workspace remains available.</div>
      ) : null}

      <div className="runtime-validation-content">
        <article className="runtime-validation-card">
          <h4>OpenPLC Load Steps</h4>
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
          <h4>Failure Diagnostics</h4>
          {diagnostics.length > 0 ? (
            <ul className="runtime-validation-diagnostics">
              {diagnostics.map((diagnostic, index) => (
                <li key={`${diagnostic.step}-${index}`}>
                  <span className={`runtime-validation-severity ${diagnostic.severity}`}>{diagnostic.severity.toUpperCase()}</span>
                  <div>
                    <strong>{STEP_LABELS[diagnostic.step]}</strong>
                    <p>{diagnostic.message}</p>
                    {diagnostic.detail ? <small>{diagnostic.detail}</small> : null}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="runtime-validation-empty">No runtime failure diagnostics reported.</div>
          )}
        </article>
      </div>
    </section>
  );
}
