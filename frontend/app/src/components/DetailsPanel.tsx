export type RightTab = "Details" | "Signals" | "Trace" | "Replay" | "Diagnostics" | "Settings";

type Equipment = {
  id: string;
  type: "Tank" | "Pump" | "Sensor" | "Valve";
  status: string;
  motor?: string;
  signals: string[];
  logic: string;
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
          <dl className="kv kv-technical">
            <dt>Equipment</dt>
            <dd>{selectedEquipment.id}</dd>
            <dt>Type</dt>
            <dd>{selectedEquipment.type}</dd>
            <dt>Status</dt>
            <dd>{selectedEquipment.status}</dd>
            <dt>Motor</dt>
            <dd>{selectedEquipment.motor ?? "N/A"}</dd>
            <dt>Logic</dt>
            <dd>{selectedEquipment.logic}</dd>
          </dl>
        ) : null}

        {activeTab === "Signals" ? (
          <>
            <div className="panel-subtitle">Signal List</div>
            <ul className="trace-chain">
              {selectedEquipment.signals.map((signal) => (
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
