import { useMemo, useRef, useState, type ReactElement } from "react";
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
import { ConfidenceBadge, StatusBadge, TypeBadge, WarningBadge } from "./Badge";
import type { EngineeringTableResponseRow } from "../../services/api";

type EngineeringTableProps = {
  rows: EngineeringTableResponseRow[];
  loading: boolean;
  error: string | null;
  onRowSelect?: (row: EngineeringTableResponseRow) => void;
  onTraceSignal?: (row: EngineeringTableResponseRow) => void;
  onOpenControlLoop?: (row: EngineeringTableResponseRow) => void;
  onOpenIOMapping?: (row: EngineeringTableResponseRow) => void;
};

const columnHelper = createColumnHelper<EngineeringTableResponseRow>();

const RELATION_KEYS: Array<
  | "measures"
  | "controls"
  | "controlled_by"
  | "signal_inputs"
  | "signal_outputs"
  | "upstream"
  | "downstream"
> = ["measures", "controls", "controlled_by", "signal_inputs", "signal_outputs", "upstream", "downstream"];

const CONFIDENCE_LEVELS = [0, 0.4, 0.6, 0.8] as const;

const toDisplayText = (value: unknown): string => {
  if (value === null || value === undefined) {
    return "—";
  }
  const text = String(value).trim();
  return text.length > 0 ? text : "—";
};

const buildSearchIndex = (row: EngineeringTableResponseRow): string => {
  const parts: string[] = [
    row.id,
    row.tag,
    row.type,
    row.subtype ?? "",
    row.description ?? "",
    row.system ?? "",
    row.equipment ?? "",
    row.process_role ?? "",
    row.state ?? "",
    row.mode ?? "",
    row.unit ?? "",
    row.power ?? "",
    ...row.document_source,
    ...row.line_reference,
    ...row.warnings,
  ];
  for (const key of RELATION_KEYS) {
    parts.push(...(row[key] ?? []));
  }
  return parts.join(" ").toLowerCase();
};

const toStatusList = (row: EngineeringTableResponseRow): Array<"Connected" | "Controlled" | "Actuated" | "Orphan"> => {
  const statuses: Array<"Connected" | "Controlled" | "Actuated" | "Orphan"> = [];
  if (row.is_orphan) {
    statuses.push("Orphan");
  } else {
    statuses.push("Connected");
  }
  if (row.is_controlled) {
    statuses.push("Controlled");
  }
  if (row.is_actuated) {
    statuses.push("Actuated");
  }
  return statuses;
};

const renderTextCell = (value: unknown, maxWidth = "max-w-[220px]"): ReactElement => {
  const text = toDisplayText(value);
  return (
    <span className={`block truncate ${maxWidth}`} title={text}>
      {text}
    </span>
  );
};

const renderArrayChips = (values: string[] | undefined, onApplySearch: (value: string) => void, tone: "relation" | "source" | "neutral"): ReactElement => {
  return <ChipList values={values ?? []} tone={tone} limit={3} onChipClick={onApplySearch} />;
};

const renderWarningBadges = (warnings: string[]): ReactElement => {
  if (warnings.length === 0) {
    return <span className="text-slate-400">—</span>;
  }
  const visible = warnings.slice(0, 2);
  const overflow = warnings.length - visible.length;
  return (
    <div className="flex max-w-[220px] items-center gap-1 overflow-hidden whitespace-nowrap" title={warnings.join(", ")}>
      {visible.map((warning) => (
        <WarningBadge key={warning} warning={warning} />
      ))}
      {overflow > 0 ? <span className="text-xs text-slate-500">+{overflow}</span> : null}
    </div>
  );
};

const renderStatusBadges = (statusList: Array<"Connected" | "Controlled" | "Actuated" | "Orphan">): ReactElement => {
  if (statusList.length === 0) {
    return <span className="text-slate-400">—</span>;
  }
  const visible = statusList.slice(0, 2);
  const overflow = statusList.length - visible.length;
  return (
    <div className="flex max-w-[210px] items-center gap-1 overflow-hidden whitespace-nowrap" title={statusList.join(", ")}>
      {visible.map((status) => (
        <StatusBadge key={status} status={status} />
      ))}
      {overflow > 0 ? <span className="text-xs text-slate-500">+{overflow}</span> : null}
    </div>
  );
};

