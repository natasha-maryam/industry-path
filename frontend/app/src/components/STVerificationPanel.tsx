import { useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronRight, FileWarning, XCircle } from "lucide-react";
import type { STWorkspaceVerificationResponse } from "../services/api";
import "../styles/st-verification-panel.css";

export type STVerificationIssueItem = {
  file: string;
  message: string;
  severity: "warning" | "error";
  line?: number | null;
  column?: number | null;
  code?: string | null;
};

type STVerificationPanelProps = {
  data: STWorkspaceVerificationResponse | null;
  loading?: boolean;
  failedMessage?: string | null;
  onRetry?: () => void;
  onSelectIssue?: (issue: STVerificationIssueItem) => void;
  requiredPreviousStep?: string;
};

type ErrorGroup = {
  file: string;
  status: "passed" | "warnings" | "failed";
  items: STVerificationIssueItem[];
};

const statusLabel = (status: STWorkspaceVerificationResponse["status"]): string => {
  if (status === "passed") {
    return "Passed";
  }
  if (status === "passed_with_warnings") {
    return "Passed with Warnings";
  }
  if (status === "failed") {
    return "Failed";
  }
  return "Failed";
};

const statusIcon = (status: STWorkspaceVerificationResponse["status"]) => {
  if (status === "passed") {
    return <CheckCircle2 size={14} />;
  }
  if (status === "failed") {
    return <XCircle size={14} />;
  }
  if (status === "passed_with_warnings") {
    return <AlertTriangle size={14} />;
  }
  return <FileWarning size={14} />;
};

const severityLabel = (severity: "warning" | "error"): string => {
  if (severity === "error") {
    return "Error";
  }
  return "Warning";
};

const formatTimestamp = (value: string): string => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
};

export default function STVerificationPanel({
  data,
  loading = false,
  failedMessage = null,
  onRetry,
  onSelectIssue,
  requiredPreviousStep = "ST Generation",
}: STVerificationPanelProps) {
  const [expandedFiles, setExpandedFiles] = useState<Record<string, boolean>>({});

  const groupedErrors = useMemo<ErrorGroup[]>(() => {
    if (!data) {
      return [];
    }
    return data.files
      .map((fileResult) => {
        const errors: STVerificationIssueItem[] = fileResult.errors.map((item) => ({
          file: fileResult.file,
          message: item.message,
          severity: "error",
          line: item.line,
          column: item.column,
          code: item.code,
        }));
        const warnings: STVerificationIssueItem[] = fileResult.warnings.map((item) => ({
          file: fileResult.file,
          message: item.message,
          severity: "warning",
          line: item.line,
          column: item.column,
          code: item.code,
        }));
        return {
          file: fileResult.file,
          status: fileResult.status,
          items: [...errors, ...warnings],
        };
      })
      .sort((left, right) => left.file.localeCompare(right.file));
  }, [data]);

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

  return (
    <section className="st-verification-panel">
      <header className="st-verification-header">
        <div className="st-verification-title-row">
          <h3>ST Verification</h3>
          <span className={`st-verification-status ${data.status === "passed" ? "success" : data.status === "failed" ? "failed" : "warning"}`}>
            {statusIcon(data.status)}
            {statusLabel(data.status)}
          </span>
        </div>

        <div className="st-verification-meta-grid">
          <span>Files Checked: {data.summary.files_checked}</span>
          <span>Errors: {data.summary.error_count}</span>
          <span>Warnings: {data.summary.warning_count}</span>
          <span>Verified: {formatTimestamp(new Date().toISOString())}</span>
        </div>
      </header>

      {data.status === "passed_with_warnings" ? (
        <div className="st-verification-warning">Verification warnings detected. Review issues below; workspace remains usable.</div>
      ) : null}

      <div className="st-verification-content">
        <article className="st-verification-card">
          <h4>Diagnostics by File</h4>
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
                      <span className={`st-verification-file-status ${group.status}`}>{group.status}</span>
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
                            {item.line ? <span className="st-verification-line">L{item.line}{item.column ? `:C${item.column}` : ""}</span> : null}
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
            <div className="st-verification-empty">No diagnostics detected. Workspace verification passed.</div>
          )}
        </article>
      </div>
    </section>
  );
}
