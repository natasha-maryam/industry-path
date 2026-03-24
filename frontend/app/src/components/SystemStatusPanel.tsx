import { useCallback, useEffect, useState } from "react";
import { Activity, ChevronDown, ChevronRight, RefreshCw } from "lucide-react";
import { getProductionHealth, type ProductionHealthResponse } from "../services/api";

type SystemStatusPanelProps = {
  authToken?: string;
  pollIntervalMs?: number;
};

export default function SystemStatusPanel({ authToken = "", pollIntervalMs = 8000 }: SystemStatusPanelProps) {
  const [isExpanded, setIsExpanded] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<ProductionHealthResponse | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await getProductionHealth(authToken);
      setHealth(payload);
    } catch {
      setError("Health endpoint unavailable or unauthorized.");
    } finally {
      setLoading(false);
    }
  }, [authToken]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      void refresh();
    }, Math.max(2000, pollIntervalMs));
    return () => {
      window.clearInterval(timer);
    };
  }, [pollIntervalMs, refresh]);

  const redisEnabled = Boolean(health?.services?.redis?.enabled);
  const healthyConnectors = Number(health?.services?.connectors?.healthy ?? 0);
  const totalConnectors = Number(health?.services?.connectors?.total ?? 0);

  return (
    <section className="rounded border border-slate-300 bg-white p-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1">
          <Activity size={14} className="text-slate-600" />
          <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-700">System Status</h4>
        </div>
        <div className="flex items-center gap-1">
          <button type="button" className="command-btn" onClick={() => void refresh()}>
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
          </button>
          <button type="button" className="command-btn" onClick={() => setIsExpanded((value) => !value)}>
            {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          </button>
        </div>
      </div>

      <div className="mt-1 flex items-center gap-2 text-[11px]">
        <span className={`rounded border px-2 py-0.5 ${health?.status === "ok" ? "border-emerald-300 bg-emerald-50 text-emerald-700" : "border-amber-300 bg-amber-50 text-amber-700"}`}>
          {health?.status ?? "unknown"}
        </span>
        <span className="text-slate-600">Connectors {healthyConnectors}/{totalConnectors}</span>
      </div>

      {isExpanded ? (
        <div className="mt-2 rounded border border-slate-200 bg-slate-50 p-2 text-[11px] text-slate-700">
          {error ? <p className="text-red-700">{error}</p> : null}
          {!error ? (
            <div className="grid grid-cols-1 gap-1">
              <p>Redis: {redisEnabled ? "enabled" : "fallback mode"}</p>
              <p>Connector health: {healthyConnectors} healthy / {totalConnectors} total</p>
              <p>Last update: {health?.timestamp ? new Date(health.timestamp).toLocaleTimeString() : "—"}</p>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
