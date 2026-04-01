import { useEffect, useMemo, useState } from "react";

import PlantGenieConnectorSettings from "./PlantGenieConnectorSettings";
import PlantGenieIndustrialConnectionsModal from "./PlantGenieIndustrialConnectionsModal";
import ChatInput from "./plantGenie/ChatInput";
import MessageList from "./plantGenie/MessageList";
import type { PlantGenieMessage } from "./plantGenie/MessageBubble";
import PlantGenieHeader from "./plantGenie/PlantGenieHeader";
import {
  getPlantGenieAIConnectors,
  getPlantGeniePlantDataConnectors,
  queryPlantGenie,
  type PlantGenieAIConnector,
  type PlantGeniePlantDataConnector,
} from "../services/api";
import "../styles/plant-genie.css";

type PlantGenieWorkspaceProps = {
  hasProject: boolean;
  projectName?: string | null;
  selectedTag?: string | null;
};

export type PlantGenieChatContext = {
  hasProject: boolean;
  projectName?: string | null;
  selectedTag?: string | null;
};

const createMessageId = (): string => {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  return `plant-genie-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
};

const buildSeedPrompt = (selectedTag?: string | null): string => {
  if (selectedTag) {
    return `Ask about ${selectedTag}`;
  }

  return "Ask a question...";
};

const buildWelcomeMessage = (context: PlantGenieChatContext): PlantGenieMessage => {
  if (!context.hasProject) {
    return {
      id: createMessageId(),
      role: "assistant",
      content:
        "Select a project, then connect an external AI service to use Plant Genie. This product no longer generates native answers from local workspace data.",
    };
  }

  return {
    id: createMessageId(),
    role: "assistant",
    content: context.selectedTag
      ? `Plant Genie is ready for ${context.projectName ?? "the active project"}. The current focus is ${context.selectedTag}, but responses only come from a connected external AI service.`
      : `Plant Genie is ready for ${context.projectName ?? "the active project"}. Connect an external AI service to begin the session.`,
  };
};

export default function PlantGenieWorkspace({ hasProject, projectName, selectedTag }: PlantGenieWorkspaceProps) {
  const context = useMemo<PlantGenieChatContext>(
    () => ({
      hasProject,
      projectName,
      selectedTag,
    }),
    [hasProject, projectName, selectedTag]
  );

  const [messages, setMessages] = useState<PlantGenieMessage[]>(() => [buildWelcomeMessage(context)]);
  const [draft, setDraft] = useState<string>(selectedTag ? buildSeedPrompt(selectedTag) : "");
  const [isThinking, setIsThinking] = useState<boolean>(false);
  const [aiConnectors, setAiConnectors] = useState<PlantGenieAIConnector[]>([]);
  const [plantDataConnectors, setPlantDataConnectors] = useState<PlantGeniePlantDataConnector[]>([]);
  const [aiModalKey, setAiModalKey] = useState<number>(0);
  const [plantDataModalKey, setPlantDataModalKey] = useState<number>(0);

  const activeAIConnector = useMemo(
    () => aiConnectors.find((connector) => connector.is_active) ?? null,
    [aiConnectors]
  );
  const activePlantDataConnector = useMemo(
    () => plantDataConnectors.find((connector) => connector.runtime.enabled) ?? null,
    [plantDataConnectors]
  );
  const canChat = Boolean(hasProject && activeAIConnector && activePlantDataConnector);
  const missingDependencies = useMemo(
    () => [
      activeAIConnector
        ? null
        : {
            title: "No AI connected",
            body: "Connect your own AI provider and API key before Plant Genie can respond.",
          },
      activePlantDataConnector
        ? null
        : {
            title: "No plant data connected",
            body: "Connect your live plant data source before Plant Genie can use real operational context.",
          },
    ].filter(Boolean) as Array<{ title: string; body: string }>,
    [activeAIConnector, activePlantDataConnector]
  );

  useEffect(() => {
    const loadSetupState = async (): Promise<void> => {
      try {
        const [nextAIConnectors, nextPlantDataConnectors] = await Promise.all([
          getPlantGenieAIConnectors(),
          getPlantGeniePlantDataConnectors(),
        ]);
        setAiConnectors(nextAIConnectors);
        setPlantDataConnectors(nextPlantDataConnectors);
      } catch {
        // Individual modal and query flows surface their own errors; keep the setup shell quiet here.
      }
    };

    void loadSetupState();
  }, []);

  useEffect(() => {
    setMessages([buildWelcomeMessage(context)]);
    setDraft(selectedTag ? buildSeedPrompt(selectedTag) : "");
    setIsThinking(false);
  }, [canChat, hasProject, projectName, selectedTag]);

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
        projectName={projectName}
        selectedTag={selectedTag}
        statuses={[
          { label: activeAIConnector ? "AI Connected" : "AI Not Connected", connected: Boolean(activeAIConnector) },
          ...(activePlantDataConnector
            ? [{ label: "Plant Data Connected", connected: true }]
            : []),
        ]}
        actions={[
          ...(!activeAIConnector ? [{ label: "Connect your AI", onClick: () => setAiModalKey((current) => current + 1) }] : []),
          ...(!activePlantDataConnector
            ? [{ label: "Connect plant data", onClick: () => setPlantDataModalKey((current) => current + 1) }]
            : []),
        ]}
      />

      {missingDependencies.length > 0 ? (
        <div className="plant-genie-empty-state-shell">
          <div className="plant-genie-empty-state-stack">
            {missingDependencies.map((item) => (
              <article key={item.title} className="plant-genie-empty-state-card">
                <h2>{item.title}</h2>
                <p>{item.body}</p>
              </article>
            ))}
            <p className="plant-genie-setup-helper">
              Plant Genie stays read-only until your own AI and live plant data are connected.
            </p>
          </div>
        </div>
      ) : (
        <MessageList messages={messages} isThinking={isThinking} />
      )}

      <ChatInput
        value={draft}
        onChange={setDraft}
        onSend={submitPrompt}
        placeholder={canChat ? "Ask a question..." : "Connect your AI and plant data to start chatting"}
        disabled={!canChat}
        isThinking={isThinking}
        helperText={
          canChat
            ? activePlantDataConnector
              ? `Using ${activeAIConnector?.name ?? "your AI connector"} and ${activePlantDataConnector.name}.`
              : undefined
            : "Plant Genie uses only your connected AI provider and live plant data."
        }
      />

      <PlantGenieConnectorSettings
        modalOnly
        openCreateModalKey={aiModalKey}
        onConnectorsChange={setAiConnectors}
      />
      <PlantGenieIndustrialConnectionsModal
        openCreateModalKey={plantDataModalKey}
        onConnectorsChange={setPlantDataConnectors}
      />
    </section>
  );
}