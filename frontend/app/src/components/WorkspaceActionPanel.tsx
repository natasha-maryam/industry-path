import type { ReactNode } from "react";

type WorkspaceActionPanelProps = {
  eyebrow?: string;
  title: string;
  description: string;
  secondaryActions?: ReactNode;
  actionLabel?: string;
  onAction?: () => void;
  actionDisabled?: boolean;
  actionLoading?: boolean;
  progressLines?: string[];
  children?: ReactNode;
};

export default function WorkspaceActionPanel({
  eyebrow,
  title,
  description,
  secondaryActions,
  actionLabel,
  onAction,
  actionDisabled = false,
  actionLoading = false,
  progressLines = [],
  children,
}: WorkspaceActionPanelProps) {
  return (
    <section className="workspace-action-panel">
      <div className="workspace-action-panel-header">
        <div>
          {eyebrow ? <p className="workspace-action-panel-eyebrow">{eyebrow}</p> : null}
          <h3>{title}</h3>
        </div>
        {secondaryActions || (actionLabel && onAction) ? (
          <div className="workspace-action-panel-actions">
            {secondaryActions ? <div className="workspace-action-panel-secondary-actions">{secondaryActions}</div> : null}
            {actionLabel && onAction ? (
              <button className="command-btn primary workspace-action-panel-trigger" type="button" onClick={onAction} disabled={actionDisabled || actionLoading}>
                {actionLoading ? <span className="btn-loader" aria-hidden="true" /> : null}
                {actionLabel}
              </button>
            ) : null}
          </div>
        ) : null}
      </div>
      <p className="workspace-action-panel-description">{description}</p>
      {progressLines.length > 0 ? (
        <div className="workspace-action-panel-progress" aria-live="polite" role="status">
          {progressLines.map((line) => (
            <div key={line} className="workspace-action-panel-progress-line">
              {line}
            </div>
          ))}
        </div>
      ) : null}
      {children ? <div className="workspace-action-panel-body">{children}</div> : null}
    </section>
  );
}