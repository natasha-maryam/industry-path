import type { VersionRecord } from "../../types/versioning";

type SnapshotManagerProps = {
  versions: VersionRecord[];
  selectedVersionTags: string[];
  busyAction: "snapshot" | "rollback" | "compare" | "export" | null;
  onCreateSnapshot: () => void;
  onToggleCompareSelection: (versionTag: string) => void;
  onLoadSnapshot: (version: VersionRecord) => void;
  onRollback: (version: VersionRecord) => void;
  onCompare: () => void;
  onExport: (version: VersionRecord) => void;
};

export default function SnapshotManager({
  versions,
  selectedVersionTags,
  busyAction,
  onCreateSnapshot,
  onToggleCompareSelection,
  onLoadSnapshot,
  onRollback,
  onCompare,
  onExport,
}: SnapshotManagerProps) {
  return (
    <section className="snapshot-manager">
      <div className="snapshot-manager-head">
        <h4>Snapshot Manager</h4>
        <button className="command-btn primary" type="button" disabled={busyAction === "snapshot"} onClick={onCreateSnapshot}>
          {busyAction === "snapshot" ? "Creating…" : "Create Snapshot"}
        </button>
      </div>

      <div className="snapshot-list">
        {versions.map((version) => {
          const selected = selectedVersionTags.includes(version.version_tag);
          return (
            <div key={version.id || version.version_tag} className="snapshot-row">
              <label className="snapshot-select">
                <input
                  type="checkbox"
                  checked={selected}
                  onChange={() => onToggleCompareSelection(version.version_tag)}
                />
                <span>{version.version_tag}</span>
              </label>
              <div className="snapshot-row-actions">
                <button className="command-btn" type="button" onClick={() => onLoadSnapshot(version)}>Load Snapshot</button>
                <button className="command-btn" type="button" onClick={() => onToggleCompareSelection(version.version_tag)}>
                  Compare
                </button>
                <button
                  className="command-btn"
                  type="button"
                  disabled={!version.rollback_available || busyAction === "rollback"}
                  onClick={() => onRollback(version)}
                >
                  Rollback
                </button>
                <button className="command-btn" type="button" onClick={() => onExport(version)}>Export</button>
              </div>
            </div>
          );
        })}
      </div>

      <div className="snapshot-compare-bar">
        <button
          className="command-btn"
          type="button"
          disabled={selectedVersionTags.length !== 2 || busyAction === "compare"}
          onClick={onCompare}
        >
          {busyAction === "compare" ? "Comparing…" : "Compare Selected Versions"}
        </button>
        {selectedVersionTags.length !== 2 ? <span>Select exactly 2 versions to compare.</span> : null}
      </div>
    </section>
  );
}
