import { useEffect, useRef, useState } from "react";

export type ToolbarAction =
  | "upload"
  | "parse"
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
  { id: "generate_st", label: "Generate ST" },
  { id: "verify_st", label: "Verify ST" },
  { id: "io_mapping", label: "Generate IO Mapping" },
  { id: "deploy", label: "Deploy Runtime" },
  { id: "versions", label: "Versions" },
  { id: "export_logic", label: "Export Logic" },
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