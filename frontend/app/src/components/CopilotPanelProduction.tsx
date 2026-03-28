import { useEffect, useMemo, useState } from "react";

import {
  type EngineeringTableResponseRow,
} from "../services/api";

type CopilotPanelProductionProps = {
  projectId?: string;
  selectedTag?: string | null;
  selectedRow?: EngineeringTableResponseRow | null;
  engineeringRows: EngineeringTableResponseRow[];
  graphSummary?: {
    nodeCount: number;
    edgeCount: number;
  } | null;
  initialCommand?: string;
};

const toPreviewRow = (row: EngineeringTableResponseRow | null): Record<string, unknown> | null => {
  if (!row) {
    return null;
  }

  return {
    tag: row.tag,
    type: row.type,
    system: row.system,
    equipment: row.equipment,
    state: row.state,
    mode: row.mode,
    confidence: row.confidence,
    warnings: row.warnings,
    upstream: row.upstream.slice(0, 6),
    downstream: row.downstream.slice(0, 6),
  };
};

const isPlainObject = (value: unknown): value is Record<string, unknown> => {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
};

function StructuredValue({ value, depth = 0 }: { value: unknown; depth?: number }) {
  if (value === null || value === undefined) {
    return <span className="text-[11px] text-slate-400">null</span>;
  }

  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return <span className="break-words text-[11px] text-slate-700">{String(value)}</span>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <span className="text-slate-400">[]</span>;
    }

    const primitiveValues = value.every(
      (item) => item === null || item === undefined || typeof item === "string" || typeof item === "number" || typeof item === "boolean"
    );

    if (primitiveValues) {
      return (
        <div className="flex flex-wrap gap-1">
          {value.map((item, index) => (
            <span key={`${depth}-${index}`} className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-700">
              {String(item)}
            </span>
          ))}
        </div>
      );
    }

    return (
      <div className="space-y-1.5">
        {value.map((item, index) => (
          <div key={`${depth}-${index}`} className="rounded-md bg-slate-50 p-1.5">
            <StructuredValue value={item} depth={depth + 1} />
          </div>
        ))}
      </div>
    );
  }

  if (isPlainObject(value)) {
    const entries = Object.entries(value);
    if (entries.length === 0) {
      return <span className="text-slate-400">{{}}</span>;
    }

    return (
      <div className={`space-y-1 ${depth === 0 ? "rounded-md bg-white" : ""}`}>
        {entries.map(([key, nestedValue]) => (
          <div key={`${depth}-${key}`} className={`min-w-0 px-1.5 py-1 ${depth === 0 ? "border-b border-slate-100 last:border-b-0" : ""}`}>
            <div className="mb-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-500">{key}</div>
            <StructuredValue value={nestedValue} depth={depth + 1} />
          </div>
        ))}
      </div>
    );
  }

  return <pre className="whitespace-pre-wrap break-words text-[11px] text-slate-700">{JSON.stringify(value, null, 2)}</pre>;
}

export default function CopilotPanelProduction({
  projectId,
  selectedTag,
  selectedRow = null,
  engineeringRows,
  graphSummary,
  initialCommand = "",
}: CopilotPanelProductionProps) {
  const [command, setCommand] = useState<string>(initialCommand);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    setCommand(initialCommand);
  }, [initialCommand]);

  const context = useMemo<Record<string, unknown>>(
    () => ({
      project_id: projectId,
      selected_tag: selectedTag,
      graph_summary: graphSummary ?? null,
      engineering_table: {
        total_rows: engineeringRows.length,
        sample_tags: engineeringRows.slice(0, 12).map((row) => row.tag),
        selected_row: toPreviewRow(selectedRow),
      },
    }),
    [engineeringRows, graphSummary, projectId, selectedRow, selectedTag]
  );

  const handleRun = async (): Promise<void> => {
    const trimmedCommand = command.trim();
    if (!trimmedCommand) {
      setNotice("Connect AI to use Automation Copilot.");
      return;
    }

    setNotice("Connect AI to use Automation Copilot.");
  };

  return (
    <div className="flex min-w-0 flex-col gap-2.5 pb-1 text-[11px]">
      <div className="text-[10px] text-slate-500">
        Connect an AI provider to enable Automation Copilot responses.
      </div>

      <form
        className="flex min-w-0 flex-col gap-1.5 md:flex-row"
        onSubmit={(event) => {
          event.preventDefault();
          void handleRun();
        }}
      >
        <input
          value={command}
          onChange={(event) => setCommand(event.target.value)}
          placeholder="Enter a prompt after connecting AI"
          className="min-w-0 flex-1 rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-[11px] text-slate-900 outline-none ring-0 transition focus:border-slate-500"
        />
        <button type="submit" className="command-btn primary min-w-[5.5rem] px-3 py-1.5 text-[11px]">
          Run
        </button>
      </form>

      <div className="flex flex-wrap items-center gap-2 text-[10px] text-slate-500">
        <span>Selected tag: {selectedTag ?? "No tag selected"}</span>
        {graphSummary ? <span>Graph: {graphSummary.nodeCount} nodes / {graphSummary.edgeCount} edges</span> : null}
      </div>

      {notice ? <div className="rounded-md border border-amber-200 bg-amber-50 px-2.5 py-1.5 text-[11px] text-amber-800">{notice}</div> : null}

      <div className="min-w-0 rounded-xl border border-slate-200 bg-slate-50 p-2.5">
        <div className="flex min-h-[96px] items-center justify-center text-[11px] text-slate-400">
          No response available. Connect AI to use Automation Copilot.
        </div>
      </div>
    </div>
  );
}