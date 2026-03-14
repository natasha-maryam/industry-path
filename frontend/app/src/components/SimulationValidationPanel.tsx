import { useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronRight, CircleDashed, Clock3, XCircle } from "lucide-react";
import type { PanelStatus, SimulationValidationPanelResponse } from "../services/api";
import "../styles/simulation-validation-panel.css";

type ScenarioKey =
  | "startup_sequence"
  | "shutdown_sequence"
  | "high_level_alarm"
  | "low_level_alarm"
  | "actuator_failure"
  | "stuck_valve"
  | "pump_failure"
  | "sensor_out_of_range";

type ScenarioDefinition = {
  key: ScenarioKey;
  label: string;
};

type ScenarioCard = ScenarioDefinition & {
  status: PanelStatus;
  detail: string;
  cycle_time_ms?: number;
  duration_s?: number;
  alarms_triggered?: number;
  source_scenario_name?: string;
};

const SCENARIOS: ScenarioDefinition[] = [
  { key: "startup_sequence", label: "Startup Sequence" },
  { key: "shutdown_sequence", label: "Shutdown Sequence" },
  { key: "high_level_alarm", label: "High Level Alarm" },
  { key: "low_level_alarm", label: "Low Level Alarm" },
  { key: "actuator_failure", label: "Actuator Failure" },
  { key: "stuck_valve", label: "Stuck Valve" },
  { key: "pump_failure", label: "Pump Failure" },
  { key: "sensor_out_of_range", label: "Sensor Out-of-Range" },
];

const KEYWORD_MAP: Record<ScenarioKey, string[]> = {
  startup_sequence: ["startup", "start_up", "start"],
  shutdown_sequence: ["shutdown", "shut_down", "stop"],
  high_level_alarm: ["high", "level", "hh", "hi"],
  low_level_alarm: ["low", "level", "ll", "lo"],
  actuator_failure: ["actuator", "failure"],
  stuck_valve: ["stuck", "valve"],
  pump_failure: ["pump", "failure"],
  sensor_out_of_range: ["sensor", "out", "range"],
};

export type SimulationValidationPanelData = SimulationValidationPanelResponse;

type SimulationValidationPanelProps = {
  data: SimulationValidationPanelData | null;
  loading?: boolean;
  failedMessage?: string | null;
  onRetry?: () => void;
  requiredPreviousStep?: string;
};

const normalize = (value: string): string => value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();

const statusLabel = (status: PanelStatus): string => {
  if (status === "success") {
    return "Pass";
  }
  if (status === "failed") {
    return "Fail";
  }
  if (status === "warning") {
    return "Warning";
  }
  if (status === "running") {
    return "Running";
  }
  return "Not Run";
};

const statusIcon = (status: PanelStatus) => {
  if (status === "success") {
    return <CheckCircle2 size={14} />;
  }
  if (status === "failed") {
    return <XCircle size={14} />;
  }
  if (status === "warning") {
    return <AlertTriangle size={14} />;
  }
  if (status === "running") {
    return <Clock3 size={14} />;
  }
  return <CircleDashed size={14} />;
};

const formatTimestamp = (value: string): string => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
};

const matchScenario = (
  scenarioName: string,
  available: SimulationValidationPanelResponse["scenarios"]
): SimulationValidationPanelResponse["scenarios"][number] | null => {
  const name = normalize(scenarioName);

  const direct = available.find((scenario) => normalize(scenario.scenario_name) === name);
  if (direct) {
    return direct;
  }

  const found = available.find((scenario) => {
    const candidate = normalize(scenario.scenario_name);
    const keys = KEYWORD_MAP[scenarioName as ScenarioKey] ?? [];
    return keys.every((key) => candidate.includes(key));
  });

  return found ?? null;
};

