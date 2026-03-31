/**
 * Placeholder billing snapshot until a license / subscription API exists.
 * Replace `BILLING_SNAPSHOT` (or wire props) when backend endpoints are available.
 */
const BILLING_SNAPSHOT = {
  licenseTier: "Team",
  productName: "Industry Path Pro",
  maintenanceActive: true,
  maintenanceNote: "Included with your current subscription term.",
  nextPaymentDateIso: "2026-04-28",
} as const;

function formatDate(isoDate: string): string {
  const d = new Date(`${isoDate}T12:00:00`);
  if (Number.isNaN(d.getTime())) {
    return isoDate;
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "long",
  }).format(d);
}

export default function BillingSettingsPanel() {
  return (
    <section className="graph-shell">
      <div className="main-workspace-view billing-settings-view">
        <div className="billing-settings-card">
          <h2 className="panel-title">Billing</h2>
          <p className="billing-settings-lead">Subscription and license details for your organization.</p>

          <dl className="kv billing-settings-kv">
            <dt>Current license</dt>
            <dd>
              {BILLING_SNAPSHOT.licenseTier} — {BILLING_SNAPSHOT.productName}
            </dd>

            <dt>Maintenance</dt>
            <dd>
              {BILLING_SNAPSHOT.maintenanceActive ? (
                <>
                  <span className="billing-status billing-status-active">Active</span>
                  <span className="billing-settings-sub">{BILLING_SNAPSHOT.maintenanceNote}</span>
                </>
              ) : (
                <span className="billing-status billing-status-inactive">Not active</span>
              )}
            </dd>

            <dt>Next payment</dt>
            <dd className="value-mono">{formatDate(BILLING_SNAPSHOT.nextPaymentDateIso)}</dd>
          </dl>
        </div>
      </div>
    </section>
  );
}
