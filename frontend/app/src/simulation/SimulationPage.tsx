import { useState } from "react";
import ConnectorPanel from "./ConnectorPanel";
import SimulationAI from "./SimulationAI";
import SimulationEngine from "./SimulationEngine";
import SimulationReliability from "./SimulationReliability";
import SimulationSignalTable from "./SimulationSignalTable";

export default function SimulationPage() {
  const [status, setStatus] = useState("");

  return (
    <div className="workspace-module-stack">
      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr 380px", gap: 12 }}>
        <div>
          <ConnectorPanel onStatus={setStatus} />
          <SimulationEngine onStatus={setStatus} />
        </div>
        <SimulationSignalTable />
        <div style={{ display: "grid", gap: 12 }}>
          <SimulationAI onStatus={setStatus} />
          <SimulationReliability />
        </div>
      </div>
      {status ? <div className="export-note">{status}</div> : null}
    </div>
  );
}
