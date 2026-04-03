import { describe, expect, test } from "vitest";

import {
  mapIndustrialConnectorFormToRequest,
  serializeOpcuaSubscriptionConfig,
  validateIndustrialConnectorForm,
  type IndustrialConnectionFormState,
} from "./industrialConnectorPayload";

const createBaseForm = (): IndustrialConnectionFormState => ({
  name: "Primary connector",
  connectorType: "opcua",
  pollIntervalMs: "5000",
  opcuaServerUrl: "opc.tcp://192.168.1.10:4840",
  opcuaSecurityMode: "none",
  opcuaSecurityPolicy: "",
  opcuaAuthMode: "anonymous",
  opcuaUsername: "",
  opcuaPassword: "",
  opcuaSessionTimeoutMs: "60000",
  opcuaBrowseRootNodeId: "i=85",
  opcuaSelectedNodes: [
    {
      nodeId: "ns=2;s=Plant/Line1/TagA",
      browseName: "TagA",
      displayName: "TagA",
      nodeClass: "Variable",
      tag: "PLC_TAG_A",
    },
  ],
  opcuaTrustListNames: [],
  opcuaTrustListPems: [],
  opcuaClientCertificateName: "",
  opcuaClientCertificatePem: "",
  opcuaClientPrivateKeyName: "",
  opcuaClientPrivateKeyPem: "",
  opcuaClientPrivateKeyPassword: "",
  opcuaNodeConfig: serializeOpcuaSubscriptionConfig(
    [
      {
        nodeId: "ns=2;s=Plant/Line1/TagA",
        browseName: "TagA",
        displayName: "TagA",
        nodeClass: "Variable",
        tag: "PLC_TAG_A",
      },
    ],
    "i=85"
  ),
  mqttBrokerUrl: "mqtt://broker.example.com:1883",
  mqttTopic: "plant/line1/#",
  mqttClientId: "client-1",
  mqttUsername: "",
  mqttPassword: "",
  mqttQos: "1",
  mqttKeepAlive: "45",
  mqttTlsEnabled: false,
  mqttTlsCertificateName: "",
  mqttTlsCertificatePem: "",
  sqlDbType: "postgresql",
  sqlHost: "historian.example.com",
  sqlPort: "5432",
  sqlDatabase: "runtime",
  sqlUsername: "operator",
  sqlPassword: "secret",
  sqlSslEnabled: false,
  sqlPoolSize: "5",
  sqlQueryMode: "table",
  sqlRefreshMode: "latest_row",
  sqlTableSchema: "public",
  sqlTableName: "live_signals",
  sqlCustomQuery: "SELECT * FROM live_signals",
  sqlTimestampColumn: "timestamp",
  sqlStateColumn: "state",
  sqlQualityColumn: "quality",
  sqlTagMappings: [{ sourceColumn: "value", targetTag: "runtime.value" }],
  modbusHost: "192.168.1.50",
  modbusPort: "502",
  modbusUnitId: "1",
  modbusTimeoutMs: "5000",
  modbusRetryAttempts: "2",
  modbusAutoReconnect: true,
  modbusBatchRead: true,
  modbusMaxRegistersPerRequest: "120",
  modbusEnableWrite: true,
  modbusFunctionCode: "fc6",
  modbusConfirmBeforeWrite: true,
  modbusWriteRateLimitMs: "1000",
  modbusTagMappings: [
    {
      registerType: "holding_register",
      address: "40001",
      quantity: "2",
      dataType: "float32",
      endianness: "big",
      wordSwap: false,
      internalTag: "flow_rate",
      multiplier: "1.5",
      offset: "2",
      engineeringUnits: "gpm",
      writable: true,
    },
  ],
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
});

