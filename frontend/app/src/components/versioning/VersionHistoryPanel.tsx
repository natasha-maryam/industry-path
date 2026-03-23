import type { VersionRecord } from "../../types/versioning";

type VersionHistoryPanelProps = {
  versions: VersionRecord[];
  selectedVersionTag: string | null;
  loading: boolean;
  errorMessage: string | null;
  onSelectVersion: (version: VersionRecord) => void;
};

const STATUS_LABEL: Record<"available" | "missing" | "unknown", string> = {
  available: "OK",
  missing: "Missing",
  unknown: "Unknown",
};

const formatDate = (value: string): string => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
};

const artifactBadgeClass = (status: "available" | "missing" | "unknown"): string =>
  status === "available" ? "artifact-badge available" : status === "missing" ? "artifact-badge missing" : "artifact-badge unknown";

export default function VersionHistoryPanel({
  versions,
  selectedVersionTag,
  loading,
  errorMessage,
  onSelectVersion,
}: VersionHistoryPanelProps) {
  if (loading) {
    return <div className="monitor-frame">Loading version history…</div>;
  }

  if (errorMessage) {
    return <div className="monitor-frame versioning-error">{errorMessage}</div>;
  }

  if (versions.length === 0) {
    return (
      <div className="monitor-frame">
        No versions created yet. Versions will appear after logic generation, simulation, deployment, or manual snapshot creation.
      </div>
    );
  }

  return (
    <section className="version-history-panel">
      {versions.map((version) => {
        const selected = version.version_tag === selectedVersionTag;
        return (
          <button
            key={version.id || version.version_tag}
            type="button"
            className={`version-row ${selected ? "selected" : ""}`}
            onClick={() => onSelectVersion(version)}
          >
            <div className="version-row-head">
              <span className="version-tag-pill">{version.version_tag}</span>
              <span className="version-trigger">{version.trigger_source}</span>
            </div>
            <div className="version-summary">{version.summary || "No summary"}</div>
            <div className="version-meta-row">
              <span className="value-mono">{formatDate(version.created_at)}</span>
              <span className="value-mono">{version.commit_hash.slice(0, 12)}</span>
            </div>
            <div className="version-artifact-badges">
              <span className={artifactBadgeClass(version.artifact_status.plant_graph)}>Plant {STATUS_LABEL[version.artifact_status.plant_graph]}</span>
              <span className={artifactBadgeClass(version.artifact_status.control_logic)}>Logic {STATUS_LABEL[version.artifact_status.control_logic]}</span>
              <span className={artifactBadgeClass(version.artifact_status.io_mapping)}>IO {STATUS_LABEL[version.artifact_status.io_mapping]}</span>
              <span className={artifactBadgeClass(version.artifact_status.simulation)}>Sim {STATUS_LABEL[version.artifact_status.simulation]}</span>
              <span className={artifactBadgeClass(version.artifact_status.runtime)}>Runtime {STATUS_LABEL[version.artifact_status.runtime]}</span>
            </div>
          </button>
        );
      })}
    </section>
  );
}
