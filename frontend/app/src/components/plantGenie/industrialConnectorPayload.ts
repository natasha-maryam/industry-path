import type { PlantGeniePlantDataConnectorType } from "../../services/api";

export type IndustrialConnectionFormState = {
  name: string;
  connectorType: PlantGeniePlantDataConnectorType;
  pollIntervalMs: string;
  opcuaServerUrl: string;
  opcuaSecurityMode: string;
  opcuaSecurityPolicy: string;
  opcuaAuthMode: string;
  opcuaUsername: string;
  opcuaPassword: string;
  opcuaSessionTimeoutMs: string;
  opcuaBrowseRootNodeId: string;
  opcuaSelectedNodes: OpcuaSelectedNodeMapping[];
  opcuaTrustListNames: string[];
  opcuaTrustListPems: string[];
  opcuaClientCertificateName: string;
  opcuaClientCertificatePem: string;
  opcuaClientPrivateKeyName: string;
  opcuaClientPrivateKeyPem: string;
  opcuaClientPrivateKeyPassword: string;
  opcuaNodeConfig: string;
  mqttBrokerUrl: string;
  mqttTopic: string;
  mqttClientId: string;
  mqttUsername: string;
  mqttPassword: string;
  mqttQos: string;
  mqttKeepAlive: string;
  mqttTlsEnabled: boolean;
  mqttTlsCertificateName: string;
  mqttTlsCertificatePem: string;
  sqlDbType: string;
  sqlHost: string;
  sqlPort: string;
  sqlDatabase: string;
  sqlUsername: string;
  sqlPassword: string;
  sqlSslEnabled: boolean;
  sqlPoolSize: string;
  sqlQueryMode: string;
  sqlRefreshMode: string;
  sqlTableSchema: string;
  sqlTableName: string;
  sqlCustomQuery: string;
  sqlTimestampColumn: string;
  sqlStateColumn: string;
  sqlQualityColumn: string;
  sqlTagMappings: SqlTagMapping[];
  modbusHost: string;
  modbusPort: string;
  modbusUnitId: string;
  modbusTimeoutMs: string;
  modbusRetryAttempts: string;
  modbusAutoReconnect: boolean;
  modbusBatchRead: boolean;
  modbusMaxRegistersPerRequest: string;
  modbusEnableWrite: boolean;
  modbusFunctionCode: string;
  modbusConfirmBeforeWrite: boolean;
  modbusWriteRateLimitMs: string;
  modbusTagMappings: ModbusTagMapping[];
  historianSubtype: string;
  historianGenericMode: string;
  historianPiServerUrl: string;
  historianAfServer: string;
  historianAfDatabase: string;
  historianAuthenticationMode: string;
  historianUsername: string;
  historianPassword: string;
  historianToken: string;
  historianRetrievalMode: string;
  historianTimeRangeValue: string;
  historianTimeRangeUnit: string;
  historianSamplingInterval: string;
  historianCacheEnabled: boolean;
  historianMaxDataPoints: string;
  historianTagMappings: HistorianTagMapping[];
  historianSearchQuery: string;
  historianDbType: string;
  historianHost: string;
  historianPort: string;
  historianDatabase: string;
  historianQuery: string;
  historianSslEnabled: boolean;
  historianEndpointUrl: string;
  historianArrayPath: string;
  historianTimeoutMs: string;
  historianTimestampField: string;
  historianTagField: string;
  historianValueField: string;
};

export type IndustrialConnectionFieldErrors = Partial<Record<keyof IndustrialConnectionFormState, string>>;

export type OpcuaSelectedNodeMapping = {
  nodeId: string;
  browseName: string;
  displayName: string;
  nodeClass: string;
  tag: string;
};

export type SqlTagMapping = {
  sourceColumn: string;
  targetTag: string;
};

export type ModbusTagMapping = {
  registerType: string;
  address: string;
  quantity: string;
  dataType: string;
  endianness: string;
  wordSwap: boolean;
  internalTag: string;
  multiplier: string;
  offset: string;
  engineeringUnits: string;
  writable: boolean;
};

export type HistorianTagMapping = {
  webId: string;
  displayPath: string;
  manualPath: string;
  internalTag: string;
};

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
  { value: "modbus_tcp", label: "Modbus TCP" },
  { value: "historian", label: "Historian" },
];

export const MQTT_QOS_OPTIONS = [
  { value: "0", label: "0" },
  { value: "1", label: "1" },
  { value: "2", label: "2" },
] as const;

export const OPCUA_SECURITY_MODE_OPTIONS = [
  { value: "none", label: "None" },
  { value: "sign", label: "Sign" },
  { value: "sign_and_encrypt", label: "Sign and Encrypt" },
] as const;

export const OPCUA_SECURITY_POLICY_OPTIONS = [
  { value: "basic256sha256", label: "Basic256Sha256" },
  { value: "aes128sha256rsaoaep", label: "Aes128Sha256RsaOaep" },
  { value: "aes256sha256rsapss", label: "Aes256Sha256RsaPss" },
] as const;

export const OPCUA_AUTH_MODE_OPTIONS = [
  { value: "anonymous", label: "Anonymous" },
  { value: "username_password", label: "Username / Password" },
  { value: "certificate", label: "Certificate" },
] as const;

