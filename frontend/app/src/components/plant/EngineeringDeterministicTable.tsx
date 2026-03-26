import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  type SortingState,
  useReactTable,
} from "@tanstack/react-table";
import { useVirtualizer } from "@tanstack/react-virtual";
import { ChipList } from "./Chip";
import { TypeBadge } from "./Badge";
import {
  createBehaviorSocket,
  exportTagIntelligenceCsv,
  exportTagIntelligenceJson,
  getBehaviorSocketCandidateUrls,
  getDeterministicBehaviorRows,
  type DeterministicBehaviorRow,
  type EngineeringTableResponseRow,
} from "../../services/api";

type EngineeringDeterministicTableProps = {
  projectId?: string;
  reloadKey?: number;
  loading: boolean;
  error: string | null;
  onRowSelect?: (row: EngineeringTableResponseRow) => void;
  onOpenWhyTrace?: (row: EngineeringTableResponseRow) => void;
  onRowsResolved?: (payload: {
    source: "deterministic_behavior";
    totalRows: number;
    filteredRows: number;
    rows: EngineeringTableResponseRow[];
  }) => void;
  onLoadingStateChange?: (loading: boolean) => void;
  externalSelectedTag?: string | null;
  highlightedTags?: string[];
};

type RowsState = {
  byTag: Record<string, DeterministicBehaviorRow>;
  order: string[];
};

const columnHelper = createColumnHelper<DeterministicBehaviorRow>();
const SEARCH_DEBOUNCE_MS = 180;

function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handle = window.setTimeout(() => {
      setDebouncedValue(value);
    }, delayMs);
    return () => {
      window.clearTimeout(handle);
    };
  }, [value, delayMs]);

  return debouncedValue;
}

const toText = (value: unknown): string => {
  if (value === null || value === undefined) {
    return "—";
  }
  const normalized = String(value).trim();
  return normalized.length > 0 ? normalized : "—";
};

const toComparableToken = (value: string): string => value.toUpperCase().replace(/[^A-Z0-9]/g, "");

const normalizeBehaviorRow = (row: Partial<DeterministicBehaviorRow> & { tag: string }): DeterministicBehaviorRow => {
  return {
    id: String(row.id ?? row.tag),
    tag: String(row.tag),
    type: String(row.type ?? "unknown"),
    subtype: row.subtype ?? null,
    description: row.description ?? null,
    system: row.system ?? null,
    equipment: row.equipment ?? null,
    process_role: row.process_role ?? null,
    measures: row.measures ?? [],
    controls: row.controls ?? [],
    controlled_by: row.controlled_by ?? [],
    signal_inputs: row.signal_inputs ?? [],
    signal_outputs: row.signal_outputs ?? [],
    upstream: row.upstream ?? [],
    downstream: row.downstream ?? [],
    flow_path: row.flow_path ?? [],
    current_value: row.current_value ?? null,
    state: row.state ?? null,
    setpoint: row.setpoint ?? null,
    mode: row.mode ?? null,
    unit: row.unit ?? null,
    range_min: row.range_min ?? null,
    range_max: row.range_max ?? null,
    fail_state: row.fail_state ?? null,
    power: row.power ?? null,
    document_source: row.document_source ?? [],
    line_reference: row.line_reference ?? [],
    confidence: row.confidence ?? 0,
    num_connections: row.num_connections ?? 0,
    num_upstream: row.num_upstream ?? (row.upstream?.length ?? 0),
    num_downstream: row.num_downstream ?? (row.downstream?.length ?? 0),
    control_chain: row.control_chain ?? [],
    flow_chain: row.flow_chain ?? [],
    is_orphan: row.is_orphan ?? false,
    is_controlled: row.is_controlled ?? false,
    is_actuated: row.is_actuated ?? false,
    warnings: row.warnings ?? [],
    grounded_fields: row.grounded_fields ?? {},
    derived_fields: row.derived_fields ?? {},
    traceability: row.traceability ?? [],
    behavior_card: row.behavior_card ?? "",
    behavior_summary: row.behavior_summary ?? "",
    cause_chain: row.cause_chain ?? [],
    effect_chain: row.effect_chain ?? [],
    impact_summary: row.impact_summary ?? "",
    behavior_confidence: row.behavior_confidence ?? row.confidence ?? 0,
    state_snapshot_id: row.state_snapshot_id ?? "snapshot-00000000",
    why_trace_available: row.why_trace_available ?? false,
  };
};

