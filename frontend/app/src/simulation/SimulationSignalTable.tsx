import { useEffect, useMemo, useState } from "react";

import { createUNSSocket, getUNSHistory, getUNSRows, type UNSHistoryRow, type UNSRow } from "../services/api";
import type { SimulationStreamRequest } from "./useSimulationWorkspaceState";

type SignalRow = {
  id: string;
  value: unknown;
  state?: string | null;
  mode?: string | null;
  equipment?: string | null;
  timestamp?: string | null;
};

const toSignalRow = (row: UNSRow): SignalRow => ({
  id: row.tag,
  value: row.current_value ?? "",
  state: row.state ?? null,
  mode: row.mode ?? null,
  equipment: row.equipment ?? null,
});

const toHistoryRow = (row: UNSHistoryRow): SignalRow => ({
  id: row.tag,
  value: row.value ?? "",
  state: "historical",
  mode: "replay",
  equipment: row.source ?? null,
  timestamp: row.timestamp,
});

type SimulationSignalTableProps = {
  request: SimulationStreamRequest;
  sourceName?: string | null;
  emptyMessage?: string;
};

export default function SimulationSignalTable({ request, sourceName = null, emptyMessage }: SimulationSignalTableProps) {
  const [signals, setSignals] = useState<Record<string, SignalRow>>({});
  const selectedTagsKey = request.selectedTags.join("|");
  const allowedTags = useMemo(() => new Set(request.selectedTags), [selectedTagsKey]);

  useEffect(() => {
    if (request.mode !== "live") {
      return;
    }

    if (!request.dataSourceId || request.selectedTags.length === 0) {
      setSignals({});
      return;
    }

    void getUNSRows()
      .then((rows) => {
        const initial = rows.reduce<Record<string, SignalRow>>((acc, row) => {
          if (allowedTags.has(row.tag)) {
            acc[row.tag] = toSignalRow(row);
          }
          return acc;
        }, {});
        setSignals(initial);
      })
      .catch(() => null);

    const socket = createUNSSocket();
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data) as {
        event?: string;
        rows?: UNSRow[];
        updated_rows?: UNSRow[];
      };

      if (payload.event === "uns_snapshot_full" && Array.isArray(payload.rows)) {
        setSignals(
          payload.rows.reduce<Record<string, SignalRow>>((acc, row) => {
            if (allowedTags.has(row.tag)) {
              acc[row.tag] = toSignalRow(row);
            }
            return acc;
          }, {})
        );
        return;
      }

      if (payload.event === "uns_snapshot_partial" && Array.isArray(payload.updated_rows)) {
        setSignals((previous) => {
          const next = { ...previous };
          payload.updated_rows?.forEach((row) => {
            if (allowedTags.has(row.tag)) {
              next[row.tag] = toSignalRow(row);
              return;
            }
            delete next[row.tag];
          });
          return next;
        });
      }
    };

    return () => socket.close();
  }, [allowedTags, request.dataSourceId, request.mode, selectedTagsKey, request.selectedTags.length]);

  useEffect(() => {
    if (request.mode !== "historical") {
      return;
    }

    const tags = request.selectedTags;
    if (tags.length === 0) {
      setSignals({});
      return;
    }

    void getUNSHistory(tags, 12)
      .then((rows) => {
        const nextSignals = rows.reduce<Record<string, SignalRow>>((acc, row, index) => {
          acc[`${row.tag}-${row.timestamp}-${index}`] = toHistoryRow(row);
          return acc;
        }, {});
        setSignals(nextSignals);
      })
      .catch(() => {
        setSignals({});
      });
  }, [request.mode, selectedTagsKey, request.selectedTags]);

  const rows = useMemo(
    () =>
      Object.values(signals)
        .filter((row) => request.mode === "historical" || allowedTags.has(row.id))
        .sort((left, right) => String(left.id).localeCompare(String(right.id))),
    [allowedTags, request.mode, signals]
  );

  return (
    <section className="workspace-documents-list-panel">
      <div className="workspace-documents-list-header">
        <h3>{request.mode === "historical" ? "Historical Simulation Replay" : "Live Simulation Signals"}</h3>
        <p>
          {request.mode === "historical"
            ? sourceName
              ? `Historical replay for ${sourceName} from the centralized unified tag/state store.`
              : "Historical replay from the centralized unified store."
            : sourceName
              ? `Real-time plant stream scoped to ${sourceName} through the centralized unified tag/state store.`
              : "Real-time plant stream from the centralized unified tag/state store."}
        </p>
      </div>
      {rows.length === 0 ? (
        <div className="workspace-documents-empty">{emptyMessage ?? "No live simulation signals available."}</div>
      ) : (
        <table className="io-mapping-table">
          <thead>
            <tr>
              <th>Tag</th>
              {request.mode === "historical" ? <th>Timestamp</th> : null}
              <th>Value</th>
              <th>State</th>
              <th>Mode</th>
              <th>Equipment</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id}>
                <td>{row.id}</td>
                {request.mode === "historical" ? <td>{row.timestamp ? new Date(row.timestamp).toLocaleString() : "-"}</td> : null}
                <td>{String(row.value ?? "")}</td>
                <td>{row.state ?? "-"}</td>
                <td>{row.mode ?? "-"}</td>
                <td>{row.equipment ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
