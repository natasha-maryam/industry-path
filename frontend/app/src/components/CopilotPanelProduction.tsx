import { useEffect, useState } from "react";

import { type EngineeringTableResponseRow } from "../services/api";

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

export default function CopilotPanelProduction({
  selectedTag,
  graphSummary,
  initialCommand = "",
}: CopilotPanelProductionProps) {
  const [command, setCommand] = useState<string>(initialCommand);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    setCommand(initialCommand);
  }, [initialCommand]);

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