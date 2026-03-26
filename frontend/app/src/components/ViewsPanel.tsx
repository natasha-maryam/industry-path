import { useCallback, useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import DiffViewer from "./DiffViewer";
import {
  createSavedView,
  createSavedViewVersion,
  diffSavedViewVersions,
  listSavedViewVersions,
  listSavedViews,
  type EngineeringTableResponseRow,
  type SavedEngineeringView,
  type SavedEngineeringViewDiff,
  type SavedEngineeringViewVersion,
} from "../services/api";

type ViewsPanelProps = {
  projectId?: string;
  currentRows: EngineeringTableResponseRow[];
  rowsSource?: string;
  filteredRowsCount?: number;
  rowsLoading?: boolean;
};

export default function ViewsPanel({
  projectId,
  currentRows,
  rowsSource = "workspace_rows",
  filteredRowsCount = 0,
  rowsLoading = false,
}: ViewsPanelProps) {
  const [views, setViews] = useState<SavedEngineeringView[]>([]);
  const [selectedViewId, setSelectedViewId] = useState<string>("");
  const [versions, setVersions] = useState<SavedEngineeringViewVersion[]>([]);

  const [viewName, setViewName] = useState<string>("");
  const [viewQuery, setViewQuery] = useState<string>("");
  const [viewScript, setViewScript] = useState<string>("");
  const [snapshotNotes, setSnapshotNotes] = useState<string>("");

  const [beforeVersionId, setBeforeVersionId] = useState<string>("");
  const [afterVersionId, setAfterVersionId] = useState<string>("");
  const [diff, setDiff] = useState<SavedEngineeringViewDiff | null>(null);

  const [loadingViews, setLoadingViews] = useState<boolean>(false);
  const [loadingDiff, setLoadingDiff] = useState<boolean>(false);
  const [busyAction, setBusyAction] = useState<"save_view" | "save_snapshot" | "refresh_versions" | null>(null);
  const [status, setStatus] = useState<string>("Views idle");
  const [error, setError] = useState<string | null>(null);

  const liveEngineeringRows = useMemo(() => currentRows, [currentRows]);
  const totalLiveRowsCount = liveEngineeringRows.length;
  const filteredVisibleRowsCount = filteredRowsCount > 0 ? filteredRowsCount : totalLiveRowsCount;

  const refreshViews = useCallback(async () => {
    if (!projectId) {
      setViews([]);
      setSelectedViewId("");
      setVersions([]);
      return;
    }

    setLoadingViews(true);
    setError(null);
    try {
      const nextViews = await listSavedViews(projectId);
      setViews(nextViews);
      if (selectedViewId && nextViews.some((item) => item.id === selectedViewId)) {
        return;
      }
      const firstId = nextViews[0]?.id ?? "";
      setSelectedViewId(firstId);
    } catch {
      setError("Failed to load saved views.");
    } finally {
      setLoadingViews(false);
    }
  }, [projectId, selectedViewId]);

  const refreshVersions = useCallback(async () => {
    if (!selectedViewId) {
      setVersions([]);
      return;
    }

    try {
      setBusyAction("refresh_versions");
      const nextVersions = await listSavedViewVersions(selectedViewId);
      setVersions(nextVersions);
      if (nextVersions.length >= 2) {
        setBeforeVersionId((current) => current || nextVersions[1].id);
        setAfterVersionId((current) => current || nextVersions[0].id);
      }
    } catch {
      setError("Failed to load view versions.");
    } finally {
      setBusyAction(null);
    }
  }, [selectedViewId]);

  useEffect(() => {
    void refreshViews();
  }, [refreshViews]);

  useEffect(() => {
    void refreshVersions();
  }, [refreshVersions]);

  const selectedView = useMemo(() => views.find((item) => item.id === selectedViewId) ?? null, [selectedViewId, views]);

  const handleSaveView = useCallback(async () => {
    if (!projectId) {
      setError("Select a project before saving a view.");
      return;
    }
    if (!viewName.trim()) {
      setError("View name is required.");
      return;
    }

    setError(null);
    setBusyAction("save_view");
    try {
      const saved = await createSavedView({
        project_id: projectId,
        name: viewName,
        query: viewQuery,
        script: viewScript,
      });
      setStatus(`Saved view: ${saved.name}`);
      setViewName("");
      await refreshViews();
      setSelectedViewId(saved.id);
    } catch {
      setError("Failed to save view.");
    } finally {
      setBusyAction(null);
    }
  }, [projectId, refreshViews, viewName, viewQuery, viewScript]);

  const handleSaveSnapshot = useCallback(async () => {
    // Manual QA checklist:
    // 1) save snapshot with visible rows loaded
    // 2) save snapshot after websocket/runtime update
    // 3) save snapshot while search/filter is active (full live dataset still saved)
    // 4) save snapshot after refresh/reload
    // 5) save snapshot with no selected view (must block)
    if (!selectedViewId) {
      setError("Select a saved view first.");
      return;
    }

    if (rowsLoading) {
      setError("Engineering rows are still loading. Please wait before saving snapshot.");
      return;
    }

    setError(null);
    setBusyAction("save_snapshot");
    try {
      console.info("[views.snapshot] save_start", {
        selectedViewId,
        totalLiveRowsCount,
        filteredVisibleRowsCount,
        dataSourceUsed: rowsSource,
        notesLength: snapshotNotes.trim().length,
      });

      if (totalLiveRowsCount === 0) {
        setError("Cannot save snapshot from an empty engineering table.");
        console.info("[views.snapshot] save_blocked_empty", {
          selectedViewId,
          totalLiveRowsCount,
          filteredVisibleRowsCount,
          dataSourceUsed: rowsSource,
        });
        return;
      }

      const response = await createSavedViewVersion({
        view_id: selectedViewId,
        snapshot: {
          rows: liveEngineeringRows,
          row_source: rowsSource,
          filtered_visible_rows_count: filteredVisibleRowsCount,
        },
        notes: snapshotNotes,
      });
      setSnapshotNotes("");
      setStatus("Snapshot saved.");
      toast.success("Snapshot created successfully.", {
        className: "industrial-toast",
      });
      console.info("[views.snapshot] save_success", {
        selectedViewId,
        totalLiveRowsCount,
        filteredVisibleRowsCount,
        dataSourceUsed: rowsSource,
        backendStatus: response?.id ? "success" : "unknown",
      });
      await refreshVersions();
    } catch (err) {
      setError("Failed to save snapshot.");
      console.info("[views.snapshot] save_error", {
        selectedViewId,
        totalLiveRowsCount,
        filteredVisibleRowsCount,
        dataSourceUsed: rowsSource,
        backendStatus: "error",
        error: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setBusyAction(null);
    }
  }, [
    filteredVisibleRowsCount,
    liveEngineeringRows,
    refreshVersions,
    rowsLoading,
    rowsSource,
    selectedViewId,
    snapshotNotes,
    totalLiveRowsCount,
  ]);

  const handleRunDiff = useCallback(async () => {
    if (!beforeVersionId || !afterVersionId) {
      setError("Select two versions for diff.");
      return;
    }
    if (beforeVersionId === afterVersionId) {
      setError("Select different versions for diff.");
      return;
    }

    setLoadingDiff(true);
    setError(null);
    try {
      const payload = await diffSavedViewVersions(beforeVersionId, afterVersionId);
      setDiff(payload);
      setStatus(`Diff computed: +${payload.summary.added} / -${payload.summary.removed} / Δ${payload.summary.changed}`);
    } catch {
      setError("Failed to compute diff.");
      setDiff(null);
    } finally {
      setLoadingDiff(false);
    }
  }, [afterVersionId, beforeVersionId]);

  return (
    <section className="mb-2 rounded border border-slate-300 bg-white p-2">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-700">Saved Engineering Views</h4>
        <span className="text-[11px] text-slate-500">{loadingViews ? "Loading..." : status}</span>
      </div>

      <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
        <div className="space-y-1 rounded border border-slate-200 bg-slate-50 p-2 md:col-span-2">
          <p className="text-[11px] font-semibold text-slate-700">Save Current View</p>
          <input
            value={viewName}
            onChange={(event) => setViewName(event.target.value)}
            placeholder="View name"
            className="w-full rounded border border-slate-300 bg-white px-2 py-1 text-[11px]"
          />
          <textarea
            value={viewQuery}
            onChange={(event) => setViewQuery(event.target.value)}
            placeholder="Optional query"
            className="h-16 w-full rounded border border-slate-300 bg-white p-2 text-[11px]"
          />
          <textarea
            value={viewScript}
            onChange={(event) => setViewScript(event.target.value)}
            placeholder="Optional script"
            className="h-16 w-full rounded border border-slate-300 bg-white p-2 text-[11px]"
          />
          <button type="button" className="command-btn" onClick={() => void handleSaveView()}>
            {busyAction === "save_view" ? "Saving..." : "Save View"}
          </button>
        </div>

        <div className="space-y-1 rounded border border-slate-200 bg-slate-50 p-2">
          <p className="text-[11px] font-semibold text-slate-700">Select Saved View</p>
          <select
            value={selectedViewId}
            onChange={(event) => setSelectedViewId(event.target.value)}
            className="w-full rounded border border-slate-300 bg-white px-2 py-1 text-[11px]"
          >
            <option value="">Select view</option>
            {views.map((view) => (
              <option key={view.id} value={view.id}>
                {view.name}
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-600">{selectedView ? `Created: ${new Date(selectedView.created_at).toLocaleString()}` : "No view selected"}</p>
        </div>
      </div>

      <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-3">
        <div className="space-y-1 rounded border border-slate-200 bg-slate-50 p-2 md:col-span-1">
          <p className="text-[11px] font-semibold text-slate-700">Save Snapshot</p>
          <textarea
            value={snapshotNotes}
            onChange={(event) => setSnapshotNotes(event.target.value)}
            placeholder="Notes"
            className="h-16 w-full rounded border border-slate-300 bg-white p-2 text-[11px]"
          />
          <button type="button" className="command-btn" onClick={() => void handleSaveSnapshot()}>
            {rowsLoading ? "Rows Loading..." : busyAction === "save_snapshot" ? "Saving..." : "Save Snapshot"}
          </button>
        </div>

        <div className="space-y-1 rounded border border-slate-200 bg-slate-50 p-2 md:col-span-2">
          <p className="text-[11px] font-semibold text-slate-700">Compare Snapshots</p>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            <select
              value={beforeVersionId}
              onChange={(event) => setBeforeVersionId(event.target.value)}
              className="rounded border border-slate-300 bg-white px-2 py-1 text-[11px]"
            >
              <option value="">Before version</option>
              {versions.map((version) => (
                <option key={`before-${version.id}`} value={version.id}>
                  {new Date(version.created_at).toLocaleString()} {version.notes ? `· ${version.notes}` : ""}
                </option>
              ))}
            </select>
            <select
              value={afterVersionId}
              onChange={(event) => setAfterVersionId(event.target.value)}
              className="rounded border border-slate-300 bg-white px-2 py-1 text-[11px]"
            >
              <option value="">After version</option>
              {versions.map((version) => (
                <option key={`after-${version.id}`} value={version.id}>
                  {new Date(version.created_at).toLocaleString()} {version.notes ? `· ${version.notes}` : ""}
                </option>
              ))}
            </select>
          </div>
          <button type="button" className="command-btn" onClick={() => void handleRunDiff()}>
            Compare Snapshots
          </button>
        </div>
      </div>

      {error ? <p className="mt-2 text-xs text-red-700">{error}</p> : null}

      <div className="mt-2">
        <DiffViewer diff={diff} loading={loadingDiff} error={error} />
      </div>
    </section>
  );
}