const toScenarioCards = (data: SimulationValidationPanelResponse): ScenarioCard[] =>
  SCENARIOS.map((definition) => {
    const matched = matchScenario(definition.key, data.scenarios ?? []);
    if (!matched) {
      return {
        ...definition,
        status: "idle",
        detail: "Scenario was not executed in this run.",
      };
    }

    return {
      ...definition,
      status: matched.status,
      detail: matched.message,
      cycle_time_ms: matched.cycle_time_ms,
      duration_s: matched.duration_s,
      alarms_triggered: matched.alarms_triggered,
      source_scenario_name: matched.scenario_name,
    };
  });

export default function SimulationValidationPanel({
  data,
  loading = false,
  failedMessage = null,
  onRetry,
  requiredPreviousStep = "Runtime Validation",
}: SimulationValidationPanelProps) {
  const [expanded, setExpanded] = useState<Record<ScenarioKey, boolean>>({} as Record<ScenarioKey, boolean>);

  const cards = useMemo(() => (data ? toScenarioCards(data) : []), [data]);
  const score = useMemo(() => {
    if (!cards.length) {
      return 0;
    }
    const weighted = cards.reduce((total, card) => {
      if (card.status === "success") {
        return total + 1;
      }
      if (card.status === "warning") {
        return total + 0.5;
      }
      return total;
    }, 0);
    return Math.round((weighted / cards.length) * 100);
  }, [cards]);

  if (loading) {
    return <section className="simulation-validation-panel simulation-validation-state">Running virtual commissioning scenarios...</section>;
  }

  if (failedMessage) {
    return (
      <section className="simulation-validation-panel simulation-validation-state error">
        <span>{failedMessage}</span>
        <button className="simulation-validation-retry-btn" onClick={onRetry} type="button" disabled={!onRetry}>
          Retry
        </button>
      </section>
    );
  }

  if (!data) {
    return <section className="simulation-validation-panel simulation-validation-state">No simulation validation results yet. Complete {requiredPreviousStep} first.</section>;
  }

  return (
    <section className="simulation-validation-panel">
      <header className="simulation-validation-header">
        <div className="simulation-validation-title-row">
          <h3>Simulation Validation</h3>
          <span className={`simulation-validation-status ${data.overall_status}`}>
            {statusIcon(data.overall_status)}
            {statusLabel(data.overall_status)}
          </span>
        </div>
        <div className="simulation-validation-meta-grid">
          <span>Summary Score: {score}%</span>
          <span>Run Timestamp: {formatTimestamp(data.validated_at)}</span>
          <span>
            Pass/Fail/Warn: {data.scenarios_passed}/{data.scenarios_failed}/{data.scenarios_warning}
          </span>
        </div>
      </header>

      {data.overall_status === "warning" ? (
        <div className="simulation-validation-warning">Simulation warnings detected. Review scenario details; workspace operations are not blocked.</div>
      ) : null}

      <div className="simulation-validation-grid">
        {cards.map((card) => (
          <article key={card.key} className={`simulation-card ${card.status}`}>
            <div className="simulation-card-head">
              <div className="simulation-card-title">
                {statusIcon(card.status)}
                <strong>{card.label}</strong>
              </div>
              <span className={`simulation-chip ${card.status}`}>{statusLabel(card.status)}</span>
            </div>

            <button
              className="simulation-expand"
              onClick={() =>
                setExpanded((prev) => ({
                  ...prev,
                  [card.key]: !prev[card.key],
                }))
              }
              type="button"
            >
              {expanded[card.key] ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
              Details
            </button>

            {expanded[card.key] ? (
              <div className="simulation-details">
                <p>{card.detail}</p>
                <ul>
                  <li>Cycle Time: {card.cycle_time_ms ?? "N/A"} ms</li>
                  <li>Duration: {card.duration_s ?? "N/A"} s</li>
                  <li>Alarms Triggered: {card.alarms_triggered ?? "N/A"}</li>
                  <li>Source Scenario: {card.source_scenario_name ?? "N/A"}</li>
                </ul>
              </div>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}
