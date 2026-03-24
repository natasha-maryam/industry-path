import { useCallback, useEffect, useMemo, useState } from "react";
import { ClipboardList, ChevronDown, ChevronRight, RefreshCw } from "lucide-react";
import { getProductionAuditLogs, type ProductionAuditEvent } from "../services/api";

type AuditPanelProps = {
  authToken?: string;
};

export default function AuditPanel({ authToken = "" }: AuditPanelProps) {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [events, setEvents] = useState<ProductionAuditEvent[]>([]);

  const loadAudit = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await getProductionAuditLogs(50, authToken);
      setEvents(rows);
    } catch {
      setError("Audit endpoint unavailable or unauthorized.");
    } finally {
      setLoading(false);
    }
  }, [authToken]);

  useEffect(() => {
    if (!isExpanded) {
      return;
    }
    void loadAudit();
  }, [isExpanded, loadAudit]);

  const latestActions = useMemo(() => events.slice(0, 8), [events]);

  return (
    <section className="rounded border border-slate-300 bg-white p-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1">
          <ClipboardList size={14} className="text-slate-600" />
          <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-700">Audit Actions</h4>
        </div>
        <div className="flex items-center gap-1">
          <button type="button" className="command-btn" onClick={() => void loadAudit()}>
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
          </button>
          <button type="button" className="command-btn" onClick={() => setIsExpanded((value) => !value)}>
            {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          </button>
        </div>
      </div>

      <p className="mt-1 text-[11px] text-slate-600">{events.length} events loaded</p>

      {isExpanded ? (
        <div className="mt-2 max-h-44 overflow-auto rounded border border-slate-200 bg-slate-50 p-2 text-[11px]">
          {error ? <p className="text-red-700">{error}</p> : null}
          {!error && latestActions.length === 0 ? <p className="text-slate-500">No audit actions yet.</p> : null}
          {!error
            ? latestActions.map((event, index) => (
                <div key={`${event.created_at}-${event.event_type}-${index}`} className="mb-1 rounded border border-slate-200 bg-white px-2 py-1 text-slate-700">
                  <p className="font-semibold">{event.event_type}</p>
                  <p>actor: {event.actor}</p>
                  <p className="text-[10px] text-slate-500">{new Date(event.created_at).toLocaleString()}</p>
                </div>
              ))
            : null}
        </div>
      ) : null}
    </section>
  );
}
