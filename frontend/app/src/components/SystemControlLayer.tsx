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
  const wsRef = useRef<WebSocket | null>(null);

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
    try {
      const rows = await getUNSRows();
      const normalized = rows.map(toEngineeringRow);
      broadcastRows(normalized, "replace");
      setStatus(`Loaded ${normalized.length} UNS rows.`);
    } catch {
      setError("UNS rows endpoint unavailable.");
    }
  }, [broadcastRows]);

  useEffect(() => {
    void refreshRows();
  }, [refreshRows]);

  useEffect(() => {
    const socket = createUNSSocket();
    wsRef.current = socket;

    socket.onmessage = (event) => {
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
          return;
        }

        if (payload.event === "uns_snapshot_partial" && Array.isArray(payload.updated_rows)) {
          const updateRows = payload.updated_rows.map(toEngineeringRow);
          broadcastRows(updateRows, "merge");
          setStatus(`UNS stream partial update (${updateRows.length} rows).`);
        }
      } catch {
        // Ignore malformed payloads to keep stream resilient.
      }
    };

    socket.onerror = () => {
      setError((current) => current ?? "UNS websocket failed.");
    };

    return () => {
      socket.close();
      wsRef.current = null;
    };
  }, [broadcastRows]);

  const handleRunQuery = useCallback(async () => {
    setError(null);
    try {
      const rows = await queryUNS(queryInput);
      const normalized = rows.map(toEngineeringRow);
      broadcastRows(normalized, "replace");
      setStatus(`Query returned ${normalized.length} rows.`);
    } catch {
      setError("UNS query failed. Verify SQL is SELECT-only and references uns_rows.");
    }
  }, [broadcastRows, queryInput]);

  const handleRunScript = useCallback(async () => {
    setError(null);
    try {
      await runUNSScript(scriptInput);
      await refreshRows();
      setStatus("UNS script executed.");
    } catch {
      setError("UNS script execution failed. Only restricted internal script operations are allowed.");
    }
  }, [refreshRows, scriptInput]);

  const connect = useCallback(
    async (connectorType: "opcua" | "mqtt" | "api") => {
      setError(null);
      try {
        await setUNSConnector(connectorType, { endpoint: endpointInput });
        setStatus(`${connectorType.toUpperCase()} metadata saved.`);
      } catch {
        setError(`${connectorType.toUpperCase()} connect metadata update failed.`);
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
    try {
      await mapUNSTag(firstTag, { mapped_to: firstTag, source: "system_control_layer" });
      setStatus(`Mapped tag ${firstTag}.`);
    } catch {
      setError("UNS mapping update failed.");
    }
  }, [rowsView]);

  const rowPreview = useMemo(() => rowsView.slice(0, 5), [rowsView]);

  return (
    <section className="mb-2 rounded border border-slate-300 bg-white p-2">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-700">System Control Layer (UNS)</h4>
        <span className="text-[11px] text-slate-500">{status}</span>
      </div>

      <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
        <div className="space-y-1">
          <label className="text-[11px] font-medium text-slate-600">Query</label>
          <textarea
            value={queryInput}
            onChange={(event) => setQueryInput(event.target.value)}
            className="h-20 w-full rounded border border-slate-300 bg-slate-50 p-2 text-[11px] text-slate-800"
          />
          <button type="button" className="command-btn" onClick={() => void handleRunQuery()}>
            Run Query
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
            <button type="button" className="command-btn" onClick={() => void handleRunScript()}>
              Run Script
            </button>
            <button type="button" className="command-btn" onClick={() => void handleQuickMap()}>
              Map First Tag
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
        <button type="button" className="command-btn" onClick={() => void connect("opcua")}>Connect OPC UA</button>
        <button type="button" className="command-btn" onClick={() => void connect("mqtt")}>Connect MQTT</button>
        <button type="button" className="command-btn" onClick={() => void connect("api")}>Connect API</button>
        <button type="button" className="command-btn" onClick={() => void refreshRows()}>Refresh UNS</button>
      </div>

      {error ? <p className="mt-2 text-xs text-red-700">{error}</p> : null}

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
