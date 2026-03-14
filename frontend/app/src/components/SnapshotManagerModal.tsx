import { Download, GitCompare, LoaderCircle, RotateCcw, Upload } from "lucide-react";

export type SnapshotTriggerSource = "manual" | "auto_validation" | "deployment" | "simulation" | "schedule";

export type SnapshotRecord = {
  id: string;
  name: string;
  trigger_source: SnapshotTriggerSource;
  timestamp: string;
};

type SnapshotManagerModalProps = {
  open: boolean;
  snapshots: SnapshotRecord[];
  loading?: boolean;
  errorMessage?: string | null;
  onClose: () => void;
  onRetry?: () => void;
  onLoadSnapshot?: (snapshot: SnapshotRecord) => void;
  onRollback?: (snapshot: SnapshotRecord) => void;
  onCompare?: (snapshot: SnapshotRecord) => void;
  onExport?: (snapshot: SnapshotRecord) => void;
};

const triggerSourceLabel = (source: SnapshotTriggerSource): string => {
  if (source === "manual") {
    return "Manual";
  }
  if (source === "auto_validation") {
    return "Auto Validation";
  }
  if (source === "deployment") {
    return "Deployment";
  }
  if (source === "simulation") {
    return "Simulation";
  }
  return "Scheduled";
};

const formatTimestamp = (value: string): string => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
};

export default function SnapshotManagerModal({
  open,
  snapshots,
  loading = false,
  errorMessage = null,
  onClose,
  onRetry,
  onLoadSnapshot,
  onRollback,
  onCompare,
  onExport,
}: SnapshotManagerModalProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card snapshot-modal" onClick={(event) => event.stopPropagation()}>
        <div className="snapshot-modal-header">
          <h3>Snapshot Manager</h3>
          <button className="command-btn" onClick={onClose} type="button">
            Close
          </button>
        </div>

        {loading ? (
          <div className="snapshot-modal-state">
            <LoaderCircle size={14} className="activity-spinner" />
            Loading snapshots...
          </div>
        ) : errorMessage ? (
          <div className="snapshot-modal-state error">
            <span>{errorMessage}</span>
            {onRetry ? (
              <button className="command-btn" onClick={onRetry} type="button">
                Retry
              </button>
            ) : null}
          </div>
        ) : snapshots.length === 0 ? (
          <div className="snapshot-modal-state">No snapshots available for this project.</div>
        ) : (
          <div className="snapshot-table-wrap">
            <table className="snapshot-table">
              <thead>
                <tr>
                  <th>Snapshot Name</th>
                  <th>Trigger Source</th>
                  <th>Timestamp</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {snapshots.map((snapshot) => (
                  <tr key={snapshot.id}>
                    <td>{snapshot.name}</td>
                    <td>
                      <span className="snapshot-trigger-chip">{triggerSourceLabel(snapshot.trigger_source)}</span>
                    </td>
                    <td className="value-mono">{formatTimestamp(snapshot.timestamp)}</td>
                    <td>
                      <div className="snapshot-actions">
                        <button className="command-btn" onClick={() => onLoadSnapshot?.(snapshot)} type="button">
                          <Upload size={12} />
                          Load Snapshot
                        </button>
                        <button className="command-btn" onClick={() => onRollback?.(snapshot)} type="button">
                          <RotateCcw size={12} />
                          Rollback
                        </button>
                        <button className="command-btn" onClick={() => onCompare?.(snapshot)} type="button">
                          <GitCompare size={12} />
                          Compare
                        </button>
                        <button className="command-btn" onClick={() => onExport?.(snapshot)} type="button">
                          <Download size={12} />
                          Export
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
