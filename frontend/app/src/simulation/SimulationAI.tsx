import { useState } from "react";
import { applyAIAction, queryAI, registerAI } from "./simulationApi";

type Props = {
  onStatus?: (message: string) => void;
};

export default function SimulationAI({ onStatus }: Props) {
  const [connectorId, setConnectorId] = useState<string>(() => window.localStorage.getItem("industrypath:ai:connectorId") || "default");
  const [endpoint, setEndpoint] = useState<string>(() => window.localStorage.getItem("industrypath:ai:endpoint") || "mock://ai");
  const [prompt, setPrompt] = useState("");
  const [messages, setMessages] = useState<Array<{ role: "user" | "ai"; text: string }>>([]);
  const [action, setAction] = useState<{ id: string; value: unknown } | null>(null);

  const handleRegister = async (): Promise<void> => {
    try {
      await registerAI({ id: connectorId, endpoint });
      window.localStorage.setItem("industrypath:ai:connectorId", connectorId);
      window.localStorage.setItem("industrypath:ai:endpoint", endpoint);
      onStatus?.("AI connector registered");
    } catch (error) {
      onStatus?.(error instanceof Error ? error.message : "AI connector registration failed");
    }
  };

  const handleAsk = async (): Promise<void> => {
    if (!prompt.trim()) return;
    const userPrompt = prompt.trim();
    setPrompt("");
    try {
      const result = await queryAI({ prompt: userPrompt, connectorId });
      const response = JSON.stringify(result.response ?? result);
      setMessages((prev) => [...prev, { role: "user", text: userPrompt }, { role: "ai", text: response }]);
      const suggested = result.suggestedAction as { id?: string; value?: unknown } | undefined;
      if (suggested?.id) {
        setAction({ id: String(suggested.id), value: suggested.value });
      }
    } catch (error) {
      onStatus?.(error instanceof Error ? error.message : "AI query failed");
    }
  };

  const handleApply = async (): Promise<void> => {
    if (!action) return;
    await applyAIAction(action);
    onStatus?.("AI action applied");
    setAction(null);
  };

  return (
    <section className="workspace-documents-list-panel">
      <div className="workspace-documents-list-header">
        <h3>Simulation AI</h3>
        <p>Ask questions and apply recommended overrides.</p>
      </div>
      <div className="settings-grid">
        <label className="settings-line">
          <span>Connector ID</span>
          <input value={connectorId} onChange={(event) => setConnectorId(event.target.value)} />
        </label>
        <label className="settings-line">
          <span>AI Endpoint</span>
          <input value={endpoint} onChange={(event) => setEndpoint(event.target.value)} placeholder="https://..." />
        </label>
      </div>
      <div className="modal-actions">
        <button type="button" className="command-btn" onClick={() => void handleRegister()}>
          Connect AI
        </button>
      </div>
      <div className="settings-grid">
        <label className="settings-line">
          <span>Prompt</span>
          <input value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="why is this tank rising" />
        </label>
      </div>
      <div className="modal-actions">
        <button type="button" className="command-btn primary" onClick={() => void handleAsk()}>
          Ask
        </button>
      </div>
      <div className="monitor-frame" style={{ maxHeight: 180, overflow: "auto" }}>
        {messages.map((message, index) => (
          <p key={`${message.role}-${index}`}>
            <strong>{message.role}:</strong> {message.text}
          </p>
        ))}
      </div>
      {action ? (
        <div className="monitor-frame">
          <p>
            <strong>Suggested Action:</strong> {JSON.stringify(action)}
          </p>
          <button type="button" className="command-btn" onClick={() => void handleApply()}>
            Apply Action
          </button>
        </div>
      ) : null}
    </section>
  );
}
