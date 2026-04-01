import type { PlantGeniePlantDataConnectorType } from "../../services/api";

export type IndustrialConnectionFormState = {
  name: string;
  connectorType: PlantGeniePlantDataConnectorType;
  pollIntervalMs: string;
  opcuaServerUrl: string;
  opcuaSecurityMode: string;
  opcuaUsername: string;
  opcuaPassword: string;
  opcuaNodeConfig: string;
  mqttBrokerUrl: string;
  mqttTopic: string;
  mqttClientId: string;
  mqttUsername: string;
  mqttPassword: string;
  sqlHost: string;
  sqlPort: string;
  sqlDatabase: string;
  sqlUsername: string;
  sqlPassword: string;
  sqlQueryConfig: string;
};

export type IndustrialConnectionFieldErrors = Partial<Record<keyof IndustrialConnectionFormState, string>>;

export type PlantGeniePlantDataConnectorRequest = {
  name: string;
  connector_type: PlantGeniePlantDataConnectorType;
  poll_interval_ms: number;
  config: Record<string, unknown>;
  secrets: Record<string, unknown>;
};

export const INDUSTRIAL_CONNECTION_TYPE_OPTIONS: Array<{ value: PlantGeniePlantDataConnectorType; label: string }> = [
  { value: "opcua", label: "OPC UA" },
  { value: "mqtt", label: "MQTT" },
  { value: "sql", label: "SQL / Historian" },
];

export const OPCUA_SECURITY_MODE_OPTIONS = [
  { value: "none", label: "None" },
  { value: "sign", label: "Sign" },
  { value: "sign_and_encrypt", label: "Sign and Encrypt" },
] as const;

const CONNECTION_TYPE_ALIASES: Record<string, PlantGeniePlantDataConnectorType> = {
  opcua: "opcua",
  "opc ua": "opcua",
  mqtt: "mqtt",
  sql: "sql",
  "sql / historian": "sql",
  historian: "sql",
};

const OPCUA_URL_PATTERN = /^(opc\.tcp|http|https):\/\/[^\s/]+/i;
const MQTT_URL_PATTERN = /^(mqtt|mqtts):\/\/[^\s/]+/i;

type SQLQueryConfig = {
  query: string;
  tagColumn: string;
  valueColumn: string;
  timestampColumn: string | null;
};

export const normalizeIndustrialConnectionType = (value: string): PlantGeniePlantDataConnectorType | null => {
  const normalized = String(value || "").trim().toLowerCase();
  return CONNECTION_TYPE_ALIASES[normalized] ?? null;
};

const isNonEmptyStringArray = (value: unknown): value is string[] => {
  return Array.isArray(value) && value.every((item) => typeof item === "string" && item.trim().length > 0);
};

const validateSchemeUrl = (value: string, pattern: RegExp): boolean => {
  return pattern.test(value.trim());
};

const parseSubscriptionConfig = (value: string): { parsed: unknown; nodeIds: string[] } => {
  const trimmed = value.trim();
  if (!trimmed) {
    throw new Error("Subscription / Node config is required.");
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(trimmed);
  } catch {
    throw new Error("Subscription / Node config must be valid JSON.");
  }

  if (isNonEmptyStringArray(parsed)) {
    return { parsed, nodeIds: parsed.map((item) => item.trim()) };
  }

  if (parsed && typeof parsed === "object") {
    const objectValue = parsed as Record<string, unknown>;
    const nodeIds = objectValue.node_ids ?? objectValue.nodeIds;
    if (isNonEmptyStringArray(nodeIds)) {
      return { parsed, nodeIds: nodeIds.map((item) => item.trim()) };
    }
  }

  throw new Error("Subscription / Node config must be a JSON array of node IDs or an object with node_ids.");
};

const parseQueryConfig = (value: string): SQLQueryConfig => {
  const trimmed = value.trim();
  if (!trimmed) {
    throw new Error("Query / Polling Config is required.");
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(trimmed);
  } catch {
    throw new Error("Query / Polling Config must be valid JSON.");
  }

  if (!parsed || typeof parsed !== "object") {
    throw new Error("Query / Polling Config must be a JSON object.");
  }

  const config = parsed as Record<string, unknown>;
  const query = String(config.query ?? "").trim();
  const tagColumn = String(config.tagColumn ?? config.tag_column ?? "").trim();
  const valueColumn = String(config.valueColumn ?? config.value_column ?? "").trim();
  const timestampColumn = String(config.timestampColumn ?? config.timestamp_column ?? "").trim();

  if (!query) {
    throw new Error("Query / Polling Config must include a query value.");
  }
  if (!tagColumn) {
    throw new Error("Query / Polling Config must include a tagColumn value.");
  }
  if (!valueColumn) {
    throw new Error("Query / Polling Config must include a valueColumn value.");
  }

  return {
    query,
    tagColumn,
    valueColumn,
    timestampColumn: timestampColumn || null,
  };
};