export const SQL_DB_TYPE_OPTIONS = [
  { value: "postgresql", label: "PostgreSQL" },
  { value: "mysql", label: "MySQL" },
  { value: "sqlserver", label: "SQL Server" },
] as const;

export const SQL_QUERY_MODE_OPTIONS = [
  { value: "table", label: "Table Select" },
  { value: "custom_query", label: "Custom Query" },
] as const;

export const SQL_REFRESH_MODE_OPTIONS = [
  { value: "latest_row", label: "Latest Row" },
  { value: "full_snapshot", label: "Full Snapshot" },
] as const;

export const MODBUS_REGISTER_TYPE_OPTIONS = [
  { value: "coil", label: "Coil" },
  { value: "discrete_input", label: "Discrete Input" },
  { value: "holding_register", label: "Holding Register" },
  { value: "input_register", label: "Input Register" },
] as const;

export const MODBUS_DATA_TYPE_OPTIONS = [
  { value: "bool", label: "Bool" },
  { value: "uint16", label: "UInt16" },
  { value: "int16", label: "Int16" },
  { value: "uint32", label: "UInt32" },
  { value: "int32", label: "Int32" },
  { value: "float32", label: "Float32" },
  { value: "uint64", label: "UInt64" },
  { value: "int64", label: "Int64" },
  { value: "float64", label: "Float64" },
  { value: "string", label: "String" },
] as const;

export const MODBUS_ENDIANNESS_OPTIONS = [
  { value: "big", label: "Big Endian" },
  { value: "little", label: "Little Endian" },
] as const;

export const MODBUS_FUNCTION_CODE_OPTIONS = [
  { value: "fc5", label: "FC5" },
  { value: "fc6", label: "FC6" },
  { value: "fc16", label: "FC16" },
] as const;

export const HISTORIAN_SUBTYPE_OPTIONS = [
  { value: "osisoft_pi", label: "OSIsoft PI" },
  { value: "generic_timeseries", label: "Generic Time-Series" },
] as const;

export const HISTORIAN_GENERIC_MODE_OPTIONS = [
  { value: "sql", label: "SQL-based" },
  { value: "rest", label: "REST-based" },
] as const;

export const HISTORIAN_AUTH_MODE_OPTIONS = [
  { value: "anonymous", label: "Anonymous" },
  { value: "basic", label: "Basic" },
  { value: "bearer", label: "Bearer Token" },
] as const;

export const HISTORIAN_RETRIEVAL_MODE_OPTIONS = [
  { value: "snapshot", label: "Snapshot" },
  { value: "recorded", label: "Recorded" },
  { value: "interpolated", label: "Interpolated" },
  { value: "summary", label: "Summary" },
] as const;

export const HISTORIAN_TIME_RANGE_UNIT_OPTIONS = [
  { value: "minutes", label: "Minutes" },
  { value: "hours", label: "Hours" },
  { value: "days", label: "Days" },
] as const;

const CONNECTION_TYPE_ALIASES: Record<string, PlantGeniePlantDataConnectorType> = {
  opcua: "opcua",
  "opc ua": "opcua",
  mqtt: "mqtt",
  sql: "sql",
  "sql / historian": "sql",
  historian: "historian",
  "time-series": "historian",
  "time series": "historian",
  historian_connector: "historian",
  modbus_tcp: "modbus_tcp",
  modbus: "modbus_tcp",
  "modbus tcp": "modbus_tcp",
};

const OPCUA_URL_PATTERN = /^(opc\.tcp|http|https):\/\/[^\s/]+/i;
const MQTT_URL_PATTERN = /^(mqtt|mqtts):\/\/[^\s/]+/i;

type SQLQueryConfig = {
  dbType: string;
  sslEnabled: boolean;
  poolSize: number;
  queryMode: string;
  refreshMode: string;
  tableSchema: string | null;
  tableName: string | null;
  customQuery: string | null;
  timestampColumn: string | null;
  stateColumn: string | null;
  qualityColumn: string | null;
  tagMappings: SqlTagMapping[];
};

export const buildDefaultMqttClientId = (): string => {
  const cryptoApi = typeof globalThis !== "undefined" ? globalThis.crypto : undefined;
  const suffix = cryptoApi && typeof cryptoApi.randomUUID === "function"
    ? cryptoApi.randomUUID().split("-")[0]
    : Math.random().toString(36).slice(2, 10);
  return `industrypath-mqtt-${suffix}`;
};

export const buildDefaultOpcuaTargetTag = (value: { browseName?: string | null; displayName?: string | null; nodeId?: string | null }): string => {
  const candidate = String(value.displayName || value.browseName || value.nodeId || "").trim();
  if (!candidate) {
    return "";
  }
  const compact = candidate.split(/[./]/).filter(Boolean).at(-1) || candidate;
  return compact.replace(/\s+/g, "_");
};

export const buildDefaultSqlPort = (dbType: string): string => {
  if (dbType === "mysql") {
    return "3306";
  }
  if (dbType === "sqlserver") {
    return "1433";
  }
  return "5432";
};

export const buildDefaultSqlTag = (value: { sourceColumn?: string | null }): string => {
  const sourceColumn = String(value.sourceColumn || "").trim();
  return sourceColumn.replace(/\s+/g, "_");
};