const buildSearchIndex = (row: DeterministicBehaviorRow): string => {
  return [
    row.tag,
    row.type,
    row.subtype ?? "",
    row.equipment ?? "",
    row.behavior_card,
    row.behavior_summary,
    row.impact_summary,
    row.current_value ?? "",
    row.state ?? "",
    row.setpoint ?? "",
    row.mode ?? "",
    ...row.controls,
    ...row.upstream,
    ...row.downstream,
    ...row.cause_chain,
    ...row.effect_chain,
  ]
    .join(" ")
    .toLowerCase();
};

const mergePartialRows = (previous: RowsState, incomingRows: DeterministicBehaviorRow[]): RowsState => {
  if (incomingRows.length === 0) {
    return previous;
  }

  const nextByTag = { ...previous.byTag };
  const nextOrder = [...previous.order];
  const knownTags = new Set(nextOrder);

  for (const row of incomingRows) {
    const normalized = normalizeBehaviorRow(row);
    nextByTag[normalized.tag] = normalized;
    if (!knownTags.has(normalized.tag)) {
      nextOrder.push(normalized.tag);
      knownTags.add(normalized.tag);
    }
  }

  return { byTag: nextByTag, order: nextOrder };
};

const setRowsFromList = (rows: DeterministicBehaviorRow[]): RowsState => {
  const byTag: Record<string, DeterministicBehaviorRow> = {};
  const order: string[] = [];

  for (const row of rows) {
    const normalized = normalizeBehaviorRow(row);
    byTag[normalized.tag] = normalized;
    order.push(normalized.tag);
  }

  return { byTag, order };
};

const downloadBlob = (blob: Blob, filename: string): void => {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
};

