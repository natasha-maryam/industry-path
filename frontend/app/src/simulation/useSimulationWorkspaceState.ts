import { useEffect, useMemo, useState } from "react";

import { extractConnectorTags, type DataSourceSelectorValue } from "../components/dataSourceSelectorModel";
import { getPlantGeniePlantDataConnectors, type PlantGeniePlantDataConnector } from "../services/api";

export type SimulationDataMode = "live" | "historical";

export type SimulationStreamRequest = {
  dataSourceId: string;
  tagScope: DataSourceSelectorValue<SimulationDataMode>["tagScope"];
  mode: SimulationDataMode;
  selectedTags: string[];
};

const SIMULATION_MODE_OPTIONS: Array<{ value: SimulationDataMode; label: string }> = [
  { value: "live", label: "Live Data" },
  { value: "historical", label: "Historical Replay" },
];

const hasUsableSimulationSource = (connectors: PlantGeniePlantDataConnector[]): boolean => connectors.some((connector) => connector.runtime.enabled);

export default function useSimulationWorkspaceState() {
  const [connectors, setConnectors] = useState<PlantGeniePlantDataConnector[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selection, setSelection] = useState<DataSourceSelectorValue<SimulationDataMode>>({
    dataSourceConnectorId: "",
    tagScope: "all",
    selectedTags: [],
    mode: "live",
  });

  useEffect(() => {
    let cancelled = false;

    const loadConnectors = async (): Promise<void> => {
      setIsLoading(true);
      try {
        const nextConnectors = await getPlantGeniePlantDataConnectors();
        if (!cancelled) {
          setConnectors(nextConnectors);
        }
      } catch {
        if (!cancelled) {
          setConnectors([]);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void loadConnectors();

    const intervalId = window.setInterval(() => {
      void loadConnectors();
    }, 15000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, []);

  const hasConnectedSource = hasUsableSimulationSource(connectors);
  const activeConnector = useMemo(() => connectors.find((connector) => connector.runtime.enabled) ?? null, [connectors]);
  const selectedConnector = useMemo(
    () => connectors.find((connector) => connector.id === selection.dataSourceConnectorId) ?? null,
    [connectors, selection.dataSourceConnectorId]
  );
  const availableTags = useMemo(() => extractConnectorTags(selectedConnector), [selectedConnector]);
  const supportsHistoricalReplay = Boolean(selectedConnector && selectedConnector.connector_type === "historian" && selectedConnector.runtime.enabled);

  useEffect(() => {
    if (selection.dataSourceConnectorId) {
      return;
    }

    const defaultConnector = activeConnector ?? (connectors.length === 1 ? connectors[0] : null);
    if (!defaultConnector) {
      return;
    }

    setSelection((current) => ({
      ...current,
      dataSourceConnectorId: defaultConnector.id,
    }));
  }, [activeConnector, connectors, selection.dataSourceConnectorId]);

  useEffect(() => {
    if (supportsHistoricalReplay || selection.mode !== "historical") {
      return;
    }

    setSelection((current) => ({
      ...current,
      mode: "live",
    }));
  }, [selection.mode, supportsHistoricalReplay]);

  const modeOptions = useMemo(
    () => SIMULATION_MODE_OPTIONS.map((option) => ({ ...option, disabled: option.value === "historical" && !supportsHistoricalReplay })),
    [supportsHistoricalReplay]
  );

  const simulationMode = supportsHistoricalReplay ? selection.mode ?? "live" : "live";
  const scopedTags = useMemo(() => {
    if (!selectedConnector) {
      return [];
    }
    return selection.tagScope === "selected" ? selection.selectedTags : availableTags;
  }, [availableTags, selectedConnector, selection.selectedTags, selection.tagScope]);

  const request = useMemo<SimulationStreamRequest>(
    () => ({
      dataSourceId: selection.dataSourceConnectorId,
      tagScope: selection.tagScope,
      mode: simulationMode,
      selectedTags: scopedTags,
    }),
    [scopedTags, selection.dataSourceConnectorId, selection.tagScope, simulationMode]
  );

  const emptyMessage = useMemo(() => {
    if (!hasConnectedSource) {
      return "No data connected. Go to Data Connectors.";
    }
    if (!selection.dataSourceConnectorId) {
      return "No data connected. Go to Data Connectors.";
    }
    if (request.selectedTags.length === 0) {
      return "No tags selected for streaming.";
    }
    if (request.mode === "historical") {
      return "No historical simulation samples match the selected source.";
    }
    return "No live plant data is currently streaming for the selected source.";
  }, [hasConnectedSource, request.mode, request.selectedTags.length, selection.dataSourceConnectorId]);

  return {
    connectors,
    isLoading,
    selection,
    setSelection,
    selectedConnector,
    availableTags,
    hasConnectedSource,
    modeOptions,
    request,
    emptyMessage,
  };
}