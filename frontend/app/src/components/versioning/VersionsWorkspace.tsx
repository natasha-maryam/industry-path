import { useMemo } from "react";
import type { VersionDiffResponse, VersionRecord } from "../../types/versioning";
import LogicDiffViewer from "./LogicDiffViewer";
import SnapshotManager from "./SnapshotManager";
import VersionDetailsCard from "./VersionDetailsCard";
import VersionHistoryPanel from "./VersionHistoryPanel";

type VersioningSettings = {
  enableAutoVersioning: boolean;
  autoSnapshotOnDeploy: boolean;
  enableDatabaseVersioning: boolean;
  maxSnapshotsStored: number;
  snapshotRetentionDays: number;
  gitRepositoryLocation: string;
};

type VersionsWorkspaceProps = {
  versions: VersionRecord[];
  selectedVersion: VersionRecord | null;
  selectedVersionTags: string[];
  diff: VersionDiffResponse | null;
  loading: boolean;
  errorMessage: string | null;
  busyAction: "snapshot" | "rollback" | "compare" | "export" | null;
  settings: VersioningSettings;
  onSelectVersion: (version: VersionRecord) => void;
  onToggleCompareSelection: (versionTag: string) => void;
  onCreateSnapshot: () => void;
  onLoadSnapshot: (version: VersionRecord) => void;
  onRollback: (version: VersionRecord) => void;
  onCompare: () => void;
  onExport: (version: VersionRecord) => void;
  onSettingsChange: (settings: VersioningSettings) => void;
};

export default function VersionsWorkspace({
  versions,
  selectedVersion,
  selectedVersionTags,
  diff,
  loading,
  errorMessage,
  busyAction,
  settings,
  onSelectVersion,
  onToggleCompareSelection,
  onCreateSnapshot,
  onLoadSnapshot,
  onRollback,
  onCompare,
  onExport,
  onSettingsChange,
}: VersionsWorkspaceProps) {
  const selectedCountLabel = useMemo(() => {
    if (selectedVersionTags.length === 0) {
      return "No compare selection";
    }
    return `Compare selection: ${selectedVersionTags.join(" vs ")}`;
  }, [selectedVersionTags]);

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
