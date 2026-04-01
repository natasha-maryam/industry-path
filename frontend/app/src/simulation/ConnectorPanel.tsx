import { useState } from "react";
import { activateConnector, testConnector } from "./simulationApi";

type Props = {
  onStatus?: (message: string) => void;
};

export default function ConnectorPanel({ onStatus }: Props) {
  const [config, setConfig] = useState({
    id: "sim-conn",
    type: "mqtt",
    url: "mqtt://localhost:1883",
    topic: "industrypath/sim",
    endpoint: "",
    query_endpoint: "",
  });
  const [loading, setLoading] = useState(false);

  const payload = {
    id: config.id,
    type: config.type,
    config:
      config.type === "mqtt"
        ? { url: config.url, topic: config.topic }
        : config.type === "opcua"
          ? { endpoint: config.endpoint }
          : { query_endpoint: config.query_endpoint },
  };

  const runTest = async (): Promise<void> => {
    if (config.type === "mqtt" && (!config.url.trim() || !config.topic.trim())) {
      onStatus?.("MQTT URL and topic are required");
      return;
    }
    if (config.type === "opcua" && !config.endpoint.trim()) {
      onStatus?.("OPC UA endpoint is required");
      return;
    }
    if (config.type === "sql" && !config.query_endpoint.trim()) {
      onStatus?.("SQL query endpoint is required");
      return;
    }
    setLoading(true);
    try {
      await testConnector(payload);
      onStatus?.("Connector test passed");
    } catch (error) {
      onStatus?.(error instanceof Error ? error.message : "Connector test failed");
    } finally {
      setLoading(false);
    }
  };

  const runActivate = async (): Promise<void> => {
    if (config.type === "mqtt" && (!config.url.trim() || !config.topic.trim())) {
      onStatus?.("MQTT URL and topic are required");
      return;
    }
    if (config.type === "opcua" && !config.endpoint.trim()) {
      onStatus?.("OPC UA endpoint is required");
      return;
    }
    if (config.type === "sql" && !config.query_endpoint.trim()) {
      onStatus?.("SQL query endpoint is required");
      return;
    }
    setLoading(true);
    try {
      await activateConnector(payload);
      onStatus?.("Connector activated");
    } catch (error) {
      onStatus?.(error instanceof Error ? error.message : "Activation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="workspace-documents-list-panel">
      <div className="workspace-documents-list-header">
        <h3>Simulation Connectors</h3>
        <p>Test and activate one live connector.</p>
      </div>
      <div className="settings-grid">
        <label className="settings-line">
          <span>Connector ID</span>
          <input value={config.id} onChange={(event) => setConfig((value) => ({ ...value, id: event.target.value }))} />
        </label>
        <label className="settings-line">
          <span>Type</span>
          <select value={config.type} onChange={(event) => setConfig((value) => ({ ...value, type: event.target.value }))}>
            <option value="mqtt">MQTT</option>
            <option value="opcua">OPC UA</option>
            <option value="sql">SQL</option>
          </select>
        </label>
        {config.type === "mqtt" ? (
          <>
            <label className="settings-line">
              <span>MQTT URL</span>
              <input value={config.url} onChange={(event) => setConfig((value) => ({ ...value, url: event.target.value }))} />
            </label>
            <label className="settings-line">
              <span>Topic</span>
              <input value={config.topic} onChange={(event) => setConfig((value) => ({ ...value, topic: event.target.value }))} />
            </label>
          </>
        ) : null}
        {config.type === "opcua" ? (
          <label className="settings-line">
            <span>Endpoint</span>
            <input value={config.endpoint} onChange={(event) => setConfig((value) => ({ ...value, endpoint: event.target.value }))} />
          </label>
        ) : null}
        {config.type === "sql" ? (
          <label className="settings-line">
            <span>Query Endpoint</span>
            <input value={config.query_endpoint} onChange={(event) => setConfig((value) => ({ ...value, query_endpoint: event.target.value }))} />
          </label>
        ) : null}
      </div>
      <div className="modal-actions">
        <button type="button" className="command-btn" disabled={loading} onClick={() => void runTest()}>
          Test
        </button>
        <button type="button" className="command-btn primary" disabled={loading} onClick={() => void runActivate()}>
          Activate
        </button>
      </div>
    </section>
  );
}
