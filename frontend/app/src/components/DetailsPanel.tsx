import { Suspense, lazy } from "react";
import type {
  ControlLoopRecord,
  EngineeringTableResponseRow,
  FaultAnalysisResult,
  IOMappingIssue,
  IOMappingTableRow,
  RuntimeEvaluationCycle,
  SimulationTraceIssue,
  SimulationTracePoint,
  PIDReconcileSummary,
} from "../services/api";
import type { SystemContext, SystemImpact } from "../intelligence/systemContext";
import type { Equipment } from "./rightTabs/types";
import type { RightPanelTabId } from "../types/workspace";

const RightDetailsTab = lazy(() => import("./rightTabs/RightDetailsTab"));
const RightSignalsTab = lazy(() => import("./rightTabs/RightSignalsTab"));
const RightTraceTab = lazy(() => import("./rightTabs/RightTraceTab"));
const RightReplayTab = lazy(() => import("./rightTabs/RightReplayTab"));
const RightIOMappingTab = lazy(() => import("./rightTabs/RightIOMappingTab"));
const RightControlLoopsTab = lazy(() => import("./rightTabs/RightControlLoopsTab"));
const RightDiagnosticsTab = lazy(() => import("./rightTabs/RightDiagnosticsTab"));
const RightPIDChangesTab = lazy(() => import("./rightTabs/RightPIDChangesTab"));
const RightWorkspaceToolsTab = lazy(() => import("./rightTabs/RightWorkspaceToolsTab"));

export type RightTab = RightPanelTabId;

type DetailsPanelProps = {
  activeTab: RightTab;
  replayPoint: number;
  selectedReplayTag?: string;
  selectedEquipment: Equipment;
  systemContext?: SystemContext | null;
  behaviorExplanation?: string;
  impactSummary?: SystemImpact | null;
  systemContextLoading?: boolean;
  systemContextError?: string | null;
  whyFocusToken?: number;
  selectedNodeId?: string;
  tracePath: string[];
  whyTraceTag?: string | null;
  ioMappingRows?: IOMappingTableRow[];
  controlLoopIOMappingRows?: IOMappingTableRow[];
  ioMappingIssues?: IOMappingIssue[];
  selectedIOMappingTag?: string | null;
  runtimeTelemetryTags?: Record<string, unknown>;
  forcedTagNames?: string[];
  runtimeDiagnostics?: RuntimeEvaluationCycle | null;
  faultAnalysis?: FaultAnalysisResult | null;
  faultAnalysisTag?: string | null;
  faultAnalysisInputMessage?: string | null;
  faultAnalysisLoading?: boolean;
  faultAnalysisError?: string | null;
  replayTrace?: SimulationTracePoint[];
  replayIssues?: SimulationTraceIssue[];
  controlLoops?: ControlLoopRecord[];
  engineeringRowsForLoops?: EngineeringTableResponseRow[];
  controlLoopsLoading?: boolean;
  controlLoopsError?: string | null;
  selectedControlLoopTag?: string | null;
  onSelectedReplayTagChange?: (tag: string) => void;
  onSelectIOMappingTag?: (tag: string) => void;
  onSelectControlLoop?: (loop: ControlLoopRecord) => void;
  onDetectControlLoops?: () => void;
  onViewControlLoop?: (loop: ControlLoopRecord) => void;
  onGenerateControlLoopLogic?: (loop: ControlLoopRecord) => void;
  onTraceControlLoop?: (loop: ControlLoopRecord) => void;
  onNavigateControlLoopToST?: (loop: ControlLoopRecord) => void;
  onNavigateControlLoopToIO?: (loop: ControlLoopRecord) => void;
  onReplayPointChange?: (point: number) => void;
  onCloseWhyTrace?: () => void;
  pidChanges?: PIDReconcileSummary | null;
  pidChangesLoading?: boolean;
  pidChangesError?: string | null;
  pidApplying?: boolean;
  pidSnapshotCreating?: boolean;
  pidAcceptedConflicts?: boolean;
  onPIDAcceptChanges?: () => void;
  onPIDReviewConflicts?: () => void;
  onPIDApplyUpdate?: () => void;
  onPIDCreateSnapshot?: () => void;
  projectId?: string;
  engineeringRows?: EngineeringTableResponseRow[];
  engineeringRowsSource?: string;
  engineeringFilteredRowsCount?: number;
  engineeringRowsLoading?: boolean;
  productionAuthToken?: string;
  onProductionAuthTokenChange?: (token: string) => void;
  onWorkspaceRowsUpdate?: (rows: EngineeringTableResponseRow[]) => void;
  onWorkspaceSelectTag?: (tag: string) => void;
  onWorkspaceTracePath?: (path: string[]) => void;
  onTraceStepSelect?: (tag: string) => void;
  onTabChange: (tab: RightTab) => void;
};

