import { useEffect, useMemo, useState } from "react";

import type { EngineeringTableResponseRow } from "../services/api";
import CopilotPanelProduction from "./CopilotPanelProduction";

type OpenCopilotPanelDetail = {
  command?: string;
  tag?: string | null;
};

type BottomPanelProps = {
  projectId?: string;
  selectedTag?: string | null;
  selectedRow?: EngineeringTableResponseRow | null;
  engineeringRows: EngineeringTableResponseRow[];
  graphSummary?: {
    nodeCount: number;
    edgeCount: number;
  } | null;
};

const isOpenCopilotPanelDetail = (value: unknown): value is OpenCopilotPanelDetail => {
  return Boolean(value) && typeof value === "object";
};

export default function BottomPanel({ projectId, selectedTag, selectedRow, engineeringRows, graphSummary }: BottomPanelProps) {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [launchDetail, setLaunchDetail] = useState<OpenCopilotPanelDetail>({});

  useEffect(() => {
    const handleOpen = (event: Event): void => {
      const detail = event instanceof CustomEvent && isOpenCopilotPanelDetail(event.detail) ? event.detail : {};
      setLaunchDetail(detail);
      setIsOpen(true);
    };

    window.addEventListener("openCopilotPanel", handleOpen as EventListener);
    return () => {
      window.removeEventListener("openCopilotPanel", handleOpen as EventListener);
    };
  }, []);

  const initialCommand = useMemo(() => {
    if (typeof launchDetail.command === "string" && launchDetail.command.trim()) {
      return launchDetail.command;
    }
    return "";
  }, [launchDetail.command]);

  return (
    <div
      className={`fixed bottom-0 left-0 right-0 z-40 h-[14rem] overflow-y-auto overflow-x-hidden transform border-t border-slate-300 bg-[#f4f7fa] shadow-[0_-18px_40px_rgba(15,23,42,0.18)] transition-transform duration-200 ${
        isOpen ? "translate-y-0" : "translate-y-full pointer-events-none"
      }`}
      aria-hidden={!isOpen}
    >
      <div className="flex min-h-full flex-col px-4 py-2.5 md:px-5">
        <div className="mb-2.5 flex items-center justify-between gap-3 border-b border-slate-200 pb-2.5">
          <div>
            <div className="text-[10px] font-semibold tracking-[0.18em] text-slate-500">Automation Copilot</div>
            <div className="text-[11px] text-slate-600">Automation Copilot uses the active AI and data connectors configured in Settings &gt; Data Connectors.</div>
          </div>
          <button
            type="button"
            className="command-btn text-[11px]"
            onClick={() => setIsOpen(false)}
          >
            Close
          </button>
        </div>

        <div className="min-h-0 flex-1">
          <CopilotPanelProduction
            projectId={projectId}
            selectedTag={selectedTag}
            selectedRow={selectedRow}
            engineeringRows={engineeringRows}
            graphSummary={graphSummary}
            initialCommand={initialCommand}
          />
        </div>
      </div>
    </div>
  );
}