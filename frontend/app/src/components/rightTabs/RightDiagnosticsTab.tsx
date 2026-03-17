import type { RuntimeEvaluationCycle } from "../../services/api";

type RightDiagnosticsTabProps = {
  diagnostics: RuntimeEvaluationCycle | null;
};

export default function RightDiagnosticsTab({ diagnostics }: RightDiagnosticsTabProps) {
  if (!diagnostics) {
    return (
      <>
        <div className="panel-subtitle">Health Checks</div>
        <ul className="trace-chain">
          <li>No evaluated diagnostics available yet.</li>
        </ul>
      </>
    );
  }

  const activeAlarms = Object.entries(diagnostics.alarms || {})
    .filter(([, active]) => Boolean(active))
    .map(([name]) => name);

  return (
    <>
      <div className="panel-subtitle">Health Checks</div>
      <ul className="trace-chain">
        {(diagnostics.health_checks || []).map((item) => (
          <li key={item.name}>
            {item.name}: {item.status} — {item.message}
          </li>
        ))}
      </ul>

      <div className="panel-subtitle" style={{ marginTop: "0.6rem" }}>
        Active Alarms
      </div>
      <ul className="trace-chain">
        {activeAlarms.length > 0 ? activeAlarms.map((alarm) => <li key={alarm}>{alarm}</li>) : <li>No active alarms</li>}
      </ul>

      <div className="panel-subtitle" style={{ marginTop: "0.6rem" }}>
        Last Evaluation
      </div>
      <ul className="trace-chain">
        <li>Reason: {diagnostics.reason}</li>
        <li>Evaluated blocks: {(diagnostics.evaluated_blocks || []).join(", ") || "none"}</li>
        <li>Signal updates: {diagnostics.signal_state_updated ? "yes" : "no"}</li>
      </ul>
    </>
  );
}