describe("industrialConnectorPayload", () => {
  test("maps opcua form state to backend request payload", () => {
    const form = createBaseForm();

    const payload = mapIndustrialConnectorFormToRequest(form, { isEditing: false });

    expect(payload).toEqual({
      name: "Primary connector",
      connector_type: "opcua",
      poll_interval_ms: 5000,
      config: {
        server_url: "opc.tcp://192.168.1.10:4840",
        security_mode: null,
        security_policy: null,
        authentication_mode: "anonymous",
        username: null,
        session_timeout_ms: 60000,
        browse_root_node_id: "i=85",
        trust_list_names: [],
        client_certificate_name: null,
        client_private_key_name: null,
        subscription_config: {
          root_node_id: "i=85",
          nodes: [
            {
              node_id: "ns=2;s=Plant/Line1/TagA",
              browse_name: "TagA",
              display_name: "TagA",
              node_class: "Variable",
              tag: "PLC_TAG_A",
            },
          ],
        },
        node_ids: ["ns=2;s=Plant/Line1/TagA"],
      },
      secrets: {},
    });
  });

  test("maps mqtt form state to backend request payload", () => {
    const form = {
      ...createBaseForm(),
      connectorType: "mqtt",
      name: "MQTT bridge",
      pollIntervalMs: "2500",
      mqttUsername: "scada",
      mqttPassword: "broker-secret",
    } satisfies IndustrialConnectionFormState;

    const payload = mapIndustrialConnectorFormToRequest(form, { isEditing: false });

    expect(payload).toEqual({
      name: "MQTT bridge",
      connector_type: "mqtt",
      poll_interval_ms: 2500,
      config: {
        broker_url: "mqtt://broker.example.com:1883",
        topic: "plant/line1/#",
        client_id: "client-1",
        username: "scada",
        qos: 1,
        keep_alive: 45,
        tls_enabled: false,
        certificate_name: null,
      },
      secrets: { password: "broker-secret" },
    });
  });

  test("maps sql form state to backend request payload", () => {
    const form = {
      ...createBaseForm(),
      connectorType: "sql",
      name: "Historian",
    } satisfies IndustrialConnectionFormState;

    const payload = mapIndustrialConnectorFormToRequest(form, { isEditing: false });

    expect(payload).toEqual({
      name: "Historian",
      connector_type: "sql",
      poll_interval_ms: 5000,
      config: {
        db_type: "postgresql",
        host: "historian.example.com",
        port: 5432,
        database: "runtime",
        username: "operator",
        ssl_enabled: false,
        pool_size: 5,
        query_mode: "table",
        refresh_mode: "latest_row",
        table_schema: "public",
        table_name: "live_signals",
        custom_query: "SELECT * FROM live_signals",
        timestamp_column: "timestamp",
        state_column: "state",
        quality_column: "quality",
        tag_mappings: [{ source_column: "value", target_tag: "runtime.value" }],
      },
      secrets: { password: "secret" },
    });
  });

  test("maps modbus tcp form state to backend request payload", () => {
    const form = {
      ...createBaseForm(),
      connectorType: "modbus_tcp",
      name: "Boiler Modbus",
      pollIntervalMs: "2000",
    } satisfies IndustrialConnectionFormState;

    const payload = mapIndustrialConnectorFormToRequest(form, { isEditing: false });

    expect(payload).toEqual({
      name: "Boiler Modbus",
      connector_type: "modbus_tcp",
      poll_interval_ms: 2000,
      config: {
        host: "192.168.1.50",
        port: 502,
        unit_id: 1,
        timeout_ms: 5000,
        retry_attempts: 2,
        auto_reconnect: true,
        batch_read: true,
        max_registers_per_request: 120,
        enable_write: true,
        write_function_code: "fc6",
        confirm_before_write: true,
        write_rate_limit_ms: 1000,
        tag_mappings: [
          {
            register_type: "holding_register",
            address: 40001,
            quantity: 2,
            data_type: "float32",
            endianness: "big",
            word_swap: false,
            internal_tag: "flow_rate",
            multiplier: 1.5,
            offset: 2,
            engineering_units: "gpm",
            writable: true,
          },
        ],
      },
      secrets: {},
    });
  });

  test("returns inline validation for invalid opcua subscription config", () => {
    const form = {
      ...createBaseForm(),
      opcuaSecurityMode: "sign",
      opcuaSecurityPolicy: "basic256sha256",
      opcuaClientCertificateName: "client-cert.pem",
      opcuaClientPrivateKeyName: "client-key.pem",
      opcuaSelectedNodes: [],
      opcuaNodeConfig: "{not valid json}",
    } satisfies IndustrialConnectionFormState;

    expect(validateIndustrialConnectorForm(form, { isEditing: false }).opcuaNodeConfig).toBe(
      "Subscription / Node config must be valid JSON."
    );
  });
});