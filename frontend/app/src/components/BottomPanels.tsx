import CodeExplorerPanel, { type GeneratedLogicFile, type STDiagnosticMarker, type STJumpLocation } from "./CodeExplorerPanel";
import RuntimeValidationPanel, { type RuntimeValidationPanelData } from "./RuntimeValidationPanel";
import SimulationValidationPanel, { type SimulationValidationPanelData } from "./SimulationValidationPanel";
import STVerificationPanel, { type STVerificationIssueItem } from "./STVerificationPanel";
import IOMappingTablePanel from "./IOMappingTablePanel";
import VersionsWorkspace from "./versioning/VersionsWorkspace";
import LogicDiffViewer from "./versioning/LogicDiffViewer";
import type {
  IOMappingSummaryByType,
  IOMappingTableRow,
  RuntimeInputCatalogItem,
  RuntimeSignalType,
  STWorkspaceVerificationResponse,
} from "../services/api";
import type { VersionDiffResponse, VersionRecord } from "../types/versioning";

type BottomView = "simulation" | "monitoring" | "logic";
type CodePanelMode = "control_logic" | "generated_st" | "verification" | "version_diff";
type MonitoringPanelMode = "io_mapping" | "runtime" | "versions";

type VersioningSettings = {
  enableAutoVersioning: boolean;
  autoSnapshotOnDeploy: boolean;
  enableDatabaseVersioning: boolean;
  maxSnapshotsStored: number;
  snapshotRetentionDays: number;
  gitRepositoryLocation: string;
};

type BottomPanelsProps = {
  activeView: BottomView;
  codePanelMode: CodePanelMode;
  monitoringPanelMode: MonitoringPanelMode;
  controlLogicCode: string;
  generatedSTCode: string;
  generatedSTFiles?: GeneratedLogicFile[];
  selectedSTFilePath?: string | null;
  onSelectSTFile?: (path: string) => void;
  stDiagnosticsByFile?: Record<string, STDiagnosticMarker[]>;
  stJumpLocation?: STJumpLocation | null;
  logicWarnings?: string[];
  logicValidationIssues?: string[];
  stVerificationData?: STWorkspaceVerificationResponse | null;
  isVerifyingST?: boolean;
  stVerificationFailedMessage?: string | null;
  onSelectVerificationIssue?: (issue: STVerificationIssueItem) => void;
  ioMappingRows?: IOMappingTableRow[];
  selectedIOMappingTag?: string | null;
  onSelectIOMappingTag?: (tag: string) => void;
  ioMappingSummary?: IOMappingSummaryByType | null;
  isGeneratingIOMapping?: boolean;
  ioMappingFailedMessage?: string | null;
  runtimeValidationData?: RuntimeValidationPanelData | null;
  runtimeLoading?: boolean;
  runtimeFailedMessage?: string | null;
  runtimeActionLoading?: boolean;
  simulationValidationData?: SimulationValidationPanelData | null;
  simulationFailedMessage?: string | null;
  onRetryIOMapping?: () => void;
  onGenerateIOMapping?: () => void;
  onAutoAssignIOMappingChannels?: () => void;
  onExportIOMappingCsv?: () => void;
  onValidateIOMapping?: () => void;
  onRetrySTVerification?: () => void;
  onRetryRuntime?: () => void;
  onRuntimeStart?: () => void;
  onRuntimeStop?: () => void;
  runtimeForceableInputs?: RuntimeInputCatalogItem[];
  forcedTagNames?: string[];
  onRuntimeApplyForce?: (payload: { tag: string; value: unknown; type: RuntimeSignalType }) => Promise<void>;
  onRuntimeClearForce?: (tag: string) => Promise<void>;
  onRuntimeRefreshForceState?: () => Promise<void>;
  onRuntimeRunEvaluationCycle?: () => Promise<void>;
  onRetrySimulation?: () => void;
  versions?: VersionRecord[];
  selectedVersion?: VersionRecord | null;
  selectedVersionTags?: string[];
  versionDiff?: VersionDiffResponse | null;
  versionsLoading?: boolean;
  versionsError?: string | null;
  versionBusyAction?: "snapshot" | "rollback" | "compare" | "export" | null;
  versionSettings?: VersioningSettings;
  onVersionSelect?: (version: VersionRecord) => void;
  onVersionToggleCompareSelection?: (versionTag: string) => void;
  onVersionCreateSnapshot?: () => void;
  onVersionLoadSnapshot?: (version: VersionRecord) => void;
  onVersionRollback?: (version: VersionRecord) => void;
  onVersionCompare?: () => void;
  onVersionExport?: (version: VersionRecord) => void;
  onVersionSettingsChange?: (settings: VersioningSettings) => void;
  showControlLogic: boolean;
  isGeneratingST?: boolean;
  isGenerating?: boolean;
  onViewChange: (view: BottomView) => void;
};

