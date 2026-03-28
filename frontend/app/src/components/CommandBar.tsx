import type { TopToolbarActionId } from "../types/workspace";

export type ToolbarAction = TopToolbarActionId;

export default function CommandBar() {
  return (
    <header className="command-bar">
      <div className="command-brand">IndustryPath</div>
    </header>
  );
}