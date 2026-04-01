import { describe, expect, test } from "vitest";

import {
  mapIndustrialConnectorFormToRequest,
  validateIndustrialConnectorForm,
  type IndustrialConnectionFormState,
} from "./industrialConnectorPayload";

const createBaseForm = (): IndustrialConnectionFormState => ({
  name: "Primary connector",
  connectorType: "opcua",
  pollIntervalMs: "5000",
  opcuaServerUrl: "opc.tcp://192.168.1.10:4840",
  opcuaSecurityMode: "none",
  opcuaUsername: "",
  opcuaPassword: "",
  opcuaNodeConfig: '["ns=2;s=Plant/Line1/TagA"]',
  mqttBrokerUrl: "mqtt://broker.example.com:1883",
  mqttTopic: "plant/line1/#",
  mqttClientId: "client-1",
  mqttUsername: "",
  mqttPassword: "",
  sqlHost: "historian.example.com",
  sqlPort: "5432",
  sqlDatabase: "runtime",
  sqlUsername: "operator",
  sqlPassword: "secret",
  sqlQueryConfig: '{"query":"SELECT tag, value, timestamp FROM live_signals","tagColumn":"tag","valueColumn":"value","timestampColumn":"timestamp"}',
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
        username: null,
        subscription_config: ["ns=2;s=Plant/Line1/TagA"],
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
        host: "historian.example.com",
        port: 5432,
        database: "runtime",
        username: "operator",
        query: "SELECT tag, value, timestamp FROM live_signals",
        tag_column: "tag",
        value_column: "value",
        timestamp_column: "timestamp",
      },
      secrets: { password: "secret" },
    });
  });

  test("returns inline validation for invalid opcua subscription config", () => {
    const form = {
      ...createBaseForm(),
      opcuaNodeConfig: "{not valid json}",
    } satisfies IndustrialConnectionFormState;

    expect(validateIndustrialConnectorForm(form, { isEditing: false }).opcuaNodeConfig).toBe(
      "Subscription / Node config must be valid JSON."
    );
  });
});