export default function RightDiagnosticsTab() {
  return (
    <>
      <div className="panel-subtitle">Health Checks</div>
      <ul className="trace-chain">
        <li>Low flow alarm: Cleared</li>
        <li>Tank high-level alarm: Standby</li>
        <li>Pump thermal trip: Healthy</li>
      </ul>
    </>
  );
}
