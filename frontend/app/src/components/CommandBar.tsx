import { useEffect, useRef, useState } from "react";
import type { TopToolbarActionId } from "../types/workspace";

export type ToolbarAction = TopToolbarActionId;

type CommandBarProps = {
  activeAction: ToolbarAction;
  loadingAction?: ToolbarAction | null;
  disabledActions?: Partial<Record<ToolbarAction, boolean>>;
  onAction: (action: ToolbarAction) => void;
};

const ACTIONS: Array<{ id: ToolbarAction; label: string; primary?: boolean }> = [
  { id: "upload_documents", label: "Upload Documents" },
  { id: "parse_plant_model", label: "Parse Plant Model" },
  { id: "detect_control_loops", label: "Detect Control Loops" },
  { id: "generate_logic", label: "Generate Logic" },
  { id: "generate_io_mapping", label: "Generate IO Mapping" },
  { id: "deploy_runtime", label: "Deploy Runtime" },
  { id: "start_monitoring", label: "Start Monitoring" },
  { id: "analyze_fault", label: "Analyze Fault" },
  { id: "replay_event", label: "Replay Event" },
];

export default function CommandBar({
  activeAction,
  loadingAction,
  disabledActions = {},
  onAction,
}: CommandBarProps) {
  const [isMenuOpen, setIsMenuOpen] = useState<boolean>(false);
  const menuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handlePointerDown = (event: MouseEvent): void => {
      if (!menuRef.current) {
        return;
      }

      if (!menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };

    const handleEscape = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        setIsMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleEscape);
    };
  }, []);

  const handleActionClick = (action: ToolbarAction): void => {
    onAction(action);
    setIsMenuOpen(false);
  };

  return (
    <header className="command-bar">
      <div className="command-brand">IndustryPath</div>

      <div className="command-menu" ref={menuRef}>
        <button
          aria-expanded={isMenuOpen}
          aria-haspopup="menu"
          aria-label="Open command menu"
          className="command-btn command-menu-trigger"
          onClick={() => setIsMenuOpen((current) => !current)}
          type="button"
        >
          <span className="command-menu-icon" aria-hidden="true">
            ☰
          </span>
        </button>

        {isMenuOpen ? (
          <div className="command-dropdown" role="menu" aria-label="Top bar actions">
            {ACTIONS.map((action) => {
              const isActive = activeAction === action.id;
              const isLoading = loadingAction === action.id;
              const isDisabled = Boolean(disabledActions[action.id]);
              const classes = ["command-btn", "command-menu-item", action.primary ? "primary" : "", isActive ? "active" : ""]
                .filter(Boolean)
                .join(" ");

              return (
                <button key={action.id} className={classes} disabled={isLoading || isDisabled} onClick={() => handleActionClick(action.id)} role="menuitem" type="button">
                  {isLoading ? <span className="btn-loader" aria-hidden="true" /> : null}
                  {action.label}
                </button>
              );
            })}
          </div>
        ) : null}
      </div>
    </header>
  );
}