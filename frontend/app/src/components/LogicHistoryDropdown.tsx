import { useEffect, useMemo, useRef, useState } from "react";
import { ChevronDown, History } from "lucide-react";
import type { LogicSnapshot } from "../utils/logicSnapshots";

type LogicHistoryDropdownProps = {
  snapshots: LogicSnapshot[];
  lastSavedLabel: string;
  previewSnapshotId: string | null;
  onPreviewSnapshot: (snapshot: LogicSnapshot) => void;
  onRestoreSnapshot: (snapshot: LogicSnapshot) => void;
  onExitPreview: () => void;
};

function formatTimestamp(value: string): string {
  const timestamp = new Date(value);
  if (Number.isNaN(timestamp.getTime())) {
    return value;
  }
  return timestamp.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function LogicHistoryDropdown({
  snapshots,
  lastSavedLabel,
  previewSnapshotId,
  onPreviewSnapshot,
  onRestoreSnapshot,
  onExitPreview,
}: LogicHistoryDropdownProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }
    const handlePointerDown = (event: MouseEvent): void => {
      if (containerRef.current && event.target instanceof Node && !containerRef.current.contains(event.target)) {
        setOpen(false);
      }
    };
    const handleEscape = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handlePointerDown, true);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown, true);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [open]);

  const previewingSnapshot = useMemo(
    () => snapshots.find((snapshot) => snapshot.id === previewSnapshotId) ?? null,
    [previewSnapshotId, snapshots]
  );

  return (
    <div className="logic-history-toolbar" ref={containerRef}>
      <span className="logic-history-save-indicator">Last saved {lastSavedLabel}</span>
      <button
        className="command-btn logic-history-trigger"
        type="button"
        onClick={() => setOpen((current) => !current)}
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <History size={13} />
        <span>View History</span>
        <ChevronDown size={13} />
      </button>
      {open ? (
        <div className="logic-history-dropdown" role="menu">
          <div className="logic-history-dropdown-head">
            <div>
              <strong>Logic History</strong>
              <span>{snapshots.length} recent version{snapshots.length === 1 ? "" : "s"}</span>
            </div>
            {previewingSnapshot ? (
              <button className="command-btn" type="button" onClick={onExitPreview}>
                Return to Current
              </button>
            ) : null}
          </div>

          <div className="logic-history-dropdown-list">
            {snapshots.length > 0 ? (
              snapshots.map((snapshot) => {
                const isPreviewing = previewSnapshotId === snapshot.id;
                return (
                  <div key={snapshot.id} className={`logic-history-dropdown-item${isPreviewing ? " is-previewing" : ""}`} role="menuitem">
                    <div className="logic-history-dropdown-copy">
                      <strong>{snapshot.label}</strong>
                      <span>{formatTimestamp(snapshot.createdAt)}</span>
                    </div>
                    <div className="logic-history-dropdown-actions">
                      <button className="command-btn" type="button" onClick={() => onPreviewSnapshot(snapshot)}>
                        {isPreviewing ? "Previewing" : "Preview"}
                      </button>
                      <button className="command-btn" type="button" onClick={() => onRestoreSnapshot(snapshot)}>
                        Restore
                      </button>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="logic-history-dropdown-empty">No logic snapshots yet.</div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
