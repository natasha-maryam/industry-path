import { Suspense, lazy } from "react";
import type { IOMappingIssue, IOMappingTableRow, RuntimeEvaluationCycle, SimulationTraceIssue, SimulationTracePoint } from "../services/api";
import type { Equipment } from "./rightTabs/types";

const RightDetailsTab = lazy(() => import("./rightTabs/RightDetailsTab"));
const RightSignalsTab = lazy(() => import("./rightTabs/RightSignalsTab"));
const RightTraceTab = lazy(() => import("./rightTabs/RightTraceTab"));
const RightReplayTab = lazy(() => import("./rightTabs/RightReplayTab"));
const RightIOMappingTab = lazy(() => import("./rightTabs/RightIOMappingTab"));
const RightVersionsTab = lazy(() => import("./rightTabs/RightVersionsTab"));
const RightDiagnosticsTab = lazy(() => import("./rightTabs/RightDiagnosticsTab"));

export type RightTab = "Details" | "Signals" | "Trace" | "Replay" | "IO Mapping" | "Versions" | "Diagnostics";

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
  replayTrace?: SimulationTracePoint[];
  replayIssues?: SimulationTraceIssue[];
  onSelectedReplayTagChange?: (tag: string) => void;
  onSelectIOMappingTag?: (tag: string) => void;
  onReplayPointChange?: (point: number) => void;
  onTabChange: (tab: RightTab) => void;
};

const TABS: RightTab[] = ["Details", "Signals", "Trace", "Replay", "IO Mapping", "Versions", "Diagnostics"];

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
  replayTrace = [],
  replayIssues = [],
  onSelectedReplayTagChange,
  onSelectIOMappingTag,
  onReplayPointChange,
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
    if (activeTab === "Versions") {
      return <RightVersionsTab />;
    }
    return <RightDiagnosticsTab diagnostics={runtimeDiagnostics} simulationIssues={replayIssues} />;
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
