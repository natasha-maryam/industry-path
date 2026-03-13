export type RightTab = "Details" | "Signals" | "Trace" | "Replay" | "Diagnostics" | "Settings";

type Equipment = {
  id: string;
  type: "Tank" | "Pump" | "Sensor" | "Valve";
  status: string;
  motor?: string;
  signals: string[];
  logic: string;
  processUnit?: string;
  controlRole?: string;
  signalType?: string;
  instrumentRole?: string;
  powerRating?: string;
  connections: string[];
  controls: string[];
  measures: string[];
  controlPath: string[];
  metadataConfidence: Record<string, number>;
};

type DetailsPanelProps = {
  activeTab: RightTab;
  replayPoint: number;
  selectedEquipment: Equipment;
  tracePath: string[];
  onTabChange: (tab: RightTab) => void;
};

const TABS: RightTab[] = ["Details", "Signals", "Trace", "Replay", "Diagnostics", "Settings"];

export default function DetailsPanel({
  activeTab,
  replayPoint,
  selectedEquipment,
  tracePath,
  onTabChange,
}: DetailsPanelProps) {
  const replayTime = `12:${String(Math.floor(replayPoint / 2)).padStart(2, "0")}:34`;

  return (
    <div>
      <h3 className="panel-title">Engineering Panel</h3>

      <div className="right-tabs">
        {TABS.map((tab) => (
          <button
            key={tab}
            className={`right-tab ${activeTab === tab ? "active" : ""}`}
            onClick={() => onTabChange(tab)}
            type="button"
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="right-content">
        {activeTab === "Details" ? (
          <>
            <dl className="kv kv-technical">
              <dt>Equipment</dt>
              <dd>{selectedEquipment.id}</dd>
              <dt>Type</dt>
              <dd>{selectedEquipment.type}</dd>
              <dt>Status</dt>
              <dd>{selectedEquipment.status}</dd>
              <dt>Process Unit</dt>
              <dd>{selectedEquipment.processUnit ?? "N/A"}</dd>
              <dt>Control Role</dt>
              <dd>{selectedEquipment.controlRole ?? "N/A"}</dd>
              <dt>Signal Type</dt>
              <dd>{selectedEquipment.signalType ?? "N/A"}</dd>
              <dt>Instrument Role</dt>
              <dd>{selectedEquipment.instrumentRole ?? "N/A"}</dd>
              <dt>Power Rating</dt>
              <dd>{selectedEquipment.powerRating ?? "N/A"}</dd>
            </dl>

            <div className="panel-subtitle">Connections</div>
            <ul className="trace-chain">
              {(selectedEquipment.connections.length ? selectedEquipment.connections : ["No known process connections"]).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>

            <div className="panel-subtitle">Control Path</div>
            <ul className="trace-chain">
              {(selectedEquipment.controlPath.length ? selectedEquipment.controlPath : ["No control path available"]).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>

            <div className="panel-subtitle">Controls</div>
            <ul className="trace-chain">
              {(selectedEquipment.controls.length ? selectedEquipment.controls : ["No control targets available"]).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>

            <div className="panel-subtitle">Measures</div>
            <ul className="trace-chain">
              {(selectedEquipment.measures.length ? selectedEquipment.measures : ["No measurement targets available"]).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>

            <div className="panel-subtitle">Inference Confidence</div>
            <ul className="trace-chain">
              {Object.entries(selectedEquipment.metadataConfidence).length ? (
                Object.entries(selectedEquipment.metadataConfidence)
                  .sort((left, right) => right[1] - left[1])
                  .slice(0, 5)
                  .map(([key, value]) => <li key={key}>{`${key}: ${(value * 100).toFixed(0)}%`}</li>)
              ) : (
                <li>No confidence scores available</li>
              )}
            </ul>
          </>
        ) : null}

        {activeTab === "Signals" ? (
          <>
            <div className="panel-subtitle">Signal List</div>
            <ul className="trace-chain">
              {(selectedEquipment.signals.length ? selectedEquipment.signals : ["No explicit signals available"]).map((signal) => (
                <li key={signal}>{signal}</li>
              ))}
            </ul>
          </>
        ) : null}

        {activeTab === "Trace" ? (
          <>
            <div className="panel-subtitle">Signal Path</div>
            <ol className="trace-chain trace-chain-ordered">
              {(tracePath.length ? tracePath : ["No active trace. Right-click a node to trace signal path."]).map((node) => (
                <li key={node}>{node}</li>
              ))}
            </ol>
          </>
        ) : null}

        {activeTab === "Replay" ? (
          <dl className="kv kv-technical">
            <dt>Time</dt>
            <dd className="value-mono">{replayTime}</dd>
            <dt>Tank-101</dt>
            <dd className="value-mono">{`${replayPoint}% level`}</dd>
            <dt>Pump-101</dt>
            <dd>{replayPoint % 2 === 0 ? "RUNNING" : "IDLE"}</dd>
            <dt>Flow Rate</dt>
            <dd className="value-mono">{`${20 + Math.floor(replayPoint / 4)} m3/h`}</dd>
          </dl>
        ) : null}

        {activeTab === "Diagnostics" ? (
          <>
            <div className="panel-subtitle">Health Checks</div>
            <ul className="trace-chain">
              <li>Low flow alarm: Cleared</li>
              <li>Tank high-level alarm: Standby</li>
              <li>Pump thermal trip: Healthy</li>
            </ul>
          </>
        ) : null}

        {activeTab === "Settings" ? (
          <div className="settings-grid">
            <div className="panel-subtitle">Runtime Preferences</div>
            <div className="settings-line">
              <span>Enable Signal Trace</span>
              <strong>ON</strong>
            </div>
            <div className="settings-line">
              <span>Trace Depth Limit</span>
              <strong className="value-mono">10</strong>
            </div>
            <div className="settings-line">
              <span>Enable Replay Engine</span>
              <strong>ON</strong>
            </div>
            <div className="settings-line">
              <span>Replay Speed</span>
              <strong className="value-mono">1x</strong>
            </div>
            <div className="settings-line">
              <span>Data Retention</span>
              <strong className="value-mono">24 hours</strong>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
