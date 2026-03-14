import { Suspense, lazy } from "react";
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
  selectedEquipment: Equipment;
  tracePath: string[];
  onTabChange: (tab: RightTab) => void;
};

const TABS: RightTab[] = ["Details", "Signals", "Trace", "Replay", "IO Mapping", "Versions", "Diagnostics"];

export default function DetailsPanel({
  activeTab,
  replayPoint,
  selectedEquipment,
  tracePath,
  onTabChange,
}: DetailsPanelProps) {
  const renderActiveTab = () => {
    if (activeTab === "Details") {
      return <RightDetailsTab selectedEquipment={selectedEquipment} />;
    }
    if (activeTab === "Signals") {
      return <RightSignalsTab selectedEquipment={selectedEquipment} />;
    }
    if (activeTab === "Trace") {
      return <RightTraceTab tracePath={tracePath} />;
    }
    if (activeTab === "Replay") {
      return <RightReplayTab replayPoint={replayPoint} />;
    }
    if (activeTab === "IO Mapping") {
      return <RightIOMappingTab selectedEquipment={selectedEquipment} />;
    }
    if (activeTab === "Versions") {
      return <RightVersionsTab />;
    }
    return <RightDiagnosticsTab />;
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
