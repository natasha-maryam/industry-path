import { Suspense, lazy } from "react";
import type {
  ControlLoopRecord,
  FaultAnalysisResult,
  IOMappingIssue,
  IOMappingTableRow,
  RuntimeEvaluationCycle,
  SimulationTraceIssue,
  SimulationTracePoint,
  PIDReconcileSummary,
} from "../services/api";
import type { Equipment } from "./rightTabs/types";
import type { RightPanelTabId } from "../types/workspace";

const RightDetailsTab = lazy(() => import("./rightTabs/RightDetailsTab"));
const RightSignalsTab = lazy(() => import("./rightTabs/RightSignalsTab"));
const RightTraceTab = lazy(() => import("./rightTabs/RightTraceTab"));
const RightReplayTab = lazy(() => import("./rightTabs/RightReplayTab"));
const RightIOMappingTab = lazy(() => import("./rightTabs/RightIOMappingTab"));
const RightControlLoopsTab = lazy(() => import("./rightTabs/RightControlLoopsTab"));
const RightDiagnosticsTab = lazy(() => import("./rightTabs/RightDiagnosticsTab"));
const RightVersionsTab = lazy(() => import("./rightTabs/RightVersionsTab"));
const RightPIDChangesTab = lazy(() => import("./rightTabs/RightPIDChangesTab"));

export type RightTab = RightPanelTabId;

type DetailsPanelProps = {
  activeTab: RightTab;
  replayPoint: number;
  selectedReplayTag?: string;
  selectedEquipment: Equipment;
  selectedNodeId?: string;
  tracePath: string[];
  ioMappingRows?: IOMappingTableRow[];
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
  controlLoopsLoading?: boolean;
  controlLoopsError?: string | null;
  selectedControlLoopTag?: string | null;
  onSelectedReplayTagChange?: (tag: string) => void;
  onSelectIOMappingTag?: (tag: string) => void;
  onSelectControlLoop?: (loop: ControlLoopRecord) => void;
  onDetectControlLoops?: () => void;
  onViewControlLoop?: (loop: ControlLoopRecord) => void;
  onEditControlLoopStrategy?: (loop: ControlLoopRecord) => void;
  onGenerateControlLoopLogic?: (loop: ControlLoopRecord) => void;
  onTraceControlLoop?: (loop: ControlLoopRecord) => void;
  onSimulateControlLoop?: (loop: ControlLoopRecord) => void;
  onReplayPointChange?: (point: number) => void;
  onOpenVersionsWorkspace?: () => void;
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
  onTabChange: (tab: RightTab) => void;
};

const TABS: RightTab[] = ["Details", "Signals", "Trace", "Replay", "IO Mapping", "Control Loops", "Diagnostics", "Versions", "P&ID Changes"];

export default function DetailsPanel({
  activeTab,
  replayPoint,
  selectedReplayTag = "",
  selectedEquipment,
  selectedNodeId = "",
  tracePath,
  ioMappingRows = [],
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
  controlLoopsLoading = false,
  controlLoopsError = null,
  selectedControlLoopTag = null,
  onSelectedReplayTagChange,
  onSelectIOMappingTag,
  onSelectControlLoop,
  onDetectControlLoops,
  onViewControlLoop,
  onEditControlLoopStrategy,
  onGenerateControlLoopLogic,
  onTraceControlLoop,
  onSimulateControlLoop,
  onReplayPointChange,
  onOpenVersionsWorkspace,
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
  onTabChange,
}: DetailsPanelProps) {
  const renderActiveTab = () => {
    if (activeTab === "Details") {
      return <RightDetailsTab selectedEquipment={selectedEquipment} />;
    }
    if (activeTab === "Signals") {
      return <RightSignalsTab selectedEquipment={selectedEquipment} runtimeTelemetryTags={runtimeTelemetryTags} forcedTags={forcedTagNames} />;
    }
    if (activeTab === "Trace") {
      return <RightTraceTab tracePath={tracePath} />;
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
          loading={controlLoopsLoading}
          error={controlLoopsError}
          selectedLoopTag={selectedControlLoopTag}
          onSelectLoop={(loop) => onSelectControlLoop?.(loop)}
          onDetectLoops={onDetectControlLoops}
          onViewLoop={(loop) => onViewControlLoop?.(loop)}
          onEditStrategy={(loop) => onEditControlLoopStrategy?.(loop)}
          onGenerateLogic={(loop) => onGenerateControlLoopLogic?.(loop)}
          onTraceLoop={(loop) => onTraceControlLoop?.(loop)}
          onSimulate={(loop) => onSimulateControlLoop?.(loop)}
        />
      );
    }
    if (activeTab === "Versions") {
      return <RightVersionsTab onOpenVersionsWorkspace={onOpenVersionsWorkspace} />;
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
    return (
      <RightDiagnosticsTab
        diagnostics={runtimeDiagnostics}
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
    <div>
      <h3 className="panel-title">Engineering Panel</h3>

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
