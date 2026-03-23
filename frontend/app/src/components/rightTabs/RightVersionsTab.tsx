type RightVersionsTabProps = {
  onOpenVersionsWorkspace?: () => void;
};

export default function RightVersionsTab({ onOpenVersionsWorkspace }: RightVersionsTabProps) {
  return (
    <section className="settings-grid">
      <div className="panel-subtitle">Versioning</div>
      <p className="modal-help-text">Open engineering version history, compare logic revisions, and execute controlled rollbacks.</p>
      <button className="command-btn primary" type="button" onClick={() => onOpenVersionsWorkspace?.()}>
        Open Versions Workspace
      </button>
    </section>
  );
}
