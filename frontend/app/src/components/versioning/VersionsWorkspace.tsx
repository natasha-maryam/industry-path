import { useMemo } from "react";
import type { PIDReconcileSummary } from "../../services/api";
import RightPIDChangesTab from "../rightTabs/RightPIDChangesTab";
import type { VersionDiffResponse, VersionRecord } from "../../types/versioning";
import LogicDiffViewer from "./LogicDiffViewer";
import SnapshotManager from "./SnapshotManager";
import VersionDetailsCard from "./VersionDetailsCard";
import VersionHistoryPanel from "./VersionHistoryPanel";

export type VersionsWorkspaceSection = "history" | "pid";

type VersioningSettings = {
  enableAutoVersioning: boolean;
  autoSnapshotOnDeploy: boolean;
  enableDatabaseVersioning: boolean;
  maxSnapshotsStored: number;
  snapshotRetentionDays: number;
  gitRepositoryLocation: string;
};

type VersionsWorkspaceProps = {
  activeSection: VersionsWorkspaceSection;
  versions: VersionRecord[];
  selectedVersion: VersionRecord | null;
  selectedVersionTags: string[];
  diff: VersionDiffResponse | null;
  loading: boolean;
  errorMessage: string | null;
  busyAction: "snapshot" | "rollback" | "compare" | "export" | null;
  settings: VersioningSettings;
  pidChanges: PIDReconcileSummary | null;
  pidChangesLoading: boolean;
  pidChangesError: string | null;
  pidApplying: boolean;
  pidSnapshotCreating: boolean;
  pidAcceptedConflicts: boolean;
  onSelectVersion: (version: VersionRecord) => void;
  onToggleCompareSelection: (versionTag: string) => void;
  onCreateSnapshot: () => void;
  onLoadSnapshot: (version: VersionRecord) => void;
  onRollback: (version: VersionRecord) => void;
  onCompare: () => void;
  onExport: (version: VersionRecord) => void;
  onSettingsChange: (settings: VersioningSettings) => void;
  onRefreshPIDChanges: () => void;
  onPIDAcceptChanges: () => void;
  onPIDReviewConflicts: () => void;
  onPIDApplyUpdate: () => void;
  onPIDCreateSnapshot: () => void;
};

