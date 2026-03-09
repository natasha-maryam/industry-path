export type ToolbarAction =
  | "upload"
  | "parse"
  | "generate"
  | "simulate"
  | "deploy"
  | "monitor"
  | "replay";

type CommandBarProps = {
  activeAction: ToolbarAction;
  replayMode: boolean;
  showLogic: boolean;
  loadingAction?: ToolbarAction | null;
  onAction: (action: ToolbarAction) => void;
  onToggleLogic: () => void;
};

const ACTIONS: Array<{ id: ToolbarAction; label: string; primary?: boolean }> = [
  { id: "upload", label: "Upload Documents" },
  { id: "parse", label: "Parse System" },
  { id: "generate", label: "Generate Control Logic" },
  { id: "simulate", label: "Run Simulation", primary: true },
  { id: "deploy", label: "Deploy PLC" },
  { id: "monitor", label: "Start Monitoring" },
  { id: "replay", label: "Replay" },
];

export default function CommandBar({
  activeAction,
  replayMode,
  showLogic,
  loadingAction,
  onAction,
  onToggleLogic,
}: CommandBarProps) {
  return (
    <header className="command-bar">
      <div className="command-brand">IndustryPath</div>

      <div className="command-actions">
        {ACTIONS.map((action) => {
          const isReplayActive = action.id === "replay" && replayMode;
          const isActive = activeAction === action.id || isReplayActive;
          const isLoading = loadingAction === action.id;
          const classes = ["command-btn", action.primary ? "primary" : "", isActive ? "active" : ""]
            .filter(Boolean)
            .join(" ");

          return (
            <button key={action.id} className={classes} disabled={isLoading} onClick={() => onAction(action.id)} type="button">
              {isLoading ? <span className="btn-loader" aria-hidden="true" /> : null}
              {action.label}
            </button>
          );
        })}

        <button className={`command-btn ${showLogic ? "active" : ""}`} onClick={onToggleLogic} type="button">
          View Logic
        </button>
      </div>
    </header>
  );
}