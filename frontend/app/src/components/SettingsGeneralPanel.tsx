import { Bot, DatabaseZap, LoaderCircle, LogOut } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import {
  getPlantGenieAIConnectors,
  getPlantGeniePlantDataConnectors,
  type PlantGenieAIConnector,
  type PlantGeniePlantDataConnector,
} from "../services/api";

const formatTimestamp = (value: string | null): string => {
  if (!value) {
    return "Never";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "Never";
  }
  return parsed.toLocaleString();
};

type SettingsGeneralPanelProps = {
  accountEmail?: string | null;
  onLogout?: () => Promise<void>;
};

export default function SettingsGeneralPanel({ accountEmail = null, onLogout }: SettingsGeneralPanelProps) {
  const [aiConnectors, setAiConnectors] = useState<PlantGenieAIConnector[]>([]);
  const [plantDataConnectors, setPlantDataConnectors] = useState<PlantGeniePlantDataConnector[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState<boolean>(false);
  const [isLoggingOut, setIsLoggingOut] = useState<boolean>(false);

  const activeAIConnector = useMemo(
    () => aiConnectors.find((connector) => connector.is_active) ?? null,
    [aiConnectors]
  );
  const visiblePlantDataConnectors = useMemo(
    () => plantDataConnectors,
    [plantDataConnectors]
  );

  useEffect(() => {
    const load = async (): Promise<void> => {
      setIsLoading(true);
      try {
        const [nextAI, nextPlantData] = await Promise.all([
          getPlantGenieAIConnectors(),
          getPlantGeniePlantDataConnectors(),
        ]);
        setAiConnectors(nextAI);
        setPlantDataConnectors(nextPlantData);
      } finally {
        setIsLoading(false);
      }
    };

    void load();
  }, []);

  const handleLogout = async (): Promise<void> => {
    if (!onLogout) {
      return;
    }
    setIsLoggingOut(true);
    try {
      await onLogout();
    } finally {
      setIsLoggingOut(false);
      setShowLogoutConfirm(false);
    }
  };

  return (
    <section className="graph-shell">
      <div className="main-workspace-view billing-settings-view plant-genie-connectors-view">
        <div className="plant-genie-connectors-layout">
          <div className="plant-genie-connectors-card">
            <div className="plant-genie-connectors-header">
              <div>
                <div className="plant-genie-settings-kicker">Settings / General</div>
                <h2 className="panel-title">General</h2>
                <p className="billing-settings-lead">
                  Connected Plant Genie services appear here so you can confirm the active AI connector and live plant data sources at a glance.
                </p>
              </div>
            </div>

            {isLoading ? (
              <div className="plant-genie-connectors-empty">
                <LoaderCircle size={14} className="animate-spin" /> Loading connected services...
              </div>
            ) : (
              <>
                <div className="plant-genie-connectors-summary">
                  <div className="plant-genie-summary-chip is-active">
                    <Bot size={12} />
                    <span>{activeAIConnector ? `Active AI: ${activeAIConnector.name}` : "No active AI connector"}</span>
                  </div>
                  <div className="plant-genie-summary-chip is-active">
                    <DatabaseZap size={12} />
                    <span>
                      {visiblePlantDataConnectors.length > 0
                        ? `${visiblePlantDataConnectors.length} saved plant model${visiblePlantDataConnectors.length === 1 ? "" : "s"}`
                        : "No saved plant models"}
                    </span>
                  </div>
                </div>

                <div className="plant-genie-connector-list">
                  <article className="plant-genie-connector-item">
                    <div className="plant-genie-connector-main">
                      <div className="plant-genie-connector-title-row">
                        <strong>Connected Plant Models</strong>
                      </div>
                      {visiblePlantDataConnectors.length === 0 ? (
                        <div className="plant-genie-connectors-empty">No plant models have been added yet.</div>
                      ) : (
                        visiblePlantDataConnectors.map((connector) => (
                          <div key={connector.id} className="plant-genie-connector-item">
                            <div className="plant-genie-connector-title-row">
                              <strong>{connector.name}</strong>
                              <div className="plant-genie-connector-badges">
                                <span className={`plant-genie-badge ${connector.runtime.enabled ? "active" : "inactive"}`}>
                                  {connector.runtime.enabled ? "Connected" : "Saved"}
                                </span>
                                <span className={`plant-genie-badge ${connector.health.healthy ? "healthy" : "unhealthy"}`}>
                                  {connector.health.healthy ? "Healthy" : "Unhealthy"}
                                </span>
                              </div>
                            </div>
                            <div className="plant-genie-connector-meta">
                              {connector.connector_type === "opcua" ? "OPC UA" : connector.connector_type === "mqtt" ? "MQTT" : "SQL / Historian"}
                            </div>
                            <div className="plant-genie-connector-status-row">
                              <span>Last tested: {formatTimestamp(connector.last_tested_at)}</span>
                              <span>Last updated: {formatTimestamp(connector.updated_at)}</span>
                            </div>
                            {connector.runtime.last_error ? <p className="plant-genie-connector-message">{connector.runtime.last_error}</p> : null}
                          </div>
                        ))
                      )}
                    </div>
                  </article>
                </div>

                {onLogout ? (
                  <article className="plant-genie-connector-item settings-account-card">
                    <div className="plant-genie-connector-main">
                      <div className="plant-genie-connector-title-row">
                        <strong>Main App Session</strong>
                      </div>
                      <div className="plant-genie-connector-status-row">
                        <span>Signed in as {accountEmail || "Current user"}</span>
                        <span>Protected main IndustryPath workspace</span>
                      </div>
                      <div className="settings-account-actions">
                        <button className="command-btn danger" type="button" onClick={() => setShowLogoutConfirm(true)}>
                          <LogOut size={12} />
                          <span>Log Out</span>
                        </button>
                      </div>
                    </div>
                  </article>
                ) : null}
              </>
            )}
          </div>
        </div>
      </div>

      {showLogoutConfirm ? (
        <div className="modal-backdrop" onClick={() => (isLoggingOut ? null : setShowLogoutConfirm(false))}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <h3>Log Out</h3>
            <p className="modal-help-text">Are you sure you want to log out?</p>
            <div className="modal-actions">
              <button className="command-btn" type="button" onClick={() => setShowLogoutConfirm(false)} disabled={isLoggingOut}>
                Cancel
              </button>
              <button className="command-btn danger" type="button" onClick={() => void handleLogout()} disabled={isLoggingOut}>
                {isLoggingOut ? "Logging Out..." : "Log Out"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}