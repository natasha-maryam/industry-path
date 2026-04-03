import { useState } from "react";

import DataSourceSelector from "../components/DataSourceSelector";
import WorkspaceActionPanel from "../components/WorkspaceActionPanel";
import SimulationEngine from "./SimulationEngine";
import SimulationSignalTable from "./SimulationSignalTable";
import useSimulationWorkspaceState from "./useSimulationWorkspaceState";

type SimulationWorkspaceProps = {
  runPanel?: {
    title: string;
    description: string;
    actionLabel?: string;
    onAction?: () => void;
    actionDisabled?: boolean;
    actionLoading?: boolean;
    progressLines?: string[];
  };
};

export default function SimulationWorkspace({ runPanel }: SimulationWorkspaceProps) {
  const [status, setStatus] = useState("");
  const { connectors, isLoading, selection, setSelection, selectedConnector, availableTags, hasConnectedSource, modeOptions, request, emptyMessage } =
    useSimulationWorkspaceState();

  return (
    <div className="workspace-module-stack">
      {/* Simulation is plant-data-only and is driven exclusively by Data Connectors + the unified tag/state store. */}
      <DataSourceSelector
        title="Simulation Data Source"
        description="Use a saved connection profile from Data Connectors to scope Simulation to centralized plant data."
        subtext="Select the data source to drive real-time or historical simulation behavior."
        connectors={connectors}
        isLoading={isLoading}
        value={selection}
        onChange={setSelection}
        modeLabel="Mode"
        modeOptions={modeOptions}
        layout="topbar"
        notice={
          !hasConnectedSource
            ? {
                text: "No data connected. Go to Data Connectors.",
              }
            : selectedConnector
              ? {
                  text:
                    request.mode === "historical"
                      ? `Historical replay is scoped to ${selectedConnector.name} through the unified tag/state store.`
                      : selection.tagScope === "selected"
                        ? `${selection.selectedTags.length} selected tag${selection.selectedTags.length === 1 ? "" : "s"} in ${selectedConnector.name}.`
                        : `${availableTags.length} reusable tag${availableTags.length === 1 ? "" : "s"} exposed by ${selectedConnector.name}.`,
                }
              : undefined
        }
      />

      {runPanel ? (
        <WorkspaceActionPanel
          eyebrow="Simulation"
          title={runPanel.title}
          description={runPanel.description}
          actionLabel={runPanel.actionLabel}
          onAction={runPanel.onAction}
          actionDisabled={runPanel.actionDisabled}
          actionLoading={runPanel.actionLoading}
          progressLines={runPanel.progressLines}
        />
      ) : null}

      <div className="simulation-page-layout simulation-page-layout-legacy">
        <div>
          <SimulationEngine onStatus={setStatus} />
        </div>
        <SimulationSignalTable request={request} sourceName={selectedConnector?.name ?? null} emptyMessage={emptyMessage} />
      </div>

      {status ? <div className="export-note">{status}</div> : null}
    </div>
  );
}