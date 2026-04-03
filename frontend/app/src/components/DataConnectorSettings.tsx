import { CheckCircle2, ChevronDown, ChevronRight, DatabaseZap, FolderTree, LoaderCircle, PlugZap, Plus, ShieldCheck, Trash2, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { toast } from "react-hot-toast";

import {
  activatePlantGeniePlantDataConnector,
  browsePlantGeniePlantDataHistorian,
  browsePlantGeniePlantDataOpcua,
  createPlantGeniePlantDataConnector,
  deactivatePlantGeniePlantDataConnector,
  deletePlantGeniePlantDataConnector,
  getPlantGeniePlantDataConnectors,
  previewPlantGeniePlantDataHistorian,
  previewPlantGeniePlantDataModbus,
  getPlantGeniePlantDataSqlSchema,
  previewPlantGeniePlantDataSql,
  testPlantGeniePlantDataConnector,
  updatePlantGeniePlantDataConnector,
  type PlantGeniePlantDataConnector,
  type PlantGeniePlantDataHistorianBrowseItem,
  type PlantGeniePlantDataHistorianPreviewResponse,
  type PlantGeniePlantDataModbusPreviewResponse,
  type PlantGeniePlantDataOpcuaBrowseNode,
  type PlantGeniePlantDataSqlColumn,
  type PlantGeniePlantDataSqlPreviewResponse,
  type PlantGeniePlantDataSqlTable,
} from "../services/api";
import {
  buildDefaultModbusTag,
  buildDefaultHistorianTag,
  buildHistorianConnectorConfig,
  buildModbusConnectorConfig,
  buildDefaultSqlPort,
  buildDefaultSqlTag,
  buildDefaultMqttClientId,
  buildDefaultOpcuaTargetTag,
  buildSqlQueryConfig,
  HISTORIAN_AUTH_MODE_OPTIONS,
  HISTORIAN_GENERIC_MODE_OPTIONS,
  HISTORIAN_RETRIEVAL_MODE_OPTIONS,
  HISTORIAN_SUBTYPE_OPTIONS,
  HISTORIAN_TIME_RANGE_UNIT_OPTIONS,
  INDUSTRIAL_CONNECTION_TYPE_OPTIONS,
  MODBUS_DATA_TYPE_OPTIONS,
  MODBUS_ENDIANNESS_OPTIONS,
  MODBUS_FUNCTION_CODE_OPTIONS,
  MODBUS_REGISTER_TYPE_OPTIONS,
  MQTT_QOS_OPTIONS,
  OPCUA_AUTH_MODE_OPTIONS,
  OPCUA_SECURITY_MODE_OPTIONS,
  OPCUA_SECURITY_POLICY_OPTIONS,
  SQL_DB_TYPE_OPTIONS,
  SQL_QUERY_MODE_OPTIONS,
  SQL_REFRESH_MODE_OPTIONS,
  mapIndustrialConnectorFormToRequest,
  resolveOpcuaSelectedNodes,
  serializeOpcuaSubscriptionConfig,
  validateIndustrialConnectorForm,
  type IndustrialConnectionFieldErrors,
  type HistorianTagMapping,
  type IndustrialConnectionFormState,
  type ModbusTagMapping,
  type OpcuaSelectedNodeMapping,
  type SqlTagMapping,
} from "./plantGenie/industrialConnectorPayload";
import PlantGenieAIBindingPanel from "./PlantGenieAIBindingPanel";

type OpcuaTreeNode = PlantGeniePlantDataOpcuaBrowseNode & {
  children?: OpcuaTreeNode[];
  childrenLoaded?: boolean;
};

const EMPTY_FORM: IndustrialConnectionFormState = {
  name: "",
  connectorType: "opcua",
  pollIntervalMs: "5000",
  opcuaServerUrl: "",
  opcuaSecurityMode: "none",
  opcuaSecurityPolicy: "",
  opcuaAuthMode: "anonymous",
  opcuaUsername: "",
  opcuaPassword: "",
  opcuaSessionTimeoutMs: "60000",
  opcuaBrowseRootNodeId: "i=85",
  opcuaSelectedNodes: [],
  opcuaTrustListNames: [],
  opcuaTrustListPems: [],
  opcuaClientCertificateName: "",
  opcuaClientCertificatePem: "",
  opcuaClientPrivateKeyName: "",
  opcuaClientPrivateKeyPem: "",
  opcuaClientPrivateKeyPassword: "",
  opcuaNodeConfig: serializeOpcuaSubscriptionConfig([], "i=85"),
  mqttBrokerUrl: "mqtt://broker.example.com:1883",
  mqttTopic: "",
  mqttClientId: buildDefaultMqttClientId(),
  mqttUsername: "",
  mqttPassword: "",
  mqttQos: "0",
  mqttKeepAlive: "30",
  mqttTlsEnabled: false,
  mqttTlsCertificateName: "",
  mqttTlsCertificatePem: "",
  sqlDbType: "postgresql",
  sqlHost: "",
  sqlPort: "5432",
  sqlDatabase: "",
  sqlUsername: "",
  sqlPassword: "",
  sqlSslEnabled: false,
  sqlPoolSize: "5",
  sqlQueryMode: "table",
  sqlRefreshMode: "latest_row",
  sqlTableSchema: "public",
  sqlTableName: "",
  sqlCustomQuery: "SELECT * FROM live_signals",
  sqlTimestampColumn: "timestamp",
  sqlStateColumn: "",
  sqlQualityColumn: "",
  sqlTagMappings: [],
  modbusHost: "",
  modbusPort: "502",
  modbusUnitId: "1",
  modbusTimeoutMs: "5000",
  modbusRetryAttempts: "2",
  modbusAutoReconnect: true,
  modbusBatchRead: true,
  modbusMaxRegistersPerRequest: "120",
  modbusEnableWrite: false,
  modbusFunctionCode: "fc6",
  modbusConfirmBeforeWrite: true,
  modbusWriteRateLimitMs: "1000",
  modbusTagMappings: [],
  historianSubtype: "osisoft_pi",
  historianGenericMode: "sql",
  historianPiServerUrl: "",
  historianAfServer: "",
  historianAfDatabase: "",
  historianAuthenticationMode: "anonymous",
  historianUsername: "",
  historianPassword: "",
  historianToken: "",
  historianRetrievalMode: "snapshot",
  historianTimeRangeValue: "1",
  historianTimeRangeUnit: "hours",
  historianSamplingInterval: "5m",
  historianCacheEnabled: true,
  historianMaxDataPoints: "500",
  historianTagMappings: [],
  historianSearchQuery: "",
  historianDbType: "postgresql",
  historianHost: "",
  historianPort: "5432",
  historianDatabase: "",
  historianQuery: "SELECT timestamp, tag, value FROM historian_points ORDER BY timestamp DESC LIMIT 500",
  historianSslEnabled: false,
  historianEndpointUrl: "",
  historianArrayPath: "items",
  historianTimeoutMs: "15000",
  historianTimestampField: "timestamp",
  historianTagField: "tag",
  historianValueField: "value",
};

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

const formatConnectorType = (value: PlantGeniePlantDataConnector["connector_type"]): string => {
  if (value === "opcua") {
    return "OPC UA";
  }
  if (value === "mqtt") {
    return "MQTT";
  }
  if (value === "modbus_tcp") {
    return "Modbus TCP";
  }
  if (value === "historian") {
    return "Historian";
  }
  return "SQL / Historian";
};

const normalizeErrorMessage = (error: unknown, fallback: string): string => {
  return error instanceof Error && error.message ? error.message : fallback;
};

const readFileAsText = async (file: File): Promise<string> => {
  return await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(typeof reader.result === "string" ? reader.result : "");
    reader.onerror = () => reject(new Error(`Failed to read ${file.name}`));
    reader.readAsText(file);
  });
};

const formatConnectorRuntimeStatus = (connector: PlantGeniePlantDataConnector | null): string => {
  if (!connector) {
    return "Draft";
  }
  if (connector.runtime.last_error) {
    return "Error";
  }
  if (connector.runtime.enabled && connector.runtime.running && connector.health.healthy) {
    return "Connected";
  }
  if (connector.runtime.enabled && connector.runtime.running) {
    return "Connecting";
  }
  if (connector.last_tested_at) {
    return connector.health.healthy ? "Test passed" : "Test failed";
  }
  return connector.runtime.enabled ? "Starting" : "Saved";
};

const toOpcuaTreeNode = (node: PlantGeniePlantDataOpcuaBrowseNode): OpcuaTreeNode => ({
  ...node,
  children: undefined,
  childrenLoaded: false,
});

const updateOpcuaTreeChildren = (nodes: OpcuaTreeNode[], parentNodeId: string, children: OpcuaTreeNode[]): OpcuaTreeNode[] => {
  return nodes.map((node) => {
    if (node.node_id === parentNodeId) {
      return {
        ...node,
        children,
        childrenLoaded: true,
      };
    }
    if (!node.children || node.children.length === 0) {
      return node;
    }
    return {
      ...node,
      children: updateOpcuaTreeChildren(node.children, parentNodeId, children),
    };
  });
};

const buildOpcuaBrowsePayload = (form: IndustrialConnectionFormState): { config: Record<string, unknown>; secrets: Record<string, unknown> } => ({
  config: {
    server_url: form.opcuaServerUrl.trim(),
    security_mode: form.opcuaSecurityMode === "none" ? null : form.opcuaSecurityMode,
    security_policy: form.opcuaSecurityMode === "none" ? null : form.opcuaSecurityPolicy.trim() || null,
    authentication_mode: form.opcuaAuthMode,
    username: form.opcuaAuthMode === "username_password" ? form.opcuaUsername.trim() || null : null,
    session_timeout_ms: Number.parseInt(form.opcuaSessionTimeoutMs, 10) || 60000,
    browse_root_node_id: form.opcuaBrowseRootNodeId.trim() || null,
    trust_list_names: form.opcuaTrustListNames,
    client_certificate_name: form.opcuaClientCertificateName.trim() || null,
    client_private_key_name: form.opcuaClientPrivateKeyName.trim() || null,
    subscription_config: {
      root_node_id: form.opcuaBrowseRootNodeId.trim() || null,
      nodes: form.opcuaSelectedNodes.map((node) => ({
        node_id: node.nodeId,
        browse_name: node.browseName,
        display_name: node.displayName,
        node_class: node.nodeClass,
        tag: node.tag,
      })),
    },
    node_ids: form.opcuaSelectedNodes.map((node) => node.nodeId),
  },
  secrets: {
    ...(form.opcuaAuthMode === "username_password" && form.opcuaPassword.trim() ? { password: form.opcuaPassword.trim() } : {}),
    ...(form.opcuaTrustListPems.length > 0 ? { trust_list_pems: form.opcuaTrustListPems } : {}),
    ...(form.opcuaClientCertificatePem.trim() ? { client_certificate_pem: form.opcuaClientCertificatePem.trim() } : {}),
    ...(form.opcuaClientPrivateKeyPem.trim() ? { client_private_key_pem: form.opcuaClientPrivateKeyPem.trim() } : {}),
    ...(form.opcuaClientPrivateKeyPassword.trim() ? { client_private_key_password: form.opcuaClientPrivateKeyPassword.trim() } : {}),
  },
});

