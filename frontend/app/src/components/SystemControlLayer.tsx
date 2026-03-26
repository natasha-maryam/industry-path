import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  createUNSSocket,
  getUNSRows,
  mapUNSTag,
  queryUNS,
  runUNSScript,
  setUNSConnector,
  type EngineeringTableResponseRow,
  type UNSRow,
} from "../services/api";

type SystemControlLayerProps = {
  onRowsUpdate?: (rows: EngineeringTableResponseRow[]) => void;
};

const toEngineeringRow = (row: UNSRow): EngineeringTableResponseRow => ({
  id: row.tag,
  tag: row.tag,
  type: row.type ?? "unknown",
  subtype: row.subtype ?? null,
  description: row.behavior_card ?? null,
  system: null,
  equipment: row.equipment ?? null,
  process_role: null,
  measures: [],
  controls: row.controls ?? [],
  controlled_by: [],
  signal_inputs: [],
  signal_outputs: [],
  upstream: row.upstream ?? [],
  downstream: row.downstream ?? [],
  flow_path: [],
  current_value: row.current_value ?? null,
  state: row.state ?? null,
  setpoint: row.setpoint ?? null,
  mode: row.mode ?? null,
  unit: null,
  range_min: null,
  range_max: null,
  fail_state: null,
  power: null,
  document_source: [],
  line_reference: [],
  confidence: 0.75,
  num_connections: (row.controls?.length ?? 0) + (row.upstream?.length ?? 0) + (row.downstream?.length ?? 0),
  num_upstream: row.upstream?.length ?? 0,
  num_downstream: row.downstream?.length ?? 0,
  control_chain: row.controls ?? [],
  flow_chain: [...(row.upstream ?? []), ...(row.downstream ?? [])],
  is_orphan: (row.upstream?.length ?? 0) + (row.downstream?.length ?? 0) === 0,
  is_controlled: (row.upstream?.length ?? 0) > 0,
  is_actuated: (row.controls?.length ?? 0) > 0,
  warnings: [],
  grounded_fields: {},
  derived_fields: {},
  traceability: [],
});

const mergeByTag = (existing: EngineeringTableResponseRow[], updates: EngineeringTableResponseRow[]): EngineeringTableResponseRow[] => {
  if (updates.length === 0) {
    return existing;
  }
  const byTag = new Map(existing.map((row) => [row.tag, row]));
  for (const row of updates) {
    byTag.set(row.tag, row);
  }
  return Array.from(byTag.values());
};

