import CodeExplorerPanel, { type GeneratedLogicFile } from "./CodeExplorerPanel";
import RuntimeValidationPanel, { type RuntimeValidationPanelData } from "./RuntimeValidationPanel";
import SimulationValidationPanel, { type SimulationValidationPanelData } from "./SimulationValidationPanel";
import STVerificationPanel, { type STVerificationError } from "./STVerificationPanel";
import IOMappingTablePanel from "./IOMappingTablePanel";
import VersionHistoryPanel from "./VersionHistoryPanel";
import type { IOMappingSummaryByType, IOMappingTableRow, STVerificationPanelPayload } from "../services/api";

type BottomView = "simulation" | "monitoring" | "logic";
type CodePanelMode = "control_logic" | "generated_st" | "verification";
type MonitoringPanelMode = "io_mapping" | "runtime" | "versions";

type BottomPanelsProps = {
  activeView: BottomView;
  codePanelMode: CodePanelMode;
  monitoringPanelMode: MonitoringPanelMode;
  controlLogicCode: string;
  generatedSTCode: string;
  generatedSTFiles?: GeneratedLogicFile[];
  selectedSTFilePath?: string | null;
  onSelectSTFile?: (path: string) => void;
  logicWarnings?: string[];
  logicValidationIssues?: string[];
  stVerificationData?: STVerificationPanelPayload | null;
  isVerifyingST?: boolean;
  stVerificationFailedMessage?: string | null;
  onSelectVerificationIssue?: (issue: STVerificationError) => void;
  ioMappingRows?: IOMappingTableRow[];
  ioMappingSummary?: IOMappingSummaryByType | null;
  isGeneratingIOMapping?: boolean;
  ioMappingFailedMessage?: string | null;
  runtimeValidationData?: RuntimeValidationPanelData | null;
  runtimeFailedMessage?: string | null;
  simulationValidationData?: SimulationValidationPanelData | null;
  simulationFailedMessage?: string | null;
  onRetryIOMapping?: () => void;
  onRetrySTVerification?: () => void;
  onRetryRuntime?: () => void;
  onRetrySimulation?: () => void;
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
  logicWarnings = [],
  logicValidationIssues = [],
  stVerificationData = null,
  isVerifyingST = false,
  stVerificationFailedMessage = null,
  onSelectVerificationIssue,
  ioMappingRows = [],
  ioMappingSummary = null,
  isGeneratingIOMapping = false,
  ioMappingFailedMessage = null,
  runtimeValidationData = null,
  runtimeFailedMessage = null,
  simulationValidationData = null,
  simulationFailedMessage = null,
  onRetryIOMapping,
  onRetrySTVerification,
  onRetryRuntime,
  onRetrySimulation,
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
            <div className="monitor-frame">No control logic artifact available yet. Run Generate Control Logic first.</div>
          )
        ) : null}

        {activeView === "logic" && codePanelMode === "generated_st" ? (
          <CodeExplorerPanel
            files={generatedSTFiles}
            bundledCode={generatedSTCode}
            selectedFilePath={selectedSTFilePath}
            onSelectFile={onSelectSTFile}
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
              loading={isGeneratingIOMapping}
              failedMessage={ioMappingFailedMessage}
              onRetry={onRetryIOMapping}
              requiredPreviousStep="Logic Completion + Plant Graph"
            />
          </>
        ) : null}

        {activeView === "monitoring" && monitoringPanelMode === "runtime" ? (
          <RuntimeValidationPanel
            data={runtimeValidationData}
            failedMessage={runtimeFailedMessage}
            onRetry={onRetryRuntime}
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

        {activeView === "monitoring" && monitoringPanelMode === "versions" ? <VersionHistoryPanel /> : null}
      </div>
    </section>
  );
}