const TABS: RightTab[] = ["Details", "Why", "Signals", "Trace", "Replay", "IO Mapping", "Control Loops", "Diagnostics"];

export default function DetailsPanel({
  activeTab,
  replayPoint,
  selectedReplayTag = "",
  selectedEquipment,
  systemContext = null,
  behaviorExplanation = "",
  impactSummary = null,
  systemContextLoading = false,
  systemContextError = null,
  whyFocusToken = 0,
  selectedNodeId = "",
  tracePath,
  whyTraceTag = null,
  ioMappingRows = [],
  controlLoopIOMappingRows = [],
  ioMappingIssues = [],
  selectedIOMappingTag = null,
  runtimeTelemetryTags = {},
  forcedTagNames = [],
  runtimeDiagnostics = null,
  faultAnalysis = null,
  faultAnalysisTag = null,
  faultAnalysisInputMessage = null,
  faultAnalysisLoading = false,
  faultAnalysisError = null,
  replayTrace = [],
  replayIssues = [],
  controlLoops = [],
  engineeringRowsForLoops = [],
  controlLoopsLoading = false,
  controlLoopsError = null,
  selectedControlLoopTag = null,
  onSelectedReplayTagChange,
  onSelectIOMappingTag,
  onSelectControlLoop,
  onDetectControlLoops,
  onViewControlLoop,
  onGenerateControlLoopLogic,
  onTraceControlLoop,
  onNavigateControlLoopToST,
  onNavigateControlLoopToIO,
  onReplayPointChange,
  onCloseWhyTrace,
  pidChanges = null,
  pidChangesLoading = false,
  pidChangesError = null,
  pidApplying = false,
  pidSnapshotCreating = false,
  pidAcceptedConflicts = false,
  onPIDAcceptChanges,
  onPIDReviewConflicts,
  onPIDApplyUpdate,
  onPIDCreateSnapshot,
  projectId,
  engineeringRows = [],
  engineeringRowsSource = "workspace_rows",
  engineeringFilteredRowsCount = 0,
  engineeringRowsLoading = false,
  productionAuthToken = "",
  onProductionAuthTokenChange,
  onWorkspaceRowsUpdate,
  onWorkspaceSelectTag,
  onWorkspaceTracePath,
  onTraceStepSelect,
  onTabChange,
}: DetailsPanelProps) {
  const renderActiveTab = () => {
    if (activeTab === "Details" || activeTab === "Why") {
      return (
        <RightDetailsTab
          selectedEquipment={selectedEquipment}
          systemContext={systemContext}
          behaviorExplanation={behaviorExplanation}
          whyFocusToken={whyFocusToken}
        />
      );
    }
    if (activeTab === "Signals") {
      return <RightSignalsTab selectedEquipment={selectedEquipment} runtimeTelemetryTags={runtimeTelemetryTags} forcedTags={forcedTagNames} />;
    }
    if (activeTab === "Trace") {
      return (
        <RightTraceTab
          tracePath={tracePath}
          systemContext={systemContext}
          whyTraceTag={whyTraceTag}
          onCloseWhyTrace={onCloseWhyTrace}
          onSelectTraceTag={onTraceStepSelect}
        />
      );
    }
    if (activeTab === "Replay") {
      return (
        <RightReplayTab
          replayPoint={replayPoint}
          selectedTag={selectedReplayTag}
          replayTrace={replayTrace}
          replayIssues={replayIssues}
          onSelectedTagChange={onSelectedReplayTagChange}
          onReplayPointChange={onReplayPointChange}
        />
      );
    }
    if (activeTab === "IO Mapping") {
      return (
        <RightIOMappingTab
          selectedNodeId={selectedNodeId}
          mappingRows={ioMappingRows}
          mappingIssues={ioMappingIssues}
          selectedTag={selectedIOMappingTag}
          onSelectTag={onSelectIOMappingTag}
        />
      );
    }
    if (activeTab === "Control Loops") {
      return (
        <RightControlLoopsTab
          loops={controlLoops}
          ioMappingRows={controlLoopIOMappingRows}
          engineeringRows={engineeringRowsForLoops}
          replayTrace={replayTrace}
          loading={controlLoopsLoading}
          error={controlLoopsError}
          selectedLoopTag={selectedControlLoopTag}
          onSelectLoop={(loop) => onSelectControlLoop?.(loop)}
          onDetectLoops={onDetectControlLoops}
          onViewLoop={(loop) => onViewControlLoop?.(loop)}
          onGenerateLogic={(loop) => onGenerateControlLoopLogic?.(loop)}
          onTraceLoop={(loop) => onTraceControlLoop?.(loop)}
          onNavigateToST={(loop) => onNavigateControlLoopToST?.(loop)}
          onNavigateToIO={(loop) => onNavigateControlLoopToIO?.(loop)}
        />
      );
    }
    if (activeTab === "P&ID Changes") {
      return (
        <RightPIDChangesTab
          changes={pidChanges}
          loading={pidChangesLoading}
          error={pidChangesError}
          applying={pidApplying}
          creatingSnapshot={pidSnapshotCreating}
          acceptedConflicts={pidAcceptedConflicts}
          onAcceptChanges={() => onPIDAcceptChanges?.()}
          onReviewConflicts={() => onPIDReviewConflicts?.()}
          onApplyUpdate={() => onPIDApplyUpdate?.()}
          onCreateSnapshot={() => onPIDCreateSnapshot?.()}
        />
      );
    }
    if (activeTab === "Workspace") {
      return (
        <RightWorkspaceToolsTab
          projectId={projectId}
          currentRows={engineeringRows}
          rowsSource={engineeringRowsSource}
          filteredRowsCount={engineeringFilteredRowsCount}
          rowsLoading={engineeringRowsLoading}
          authToken={productionAuthToken}
          onAuthTokenChange={(token) => onProductionAuthTokenChange?.(token)}
          onRowsUpdate={onWorkspaceRowsUpdate}
          onSelectTag={onWorkspaceSelectTag}
          onTracePath={onWorkspaceTracePath}
        />
      );
    }
    return (
      <RightDiagnosticsTab
        diagnostics={runtimeDiagnostics}
        systemContext={systemContext}
        impactSummary={impactSummary}
        simulationIssues={replayIssues}
        faultAnalysis={faultAnalysis}
        analyzedTag={faultAnalysisTag}
        inputMessage={faultAnalysisInputMessage}
        loading={faultAnalysisLoading}
        error={faultAnalysisError}
      />
    );
  };

  return (
    <div className="engineering-panel">
      <h3 className="panel-title">Engineering Panel</h3>

      {systemContextLoading ? <div className="monitor-frame">Loading engineering intelligence...</div> : null}
      {!systemContextLoading && systemContextError ? <div className="monitor-frame">{systemContextError}</div> : null}

      <div className="right-tabs">
        {TABS.map((tab) => (
          <button
            key={tab}
            className={`right-tab ${activeTab === tab ? "active" : ""}`}
            onClick={() => onTabChange(tab)}
            type="button"
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="right-content">
        <Suspense fallback={<div className="monitor-frame">Loading tab content...</div>}>{renderActiveTab()}</Suspense>
      </div>
    </div>
  );
}
