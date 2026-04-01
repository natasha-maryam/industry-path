import { ChevronDown, ChevronRight, Sparkles } from "lucide-react";
import { useCallback, useDeferredValue, useEffect, useMemo, useRef, useState } from "react";
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
  seedRows?: EngineeringTableResponseRow[];
  loading: boolean;
  error: string | null;
  sandboxMode?: boolean;
  onRowSelect?: (row: EngineeringTableResponseRow) => void;
  onOpenWhyTrace?: (row: EngineeringTableResponseRow) => void;
  onRowsResolved?: (payload: {
    source: "deterministic_behavior";
    totalRows: number;
    filteredRows: number;
    rows: EngineeringTableResponseRow[];
  }) => void;
  onLoadingStateChange?: (loading: boolean) => void;
  onOpenPlantGenie?: (seedTag?: string | null) => void;
  externalSelectedTag?: string | null;
  highlightedTags?: string[];
};

type RowsState = {
  byTag: Record<string, DeterministicBehaviorRow>;
  order: string[];
  searchIndexByTag: Record<string, string>;
};

const columnHelper = createColumnHelper<DeterministicBehaviorRow>();
const SEARCH_DEBOUNCE_MS = 180;
const TABLE_ROW_HEIGHT = 48;

const tableColumnWidthClass = (columnId: string): string => {
  switch (columnId) {
    case "tag":
      return "w-[30%]";
    case "process_role":
      return "w-[15%]";
    case "flow_preview":
      return "w-[40%]";
    case "why":
      return "w-[15%]";
    default:
      return "";
  }
};

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
    upstream_links: row.upstream_links ?? [],
    downstream_links: row.downstream_links ?? [],
    has_inferred_upstream: row.has_inferred_upstream ?? false,
    has_inferred_downstream: row.has_inferred_downstream ?? false,
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

const hasMeaningfulRowChange = (previousRow: DeterministicBehaviorRow | undefined, nextRow: DeterministicBehaviorRow): boolean => {
  if (!previousRow) {
    return true;
  }

  return (
    previousRow.state_snapshot_id !== nextRow.state_snapshot_id ||
    previousRow.behavior_card !== nextRow.behavior_card ||
    previousRow.behavior_summary !== nextRow.behavior_summary ||
    previousRow.impact_summary !== nextRow.impact_summary ||
    previousRow.current_value !== nextRow.current_value ||
    previousRow.state !== nextRow.state ||
    previousRow.setpoint !== nextRow.setpoint ||
    previousRow.mode !== nextRow.mode ||
    previousRow.behavior_confidence !== nextRow.behavior_confidence ||
    previousRow.controls.length !== nextRow.controls.length ||
    previousRow.upstream.length !== nextRow.upstream.length ||
    previousRow.downstream.length !== nextRow.downstream.length ||
    previousRow.cause_chain.length !== nextRow.cause_chain.length ||
    previousRow.effect_chain.length !== nextRow.effect_chain.length
  );
};

const mergePartialRows = (previous: RowsState, incomingRows: DeterministicBehaviorRow[]): RowsState => {
  if (incomingRows.length === 0) {
    return previous;
  }

  const nextByTag = { ...previous.byTag };
  const nextOrder = [...previous.order];
  const nextSearchIndexByTag = { ...previous.searchIndexByTag };
  const knownTags = new Set(nextOrder);
  let changed = false;

  for (const row of incomingRows) {
    const normalized = normalizeBehaviorRow(row);
    const previousRow = nextByTag[normalized.tag];
    if (hasMeaningfulRowChange(previousRow, normalized)) {
      nextByTag[normalized.tag] = normalized;
      nextSearchIndexByTag[normalized.tag] = buildSearchIndex(normalized);
      changed = true;
    }
    if (!knownTags.has(normalized.tag)) {
      nextOrder.push(normalized.tag);
      knownTags.add(normalized.tag);
      changed = true;
    }
  }

  if (!changed) {
    return previous;
  }

  return { byTag: nextByTag, order: nextOrder, searchIndexByTag: nextSearchIndexByTag };
};