export const validateIndustrialConnectorForm = (
  form: IndustrialConnectionFormState,
  options: { isEditing: boolean }
): IndustrialConnectionFieldErrors => {
  const errors: IndustrialConnectionFieldErrors = {};

  if (!form.name.trim()) {
    errors.name = "Connection name is required.";
  }

  const connectorType = normalizeIndustrialConnectionType(form.connectorType);
  if (!connectorType) {
    errors.connectorType = "Connection type is required.";
    return errors;
  }

  const pollIntervalMs = Number.parseInt(form.pollIntervalMs, 10);
  if (!Number.isFinite(pollIntervalMs) || pollIntervalMs < 500 || pollIntervalMs > 300000) {
    errors.pollIntervalMs = "Poll interval must be a number between 500 and 300000.";
  }

  if (connectorType === "opcua") {
    if (!form.opcuaServerUrl.trim()) {
      errors.opcuaServerUrl = "Server URL is required.";
    } else if (!validateSchemeUrl(form.opcuaServerUrl, OPCUA_URL_PATTERN)) {
      errors.opcuaServerUrl = "Server URL must start with opc.tcp://, http://, or https://.";
    }

    try {
      parseSubscriptionConfig(form.opcuaNodeConfig);
    } catch (error) {
      errors.opcuaNodeConfig = error instanceof Error ? error.message : "Subscription / Node config is invalid.";
    }
  }

  if (connectorType === "mqtt") {
    if (!form.mqttBrokerUrl.trim()) {
      errors.mqttBrokerUrl = "Broker URL is required.";
    } else if (!validateSchemeUrl(form.mqttBrokerUrl, MQTT_URL_PATTERN)) {
      errors.mqttBrokerUrl = "Broker URL must start with mqtt:// or mqtts://.";
    }
    if (!form.mqttTopic.trim()) {
      errors.mqttTopic = "Topic is required.";
    }
  }

  if (connectorType === "sql") {
    if (!form.sqlHost.trim()) {
      errors.sqlHost = "Host is required.";
    }

    const port = Number.parseInt(form.sqlPort, 10);
    if (!Number.isFinite(port) || port < 1 || port > 65535) {
      errors.sqlPort = "Port must be a number between 1 and 65535.";
    }
    if (!form.sqlDatabase.trim()) {
      errors.sqlDatabase = "Database is required.";
    }
    if (!form.sqlUsername.trim()) {
      errors.sqlUsername = "Username is required.";
    }
    if (!options.isEditing && !form.sqlPassword.trim()) {
      errors.sqlPassword = "Password is required.";
    }
    try {
      parseQueryConfig(form.sqlQueryConfig);
    } catch (error) {
      errors.sqlQueryConfig = error instanceof Error ? error.message : "Query / Polling Config is invalid.";
    }
  }

  return errors;
};

export const mapIndustrialConnectorFormToRequest = (
  form: IndustrialConnectionFormState,
  options: { isEditing: boolean }
): PlantGeniePlantDataConnectorRequest => {
  const validationErrors = validateIndustrialConnectorForm(form, options);
  if (Object.keys(validationErrors).length > 0) {
    const firstMessage = Object.values(validationErrors)[0];
    throw new Error(firstMessage || "Connection configuration is invalid.");
  }

  const connectorType = normalizeIndustrialConnectionType(form.connectorType);
  if (!connectorType) {
    throw new Error("Connection type is required.");
  }

  const pollIntervalMs = Number.parseInt(form.pollIntervalMs, 10);

  if (connectorType === "opcua") {
    const subscription = parseSubscriptionConfig(form.opcuaNodeConfig);
    return {
      name: form.name.trim(),
      connector_type: "opcua",
      poll_interval_ms: pollIntervalMs,
      config: {
        server_url: form.opcuaServerUrl.trim(),
        security_mode: form.opcuaSecurityMode === "none" ? null : form.opcuaSecurityMode,
        username: form.opcuaUsername.trim() || null,
        subscription_config: subscription.parsed,
        node_ids: subscription.nodeIds,
      },
      secrets: form.opcuaPassword.trim() ? { password: form.opcuaPassword.trim() } : {},
    };
  }

  if (connectorType === "mqtt") {
    return {
      name: form.name.trim(),
      connector_type: "mqtt",
      poll_interval_ms: pollIntervalMs,
      config: {
        broker_url: form.mqttBrokerUrl.trim(),
        topic: form.mqttTopic.trim(),
        client_id: form.mqttClientId.trim() || null,
        username: form.mqttUsername.trim() || null,
      },
      secrets: form.mqttPassword.trim() ? { password: form.mqttPassword.trim() } : {},
    };
  }

  const queryConfig = parseQueryConfig(form.sqlQueryConfig);
  return {
    name: form.name.trim(),
    connector_type: "sql",
    poll_interval_ms: pollIntervalMs,
    config: {
      host: form.sqlHost.trim(),
      port: Number.parseInt(form.sqlPort, 10),
      database: form.sqlDatabase.trim(),
      username: form.sqlUsername.trim(),
      query: queryConfig.query,
      tag_column: queryConfig.tagColumn,
      value_column: queryConfig.valueColumn,
      timestamp_column: queryConfig.timestampColumn,
    },
    secrets: form.sqlPassword.trim() ? { password: form.sqlPassword.trim() } : {},
  };
};