const buildSqlPayload = (form: IndustrialConnectionFormState): { config: Record<string, unknown>; secrets: Record<string, unknown> } => {
  const queryConfig = buildSqlQueryConfig(form);
  return {
    config: {
      db_type: queryConfig.dbType,
      host: form.sqlHost.trim(),
      port: Number.parseInt(form.sqlPort, 10) || Number.parseInt(buildDefaultSqlPort(queryConfig.dbType), 10),
      database: form.sqlDatabase.trim(),
      username: form.sqlUsername.trim(),
      ssl_enabled: queryConfig.sslEnabled,
      pool_size: Number.parseInt(form.sqlPoolSize, 10) || 5,
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

const buildModbusPayload = (form: IndustrialConnectionFormState): { config: Record<string, unknown>; secrets: Record<string, unknown> } => ({
  config: buildModbusConnectorConfig(form),
  secrets: {},
});

const buildHistorianPayload = (form: IndustrialConnectionFormState): { config: Record<string, unknown>; secrets: Record<string, unknown> } => ({
  config: buildHistorianConnectorConfig(form),
  secrets: {
    ...(form.historianAuthenticationMode === "basic" && form.historianPassword.trim() ? { password: form.historianPassword.trim() } : {}),
    ...(form.historianAuthenticationMode === "bearer" && form.historianToken.trim() ? { token: form.historianToken.trim() } : {}),
  },
});

const toFormState = (connector: PlantGeniePlantDataConnector): IndustrialConnectionFormState => {
  if (connector.connector_type === "opcua") {
    const opcuaNodeConfig = JSON.stringify(connector.config.subscription_config ?? connector.config.node_ids ?? [], null, 2);
    const opcuaSelectedNodes = resolveOpcuaSelectedNodes({
      opcuaSelectedNodes: [],
      opcuaNodeConfig,
    });
    return {
      ...EMPTY_FORM,
      name: connector.name,
      connectorType: "opcua",
      pollIntervalMs: String(connector.poll_interval_ms),
      opcuaServerUrl: String(connector.config.server_url ?? connector.config.endpoint ?? ""),
      opcuaSecurityMode: String(connector.config.security_mode ?? "none"),
      opcuaSecurityPolicy: String(connector.config.security_policy ?? ""),
      opcuaAuthMode: String(connector.config.authentication_mode ?? "anonymous"),
      opcuaUsername: String(connector.config.username ?? ""),
      opcuaPassword: "",
      opcuaSessionTimeoutMs: String(connector.config.session_timeout_ms ?? 60000),
      opcuaBrowseRootNodeId: String(connector.config.browse_root_node_id ?? "i=85"),
      opcuaSelectedNodes,
      opcuaTrustListNames: Array.isArray(connector.config.trust_list_names) ? connector.config.trust_list_names.map((item) => String(item)) : [],
      opcuaTrustListPems: [],
      opcuaClientCertificateName: String(connector.config.client_certificate_name ?? ""),
      opcuaClientCertificatePem: "",
      opcuaClientPrivateKeyName: String(connector.config.client_private_key_name ?? ""),
      opcuaClientPrivateKeyPem: "",
      opcuaClientPrivateKeyPassword: "",
      opcuaNodeConfig,
    };
  }

  if (connector.connector_type === "mqtt") {
    return {
      ...EMPTY_FORM,
      name: connector.name,
      connectorType: "mqtt",
      pollIntervalMs: String(connector.poll_interval_ms),
      mqttBrokerUrl: String(
        connector.config.broker_url ?? `mqtt://${String(connector.config.host ?? "")}:${String(connector.config.port ?? 1883)}`
      ),
      mqttTopic: String(connector.config.topic ?? ""),
      mqttClientId: String(connector.config.client_id ?? buildDefaultMqttClientId()),
      mqttUsername: String(connector.config.username ?? ""),
      mqttPassword: "",
      mqttQos: String(connector.config.qos ?? 0),
      mqttKeepAlive: String(connector.config.keep_alive ?? 30),
      mqttTlsEnabled: Boolean(connector.config.tls_enabled ?? String(connector.config.broker_url ?? "").startsWith("mqtts://")),
      mqttTlsCertificateName: String(connector.config.certificate_name ?? ""),
      mqttTlsCertificatePem: "",
    };
  }

  if (connector.connector_type === "modbus_tcp") {
    return {
      ...EMPTY_FORM,
      name: connector.name,
      connectorType: "modbus_tcp",
      pollIntervalMs: String(connector.poll_interval_ms),
      modbusHost: String(connector.config.host ?? ""),
      modbusPort: String(connector.config.port ?? 502),
      modbusUnitId: String(connector.config.unit_id ?? 1),
      modbusTimeoutMs: String(connector.config.timeout_ms ?? 5000),
      modbusRetryAttempts: String(connector.config.retry_attempts ?? 2),
      modbusAutoReconnect: Boolean(connector.config.auto_reconnect ?? true),
      modbusBatchRead: Boolean(connector.config.batch_read ?? true),
      modbusMaxRegistersPerRequest: String(connector.config.max_registers_per_request ?? 120),
      modbusEnableWrite: Boolean(connector.config.enable_write),
      modbusFunctionCode: String(connector.config.write_function_code ?? "fc6"),
      modbusConfirmBeforeWrite: Boolean(connector.config.confirm_before_write ?? true),
      modbusWriteRateLimitMs: String(connector.config.write_rate_limit_ms ?? 1000),
      modbusTagMappings: Array.isArray(connector.config.tag_mappings)
        ? connector.config.tag_mappings
            .map((mapping) => {
              if (!mapping || typeof mapping !== "object") {
                return null;
              }
              const raw = mapping as Record<string, unknown>;
              const registerType = String(raw.register_type ?? raw.registerType ?? "").trim();
              const address = String(raw.address ?? "").trim();
              const quantity = String(raw.quantity ?? "1").trim() || "1";
              const dataType = String(raw.data_type ?? raw.dataType ?? "").trim();
              const internalTag = String(raw.internal_tag ?? raw.internalTag ?? "").trim();
              if (!registerType || !address || !dataType || !internalTag) {
                return null;
              }
              return {
                registerType,
                address,
                quantity,
                dataType,
                endianness: String(raw.endianness ?? "big").trim() || "big",
                wordSwap: Boolean(raw.word_swap ?? raw.wordSwap),
                internalTag,
                multiplier: String(raw.multiplier ?? "1").trim() || "1",
                offset: String(raw.offset ?? "0").trim() || "0",
                engineeringUnits: String(raw.engineering_units ?? raw.engineeringUnits ?? "").trim(),
                writable: Boolean(raw.writable),
              } satisfies ModbusTagMapping;
            })
            .filter((mapping): mapping is ModbusTagMapping => mapping !== null)
        : [],
    };
  }

  if (connector.connector_type === "historian") {
    return {
      ...EMPTY_FORM,
      name: connector.name,
      connectorType: "historian",
      pollIntervalMs: String(connector.poll_interval_ms),
      historianSubtype: String(connector.config.historian_subtype ?? "osisoft_pi"),
      historianGenericMode: String(connector.config.generic_mode ?? "sql"),
      historianPiServerUrl: String(connector.config.pi_server_url ?? connector.config.server_url ?? ""),
      historianAfServer: String(connector.config.af_server ?? ""),
      historianAfDatabase: String(connector.config.af_database ?? ""),
      historianAuthenticationMode: String(connector.config.authentication_mode ?? "anonymous"),
      historianUsername: String(connector.config.username ?? ""),
      historianPassword: "",
      historianToken: "",
      historianRetrievalMode: String(connector.config.retrieval_mode ?? "snapshot"),
      historianTimeRangeValue: String(connector.config.time_range_value ?? 1),
      historianTimeRangeUnit: String(connector.config.time_range_unit ?? "hours"),
      historianSamplingInterval: String(connector.config.sampling_interval ?? "5m"),
      historianCacheEnabled: Boolean(connector.config.cache_enabled ?? true),
      historianMaxDataPoints: String(connector.config.max_data_points ?? 500),
      historianTagMappings: Array.isArray(connector.config.tag_mappings)
        ? connector.config.tag_mappings
            .map((mapping) => {
              if (!mapping || typeof mapping !== "object") {
                return null;
              }
              const raw = mapping as Record<string, unknown>;
              const manualPath = String(raw.manual_path ?? raw.manualPath ?? "").trim();
              const displayPath = String(raw.display_path ?? raw.displayPath ?? manualPath).trim();
              const internalTag = String(raw.internal_tag ?? raw.internalTag ?? buildDefaultHistorianTag({ displayPath, manualPath })).trim();
              if (!internalTag || (!manualPath && !String(raw.web_id ?? raw.webId ?? "").trim())) {
                return null;
              }
              return {
                webId: String(raw.web_id ?? raw.webId ?? "").trim(),
                displayPath,
                manualPath,
                internalTag,
              } satisfies HistorianTagMapping;
            })
            .filter((mapping): mapping is HistorianTagMapping => mapping !== null)
        : [],
      historianDbType: String(connector.config.db_type ?? "postgresql"),
      historianHost: String(connector.config.host ?? ""),
      historianPort: String(connector.config.port ?? "5432"),
      historianDatabase: String(connector.config.database ?? ""),
      historianQuery: String(connector.config.query ?? "SELECT timestamp, tag, value FROM historian_points ORDER BY timestamp DESC LIMIT 500"),
      historianSslEnabled: Boolean(connector.config.ssl_enabled),
      historianEndpointUrl: String(connector.config.endpoint_url ?? ""),
      historianArrayPath: String(connector.config.array_path ?? "items"),
      historianTimeoutMs: String(connector.config.timeout_ms ?? 15000),
      historianTimestampField: String(connector.config.timestamp_field ?? "timestamp"),
      historianTagField: String(connector.config.tag_field ?? "tag"),
      historianValueField: String(connector.config.value_field ?? "value"),
    };
  }

  return {
    ...EMPTY_FORM,
    name: connector.name,
    connectorType: "sql",
    pollIntervalMs: String(connector.poll_interval_ms),
    sqlDbType: String(connector.config.db_type ?? "postgresql"),
    sqlHost: String(connector.config.host ?? ""),
    sqlPort: String(connector.config.port ?? buildDefaultSqlPort(String(connector.config.db_type ?? "postgresql"))),
    sqlDatabase: String(connector.config.database ?? ""),
    sqlUsername: String(connector.config.username ?? ""),
    sqlPassword: "",
    sqlSslEnabled: Boolean(connector.config.ssl_enabled),
    sqlPoolSize: String(connector.config.pool_size ?? 5),
    sqlQueryMode: String(connector.config.query_mode ?? (connector.config.custom_query ? "custom_query" : "table")),
    sqlRefreshMode: String(connector.config.refresh_mode ?? "latest_row"),
    sqlTableSchema: String(connector.config.table_schema ?? (connector.config.db_type === "sqlserver" ? "dbo" : "public")),
    sqlTableName: String(connector.config.table_name ?? ""),
    sqlCustomQuery: String(connector.config.custom_query ?? connector.config.query ?? "SELECT * FROM live_signals"),
    sqlTimestampColumn: String(connector.config.timestamp_column ?? "timestamp"),
    sqlStateColumn: String(connector.config.state_column ?? ""),
    sqlQualityColumn: String(connector.config.quality_column ?? ""),
    sqlTagMappings: Array.isArray(connector.config.tag_mappings)
      ? connector.config.tag_mappings
          .map((mapping) => {
            if (!mapping || typeof mapping !== "object") {
              return null;
            }
            const raw = mapping as Record<string, unknown>;
            const sourceColumn = String(raw.source_column ?? raw.sourceColumn ?? "").trim();
            const targetTag = String(raw.target_tag ?? raw.targetTag ?? "").trim();
            if (!sourceColumn || !targetTag) {
              return null;
            }
            return { sourceColumn, targetTag };
          })
          .filter((mapping): mapping is SqlTagMapping => mapping !== null)
      : [],
  };
};

export default function DataConnectorSettings() {
  const [connectors, setConnectors] = useState<PlantGeniePlantDataConnector[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedConnectorId, setSelectedConnectorId] = useState<string | null>(null);
  const [form, setForm] = useState<IndustrialConnectionFormState>(EMPTY_FORM);
  const [fieldErrors, setFieldErrors] = useState<IndustrialConnectionFieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);
  const [isTogglingActive, setIsTogglingActive] = useState<boolean>(false);
  const [isTesting, setIsTesting] = useState<boolean>(false);
  const [createType, setCreateType] = useState<string>("");
  const [opcuaTreeRoots, setOpcuaTreeRoots] = useState<OpcuaTreeNode[]>([]);
  const [opcuaExpandedNodeIds, setOpcuaExpandedNodeIds] = useState<string[]>([]);
  const [opcuaBrowseError, setOpcuaBrowseError] = useState<string | null>(null);
  const [opcuaLoadingNodeId, setOpcuaLoadingNodeId] = useState<string | null>(null);
  const [sqlTables, setSqlTables] = useState<PlantGeniePlantDataSqlTable[]>([]);
  const [sqlColumns, setSqlColumns] = useState<PlantGeniePlantDataSqlColumn[]>([]);
  const [sqlPreview, setSqlPreview] = useState<PlantGeniePlantDataSqlPreviewResponse | null>(null);
  const [sqlSchemaError, setSqlSchemaError] = useState<string | null>(null);
  const [isSqlSchemaLoading, setIsSqlSchemaLoading] = useState<boolean>(false);
  const [isSqlPreviewLoading, setIsSqlPreviewLoading] = useState<boolean>(false);
  const [modbusPreview, setModbusPreview] = useState<PlantGeniePlantDataModbusPreviewResponse | null>(null);
  const [modbusPreviewError, setModbusPreviewError] = useState<string | null>(null);
  const [isModbusPreviewLoading, setIsModbusPreviewLoading] = useState<boolean>(false);
  const [historianPreview, setHistorianPreview] = useState<PlantGeniePlantDataHistorianPreviewResponse | null>(null);
  const [historianPreviewError, setHistorianPreviewError] = useState<string | null>(null);
  const [historianBrowseResults, setHistorianBrowseResults] = useState<PlantGeniePlantDataHistorianBrowseItem[]>([]);
  const [historianBrowseError, setHistorianBrowseError] = useState<string | null>(null);
  const [isHistorianPreviewLoading, setIsHistorianPreviewLoading] = useState<boolean>(false);
  const [isHistorianBrowseLoading, setIsHistorianBrowseLoading] = useState<boolean>(false);

  const selectedConnector = useMemo(
    () => connectors.find((connector) => connector.id === selectedConnectorId) ?? null,
    [connectors, selectedConnectorId]
  );

  const isEditing = selectedConnector !== null;
  const activeConnector = useMemo(
    () => connectors.find((connector) => connector.runtime.enabled) ?? null,
    [connectors]
  );

  const loadConnectors = async (): Promise<void> => {
    setIsLoading(true);
    try {
      const nextConnectors = await getPlantGeniePlantDataConnectors();
      setConnectors(nextConnectors);
      setSelectedConnectorId((current) => {
        if (current && nextConnectors.some((connector) => connector.id === current)) {
          return current;
        }
        return nextConnectors[0]?.id ?? null;
      });
    } catch (error) {
      const message = normalizeErrorMessage(error, "Failed to load data connector profiles.");
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadConnectors();
  }, []);

  useEffect(() => {
    if (!selectedConnector) {
      return;
    }
    setForm(toFormState(selectedConnector));
    setFieldErrors({});
    setFormError(null);
    setOpcuaTreeRoots([]);
    setOpcuaExpandedNodeIds([]);
    setOpcuaBrowseError(null);
    setSqlTables([]);
    setSqlColumns([]);
    setSqlPreview(null);
    setSqlSchemaError(null);
    setModbusPreview(null);
    setModbusPreviewError(null);
    setHistorianPreview(null);
    setHistorianPreviewError(null);
    setHistorianBrowseResults([]);
    setHistorianBrowseError(null);
  }, [selectedConnector]);

  const resetToCreateMode = (connectorType: IndustrialConnectionFormState["connectorType"] = "opcua"): void => {
    setSelectedConnectorId(null);
    setForm({
      ...EMPTY_FORM,
      connectorType,
      mqttClientId: connectorType === "mqtt" ? buildDefaultMqttClientId() : EMPTY_FORM.mqttClientId,
    });
    setFieldErrors({});
    setFormError(null);
    setSqlTables([]);
    setSqlColumns([]);
    setSqlPreview(null);
    setSqlSchemaError(null);
    setModbusPreview(null);
    setModbusPreviewError(null);
    setHistorianPreview(null);
    setHistorianPreviewError(null);
    setHistorianBrowseResults([]);
    setHistorianBrowseError(null);
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

  const updateOpcuaSelectedNodes = (selectedNodes: OpcuaSelectedNodeMapping[], browseRootNodeId = form.opcuaBrowseRootNodeId): void => {
    setForm((current) => ({
      ...current,
      opcuaSelectedNodes: selectedNodes,
      opcuaNodeConfig: serializeOpcuaSubscriptionConfig(selectedNodes, browseRootNodeId),
    }));
    clearFieldError("opcuaNodeConfig");
    if (formError) {
      setFormError(null);
    }
  };

  const updateOpcuaBrowseRootNodeId = (browseRootNodeId: string): void => {
    setForm((current) => ({
      ...current,
      opcuaBrowseRootNodeId: browseRootNodeId,
      opcuaNodeConfig: serializeOpcuaSubscriptionConfig(current.opcuaSelectedNodes, browseRootNodeId),
    }));
  };

  const handleCreateTypeSelect = (value: string): void => {
    setCreateType("");
    if (value !== "opcua" && value !== "mqtt" && value !== "sql" && value !== "modbus_tcp" && value !== "historian") {
      return;
    }
    resetToCreateMode(value);
  };

  const updateHistorianTagMapping = (index: number, field: keyof HistorianTagMapping, value: string): void => {
    updateField(
      "historianTagMappings",
      form.historianTagMappings.map((mapping, mappingIndex) => {
        if (mappingIndex !== index) {
          return mapping;
        }
        const nextMapping = { ...mapping, [field]: value };
        if ((field === "displayPath" || field === "manualPath") && !nextMapping.internalTag.trim()) {
          nextMapping.internalTag = buildDefaultHistorianTag({ displayPath: nextMapping.displayPath, manualPath: nextMapping.manualPath });
        }
        return nextMapping;
      })
    );
  };

  const addHistorianManualMapping = (): void => {
    updateField("historianTagMappings", [
      ...form.historianTagMappings,
      {
        webId: "",
        displayPath: "",
        manualPath: "",
        internalTag: "",
      },
    ]);
  };

  const removeHistorianTagMapping = (index: number): void => {
    updateField("historianTagMappings", form.historianTagMappings.filter((_, mappingIndex) => mappingIndex !== index));
  };

  const addHistorianBrowseItem = (item: PlantGeniePlantDataHistorianBrowseItem): void => {
    if (form.historianTagMappings.some((mapping) => mapping.webId === item.web_id)) {
      return;
    }
    updateField("historianTagMappings", [
      ...form.historianTagMappings,
      {
        webId: item.web_id,
        displayPath: item.path || item.label,
        manualPath: "",
        internalTag: buildDefaultHistorianTag({ displayPath: item.path || item.label }),
      },
    ]);
  };

  const handleHistorianBrowse = async (): Promise<void> => {
    setIsHistorianBrowseLoading(true);
    setHistorianBrowseError(null);
    try {
      const response = await browsePlantGeniePlantDataHistorian({
        ...buildHistorianPayload(form),
        query: form.historianSearchQuery.trim() || null,
        limit: 50,
      });
      setHistorianBrowseResults(response.items);
    } catch (error) {
      const message = normalizeErrorMessage(error, "Failed to browse historian assets.");
      setHistorianBrowseError(message);
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setIsHistorianBrowseLoading(false);
    }
  };

  const handleHistorianPreview = async (): Promise<void> => {
    setIsHistorianPreviewLoading(true);
    setHistorianPreviewError(null);
    try {
      const response = await previewPlantGeniePlantDataHistorian(buildHistorianPayload(form));
      setHistorianPreview(response);
    } catch (error) {
      const message = normalizeErrorMessage(error, "Failed to preview historian data.");
      setHistorianPreviewError(message);
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setIsHistorianPreviewLoading(false);
    }
  };

  const handleSqlDbTypeChange = (dbType: string): void => {
    updateField("sqlDbType", dbType);
    updateField("sqlPort", buildDefaultSqlPort(dbType));
    updateField("sqlTableSchema", dbType === "sqlserver" ? "dbo" : "public");
    updateField("sqlTableName", "");
    updateField("sqlTagMappings", []);
    setSqlColumns([]);
    setSqlPreview(null);
    setSqlSchemaError(null);
  };

  const updateSqlTagMapping = (index: number, field: keyof SqlTagMapping, value: string): void => {
    const nextMappings = form.sqlTagMappings.map((mapping, mappingIndex) => {
      if (mappingIndex !== index) {
        return mapping;
      }
      const nextMapping = { ...mapping, [field]: value };
      if (field === "sourceColumn" && !nextMapping.targetTag.trim()) {
        nextMapping.targetTag = buildDefaultSqlTag({ sourceColumn: value });
      }
      return nextMapping;
    });
    updateField("sqlTagMappings", nextMappings);
  };

  const addSqlTagMapping = (): void => {
    const defaultColumn = sqlColumns.find((column) => !form.sqlTagMappings.some((mapping) => mapping.sourceColumn === column.name))?.name ?? "";
    updateField("sqlTagMappings", [
      ...form.sqlTagMappings,
      {
        sourceColumn: defaultColumn,
        targetTag: buildDefaultSqlTag({ sourceColumn: defaultColumn }),
      },
    ]);
  };

  const removeSqlTagMapping = (index: number): void => {
    updateField("sqlTagMappings", form.sqlTagMappings.filter((_, mappingIndex) => mappingIndex !== index));
  };

  const updateModbusTagMapping = (index: number, field: keyof ModbusTagMapping, value: string | boolean): void => {
    const nextMappings = form.modbusTagMappings.map((mapping, mappingIndex) => {
      if (mappingIndex !== index) {
        return mapping;
      }
      const nextMapping = { ...mapping, [field]: value } as ModbusTagMapping;
      if ((field === "registerType" || field === "address") && !nextMapping.internalTag.trim()) {
        nextMapping.internalTag = buildDefaultModbusTag({ registerType: nextMapping.registerType, address: nextMapping.address });
      }
      if ((field === "registerType" || field === "dataType") && (nextMapping.registerType === "coil" || nextMapping.registerType === "discrete_input")) {
        nextMapping.dataType = "bool";
        nextMapping.quantity = "1";
      }
      return nextMapping;
    });
    updateField("modbusTagMappings", nextMappings);
  };

  const addModbusTagMapping = (): void => {
    const nextAddress = String(form.modbusTagMappings.length === 0 ? 0 : Math.max(...form.modbusTagMappings.map((mapping) => Number.parseInt(mapping.address, 10) || 0)) + 1);
    updateField("modbusTagMappings", [
      ...form.modbusTagMappings,
      {
        registerType: "holding_register",
        address: nextAddress,
        quantity: "1",
        dataType: "uint16",
        endianness: "big",
        wordSwap: false,
        internalTag: buildDefaultModbusTag({ registerType: "holding_register", address: nextAddress }),
        multiplier: "1",
        offset: "0",
        engineeringUnits: "",
        writable: false,
      },
    ]);
  };

  const removeModbusTagMapping = (index: number): void => {
    updateField("modbusTagMappings", form.modbusTagMappings.filter((_, mappingIndex) => mappingIndex !== index));
  };

  const loadSqlSchema = async (options?: { tableName?: string; tableSchema?: string }): Promise<void> => {
    setIsSqlSchemaLoading(true);
    setSqlSchemaError(null);
    try {
      const payload = buildSqlPayload(form);
      const response = await getPlantGeniePlantDataSqlSchema({
        ...payload,
        table_name: options?.tableName ?? (form.sqlTableName.trim() || null),
        table_schema: options?.tableSchema ?? (form.sqlTableSchema.trim() || null),
      });
      setSqlTables(response.tables);
      setSqlColumns(response.columns);
    } catch (error) {
      const message = normalizeErrorMessage(error, "Failed to load SQL tables and columns.");
      setSqlSchemaError(message);
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setIsSqlSchemaLoading(false);
    }
  };

  const handleSqlTableChange = async (tableLabel: string): Promise<void> => {
    const selectedTable = sqlTables.find((table) => table.label === tableLabel || table.name === tableLabel) ?? null;
    const nextSchema = selectedTable?.schema ?? form.sqlTableSchema;
    const nextTableName = selectedTable?.name ?? tableLabel;
    updateField("sqlTableSchema", nextSchema);
    updateField("sqlTableName", nextTableName);
    updateField("sqlTagMappings", []);
    setSqlPreview(null);
    await loadSqlSchema({ tableName: nextTableName, tableSchema: nextSchema });
  };

  const handleSqlPreview = async (): Promise<void> => {
    setIsSqlPreviewLoading(true);
    setSqlSchemaError(null);
    try {
      const payload = buildSqlPayload(form);
      const response = await previewPlantGeniePlantDataSql({
        ...payload,
        limit: 25,
      });
      setSqlPreview(response);
    } catch (error) {
      const message = normalizeErrorMessage(error, "Failed to preview SQL data.");
      setSqlSchemaError(message);
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setIsSqlPreviewLoading(false);
    }
  };

  const handleModbusPreview = async (): Promise<void> => {
    setIsModbusPreviewLoading(true);
    setModbusPreviewError(null);
    try {
      const payload = buildModbusPayload(form);
      const response = await previewPlantGeniePlantDataModbus(payload);
      setModbusPreview(response);
    } catch (error) {
      const message = normalizeErrorMessage(error, "Failed to preview Modbus data.");
      setModbusPreviewError(message);
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setIsModbusPreviewLoading(false);
    }
  };

  const persistConnector = async (options: { successMessage: string }): Promise<PlantGeniePlantDataConnector | null> => {
    const validationErrors = validateIndustrialConnectorForm(form, { isEditing });
    if (Object.keys(validationErrors).length > 0) {
      setFieldErrors(validationErrors);
      setFormError(null);
      return null;
    }

    setFieldErrors({});
    setFormError(null);

    try {
      const payload = mapIndustrialConnectorFormToRequest(form, { isEditing });
      const saved = isEditing && selectedConnector
        ? await updatePlantGeniePlantDataConnector(selectedConnector.id, payload)
        : await createPlantGeniePlantDataConnector(payload);
      toast.success(options.successMessage.replace("{name}", saved.name), { className: "industrial-toast" });
      await loadConnectors();
      setSelectedConnectorId(saved.id);
      return saved;
    } catch (error) {
      const message = normalizeErrorMessage(error, "Failed to save data connector profile.");
      setFormError(message);
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
      return null;
    }
  };

  const handleSubmit = async (): Promise<void> => {
    setIsSaving(true);
    try {
      await persistConnector({ successMessage: isEditing ? "Updated {name}" : "Created {name}" });
    } finally {
      setIsSaving(false);
    }
  };

  const handleMqttCertificateChange = async (fileList: FileList | null): Promise<void> => {
    const file = fileList?.[0] ?? null;
    if (!file) {
      updateField("mqttTlsCertificateName", "");
      updateField("mqttTlsCertificatePem", "");
      return;
    }

    try {
      const certificatePem = await readFileAsText(file);
      updateField("mqttTlsCertificateName", file.name);
      updateField("mqttTlsCertificatePem", certificatePem);
    } catch (error) {
      const message = normalizeErrorMessage(error, "Failed to read TLS certificate.");
      setFormError(message);
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    }
  };

  const handleOpcuaTrustListChange = async (fileList: FileList | null): Promise<void> => {
    const files = Array.from(fileList ?? []);
    if (files.length === 0) {
      updateField("opcuaTrustListNames", []);
      updateField("opcuaTrustListPems", []);
      return;
    }

    try {
      const contents = await Promise.all(files.map((file) => readFileAsText(file)));
      updateField("opcuaTrustListNames", files.map((file) => file.name));
      updateField("opcuaTrustListPems", contents);
    } catch (error) {
      const message = normalizeErrorMessage(error, "Failed to read OPC UA trust list file.");
      setFormError(message);
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    }
  };

  const removeOpcuaTrustListEntry = (index: number): void => {
    updateField("opcuaTrustListNames", form.opcuaTrustListNames.filter((_, itemIndex) => itemIndex !== index));
    updateField("opcuaTrustListPems", form.opcuaTrustListPems.filter((_, itemIndex) => itemIndex !== index));
  };

  const handleOpcuaCertificateFile = async (
    fileList: FileList | null,
    fields: {
      nameField: "opcuaClientCertificateName" | "opcuaClientPrivateKeyName";
      valueField: "opcuaClientCertificatePem" | "opcuaClientPrivateKeyPem";
    }
  ): Promise<void> => {
    const file = fileList?.[0] ?? null;
    if (!file) {
      updateField(fields.nameField, "");
      updateField(fields.valueField, "");
      return;
    }

    try {
      const fileContent = await readFileAsText(file);
      updateField(fields.nameField, file.name);
      updateField(fields.valueField, fileContent);
    } catch (error) {
      const message = normalizeErrorMessage(error, `Failed to read ${file.name}.`);
      setFormError(message);
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    }
  };

  const handleOpcuaBrowse = async (parentNodeId?: string): Promise<void> => {
    if (!form.opcuaServerUrl.trim()) {
      setFieldErrors((current) => ({ ...current, opcuaServerUrl: "Server URL is required before browsing." }));
      return;
    }

    const browseNodeId = parentNodeId ?? (form.opcuaBrowseRootNodeId.trim() || undefined);
    setOpcuaLoadingNodeId(browseNodeId ?? "root");
    setOpcuaBrowseError(null);

    try {
      const response = await browsePlantGeniePlantDataOpcua({
        ...buildOpcuaBrowsePayload(form),
        node_id: browseNodeId ?? null,
      });
      const children = response.nodes.map(toOpcuaTreeNode);
      if (!parentNodeId) {
        setOpcuaTreeRoots([
          {
            node_id: response.node_id,
            browse_name: response.browse_name,
            display_name: response.display_name,
            node_class: "Object",
            has_children: true,
            selectable: false,
            children,
            childrenLoaded: true,
          },
        ]);
        setOpcuaExpandedNodeIds([response.node_id]);
        updateOpcuaBrowseRootNodeId(response.node_id);
        return;
      }

      setOpcuaTreeRoots((current) => updateOpcuaTreeChildren(current, parentNodeId, children));
      setOpcuaExpandedNodeIds((current) => (current.includes(parentNodeId) ? current : [...current, parentNodeId]));
    } catch (error) {
      const message = normalizeErrorMessage(error, "OPC UA browse failed.");
      setOpcuaBrowseError(message);
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setOpcuaLoadingNodeId(null);
    }
  };

  const handleOpcuaToggleExpand = async (node: OpcuaTreeNode): Promise<void> => {
    const isExpanded = opcuaExpandedNodeIds.includes(node.node_id);
    if (isExpanded) {
      setOpcuaExpandedNodeIds((current) => current.filter((item) => item !== node.node_id));
      return;
    }

    setOpcuaExpandedNodeIds((current) => [...current, node.node_id]);
    if (node.has_children && !node.childrenLoaded) {
      await handleOpcuaBrowse(node.node_id);
    }
  };

  const handleOpcuaToggleSelection = (node: OpcuaTreeNode): void => {
    const exists = form.opcuaSelectedNodes.find((item) => item.nodeId === node.node_id);
    if (exists) {
      updateOpcuaSelectedNodes(form.opcuaSelectedNodes.filter((item) => item.nodeId !== node.node_id));
      return;
    }

    updateOpcuaSelectedNodes([
      ...form.opcuaSelectedNodes,
      {
        nodeId: node.node_id,
        browseName: node.browse_name,
        displayName: node.display_name,
        nodeClass: node.node_class,
        tag: buildDefaultOpcuaTargetTag({
          browseName: node.browse_name,
          displayName: node.display_name,
          nodeId: node.node_id,
        }),
      },
    ]);
  };

  const handleOpcuaMappedTagChange = (nodeId: string, tag: string): void => {
    updateOpcuaSelectedNodes(
      form.opcuaSelectedNodes.map((node) => (node.nodeId === nodeId ? { ...node, tag } : node))
    );
  };

  const handleConnectTest = async (): Promise<void> => {
    setIsTesting(true);
    try {
      const saved = await persistConnector({ successMessage: isEditing ? "Updated {name}" : "Created {name}" });
      if (!saved) {
        return;
      }
      const testResult = await testPlantGeniePlantDataConnector(saved.id);
      if (!testResult.success) {
        toast.error(testResult.message, { className: "industrial-toast industrial-toast-error" });
        await loadConnectors();
        setSelectedConnectorId(saved.id);
        return;
      }
      const activated = await activatePlantGeniePlantDataConnector(saved.id);
      toast.success(`${activated.name} connected and subscribed successfully.`, { className: "industrial-toast" });
      await loadConnectors();
      setSelectedConnectorId(activated.id);
    } catch (error) {
      const message = normalizeErrorMessage(error, "Connector connect/test failed.");
      setFormError(message);
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setIsTesting(false);
    }
  };

  const renderOpcuaTree = (nodes: OpcuaTreeNode[], depth = 0) => {
    if (nodes.length === 0) {
      return null;
    }

    return (
      <ul className="data-connectors-opcua-tree">
        {nodes.map((node) => {
          const isExpanded = opcuaExpandedNodeIds.includes(node.node_id);
          const isSelected = form.opcuaSelectedNodes.some((item) => item.nodeId === node.node_id);
          return (
            <li key={node.node_id}>
              <div className="data-connectors-opcua-node" style={{ paddingLeft: `${depth * 0.85}rem` }}>
                <button
                  type="button"
                  className="data-connectors-opcua-expand"
                  onClick={() => {
                    void handleOpcuaToggleExpand(node);
                  }}
                  disabled={!node.has_children && !node.childrenLoaded}
                >
                  {node.has_children ? (isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />) : <span className="data-connectors-opcua-expand-spacer" />}
                </button>
                <label className="data-connectors-opcua-selectable">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => handleOpcuaToggleSelection(node)}
                    disabled={!node.selectable}
                  />
                  <span className="data-connectors-opcua-node-copy">
                    <strong>{node.display_name}</strong>
                    <span>
                      {node.browse_name} · {node.node_class} · {node.node_id}
                    </span>
                  </span>
                </label>
                {opcuaLoadingNodeId === node.node_id ? <LoaderCircle size={12} className="animate-spin" /> : null}
              </div>
              {isExpanded && node.children && node.children.length > 0 ? renderOpcuaTree(node.children, depth + 1) : null}
            </li>
          );
        })}
      </ul>
    );
  };

  const handleDelete = async (): Promise<void> => {
    if (!selectedConnector) {
      return;
    }

    setIsDeleting(true);
    try {
      const response = await deletePlantGeniePlantDataConnector(selectedConnector.id);
      toast.success(response.message, { className: "industrial-toast" });
      resetToCreateMode();
      await loadConnectors();
    } catch (error) {
      const message = normalizeErrorMessage(error, "Failed to delete data connector profile.");
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setIsDeleting(false);
    }
  };

  const handleToggleActive = async (): Promise<void> => {
    if (!selectedConnector) {
      return;
    }

    setIsTogglingActive(true);
    try {
      const nextConnector = selectedConnector.runtime.enabled
        ? await deactivatePlantGeniePlantDataConnector(selectedConnector.id)
        : await activatePlantGeniePlantDataConnector(selectedConnector.id);
      toast.success(
        nextConnector.runtime.enabled ? `${nextConnector.name} is now the active data source.` : `${nextConnector.name} is no longer active.`,
        { className: "industrial-toast" }
      );
      await loadConnectors();
      setSelectedConnectorId(nextConnector.id);
    } catch (error) {
      const message = normalizeErrorMessage(error, "Failed to update active data source.");
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setIsTogglingActive(false);
    }
  };

  return (
    <section className="graph-shell">
      <div className="main-workspace-view billing-settings-view plant-genie-connectors-view">
        <div className="plant-genie-connectors-layout data-connectors-layout">
          <PlantGenieAIBindingPanel connectors={connectors} isConnectorsLoading={isLoading} />
          <div className="plant-genie-connectors-card data-connectors-card data-connectors-card-full">
            <div className="plant-genie-connectors-header data-connectors-header">
              <div>
                <div className="plant-genie-settings-kicker">Settings / Data Connectors</div>
                <h2 className="panel-title">Data Connectors</h2>
                <p className="billing-settings-lead">
                  Configure your plant data sources here; this data powers both the Simulation Panel and Plant Genie, so
                  select where your data comes from and how it should be used across the system.
                </p>
              </div>
              <label className="data-connectors-add-control">
                <span>Add connector</span>
                <div className="data-connectors-select-wrap">
                  <select value={createType} onChange={(event) => handleCreateTypeSelect(event.target.value)}>
                    <option value="">Choose type</option>
                    {INDUSTRIAL_CONNECTION_TYPE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <ChevronDown size={14} />
                </div>
              </label>
            </div>

            <div className="plant-genie-connectors-summary">
              <div className="plant-genie-summary-chip is-active">
                <DatabaseZap size={12} />
                <span>{activeConnector ? `Active source: ${activeConnector.name}` : "No active data source selected"}</span>
              </div>
              <div className="plant-genie-summary-chip">
                <CheckCircle2 size={12} />
                <span>{connectors.length} saved profile{connectors.length === 1 ? "" : "s"}</span>
              </div>
            </div>

            <div className="data-connectors-card-body">
            <div className="data-connectors-workspace">
              <aside className="data-connectors-sidebar">
                <div className="data-connectors-sidebar-header">Saved profiles</div>
                <div className="data-connectors-sidebar-body">
                  {isLoading ? (
                    <div className="plant-genie-connectors-empty data-connectors-empty-state">
                      <LoaderCircle size={14} className="animate-spin" /> Loading profiles...
                    </div>
                  ) : connectors.length === 0 ? (
                    <div className="plant-genie-connectors-empty data-connectors-empty-state">
                      No saved profiles yet. Use the add connector dropdown to create one.
                    </div>
                  ) : (
                    <div className="plant-genie-connector-list data-connectors-profile-list">
                      {connectors.map((connector) => (
                        <button
                          key={connector.id}
                          type="button"
                          className={`plant-genie-connector-item data-connectors-profile-item ${selectedConnectorId === connector.id ? "selected" : ""}`}
                          onClick={() => setSelectedConnectorId(connector.id)}
                        >
                          <div className="plant-genie-connector-title-row">
                            <strong>{connector.name}</strong>
                            <div className="plant-genie-connector-badges">
                              {connector.runtime.enabled ? <span className="plant-genie-badge active">Active</span> : null}
                              <span className={`plant-genie-badge ${connector.runtime.last_error ? "unhealthy" : connector.health.healthy ? "healthy" : "unknown"}`}>
                                {formatConnectorRuntimeStatus(connector)}
                              </span>
                            </div>
                          </div>
                          <div className="plant-genie-connector-meta">{formatConnectorType(connector.connector_type)}</div>
                          <div className="plant-genie-connector-status-row">
                            <span>Updated {formatTimestamp(connector.updated_at)}</span>
                            {connector.last_tested_at ? <span>Tested {formatTimestamp(connector.last_tested_at)}</span> : null}
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </aside>

              <section className="data-connectors-editor">
                <div className="plant-genie-form-header data-connectors-editor-header">
                  <div>
                    <h3>{isEditing ? `Edit ${selectedConnector?.name ?? "Profile"}` : "Create Connector Profile"}</h3>
                    <p>
                      {isEditing
                        ? "Update the selected connector profile. Leave secret fields blank to keep the currently stored credentials."
                        : "Create a reusable connector profile for OPC UA, MQTT, or SQL / Historian plant data sources."}
                    </p>
                  </div>
                  <div className="data-connectors-editor-actions">
                    {isEditing ? (
                      <button
                        type="button"
                        className={`command-btn ${selectedConnector?.runtime.enabled ? "" : "primary"}`}
                        onClick={() => void handleToggleActive()}
                        disabled={isTogglingActive || isSaving || isDeleting}
                      >
                        <CheckCircle2 size={12} />
                        <span>
                          {isTogglingActive
                            ? "Updating..."
                            : selectedConnector?.runtime.enabled
                              ? "Deactivate"
                              : "Set Active"}
                        </span>
                      </button>
                    ) : null}
                    <button
                      type="button"
                      className="command-btn"
                      onClick={() => resetToCreateMode(form.connectorType)}
                      disabled={isSaving || isDeleting || isTogglingActive}
                    >
                      <Plus size={12} />
                      <span>New Profile</span>
                    </button>
                    {isEditing ? (
                      <button
                        type="button"
                        className="command-btn danger"
                        onClick={() => void handleDelete()}
                        disabled={isDeleting || isSaving || isTogglingActive}
                      >
                        <Trash2 size={12} />
                        <span>{isDeleting ? "Deleting..." : "Delete"}</span>
                      </button>
                    ) : null}
                  </div>
                </div>

                <div className="data-connectors-editor-body">
                <div className="plant-genie-form-grid">
                  <label className="plant-genie-field">
                    <span>Profile name</span>
                    <input type="text" value={form.name} onChange={(event) => updateField("name", event.target.value)} placeholder="Primary historian" />
                    {fieldErrors.name ? <span className="plant-genie-field-error">{fieldErrors.name}</span> : null}
                  </label>

                  <label className="plant-genie-field">
                    <span>Connector type</span>
                    <select value={form.connectorType} onChange={(event) => updateField("connectorType", event.target.value as IndustrialConnectionFormState["connectorType"])}>
                      {INDUSTRIAL_CONNECTION_TYPE_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                    {fieldErrors.connectorType ? <span className="plant-genie-field-error">{fieldErrors.connectorType}</span> : null}
                  </label>

                  <label className="plant-genie-field">
                    <span>Poll interval (ms)</span>
                    <input type="number" min={500} step={100} value={form.pollIntervalMs} onChange={(event) => updateField("pollIntervalMs", event.target.value)} />
                    {fieldErrors.pollIntervalMs ? <span className="plant-genie-field-error">{fieldErrors.pollIntervalMs}</span> : null}
                  </label>

                  <label className="plant-genie-field">
                    <span>Status</span>
                    <div className="data-connectors-status-panel">
                      <div className="data-connectors-readout">
                        <span className={`plant-genie-badge ${selectedConnector?.runtime.enabled ? "active" : "inactive"}`}>
                          {selectedConnector?.runtime.enabled ? "Active across system" : "Saved only"}
                        </span>
                        <span className={`plant-genie-badge ${selectedConnector?.runtime.last_error ? "unhealthy" : selectedConnector?.health.healthy ? "healthy" : "unknown"}`}>
                          {formatConnectorRuntimeStatus(selectedConnector)}
                        </span>
                      </div>
                      {selectedConnector?.runtime.last_update ? <span>Last message: {formatTimestamp(selectedConnector.runtime.last_update)}</span> : null}
                      {selectedConnector?.runtime.last_error ? <span>{selectedConnector.runtime.last_error}</span> : null}
                    </div>
                  </label>

                  {form.connectorType === "opcua" ? (
                    <>
                      <label className="plant-genie-field">
                        <span>Endpoint URL</span>
                        <input
                          type="text"
                          value={form.opcuaServerUrl}
                          onChange={(event) => updateField("opcuaServerUrl", event.target.value)}
                          placeholder="opc.tcp://192.168.1.10:4840"
                        />
                        {fieldErrors.opcuaServerUrl ? <span className="plant-genie-field-error">{fieldErrors.opcuaServerUrl}</span> : null}
                      </label>

                      <label className="plant-genie-field">
                        <span>Security mode</span>
                        <select value={form.opcuaSecurityMode} onChange={(event) => updateField("opcuaSecurityMode", event.target.value)}>
                          {OPCUA_SECURITY_MODE_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </label>

                      <label className="plant-genie-field">
                        <span>Security policy</span>
                        <select
                          value={form.opcuaSecurityPolicy}
                          onChange={(event) => updateField("opcuaSecurityPolicy", event.target.value)}
                          disabled={form.opcuaSecurityMode === "none"}
                        >
                          <option value="">Select policy</option>
                          {OPCUA_SECURITY_POLICY_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                        {fieldErrors.opcuaSecurityPolicy ? <span className="plant-genie-field-error">{fieldErrors.opcuaSecurityPolicy}</span> : null}
                      </label>

                      <label className="plant-genie-field">
                        <span>Authentication</span>
                        <select value={form.opcuaAuthMode} onChange={(event) => updateField("opcuaAuthMode", event.target.value)}>
                          {OPCUA_AUTH_MODE_OPTIONS.map((option) => (
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
                          placeholder={form.opcuaAuthMode === "username_password" ? "Required username" : "Optional username"}
                          disabled={form.opcuaAuthMode !== "username_password"}
                        />
                        {fieldErrors.opcuaUsername ? <span className="plant-genie-field-error">{fieldErrors.opcuaUsername}</span> : null}
                      </label>

                      <label className="plant-genie-field">
                        <span>Password</span>
                        <input
                          type="password"
                          value={form.opcuaPassword}
                          onChange={(event) => updateField("opcuaPassword", event.target.value)}
                          placeholder={isEditing ? "Leave blank to keep stored secret" : "Required for username/password auth"}
                          disabled={form.opcuaAuthMode !== "username_password"}
                        />
                        {fieldErrors.opcuaPassword ? <span className="plant-genie-field-error">{fieldErrors.opcuaPassword}</span> : null}
                      </label>

                      <label className="plant-genie-field">
                        <span>Session timeout (ms)</span>
                        <input type="number" min={1000} max={3600000} value={form.opcuaSessionTimeoutMs} onChange={(event) => updateField("opcuaSessionTimeoutMs", event.target.value)} />
                        {fieldErrors.opcuaSessionTimeoutMs ? <span className="plant-genie-field-error">{fieldErrors.opcuaSessionTimeoutMs}</span> : null}
                      </label>

                      <label className="plant-genie-field plant-genie-field-full">
                        <span>Certificate manager / trust list</span>
                        <div className="data-connectors-opcua-cert-grid">
                          <label className="plant-genie-field">
                            <span>Trusted server certificates</span>
                            <input
                              className="data-connectors-file-input"
                              type="file"
                              accept=".pem,.crt,.cer,.txt"
                              multiple
                              onChange={(event) => {
                                void handleOpcuaTrustListChange(event.target.files);
                              }}
                            />
                          </label>
                          <label className="plant-genie-field">
                            <span>Client certificate</span>
                            <input
                              className="data-connectors-file-input"
                              type="file"
                              accept=".pem,.crt,.cer,.txt"
                              onChange={(event) => {
                                void handleOpcuaCertificateFile(event.target.files, {
                                  nameField: "opcuaClientCertificateName",
                                  valueField: "opcuaClientCertificatePem",
                                });
                              }}
                            />
                            {fieldErrors.opcuaClientCertificateName ? <span className="plant-genie-field-error">{fieldErrors.opcuaClientCertificateName}</span> : null}
                          </label>
                          <label className="plant-genie-field">
                            <span>Client private key</span>
                            <input
                              className="data-connectors-file-input"
                              type="file"
                              accept=".pem,.key,.txt"
                              onChange={(event) => {
                                void handleOpcuaCertificateFile(event.target.files, {
                                  nameField: "opcuaClientPrivateKeyName",
                                  valueField: "opcuaClientPrivateKeyPem",
                                });
                              }}
                            />
                            {fieldErrors.opcuaClientPrivateKeyName ? <span className="plant-genie-field-error">{fieldErrors.opcuaClientPrivateKeyName}</span> : null}
                          </label>
                          <label className="plant-genie-field">
                            <span>Private key password</span>
                            <input type="password" value={form.opcuaClientPrivateKeyPassword} onChange={(event) => updateField("opcuaClientPrivateKeyPassword", event.target.value)} placeholder="Optional key password" />
                          </label>
                        </div>
                        <div className="data-connectors-opcua-cert-list">
                          {form.opcuaTrustListNames.length > 0 ? form.opcuaTrustListNames.map((item, index) => (
                            <span key={`${item}-${index}`} className="data-connectors-opcua-chip">
                              <ShieldCheck size={12} />
                              <span>{item}</span>
                              <button type="button" onClick={() => removeOpcuaTrustListEntry(index)}>
                                <X size={11} />
                              </button>
                            </span>
                          )) : <span className="data-connectors-file-name">No trusted server certificates uploaded.</span>}
                        </div>
                        <div className="data-connectors-opcua-cert-list">
                          {form.opcuaClientCertificateName ? <span className="data-connectors-opcua-chip"><ShieldCheck size={12} /><span>{form.opcuaClientCertificateName}</span></span> : null}
                          {form.opcuaClientPrivateKeyName ? <span className="data-connectors-opcua-chip"><ShieldCheck size={12} /><span>{form.opcuaClientPrivateKeyName}</span></span> : null}
                        </div>
                      </label>

                      <label className="plant-genie-field plant-genie-field-full">
                        <span>OPC UA actions</span>
                        <div className="data-connectors-editor-actions">
                          <button
                            type="button"
                            className="command-btn"
                            onClick={() => {
                              void handleOpcuaBrowse();
                            }}
                            disabled={isTesting || isSaving || isDeleting || isTogglingActive || Boolean(opcuaLoadingNodeId)}
                          >
                            {opcuaLoadingNodeId ? <LoaderCircle size={12} className="animate-spin" /> : <FolderTree size={12} />}
                            <span>{opcuaLoadingNodeId ? "Browsing..." : "Browse Server"}</span>
                          </button>
                          <button
                            type="button"
                            className="command-btn"
                            onClick={() => void handleConnectTest()}
                            disabled={isTesting || isSaving || isDeleting || isTogglingActive}
                          >
                            {isTesting ? <LoaderCircle size={12} className="animate-spin" /> : <PlugZap size={12} />}
                            <span>{isTesting ? "Connecting..." : "Connect / Test"}</span>
                          </button>
                        </div>
                      </label>

                      <div className="plant-genie-field plant-genie-field-full">
                        <span>Node browser</span>
                        <div className="data-connectors-opcua-browser">
                          {opcuaBrowseError ? <div className="plant-genie-inline-alert error"><span>{opcuaBrowseError}</span></div> : null}
                          {opcuaTreeRoots.length > 0 ? renderOpcuaTree(opcuaTreeRoots) : <p className="data-connectors-file-name">Browse the server to select variables for this connector profile.</p>}
                        </div>
                      </div>

                      <div className="plant-genie-field plant-genie-field-full">
                        <span>Selected nodes and tag mappings</span>
                        <div className="data-connectors-opcua-selection-list">
                          {form.opcuaSelectedNodes.length > 0 ? form.opcuaSelectedNodes.map((node) => (
                            <div key={node.nodeId} className="data-connectors-opcua-selection-item">
                              <div className="data-connectors-opcua-selection-copy">
                                <strong>{node.displayName}</strong>
                                <span>{node.nodeId}</span>
                              </div>
                              <label className="plant-genie-field">
                                <span>Unified tag</span>
                                <input type="text" value={node.tag} onChange={(event) => handleOpcuaMappedTagChange(node.nodeId, event.target.value)} placeholder="UNS tag name" />
                              </label>
                              <button type="button" className="command-btn danger" onClick={() => updateOpcuaSelectedNodes(form.opcuaSelectedNodes.filter((item) => item.nodeId !== node.nodeId))}>
                                <Trash2 size={12} />
                                <span>Remove</span>
                              </button>
                            </div>
                          )) : <p className="data-connectors-file-name">No OPC UA nodes selected yet.</p>}
                        </div>
                        {fieldErrors.opcuaNodeConfig ? <span className="plant-genie-field-error">{fieldErrors.opcuaNodeConfig}</span> : null}
                      </div>
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
                        <input type="text" value={form.mqttTopic} onChange={(event) => updateField("mqttTopic", event.target.value)} placeholder="plant/line1/#" />
                        {fieldErrors.mqttTopic ? <span className="plant-genie-field-error">{fieldErrors.mqttTopic}</span> : null}
                      </label>

                      <label className="plant-genie-field">
                        <span>Client ID</span>
                        <input type="text" value={form.mqttClientId} onChange={(event) => updateField("mqttClientId", event.target.value)} placeholder="Auto-generated but editable" />
                      </label>

                      <label className="plant-genie-field">
                        <span>Username</span>
                        <input type="text" value={form.mqttUsername} onChange={(event) => updateField("mqttUsername", event.target.value)} placeholder="Optional username" />
                      </label>

                      <label className="plant-genie-field">
                        <span>QoS</span>
                        <select value={form.mqttQos} onChange={(event) => updateField("mqttQos", event.target.value)}>
                          {MQTT_QOS_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                        {fieldErrors.mqttQos ? <span className="plant-genie-field-error">{fieldErrors.mqttQos}</span> : null}
                      </label>

                      <label className="plant-genie-field">
                        <span>Keep Alive</span>
                        <input type="number" min={5} max={3600} value={form.mqttKeepAlive} onChange={(event) => updateField("mqttKeepAlive", event.target.value)} />
                        {fieldErrors.mqttKeepAlive ? <span className="plant-genie-field-error">{fieldErrors.mqttKeepAlive}</span> : null}
                      </label>

                      <label className="plant-genie-field plant-genie-field-full">
                        <span>Password</span>
                        <input
                          type="password"
                          value={form.mqttPassword}
                          onChange={(event) => updateField("mqttPassword", event.target.value)}
                          placeholder={isEditing ? "Leave blank to keep stored secret" : "Optional password"}
                        />
                      </label>

                      <label className="plant-genie-field plant-genie-field-full data-connectors-toggle-field">
                        <span>TLS</span>
                        <label className="data-connectors-toggle">
                          <input
                            type="checkbox"
                            checked={form.mqttTlsEnabled}
                            onChange={(event) => updateField("mqttTlsEnabled", event.target.checked)}
                          />
                          <span>Enable TLS</span>
                        </label>
                      </label>

                      {form.mqttTlsEnabled ? (
                        <label className="plant-genie-field plant-genie-field-full">
                          <span>CA Certificate</span>
                          <input
                            className="data-connectors-file-input"
                            type="file"
                            accept=".pem,.crt,.cer,.txt"
                            onChange={(event) => {
                              void handleMqttCertificateChange(event.target.files);
                            }}
                          />
                          <span className="data-connectors-file-name">
                            {form.mqttTlsCertificateName || "No certificate uploaded. System CA trust will be used if supported by the broker."}
                          </span>
                        </label>
                      ) : null}

                      <div className="plant-genie-field plant-genie-field-full data-connectors-inline-actions">
                        <span>MQTT Actions</span>
                        <div className="data-connectors-editor-actions">
                          <button
                            type="button"
                            className="command-btn"
                            onClick={() => void handleConnectTest()}
                            disabled={isTesting || isSaving || isDeleting || isTogglingActive}
                          >
                            {isTesting ? <LoaderCircle size={12} className="animate-spin" /> : <PlugZap size={12} />}
                            <span>{isTesting ? "Connecting..." : "Connect / Test"}</span>
                          </button>
                        </div>
                      </div>
                    </>
                  ) : null}

                  {form.connectorType === "modbus_tcp" ? (
                    <>
                      <label className="plant-genie-field">
                        <span>Host</span>
                        <input type="text" value={form.modbusHost} onChange={(event) => updateField("modbusHost", event.target.value)} placeholder="192.168.1.50" />
                        {fieldErrors.modbusHost ? <span className="plant-genie-field-error">{fieldErrors.modbusHost}</span> : null}
                      </label>

                      <label className="plant-genie-field">
                        <span>Port</span>
                        <input type="number" min={1} max={65535} value={form.modbusPort} onChange={(event) => updateField("modbusPort", event.target.value)} />
                        {fieldErrors.modbusPort ? <span className="plant-genie-field-error">{fieldErrors.modbusPort}</span> : null}
                      </label>

                      <label className="plant-genie-field">
                        <span>Unit ID</span>
                        <input type="number" min={0} max={255} value={form.modbusUnitId} onChange={(event) => updateField("modbusUnitId", event.target.value)} />
                        {fieldErrors.modbusUnitId ? <span className="plant-genie-field-error">{fieldErrors.modbusUnitId}</span> : null}
                      </label>

                      <label className="plant-genie-field">
                        <span>Timeout (ms)</span>
                        <input type="number" min={100} max={60000} value={form.modbusTimeoutMs} onChange={(event) => updateField("modbusTimeoutMs", event.target.value)} />
                        {fieldErrors.modbusTimeoutMs ? <span className="plant-genie-field-error">{fieldErrors.modbusTimeoutMs}</span> : null}
                      </label>

                      <label className="plant-genie-field">
                        <span>Retry Attempts</span>
                        <input type="number" min={0} max={10} value={form.modbusRetryAttempts} onChange={(event) => updateField("modbusRetryAttempts", event.target.value)} />
                        {fieldErrors.modbusRetryAttempts ? <span className="plant-genie-field-error">{fieldErrors.modbusRetryAttempts}</span> : null}
                      </label>

                      <label className="plant-genie-field data-connectors-toggle-field">
                        <span>Auto-Reconnect</span>
                        <label className="data-connectors-toggle">
                          <input type="checkbox" checked={form.modbusAutoReconnect} onChange={(event) => updateField("modbusAutoReconnect", event.target.checked)} />
                          <span>Reconnect automatically</span>
                        </label>
                      </label>

                      <label className="plant-genie-field data-connectors-toggle-field">
                        <span>Batch Read</span>
                        <label className="data-connectors-toggle">
                          <input type="checkbox" checked={form.modbusBatchRead} onChange={(event) => updateField("modbusBatchRead", event.target.checked)} />
                          <span>Read contiguous registers in batches</span>
                        </label>
                      </label>

                      <label className="plant-genie-field">
                        <span>Max Registers per Request</span>
                        <input type="number" min={1} max={125} value={form.modbusMaxRegistersPerRequest} onChange={(event) => updateField("modbusMaxRegistersPerRequest", event.target.value)} />
                        {fieldErrors.modbusMaxRegistersPerRequest ? <span className="plant-genie-field-error">{fieldErrors.modbusMaxRegistersPerRequest}</span> : null}
                      </label>

                      <label className="plant-genie-field plant-genie-field-full data-connectors-toggle-field">
                        <span>Enable Write</span>
                        <label className="data-connectors-toggle">
                          <input type="checkbox" checked={form.modbusEnableWrite} onChange={(event) => updateField("modbusEnableWrite", event.target.checked)} />
                          <span>Allow writable mappings</span>
                        </label>
                      </label>

                      <label className="plant-genie-field">
                        <span>Function Code</span>
                        <select value={form.modbusFunctionCode} onChange={(event) => updateField("modbusFunctionCode", event.target.value)} disabled={!form.modbusEnableWrite}>
                          {MODBUS_FUNCTION_CODE_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                        {fieldErrors.modbusFunctionCode ? <span className="plant-genie-field-error">{fieldErrors.modbusFunctionCode}</span> : null}
                      </label>

                      <label className="plant-genie-field data-connectors-toggle-field">
                        <span>Confirm Before Write</span>
                        <label className="data-connectors-toggle">
                          <input type="checkbox" checked={form.modbusConfirmBeforeWrite} onChange={(event) => updateField("modbusConfirmBeforeWrite", event.target.checked)} disabled={!form.modbusEnableWrite} />
                          <span>Require confirmation</span>
                        </label>
                      </label>

                      <label className="plant-genie-field">
                        <span>Write Rate Limit (ms)</span>
                        <input type="number" min={0} max={600000} value={form.modbusWriteRateLimitMs} onChange={(event) => updateField("modbusWriteRateLimitMs", event.target.value)} disabled={!form.modbusEnableWrite} />
                        {fieldErrors.modbusWriteRateLimitMs ? <span className="plant-genie-field-error">{fieldErrors.modbusWriteRateLimitMs}</span> : null}
                      </label>

                      <div className="plant-genie-field plant-genie-field-full">
                        <span>Register Config and Tag Mapping</span>
                        <div className="data-connectors-opcua-selection-list">
                          {form.modbusTagMappings.length > 0 ? form.modbusTagMappings.map((mapping, index) => (
                            <div key={`${mapping.internalTag || "modbus"}-${index}`} className="data-connectors-opcua-selection-item data-connectors-modbus-mapping-item">
                              <label className="plant-genie-field">
                                <span>Register Type</span>
                                <select value={mapping.registerType} onChange={(event) => updateModbusTagMapping(index, "registerType", event.target.value)}>
                                  {MODBUS_REGISTER_TYPE_OPTIONS.map((option) => (
                                    <option key={option.value} value={option.value}>
                                      {option.label}
                                    </option>
                                  ))}
                                </select>
                              </label>
                              <label className="plant-genie-field">
                                <span>Address</span>
                                <input type="number" min={0} max={65535} value={mapping.address} onChange={(event) => updateModbusTagMapping(index, "address", event.target.value)} />
                              </label>
                              <label className="plant-genie-field">
                                <span>Quantity</span>
                                <input type="number" min={1} max={125} value={mapping.quantity} onChange={(event) => updateModbusTagMapping(index, "quantity", event.target.value)} />
                              </label>
                              <label className="plant-genie-field">
                                <span>Data Type</span>
                                <select value={mapping.dataType} onChange={(event) => updateModbusTagMapping(index, "dataType", event.target.value)} disabled={mapping.registerType === "coil" || mapping.registerType === "discrete_input"}>
                                  {MODBUS_DATA_TYPE_OPTIONS.map((option) => (
                                    <option key={option.value} value={option.value}>
                                      {option.label}
                                    </option>
                                  ))}
                                </select>
                              </label>
                              <label className="plant-genie-field">
                                <span>Endianness</span>
                                <select value={mapping.endianness} onChange={(event) => updateModbusTagMapping(index, "endianness", event.target.value)}>
                                  {MODBUS_ENDIANNESS_OPTIONS.map((option) => (
                                    <option key={option.value} value={option.value}>
                                      {option.label}
                                    </option>
                                  ))}
                                </select>
                              </label>
                              <label className="plant-genie-field data-connectors-toggle-field">
                                <span>Word Swap</span>
                                <label className="data-connectors-toggle">
                                  <input type="checkbox" checked={mapping.wordSwap} onChange={(event) => updateModbusTagMapping(index, "wordSwap", event.target.checked)} />
                                  <span>Swap words</span>
                                </label>
                              </label>
                              <label className="plant-genie-field">
                                <span>Internal Tag</span>
                                <input type="text" value={mapping.internalTag} onChange={(event) => updateModbusTagMapping(index, "internalTag", event.target.value)} placeholder="line1.pressure" />
                              </label>
                              <label className="plant-genie-field">
                                <span>Multiplier</span>
                                <input type="number" step="any" value={mapping.multiplier} onChange={(event) => updateModbusTagMapping(index, "multiplier", event.target.value)} />
                              </label>
                              <label className="plant-genie-field">
                                <span>Offset</span>
                                <input type="number" step="any" value={mapping.offset} onChange={(event) => updateModbusTagMapping(index, "offset", event.target.value)} />
                              </label>
                              <label className="plant-genie-field">
                                <span>Engineering Units</span>
                                <input type="text" value={mapping.engineeringUnits} onChange={(event) => updateModbusTagMapping(index, "engineeringUnits", event.target.value)} placeholder="psi" />
                              </label>
                              <label className="plant-genie-field data-connectors-toggle-field">
                                <span>Writable</span>
                                <label className="data-connectors-toggle">
                                  <input type="checkbox" checked={mapping.writable} onChange={(event) => updateModbusTagMapping(index, "writable", event.target.checked)} disabled={!form.modbusEnableWrite} />
                                  <span>Writable</span>
                                </label>
                              </label>
                              <button type="button" className="command-btn danger" onClick={() => removeModbusTagMapping(index)}>
                                <Trash2 size={12} />
                                <span>Remove</span>
                              </button>
                            </div>
                          )) : <p className="data-connectors-file-name">No Modbus register mappings configured yet.</p>}
                        </div>
                        <div className="data-connectors-editor-actions">
                          <button type="button" className="command-btn" onClick={addModbusTagMapping}>
                            <Plus size={12} />
                            <span>Add Register Mapping</span>
                          </button>
                        </div>
                        {fieldErrors.modbusTagMappings ? <span className="plant-genie-field-error">{fieldErrors.modbusTagMappings}</span> : null}
                      </div>

                      <div className="plant-genie-field plant-genie-field-full data-connectors-inline-actions">
                        <span>Validation</span>
                        <div className="data-connectors-editor-actions">
                          <button type="button" className="command-btn" onClick={() => void handleModbusPreview()} disabled={isModbusPreviewLoading || isSaving || isDeleting || isTogglingActive}>
                            {isModbusPreviewLoading ? <LoaderCircle size={12} className="animate-spin" /> : <DatabaseZap size={12} />}
                            <span>{isModbusPreviewLoading ? "Loading Preview..." : "Preview Data"}</span>
                          </button>
                          <button type="button" className="command-btn" onClick={() => void handleConnectTest()} disabled={isTesting || isSaving || isDeleting || isTogglingActive}>
                            {isTesting ? <LoaderCircle size={12} className="animate-spin" /> : <PlugZap size={12} />}
                            <span>{isTesting ? "Connecting..." : "Test Connection"}</span>
                          </button>
                        </div>
                      </div>

                      <div className="plant-genie-field plant-genie-field-full">
                        <span>Preview</span>
                        {modbusPreviewError ? <div className="plant-genie-inline-alert error"><span>{modbusPreviewError}</span></div> : null}
                        {modbusPreview && modbusPreview.columns.length > 0 ? (
                          <div className="data-connectors-opcua-browser">
                            <div className="data-connectors-status-panel">
                              <span>{modbusPreview.row_count} row{modbusPreview.row_count === 1 ? "" : "s"} returned</span>
                            </div>
                            <div className="data-connectors-preview-table-wrap">
                              <table className="data-connectors-preview-table">
                                <thead>
                                  <tr>
                                    {modbusPreview.columns.map((column) => (
                                      <th key={column}>{column}</th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody>
                                  {modbusPreview.rows.map((row, rowIndex) => (
                                    <tr key={`modbus-row-${rowIndex}`}>
                                      {modbusPreview.columns.map((column) => (
                                        <td key={`${rowIndex}-${column}`}>{String(row[column] ?? "")}</td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        ) : <p className="data-connectors-file-name">Run Preview Data to validate the register map and scaling output.</p>}
                      </div>
                    </>
                  ) : null}

                  {form.connectorType === "historian" ? (
                    <>
                      <label className="plant-genie-field">
                        <span>Subtype</span>
                        <select value={form.historianSubtype} onChange={(event) => updateField("historianSubtype", event.target.value)}>
                          {HISTORIAN_SUBTYPE_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                        {fieldErrors.historianSubtype ? <span className="plant-genie-field-error">{fieldErrors.historianSubtype}</span> : null}
                      </label>

                      <label className="plant-genie-field">
                        <span>Authentication</span>
                        <select value={form.historianAuthenticationMode} onChange={(event) => updateField("historianAuthenticationMode", event.target.value)}>
                          {HISTORIAN_AUTH_MODE_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                        {fieldErrors.historianAuthenticationMode ? <span className="plant-genie-field-error">{fieldErrors.historianAuthenticationMode}</span> : null}
                      </label>

                      <label className="plant-genie-field">
                        <span>Retrieval Mode</span>
                        <select value={form.historianRetrievalMode} onChange={(event) => updateField("historianRetrievalMode", event.target.value)}>
                          {HISTORIAN_RETRIEVAL_MODE_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                        {fieldErrors.historianRetrievalMode ? <span className="plant-genie-field-error">{fieldErrors.historianRetrievalMode}</span> : null}
                      </label>

                      <label className="plant-genie-field">
                        <span>Time Range</span>
                        <div className="data-connectors-editor-actions">
                          <input type="number" min={1} max={10000} value={form.historianTimeRangeValue} onChange={(event) => updateField("historianTimeRangeValue", event.target.value)} />
                          <select value={form.historianTimeRangeUnit} onChange={(event) => updateField("historianTimeRangeUnit", event.target.value)}>
                            {HISTORIAN_TIME_RANGE_UNIT_OPTIONS.map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>
                        </div>
                        {fieldErrors.historianTimeRangeValue ? <span className="plant-genie-field-error">{fieldErrors.historianTimeRangeValue}</span> : null}
                      </label>

                      <label className="plant-genie-field">
                        <span>Sampling Interval</span>
                        <input type="text" value={form.historianSamplingInterval} onChange={(event) => updateField("historianSamplingInterval", event.target.value)} placeholder="5m / 1h" />
                      </label>

                      <label className="plant-genie-field">
                        <span>Max Data Points</span>
                        <input type="number" min={1} max={5000} value={form.historianMaxDataPoints} onChange={(event) => updateField("historianMaxDataPoints", event.target.value)} />
                        {fieldErrors.historianMaxDataPoints ? <span className="plant-genie-field-error">{fieldErrors.historianMaxDataPoints}</span> : null}
                      </label>

                      <label className="plant-genie-field data-connectors-toggle-field">
                        <span>Cache</span>
                        <label className="data-connectors-toggle">
                          <input type="checkbox" checked={form.historianCacheEnabled} onChange={(event) => updateField("historianCacheEnabled", event.target.checked)} />
                          <span>Reuse recent preview/browse results</span>
                        </label>
                      </label>

                      {form.historianAuthenticationMode === "basic" ? (
                        <>
                          <label className="plant-genie-field">
                            <span>Username</span>
                            <input type="text" value={form.historianUsername} onChange={(event) => updateField("historianUsername", event.target.value)} />
                            {fieldErrors.historianUsername ? <span className="plant-genie-field-error">{fieldErrors.historianUsername}</span> : null}
                          </label>

                          <label className="plant-genie-field">
                            <span>Password</span>
                            <input type="password" value={form.historianPassword} onChange={(event) => updateField("historianPassword", event.target.value)} placeholder={isEditing ? "Leave blank to keep stored secret" : "Enter password"} />
                            {fieldErrors.historianPassword ? <span className="plant-genie-field-error">{fieldErrors.historianPassword}</span> : null}
                          </label>
                        </>
                      ) : null}

                      {form.historianAuthenticationMode === "bearer" ? (
                        <label className="plant-genie-field plant-genie-field-full">
                          <span>Bearer Token</span>
                          <input type="password" value={form.historianToken} onChange={(event) => updateField("historianToken", event.target.value)} placeholder={isEditing ? "Leave blank to keep stored token" : "Enter API token"} />
                          {fieldErrors.historianToken ? <span className="plant-genie-field-error">{fieldErrors.historianToken}</span> : null}
                        </label>
                      ) : null}

                      {form.historianSubtype === "osisoft_pi" ? (
                        <>
                          <label className="plant-genie-field">
                            <span>PI Server URL</span>
                            <input type="text" value={form.historianPiServerUrl} onChange={(event) => updateField("historianPiServerUrl", event.target.value)} placeholder="https://piwebapi.example.com/piwebapi" />
                            {fieldErrors.historianPiServerUrl ? <span className="plant-genie-field-error">{fieldErrors.historianPiServerUrl}</span> : null}
                          </label>

                          <label className="plant-genie-field">
                            <span>AF Server</span>
                            <input type="text" value={form.historianAfServer} onChange={(event) => updateField("historianAfServer", event.target.value)} placeholder="AFSERVER01" />
                            {fieldErrors.historianAfServer ? <span className="plant-genie-field-error">{fieldErrors.historianAfServer}</span> : null}
                          </label>

                          <label className="plant-genie-field">
                            <span>AF Database</span>
                            <input type="text" value={form.historianAfDatabase} onChange={(event) => updateField("historianAfDatabase", event.target.value)} placeholder="PlantModel" />
                            {fieldErrors.historianAfDatabase ? <span className="plant-genie-field-error">{fieldErrors.historianAfDatabase}</span> : null}
                          </label>

                          <div className="plant-genie-field plant-genie-field-full">
                            <span>Browse Assets / Attributes</span>
                            <div className="data-connectors-editor-actions">
                              <input type="text" value={form.historianSearchQuery} onChange={(event) => updateField("historianSearchQuery", event.target.value)} placeholder="Search PI assets or attributes" />
                              <button type="button" className="command-btn" onClick={() => void handleHistorianBrowse()} disabled={isHistorianBrowseLoading || isSaving || isDeleting || isTogglingActive}>
                                {isHistorianBrowseLoading ? <LoaderCircle size={12} className="animate-spin" /> : <FolderTree size={12} />}
                                <span>{isHistorianBrowseLoading ? "Searching..." : "Browse"}</span>
                              </button>
                            </div>
                            {historianBrowseError ? <div className="plant-genie-inline-alert error"><span>{historianBrowseError}</span></div> : null}
                            {historianBrowseResults.length > 0 ? (
                              <div className="data-connectors-opcua-selection-list">
                                {historianBrowseResults.map((item) => (
                                  <div key={item.web_id} className="data-connectors-opcua-selection-item">
                                    <div className="data-connectors-opcua-selection-copy">
                                      <strong>{item.label}</strong>
                                      <span>{item.path}</span>
                                    </div>
                                    <button type="button" className="command-btn" onClick={() => addHistorianBrowseItem(item)}>
                                      <Plus size={12} />
                                      <span>Add Mapping</span>
                                    </button>
                                  </div>
                                ))}
                              </div>
                            ) : <p className="data-connectors-file-name">Search PI to add AF attributes, or enter manual paths below.</p>}
                          </div>

                          <div className="plant-genie-field plant-genie-field-full">
                            <span>Tag Mapping</span>
                            <div className="data-connectors-opcua-selection-list">
                              {form.historianTagMappings.length > 0 ? form.historianTagMappings.map((mapping, index) => (
                                <div key={`${mapping.webId || mapping.manualPath || index}`} className="data-connectors-opcua-selection-item">
                                  <label className="plant-genie-field">
                                    <span>Browsed Path</span>
                                    <input type="text" value={mapping.displayPath} onChange={(event) => updateHistorianTagMapping(index, "displayPath", event.target.value)} placeholder="AF path" />
                                  </label>
                                  <label className="plant-genie-field">
                                    <span>Manual Tag / Path</span>
                                    <input type="text" value={mapping.manualPath} onChange={(event) => updateHistorianTagMapping(index, "manualPath", event.target.value)} placeholder="Element|Attribute or full AF path" />
                                  </label>
                                  <label className="plant-genie-field">
                                    <span>Internal Tag</span>
                                    <input type="text" value={mapping.internalTag} onChange={(event) => updateHistorianTagMapping(index, "internalTag", event.target.value)} placeholder="plant.line1.flow" />
                                  </label>
                                  <button type="button" className="command-btn danger" onClick={() => removeHistorianTagMapping(index)}>
                                    <Trash2 size={12} />
                                    <span>Remove</span>
                                  </button>
                                </div>
                              )) : <p className="data-connectors-file-name">No PI mappings configured yet.</p>}
                            </div>
                            <div className="data-connectors-editor-actions">
                              <button type="button" className="command-btn" onClick={addHistorianManualMapping}>
                                <Plus size={12} />
                                <span>Add Manual Mapping</span>
                              </button>
                            </div>
                            {fieldErrors.historianTagMappings ? <span className="plant-genie-field-error">{fieldErrors.historianTagMappings}</span> : null}
                          </div>
                        </>
                      ) : (
                        <>
                          <label className="plant-genie-field">
                            <span>Mode</span>
                            <select value={form.historianGenericMode} onChange={(event) => updateField("historianGenericMode", event.target.value)}>
                              {HISTORIAN_GENERIC_MODE_OPTIONS.map((option) => (
                                <option key={option.value} value={option.value}>
                                  {option.label}
                                </option>
                              ))}
                            </select>
                            {fieldErrors.historianGenericMode ? <span className="plant-genie-field-error">{fieldErrors.historianGenericMode}</span> : null}
                          </label>

                          {form.historianGenericMode === "sql" ? (
                            <>
                              <label className="plant-genie-field">
                                <span>DB Type</span>
                                <select value={form.historianDbType} onChange={(event) => updateField("historianDbType", event.target.value)}>
                                  {SQL_DB_TYPE_OPTIONS.map((option) => (
                                    <option key={option.value} value={option.value}>
                                      {option.label}
                                    </option>
                                  ))}
                                </select>
                              </label>
                              <label className="plant-genie-field">
                                <span>Host</span>
                                <input type="text" value={form.historianHost} onChange={(event) => updateField("historianHost", event.target.value)} />
                                {fieldErrors.historianHost ? <span className="plant-genie-field-error">{fieldErrors.historianHost}</span> : null}
                              </label>
                              <label className="plant-genie-field">
                                <span>Port</span>
                                <input type="number" min={1} max={65535} value={form.historianPort} onChange={(event) => updateField("historianPort", event.target.value)} />
                                {fieldErrors.historianPort ? <span className="plant-genie-field-error">{fieldErrors.historianPort}</span> : null}
                              </label>
                              <label className="plant-genie-field">
                                <span>Database</span>
                                <input type="text" value={form.historianDatabase} onChange={(event) => updateField("historianDatabase", event.target.value)} />
                                {fieldErrors.historianDatabase ? <span className="plant-genie-field-error">{fieldErrors.historianDatabase}</span> : null}
                              </label>
                              <label className="plant-genie-field data-connectors-toggle-field">
                                <span>SSL</span>
                                <label className="data-connectors-toggle">
                                  <input type="checkbox" checked={form.historianSslEnabled} onChange={(event) => updateField("historianSslEnabled", event.target.checked)} />
                                  <span>Enable SSL</span>
                                </label>
                              </label>
                              <label className="plant-genie-field plant-genie-field-full">
                                <span>Query</span>
                                <textarea value={form.historianQuery} onChange={(event) => updateField("historianQuery", event.target.value)} rows={6} />
                                {fieldErrors.historianQuery ? <span className="plant-genie-field-error">{fieldErrors.historianQuery}</span> : null}
                              </label>
                            </>
                          ) : (
                            <>
                              <label className="plant-genie-field plant-genie-field-full">
                                <span>Endpoint URL</span>
                                <input type="text" value={form.historianEndpointUrl} onChange={(event) => updateField("historianEndpointUrl", event.target.value)} placeholder="https://api.example.com/history" />
                                {fieldErrors.historianEndpointUrl ? <span className="plant-genie-field-error">{fieldErrors.historianEndpointUrl}</span> : null}
                              </label>
                              <label className="plant-genie-field">
                                <span>Array Path</span>
                                <input type="text" value={form.historianArrayPath} onChange={(event) => updateField("historianArrayPath", event.target.value)} placeholder="items" />
                              </label>
                              <label className="plant-genie-field">
                                <span>Timeout (ms)</span>
                                <input type="number" min={100} max={60000} value={form.historianTimeoutMs} onChange={(event) => updateField("historianTimeoutMs", event.target.value)} />
                                {fieldErrors.historianTimeoutMs ? <span className="plant-genie-field-error">{fieldErrors.historianTimeoutMs}</span> : null}
                              </label>
                            </>
                          )}

                          <label className="plant-genie-field">
                            <span>Timestamp Field</span>
                            <input type="text" value={form.historianTimestampField} onChange={(event) => updateField("historianTimestampField", event.target.value)} placeholder="timestamp" />
                            {fieldErrors.historianTimestampField ? <span className="plant-genie-field-error">{fieldErrors.historianTimestampField}</span> : null}
                          </label>
                          <label className="plant-genie-field">
                            <span>Tag Field</span>
                            <input type="text" value={form.historianTagField} onChange={(event) => updateField("historianTagField", event.target.value)} placeholder="tag" />
                            {fieldErrors.historianTagField ? <span className="plant-genie-field-error">{fieldErrors.historianTagField}</span> : null}
                          </label>
                          <label className="plant-genie-field">
                            <span>Value Field</span>
                            <input type="text" value={form.historianValueField} onChange={(event) => updateField("historianValueField", event.target.value)} placeholder="value" />
                            {fieldErrors.historianValueField ? <span className="plant-genie-field-error">{fieldErrors.historianValueField}</span> : null}
                          </label>
                        </>
                      )}

                      <div className="plant-genie-field plant-genie-field-full data-connectors-inline-actions">
                        <span>Historian Actions</span>
                        <div className="data-connectors-editor-actions">
                          <button type="button" className="command-btn" onClick={() => void handleHistorianPreview()} disabled={isHistorianPreviewLoading || isSaving || isDeleting || isTogglingActive}>
                            {isHistorianPreviewLoading ? <LoaderCircle size={12} className="animate-spin" /> : <DatabaseZap size={12} />}
                            <span>{isHistorianPreviewLoading ? "Loading Preview..." : "Preview Data"}</span>
                          </button>
                          <button type="button" className="command-btn" onClick={() => void handleConnectTest()} disabled={isTesting || isSaving || isDeleting || isTogglingActive}>
                            {isTesting ? <LoaderCircle size={12} className="animate-spin" /> : <PlugZap size={12} />}
                            <span>{isTesting ? "Connecting..." : "Test Connection"}</span>
                          </button>
                        </div>
                      </div>

                      <div className="plant-genie-field plant-genie-field-full">
                        <span>Preview</span>
                        {historianPreviewError ? <div className="plant-genie-inline-alert error"><span>{historianPreviewError}</span></div> : null}
                        {historianPreview && historianPreview.columns.length > 0 ? (
                          <div className="data-connectors-opcua-browser">
                            <div className="data-connectors-status-panel">
                              <span>{historianPreview.row_count} row{historianPreview.row_count === 1 ? "" : "s"} returned</span>
                            </div>
                            <div className="data-connectors-preview-table-wrap">
                              <table className="data-connectors-preview-table">
                                <thead>
                                  <tr>
                                    {historianPreview.columns.map((column) => (
                                      <th key={column}>{column}</th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody>
                                  {historianPreview.rows.map((row, rowIndex) => (
                                    <tr key={`historian-row-${rowIndex}`}>
                                      {historianPreview.columns.map((column) => (
                                        <td key={`${rowIndex}-${column}`}>{String(row[column] ?? "")}</td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        ) : <p className="data-connectors-file-name">Run Preview Data to validate historian normalization into timestamp, tag, and value rows.</p>}
                      </div>
                    </>
                  ) : null}

                  {form.connectorType === "sql" ? (
                    <>
                      <label className="plant-genie-field">
                        <span>DB Type</span>
                        <select value={form.sqlDbType} onChange={(event) => handleSqlDbTypeChange(event.target.value)}>
                          {SQL_DB_TYPE_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                        {fieldErrors.sqlDbType ? <span className="plant-genie-field-error">{fieldErrors.sqlDbType}</span> : null}
                      </label>

                      <label className="plant-genie-field">
                        <span>Host</span>
                        <input type="text" value={form.sqlHost} onChange={(event) => updateField("sqlHost", event.target.value)} placeholder="historian.internal" />
                        {fieldErrors.sqlHost ? <span className="plant-genie-field-error">{fieldErrors.sqlHost}</span> : null}
                      </label>

                      <label className="plant-genie-field">
                        <span>Port</span>
                        <input type="number" min={1} max={65535} value={form.sqlPort} onChange={(event) => updateField("sqlPort", event.target.value)} />
                        {fieldErrors.sqlPort ? <span className="plant-genie-field-error">{fieldErrors.sqlPort}</span> : null}
                      </label>

                      <label className="plant-genie-field">
                        <span>Database</span>
                        <input type="text" value={form.sqlDatabase} onChange={(event) => updateField("sqlDatabase", event.target.value)} placeholder="process_history" />
                        {fieldErrors.sqlDatabase ? <span className="plant-genie-field-error">{fieldErrors.sqlDatabase}</span> : null}
                      </label>

                      <label className="plant-genie-field">
                        <span>Username</span>
                        <input type="text" value={form.sqlUsername} onChange={(event) => updateField("sqlUsername", event.target.value)} placeholder="historian_reader" />
                        {fieldErrors.sqlUsername ? <span className="plant-genie-field-error">{fieldErrors.sqlUsername}</span> : null}
                      </label>

                      <label className="plant-genie-field data-connectors-toggle-field">
                        <span>SSL</span>
                        <label className="data-connectors-toggle">
                          <input type="checkbox" checked={form.sqlSslEnabled} onChange={(event) => updateField("sqlSslEnabled", event.target.checked)} />
                          <span>Enable SSL</span>
                        </label>
                      </label>

                      <label className="plant-genie-field">
                        <span>Pool Size</span>
                        <input type="number" min={1} max={50} value={form.sqlPoolSize} onChange={(event) => updateField("sqlPoolSize", event.target.value)} />
                        {fieldErrors.sqlPoolSize ? <span className="plant-genie-field-error">{fieldErrors.sqlPoolSize}</span> : null}
                      </label>

                      <label className="plant-genie-field">
                        <span>Refresh Mode</span>
                        <select value={form.sqlRefreshMode} onChange={(event) => updateField("sqlRefreshMode", event.target.value)}>
                          {SQL_REFRESH_MODE_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                        {fieldErrors.sqlRefreshMode ? <span className="plant-genie-field-error">{fieldErrors.sqlRefreshMode}</span> : null}
                      </label>

                      <label className="plant-genie-field plant-genie-field-full">
                        <span>Password</span>
                        <input
                          type="password"
                          value={form.sqlPassword}
                          onChange={(event) => updateField("sqlPassword", event.target.value)}
                          placeholder={isEditing ? "Leave blank to keep stored secret" : "Enter password"}
                        />
                        {fieldErrors.sqlPassword ? <span className="plant-genie-field-error">{fieldErrors.sqlPassword}</span> : null}
                      </label>

                      <label className="plant-genie-field">
                        <span>Query Mode</span>
                        <select value={form.sqlQueryMode} onChange={(event) => updateField("sqlQueryMode", event.target.value)}>
                          {SQL_QUERY_MODE_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                        {fieldErrors.sqlQueryMode ? <span className="plant-genie-field-error">{fieldErrors.sqlQueryMode}</span> : null}
                      </label>

                      {form.sqlQueryMode === "table" ? (
                        <>
                          <label className="plant-genie-field">
                            <span>Schema</span>
                            <input type="text" value={form.sqlTableSchema} onChange={(event) => updateField("sqlTableSchema", event.target.value)} placeholder="public" />
                          </label>

                          <label className="plant-genie-field plant-genie-field-full">
                            <span>Table</span>
                            <div className="data-connectors-editor-actions">
                              <div className="data-connectors-select-wrap">
                                <select value={form.sqlTableName} onChange={(event) => { void handleSqlTableChange(event.target.value); }}>
                                  <option value="">Select table</option>
                                  {sqlTables.map((table) => (
                                    <option key={table.label} value={table.label}>
                                      {table.label}
                                    </option>
                                  ))}
                                </select>
                                <ChevronDown size={14} />
                              </div>
                              <button type="button" className="command-btn" onClick={() => { void loadSqlSchema(); }} disabled={isSqlSchemaLoading || isSaving || isDeleting || isTogglingActive}>
                                {isSqlSchemaLoading ? <LoaderCircle size={12} className="animate-spin" /> : <DatabaseZap size={12} />}
                                <span>{isSqlSchemaLoading ? "Loading..." : "Load Tables"}</span>
                              </button>
                            </div>
                            {fieldErrors.sqlTableName ? <span className="plant-genie-field-error">{fieldErrors.sqlTableName}</span> : null}
                          </label>
                        </>
                      ) : (
                        <label className="plant-genie-field plant-genie-field-full">
                          <span>Custom Query</span>
                          <textarea value={form.sqlCustomQuery} onChange={(event) => updateField("sqlCustomQuery", event.target.value)} rows={7} />
                          {fieldErrors.sqlCustomQuery ? <span className="plant-genie-field-error">{fieldErrors.sqlCustomQuery}</span> : null}
                        </label>
                      )}

                      <label className="plant-genie-field">
                        <span>Timestamp Column</span>
                        <input type="text" value={form.sqlTimestampColumn} onChange={(event) => updateField("sqlTimestampColumn", event.target.value)} placeholder="timestamp" />
                      </label>

                      <label className="plant-genie-field">
                        <span>State Column</span>
                        <input type="text" value={form.sqlStateColumn} onChange={(event) => updateField("sqlStateColumn", event.target.value)} placeholder="state" />
                      </label>

                      <label className="plant-genie-field">
                        <span>Quality Column</span>
                        <input type="text" value={form.sqlQualityColumn} onChange={(event) => updateField("sqlQualityColumn", event.target.value)} placeholder="quality" />
                      </label>

                      <div className="plant-genie-field plant-genie-field-full data-connectors-inline-actions">
                        <span>SQL Actions</span>
                        <div className="data-connectors-editor-actions">
                          <button type="button" className="command-btn" onClick={() => void handleSqlPreview()} disabled={isSqlPreviewLoading || isSaving || isDeleting || isTogglingActive}>
                            {isSqlPreviewLoading ? <LoaderCircle size={12} className="animate-spin" /> : <DatabaseZap size={12} />}
                            <span>{isSqlPreviewLoading ? "Loading Preview..." : "Preview Data"}</span>
                          </button>
                          <button type="button" className="command-btn" onClick={() => void handleConnectTest()} disabled={isTesting || isSaving || isDeleting || isTogglingActive}>
                            {isTesting ? <LoaderCircle size={12} className="animate-spin" /> : <PlugZap size={12} />}
                            <span>{isTesting ? "Connecting..." : "Test Connection"}</span>
                          </button>
                        </div>
                      </div>

                      <div className="plant-genie-field plant-genie-field-full">
                        <span>Tag Mapping</span>
                        <div className="data-connectors-opcua-selection-list">
                          {form.sqlTagMappings.length > 0 ? form.sqlTagMappings.map((mapping, index) => (
                            <div key={`${mapping.sourceColumn || "mapping"}-${index}`} className="data-connectors-opcua-selection-item">
                              <label className="plant-genie-field">
                                <span>Source Column</span>
                                <select value={mapping.sourceColumn} onChange={(event) => updateSqlTagMapping(index, "sourceColumn", event.target.value)}>
                                  <option value="">Select column</option>
                                  {sqlColumns.map((column) => (
                                    <option key={column.name} value={column.name}>
                                      {column.name} ({column.data_type})
                                    </option>
                                  ))}
                                </select>
                              </label>
                              <label className="plant-genie-field">
                                <span>Internal Tag</span>
                                <input type="text" value={mapping.targetTag} onChange={(event) => updateSqlTagMapping(index, "targetTag", event.target.value)} placeholder="line1.temperature" />
                              </label>
                              <button type="button" className="command-btn danger" onClick={() => removeSqlTagMapping(index)}>
                                <Trash2 size={12} />
                                <span>Remove</span>
                              </button>
                            </div>
                          )) : <p className="data-connectors-file-name">No SQL tag mappings configured yet.</p>}
                        </div>
                        <div className="data-connectors-editor-actions">
                          <button type="button" className="command-btn" onClick={addSqlTagMapping}>
                            <Plus size={12} />
                            <span>Add Mapping</span>
                          </button>
                        </div>
                        {fieldErrors.sqlTagMappings ? <span className="plant-genie-field-error">{fieldErrors.sqlTagMappings}</span> : null}
                      </div>

                      <div className="plant-genie-field plant-genie-field-full">
                        <span>Preview</span>
                        {sqlSchemaError ? <div className="plant-genie-inline-alert error"><span>{sqlSchemaError}</span></div> : null}
                        {sqlPreview && sqlPreview.columns.length > 0 ? (
                          <div className="data-connectors-opcua-browser">
                            <div className="data-connectors-status-panel">
                              <span>{sqlPreview.row_count} row{sqlPreview.row_count === 1 ? "" : "s"} returned</span>
                            </div>
                            <div className="data-connectors-preview-table-wrap">
                              <table className="data-connectors-preview-table">
                                <thead>
                                  <tr>
                                    {sqlPreview.columns.map((column) => (
                                      <th key={column}>{column}</th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody>
                                  {sqlPreview.rows.map((row, rowIndex) => (
                                    <tr key={`row-${rowIndex}`}>
                                      {sqlPreview.columns.map((column) => (
                                        <td key={`${rowIndex}-${column}`}>{String(row[column] ?? "")}</td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        ) : <p className="data-connectors-file-name">Run Preview Data to inspect rows and confirm your mappings.</p>}
                      </div>
                    </>
                  ) : null}
                </div>

                <div className="plant-genie-form-help">
                  <DatabaseZap size={13} />
                  <span>Profiles are stored in backend storage. Secret fields are encrypted and are not returned to the browser after save.</span>
                </div>

                {formError ? (
                  <div className="plant-genie-inline-alert error">
                    <span>{formError}</span>
                  </div>
                ) : null}

                <div className="plant-genie-form-actions">
                  <button type="button" className="command-btn" onClick={() => resetToCreateMode(form.connectorType)} disabled={isSaving || isDeleting}>
                    Reset
                  </button>
                  <button type="button" className="command-btn primary" onClick={() => void handleSubmit()} disabled={isSaving || isDeleting || isTogglingActive || isTesting}>
                    <CheckCircle2 size={12} />
                    <span>{isSaving ? "Saving..." : isEditing ? "Save Changes" : "Create Profile"}</span>
                  </button>
                </div>
                </div>
              </section>
            </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}