export default function VersionsWorkspace({
  activeSection,
  versions,
  selectedVersion,
  selectedVersionTags,
  diff,
  loading,
  errorMessage,
  busyAction,
  settings,
  pidChanges,
  pidChangesLoading,
  pidChangesError,
  pidApplying,
  pidSnapshotCreating,
  pidAcceptedConflicts,
  onSelectVersion,
  onToggleCompareSelection,
  onCreateSnapshot,
  onLoadSnapshot,
  onRollback,
  onCompare,
  onExport,
  onSettingsChange,
  onRefreshPIDChanges,
  onPIDAcceptChanges,
  onPIDReviewConflicts,
  onPIDApplyUpdate,
  onPIDCreateSnapshot,
}: VersionsWorkspaceProps) {
  const selectedCountLabel = useMemo(() => {
    if (selectedVersionTags.length === 0) {
      return "No compare selection";
    }
    return `Compare selection: ${selectedVersionTags.join(" vs ")}`;
  }, [selectedVersionTags]);

  const pidSummary = useMemo(
    () => [
      { label: "New devices", value: pidChanges?.new_devices.length ?? 0 },
      { label: "Connection changes", value: pidChanges?.topology_changes.length ?? 0 },
      { label: "Deprecated devices", value: pidChanges?.deprecated_devices.length ?? 0 },
      { label: "Possible conflicts", value: pidChanges?.possible_conflicts.length ?? 0 },
    ],
    [pidChanges]
  );

  if (activeSection === "pid") {
    return (
      <section className="versions-workspace versions-workspace-pid">
        <div className="versions-grid-left">
          <section className="snapshot-manager versions-summary-panel">
            <div className="snapshot-manager-head">
              <h4>P&ID Reconciliation</h4>
              <button className="command-btn" type="button" disabled={pidChangesLoading} onClick={onRefreshPIDChanges}>
                {pidChangesLoading ? "Refreshing…" : "Refresh"}
              </button>
            </div>

            <div className="versions-summary-grid">
              {pidSummary.map((item) => (
                <article key={item.label} className="versions-summary-card">
                  <span className="versions-summary-label">{item.label}</span>
                  <strong className="versions-summary-value">{item.value}</strong>
                </article>
              ))}
            </div>

            <div className="version-summary-stack">
              <div className="version-summary-meta-row">
                <span>Apply ready</span>
                <strong>{pidChanges?.apply_ready ? "Yes" : "No"}</strong>
              </div>
              <div className="version-summary-meta-row">
                <span>Similarity threshold</span>
                <strong>{pidChanges?.similarity_threshold ?? "-"}</strong>
              </div>
              <div className="version-summary-meta-row">
                <span>Generated at</span>
                <strong>{pidChanges?.generated_at ? new Date(pidChanges.generated_at).toLocaleString() : "Not available"}</strong>
              </div>
            </div>

            <p className="modal-help-text versions-summary-copy">
              Review extracted P&ID reconciliation output here before applying graph updates or creating a new snapshot.
            </p>
          </section>
        </div>

        <div className="versions-grid-center">
          <RightPIDChangesTab
            changes={pidChanges}
            loading={pidChangesLoading}
            error={pidChangesError}
            applying={pidApplying}
            creatingSnapshot={pidSnapshotCreating}
            acceptedConflicts={pidAcceptedConflicts}
            onAcceptChanges={onPIDAcceptChanges}
            onReviewConflicts={onPIDReviewConflicts}
            onApplyUpdate={onPIDApplyUpdate}
            onCreateSnapshot={onPIDCreateSnapshot}
          />
        </div>
      </section>
    );
  }

  return (
    <section className="versions-workspace">
      <div className="versions-grid-left">
        <h4>Version History</h4>
        <VersionHistoryPanel
          versions={versions}
          selectedVersionTag={selectedVersion?.version_tag ?? null}
          loading={loading}
          errorMessage={errorMessage}
          onSelectVersion={onSelectVersion}
        />
      </div>

      <div className="versions-grid-center">
        <VersionDetailsCard version={selectedVersion} />
        <div className="version-compare-selection">{selectedCountLabel}</div>
        <SnapshotManager
          versions={versions}
          selectedVersionTags={selectedVersionTags}
          busyAction={busyAction}
          onCreateSnapshot={onCreateSnapshot}
          onToggleCompareSelection={onToggleCompareSelection}
          onLoadSnapshot={onLoadSnapshot}
          onRollback={onRollback}
          onCompare={onCompare}
          onExport={onExport}
        />

        <section className="version-settings-card">
          <h4>Versioning Settings</h4>
          <label className="settings-line"><span>Enable Auto Versioning</span><input type="checkbox" checked={settings.enableAutoVersioning} onChange={(event) => onSettingsChange({ ...settings, enableAutoVersioning: event.target.checked })} /></label>
          <label className="settings-line"><span>Auto Snapshot on Deploy</span><input type="checkbox" checked={settings.autoSnapshotOnDeploy} onChange={(event) => onSettingsChange({ ...settings, autoSnapshotOnDeploy: event.target.checked })} /></label>
          <label className="settings-line"><span>Enable Database Versioning</span><input type="checkbox" checked={settings.enableDatabaseVersioning} onChange={(event) => onSettingsChange({ ...settings, enableDatabaseVersioning: event.target.checked })} /></label>
          <label className="settings-line"><span>Max Snapshots Stored</span><input type="number" min={1} value={settings.maxSnapshotsStored} onChange={(event) => onSettingsChange({ ...settings, maxSnapshotsStored: Math.max(1, Number(event.target.value) || 1) })} /></label>
          <label className="settings-line"><span>Snapshot Retention Days</span><input type="number" min={1} value={settings.snapshotRetentionDays} onChange={(event) => onSettingsChange({ ...settings, snapshotRetentionDays: Math.max(1, Number(event.target.value) || 1) })} /></label>
          <label className="settings-line"><span>Git Repository Location</span><input type="text" readOnly value={settings.gitRepositoryLocation} /></label>
        </section>
      </div>

      <div className="versions-grid-bottom">
        <LogicDiffViewer diff={diff} loading={busyAction === "compare"} />
      </div>
    </section>
  );
}