export const buildDefaultModbusTag = (value: { registerType?: string | null; address?: string | number | null }): string => {
  const registerType = String(value.registerType || "holding_register").trim().toLowerCase();
  const address = String(value.address ?? "").trim();
  return `${registerType}_${address || "0"}`;
};

export const buildDefaultHistorianTag = (value: { displayPath?: string | null; manualPath?: string | null }): string => {
  const source = String(value.displayPath || value.manualPath || "").trim();
  if (!source) {
    return "";
  }
  return source
    .split(/[\\|/]/)
    .filter(Boolean)
    .at(-1)
    ?.replace(/\s+/g, "_") ?? "";
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

const normalizeOpcuaSelectedNode = (value: unknown): OpcuaSelectedNodeMapping | null => {
  if (typeof value === "string") {
    const nodeId = value.trim();
    if (!nodeId) {
      return null;
    }
    const tag = buildDefaultOpcuaTargetTag({ nodeId });
    return {
      nodeId,
      browseName: nodeId,
      displayName: nodeId,
      nodeClass: "Variable",
      tag,
    };
  }

  if (!value || typeof value !== "object") {
    return null;
  }

  const raw = value as Record<string, unknown>;
  const nodeId = String(raw.node_id ?? raw.nodeId ?? raw.id ?? "").trim();
  if (!nodeId) {
    return null;
  }

  const browseName = String(raw.browse_name ?? raw.browseName ?? raw.name ?? nodeId).trim() || nodeId;
  const displayName = String(raw.display_name ?? raw.displayName ?? browseName).trim() || browseName;
  const nodeClass = String(raw.node_class ?? raw.nodeClass ?? "Variable").trim() || "Variable";
  const tag = String(raw.tag ?? buildDefaultOpcuaTargetTag({ browseName, displayName, nodeId })).trim();

  return {
    nodeId,
    browseName,
    displayName,
    nodeClass,
    tag: tag || buildDefaultOpcuaTargetTag({ browseName, displayName, nodeId }),
  };
};

export const serializeOpcuaSubscriptionConfig = (selectedNodes: OpcuaSelectedNodeMapping[], browseRootNodeId?: string | null): string => {
  return JSON.stringify(
    {
      root_node_id: browseRootNodeId?.trim() || null,
      nodes: selectedNodes.map((node) => ({
        node_id: node.nodeId,
        browse_name: node.browseName,
        display_name: node.displayName,
        node_class: node.nodeClass,
        tag: node.tag,
      })),
    },
    null,
    2
  );
};

const parseSubscriptionConfig = (value: string): { parsed: unknown; nodeIds: string[]; selectedNodes: OpcuaSelectedNodeMapping[]; rootNodeId: string | null } => {
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
    const selectedNodes = parsed.map((item) => normalizeOpcuaSelectedNode(item)).filter((item): item is OpcuaSelectedNodeMapping => item !== null);
    return {
      parsed,
      nodeIds: selectedNodes.map((item) => item.nodeId),
      selectedNodes,
      rootNodeId: null,
    };
  }

  if (parsed && typeof parsed === "object") {
    const objectValue = parsed as Record<string, unknown>;
    const nodesValue = objectValue.nodes ?? objectValue.selected_nodes ?? objectValue.subscriptions ?? objectValue.node_ids ?? objectValue.nodeIds;
    if (Array.isArray(nodesValue)) {
      const selectedNodes = nodesValue.map((item) => normalizeOpcuaSelectedNode(item)).filter((item): item is OpcuaSelectedNodeMapping => item !== null);
      if (selectedNodes.length > 0) {
        return {
          parsed,
          nodeIds: selectedNodes.map((item) => item.nodeId),
          selectedNodes,
          rootNodeId: String(objectValue.root_node_id ?? objectValue.rootNodeId ?? "").trim() || null,
        };
      }
    }
  }

  throw new Error("Subscription / Node config must describe at least one node selection.");
};

export const resolveOpcuaSelectedNodes = (form: Pick<IndustrialConnectionFormState, "opcuaSelectedNodes" | "opcuaNodeConfig">): OpcuaSelectedNodeMapping[] => {
  if (Array.isArray(form.opcuaSelectedNodes) && form.opcuaSelectedNodes.length > 0) {
    return form.opcuaSelectedNodes
      .map((item) => normalizeOpcuaSelectedNode(item))
      .filter((item): item is OpcuaSelectedNodeMapping => item !== null);
  }

  return parseSubscriptionConfig(form.opcuaNodeConfig).selectedNodes;
};

const normalizeSqlTagMappings = (value: unknown): SqlTagMapping[] => {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => {
      if (!item || typeof item !== "object") {
        return null;
      }

      const raw = item as Record<string, unknown>;
      const sourceColumn = String(raw.sourceColumn ?? raw.source_column ?? "").trim();
      const targetTag = String(raw.targetTag ?? raw.target_tag ?? "").trim();
      if (!sourceColumn || !targetTag) {
        return null;
      }

      return { sourceColumn, targetTag };
    })
    .filter((item): item is SqlTagMapping => item !== null);
};

