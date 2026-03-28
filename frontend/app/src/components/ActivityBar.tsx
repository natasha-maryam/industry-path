import { ChevronRight, FolderKanban, Settings } from "lucide-react";

type ActivityMode = "projects" | "settings";

type ActivityBarProps = {
  activeActivity: ActivityMode;
  onSelectActivity: (activity: ActivityMode) => void;
  isSidebarCollapsed?: boolean;
  onOpenSidebar?: () => void;
};

const ACTIVITY_ITEMS: Array<{ id: ActivityMode; label: string; Icon: typeof FolderKanban }> = [
  { id: "projects", label: "Projects", Icon: FolderKanban },
  { id: "settings", label: "Settings", Icon: Settings },
];

export default function ActivityBar({
  activeActivity,
  onSelectActivity,
  isSidebarCollapsed = false,
  onOpenSidebar,
}: ActivityBarProps) {
  return (
    <div className="activity-bar" role="navigation" aria-label="Activity">
      <div className="activity-bar-actions">
        {ACTIVITY_ITEMS.map(({ id, label, Icon }) => (
          <button
            key={id}
            className={`activity-bar-item ${activeActivity === id ? "active" : ""}`}
            type="button"
            onClick={() => onSelectActivity(id)}
            title={label}
            aria-label={label}
          >
            <Icon size={14} />
            <span>{label}</span>
          </button>
        ))}
      </div>

      {isSidebarCollapsed && onOpenSidebar ? (
        <button className="activity-bar-item activity-bar-open" type="button" onClick={onOpenSidebar} title="Open" aria-label="Open sidebar">
          <ChevronRight size={14} />
          <span>Open</span>
        </button>
      ) : null}
    </div>
  );
}