export default function SystemControlLayer({ onRowsUpdate }: SystemControlLayerProps) {
  const [queryInput, setQueryInput] = useState<string>("SELECT tag, type, subtype, equipment, current_value, state, setpoint, mode FROM uns_rows LIMIT 100");
  const [scriptInput, setScriptInput] = useState<string>("# result variable is optional\nresult = {'note': 'uns script executed'}");
  const [endpointInput, setEndpointInput] = useState<string>("");
  const [rowsView, setRowsView] = useState<EngineeringTableResponseRow[]>([]);
  const [status, setStatus] = useState<string>("UNS idle");
  const [error, setError] = useState<string | null>(null);
  const [busyAction, setBusyAction] = useState<"query" | "script" | "connector" | "refresh" | "map" | null>(null);
  const [wsState, setWsState] = useState<"connected" | "reconnecting" | "disconnected">("disconnected");
  const [lastResponse, setLastResponse] = useState<Record<string, unknown> | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const reconnectAttemptRef = useRef<number>(0);

  const broadcastRows = useCallback(
    (rows: EngineeringTableResponseRow[], mode: "replace" | "merge" = "replace") => {
      setRowsView((prev) => {
        const next = mode === "merge" ? mergeByTag(prev, rows) : rows;
        onRowsUpdate?.(next);
        return next;
      });
    },
    [onRowsUpdate]
  );

  const refreshRows = useCallback(async (): Promise<void> => {
    setError(null);
    setBusyAction("refresh");
    try {
      const rows = await getUNSRows();
      const normalized = rows.map(toEngineeringRow);
      broadcastRows(normalized, "replace");
      setStatus(`Loaded ${normalized.length} UNS rows.`);
      setLastResponse({ rows: normalized.length, mode: "refresh" });
    } catch {
      setError("UNS rows endpoint unavailable.");
    } finally {
      setBusyAction(null);
    }
  }, [broadcastRows]);

  useEffect(() => {
    void refreshRows();
  }, [refreshRows]);

  useEffect(() => {
    let disposed = false;

    const clearTimer = (): void => {
      if (reconnectTimerRef.current !== null) {
        window.clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
    };

    const scheduleReconnect = (): void => {
      if (disposed) {
        return;
      }
      clearTimer();
      reconnectAttemptRef.current += 1;
      setWsState("reconnecting");
      const delay = Math.min(12000, 600 * 2 ** Math.min(reconnectAttemptRef.current, 5));
      reconnectTimerRef.current = window.setTimeout(() => {
        if (!disposed) {
          openSocket();
        }
      }, delay);
    };

    const openSocket = (): void => {
      const socket = createUNSSocket();
      wsRef.current = socket;

      socket.onopen = () => {
        if (wsRef.current !== socket) {
          return;
        }
        reconnectAttemptRef.current = 0;
        setWsState("connected");
      };

      socket.onmessage = (event) => {
        if (wsRef.current !== socket) {
          return;
        }
        try {
          const payload = JSON.parse(event.data) as {
            event?: string;
            rows?: UNSRow[];
            updated_rows?: UNSRow[];
          };

          if (payload.event === "uns_snapshot_full" && Array.isArray(payload.rows)) {
            const nextRows = payload.rows.map(toEngineeringRow);
            broadcastRows(nextRows, "replace");
            setStatus(`UNS stream full snapshot (${nextRows.length} rows).`);
            setLastResponse({ event: payload.event, rows: nextRows.length });
            return;
          }

          if (payload.event === "uns_snapshot_partial" && Array.isArray(payload.updated_rows)) {
            const updateRows = payload.updated_rows.map(toEngineeringRow);
            broadcastRows(updateRows, "merge");
            setStatus(`UNS stream partial update (${updateRows.length} rows).`);
            setLastResponse({ event: payload.event, rows: updateRows.length });
          }
        } catch {
          setError((current) => current ?? "UNS websocket payload malformed.");
        }
      };

      socket.onerror = () => {
        if (wsRef.current !== socket) {
          return;
        }
        setWsState("disconnected");
        setError((current) => current ?? "UNS websocket failed.");
      };

      socket.onclose = () => {
        if (disposed) {
          return;
        }
        if (wsRef.current !== socket) {
          return;
        }
        setWsState("reconnecting");
        scheduleReconnect();
      };
    };

    openSocket();

    return () => {
      disposed = true;
      clearTimer();
      wsRef.current?.close();
      wsRef.current = null;
      setWsState("disconnected");
    };
  }, [broadcastRows]);

  const handleRunQuery = useCallback(async () => {
    const normalizedQuery = queryInput.trim();
    if (!normalizedQuery) {
      setError("Query is required.");
      return;
    }
    setError(null);
    setBusyAction("query");
    try {
      const rows = await queryUNS(normalizedQuery);
      const normalized = rows.map(toEngineeringRow);
      broadcastRows(normalized, "replace");
      setStatus(`Query returned ${normalized.length} rows.`);
      setLastResponse({ rows: normalized.length, mode: "query" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "UNS query failed. Verify SQL is SELECT-only and references uns_rows.");
    } finally {
      setBusyAction(null);
    }
  }, [broadcastRows, queryInput]);

  const handleRunScript = useCallback(async () => {
    const normalizedScript = scriptInput.trim();
    if (!normalizedScript) {
      setError("Script is required.");
      return;
    }
    setError(null);
    setBusyAction("script");
    try {
      const result = await runUNSScript(normalizedScript);
      await refreshRows();
      setStatus("UNS script executed.");
      setLastResponse({ mode: "script", result });
    } catch (err) {
      setError(err instanceof Error ? err.message : "UNS script execution failed. Only restricted internal script operations are allowed.");
    } finally {
      setBusyAction(null);
    }
  }, [refreshRows, scriptInput]);

  const connect = useCallback(
    async (connectorType: "opcua" | "mqtt" | "api") => {
      if (!endpointInput.trim()) {
        setError("Connector endpoint is required.");
        return;
      }
      setError(null);
      setBusyAction("connector");
      try {
        const result = await setUNSConnector(connectorType, { endpoint: endpointInput.trim() });
        setStatus(`${connectorType.toUpperCase()} metadata saved.`);
        setLastResponse({ mode: "connector", connector: connectorType, result });
      } catch (err) {
        setError(err instanceof Error ? err.message : `${connectorType.toUpperCase()} connect metadata update failed.`);
      } finally {
        setBusyAction(null);
      }
    },
    [endpointInput]
  );

  const handleQuickMap = useCallback(async () => {
    if (rowsView.length === 0) {
      setError("No rows available to map.");
      return;
    }
    const firstTag = rowsView[0].tag;
    setError(null);
    setBusyAction("map");
    try {
      const result = await mapUNSTag(firstTag, { mapped_to: firstTag, source: "system_control_layer" });
      setStatus(`Mapped tag ${firstTag}.`);
      setLastResponse({ mode: "map", result });
    } catch (err) {
      setError(err instanceof Error ? err.message : "UNS mapping update failed.");
    } finally {
      setBusyAction(null);
    }
  }, [rowsView]);

  const rowPreview = useMemo(() => rowsView.slice(0, 5), [rowsView]);

  return (
    <section className="mb-2 rounded border border-slate-300 bg-white p-2">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-700">System Control Layer (UNS)</h4>
        <span className="text-[11px] text-slate-500">{status}</span>
        <span className={`rounded border px-1.5 py-0.5 text-[10px] ${wsState === "connected" ? "border-emerald-300 bg-emerald-50 text-emerald-700" : wsState === "reconnecting" ? "border-amber-300 bg-amber-50 text-amber-700" : "border-slate-300 bg-slate-100 text-slate-600"}`}>
          {wsState === "connected" ? "Live Connected" : wsState === "reconnecting" ? "Reconnecting" : "Disconnected"}
        </span>
      </div>

      <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
        <div className="space-y-1">
          <label className="text-[11px] font-medium text-slate-600">Query</label>
          <textarea
            value={queryInput}
            onChange={(event) => setQueryInput(event.target.value)}
            className="h-20 w-full rounded border border-slate-300 bg-slate-50 p-2 text-[11px] text-slate-800"
          />
          <button type="button" className="command-btn" onClick={() => void handleRunQuery()} disabled={busyAction !== null}>
            {busyAction === "query" ? "Running..." : "Run Query"}
          </button>
        </div>

        <div className="space-y-1">
          <label className="text-[11px] font-medium text-slate-600">Script</label>
          <textarea
            value={scriptInput}
            onChange={(event) => setScriptInput(event.target.value)}
            className="h-20 w-full rounded border border-slate-300 bg-slate-50 p-2 text-[11px] text-slate-800"
          />
          <div className="flex gap-2">
            <button type="button" className="command-btn" onClick={() => void handleRunScript()} disabled={busyAction !== null}>
              {busyAction === "script" ? "Running..." : "Run Script"}
            </button>
            <button type="button" className="command-btn" onClick={() => void handleQuickMap()} disabled={busyAction !== null}>
              {busyAction === "map" ? "Mapping..." : "Map First Tag"}
            </button>
          </div>
        </div>
      </div>

      <div className="mt-2 flex flex-wrap items-end gap-2">
        <label className="text-[11px] font-medium text-slate-600">
          Endpoint
          <input
            value={endpointInput}
            onChange={(event) => setEndpointInput(event.target.value)}
            className="ml-2 w-[280px] rounded border border-slate-300 bg-slate-50 px-2 py-1 text-[11px] text-slate-800"
            placeholder="opc.tcp://localhost:4840 or mqtt://broker or https://api"
          />
        </label>
        <button type="button" className="command-btn" onClick={() => void connect("opcua")} disabled={busyAction !== null}>Connect OPC UA</button>
        <button type="button" className="command-btn" onClick={() => void connect("mqtt")} disabled={busyAction !== null}>Connect MQTT</button>
        <button type="button" className="command-btn" onClick={() => void connect("api")} disabled={busyAction !== null}>Connect API</button>
        <button type="button" className="command-btn" onClick={() => void refreshRows()} disabled={busyAction !== null}>{busyAction === "refresh" ? "Refreshing..." : "Refresh UNS"}</button>
      </div>

      {error ? <p className="mt-2 text-xs text-red-700">{error}</p> : null}

      {lastResponse ? (
        <div className="mt-2 rounded border border-slate-200 bg-slate-50 p-2">
          <p className="text-[11px] font-semibold text-slate-700">Latest response</p>
          <pre className="mt-1 max-h-28 overflow-auto text-[10px] text-slate-700">{JSON.stringify(lastResponse, null, 2)}</pre>
        </div>
      ) : null}

      <div className="mt-2 rounded border border-slate-200 bg-slate-50 p-2">
        <p className="text-[11px] text-slate-600">Live view preview ({rowsView.length} rows):</p>
        <div className="mt-1 flex flex-wrap gap-1 text-[11px] text-slate-700">
          {rowPreview.length === 0 ? <span className="text-slate-500">No UNS rows loaded.</span> : null}
          {rowPreview.map((row) => (
            <span key={row.tag} className="rounded border border-slate-300 bg-white px-2 py-0.5">
              {row.tag}={row.current_value ?? "—"}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