export const buildSqlQueryConfig = (form: Pick<IndustrialConnectionFormState,
  "sqlDbType"
  | "sqlSslEnabled"
  | "sqlPoolSize"
  | "sqlQueryMode"
  | "sqlRefreshMode"
  | "sqlTableSchema"
  | "sqlTableName"
  | "sqlCustomQuery"
  | "sqlTimestampColumn"
  | "sqlStateColumn"
  | "sqlQualityColumn"
  | "sqlTagMappings"
>): SQLQueryConfig => {
  return {
    dbType: form.sqlDbType.trim() || "postgresql",
    sslEnabled: Boolean(form.sqlSslEnabled),
    poolSize: Number.parseInt(form.sqlPoolSize, 10),
    queryMode: form.sqlQueryMode.trim() || "table",
    refreshMode: form.sqlRefreshMode.trim() || "latest_row",
    tableSchema: form.sqlTableSchema.trim() || null,
    tableName: form.sqlTableName.trim() || null,
    customQuery: form.sqlCustomQuery.trim() || null,
    timestampColumn: form.sqlTimestampColumn.trim() || null,
    stateColumn: form.sqlStateColumn.trim() || null,
    qualityColumn: form.sqlQualityColumn.trim() || null,
    tagMappings: normalizeSqlTagMappings(form.sqlTagMappings),
  };
};

const normalizeModbusTagMappings = (value: unknown): ModbusTagMapping[] => {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => {
      if (!item || typeof item !== "object") {
        return null;
      }

      const raw = item as Record<string, unknown>;
      const registerType = String(raw.registerType ?? raw.register_type ?? "").trim();
      const address = String(raw.address ?? "").trim();
      const quantity = String(raw.quantity ?? "").trim();
      const dataType = String(raw.dataType ?? raw.data_type ?? "").trim();
      const endianness = String(raw.endianness ?? "big").trim();
      const internalTag = String(raw.internalTag ?? raw.internal_tag ?? "").trim();
      if (!registerType || !address || !quantity || !dataType || !internalTag) {
        return null;
      }

      return {
        registerType,
        address,
        quantity,
        dataType,
        endianness,
        wordSwap: Boolean(raw.wordSwap ?? raw.word_swap),
        internalTag,
        multiplier: String(raw.multiplier ?? "1").trim() || "1",
        offset: String(raw.offset ?? "0").trim() || "0",
        engineeringUnits: String(raw.engineeringUnits ?? raw.engineering_units ?? "").trim(),
        writable: Boolean(raw.writable),
      } satisfies ModbusTagMapping;
    })
    .filter((item): item is ModbusTagMapping => item !== null);
};

const normalizeHistorianTagMappings = (value: unknown): HistorianTagMapping[] => {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => {
      if (!item || typeof item !== "object") {
        return null;
      }
      const raw = item as Record<string, unknown>;
      const webId = String(raw.webId ?? raw.web_id ?? "").trim();
      const displayPath = String(raw.displayPath ?? raw.display_path ?? "").trim();
      const manualPath = String(raw.manualPath ?? raw.manual_path ?? "").trim();
      const internalTag = String(raw.internalTag ?? raw.internal_tag ?? "").trim();
      if (!internalTag || (!webId && !manualPath)) {
        return null;
      }
      return {
        webId,
        displayPath,
        manualPath,
        internalTag,
      } satisfies HistorianTagMapping;
    })
    .filter((item): item is HistorianTagMapping => item !== null);
};

export const buildModbusConnectorConfig = (form: Pick<IndustrialConnectionFormState,
  "modbusHost"
  | "modbusPort"
  | "modbusUnitId"
  | "modbusTimeoutMs"
  | "modbusRetryAttempts"
  | "modbusAutoReconnect"
  | "modbusBatchRead"
  | "modbusMaxRegistersPerRequest"
  | "modbusEnableWrite"
  | "modbusFunctionCode"
  | "modbusConfirmBeforeWrite"
  | "modbusWriteRateLimitMs"
  | "modbusTagMappings"
>): Record<string, unknown> => {
  return {
    host: form.modbusHost.trim(),
    port: Number.parseInt(form.modbusPort, 10),
    unit_id: Number.parseInt(form.modbusUnitId, 10),
    timeout_ms: Number.parseInt(form.modbusTimeoutMs, 10),
    retry_attempts: Number.parseInt(form.modbusRetryAttempts, 10),
    auto_reconnect: Boolean(form.modbusAutoReconnect),
    batch_read: Boolean(form.modbusBatchRead),
    max_registers_per_request: Number.parseInt(form.modbusMaxRegistersPerRequest, 10),
    enable_write: Boolean(form.modbusEnableWrite),
    write_function_code: form.modbusFunctionCode.trim() || "fc6",
    confirm_before_write: Boolean(form.modbusConfirmBeforeWrite),
    write_rate_limit_ms: Number.parseInt(form.modbusWriteRateLimitMs, 10),
    tag_mappings: normalizeModbusTagMappings(form.modbusTagMappings).map((mapping) => ({
      register_type: mapping.registerType,
      address: Number.parseInt(mapping.address, 10),
      quantity: Number.parseInt(mapping.quantity, 10),
      data_type: mapping.dataType,
      endianness: mapping.endianness,
      word_swap: mapping.wordSwap,
      internal_tag: mapping.internalTag,
      multiplier: Number.parseFloat(mapping.multiplier),
      offset: Number.parseFloat(mapping.offset),
      engineering_units: mapping.engineeringUnits.trim() || null,
      writable: mapping.writable,
    })),
  };
};

