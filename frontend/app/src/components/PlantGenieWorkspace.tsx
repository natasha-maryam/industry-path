import { useEffect, useMemo, useRef, useState } from "react";

import ChatInput from "./plantGenie/ChatInput";
import DataSourceSelector from "./DataSourceSelector";
import MessageList from "./plantGenie/MessageList";
import type { PlantGenieMessage } from "./plantGenie/MessageBubble";
import PlantGenieHeader from "./plantGenie/PlantGenieHeader";
import {
  connectPlantGenieAIBinding,
  getPlantGenieAIBinding,
  getPlantGenieAIConnectors,
  getPlantGeniePlantDataConnectors,
  queryPlantGenie,
  type PlantGenieAIBinding,
  type PlantGenieAIBindingContextMode,
  type PlantGenieAIConnector,
  type PlantGeniePlantDataConnector,
} from "../services/api";
import type { DataSourceSelectorValue } from "./dataSourceSelectorModel";
import "../styles/plant-genie.css";

type PlantGenieWorkspaceProps = {
  hasProject: boolean;
  projectName?: string | null;
};

export type PlantGenieChatContext = {
  hasProject: boolean;
  projectName?: string | null;
};

const DEFAULT_BINDING: PlantGenieAIBinding = {
  configured: false,
  data_source_connector_id: null,
  data_source_connector_name: null,
  tag_scope: "all",
  selected_tags: [],
  context_mode: "live_only",
  sampling_mode: "stream",
  sampling_interval_ms: 5000,
  ai_access_mode: "read_only",
  include_system_structure: true,
  ai_api_input: null,
  source_connector_enabled: false,
  source_connector_healthy: false,
  updated_at: null,
};

