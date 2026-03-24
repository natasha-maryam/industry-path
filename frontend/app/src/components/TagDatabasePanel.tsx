import { useCallback, useEffect, useMemo, useState } from "react";
import {
  exportTagIntelligenceCsv,
  exportTagIntelligenceJson,
  getTagIntelligence,
  type TagIntelligencePayload,
  type TagIntelligenceRow,
} from "../services/api";

type TagCategory = "all" | "unused" | "orphans" | "conflicts";

type TagDatabasePanelProps = {
  projectId?: string;
};

const CATEGORY_LABELS: Record<TagCategory, string> = {
  all: "All",
  unused: "Unused",
  orphans: "Orphans",
  conflicts: "Conflicts",
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

export default function TagDatabasePanel({ projectId }: TagDatabasePanelProps) {
  const [category, setCategory] = useState<TagCategory>("all");
  const [searchInput, setSearchInput] = useState<string>("");
  const [payload, setPayload] = useState<TagIntelligencePayload | null>(null);
  const [rows, setRows] = useState<TagIntelligenceRow[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState<"csv" | "json" | null>(null);

  const loadRows = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getTagIntelligence({
        projectId,
        category,
        search: searchInput,
      });
      setPayload(result);
      setRows(result.rows ?? []);
    } catch {
      setError("Tag intelligence endpoint unavailable.");
      setRows([]);
      setPayload(null);
    } finally {
      setLoading(false);
    }
  }, [category, projectId, searchInput]);

  useEffect(() => {
    void loadRows();
  }, [loadRows]);

  const summaryText = useMemo(() => {
    if (!payload?.summary) {
      return "No summary";
    }
    return `total ${payload.summary.total} · unused ${payload.summary.unused} · orphans ${payload.summary.orphans} · conflicts ${payload.summary.conflicts}`;
  }, [payload]);

  const exportCsv = useCallback(async () => {
    setExporting("csv");
    try {
      const blob = await exportTagIntelligenceCsv({ projectId, category, search: searchInput });
      downloadBlob(blob, `tag-intelligence-${category}.csv`);
    } finally {
      setExporting(null);
    }
  }, [category, projectId, searchInput]);

  const exportJson = useCallback(async () => {
    setExporting("json");
    try {
      const blob = await exportTagIntelligenceJson({ projectId, category, search: searchInput });
      downloadBlob(blob, `tag-intelligence-${category}.json`);
    } finally {
      setExporting(null);
    }
  }, [category, projectId, searchInput]);

  return (
    <section className="rounded border border-slate-300 bg-white p-2">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-700">Tag Intelligence</h4>
        <div className="flex flex-wrap gap-1">
          {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
            <button
              key={value}
              type="button"
              className={`command-btn ${category === value ? "primary" : ""}`}
              onClick={() => setCategory(value as TagCategory)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-2 flex flex-wrap items-center gap-2">
        <input
          value={searchInput}
          onChange={(event) => setSearchInput(event.target.value)}
          placeholder="Search tag, type, equipment, conflict..."
          className="min-w-[240px] flex-1 rounded border border-slate-300 bg-slate-50 px-2 py-1 text-[11px]"
        />
        <button type="button" className="command-btn" onClick={() => void loadRows()}>
          Refresh
        </button>
        <button type="button" className="command-btn" onClick={() => void exportCsv()} disabled={exporting !== null}>
          {exporting === "csv" ? "Exporting CSV..." : "Export CSV"}
        </button>
        <button type="button" className="command-btn" onClick={() => void exportJson()} disabled={exporting !== null}>
          {exporting === "json" ? "Exporting JSON..." : "Export JSON"}
        </button>
      </div>

      <p className="mb-2 text-[11px] text-slate-600">{summaryText}</p>

      <div className="max-h-64 overflow-auto rounded border border-slate-200 bg-slate-50">
        <table className="w-full border-collapse text-left text-[11px] text-slate-700">
          <thead className="sticky top-0 bg-slate-100 text-[10px] uppercase tracking-wide text-slate-600">
            <tr>
              <th className="border-b border-slate-300 px-2 py-1">Tag</th>
              <th className="border-b border-slate-300 px-2 py-1">Type</th>
              <th className="border-b border-slate-300 px-2 py-1">Equipment</th>
              <th className="border-b border-slate-300 px-2 py-1">In/Out</th>
              <th className="border-b border-slate-300 px-2 py-1">Flags</th>
              <th className="border-b border-slate-300 px-2 py-1">Conflicts</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td className="px-2 py-2" colSpan={6}>
                  Loading tag intelligence...
                </td>
              </tr>
            ) : null}
            {!loading && error ? (
              <tr>
                <td className="px-2 py-2 text-red-700" colSpan={6}>
                  {error}
                </td>
              </tr>
            ) : null}
            {!loading && !error && rows.length === 0 ? (
              <tr>
                <td className="px-2 py-2 text-slate-500" colSpan={6}>
                  No rows for selected filter.
                </td>
              </tr>
            ) : null}
            {!loading && !error
              ? rows.map((row) => (
                  <tr key={row.tag}>
                    <td className="border-b border-slate-200 px-2 py-1 font-medium">{row.tag}</td>
                    <td className="border-b border-slate-200 px-2 py-1">{row.tag_type ?? "—"}</td>
                    <td className="border-b border-slate-200 px-2 py-1">{row.equipment ?? "—"}</td>
                    <td className="border-b border-slate-200 px-2 py-1">{row.inbound_count}/{row.outbound_count}</td>
                    <td className="border-b border-slate-200 px-2 py-1">
                      {row.is_unused ? "unused " : ""}
                      {row.is_orphan ? "orphan" : ""}
                      {!row.is_unused && !row.is_orphan ? "—" : ""}
                    </td>
                    <td className="border-b border-slate-200 px-2 py-1">{row.conflicts.length > 0 ? row.conflicts.join("; ") : "—"}</td>
                  </tr>
                ))
              : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}
