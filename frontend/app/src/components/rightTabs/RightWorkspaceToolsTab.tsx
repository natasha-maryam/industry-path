import AdvancedSystemPanel from "../AdvancedSystemPanel";
import AuditPanel from "../AuditPanel";
import AuthPanel from "../AuthPanel";
import SystemControlLayer from "../SystemControlLayer";
import SystemStatusPanel from "../SystemStatusPanel";
import TagDatabasePanel from "../TagDatabasePanel";
import ViewsPanel from "../ViewsPanel";
import type { EngineeringTableResponseRow } from "../../services/api";

type RightWorkspaceToolsTabProps = {
  projectId?: string;
  currentRows: EngineeringTableResponseRow[];
  rowsSource?: string;
  filteredRowsCount?: number;
  rowsLoading?: boolean;
  authToken: string;
  onAuthTokenChange: (token: string) => void;
  onRowsUpdate?: (rows: EngineeringTableResponseRow[]) => void;
  onSelectTag?: (tag: string) => void;
  onTracePath?: (path: string[]) => void;
};

export default function RightWorkspaceToolsTab({
  projectId,
  currentRows,
  rowsSource = "workspace_rows",
  filteredRowsCount = 0,
  rowsLoading = false,
  authToken,
  onAuthTokenChange,
  onRowsUpdate,
  onSelectTag,
  onTracePath,
}: RightWorkspaceToolsTabProps) {
  return (
    <section className="space-y-2">
      <AuthPanel onTokenChange={onAuthTokenChange} />
      <SystemStatusPanel authToken={authToken} />
      <AuditPanel authToken={authToken} />
      <TagDatabasePanel projectId={projectId} />
      <ViewsPanel projectId={projectId} currentRows={currentRows} rowsSource={rowsSource} filteredRowsCount={filteredRowsCount} rowsLoading={rowsLoading} />
      <AdvancedSystemPanel projectId={projectId} onSelectTag={onSelectTag} onTracePath={onTracePath} />
      <SystemControlLayer onRowsUpdate={onRowsUpdate} />
    </section>
  );
}
