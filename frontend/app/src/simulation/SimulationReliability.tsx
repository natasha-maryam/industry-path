import { useEffect, useState } from "react";
import { getSimulationChangelog, getSimulationEventsReplay, getSimulationHealth } from "./simulationApi";

export default function SimulationReliability() {
  const [health, setHealth] = useState<{ overallHealthy?: boolean; connectors?: Array<{ id: string; healthy: boolean; latency: number | null }> } | null>(null);
  const [changes, setChanges] = useState<Array<Record<string, unknown>>>([]);
  const [events, setEvents] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState("");

  const refresh = async (): Promise<void> => {
    try {
      const [nextHealth, nextChanges, nextEvents] = await Promise.all([
        getSimulationHealth(),
        getSimulationChangelog(),
        getSimulationEventsReplay(),
      ]);
      setHealth(nextHealth as { overallHealthy?: boolean; connectors?: Array<{ id: string; healthy: boolean; latency: number | null }> });
      setChanges(nextChanges.slice(0, 5));
      setEvents(nextEvents.slice(0, 5));
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load reliability data");
    }
  };

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => {
      void refresh();
    }, 3000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <section className="workspace-documents-list-panel">
      <div className="workspace-documents-list-header">
        <h3>Reliability / Ops</h3>
        <p>Health, changelog, and replay snapshots.</p>
      </div>
      <div className="modal-actions" style={{ marginTop: 0 }}>
        <button type="button" className="command-btn" onClick={() => void refresh()}>
          Refresh
        </button>
      </div>
      <p>
        <strong>Overall:</strong> {health?.overallHealthy ? "Healthy" : "Not healthy yet"}
      </p>
      <div className="monitor-frame" style={{ maxHeight: 120, overflow: "auto" }}>
        {(health?.connectors ?? []).map((connector) => (
          <p key={connector.id}>
            {connector.id}: {connector.healthy ? "OK" : "Stale"} (latency: {connector.latency ?? "N/A"} ms)
          </p>
        ))}
      </div>
      <div className="monitor-frame" style={{ maxHeight: 120, overflow: "auto" }}>
        <strong>Changelog</strong>
        {changes.map((entry, index) => (
          <p key={index}>{JSON.stringify(entry)}</p>
        ))}
      </div>
      <div className="monitor-frame" style={{ maxHeight: 120, overflow: "auto" }}>
        <strong>Events Replay</strong>
        {events.map((entry, index) => (
          <p key={index}>{JSON.stringify(entry)}</p>
        ))}
      </div>
      {error ? <p style={{ color: "#a11" }}>{error}</p> : null}
    </section>
  );
}
