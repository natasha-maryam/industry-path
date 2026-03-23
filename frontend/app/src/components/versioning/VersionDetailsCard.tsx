import type { VersionRecord } from "../../types/versioning";

type VersionDetailsCardProps = {
  version: VersionRecord | null;
};

const renderPath = (label: string, value: string | null | undefined) => (
  <div className="details-path-row">
    <strong>{label}</strong>
    <span className="value-mono">{value || "N/A"}</span>
  </div>
);

export default function VersionDetailsCard({ version }: VersionDetailsCardProps) {
  if (!version) {
    return <div className="monitor-frame">Select a version to inspect details.</div>;
  }

  return (
    <section className="version-details-card">
      <div className="details-grid">
        <div><strong>Version</strong><span>{version.version_tag}</span></div>
        <div><strong>Trigger</strong><span>{version.trigger_source}</span></div>
        <div><strong>Created By</strong><span>{version.created_by || "system"}</span></div>
        <div><strong>Created At</strong><span className="value-mono">{new Date(version.created_at).toLocaleString()}</span></div>
        <div><strong>Commit Hash</strong><span className="value-mono">{version.commit_hash}</span></div>
        <div><strong>Deployment Tag</strong><span>{version.deployment_tag || "N/A"}</span></div>
        <div><strong>Rollback</strong><span>{version.rollback_available ? "Available" : "Disabled"}</span></div>
      </div>
      <div className="version-summary-block">
        <strong>Summary</strong>
        <p>{version.summary || "No summary"}</p>
      </div>
      <div className="version-paths-grid">
        {renderPath("Plant Graph", version.plant_graph_path)}
        {renderPath("Control Logic", version.logic_path)}
        {renderPath("IO Mapping", version.io_mapping_path)}
        {renderPath("Simulation", version.simulation_results_path)}
        {renderPath("Runtime", version.runtime_state_path)}
      </div>
    </section>
  );
}