export const buildHistorianConnectorConfig = (form: Pick<IndustrialConnectionFormState,
  "pollIntervalMs"
  | "historianSubtype"
  | "historianGenericMode"
  | "historianPiServerUrl"
  | "historianAfServer"
  | "historianAfDatabase"
  | "historianAuthenticationMode"
  | "historianUsername"
  | "historianRetrievalMode"
  | "historianTimeRangeValue"
  | "historianTimeRangeUnit"
  | "historianSamplingInterval"
  | "historianCacheEnabled"
  | "historianMaxDataPoints"
  | "historianTagMappings"
  | "historianDbType"
  | "historianHost"
  | "historianPort"
  | "historianDatabase"
  | "historianQuery"
  | "historianSslEnabled"
  | "historianEndpointUrl"
  | "historianArrayPath"
  | "historianTimeoutMs"
  | "historianTimestampField"
  | "historianTagField"
  | "historianValueField"
>): Record<string, unknown> => {
  const subtype = form.historianSubtype.trim() || "osisoft_pi";
  const baseConfig: Record<string, unknown> = {
    poll_interval_ms: Number.parseInt(form.pollIntervalMs, 10),
    historian_subtype: subtype,
    authentication_mode: form.historianAuthenticationMode.trim() || "anonymous",
    retrieval_mode: form.historianRetrievalMode.trim() || "snapshot",
    time_range_value: Number.parseInt(form.historianTimeRangeValue, 10),
    time_range_unit: form.historianTimeRangeUnit.trim() || "hours",
    sampling_interval: form.historianSamplingInterval.trim() || null,
    cache_enabled: Boolean(form.historianCacheEnabled),
    max_data_points: Number.parseInt(form.historianMaxDataPoints, 10),
  };
  if (subtype === "osisoft_pi") {
    return {
      ...baseConfig,
      pi_server_url: form.historianPiServerUrl.trim(),
      af_server: form.historianAfServer.trim(),
      af_database: form.historianAfDatabase.trim(),
      username: form.historianUsername.trim() || null,
      tag_mappings: normalizeHistorianTagMappings(form.historianTagMappings).map((mapping) => ({
        web_id: mapping.webId || null,
        display_path: mapping.displayPath || null,
        manual_path: mapping.manualPath || null,
        internal_tag: mapping.internalTag,
      })),
    };
  }
  if (form.historianGenericMode === "sql") {
    return {
      ...baseConfig,
      historian_subtype: "generic_timeseries",
      generic_mode: "sql",
      db_type: form.historianDbType.trim() || "postgresql",
      host: form.historianHost.trim(),
      port: Number.parseInt(form.historianPort, 10),
      database: form.historianDatabase.trim(),
      username: form.historianUsername.trim(),
      ssl_enabled: Boolean(form.historianSslEnabled),
      query: form.historianQuery.trim(),
      timestamp_field: form.historianTimestampField.trim(),
      tag_field: form.historianTagField.trim(),
      value_field: form.historianValueField.trim(),
    };
  }
  return {
    ...baseConfig,
    historian_subtype: "generic_timeseries",
    generic_mode: "rest",
    endpoint_url: form.historianEndpointUrl.trim(),
    username: form.historianUsername.trim() || null,
    array_path: form.historianArrayPath.trim() || null,
    timeout_ms: Number.parseInt(form.historianTimeoutMs, 10),
    timestamp_field: form.historianTimestampField.trim(),
    tag_field: form.historianTagField.trim(),
    value_field: form.historianValueField.trim(),
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

    const sessionTimeoutMs = Number.parseInt(form.opcuaSessionTimeoutMs, 10);
    if (!Number.isFinite(sessionTimeoutMs) || sessionTimeoutMs < 1000 || sessionTimeoutMs > 3600000) {
      errors.opcuaSessionTimeoutMs = "Session timeout must be between 1000 and 3600000 ms.";
    }

    if (form.opcuaSecurityMode !== "none" && !form.opcuaSecurityPolicy.trim()) {
      errors.opcuaSecurityPolicy = "Security policy is required when security mode is enabled.";
    }

    if (form.opcuaAuthMode === "username_password" && !form.opcuaUsername.trim()) {
      errors.opcuaUsername = "Username is required for username/password authentication.";
    }

    if (form.opcuaAuthMode === "username_password" && !options.isEditing && !form.opcuaPassword.trim()) {
      errors.opcuaPassword = "Password is required for username/password authentication.";
    }

    const requiresClientCertificate = form.opcuaSecurityMode !== "none" || form.opcuaAuthMode === "certificate";
    if (requiresClientCertificate && !form.opcuaClientCertificateName.trim()) {
      errors.opcuaClientCertificateName = "Client certificate is required for secure OPC UA sessions.";
    }
    if (requiresClientCertificate && !form.opcuaClientPrivateKeyName.trim()) {
      errors.opcuaClientPrivateKeyName = "Client private key is required for secure OPC UA sessions.";
    }

    try {
      const subscription = resolveOpcuaSelectedNodes(form);
      if (subscription.length === 0) {
        errors.opcuaNodeConfig = "Select at least one OPC UA node.";
      }
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
    const qos = Number.parseInt(form.mqttQos, 10);
    if (!Number.isFinite(qos) || qos < 0 || qos > 2) {
      errors.mqttQos = "QoS must be 0, 1, or 2.";
    }
    const keepAlive = Number.parseInt(form.mqttKeepAlive, 10);
    if (!Number.isFinite(keepAlive) || keepAlive < 5 || keepAlive > 3600) {
      errors.mqttKeepAlive = "Keep Alive must be between 5 and 3600 seconds.";
    }
  }

  if (connectorType === "sql") {
    if (!["postgresql", "mysql", "sqlserver"].includes(form.sqlDbType)) {
      errors.sqlDbType = "DB Type must be PostgreSQL, MySQL, or SQL Server.";
    }

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

    const poolSize = Number.parseInt(form.sqlPoolSize, 10);
    if (!Number.isFinite(poolSize) || poolSize < 1 || poolSize > 50) {
      errors.sqlPoolSize = "Pool size must be between 1 and 50.";
    }

    if (!["table", "custom_query"].includes(form.sqlQueryMode)) {
      errors.sqlQueryMode = "Query mode must be Table Select or Custom Query.";
    }

    if (!["latest_row", "full_snapshot"].includes(form.sqlRefreshMode)) {
      errors.sqlRefreshMode = "Refresh mode must be Latest Row or Full Snapshot.";
    }

    if (form.sqlQueryMode === "table" && !form.sqlTableName.trim()) {
      errors.sqlTableName = "Table selection is required.";
    }

    if (form.sqlQueryMode === "custom_query") {
      if (!form.sqlCustomQuery.trim()) {
        errors.sqlCustomQuery = "Custom query is required.";
      } else if (!/^select\b/i.test(form.sqlCustomQuery.trim())) {
        errors.sqlCustomQuery = "Custom query must start with SELECT.";
      }
    }

    if (normalizeSqlTagMappings(form.sqlTagMappings).length === 0) {
      errors.sqlTagMappings = "Add at least one column-to-tag mapping.";
    }
  }

  if (connectorType === "modbus_tcp") {
    if (!form.modbusHost.trim()) {
      errors.modbusHost = "Host is required.";
    }

    const port = Number.parseInt(form.modbusPort, 10);
    if (!Number.isFinite(port) || port < 1 || port > 65535) {
      errors.modbusPort = "Port must be a number between 1 and 65535.";
    }

    const unitId = Number.parseInt(form.modbusUnitId, 10);
    if (!Number.isFinite(unitId) || unitId < 0 || unitId > 255) {
      errors.modbusUnitId = "Unit ID must be between 0 and 255.";
    }

    const timeoutMs = Number.parseInt(form.modbusTimeoutMs, 10);
    if (!Number.isFinite(timeoutMs) || timeoutMs < 100 || timeoutMs > 60000) {
      errors.modbusTimeoutMs = "Timeout must be between 100 and 60000 ms.";
    }

    const retryAttempts = Number.parseInt(form.modbusRetryAttempts, 10);
    if (!Number.isFinite(retryAttempts) || retryAttempts < 0 || retryAttempts > 10) {
      errors.modbusRetryAttempts = "Retry attempts must be between 0 and 10.";
    }

    const maxRegisters = Number.parseInt(form.modbusMaxRegistersPerRequest, 10);
    if (!Number.isFinite(maxRegisters) || maxRegisters < 1 || maxRegisters > 125) {
      errors.modbusMaxRegistersPerRequest = "Max registers per request must be between 1 and 125.";
    }

    if (!MODBUS_FUNCTION_CODE_OPTIONS.some((option) => option.value === form.modbusFunctionCode)) {
      errors.modbusFunctionCode = "Write function code must be FC5, FC6, or FC16.";
    }

    const writeRateLimitMs = Number.parseInt(form.modbusWriteRateLimitMs, 10);
    if (!Number.isFinite(writeRateLimitMs) || writeRateLimitMs < 0 || writeRateLimitMs > 600000) {
      errors.modbusWriteRateLimitMs = "Write rate limit must be between 0 and 600000 ms.";
    }

    const mappings = normalizeModbusTagMappings(form.modbusTagMappings);
    if (mappings.length === 0) {
      errors.modbusTagMappings = "Add at least one Modbus register mapping.";
    } else {
      const invalidMapping = mappings.find((mapping) => {
        const address = Number.parseInt(mapping.address, 10);
        const quantity = Number.parseInt(mapping.quantity, 10);
        const multiplier = Number.parseFloat(mapping.multiplier);
        const offset = Number.parseFloat(mapping.offset);
        if (!MODBUS_REGISTER_TYPE_OPTIONS.some((option) => option.value === mapping.registerType)) {
          return true;
        }
        if (!MODBUS_DATA_TYPE_OPTIONS.some((option) => option.value === mapping.dataType)) {
          return true;
        }
        if (!MODBUS_ENDIANNESS_OPTIONS.some((option) => option.value === mapping.endianness)) {
          return true;
        }
        if (!Number.isFinite(address) || address < 0 || address > 65535) {
          return true;
        }
        if (!Number.isFinite(quantity) || quantity < 1 || quantity > 125) {
          return true;
        }
        if (!Number.isFinite(multiplier) || !Number.isFinite(offset)) {
          return true;
        }
        if ((mapping.registerType === "coil" || mapping.registerType === "discrete_input") && mapping.dataType !== "bool") {
          return true;
        }
        if (mapping.writable && mapping.registerType !== "coil" && mapping.registerType !== "holding_register") {
          return true;
        }
        return false;
      });
      if (invalidMapping) {
        errors.modbusTagMappings = "Each Modbus mapping must include a valid register config, datatype, and internal tag.";
      }
      const writableMappings = mappings.filter((mapping) => mapping.writable);
      if (writableMappings.length > 0) {
        if (form.modbusFunctionCode === "fc5" && writableMappings.some((mapping) => mapping.registerType !== "coil")) {
          errors.modbusFunctionCode = "FC5 can only be used with writable coil mappings.";
        }
        if ((form.modbusFunctionCode === "fc6" || form.modbusFunctionCode === "fc16") && writableMappings.some((mapping) => mapping.registerType !== "holding_register")) {
          errors.modbusFunctionCode = "FC6 and FC16 can only be used with writable holding register mappings.";
        }
      }
    }
  }

  if (connectorType === "historian") {
    if (!HISTORIAN_SUBTYPE_OPTIONS.some((option) => option.value === form.historianSubtype)) {
      errors.historianSubtype = "Select a historian subtype.";
    }
    if (!HISTORIAN_RETRIEVAL_MODE_OPTIONS.some((option) => option.value === form.historianRetrievalMode)) {
      errors.historianRetrievalMode = "Select a valid retrieval mode.";
    }
    const timeRangeValue = Number.parseInt(form.historianTimeRangeValue, 10);
    if (!Number.isFinite(timeRangeValue) || timeRangeValue < 1 || timeRangeValue > 10000) {
      errors.historianTimeRangeValue = "Time range must be between 1 and 10000.";
    }
    if (!HISTORIAN_TIME_RANGE_UNIT_OPTIONS.some((option) => option.value === form.historianTimeRangeUnit)) {
      errors.historianTimeRangeUnit = "Select a valid time range unit.";
    }
    const maxDataPoints = Number.parseInt(form.historianMaxDataPoints, 10);
    if (!Number.isFinite(maxDataPoints) || maxDataPoints < 1 || maxDataPoints > 5000) {
      errors.historianMaxDataPoints = "Max data points must be between 1 and 5000.";
    }
    if (!HISTORIAN_AUTH_MODE_OPTIONS.some((option) => option.value === form.historianAuthenticationMode)) {
      errors.historianAuthenticationMode = "Select a valid authentication mode.";
    }
    if (form.historianAuthenticationMode === "basic" && !options.isEditing && !form.historianPassword.trim()) {
      errors.historianPassword = "Password is required for basic authentication.";
    }
    if (form.historianAuthenticationMode === "bearer" && !options.isEditing && !form.historianToken.trim()) {
      errors.historianToken = "Token is required for bearer authentication.";
    }
    if (form.historianSubtype === "osisoft_pi") {
      if (!form.historianPiServerUrl.trim()) {
        errors.historianPiServerUrl = "PI Server URL is required.";
      }
      if (!form.historianAfServer.trim()) {
        errors.historianAfServer = "AF Server is required.";
      }
      if (!form.historianAfDatabase.trim()) {
        errors.historianAfDatabase = "AF Database is required.";
      }
      if (normalizeHistorianTagMappings(form.historianTagMappings).length === 0) {
        errors.historianTagMappings = "Add at least one PI tag mapping or manual path.";
      }
    } else {
      if (!HISTORIAN_GENERIC_MODE_OPTIONS.some((option) => option.value === form.historianGenericMode)) {
        errors.historianGenericMode = "Select a generic historian mode.";
      }
      if (!form.historianTimestampField.trim()) {
        errors.historianTimestampField = "Timestamp field is required.";
      }
      if (!form.historianTagField.trim()) {
        errors.historianTagField = "Tag field is required.";
      }
      if (!form.historianValueField.trim()) {
        errors.historianValueField = "Value field is required.";
      }
      if (form.historianGenericMode === "sql") {
        if (!form.historianHost.trim()) {
          errors.historianHost = "Host is required.";
        }
        const port = Number.parseInt(form.historianPort, 10);
        if (!Number.isFinite(port) || port < 1 || port > 65535) {
          errors.historianPort = "Port must be between 1 and 65535.";
        }
        if (!form.historianDatabase.trim()) {
          errors.historianDatabase = "Database is required.";
        }
        if (!form.historianUsername.trim()) {
          errors.historianUsername = "Username is required.";
        }
        if (!form.historianQuery.trim()) {
          errors.historianQuery = "Query is required.";
        } else if (!/^select\b/i.test(form.historianQuery.trim())) {
          errors.historianQuery = "Query must start with SELECT.";
        }
      } else {
        if (!form.historianEndpointUrl.trim()) {
          errors.historianEndpointUrl = "Endpoint URL is required.";
        }
        const timeoutMs = Number.parseInt(form.historianTimeoutMs, 10);
        if (!Number.isFinite(timeoutMs) || timeoutMs < 100 || timeoutMs > 60000) {
          errors.historianTimeoutMs = "Timeout must be between 100 and 60000 ms.";
        }
      }
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
    const selectedNodes = resolveOpcuaSelectedNodes(form);
    return {
      name: form.name.trim(),
      connector_type: "opcua",
      poll_interval_ms: pollIntervalMs,
      config: {
        server_url: form.opcuaServerUrl.trim(),
        security_mode: form.opcuaSecurityMode === "none" ? null : form.opcuaSecurityMode,
        security_policy: form.opcuaSecurityMode === "none" ? null : form.opcuaSecurityPolicy.trim() || null,
        authentication_mode: form.opcuaAuthMode.trim() || "anonymous",
        username: form.opcuaAuthMode === "username_password" ? form.opcuaUsername.trim() || null : null,
        session_timeout_ms: Number.parseInt(form.opcuaSessionTimeoutMs, 10),
        browse_root_node_id: form.opcuaBrowseRootNodeId.trim() || null,
        trust_list_names: form.opcuaTrustListNames,
        client_certificate_name: form.opcuaClientCertificateName.trim() || null,
        client_private_key_name: form.opcuaClientPrivateKeyName.trim() || null,
        subscription_config: {
          root_node_id: form.opcuaBrowseRootNodeId.trim() || null,
          nodes: selectedNodes.map((node) => ({
            node_id: node.nodeId,
            browse_name: node.browseName,
            display_name: node.displayName,
            node_class: node.nodeClass,
            tag: node.tag.trim() || buildDefaultOpcuaTargetTag(node),
          })),
        },
        node_ids: selectedNodes.map((node) => node.nodeId),
      },
      secrets: {
        ...(form.opcuaAuthMode === "username_password" && form.opcuaPassword.trim() ? { password: form.opcuaPassword.trim() } : {}),
        ...(form.opcuaTrustListPems.length > 0 ? { trust_list_pems: form.opcuaTrustListPems } : {}),
        ...(form.opcuaClientCertificatePem.trim() ? { client_certificate_pem: form.opcuaClientCertificatePem.trim() } : {}),
        ...(form.opcuaClientPrivateKeyPem.trim() ? { client_private_key_pem: form.opcuaClientPrivateKeyPem.trim() } : {}),
        ...(form.opcuaClientPrivateKeyPassword.trim() ? { client_private_key_password: form.opcuaClientPrivateKeyPassword.trim() } : {}),
      },
    };
  }

  if (connectorType === "mqtt") {
    const clientId = form.mqttClientId.trim() || buildDefaultMqttClientId();
    return {
      name: form.name.trim(),
      connector_type: "mqtt",
      poll_interval_ms: pollIntervalMs,
      config: {
        broker_url: form.mqttBrokerUrl.trim(),
        topic: form.mqttTopic.trim(),
        client_id: clientId,
        username: form.mqttUsername.trim() || null,
        qos: Number.parseInt(form.mqttQos, 10),
        keep_alive: Number.parseInt(form.mqttKeepAlive, 10),
        tls_enabled: form.mqttTlsEnabled,
        certificate_name: form.mqttTlsEnabled ? form.mqttTlsCertificateName.trim() || null : null,
      },
      secrets: {
        ...(form.mqttPassword.trim() ? { password: form.mqttPassword.trim() } : {}),
        ...(form.mqttTlsEnabled && form.mqttTlsCertificatePem.trim()
          ? { ca_certificate_pem: form.mqttTlsCertificatePem.trim() }
          : {}),
      },
    };
  }

  if (connectorType === "modbus_tcp") {
    return {
      name: form.name.trim(),
      connector_type: "modbus_tcp",
      poll_interval_ms: pollIntervalMs,
      config: buildModbusConnectorConfig(form),
      secrets: {},
    };
  }

  if (connectorType === "historian") {
    return {
      name: form.name.trim(),
      connector_type: "historian",
      poll_interval_ms: pollIntervalMs,
      config: buildHistorianConnectorConfig(form),
      secrets: {
        ...(form.historianAuthenticationMode === "basic" && form.historianPassword.trim() ? { password: form.historianPassword.trim() } : {}),
        ...(form.historianAuthenticationMode === "bearer" && form.historianToken.trim() ? { token: form.historianToken.trim() } : {}),
      },
    };
  }

  const queryConfig = buildSqlQueryConfig(form);
  return {
    name: form.name.trim(),
    connector_type: "sql",
    poll_interval_ms: pollIntervalMs,
    config: {
      db_type: queryConfig.dbType,
      host: form.sqlHost.trim(),
      port: Number.parseInt(form.sqlPort, 10),
      database: form.sqlDatabase.trim(),
      username: form.sqlUsername.trim(),
      ssl_enabled: queryConfig.sslEnabled,
      pool_size: queryConfig.poolSize,
      query_mode: queryConfig.queryMode,
      refresh_mode: queryConfig.refreshMode,
      table_schema: queryConfig.tableSchema,
      table_name: queryConfig.tableName,
      custom_query: queryConfig.customQuery,
      timestamp_column: queryConfig.timestampColumn,
      state_column: queryConfig.stateColumn,
      quality_column: queryConfig.qualityColumn,
      tag_mappings: queryConfig.tagMappings.map((mapping) => ({
        source_column: mapping.sourceColumn,
        target_tag: mapping.targetTag,
      })),
    },
    secrets: form.sqlPassword.trim() ? { password: form.sqlPassword.trim() } : {},
  };
};