export default function BottomPanels({
  activeView,
  codePanelMode,
  monitoringPanelMode,
  controlLogicCode,
  generatedSTCode,
  generatedSTFiles = [],
  selectedSTFilePath = null,
  onSelectSTFile,
  stDiagnosticsByFile = {},
  stJumpLocation = null,
  logicWarnings = [],
  logicValidationIssues = [],
  stVerificationData = null,
  isVerifyingST = false,
  stVerificationFailedMessage = null,
  onSelectVerificationIssue,
  ioMappingRows = [],
  selectedIOMappingTag = null,
  onSelectIOMappingTag,
  ioMappingSummary = null,
  isGeneratingIOMapping = false,
  ioMappingFailedMessage = null,
  runtimeValidationData = null,
  runtimeLoading = false,
  runtimeFailedMessage = null,
  runtimeActionLoading = false,
  simulationValidationData = null,
  simulationFailedMessage = null,
  onRetryIOMapping,
  onGenerateIOMapping,
  onAutoAssignIOMappingChannels,
  onExportIOMappingCsv,
  onValidateIOMapping,
  onRetrySTVerification,
  onRetryRuntime,
  onRuntimeStart,
  onRuntimeStop,
  runtimeForceableInputs = [],
  forcedTagNames = [],
  onRuntimeApplyForce,
  onRuntimeClearForce,
  onRuntimeRefreshForceState,
  onRuntimeRunEvaluationCycle,
  onRetrySimulation,
  versions = [],
  selectedVersion = null,
  selectedVersionTags = [],
  versionDiff = null,
  versionsLoading = false,
  versionsError = null,
  versionBusyAction = null,
  versionSettings = {
    enableAutoVersioning: true,
    autoSnapshotOnDeploy: true,
    enableDatabaseVersioning: true,
    maxSnapshotsStored: 100,
    snapshotRetentionDays: 90,
    gitRepositoryLocation: "backend-controlled",
  },
  onVersionSelect,
  onVersionToggleCompareSelection,
  onVersionCreateSnapshot,
  onVersionLoadSnapshot,
  onVersionRollback,
  onVersionCompare,
  onVersionExport,
  onVersionSettingsChange,
  showControlLogic,
  isGeneratingST = false,
  isGenerating = false,
  onViewChange,
}: BottomPanelsProps) {
  return (
    <section className="bottom-shell">
      <nav className="bottom-nav">
        <button className={activeView === "simulation" ? "active" : ""} onClick={() => onViewChange("simulation")} type="button">
          Simulation Panel
        </button>
        <button className={activeView === "monitoring" ? "active" : ""} onClick={() => onViewChange("monitoring")} type="button">
          Monitoring Dashboard
        </button>
        <button className={activeView === "logic" ? "active" : ""} onClick={() => onViewChange("logic")} type="button">
          Code Panel
        </button>
      </nav>

      <div className="bottom-content">
        {activeView === "logic" && codePanelMode === "control_logic" ? (
          isGenerating ? (
            <div className="monitor-frame">Generating control logic, please wait...</div>
          ) : showControlLogic ? (
            <>
              <pre className="logic-box">{controlLogicCode}</pre>
              {logicValidationIssues.length > 0 ? (
                <div className="monitor-frame">
                  <pre className="monitor-json">{`ST validation issues:\n- ${logicValidationIssues.join("\n- ")}`}</pre>
                </div>
              ) : null}
              {logicWarnings.length > 0 ? (
                <div className="monitor-frame">
                  <pre className="monitor-json">{`Generation warnings:\n- ${logicWarnings.join("\n- ")}`}</pre>
                </div>
              ) : null}
            </>
          ) : (
            <div className="monitor-frame">No control logic artifact available yet. Run Generate ST first.</div>
          )
        ) : null}

        {activeView === "logic" && codePanelMode === "generated_st" ? (
          <CodeExplorerPanel
            files={generatedSTFiles}
            bundledCode={generatedSTCode}
            selectedFilePath={selectedSTFilePath}
            onSelectFile={onSelectSTFile}
            diagnosticsByFile={stDiagnosticsByFile}
            jumpToLocation={stJumpLocation}
            loading={isGeneratingST}
            requiredPreviousStep="Generate ST"
          />
        ) : null}

        {activeView === "logic" && codePanelMode === "verification" ? (
          <STVerificationPanel
            data={stVerificationData}
            loading={isVerifyingST}
            failedMessage={stVerificationFailedMessage}
            onRetry={onRetrySTVerification}
            onSelectIssue={onSelectVerificationIssue}
            requiredPreviousStep="ST Generation"
          />
        ) : null}

        {activeView === "logic" && codePanelMode === "version_diff" ? <LogicDiffViewer diff={versionDiff} loading={versionBusyAction === "compare"} /> : null}

        {activeView === "monitoring" && monitoringPanelMode === "io_mapping" ? (
          <>
            <div className="stat-grid">
              <article className="stat-card">
                <h4>AI Count</h4>
                <p className="value-mono">{ioMappingSummary?.AI ?? 0}</p>
              </article>
              <article className="stat-card">
                <h4>AO Count</h4>
                <p className="value-mono">{ioMappingSummary?.AO ?? 0}</p>
              </article>
              <article className="stat-card">
                <h4>DI Count</h4>
                <p className="value-mono">{ioMappingSummary?.DI ?? 0}</p>
              </article>
              <article className="stat-card">
                <h4>DO Count</h4>
                <p className="value-mono">{ioMappingSummary?.DO ?? 0}</p>
              </article>
            </div>
            <IOMappingTablePanel
              rows={ioMappingRows}
              selectedTag={selectedIOMappingTag}
              onSelectRow={onSelectIOMappingTag}
              loading={isGeneratingIOMapping}
              failedMessage={ioMappingFailedMessage}
              onRetry={onRetryIOMapping}
              onGenerateMapping={onGenerateIOMapping}
              onAutoAssignChannels={onAutoAssignIOMappingChannels}
              onExportCsv={onExportIOMappingCsv}
              onValidateMapping={onValidateIOMapping}
              forcedTags={forcedTagNames}
              requiredPreviousStep="Logic Completion + Plant Graph"
            />
          </>
        ) : null}

        {activeView === "monitoring" && monitoringPanelMode === "runtime" ? (
          <RuntimeValidationPanel
            data={runtimeValidationData}
            loading={runtimeLoading}
            actionLoading={runtimeActionLoading}
            failedMessage={runtimeFailedMessage}
            onDeploy={onRetryRuntime}
            onStart={onRuntimeStart}
            onStop={onRuntimeStop}
            forceableInputs={runtimeForceableInputs}
            onApplyInputForce={onRuntimeApplyForce}
            onClearInputForce={onRuntimeClearForce}
            onRefreshInputForceState={onRuntimeRefreshForceState}
            onRunEvaluationCycle={onRuntimeRunEvaluationCycle}
            requiredPreviousStep="IO Mapping"
          />
        ) : null}

        {activeView === "simulation" ? (
          <SimulationValidationPanel
            data={simulationValidationData}
            failedMessage={simulationFailedMessage}
            onRetry={onRetrySimulation}
            requiredPreviousStep="Runtime Check"
          />
        ) : null}

        {activeView === "monitoring" && monitoringPanelMode === "versions" ? (
          <VersionsWorkspace
            versions={versions}
            selectedVersion={selectedVersion}
            selectedVersionTags={selectedVersionTags}
            diff={versionDiff}
            loading={versionsLoading}
            errorMessage={versionsError}
            busyAction={versionBusyAction}
            settings={versionSettings}
            onSelectVersion={(version) => onVersionSelect?.(version)}
            onToggleCompareSelection={(versionTag) => onVersionToggleCompareSelection?.(versionTag)}
            onCreateSnapshot={() => onVersionCreateSnapshot?.()}
            onLoadSnapshot={(version) => onVersionLoadSnapshot?.(version)}
            onRollback={(version) => onVersionRollback?.(version)}
            onCompare={() => onVersionCompare?.()}
            onExport={(version) => onVersionExport?.(version)}
            onSettingsChange={(settings) => onVersionSettingsChange?.(settings)}
          />
        ) : null}
      </div>
    </section>
  );
}