const DetailGroup = ({ title, children }: { title: string; children: ReactElement | ReactElement[] }) => (
  <section className="space-y-1.5 rounded border border-slate-200 bg-slate-50 p-2">
    <h4 className="text-[10px] font-semibold uppercase tracking-wide text-slate-600">{title}</h4>
    <div className="space-y-1 text-[11px] text-slate-700">{children}</div>
  </section>
);

export default function EngineeringTable({
  rows,
  loading,
  error,
  onRowSelect,
  onTraceSignal,
  onOpenControlLoop,
  onOpenIOMapping,
}: EngineeringTableProps) {
  const [globalSearch, setGlobalSearch] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [sourceFilter, setSourceFilter] = useState<string>("all");
  const [confidenceThreshold, setConfidenceThreshold] = useState<number>(0);
  const [orphanOnly, setOrphanOnly] = useState<boolean>(false);
  const [controlledOnly, setControlledOnly] = useState<boolean>(false);
  const [sorting, setSorting] = useState<SortingState>([{ id: "confidence", desc: true }]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [selectedRow, setSelectedRow] = useState<EngineeringTableResponseRow | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const onApplySearch = (value: string): void => {
    setGlobalSearch(value);
  };

  const rowSearchIndex = useMemo(() => {
    const index = new Map<string, string>();
    for (const row of rows) {
      index.set(row.id, buildSearchIndex(row));
    }
    return index;
  }, [rows]);

  const typeOptions = useMemo(() => {
    return Array.from(new Set(rows.map((row) => row.type).filter((value) => value && value.trim().length > 0))).sort((a, b) => a.localeCompare(b));
  }, [rows]);

  const sourceOptions = useMemo(() => {
    return Array.from(
      new Set(rows.flatMap((row) => row.document_source).filter((value) => value && value.trim().length > 0))
    ).sort((a, b) => a.localeCompare(b));
  }, [rows]);

  const filteredRows = useMemo(() => {
    const normalizedSearch = globalSearch.trim().toLowerCase();
    return rows.filter((row) => {
      if (typeFilter !== "all" && row.type !== typeFilter) {
        return false;
      }
      if (sourceFilter !== "all" && !row.document_source.includes(sourceFilter)) {
        return false;
      }
      if (row.confidence < confidenceThreshold) {
        return false;
      }
      if (orphanOnly && !row.is_orphan) {
        return false;
      }
      if (controlledOnly && !row.is_controlled) {
        return false;
      }
      if (!normalizedSearch) {
        return true;
      }
      return (rowSearchIndex.get(row.id) || "").includes(normalizedSearch);
    });
  }, [rows, globalSearch, typeFilter, sourceFilter, confidenceThreshold, orphanOnly, controlledOnly, rowSearchIndex]);

  const selectedRowResolved = useMemo(() => {
    if (!selectedRow) {
      return null;
    }
    return rows.find((row) => row.id === selectedRow.id) ?? selectedRow;
  }, [rows, selectedRow]);

  const columns = useMemo(
    () => [
      columnHelper.accessor("tag", {
        header: "Tag",
        cell: (info) => renderTextCell(info.getValue(), "max-w-[150px]"),
      }),
      columnHelper.accessor("type", {
        header: "Type",
        cell: (info) => <TypeBadge type={toDisplayText(info.getValue())} />,
      }),
      columnHelper.accessor("subtype", {
        header: "Subtype",
        cell: (info) => renderTextCell(info.getValue(), "max-w-[140px]"),
      }),
      columnHelper.accessor("description", {
        header: "Description",
        cell: (info) => renderTextCell(info.getValue(), "max-w-[150px]"),
      }),
      columnHelper.accessor("system", {
        header: "System",
        cell: (info) => renderTextCell(info.getValue(), "max-w-[150px]"),
      }),
      columnHelper.accessor("process_role", {
        header: "Role",
        cell: (info) => renderTextCell(info.getValue(), "max-w-[140px]"),
      }),
      columnHelper.accessor("controls", {
        header: "Controls",
        cell: (info) => renderArrayChips(info.getValue(), onApplySearch, "relation"),
        sortingFn: (left, right) => left.original.controls.length - right.original.controls.length,
      }),
      columnHelper.accessor("controlled_by", {
        header: "Controlled By",
        cell: (info) => renderArrayChips(info.getValue(), onApplySearch, "relation"),
        sortingFn: (left, right) => left.original.controlled_by.length - right.original.controlled_by.length,
      }),
      columnHelper.accessor("signal_inputs", {
        header: "Signal Inputs",
        cell: (info) => renderArrayChips(info.getValue(), onApplySearch, "relation"),
        sortingFn: (left, right) => left.original.signal_inputs.length - right.original.signal_inputs.length,
      }),
      columnHelper.accessor("signal_outputs", {
        header: "Signal Outputs",
        cell: (info) => renderArrayChips(info.getValue(), onApplySearch, "relation"),
        sortingFn: (left, right) => left.original.signal_outputs.length - right.original.signal_outputs.length,
      }),
      columnHelper.accessor("upstream", {
        header: "Upstream",
        cell: (info) => renderArrayChips(info.getValue(), onApplySearch, "relation"),
        sortingFn: (left, right) => left.original.num_upstream - right.original.num_upstream,
      }),
      columnHelper.accessor("downstream", {
        header: "Downstream",
        cell: (info) => renderArrayChips(info.getValue(), onApplySearch, "relation"),
        sortingFn: (left, right) => left.original.num_downstream - right.original.num_downstream,
      }),
      columnHelper.accessor("document_source", {
        header: "Source",
        cell: (info) => renderArrayChips(info.getValue(), onApplySearch, "source"),
        sortingFn: (left, right) => left.original.document_source.length - right.original.document_source.length,
      }),
      columnHelper.accessor("confidence", {
        header: "Confidence",
        cell: (info) => <ConfidenceBadge value={info.getValue()} />,
      }),
      columnHelper.display({
        id: "status",
        header: "Status",
        cell: (info) => {
          const row = info.row.original;
          const statusList = toStatusList(row);
          return renderStatusBadges(statusList);
        },
        sortingFn: (left, right) => left.original.num_connections - right.original.num_connections,
      }),
      columnHelper.accessor("warnings", {
        header: "Warnings",
        cell: (info) => renderWarningBadges(info.getValue()),
        sortingFn: (left, right) => left.original.warnings.length - right.original.warnings.length,
      }),
      columnHelper.display({
        id: "actions",
        header: "Actions",
        enableSorting: false,
        cell: (info) => {
          const row = info.row.original;
          return (
            <div className="flex items-center gap-1" onClick={(event) => event.stopPropagation()}>
              <button
                type="button"
                className="rounded border border-slate-300 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-gray-100"
                onClick={() => onTraceSignal?.(row)}
              >
                Trace Signal
              </button>
              <button
                type="button"
                className="rounded border border-slate-300 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-gray-100"
                onClick={() => onOpenControlLoop?.(row)}
              >
                Open CL
              </button>
              <button
                type="button"
                className="rounded border border-slate-300 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-gray-100"
                onClick={() => onOpenIOMapping?.(row)}
              >
                Open IO
              </button>
            </div>
          );
        },
      }),
    ],
    [onTraceSignal, onOpenControlLoop, onOpenIOMapping]
  );

  const table = useReactTable({
    data: filteredRows,
    columns,
    state: {
      sorting,
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const tableBodyRows = table.getRowModel().rows;

  const rowVirtualizer = useVirtualizer({
    count: tableBodyRows.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => 36,
    overscan: 12,
  });

  if (loading) {
    return <div className="flex h-full items-center justify-center text-sm text-slate-500">Loading engineering table…</div>;
  }

  if (error) {
    return <div className="flex h-full items-center justify-center text-sm text-red-600">{error}</div>;
  }

  if (rows.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 text-sm text-slate-500">
        <p>No engineering rows found for this project.</p>
        <p className="text-xs text-slate-400">Run parse to generate entities and relationships.</p>
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 w-full gap-3 overflow-hidden rounded border border-slate-300 bg-slate-50 p-2">
      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden rounded border border-slate-300 bg-white">
        <div className="grid grid-cols-1 gap-2 border-b border-slate-200 p-2 md:grid-cols-6">
          <input
            value={globalSearch}
            onChange={(event) => setGlobalSearch(event.target.value)}
            placeholder="Search tags, types, relationships, source..."
            className="w-full rounded border border-slate-300 bg-slate-50 px-2 py-1.5 text-xs text-slate-700 outline-none ring-slate-400 focus:ring md:col-span-2"
          />
          <select
            value={typeFilter}
            onChange={(event) => setTypeFilter(event.target.value)}
            className="rounded border border-slate-300 bg-slate-50 px-2 py-1.5 text-xs text-slate-700"
          >
            <option value="all">All Types</option>
            {typeOptions.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
          <select
            value={sourceFilter}
            onChange={(event) => setSourceFilter(event.target.value)}
            className="rounded border border-slate-300 bg-slate-50 px-2 py-1.5 text-xs text-slate-700"
          >
            <option value="all">All Sources</option>
            {sourceOptions.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
          <select
            value={String(confidenceThreshold)}
            onChange={(event) => setConfidenceThreshold(Number(event.target.value))}
            className="rounded border border-slate-300 bg-slate-50 px-2 py-1.5 text-xs text-slate-700"
          >
            {CONFIDENCE_LEVELS.map((level) => (
              <option key={level} value={String(level)}>
                Min conf. {level.toFixed(1)}
              </option>
            ))}
          </select>
          <div className="flex items-center gap-3 text-[11px] text-slate-600">
            <label className="inline-flex items-center gap-1">
              <input type="checkbox" checked={orphanOnly} onChange={(event) => setOrphanOnly(event.target.checked)} />
              Orphan only
            </label>
            <label className="inline-flex items-center gap-1">
              <input type="checkbox" checked={controlledOnly} onChange={(event) => setControlledOnly(event.target.checked)} />
              Controlled only
            </label>
          </div>

          <div className="text-xs text-slate-500">
            {filteredRows.length} / {rows.length} rows
          </div>
        </div>

        <div ref={scrollRef} className="min-h-0 flex-1 overflow-auto" id="engineering-table-scroll">
          <table className="min-w-[2100px] w-full table-fixed border-collapse text-left text-[11px] text-slate-700">
            <thead className="sticky top-0 z-10 bg-slate-100 text-[10px] uppercase tracking-wide text-slate-600">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => {
                    const sortable = header.column.getCanSort();
                    const sorted = header.column.getIsSorted();
                    return (
                      <th
                        key={header.id}
                        className={`border-b border-slate-300 px-2 py-2 ${sorted ? "bg-blue-50 text-blue-700" : "bg-gray-100"}`}
                        style={{ width: header.getSize() }}
                      >
                        {header.isPlaceholder ? null : (
                          <button
                            type="button"
                            className={`flex items-center gap-1 ${sortable ? "cursor-pointer" : "cursor-default"}`}
                            onClick={sortable ? header.column.getToggleSortingHandler() : undefined}
                          >
                            {flexRender(header.column.columnDef.header, header.getContext())}
                            {sortable ? (
                              <span>{sorted === "desc" ? "↓" : sorted === "asc" ? "↑" : "↕"}</span>
                            ) : null}
                          </button>
                        )}
                      </th>
                    );
                  })}
                </tr>
              ))}
            </thead>
            <tbody
              style={{
                height: `${rowVirtualizer.getTotalSize()}px`,
                position: "relative",
              }}
            >
              {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                const row = tableBodyRows[virtualRow.index];
                if (!row) {
                  return null;
                }
                const selected = row.original.id === selectedId;
                const hasWarnings = row.original.warnings.length > 0;

                return (
                  <tr
                    key={row.id}
                    className={`absolute left-0 top-0 cursor-pointer border-b border-slate-200 hover:bg-gray-50 ${selected ? "bg-blue-50" : ""} ${
                      hasWarnings ? "border-l-2 border-l-red-400" : ""
                    }`}
                    style={{ transform: `translateY(${virtualRow.start}px)`, width: "100%", display: "table", tableLayout: "fixed" }}
                    onClick={() => {
                      setSelectedId(row.original.id);
                      setSelectedRow(row.original);
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
      </div>

      {selectedRowResolved ? (
        <aside className="h-full w-[380px] shrink-0 overflow-auto border-l border-slate-300 bg-white p-3">
          <div className="space-y-2 text-xs text-slate-700">
            <div className="flex items-start justify-between gap-2 border-b border-slate-200 pb-2">
              <div>
                <h3 className="text-sm font-semibold text-slate-800" title={selectedRowResolved.tag}>
                  {selectedRowResolved.tag}
                </h3>
                <div className="mt-1">
                  <TypeBadge type={toDisplayText(selectedRowResolved.type)} />
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  setSelectedId("");
                  setSelectedRow(null);
                }}
                className="rounded border border-slate-300 px-2 py-0.5 text-xs font-medium text-slate-600 hover:bg-gray-100"
              >
                ×
              </button>
            </div>

            <DetailGroup title="Basic Info">
              <p className="truncate" title={toDisplayText(selectedRowResolved.description)}>Description: {toDisplayText(selectedRowResolved.description)}</p>
              <p className="truncate" title={toDisplayText(selectedRowResolved.system)}>System: {toDisplayText(selectedRowResolved.system)}</p>
              <p>Role: {toDisplayText(selectedRowResolved.process_role)}</p>
            </DetailGroup>

            <DetailGroup title="Signals">
              <p>Signal Inputs</p>
              {renderArrayChips(selectedRowResolved.signal_inputs, onApplySearch, "relation")}
              <p>Signal Outputs</p>
              {renderArrayChips(selectedRowResolved.signal_outputs, onApplySearch, "relation")}
            </DetailGroup>

            <DetailGroup title="Relationships">
              <p>Controls</p>
              {renderArrayChips(selectedRowResolved.controls, onApplySearch, "relation")}
              <p>Controlled By</p>
              {renderArrayChips(selectedRowResolved.controlled_by, onApplySearch, "relation")}
              <p>Upstream</p>
              {renderArrayChips(selectedRowResolved.upstream, onApplySearch, "relation")}
              <p>Downstream</p>
              {renderArrayChips(selectedRowResolved.downstream, onApplySearch, "relation")}
            </DetailGroup>

            <DetailGroup title="Chains">
              <p>Control Chain</p>
              <p className="truncate max-w-[150px]" title={selectedRowResolved.control_chain.join(" -> ")}>
                {selectedRowResolved.control_chain.join(" -> ") || "—"}
              </p>
              <p>Flow Chain</p>
              <p className="truncate max-w-[150px]" title={selectedRowResolved.flow_chain.join(" -> ")}>
                {selectedRowResolved.flow_chain.join(" -> ") || "—"}
              </p>
            </DetailGroup>

            <DetailGroup title="Source">
              <p>Document Source</p>
              {renderArrayChips(selectedRowResolved.document_source, onApplySearch, "source")}
              <p>Line Reference</p>
              {renderArrayChips(selectedRowResolved.line_reference, onApplySearch, "source")}
            </DetailGroup>

            <DetailGroup title="Status">
              <div className="flex flex-wrap gap-1">
                {toStatusList(selectedRowResolved).map((status) => (
                  <StatusBadge key={status} status={status} />
                ))}
              </div>
              <div className="pt-1">
                <ConfidenceBadge value={selectedRowResolved.confidence} />
              </div>
              <p>Current Value: {toDisplayText(selectedRowResolved.current_value)}</p>
              <p>State: {toDisplayText(selectedRowResolved.state)}</p>
              <p>Setpoint: {toDisplayText(selectedRowResolved.setpoint)}</p>
              <p>Mode: {toDisplayText(selectedRowResolved.mode)}</p>
              <p>Unit: {toDisplayText(selectedRowResolved.unit)}</p>
              <p>Range: {toDisplayText(selectedRowResolved.range_min)} to {toDisplayText(selectedRowResolved.range_max)}</p>
              <p>Fail State: {toDisplayText(selectedRowResolved.fail_state)}</p>
              <p>Warnings</p>
              {renderWarningBadges(selectedRowResolved.warnings)}
            </DetailGroup>
          </div>
        </aside>
      ) : null}
    </div>
  );
}
