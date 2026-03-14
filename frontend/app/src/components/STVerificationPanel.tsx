import { useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronRight, FileWarning, XCircle } from "lucide-react";
import type { PanelStatus, STVerificationPanelResponse, VerificationSeverity } from "../services/api";
import "../styles/st-verification-panel.css";

export type STVerificationError = {
  file: string;
  message: string;
  severity: VerificationSeverity;
  line?: number | null;
  code?: string | null;
};

type ExtendedVerificationCheck = STVerificationPanelResponse["checks"][number] & {
  file?: string | null;
};

export type STVerificationPanelData = STVerificationPanelResponse & {
  parsed_file_count?: number;
  ast_validation_result?: "pass" | "fail" | "warning";
  errors?: STVerificationError[];
  checks?: ExtendedVerificationCheck[];
};

type STVerificationPanelProps = {
  data: STVerificationPanelData | null;
  loading?: boolean;
  failedMessage?: string | null;
  onRetry?: () => void;
  onSelectIssue?: (issue: STVerificationError) => void;
  requiredPreviousStep?: string;
};

type ErrorGroup = {
  file: string;
  items: STVerificationError[];
};

const statusLabel = (status: PanelStatus): string => {
  if (status === "success") {
    return "Pass";
  }
  if (status === "failed") {
    return "Fail";
  }
  if (status === "warning") {
    return "Warning";
  }
  if (status === "running") {
    return "Running";
  }
  return "Idle";
};

const statusIcon = (status: PanelStatus) => {
  if (status === "success") {
    return <CheckCircle2 size={14} />;
  }
  if (status === "failed") {
    return <XCircle size={14} />;
  }
  if (status === "warning") {
    return <AlertTriangle size={14} />;
  }
  return <FileWarning size={14} />;
};

const severityLabel = (severity: VerificationSeverity): string => {
  if (severity === "error") {
    return "Error";
  }
  if (severity === "warning") {
    return "Warning";
  }
  return "Info";
};

const toAstStatus = (result: STVerificationPanelData["ast_validation_result"], fallback: PanelStatus): PanelStatus => {
  if (result === "pass") {
    return "success";
  }
  if (result === "fail") {
    return "failed";
  }
  if (result === "warning") {
    return "warning";
  }
  return fallback;
};

const formatTimestamp = (value: string): string => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
};

const deriveErrorsFromChecks = (checks: ExtendedVerificationCheck[]): STVerificationError[] =>
  checks
    .filter((check) => check.severity !== "info" || check.status === "failed")
    .map((check) => ({
      file: check.file || "main.st",
      message: check.message,
      severity: check.severity,
      line: check.line_number,
      code: check.check_name,
    }));

export default function STVerificationPanel({
  data,
  loading = false,
  failedMessage = null,
  onRetry,
  onSelectIssue,
  requiredPreviousStep = "ST Generation",
}: STVerificationPanelProps) {
  const [expandedFiles, setExpandedFiles] = useState<Record<string, boolean>>({});

  const verificationErrors = useMemo<STVerificationError[]>(() => {
    if (!data) {
      return [];
    }
    if (data.errors && data.errors.length > 0) {
      return data.errors;
    }
    return deriveErrorsFromChecks((data.checks as ExtendedVerificationCheck[]) ?? []);
  }, [data]);

  const groupedErrors = useMemo<ErrorGroup[]>(() => {
    const grouped = new Map<string, STVerificationError[]>();
    for (const error of verificationErrors) {
      const file = error.file || "main.st";
      const existing = grouped.get(file) ?? [];
      grouped.set(file, [...existing, error]);
    }
    return [...grouped.entries()]
      .map(([file, items]) => ({ file, items }))
      .sort((left, right) => left.file.localeCompare(right.file));
  }, [verificationErrors]);

  const parsedFileCount = useMemo<number>(() => {
    if (!data) {
      return 0;
    }
    if (typeof data.parsed_file_count === "number") {
      return data.parsed_file_count;
    }
    if (groupedErrors.length > 0) {
      return groupedErrors.length;
    }
    return Math.max(1, data.checks_passed + data.checks_failed + data.checks_warning > 0 ? 1 : 0);
  }, [data, groupedErrors.length]);

  if (loading) {
    return <section className="st-verification-panel st-verification-state">Verifying Structured Text syntax...</section>;
  }

  if (failedMessage) {
    return (
      <section className="st-verification-panel st-verification-state st-verification-failed-state">
        <span>{failedMessage}</span>
        <button className="st-verification-retry-btn" onClick={onRetry} type="button" disabled={!onRetry}>
          Retry
        </button>
      </section>
    );
  }

  if (!data) {
    return <section className="st-verification-panel st-verification-state">No verification results available yet. Complete {requiredPreviousStep} first.</section>;
  }

  const astStatus = toAstStatus(data.ast_validation_result, data.overall_status);

  return (
    <section className="st-verification-panel">
      <header className="st-verification-header">
        <div className="st-verification-title-row">
          <h3>ST Verification</h3>
          <span className={`st-verification-status ${data.overall_status}`}>
            {statusIcon(data.overall_status)}
            {statusLabel(data.overall_status)}
          </span>
        </div>

        <div className="st-verification-meta-grid">
          <span>Parsed Files: {parsedFileCount}</span>
          <span className={`st-verification-ast ${astStatus}`}>AST: {statusLabel(astStatus)}</span>
          <span>Verified: {formatTimestamp(data.verified_at)}</span>
          <span>
            Checks: {data.checks_passed} pass / {data.checks_warning} warn / {data.checks_failed} fail
          </span>
        </div>
      </header>

      {data.overall_status === "warning" ? (
        <div className="st-verification-warning">Verification warnings detected. Review issues below; workspace remains usable.</div>
      ) : null}

      <div className="st-verification-content">
        <article className="st-verification-card">
          <h4>Error Groups by File</h4>
          {groupedErrors.length > 0 ? (
            <ul className="st-verification-file-list">
              {groupedErrors.map((group) => {
                const expanded = expandedFiles[group.file] ?? true;
                return (
                  <li key={group.file}>
                    <button
                      className="st-verification-file-toggle"
                      onClick={() =>
                        setExpandedFiles((previous) => ({
                          ...previous,
                          [group.file]: !previous[group.file],
                        }))
                      }
                      type="button"
                    >
                      {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                      <span>{group.file}</span>
                      <span className="st-verification-count">{group.items.length}</span>
                    </button>

                    {expanded ? (
                      <ul className="st-verification-error-list">
                        {group.items.map((item, index) => (
                          <li key={`${group.file}-${item.code || "issue"}-${index}`}>
                            <span className={`st-verification-severity ${item.severity}`}>{severityLabel(item.severity)}</span>
                            <button
                              className="st-verification-message st-verification-issue-link"
                              onClick={() => onSelectIssue?.(item)}
                              type="button"
                              disabled={!onSelectIssue}
                            >
                              {item.message}
                            </button>
                            {item.line ? <span className="st-verification-line">L{item.line}</span> : null}
                            {item.code ? <span className="st-verification-code">{item.code}</span> : null}
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          ) : (
            <div className="st-verification-empty">No syntax errors detected (e.g. missing END_IF, malformed CASE, parse failure).</div>
          )}
        </article>
      </div>
    </section>
  );
}
