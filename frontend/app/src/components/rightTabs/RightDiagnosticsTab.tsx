import type { RuntimeEvaluationCycle } from "../../services/api";
import type { SimulationTraceIssue } from "../../services/api";
import type { FaultAnalysisResult } from "../../services/api";

type RightDiagnosticsTabProps = {
  diagnostics: RuntimeEvaluationCycle | null;
  simulationIssues?: SimulationTraceIssue[];
  faultAnalysis?: FaultAnalysisResult | null;
  analyzedTag?: string | null;
  inputMessage?: string | null;
  loading?: boolean;
  error?: string | null;
};

export default function RightDiagnosticsTab({
  diagnostics,
  simulationIssues = [],
  faultAnalysis = null,
  analyzedTag = null,
  inputMessage = null,
  loading = false,
  error = null,
}: RightDiagnosticsTabProps) {
  if (!diagnostics) {
    return (
      <>
        <div className="panel-subtitle">Simulation Diagnostics</div>
        <ul className="trace-chain">
          {simulationIssues.length > 0 ? (
            simulationIssues.map((issue, index) => <li key={`${issue.tag}-${issue.issue}-${index}`}>{`${issue.tag}: ${issue.issue}`}</li>)
          ) : (
            <li>No simulation issues detected</li>
          )}
        </ul>

        <div className="panel-subtitle">Health Checks</div>
        <ul className="trace-chain">
          <li>No evaluated diagnostics available yet.</li>
        </ul>

        <div className="panel-subtitle">Fault Analysis</div>
        <ul className="trace-chain">
          {analyzedTag ? <li>Analyzed Tag: {analyzedTag}</li> : null}
          {inputMessage ? <li>{inputMessage}</li> : null}
          {loading ? <li>Analyzing fault...</li> : error ? <li>{error}</li> : <li>No fault analysis run yet.</li>}
        </ul>
      </>
    );
  }

  const activeAlarms = Object.entries(diagnostics.alarms || {})
    .filter(([, active]) => Boolean(active))
    .map(([name]) => name);

  return (
    <>
      <div className="panel-subtitle">Simulation Diagnostics</div>
      <ul className="trace-chain">
        <li>Issue count: {simulationIssues.length}</li>
        {simulationIssues.length > 0 ? (
          simulationIssues.map((issue, index) => <li key={`${issue.tag}-${issue.issue}-${index}`}>{`${issue.tag}: ${issue.issue}`}</li>)
        ) : (
          <li>No simulation issues detected</li>
        )}
      </ul>

      <div className="panel-subtitle">Health Checks</div>
      <ul className="trace-chain">
        {(diagnostics.health_checks || []).map((item) => (
          <li key={item.name}>
            {item.name}: {item.status} — {item.message}
          </li>
        ))}
      </ul>

      <div className="panel-subtitle" style={{ marginTop: "0.6rem" }}>
        Active Alarms
      </div>
      <ul className="trace-chain">
        {activeAlarms.length > 0 ? activeAlarms.map((alarm) => <li key={alarm}>{alarm}</li>) : <li>No active alarms</li>}
      </ul>

      <div className="panel-subtitle" style={{ marginTop: "0.6rem" }}>
        Last Evaluation
      </div>
      <ul className="trace-chain">
        <li>Reason: {diagnostics.reason}</li>
        <li>Evaluated blocks: {(diagnostics.evaluated_blocks || []).join(", ") || "none"}</li>
        <li>Signal updates: {diagnostics.signal_state_updated ? "yes" : "no"}</li>
      </ul>

      <div className="panel-subtitle" style={{ marginTop: "0.6rem" }}>
        Fault Analysis{analyzedTag ? ` (${analyzedTag})` : ""}
      </div>
      {inputMessage ? <ul className="trace-chain"><li>{inputMessage}</li></ul> : null}
      {loading ? (
        <ul className="trace-chain">
          <li>{analyzedTag ? `Analyzing fault for ${analyzedTag}...` : "Analyzing fault..."}</li>
        </ul>
      ) : error ? (
        <ul className="trace-chain">
          <li>{error}</li>
        </ul>
      ) : !faultAnalysis ? (
        <ul className="trace-chain">
          <li>No fault analysis run yet.</li>
        </ul>
      ) : (
        <ul className="trace-chain">
          <li>Alarm: {faultAnalysis.alarm}</li>
          {faultAnalysis.loop_id ? <li>Loop ID: {faultAnalysis.loop_id}</li> : null}
          {faultAnalysis.actuator_tag ? <li>Actuator Tag: {faultAnalysis.actuator_tag}</li> : null}
          {faultAnalysis.control_strategy ? <li>Control Strategy: {faultAnalysis.control_strategy}</li> : null}
          <li>Root Cause: {faultAnalysis.root_cause}</li>
          <li>Confidence: {Number(faultAnalysis.confidence || 0).toFixed(2)}</li>
          <li>Affected Devices: {(faultAnalysis.affected_devices || []).join(", ") || "none"}</li>
          <li>Timeline: {(faultAnalysis.timeline || []).length} sample(s)</li>
        </ul>
      )}
    </>
  );
}
