export type ToolbarAction =
  | "upload"
  | "parse"
  | "generate"
  | "generate_st"
  | "io_mapping"
  | "verify_st"
  | "versions"
  | "export_logic"
  | "simulate"
  | "deploy";

type CommandBarProps = {
  activeAction: ToolbarAction;
  loadingAction?: ToolbarAction | null;
  disabledActions?: Partial<Record<ToolbarAction, boolean>>;
  onAction: (action: ToolbarAction) => void;
};

const ACTIONS: Array<{ id: ToolbarAction; label: string; primary?: boolean }> = [
  { id: "upload", label: "Upload Documents" },
  { id: "parse", label: "Parse System" },
  { id: "generate", label: "Generate Control Logic" },
  { id: "generate_st", label: "Generate ST" },
  { id: "verify_st", label: "Verify ST" },
  { id: "io_mapping", label: "Generate IO Mapping" },
  { id: "deploy", label: "Deploy PLC" },
  { id: "simulate", label: "Run Simulation", primary: true },
  { id: "versions", label: "Versions" },
  { id: "export_logic", label: "Export Logic" },
];

export default function CommandBar({
  activeAction,
  loadingAction,
  disabledActions = {},
  onAction,
}: CommandBarProps) {
  return (
    <header className="command-bar">
      <div className="command-brand">IndustryPath</div>

      <div className="command-actions">
        {ACTIONS.map((action) => {
          const isActive = activeAction === action.id;
          const isLoading = loadingAction === action.id;
          const isDisabled = Boolean(disabledActions[action.id]);
          const classes = ["command-btn", action.primary ? "primary" : "", isActive ? "active" : ""]
            .filter(Boolean)
            .join(" ");

          return (
            <button key={action.id} className={classes} disabled={isLoading || isDisabled} onClick={() => onAction(action.id)} type="button">
              {isLoading ? <span className="btn-loader" aria-hidden="true" /> : null}
              {action.label}
            </button>
          );
        })}
      </div>
    </header>
  );
}