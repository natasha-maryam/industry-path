import type { PIDReconcileSummary } from "../../services/api";

type RightPIDChangesTabProps = {
  changes: PIDReconcileSummary | null;
  loading: boolean;
  error: string | null;
  applying: boolean;
  creatingSnapshot: boolean;
  onAcceptChanges: () => void;
  onReviewConflicts: () => void;
  onApplyUpdate: () => void;
  onCreateSnapshot: () => void;
  acceptedConflicts: boolean;
};

const Section = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <section className="snapshot-manager" style={{ marginBottom: "0.45rem" }}>
    <h4>{title}</h4>
    {children}
  </section>
);

export default function RightPIDChangesTab({
  changes,
  loading,
  error,
  applying,
  creatingSnapshot,
  onAcceptChanges,
  onReviewConflicts,
  onApplyUpdate,
  onCreateSnapshot,
  acceptedConflicts,
}: RightPIDChangesTabProps) {
  if (loading) {
    return <div className="monitor-frame">Loading P&ID changes…</div>;
  }

  if (error) {
    return <div className="monitor-frame">{error}</div>;
  }

  if (!changes) {
    return <div className="monitor-frame">No reconciliation data available for the active project.</div>;
  }

  return (
    <div>
      <Section title="New Devices">
        {changes.new_devices.length === 0 ? <div className="modal-help-text">No new devices.</div> : changes.new_devices.map((item) => <div key={item.tag} className="details-path-row"><strong>{item.tag}</strong><span>{item.details}</span></div>)}
      </Section>

      <Section title="Modified Connections">
        {changes.topology_changes.length === 0 ? <div className="modal-help-text">No topology changes.</div> : changes.topology_changes.map((item) => <div key={`${item.edge_id}-${item.change}`} className="details-path-row"><strong>{item.change.toUpperCase()}</strong><span>{item.source} -[{item.edge_type}]-&gt; {item.target}</span></div>)}
      </Section>

      <Section title="Deprecated Devices">
        {changes.deprecated_devices.length === 0 ? <div className="modal-help-text">No deprecated devices.</div> : changes.deprecated_devices.map((item) => <div key={item.tag} className="details-path-row"><strong>{item.tag}</strong><span>{item.details}</span></div>)}
      </Section>

      <Section title="Possible Tag Conflicts">
        {changes.possible_conflicts.length === 0 ? <div className="modal-help-text">No possible conflicts.</div> : changes.possible_conflicts.map((item, index) => <div key={`${item.incoming_tag}-${item.existing_tag}-${index}`} className="details-path-row"><strong>{item.incoming_tag}</strong><span>{item.reason}: {item.existing_tag} ({item.similarity.toFixed(2)})</span></div>)}
      </Section>

      <div className="modal-actions" style={{ justifyContent: "flex-start", flexWrap: "wrap" }}>
        <button className="command-btn" type="button" onClick={onAcceptChanges}>{acceptedConflicts ? "Accepted" : "Accept Changes"}</button>
        <button className="command-btn" type="button" onClick={onReviewConflicts}>Review Conflicts</button>
        <button className="command-btn primary" type="button" disabled={applying} onClick={onApplyUpdate}>{applying ? "Applying…" : "Apply Update"}</button>
        <button className="command-btn" type="button" disabled={creatingSnapshot} onClick={onCreateSnapshot}>{creatingSnapshot ? "Creating…" : "Create Version Snapshot"}</button>
      </div>
    </div>
  );
}
