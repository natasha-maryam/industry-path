import { CheckCircle2, Plus, RadioTower, XCircle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { toast } from "react-hot-toast";

import {
  createPlantGeniePlantDataConnector,
  getPlantGeniePlantDataConnectors,
  updatePlantGeniePlantDataConnector,
  type PlantGeniePlantDataConnector,
} from "../services/api";
import {
  INDUSTRIAL_CONNECTION_TYPE_OPTIONS,
  OPCUA_SECURITY_MODE_OPTIONS,
  mapIndustrialConnectorFormToRequest,
  normalizeIndustrialConnectionType,
  validateIndustrialConnectorForm,
  type IndustrialConnectionFieldErrors,
  type IndustrialConnectionFormState,
} from "./plantGenie/industrialConnectorPayload";

type PlantGenieIndustrialConnectionsModalProps = {
  openCreateModalKey?: number;
  onConnectorsChange?: (connectors: PlantGeniePlantDataConnector[]) => void;
};

const EMPTY_FORM: IndustrialConnectionFormState = {
  name: "",
  connectorType: "opcua",
  pollIntervalMs: "5000",
  opcuaServerUrl: "",
  opcuaSecurityMode: "none",
  opcuaUsername: "",
  opcuaPassword: "",
  opcuaNodeConfig: "[\n  \"ns=2;s=Plant/Line1/TagA\"\n]",
  mqttBrokerUrl: "mqtt://broker.example.com:1883",
  mqttTopic: "",
  mqttClientId: "",
  mqttUsername: "",
  mqttPassword: "",
  sqlHost: "",
  sqlPort: "5432",
  sqlDatabase: "",
  sqlUsername: "",
  sqlPassword: "",
  sqlQueryConfig: '{\n  "query": "SELECT tag, value, timestamp FROM live_signals",\n  "tagColumn": "tag",\n  "valueColumn": "value",\n  "timestampColumn": "timestamp"\n}',
};

const normalizeConnectorModalError = (error: unknown, fallback: string): string => {
  return error instanceof Error && error.message ? error.message : fallback;
};

const buildSQLQueryConfigText = (config: Record<string, unknown>): string => {
  return JSON.stringify(
    {
      query: String(config.query ?? "SELECT tag, value, timestamp FROM live_signals"),
      tagColumn: String(config.tag_column ?? "tag"),
      valueColumn: String(config.value_column ?? "value"),
      timestampColumn: String(config.timestamp_column ?? "timestamp"),
    },
    null,
    2
  );
};

export default function PlantGenieIndustrialConnectionsModal({
  openCreateModalKey = 0,
  onConnectorsChange,
}: PlantGenieIndustrialConnectionsModalProps) {
  const [connectors, setConnectors] = useState<PlantGeniePlantDataConnector[]>([]);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [selectedConnectorId, setSelectedConnectorId] = useState<string | null>(null);
  const [form, setForm] = useState<IndustrialConnectionFormState>(EMPTY_FORM);
  const [fieldErrors, setFieldErrors] = useState<IndustrialConnectionFieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState<boolean>(false);

  const selectedConnector = useMemo(
    () => connectors.find((connector) => connector.id === selectedConnectorId) ?? null,
    [connectors, selectedConnectorId]
  );

  const isEditing = selectedConnector !== null;

  const connectionCopy = useMemo(() => {
    if (form.connectorType === "mqtt") {
      return "Connect live plant data over MQTT using your own broker and topic.";
    }
    if (form.connectorType === "sql") {
      return "Connect live plant data from your own historian or SQL source.";
    }
    return "Connect live plant data over OPC UA using your own endpoint and tags.";
  }, [form.connectorType]);

  const loadConnectors = async (): Promise<void> => {
    const nextConnectors = await getPlantGeniePlantDataConnectors();
    setConnectors(nextConnectors);
    onConnectorsChange?.(nextConnectors);
    setSelectedConnectorId((current) => {
      if (current && nextConnectors.some((connector) => connector.id === current)) {
        return current;
      }
      return null;
    });
  };

  useEffect(() => {
    void loadConnectors().catch((error) => {
      toast.error(normalizeConnectorModalError(error, "Failed to load Plant Genie plant data connectors."), {
        className: "industrial-toast industrial-toast-error",
      });
    });
  }, []);

  useEffect(() => {
    if (openCreateModalKey <= 0) {
      return;
    }
    setSelectedConnectorId(null);
    setForm(EMPTY_FORM);
    setFormError(null);
    setIsModalOpen(true);
  }, [openCreateModalKey]);

  useEffect(() => {
    if (!selectedConnector) {
      return;
    }

    if (selectedConnector.connector_type === "opcua") {
      setForm({
        name: selectedConnector.name,
        connectorType: "opcua",
        pollIntervalMs: String(selectedConnector.poll_interval_ms),
        opcuaServerUrl: String(selectedConnector.config.server_url ?? selectedConnector.config.endpoint ?? ""),
        opcuaSecurityMode: String(selectedConnector.config.security_mode ?? "none"),
        opcuaUsername: String(selectedConnector.config.username ?? ""),
        opcuaPassword: "",
        opcuaNodeConfig: JSON.stringify(selectedConnector.config.subscription_config ?? selectedConnector.config.node_ids ?? [], null, 2),
        mqttBrokerUrl: EMPTY_FORM.mqttBrokerUrl,
        mqttTopic: "",
        mqttClientId: "",
        mqttUsername: "",
        mqttPassword: "",
        sqlHost: "",
        sqlPort: "5432",
        sqlDatabase: "",
        sqlUsername: "",
        sqlPassword: "",
        sqlQueryConfig: EMPTY_FORM.sqlQueryConfig,
      });
      setFieldErrors({});
      setFormError(null);
      return;
    }

    if (selectedConnector.connector_type === "mqtt") {
      setForm({
        name: selectedConnector.name,
        connectorType: "mqtt",
        pollIntervalMs: String(selectedConnector.poll_interval_ms),
        opcuaServerUrl: "",
        opcuaSecurityMode: "",
        opcuaUsername: "",
        opcuaPassword: "",
        opcuaNodeConfig: EMPTY_FORM.opcuaNodeConfig,
        mqttBrokerUrl: String(selectedConnector.config.broker_url ?? `mqtt://${selectedConnector.config.host ?? ""}:${selectedConnector.config.port ?? 1883}`),
        mqttTopic: String(selectedConnector.config.topic ?? ""),
        mqttClientId: String(selectedConnector.config.client_id ?? ""),
        mqttUsername: String(selectedConnector.config.username ?? ""),
        mqttPassword: "",
        sqlHost: "",
        sqlPort: "5432",
        sqlDatabase: "",
        sqlUsername: "",
        sqlPassword: "",
        sqlQueryConfig: EMPTY_FORM.sqlQueryConfig,
      });
      setFormError(null);
      return;
    }

    setForm({
      name: selectedConnector.name,
      connectorType: "sql",
      pollIntervalMs: String(selectedConnector.poll_interval_ms),
      opcuaServerUrl: "",
      opcuaSecurityMode: "",
      opcuaUsername: "",
      opcuaPassword: "",
      opcuaNodeConfig: EMPTY_FORM.opcuaNodeConfig,
      mqttBrokerUrl: EMPTY_FORM.mqttBrokerUrl,
      mqttTopic: "",
      mqttClientId: "",
      mqttUsername: "",
      mqttPassword: "",
      sqlHost: String(selectedConnector.config.host ?? ""),
      sqlPort: String(selectedConnector.config.port ?? 5432),
      sqlDatabase: String(selectedConnector.config.database ?? ""),
      sqlUsername: String(selectedConnector.config.username ?? ""),
      sqlPassword: "",
      sqlQueryConfig: buildSQLQueryConfigText(selectedConnector.config),
    });
    setFieldErrors({});
    setFormError(null);
  }, [selectedConnector]);

  const resetToCreateMode = (): void => {
    setSelectedConnectorId(null);
    setForm(EMPTY_FORM);
    setFieldErrors({});
    setFormError(null);
  };

  const closeModal = (): void => {
    if (isSaving) {
      return;
    }
    setIsModalOpen(false);
    resetToCreateMode();
  };

  const clearFieldError = (field: keyof IndustrialConnectionFormState): void => {
    setFieldErrors((current) => {
      if (!current[field]) {
        return current;
      }
      const next = { ...current };
      delete next[field];
      return next;
    });
  };

  const updateField = <K extends keyof IndustrialConnectionFormState>(field: K, value: IndustrialConnectionFormState[K]): void => {
    setForm((current) => ({ ...current, [field]: value }));
    clearFieldError(field);
    if (formError) {
      setFormError(null);
    }
  };

  const handleSubmit = async (): Promise<void> => {
    const validationErrors = validateIndustrialConnectorForm(form, { isEditing });
    if (Object.keys(validationErrors).length > 0) {
      setFieldErrors(validationErrors);
      setFormError(null);
      return;
    }

    setIsSaving(true);
    setFieldErrors({});
    setFormError(null);

    try {
      const payload = mapIndustrialConnectorFormToRequest(form, { isEditing });
      if (import.meta.env.DEV) {
        console.info("Plant Genie plant-data outbound payload", payload);
      }
      if (isEditing && selectedConnector) {
        await updatePlantGeniePlantDataConnector(selectedConnector.id, payload);
        toast.success(`Updated ${form.name.trim()}`, { className: "industrial-toast" });
      } else {
        await createPlantGeniePlantDataConnector(payload);
        toast.success(`Created ${form.name.trim()}`, { className: "industrial-toast" });
      }
      await loadConnectors();
      setIsModalOpen(false);
      resetToCreateMode();
    } catch (error) {
      const message = normalizeConnectorModalError(error, "Plant data connection failed.");
      setFormError(message);
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setIsSaving(false);
    }
  };

  if (!isModalOpen) {
    return null;
  }

  return (
    <div className="modal-backdrop" onClick={closeModal}>
      <div className="modal-card plant-genie-connector-modal" onClick={(event) => event.stopPropagation()}>
        <div className="plant-genie-form-header">
          <div>
            <h3>Connect Plant Data</h3>
            <p>Manage live plant data connectors for OPC UA, MQTT, and SQL / Historian sources. Plant Genie uses only your connected live data.</p>
          </div>
          <div className="plant-genie-modal-toolbar">
            <button type="button" className="command-btn" onClick={resetToCreateMode} disabled={isSaving}>
              <Plus size={12} />
              <span>Add Connection</span>
            </button>
            <button type="button" className="command-btn" onClick={closeModal} disabled={isSaving}>
              Close
            </button>
          </div>
        </div>

        <div className="plant-genie-form-header plant-genie-subsection-header">
          <div>
            <h3>{isEditing ? "Edit Connection" : "Create Connection"}</h3>
            <p>{isEditing ? "Update the connector settings. Leave passwords blank to keep stored secrets." : connectionCopy}</p>
          </div>
        </div>

        <div className="plant-genie-form-grid">
          <label className="plant-genie-field">
            <span>Name</span>
            <input
              type="text"
              value={form.name}
                onChange={(event) => updateField("name", event.target.value)}
              placeholder="Primary plant data connection"
            />
              {fieldErrors.name ? <span className="plant-genie-field-error">{fieldErrors.name}</span> : null}
          </label>

          <label className="plant-genie-field">
            <span>Connection Type</span>
            <select
              value={form.connectorType}
              onChange={(event) => {
                const normalized = normalizeIndustrialConnectionType(event.target.value);
                updateField("connectorType", normalized ?? form.connectorType);
              }}
            >
              {INDUSTRIAL_CONNECTION_TYPE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {fieldErrors.connectorType ? <span className="plant-genie-field-error">{fieldErrors.connectorType}</span> : null}
          </label>

          <label className="plant-genie-field">
            <span>Poll Interval (ms)</span>
            <input
              type="number"
              min={500}
              step={100}
              value={form.pollIntervalMs}
              onChange={(event) => updateField("pollIntervalMs", event.target.value)}
            />
            {fieldErrors.pollIntervalMs ? <span className="plant-genie-field-error">{fieldErrors.pollIntervalMs}</span> : null}
          </label>

          {form.connectorType === "opcua" ? (
            <>
              <label className="plant-genie-field">
                <span>Server URL</span>
                <input
                  type="text"
                  value={form.opcuaServerUrl}
                  onChange={(event) => updateField("opcuaServerUrl", event.target.value)}
                  placeholder="opc.tcp://192.168.1.10:4840"
                />
                {fieldErrors.opcuaServerUrl ? <span className="plant-genie-field-error">{fieldErrors.opcuaServerUrl}</span> : null}
              </label>

              <label className="plant-genie-field">
                <span>Security Mode</span>
                <select
                  value={form.opcuaSecurityMode}
                  onChange={(event) => updateField("opcuaSecurityMode", event.target.value)}
                >
                  {OPCUA_SECURITY_MODE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="plant-genie-field">
                <span>Username</span>
                <input
                  type="text"
                  value={form.opcuaUsername}
                  onChange={(event) => updateField("opcuaUsername", event.target.value)}
                  placeholder="Optional username"
                />
              </label>

              <label className="plant-genie-field">
                <span>Password</span>
                <input
                  type="password"
                  value={form.opcuaPassword}
                  onChange={(event) => updateField("opcuaPassword", event.target.value)}
                  placeholder={isEditing ? "Leave blank to keep stored secret" : "Optional password"}
                />
              </label>

              <label className="plant-genie-field plant-genie-field-full">
                <span>Subscription / Node Config</span>
                <textarea
                  value={form.opcuaNodeConfig}
                  onChange={(event) => updateField("opcuaNodeConfig", event.target.value)}
                  rows={5}
                />
                {fieldErrors.opcuaNodeConfig ? <span className="plant-genie-field-error">{fieldErrors.opcuaNodeConfig}</span> : null}
              </label>
            </>
          ) : null}

          {form.connectorType === "mqtt" ? (
            <>
              <label className="plant-genie-field">
                <span>Broker URL</span>
                <input
                  type="text"
                  value={form.mqttBrokerUrl}
                  onChange={(event) => updateField("mqttBrokerUrl", event.target.value)}
                  placeholder="mqtt://broker.example.com:1883"
                />
                {fieldErrors.mqttBrokerUrl ? <span className="plant-genie-field-error">{fieldErrors.mqttBrokerUrl}</span> : null}
              </label>

              <label className="plant-genie-field">
                <span>Topic</span>
                <input
                  type="text"
                  value={form.mqttTopic}
                  onChange={(event) => updateField("mqttTopic", event.target.value)}
                  placeholder="plant/line1/#"
                />
                {fieldErrors.mqttTopic ? <span className="plant-genie-field-error">{fieldErrors.mqttTopic}</span> : null}
              </label>

              <label className="plant-genie-field">
                <span>Client ID</span>
                <input
                  type="text"
                  value={form.mqttClientId}
                  onChange={(event) => updateField("mqttClientId", event.target.value)}
                  placeholder="Optional client ID"
                />
              </label>

              <label className="plant-genie-field">
                <span>Username</span>
                <input
                  type="text"
                  value={form.mqttUsername}
                  onChange={(event) => updateField("mqttUsername", event.target.value)}
                  placeholder="Optional username"
                />
              </label>

              <label className="plant-genie-field">
                <span>Password</span>
                <input
                  type="password"
                  value={form.mqttPassword}
                  onChange={(event) => updateField("mqttPassword", event.target.value)}
                  placeholder="Optional broker secret"
                />
              </label>
            </>
          ) : null}

          {form.connectorType === "sql" ? (
            <>
              <label className="plant-genie-field">
                <span>Host</span>
                <input
                  type="text"
                  value={form.sqlHost}
                  onChange={(event) => updateField("sqlHost", event.target.value)}
                  placeholder="historian.example.com"
                />
                {fieldErrors.sqlHost ? <span className="plant-genie-field-error">{fieldErrors.sqlHost}</span> : null}
              </label>

              <label className="plant-genie-field">
                <span>Port</span>
                <input
                  type="number"
                  min={1}
                  max={65535}
                  value={form.sqlPort}
                  onChange={(event) => updateField("sqlPort", event.target.value)}
                />
                {fieldErrors.sqlPort ? <span className="plant-genie-field-error">{fieldErrors.sqlPort}</span> : null}
              </label>

              <label className="plant-genie-field">
                <span>Database</span>
                <input
                  type="text"
                  value={form.sqlDatabase}
                  onChange={(event) => updateField("sqlDatabase", event.target.value)}
                />
                {fieldErrors.sqlDatabase ? <span className="plant-genie-field-error">{fieldErrors.sqlDatabase}</span> : null}
              </label>

              <label className="plant-genie-field">
                <span>Username</span>
                <input
                  type="text"
                  value={form.sqlUsername}
                  onChange={(event) => updateField("sqlUsername", event.target.value)}
                />
                {fieldErrors.sqlUsername ? <span className="plant-genie-field-error">{fieldErrors.sqlUsername}</span> : null}
              </label>

              <label className="plant-genie-field">
                <span>Password</span>
                <input
                  type="password"
                  value={form.sqlPassword}
                  onChange={(event) => updateField("sqlPassword", event.target.value)}
                  placeholder={isEditing ? "Leave blank to keep stored secret" : "Enter password"}
                />
                {fieldErrors.sqlPassword ? <span className="plant-genie-field-error">{fieldErrors.sqlPassword}</span> : null}
              </label>

              <label className="plant-genie-field plant-genie-field-full">
                <span>Query / Polling Config</span>
                <textarea
                  value={form.sqlQueryConfig}
                  onChange={(event) => updateField("sqlQueryConfig", event.target.value)}
                  rows={6}
                />
                {fieldErrors.sqlQueryConfig ? <span className="plant-genie-field-error">{fieldErrors.sqlQueryConfig}</span> : null}
              </label>
            </>
          ) : null}
        </div>

        <div className="plant-genie-form-help">
          <RadioTower size={13} />
          <span>Connector credentials are encrypted on the backend and never returned to the browser after save.</span>
        </div>

        {formError ? (
          <div className="plant-genie-inline-alert error">
            <XCircle size={13} />
            <span>{formError}</span>
          </div>
        ) : null}

        <div className="modal-actions plant-genie-modal-actions">
          <button type="button" className="command-btn" onClick={closeModal} disabled={isSaving}>
            Cancel
          </button>
          <button type="button" className="command-btn primary" onClick={() => void handleSubmit()} disabled={isSaving}>
            <CheckCircle2 size={12} />
            <span>{isSaving ? "Saving..." : isEditing ? "Save Changes" : "Create Connector"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}