import { useEffect, useMemo, useState } from "react";
import { createSimulationEventSource, getSimulationState } from "./simulationApi";

type SignalRow = {
  id: string;
  value: unknown;
  timestamp?: number;
  source?: string;
  simulated?: boolean;
};

export default function SimulationSignalTable() {
  const [signals, setSignals] = useState<Record<string, SignalRow>>({});

  useEffect(() => {
    void getSimulationState()
      .then((snapshot) => {
        const initial = Object.entries(snapshot).reduce<Record<string, SignalRow>>((acc, [id, raw]) => {
          if (raw && typeof raw === "object") {
            acc[id] = { id, ...(raw as Omit<SignalRow, "id">) };
          }
          return acc;
        }, {});
        setSignals(initial);
      })
      .catch(() => null);

    const source = createSimulationEventSource();
    source.onmessage = (event) => {
      const payload = JSON.parse(event.data) as SignalRow;
      if (!payload.id) return;
      setSignals((previous) => ({ ...previous, [payload.id]: payload }));
    };
    return () => source.close();
  }, []);

  const rows = useMemo(() => Object.values(signals).sort((left, right) => String(left.id).localeCompare(String(right.id))), [signals]);

  return (
    <section className="workspace-documents-list-panel">
      <div className="workspace-documents-list-header">
        <h3>Live Simulation Signals</h3>
        <p>Real-time stream from Redis-backed simulation layer.</p>
      </div>
      <table className="io-mapping-table">
        <thead>
          <tr>
            <th>Tag</th>
            <th>Value</th>
            <th>Source</th>
            <th>Timestamp</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td>{row.id}</td>
              <td>{String(row.value ?? "")}</td>
              <td>{row.source ?? "live"}</td>
              <td>{row.timestamp ? new Date(row.timestamp).toLocaleTimeString() : "N/A"}</td>
              <td>{row.simulated ? "SIMULATED" : "LIVE"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
