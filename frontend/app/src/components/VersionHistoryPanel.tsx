type VersionChangeType = "logic_generation" | "plant_graph_update" | "simulation_validation" | "deployment" | "configuration_change";

export type VersionHistoryEntry = {
  id: string;
  version_label: string;
  title: string;
  timestamp: string;
  change_type: VersionChangeType;
};

type VersionHistoryPanelProps = {
  entries?: VersionHistoryEntry[];
  onLoad?: (entry: VersionHistoryEntry) => void;
  onCompare?: (entry: VersionHistoryEntry) => void;
  onRollback?: (entry: VersionHistoryEntry) => void;
  onExport?: (entry: VersionHistoryEntry) => void;
};

const DEFAULT_ENTRIES: VersionHistoryEntry[] = [
  {
    id: "ver-logic-001",
    version_label: "v2.14",
    title: "Logic Generation",
    timestamp: "2026-03-13T10:31:00Z",
    change_type: "logic_generation",
  },
  {
    id: "ver-graph-001",
    version_label: "v2.13",
    title: "Plant Graph Update",
    timestamp: "2026-03-13T10:18:12Z",
    change_type: "plant_graph_update",
  },
  {
    id: "ver-sim-001",
    version_label: "v2.12",
    title: "Simulation Validation",
    timestamp: "2026-03-13T10:07:02Z",
    change_type: "simulation_validation",
  },
  {
    id: "ver-deploy-001",
    version_label: "v2.11",
    title: "Deployment",
    timestamp: "2026-03-13T09:56:21Z",
    change_type: "deployment",
  },
  {
    id: "ver-config-001",
    version_label: "v2.10",
    title: "Configuration Change",
    timestamp: "2026-03-13T09:43:55Z",
    change_type: "configuration_change",
  },
];

const formatTimestamp = (value: string): string => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
};

export default function VersionHistoryPanel({
  entries = DEFAULT_ENTRIES,
  onLoad,
  onCompare,
  onRollback,
  onExport,
}: VersionHistoryPanelProps) {
  return (
    <div className="version-history-grid">
      <div className="panel-subtitle">Version History</div>

      <div className="version-history-list" role="list" aria-label="Version history list">
        {entries.map((entry) => (
          <article className="version-history-item" key={entry.id} role="listitem">
            <div className="version-history-head">
              <span className="version-history-label">{entry.version_label}</span>
              <strong>{entry.title}</strong>
            </div>

            <div className="version-history-time value-mono">{formatTimestamp(entry.timestamp)}</div>

            <div className="version-history-actions">
              <button onClick={() => onLoad?.(entry)} type="button">
                Load
              </button>
              <button onClick={() => onCompare?.(entry)} type="button">
                Compare
              </button>
              <button onClick={() => onRollback?.(entry)} type="button">
                Rollback
              </button>
              <button onClick={() => onExport?.(entry)} type="button">
                Export
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