const createMessageId = (): string => {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  return `plant-genie-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
};

const buildSeedPrompt = (): string => {
  return "";
};

const buildWelcomeMessage = (): PlantGenieMessage => {
  return {
    id: createMessageId(),
    role: "assistant",
    content: "Hi! Im your Plant Genie, ask me anything about your plant.",
  };
};

export default function PlantGenieWorkspace({ hasProject, projectName }: PlantGenieWorkspaceProps) {
  const context = useMemo<PlantGenieChatContext>(
    () => ({
      hasProject,
      projectName,
    }),
    [hasProject, projectName]
  );

  const [messages, setMessages] = useState<PlantGenieMessage[]>(() => [buildWelcomeMessage()]);
  const [draft, setDraft] = useState<string>(buildSeedPrompt());
  const [isThinking, setIsThinking] = useState<boolean>(false);
  const [aiConnectors, setAiConnectors] = useState<PlantGenieAIConnector[]>([]);
  const [plantDataConnectors, setPlantDataConnectors] = useState<PlantGeniePlantDataConnector[]>([]);
  const [binding, setBinding] = useState<PlantGenieAIBinding>(DEFAULT_BINDING);
  const [isBindingLoading, setIsBindingLoading] = useState<boolean>(true);
  const [selectorError, setSelectorError] = useState<string | null>(null);
  const [isSelectorSaving, setIsSelectorSaving] = useState<boolean>(false);
  const saveSequenceRef = useRef(0);

  const activeAIConnector = useMemo(
    () => aiConnectors.find((connector) => connector.is_active) ?? null,
    [aiConnectors]
  );
  const selectedPlantDataConnector = useMemo(
    () => plantDataConnectors.find((connector) => connector.id === binding.data_source_connector_id) ?? null,
    [binding.data_source_connector_id, plantDataConnectors]
  );
  const selectorValue = useMemo<DataSourceSelectorValue<PlantGenieAIBindingContextMode>>(
    () => ({
      dataSourceConnectorId: binding.data_source_connector_id ?? "",
      tagScope: binding.tag_scope,
      selectedTags: binding.selected_tags,
      mode: binding.context_mode,
    }),
    [binding.context_mode, binding.data_source_connector_id, binding.selected_tags, binding.tag_scope]
  );
  const canChat = Boolean(hasProject && activeAIConnector && binding.configured && binding.source_connector_enabled);

  useEffect(() => {
    const loadSetupState = async (): Promise<void> => {
      setIsBindingLoading(true);
      try {
        const [nextAIConnectors, nextPlantDataConnectors, nextBinding] = await Promise.all([
          getPlantGenieAIConnectors(),
          getPlantGeniePlantDataConnectors(),
          getPlantGenieAIBinding(),
        ]);
        setAiConnectors(nextAIConnectors);
        setPlantDataConnectors(nextPlantDataConnectors);
        setBinding(nextBinding);
        setSelectorError(null);
      } catch (error) {
        setSelectorError(error instanceof Error ? error.message : "Failed to load the Plant Genie data source selector.");
      } finally {
        setIsBindingLoading(false);
      }
    };

    void loadSetupState();
  }, []);

  useEffect(() => {
    setMessages([buildWelcomeMessage()]);
    setDraft(buildSeedPrompt());
    setIsThinking(false);
  }, [canChat, hasProject, projectName]);

  const persistBinding = async (
    updater: (current: PlantGenieAIBinding) => PlantGenieAIBinding,
    errorMessage: string
  ): Promise<void> => {
    const baseBinding = binding ?? DEFAULT_BINDING;
    const nextBinding = updater(baseBinding);
    const sequence = saveSequenceRef.current + 1;
    saveSequenceRef.current = sequence;

    setBinding(nextBinding);
    setSelectorError(null);

    if (!nextBinding.data_source_connector_id) {
      return;
    }

    setIsSelectorSaving(true);
    try {
      const response = await connectPlantGenieAIBinding({
        data_source_connector_id: nextBinding.data_source_connector_id,
        tag_scope: nextBinding.tag_scope,
        selected_tags: nextBinding.selected_tags,
        context_mode: nextBinding.context_mode,
        sampling_mode: nextBinding.sampling_mode,
        sampling_interval_ms: nextBinding.sampling_mode === "interval" ? nextBinding.sampling_interval_ms : null,
        ai_access_mode: nextBinding.ai_access_mode,
        include_system_structure: nextBinding.include_system_structure,
        ai_api_input: nextBinding.ai_api_input,
      });

      if (saveSequenceRef.current === sequence) {
        setBinding(response.binding);
      }
    } catch (error) {
      if (saveSequenceRef.current === sequence) {
        setSelectorError(error instanceof Error ? error.message : errorMessage);
      }
    } finally {
      if (saveSequenceRef.current === sequence) {
        setIsSelectorSaving(false);
      }
    }
  };

  const handleSelectorChange = async (nextValue: DataSourceSelectorValue<PlantGenieAIBindingContextMode>): Promise<void> => {
    const nextConnector = plantDataConnectors.find((connector) => connector.id === nextValue.dataSourceConnectorId) ?? null;
    await persistBinding(
      (baseBinding) => ({
        ...baseBinding,
        configured: Boolean(nextValue.dataSourceConnectorId),
        data_source_connector_id: nextValue.dataSourceConnectorId || null,
        data_source_connector_name: nextConnector?.name ?? null,
        tag_scope: nextValue.tagScope,
        selected_tags: nextValue.selectedTags,
        source_connector_enabled: nextConnector?.runtime.enabled ?? false,
        source_connector_healthy: nextConnector?.health.healthy ?? false,
      }),
      "Failed to update the Plant Genie data source."
    );
  };

  const handleSystemStructureToggle = async (enabled: boolean): Promise<void> => {
    await persistBinding(
      (baseBinding) => ({
        ...baseBinding,
        include_system_structure: enabled,
      }),
      "Failed to update the Plant Genie context toggle."
    );
  };

  const submitPrompt = async (prompt: string): Promise<void> => {
    const trimmedPrompt = prompt.trim();
    if (!trimmedPrompt || isThinking) {
      return;
    }

    setMessages((current) => [
      ...current,
      {
        id: createMessageId(),
        role: "user",
        content: trimmedPrompt,
      },
    ]);
    setDraft("");
    setIsThinking(true);

    try {
      const response = await queryPlantGenie({
        prompt: trimmedPrompt,
        context,
      });
      setMessages((current) => [
        ...current,
        {
          id: createMessageId(),
          role: "assistant",
          content: response.answer,
        },
      ]);
    } catch (error) {
      const content = error instanceof Error && error.message
        ? error.message
        : "The Plant Genie request could not be completed. Retry when the assistant backend is available.";
      setMessages((current) => [
        ...current,
        {
          id: createMessageId(),
          role: "assistant",
          content,
        },
      ]);
    } finally {
      setIsThinking(false);
    }
  };

  return (
    <section className="plant-genie-chat-screen" aria-label="Plant Genie chat workspace">
      <PlantGenieHeader
        description="Plant Genie uses the active AI connector and the saved data source selected below."
        statuses={[
          { label: activeAIConnector ? "AI Connected" : "AI Not Connected", connected: Boolean(activeAIConnector) },
          { label: binding.configured ? "Data Source Selected" : "No Data Source", connected: binding.configured && binding.source_connector_enabled },
        ]}
      />

      <div className="plant-genie-selector-shell">
        <DataSourceSelector
          title="Active Data Source"
          description="Reference only existing centralized data source and AI binding configuration for Plant Genie."
          subtext="Select the data source the AI will use to analyze and answer questions about your system."
          connectors={plantDataConnectors}
          isLoading={isBindingLoading}
          value={selectorValue}
          onChange={(nextValue) => {
            void handleSelectorChange(nextValue);
          }}
          layout="topbar"
          notice={
            selectorError
              ? { tone: "error", text: selectorError }
              : isSelectorSaving
                ? { text: "Updating Plant Genie source..." }
                : selectedPlantDataConnector
                  ? { text: `Using: ${selectedPlantDataConnector.name}` }
                  : undefined
          }
        />
        <div className="plant-genie-selector-toolbar">
          <div className="plant-genie-selector-indicator" aria-live="polite">
            <span className="plant-genie-selector-indicator-label">Using:</span>
            <span className="plant-genie-selector-indicator-value">{selectedPlantDataConnector?.name ?? "No active data source selected"}</span>
          </div>
          <label className="plant-genie-selector-toggle">
            <input
              type="checkbox"
              checked={binding.include_system_structure}
              onChange={(event) => {
                void handleSystemStructureToggle(event.target.checked);
              }}
              disabled={isBindingLoading || isSelectorSaving || !binding.configured}
            />
            <span>Include system structure</span>
          </label>
        </div>
      </div>

      <MessageList messages={messages} isThinking={isThinking} />

      <ChatInput
        value={draft}
        onChange={setDraft}
        onSend={submitPrompt}
        placeholder="Ask me about your system :)"
        tooltip="Ask me about your system :)"
        disabled={!canChat}
        isThinking={isThinking}
        helperText={
          canChat
            ? selectedPlantDataConnector
              ? `Using ${activeAIConnector?.name ?? "your AI connector"} and ${selectedPlantDataConnector.name}.`
              : undefined
            : "Plant Genie uses only saved sources from Settings > Data Connectors."
        }
      />
    </section>
  );
}