export default function EngineeringDeterministicTable({
  projectId,
  reloadKey = 0,
  loading,
  error,
  onRowSelect,
  onOpenWhyTrace,
  onRowsResolved,
  onLoadingStateChange,
  externalSelectedTag = null,
  highlightedTags = [],
}: EngineeringDeterministicTableProps) {
  const [searchInput, setSearchInput] = useState<string>("");
  const [sorting, setSorting] = useState<SortingState>([{ id: "tag", desc: false }]);
  const [rowsState, setRowsState] = useState<RowsState>(() => setRowsFromList([]));
  const [selectedTag, setSelectedTag] = useState<string>("");
  const [isBehaviorLoading, setIsBehaviorLoading] = useState<boolean>(false);
  const [behaviorError, setBehaviorError] = useState<string | null>(null);
  const [wsStatus, setWsStatus] = useState<"connecting" | "connected" | "reconnecting" | "disconnected">("connecting");
  const [exporting, setExporting] = useState<"csv" | "json" | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement | null>(null);
  const scrollTopRef = useRef<number>(0);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const reconnectAttemptRef = useRef<number>(0);
  const lastPartialSignatureRef = useRef<string>("");
  const lastFullSnapshotRef = useRef<string>("");
  const search = useDebouncedValue(searchInput, SEARCH_DEBOUNCE_MS);

  const applyChipSearch = useCallback((value: string): void => {
    setSearchInput(value);
  }, []);

  const loadBehaviorRows = useCallback(async (): Promise<void> => {
    setIsBehaviorLoading(true);
    setBehaviorError(null);
    try {
      const response = await getDeterministicBehaviorRows();
      const normalized = response.rows.map((row) => normalizeBehaviorRow(row));
      setRowsState(setRowsFromList(normalized));
    } catch {
      setBehaviorError("Behavior rows endpoint unavailable.");
    } finally {
      setIsBehaviorLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadBehaviorRows();
  }, [loadBehaviorRows, projectId, reloadKey]);

  useEffect(() => {
    let disposed = false;
    const candidateUrls = getBehaviorSocketCandidateUrls();

    const clearReconnectTimer = (): void => {
      if (reconnectTimerRef.current !== null) {
        window.clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
    };

    const scheduleReconnect = (): void => {
      if (disposed) {
        return;
      }
      clearReconnectTimer();
      reconnectAttemptRef.current += 1;
      setWsStatus("reconnecting");
      const delay = Math.min(15000, 800 * 2 ** Math.min(reconnectAttemptRef.current, 5));
      reconnectTimerRef.current = window.setTimeout(() => {
        if (!disposed) {
          openSocket();
        }
      }, delay);
    };

    const openSocket = (): void => {
      setWsStatus("connecting");
      const attempt = reconnectAttemptRef.current;
      const candidateIndex = Math.min(attempt, Math.max(0, candidateUrls.length - 1));
      const socketUrl = candidateUrls[candidateIndex] ?? candidateUrls[0];
      const socket = createBehaviorSocket(socketUrl);
      wsRef.current = socket;

      socket.onopen = () => {
        if (wsRef.current !== socket) {
          return;
        }
        reconnectAttemptRef.current = 0;
        setWsStatus("connected");
        setBehaviorError(null);
      };

      socket.onmessage = (event) => {
        if (wsRef.current !== socket) {
          return;
        }
        try {
          const payload = JSON.parse(event.data) as {
            event?: string;
            rows?: DeterministicBehaviorRow[];
            updated_rows?: DeterministicBehaviorRow[];
            snapshot_id?: string;
            changed_tags?: string[];
          };

          if (payload.event === "behavior_snapshot_full" && Array.isArray(payload.rows)) {
            const snapshotId = String(payload.snapshot_id ?? "");
            if (snapshotId && lastFullSnapshotRef.current === snapshotId) {
              return;
            }
            if (snapshotId) {
              lastFullSnapshotRef.current = snapshotId;
            }
            const normalized = payload.rows.map((row) => normalizeBehaviorRow(row));
            setRowsState(setRowsFromList(normalized));
            return;
          }

          if (payload.event === "behavior_snapshot_partial" && Array.isArray(payload.updated_rows)) {
            const signature = `${payload.snapshot_id ?? ""}|${(payload.changed_tags ?? []).join(",")}|${payload.updated_rows.length}`;
            if (signature === lastPartialSignatureRef.current) {
              return;
            }
            lastPartialSignatureRef.current = signature;
            const normalized = payload.updated_rows.map((row) => normalizeBehaviorRow(row));
            setRowsState((previous) => mergePartialRows(previous, normalized));
          }
        } catch {
          // Ignore malformed payloads to keep stream resilient.
        }
      };

      socket.onerror = () => {
        if (wsRef.current !== socket) {
          return;
        }
        setWsStatus("disconnected");
        setBehaviorError((current) => current ?? `Behavior websocket connection failed (${socketUrl}).`);
      };

      socket.onclose = () => {
        if (disposed) {
          return;
        }
        if (wsRef.current !== socket) {
          return;
        }
        setWsStatus("reconnecting");
        scheduleReconnect();
      };
    };

    openSocket();

    return () => {
      disposed = true;
      clearReconnectTimer();
      const socket = wsRef.current;
      wsRef.current = null;
      if (socket) {
        socket.close();
      }
      setWsStatus("disconnected");
    };
  }, [projectId]);

  useEffect(() => {
    if (!selectedTag) {
      return;
    }
    if (!rowsState.byTag[selectedTag]) {
      setSelectedTag("");
    }
  }, [selectedTag, rowsState]);

  useEffect(() => {
    if (!scrollRef.current) {
      return;
    }
    const nextScrollTop = scrollTopRef.current;
    if (Math.abs(scrollRef.current.scrollTop - nextScrollTop) > 1) {
      scrollRef.current.scrollTop = nextScrollTop;
    }
  }, [rowsState]);

  const onScroll = useCallback((): void => {
    if (!scrollRef.current) {
      return;
    }
    scrollTopRef.current = scrollRef.current.scrollTop;
  }, []);

  const orderedRows = useMemo(() => {
    return rowsState.order.map((tag) => rowsState.byTag[tag]).filter((row): row is DeterministicBehaviorRow => Boolean(row));
  }, [rowsState]);

  const tagByComparableToken = useMemo(() => {
    const map = new Map<string, string>();
    for (const row of orderedRows) {
      map.set(toComparableToken(row.tag), row.tag);
    }
    return map;
  }, [orderedRows]);

  const highlightedTagSet = useMemo(() => {
    return new Set(highlightedTags.map((item) => toComparableToken(item || "")).filter((item) => item.length > 0));
  }, [highlightedTags]);

  useEffect(() => {
    if (!externalSelectedTag) {
      return;
    }
    const resolved = tagByComparableToken.get(toComparableToken(externalSelectedTag));
    if (!resolved) {
      return;
    }
    setSelectedTag((current) => (current === resolved ? current : resolved));
  }, [externalSelectedTag, tagByComparableToken]);

  const rowSearchIndex = useMemo(() => {
    const index = new Map<string, string>();
    for (const row of orderedRows) {
      index.set(row.tag, buildSearchIndex(row));
    }
    return index;
  }, [orderedRows]);

  const filteredRows = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    if (!normalizedSearch) {
      return orderedRows;
    }
    return orderedRows.filter((row) => (rowSearchIndex.get(row.tag) ?? "").includes(normalizedSearch));
  }, [orderedRows, rowSearchIndex, search]);

  const selectedRow = useMemo(() => (selectedTag ? rowsState.byTag[selectedTag] ?? null : null), [rowsState.byTag, selectedTag]);

  useEffect(() => {
    if (selectedRow) {
      onRowSelect?.(selectedRow);
    }
  }, [selectedRow, onRowSelect]);

  const handleExportCsv = useCallback(async () => {
    setExporting("csv");
    setExportError(null);
    try {
      const blob = await exportTagIntelligenceCsv({
        projectId,
        category: "all",
        search: searchInput,
      });
      if (blob.size === 0) {
        throw new Error("CSV export returned empty content.");
      }
      downloadBlob(blob, "tag-intelligence-all.csv");
    } catch (err) {
      setExportError(err instanceof Error ? err.message : "CSV export failed.");
    } finally {
      setExporting(null);
    }
  }, [projectId, searchInput]);

  const handleExportJson = useCallback(async () => {
    setExporting("json");
    setExportError(null);
    try {
      const blob = await exportTagIntelligenceJson({
        projectId,
        category: "all",
        search: searchInput,
      });
      if (blob.size === 0) {
        throw new Error("JSON export returned empty content.");
      }
      downloadBlob(blob, "tag-intelligence-all.json");
    } catch (err) {
      setExportError(err instanceof Error ? err.message : "JSON export failed.");
    } finally {
      setExporting(null);
    }
  }, [projectId, searchInput]);

  const columns = useMemo(
    () => [
      columnHelper.accessor("tag", {
        header: "Tag",
        cell: (info) => {
          const row = info.row.original;
          return (
            <button
              type="button"
              className="max-w-[140px] truncate text-left font-semibold text-slate-800 hover:text-red-600"
              title={row.tag}
              onClick={(event) => {
                event.stopPropagation();
                setSelectedTag(row.tag);
                onRowSelect?.(row);
              }}
            >
              {row.tag}
            </button>
          );
        },
      }),
      columnHelper.accessor("type", {
        header: "Type",
        cell: (info) => <TypeBadge type={toText(info.getValue())} />,
      }),
      columnHelper.accessor("subtype", {
        header: "Subtype",
        cell: (info) => <span className="block max-w-[130px] truncate">{toText(info.getValue())}</span>,
      }),
      columnHelper.accessor("equipment", {
        header: "Equipment",
        cell: (info) => <span className="block max-w-[140px] truncate">{toText(info.getValue())}</span>,
      }),
      columnHelper.accessor("behavior_card", {
        header: "Behavior",
        cell: (info) => <span className="block max-w-[340px] truncate text-slate-700">{toText(info.getValue())}</span>,
      }),
      columnHelper.accessor("current_value", {
        header: "Current",
        cell: (info) => <span className="text-slate-800">{toText(info.getValue())}</span>,
      }),
      columnHelper.accessor("state", {
        header: "State",
        cell: (info) => <span className="text-slate-700">{toText(info.getValue())}</span>,
      }),
      columnHelper.accessor("setpoint", {
        header: "Setpoint",
        cell: (info) => <span className="text-slate-700">{toText(info.getValue())}</span>,
      }),
      columnHelper.accessor("mode", {
        header: "Mode",
        cell: (info) => <span className="text-slate-700">{toText(info.getValue())}</span>,
      }),
      columnHelper.accessor("controls", {
        header: "Controls",
        cell: (info) => <ChipList values={info.getValue()} tone="relation" limit={3} onChipClick={applyChipSearch} />,
        sortingFn: (left, right) => left.original.controls.length - right.original.controls.length,
      }),
      columnHelper.accessor("upstream", {
        header: "Upstream",
        cell: (info) => <ChipList values={info.getValue()} tone="relation" limit={3} onChipClick={applyChipSearch} />,
        sortingFn: (left, right) => left.original.upstream.length - right.original.upstream.length,
      }),
      columnHelper.accessor("downstream", {
        header: "Downstream",
        cell: (info) => <ChipList values={info.getValue()} tone="relation" limit={3} onChipClick={applyChipSearch} />,
        sortingFn: (left, right) => left.original.downstream.length - right.original.downstream.length,
      }),
      columnHelper.display({
        id: "why",
        header: "Why",
        enableSorting: false,
        cell: (info) => {
          const row = info.row.original;
          return (
            <button
              type="button"
              className="rounded border border-red-300 bg-red-50 px-2 py-1 text-[11px] font-medium text-red-700 hover:bg-red-100"
              onClick={(event) => {
                event.stopPropagation();
                onOpenWhyTrace?.(row);
              }}
            >
              Why
            </button>
          );
        },
      }),
    ],
    [applyChipSearch, onOpenWhyTrace, onRowSelect]
  );

  const table = useReactTable({
    data: filteredRows,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const tableRows = table.getRowModel().rows;

  const rowVirtualizer = useVirtualizer({
    count: tableRows.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => 34,
    overscan: 12,
  });

  const activeError = error ?? behaviorError;
  const isLoading = loading || isBehaviorLoading;

  useEffect(() => {
    onLoadingStateChange?.(isLoading);
  }, [isLoading, onLoadingStateChange]);

  useEffect(() => {
    onRowsResolved?.({
      source: "deterministic_behavior",
      totalRows: orderedRows.length,
      filteredRows: filteredRows.length,
      rows: orderedRows,
    });
  }, [filteredRows.length, onRowsResolved, orderedRows]);

  if (isLoading && orderedRows.length === 0) {
    return <div className="flex h-full items-center justify-center bg-white text-sm text-slate-600">Loading deterministic behavior rows…</div>;
  }

  if (activeError && orderedRows.length === 0) {
    return <div className="flex h-full items-center justify-center bg-white text-sm text-red-700">{activeError}</div>;
  }

  if (orderedRows.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-1 bg-white text-sm text-slate-600">
        <p>No deterministic behavior rows available.</p>
        <p className="text-xs text-slate-500">Parse a project to populate behavior rows.</p>
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 w-full gap-3 overflow-hidden rounded border border-slate-300 bg-slate-50 p-2">
      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden rounded border border-slate-300 bg-white">
        <div className="grid grid-cols-1 items-center gap-2 border-b border-slate-200 p-2 md:grid-cols-[1fr_auto_auto]">
          <input
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Search behavior, equipment, controls, upstream, downstream..."
            className="w-full rounded border border-slate-300 bg-white px-2 py-1.5 text-xs text-slate-800 outline-none ring-slate-400 focus:ring"
          />
          <div className="text-xs text-slate-600">
            {filteredRows.length} / {orderedRows.length} rows
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-600">
            <span
              className={`rounded border px-1.5 py-0.5 ${
                wsStatus === "connected"
                  ? "border-emerald-300 bg-emerald-50 text-emerald-700"
                  : wsStatus === "reconnecting"
                    ? "border-amber-300 bg-amber-50 text-amber-700"
                    : "border-slate-300 bg-slate-100 text-slate-600"
              }`}
            >
              {wsStatus === "connected" ? "Live Connected" : wsStatus === "reconnecting" ? "Reconnecting" : "Disconnected"}
            </span>
            <button type="button" className="command-btn" onClick={() => void handleExportCsv()} disabled={exporting !== null}>
              {exporting === "csv" ? "Exporting CSV..." : "Export CSV"}
            </button>
            <button type="button" className="command-btn" onClick={() => void handleExportJson()} disabled={exporting !== null}>
              {exporting === "json" ? "Exporting JSON..." : "Export JSON"}
            </button>
          </div>
          {(isLoading || activeError) && orderedRows.length > 0 ? (
            <div className="text-xs text-slate-600">{isLoading ? "Refreshing…" : activeError}</div>
          ) : null}
          {exportError ? <div className="text-xs text-red-700">{exportError}</div> : null}
        </div>

        <div ref={scrollRef} onScroll={onScroll} className="min-h-0 flex-1 overflow-auto">
          <table className="min-w-[1850px] w-full table-fixed border-collapse text-left text-[11px] text-slate-700">
            <thead className="sticky top-0 z-10 bg-slate-100 text-[10px] uppercase tracking-wide text-slate-600">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => {
                    const sortable = header.column.getCanSort();
                    const sorted = header.column.getIsSorted();
                    return (
                      <th key={header.id} className="border-b border-slate-300 px-2 py-2">
                        {header.isPlaceholder ? null : (
                          <button
                            type="button"
                            className={`flex items-center gap-1 ${sortable ? "cursor-pointer" : "cursor-default"}`}
                            onClick={sortable ? header.column.getToggleSortingHandler() : undefined}
                          >
                            {flexRender(header.column.columnDef.header, header.getContext())}
                            {sortable ? <span>{sorted === "desc" ? "↓" : sorted === "asc" ? "↑" : "↕"}</span> : null}
                          </button>
                        )}
                      </th>
                    );
                  })}
                </tr>
              ))}
            </thead>
            <tbody style={{ height: `${rowVirtualizer.getTotalSize()}px`, position: "relative" }}>
              {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                const row = tableRows[virtualRow.index];
                if (!row) {
                  return null;
                }
                const selected = selectedTag === row.original.tag;
                const loopHighlighted = highlightedTagSet.has(toComparableToken(row.original.tag));
                return (
                  <tr
                    key={row.original.tag}
                    className={`absolute left-0 top-0 cursor-pointer border-b border-slate-200 hover:bg-slate-50 ${selected ? "bg-red-50" : loopHighlighted ? "bg-amber-50" : ""}`}
                    style={{ transform: `translateY(${virtualRow.start}px)`, width: "100%", display: "table", tableLayout: "fixed" }}
                    onClick={() => {
                      setSelectedTag(row.original.tag);
                      onRowSelect?.(row.original);
                    }}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="truncate px-2 py-1.5 align-top text-[11px]">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="border-t border-slate-200 bg-white p-2">
          {selectedRow ? (
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              <section className="rounded border border-slate-200 bg-slate-50 p-2">
                <h4 className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-600">Cause Chain</h4>
                <ChipList values={selectedRow.cause_chain} tone="relation" limit={8} onChipClick={applyChipSearch} emptyLabel="No upstream causes" />
              </section>
              <section className="rounded border border-slate-200 bg-slate-50 p-2">
                <h4 className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-600">Effect Chain</h4>
                <ChipList values={selectedRow.effect_chain} tone="relation" limit={8} onChipClick={applyChipSearch} emptyLabel="No downstream effects" />
              </section>
              <section className="rounded border border-slate-200 bg-slate-50 p-2 md:col-span-2">
                <h4 className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-600">Impact</h4>
                <p className="text-xs text-slate-700">{toText(selectedRow.impact_summary)}</p>
              </section>
              <section className="rounded border border-slate-200 bg-slate-50 p-2 md:col-span-2">
                <h4 className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-600">Live State</h4>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-slate-700 md:grid-cols-5">
                  <p>Tag: {selectedRow.tag}</p>
                  <p>Current: {toText(selectedRow.current_value)}</p>
                  <p>State: {toText(selectedRow.state)}</p>
                  <p>Setpoint: {toText(selectedRow.setpoint)}</p>
                  <p>Mode: {toText(selectedRow.mode)}</p>
                </div>
              </section>
            </div>
          ) : (
            <p className="text-xs text-slate-500">Select a row tag to inspect deterministic cause/effect and live behavior details.</p>
          )}
        </div>
      </div>

    </div>
  );
}
