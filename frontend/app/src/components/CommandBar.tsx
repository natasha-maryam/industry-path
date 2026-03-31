import type { ReactNode } from "react";
import type { TopToolbarActionId } from "../types/workspace";

export type ToolbarAction = TopToolbarActionId;

type CommandBarProps = {
  rightActions?: ReactNode;
};

export default function CommandBar({ rightActions = null }: CommandBarProps) {
  return (
    <header className="command-bar">
      <div className="command-brand">IndustryPath</div>
      {rightActions ? <div style={{ marginLeft: "auto", display: "flex", gap: "0.35rem" }}>{rightActions}</div> : null}
    </header>
  );
}