const setRowsFromList = (rows: DeterministicBehaviorRow[]): RowsState => {
  const byTag: Record<string, DeterministicBehaviorRow> = {};
  const order: string[] = [];
  const searchIndexByTag: Record<string, string> = {};
  const seen = new Set<string>();

  for (const row of rows) {
    const normalized = normalizeBehaviorRow(row);
    byTag[normalized.tag] = normalized;
    searchIndexByTag[normalized.tag] = buildSearchIndex(normalized);
    if (!seen.has(normalized.tag)) {
      order.push(normalized.tag);
      seen.add(normalized.tag);
    }
  }

  return { byTag, order, searchIndexByTag };
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
  seedRows = [],
  loading,
  error,
  sandboxMode = false,
  onRowSelect,
  onOpenWhyTrace,
  onRowsResolved,
  onLoadingStateChange,
  onOpenPlantGenie,
  externalSelectedTag = null,
  highlightedTags = [],
}: EngineeringDeterministicTableProps) {
  const [searchInput, setSearchInput] = useState<string>("");
  const [sorting, setSorting] = useState<SortingState>([{ id: "tag", desc: false }]);
  const [rowsState, setRowsState] = useState<RowsState>(() => setRowsFromList(seedRows.map((row) => normalizeBehaviorRow(row))));
  const [selectedTag, setSelectedTag] = useState<string>("");
  const [viewMode, setViewMode] = useState<"system" | "table">("system");
  const [expandedEquipmentGroups, setExpandedEquipmentGroups] = useState<Record<string, boolean>>({});
  const [hoveredTag, setHoveredTag] = useState<string | null>(null);
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
  const deferredSearch = useDeferredValue(search);
  const plantGenieSeedTag = selectedTag || externalSelectedTag || "";

  const applyChipSearch = useCallback((value: string): void => {
    setSearchInput(value);
  }, []);

  const toggleEquipmentGroup = useCallback((equipment: string): void => {
    setExpandedEquipmentGroups((current) => ({ ...current, [equipment]: !current[equipment] }));
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
    if (sandboxMode) {
      return;
    }
    void loadBehaviorRows();
  }, [loadBehaviorRows, projectId, reloadKey]);

  useEffect(() => {
    if (seedRows.length === 0) {
      return;
    }
    setRowsState((previous) => mergePartialRows(previous, seedRows.map((row) => normalizeBehaviorRow(row))));
  }, [seedRows]);

  useEffect(() => {
    if (sandboxMode) {
      return;
    }
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

  const filteredRows = useMemo(() => {
    const normalizedSearch = deferredSearch.trim().toLowerCase();
    if (!normalizedSearch) {
      return orderedRows;
    }
    return orderedRows.filter((row) => (rowsState.searchIndexByTag[row.tag] ?? "").includes(normalizedSearch));
  }, [deferredSearch, orderedRows, rowsState.searchIndexByTag]);

  const deferredFilteredRows = useDeferredValue(filteredRows);

  const selectedRow = useMemo(() => (selectedTag ? rowsState.byTag[selectedTag] ?? null : null), [rowsState.byTag, selectedTag]);
  const previewRow = useMemo(() => {
    if (hoveredTag) {
      return rowsState.byTag[hoveredTag] ?? selectedRow;
    }
    return selectedRow;
  }, [hoveredTag, rowsState.byTag, selectedRow]);

  const equipmentGroups = useMemo(() => {
    const groups = new Map<string, DeterministicBehaviorRow[]>();
    for (const row of deferredFilteredRows) {
      const equipmentKey = row.equipment?.trim() || "unassigned_equipment";
      const existing = groups.get(equipmentKey) ?? [];
      existing.push(row);
      groups.set(equipmentKey, existing);
    }
    return Array.from(groups.entries()).sort((left, right) => left[0].localeCompare(right[0]));
  }, [deferredFilteredRows]);

  useEffect(() => {
    setExpandedEquipmentGroups((current) => {
      const next = { ...current };
      let changed = false;
      for (const [equipment] of equipmentGroups) {
        if (!(equipment in next)) {
          next[equipment] = equipmentGroups.length <= 3;
          changed = true;
        }
      }
      return changed ? next : current;
    });
  }, [equipmentGroups]);

  const primaryFlowPath = useMemo(() => {
    const candidate = deferredFilteredRows
      .map((row) => row.flow_chain.filter((item) => Boolean(item)))
      .sort((left, right) => right.length - left.length)[0] ?? [];
    const deduped: string[] = [];
    for (const item of candidate) {
      if (item && deduped[deduped.length - 1] !== item) {
        deduped.push(item);
      }
    }
    return deduped;
  }, [deferredFilteredRows]);

  const roleToneClass = useCallback((role: string | null | undefined): string => {
    switch ((role || "").toLowerCase()) {
      case "sensor":
        return "border-sky-200 bg-sky-50 text-sky-900";
      case "controller":
        return "border-amber-200 bg-amber-50 text-amber-900";
      case "actuator":
        return "border-emerald-200 bg-emerald-50 text-emerald-900";
      case "process":
        return "border-violet-200 bg-violet-50 text-violet-900";
      default:
        return "border-slate-200 bg-slate-50 text-slate-800";
    }
  }, []);

  const buildFlowPreview = useCallback((row: DeterministicBehaviorRow): string => {
    const preview = [...row.upstream.slice(0, 1), row.tag, ...row.downstream.slice(0, 1)].filter(Boolean);
    return preview.length > 0 ? preview.join(" -> ") : row.flow_chain.join(" -> ");
  }, []);

  useEffect(() => {
    if (selectedRow) {
      onRowSelect?.(selectedRow);
    }
  }, [selectedRow, onRowSelect]);

  const handleExportCsv = useCallback(async () => {
    if (sandboxMode) {
      setExportError("Export is disabled in sandbox mode.");
      setExporting(null);
      return;
    }
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
    if (sandboxMode) {
      setExportError("Export is disabled in sandbox mode.");
      setExporting(null);
      return;
    }
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
        header: "Component",
        cell: (info) => {
          const row = info.row.original;
          return (
            <div className="flex items-center gap-2 min-w-0 whitespace-nowrap overflow-hidden text-ellipsis">
              <button
                type="button"
                className="block max-w-full whitespace-nowrap overflow-hidden text-ellipsis text-left font-semibold text-slate-800 hover:text-red-600"
                title={row.tag}
                onClick={(event) => {
                  event.stopPropagation();
                  setSelectedTag(row.tag);
                  onRowSelect?.(row);
                }}
              >
                {row.tag}
              </button>
              <span className="block max-w-full whitespace-nowrap overflow-hidden text-ellipsis text-[9px] text-slate-500">{toText(row.equipment)}</span>
            </div>
          );
        },
      }),
      columnHelper.accessor("process_role", {
        header: "Role",
        cell: (info) => (
          <div className="flex items-center gap-2 overflow-hidden whitespace-nowrap">
            <span className={`inline-flex max-w-full overflow-hidden text-ellipsis whitespace-nowrap rounded-full border px-2 py-0.5 text-[8px] font-semibold uppercase ${roleToneClass(info.getValue())}`}>
              {toText(info.getValue())}
            </span>
          </div>
        ),
      }),
      columnHelper.display({
        id: "flow_preview",
        header: "Flow Preview",
        cell: (info) => {
          const row = info.row.original;
          return (
            <div className="flex items-center gap-2 max-w-[300px] overflow-hidden whitespace-nowrap text-ellipsis">
              <div className="max-w-[300px] truncate whitespace-nowrap text-[10px] text-slate-700" title={buildFlowPreview(row)}>
                {buildFlowPreview(row)}
              </div>
            </div>
          );
        },
        sortingFn: (left, right) => buildFlowPreview(left.original).localeCompare(buildFlowPreview(right.original)),
      }),
      columnHelper.display({
        id: "why",
        header: "Why",
        enableSorting: false,
        cell: (info) => {
          const row = info.row.original;
          return (
            <div className="flex items-center gap-2 overflow-hidden whitespace-nowrap">
              <button
                type="button"
                className="rounded border border-red-300 bg-red-50 px-1.5 py-0.5 text-[8px] font-medium text-red-700 hover:bg-red-100"
                onClick={(event) => {
                  event.stopPropagation();
                  onOpenWhyTrace?.(row);
                }}
              >
                Why
              </button>
            </div>
          );
        },
      }),
    ],
    [applyChipSearch, onOpenWhyTrace, onRowSelect]
  );

  const table = useReactTable({
    data: deferredFilteredRows,
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
    getItemKey: (index) => tableRows[index]?.id ?? index,
    estimateSize: () => TABLE_ROW_HEIGHT,
    overscan: 12,
  });

  const activeError = error ?? behaviorError;
  const isLoading = loading || isBehaviorLoading;

  useEffect(() => {
    onLoadingStateChange?.(isLoading);
  }, [isLoading, onLoadingStateChange]);

  useEffect(() => {
    if (!onRowsResolved) {
      return;
    }

    const handle = window.setTimeout(() => {
      onRowsResolved({
        source: "deterministic_behavior",
        totalRows: orderedRows.length,
        filteredRows: filteredRows.length,
        rows: orderedRows,
      });
    }, 90);

    return () => {
      window.clearTimeout(handle);
    };
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
        <div className="deterministic-toolbar grid grid-cols-1 items-center gap-2 border-b border-slate-200 p-2 md:grid-cols-[1fr_auto_auto]">
          <input
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Search behavior, equipment, controls, upstream, downstream..."
            className="w-full rounded border border-slate-300 bg-white px-2 py-1 text-[10px] text-slate-800 outline-none ring-slate-400 focus:ring"
          />
          <div className="text-[10px] text-slate-600">
            {filteredRows.length} / {orderedRows.length} rows
          </div>
          <div className="deterministic-toolbar-actions flex items-center gap-2 text-[10px] text-slate-600">
            <span
              className={`rounded border px-1.5 py-0.5 text-[9px] ${
                wsStatus === "connected"
                  ? "border-emerald-300 bg-emerald-50 text-emerald-700"
                  : wsStatus === "reconnecting"
                    ? "border-amber-300 bg-amber-50 text-amber-700"
                    : "border-slate-300 bg-slate-100 text-slate-600"
              }`}
            >
              {wsStatus === "connected" ? "Live Connected" : wsStatus === "reconnecting" ? "Reconnecting" : "Disconnected"}
            </span>
            <button
              type="button"
              className="command-btn deterministic-toolbar-btn plant-genie-quick-access"
              onClick={() => onOpenPlantGenie?.(plantGenieSeedTag || null)}
            >
              <Sparkles size={10} />
              <span>Plant Genie</span>
              <span className="plant-genie-inline-badge">NEW</span>
            </button>
            <button
              type="button"
              className="command-btn deterministic-toolbar-btn"
              onClick={() => void handleExportCsv()}
              disabled={sandboxMode || exporting !== null}
            >
              {exporting === "csv" ? "Exporting CSV..." : "Export CSV"}
            </button>
            <button
              type="button"
              className="command-btn deterministic-toolbar-btn"
              onClick={() => void handleExportJson()}
              disabled={sandboxMode || exporting !== null}
            >
              {exporting === "json" ? "Exporting JSON..." : "Export JSON"}
            </button>
          </div>
          {(isLoading || activeError) && orderedRows.length > 0 ? (
            <div className="text-[10px] text-slate-600">{isLoading ? "Refreshing…" : activeError}</div>
          ) : null}
          {exportError ? <div className="text-[10px] text-red-700">{exportError}</div> : null}
        </div>

        <div className="grid gap-2 border-b border-slate-200 bg-slate-50 p-2 lg:grid-cols-[minmax(0,1.4fr)_minmax(260px,0.8fr)]">
          <section className="rounded border border-slate-200 bg-white p-2">
            <div className="mb-1 flex items-center justify-between gap-2">
              <div>
                <p className="text-[9px] font-semibold uppercase tracking-[0.18em] text-slate-500">Flow View</p>
                <p className="text-[10px] text-slate-600">Primary system flow inferred from the validated rows.</p>
              </div>
              <div className="inline-flex rounded border border-slate-200 bg-slate-100 p-0.5">
                <button
                  type="button"
                  className={`rounded px-2 py-1 text-[10px] font-medium ${viewMode === "system" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"}`}
                  onClick={() => setViewMode("system")}
                >
                  System View
                </button>
                <button
                  type="button"
                  className={`rounded px-2 py-1 text-[10px] font-medium ${viewMode === "table" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"}`}
                  onClick={() => setViewMode("table")}
                >
                  Table View
                </button>
              </div>
            </div>
            {primaryFlowPath.length > 0 ? (
              <div className="flex flex-wrap items-center gap-1.5">
                {primaryFlowPath.map((item, index) => (
                  <div key={`${item}-${index}`} className="flex items-center gap-1.5">
                    <button
                      type="button"
                      className="rounded-full border border-slate-200 bg-slate-50 px-2 py-1 text-[10px] font-medium text-slate-700 hover:border-red-200 hover:text-red-700"
                      onMouseEnter={() => setHoveredTag(tagByComparableToken.get(toComparableToken(item)) ?? null)}
                      onMouseLeave={() => setHoveredTag(null)}
                      onClick={() => {
                        const resolved = tagByComparableToken.get(toComparableToken(item));
                        if (resolved) {
                          setSelectedTag(resolved);
                        }
                      }}
                    >
                      {item}
                    </button>
                    {index < primaryFlowPath.length - 1 ? <span className="text-slate-400">→</span> : null}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-[10px] text-slate-500">No validated flow path is available yet.</p>
            )}
          </section>

          <section className="rounded border border-slate-200 bg-white p-2">
            <p className="text-[9px] font-semibold uppercase tracking-[0.18em] text-slate-500">Signal Hover Preview</p>
            {previewRow ? (
              <div className="mt-1 space-y-2">
                <div>
                  <p className="text-[11px] font-semibold text-slate-800">{previewRow.tag}</p>
                  <p className="text-[10px] text-slate-500">{toText(previewRow.equipment)} · {toText(previewRow.process_role)}</p>
                </div>
                <div>
                  <p className="mb-1 text-[9px] font-semibold uppercase tracking-wide text-slate-500">Upstream</p>
                  <ChipList values={previewRow.upstream} tone="relation" limit={6} onChipClick={applyChipSearch} emptyLabel="No upstream context" compact />
                </div>
                <div>
                  <p className="mb-1 text-[9px] font-semibold uppercase tracking-wide text-slate-500">Downstream</p>
                  <ChipList values={previewRow.downstream} tone="relation" limit={6} onChipClick={applyChipSearch} emptyLabel="No downstream context" compact />
                </div>
              </div>
            ) : (
              <p className="mt-1 text-[10px] text-slate-500">Hover a row or flow token to preview upstream and downstream context.</p>
            )}
          </section>
        </div>

        {viewMode === "table" ? (
        <div ref={scrollRef} onScroll={onScroll} className="min-h-0 flex-1 overflow-auto">
          <table className="w-full table-fixed border-collapse text-left text-[8px] text-slate-700">
            <thead className="sticky top-0 z-10 bg-slate-100 text-[8px] uppercase tracking-wide text-slate-600">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => {
                    const sortable = header.column.getCanSort();
                    const sorted = header.column.getIsSorted();
                    const widthClass = tableColumnWidthClass(header.column.id);
                    return (
                      <th key={header.id} className={`p-2 ${widthClass} border-b border-slate-300 align-middle whitespace-nowrap overflow-hidden text-ellipsis`}>
                        {header.isPlaceholder ? null : (
                          <button
                            type="button"
                            className={`flex max-w-full items-center gap-1 overflow-hidden whitespace-nowrap text-ellipsis ${sortable ? "cursor-pointer" : "cursor-default"}`}
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
                    className={`absolute left-0 top-0 h-12 cursor-pointer align-middle border-b border-slate-200 hover:bg-slate-50 ${selected ? "bg-red-50" : loopHighlighted ? "bg-amber-50" : ""}`}
                    style={{ transform: `translateY(${virtualRow.start}px)`, width: "100%", display: "table", tableLayout: "fixed", height: `${TABLE_ROW_HEIGHT}px` }}
                    onMouseEnter={() => setHoveredTag(row.original.tag)}
                    onMouseLeave={() => setHoveredTag(null)}
                    onClick={() => {
                      setSelectedTag(row.original.tag);
                      onRowSelect?.(row.original);
                    }}
                  >
                    {row.getVisibleCells().map((cell) => {
                      const widthClass = tableColumnWidthClass(cell.column.id);
                      return (
                        <td key={cell.id} className={`p-2 ${widthClass} h-12 align-middle whitespace-nowrap overflow-hidden text-ellipsis text-[8px]`}>
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        ) : (
          <div className="min-h-0 flex-1 overflow-auto p-2">
            {equipmentGroups.length > 0 ? (
              <div className="space-y-2">
                {equipmentGroups.map(([equipment, rows]) => {
                  const expanded = expandedEquipmentGroups[equipment] ?? false;
                  return (
                    <section key={equipment} className="overflow-hidden rounded border border-slate-200 bg-white">
                      <button
                        type="button"
                        className="flex w-full items-center justify-between gap-3 border-b border-slate-100 px-3 py-2 text-left hover:bg-slate-50"
                        onClick={() => toggleEquipmentGroup(equipment)}
                      >
                        <div>
                          <p className="text-[11px] font-semibold text-slate-800">{equipment.replace(/_/g, " ")}</p>
                          <p className="text-[10px] text-slate-500">{rows.length} validated component{rows.length === 1 ? "" : "s"}</p>
                        </div>
                        <span className="text-slate-500">{expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}</span>
                      </button>
                      {expanded ? (
                        <div className="divide-y divide-slate-100">
                          {rows.map((row) => {
                            const selected = selectedTag === row.tag;
                            const highlighted = highlightedTagSet.has(toComparableToken(row.tag));
                            return (
                              <button
                                key={row.tag}
                                type="button"
                                className={`grid w-full gap-2 px-3 py-2 text-left hover:bg-slate-50 md:grid-cols-[minmax(0,180px)_110px_minmax(0,1fr)_minmax(220px,0.9fr)] ${selected ? "bg-red-50" : highlighted ? "bg-amber-50" : ""}`}
                                onMouseEnter={() => setHoveredTag(row.tag)}
                                onMouseLeave={() => setHoveredTag(null)}
                                onClick={() => {
                                  setSelectedTag(row.tag);
                                  onRowSelect?.(row);
                                }}
                              >
                                <div className="min-w-0">
                                  <p className="truncate text-[11px] font-semibold text-slate-800">{row.tag}</p>
                                  <p className="truncate text-[10px] text-slate-500">{toText(row.description)}</p>
                                </div>
                                <div>
                                  <span className={`inline-flex rounded-full border px-2 py-0.5 text-[8px] font-semibold uppercase ${roleToneClass(row.process_role)}`}>{toText(row.process_role)}</span>
                                </div>
                                <div className="min-w-0">
                                  <p className="truncate text-[10px] text-slate-700">{buildFlowPreview(row)}</p>
                                  <div className="mt-1 flex flex-wrap gap-1">
                                    <ChipList values={row.upstream.slice(0, 2)} tone="relation" limit={2} onChipClick={applyChipSearch} compact />
                                    <ChipList values={row.downstream.slice(0, 2)} tone="relation" limit={2} onChipClick={applyChipSearch} compact />
                                  </div>
                                </div>
                                <div className="min-w-0">
                                  <p className="truncate text-[10px] text-slate-600">Behavior: {toText(row.behavior_summary || row.behavior_card)}</p>
                                  <p className="mt-1 text-[9px] text-slate-500">Confidence {row.behavior_confidence.toFixed(2)}</p>
                                </div>
                              </button>
                            );
                          })}
                        </div>
                      ) : null}
                    </section>
                  );
                })}
              </div>
            ) : (
              <div className="flex h-full items-center justify-center rounded border border-dashed border-slate-300 bg-white text-[10px] text-slate-500">
                No validated plant model rows match the current filter.
              </div>
            )}
          </div>
        )}

        <div className="border-t border-slate-200 bg-white p-2">
          {selectedRow ? (
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              <section className="rounded border border-slate-200 bg-slate-50 p-2">
                <h4 className="mb-1 text-[9px] font-semibold uppercase tracking-wide text-slate-600">Cause Chain</h4>
                <ChipList values={selectedRow.cause_chain} tone="relation" limit={8} onChipClick={applyChipSearch} emptyLabel="No upstream causes" compact />
              </section>
              <section className="rounded border border-slate-200 bg-slate-50 p-2">
                <h4 className="mb-1 text-[9px] font-semibold uppercase tracking-wide text-slate-600">Effect Chain</h4>
                <ChipList values={selectedRow.effect_chain} tone="relation" limit={8} onChipClick={applyChipSearch} emptyLabel="No downstream effects" compact />
              </section>
              <section className="rounded border border-slate-200 bg-slate-50 p-2 md:col-span-2">
                <h4 className="mb-1 text-[9px] font-semibold uppercase tracking-wide text-slate-600">Impact</h4>
                <p className="text-[10px] leading-tight text-slate-700">{toText(selectedRow.impact_summary)}</p>
              </section>
              <section className="rounded border border-slate-200 bg-slate-50 p-2 md:col-span-2">
                <h4 className="mb-1 text-[9px] font-semibold uppercase tracking-wide text-slate-600">Live State</h4>
                <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-[10px] leading-tight text-slate-700 md:grid-cols-5">
                  <p>Tag: {selectedRow.tag}</p>
                  <p>Current: {toText(selectedRow.current_value)}</p>
                  <p>State: {toText(selectedRow.state)}</p>
                  <p>Setpoint: {toText(selectedRow.setpoint)}</p>
                  <p>Mode: {toText(selectedRow.mode)}</p>
                </div>
              </section>
            </div>
          ) : (
            <p className="text-[10px] text-slate-500">Select a row tag to inspect deterministic cause/effect and live behavior details.</p>
          )}
        </div>
      </div>

    </div>
  );
}
