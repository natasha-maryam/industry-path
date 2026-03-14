import { useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronRight, CircleDashed, LoaderCircle, Lock, XCircle } from "lucide-react";
import type { PipelineStageKey, PipelineStageState } from "../services/api";
import "../styles/pipeline-progress.css";

export const PIPELINE_PROGRESS_STEPS: PipelineStageKey[] = [
  "extraction",
  "normalization",
  "plant_graph",
  "control_loop_discovery",
  "engineering_validation",
  "logic_completion",
  "st_generation",
  "st_verification",
  "io_mapping",
  "runtime_validation",
  "simulation_validation",
  "version_snapshot",
];

const STEP_LABELS: Record<PipelineStageKey, string> = {
  extraction: "Extraction",
  normalization: "Normalization",
  plant_graph: "Plant Graph",
  control_loop_discovery: "Control Loops",
  engineering_validation: "Validation",
  logic_completion: "Logic Completion",
  st_generation: "ST Generation",
  st_verification: "ST Verification",
  io_mapping: "IO Mapping",
  runtime_validation: "Runtime Check",
  simulation_validation: "Simulation",
  version_snapshot: "Snapshot",
};

const STATUS_LABELS: Record<PipelineStageState, string> = {
  idle: "Idle",
  running: "Running",
  success: "Success",
  failed: "Failed",
  warning: "Warning",
  blocked: "Blocked",
};

const STATUS_CLASSNAMES: Record<PipelineStageState, string> = {
  idle: "idle",
  running: "running",
  success: "success",
  failed: "failed",
  warning: "warning",
  blocked: "blocked",
};

type PipelineStepDetails = {
  title?: string;
  lines?: string[];
};

export type PipelineProgressProps = {
  statuses: Partial<Record<PipelineStageKey, PipelineStageState>>;
  details?: Partial<Record<PipelineStageKey, PipelineStepDetails>>;
  className?: string;
};

const statusIcon = (state: PipelineStageState) => {
  if (state === "running") {
    return <LoaderCircle size={13} className="pipeline-progress-icon-spin" />;
  }
  if (state === "success") {
    return <CheckCircle2 size={13} />;
  }
  if (state === "failed") {
    return <XCircle size={13} />;
  }
  if (state === "warning") {
    return <AlertTriangle size={13} />;
  }
  if (state === "blocked") {
    return <Lock size={13} />;
  }
  return <CircleDashed size={13} />;
};

export default function PipelineProgress({ statuses, details = {}, className = "" }: PipelineProgressProps) {
  const [expandedSteps, setExpandedSteps] = useState<Record<PipelineStageKey, boolean>>({} as Record<PipelineStageKey, boolean>);

  const rows = useMemo(
    () =>
      PIPELINE_PROGRESS_STEPS.map((step) => {
        const status = statuses[step] ?? "idle";
        const stepDetails = details[step];
        const hasDetails = Boolean(stepDetails?.lines?.length);
        const expanded = expandedSteps[step] ?? false;

        return {
          step,
          label: STEP_LABELS[step],
          status,
          hasDetails,
          detailsTitle: stepDetails?.title ?? "Details",
          detailLines: stepDetails?.lines ?? [],
          expanded,
        };
      }),
    [details, expandedSteps, statuses]
  );

  return (
    <section className={`pipeline-progress ${className}`.trim()}>
      <header className="pipeline-progress-header">
        <h3>Engineering Workflow</h3>
      </header>

      <div className="pipeline-progress-track" role="list" aria-label="CrossLayerX engineering workflow progress">
        {rows.map((row, index) => {
          const statusClass = STATUS_CLASSNAMES[row.status];
          const isLast = index === rows.length - 1;

          return (
            <article key={row.step} className={`pipeline-progress-step ${statusClass}`} role="listitem">
              <div className="pipeline-progress-step-main">
                <div className="pipeline-progress-node" aria-hidden="true">
                  {statusIcon(row.status)}
                </div>

                {!isLast ? <span className={`pipeline-progress-link ${statusClass}`} aria-hidden="true" /> : null}

                <div className="pipeline-progress-content">
                  <div className="pipeline-progress-row">
                    <span className="pipeline-progress-label">{row.label}</span>
                    <span className={`pipeline-progress-state ${statusClass}`}>{STATUS_LABELS[row.status]}</span>
                  </div>

                  {row.hasDetails ? (
                    <button
                      className="pipeline-progress-expand"
                      onClick={() =>
                        setExpandedSteps((previous) => ({
                          ...previous,
                          [row.step]: !previous[row.step],
                        }))
                      }
                      type="button"
                    >
                      {row.expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                      {row.detailsTitle}
                    </button>
                  ) : (
                    <span className="pipeline-progress-no-details">No details</span>
                  )}
                </div>
              </div>

              {row.expanded && row.detailLines.length > 0 ? (
                <div className="pipeline-progress-details">
                  <ul>
                    {row.detailLines.map((line, lineIndex) => (
                      <li key={`${row.step}-${lineIndex}`}>{line}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}
