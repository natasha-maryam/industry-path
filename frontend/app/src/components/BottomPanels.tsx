type BottomView = "simulation" | "monitoring" | "logic";

type BottomPanelsProps = {
  activeView: BottomView;
  generatedLogic: string;
  simulationMetrics?: Record<string, unknown>;
  monitoringSummary?: Record<string, unknown>;
  showLogic: boolean;
  onViewChange: (view: BottomView) => void;
};

export default function BottomPanels({
  activeView,
  generatedLogic,
  simulationMetrics,
  monitoringSummary,
  showLogic,
  onViewChange,
}: BottomPanelsProps) {
  const toMetricLabel = (key: string): string =>
    key
      .replace(/_/g, " ")
      .replace(/\b\w/g, (character) => character.toUpperCase());

  const metricEntries = Object.entries(simulationMetrics ?? {});

  return (
    <section className="bottom-shell">
      <nav className="bottom-nav">
        <button className={activeView === "simulation" ? "active" : ""} onClick={() => onViewChange("simulation")} type="button">
          Simulation Panel
        </button>
        <button className={activeView === "monitoring" ? "active" : ""} onClick={() => onViewChange("monitoring")} type="button">
          Monitoring Dashboard
        </button>
        <button className={activeView === "logic" ? "active" : ""} onClick={() => onViewChange("logic")} type="button">
          Code Panel
        </button>
      </nav>

      <div className="bottom-content">
        {activeView === "simulation" ? (
          metricEntries.length > 0 ? (
            <div className="stat-grid">
              {metricEntries.map(([key, value]) => (
                <article key={key} className="stat-card">
                  <h4>{toMetricLabel(key)}</h4>
                  <p className="value-mono">{String(value)}</p>
                </article>
              ))}
            </div>
          ) : (
            <div className="monitor-frame">No simulation metrics available yet.</div>
          )
        ) : null}

        {activeView === "monitoring" ? (
          <div className="monitor-frame">
            {monitoringSummary ? (
              <pre className="monitor-json">{JSON.stringify(monitoringSummary, null, 2)}</pre>
            ) : (
              "No monitoring summary available yet."
            )}
          </div>
        ) : null}

        {activeView === "logic" ? (
          showLogic ? (
            <pre className="logic-box">{generatedLogic}</pre>
          ) : (
            <div className="monitor-frame">Click "Generate Control Logic" or "View Logic" to show generated PLC code.</div>
          )
        ) : null}
      </div>
    </section>
  );
}