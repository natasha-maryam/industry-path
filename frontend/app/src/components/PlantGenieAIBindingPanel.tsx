import { Bot, CheckCircle2, LoaderCircle, PlugZap } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { toast } from "react-hot-toast";

import {
  connectPlantGenieAIBinding,
  getPlantGenieAIBinding,
  type PlantGenieAIBinding,
  type PlantGenieAIBindingAccessMode,
  type PlantGenieAIBindingContextMode,
  type PlantGenieAIBindingSamplingMode,
  type PlantGenieAIBindingTagScope,
  type PlantGeniePlantDataConnector,
} from "../services/api";
import { extractConnectorTags, TAG_SCOPE_OPTIONS } from "./dataSourceSelectorModel";

type PlantGenieAIBindingPanelProps = {
  connectors: PlantGeniePlantDataConnector[];
  isConnectorsLoading?: boolean;
};

type BindingFormState = {
  dataSourceConnectorId: string;
  tagScope: PlantGenieAIBindingTagScope;
  selectedTags: string[];
  contextMode: PlantGenieAIBindingContextMode;
  samplingMode: PlantGenieAIBindingSamplingMode;
  samplingIntervalMs: string;
  aiAccessMode: PlantGenieAIBindingAccessMode;
  includeSystemStructure: boolean;
  aiApiInput: string;
};

const EMPTY_FORM: BindingFormState = {
  dataSourceConnectorId: "",
  tagScope: "all",
  selectedTags: [],
  contextMode: "live_only",
  samplingMode: "stream",
  samplingIntervalMs: "5000",
  aiAccessMode: "read_only",
  includeSystemStructure: true,
  aiApiInput: "",
};

const CONTEXT_MODE_OPTIONS: Array<{ value: PlantGenieAIBindingContextMode; label: string }> = [
  { value: "live_only", label: "Live Only" },
  { value: "historical", label: "Historical" },
  { value: "hybrid", label: "Hybrid" },
];

const SAMPLING_MODE_OPTIONS: Array<{ value: PlantGenieAIBindingSamplingMode; label: string }> = [
  { value: "stream", label: "Real-time stream" },
  { value: "interval", label: "Interval" },
];

const ACCESS_MODE_OPTIONS: Array<{ value: PlantGenieAIBindingAccessMode; label: string }> = [
  { value: "read_only", label: "Read-only" },
  { value: "read_recommend", label: "Read + Recommend" },
];

const formatTimestamp = (value: string | null): string => {
  if (!value) {
    return "Never";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "Never";
  }
  return parsed.toLocaleString();
};

const toFormState = (binding: PlantGenieAIBinding): BindingFormState => ({
  dataSourceConnectorId: binding.data_source_connector_id ?? "",
  tagScope: binding.tag_scope,
  selectedTags: binding.selected_tags,
  contextMode: binding.context_mode,
  samplingMode: binding.sampling_mode,
  samplingIntervalMs: String(binding.sampling_interval_ms ?? 5000),
  aiAccessMode: binding.ai_access_mode,
  includeSystemStructure: binding.include_system_structure,
  aiApiInput: binding.ai_api_input ?? "",
});

export default function PlantGenieAIBindingPanel({
  connectors,
  isConnectorsLoading = false,
}: PlantGenieAIBindingPanelProps) {
  const [binding, setBinding] = useState<PlantGenieAIBinding | null>(null);
  const [form, setForm] = useState<BindingFormState>(EMPTY_FORM);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isConnecting, setIsConnecting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const selectedConnector = useMemo(
    () => connectors.find((connector) => connector.id === form.dataSourceConnectorId) ?? null,
    [connectors, form.dataSourceConnectorId]
  );

  const availableTags = useMemo(() => extractConnectorTags(selectedConnector), [selectedConnector]);

  useEffect(() => {
    const load = async (): Promise<void> => {
      setIsLoading(true);
      try {
        const nextBinding = await getPlantGenieAIBinding();
        setBinding(nextBinding);
        setForm(toFormState(nextBinding));
      } catch (loadError) {
        const message = loadError instanceof Error ? loadError.message : "Failed to load AI binding.";
        setError(message);
      } finally {
        setIsLoading(false);
      }
    };

    void load();
  }, []);

  useEffect(() => {
    if (form.tagScope !== "selected") {
      return;
    }
    setForm((current) => ({
      ...current,
      selectedTags: current.selectedTags.filter((tag) => availableTags.includes(tag)),
    }));
  }, [availableTags, form.tagScope]);

  const updateField = <K extends keyof BindingFormState>(field: K, value: BindingFormState[K]): void => {
    setForm((current) => ({ ...current, [field]: value }));
    setError(null);
  };

  const toggleTag = (tag: string): void => {
    setForm((current) => ({
      ...current,
      selectedTags: current.selectedTags.includes(tag)
        ? current.selectedTags.filter((item) => item !== tag)
        : [...current.selectedTags, tag],
    }));
  };

  const handleConnect = async (): Promise<void> => {
    if (!form.dataSourceConnectorId) {
      setError("Select a saved data source profile.");
      return;
    }
    if (form.tagScope === "selected" && form.selectedTags.length === 0) {
      setError("Select at least one tag for the chosen profile.");
      return;
    }
    if (form.samplingMode === "interval") {
      const parsedInterval = Number.parseInt(form.samplingIntervalMs, 10);
      if (Number.isNaN(parsedInterval) || parsedInterval < 500) {
        setError("Sampling interval must be at least 500 ms.");
        return;
      }
    }

    setIsConnecting(true);
    setError(null);
    try {
      const response = await connectPlantGenieAIBinding({
        data_source_connector_id: form.dataSourceConnectorId,
        tag_scope: form.tagScope,
        selected_tags: form.selectedTags,
        context_mode: form.contextMode,
        sampling_mode: form.samplingMode,
        sampling_interval_ms: form.samplingMode === "interval" ? Number.parseInt(form.samplingIntervalMs, 10) : null,
        ai_access_mode: form.aiAccessMode,
        include_system_structure: form.includeSystemStructure,
        ai_api_input: form.aiApiInput.trim() || null,
      });
      setBinding(response.binding);
      setForm(toFormState(response.binding));
      toast.success(response.message, { className: "industrial-toast industrial-toast-success" });
    } catch (connectError) {
      const message = connectError instanceof Error ? connectError.message : "AI binding save failed.";
      setError(message);
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setIsConnecting(false);
    }
  };

  return (
    <section className="plant-genie-connectors-card data-connectors-card data-connectors-card-full">
      <div className="plant-genie-connectors-header data-connectors-header">
        <div>
          <div className="plant-genie-settings-kicker">AI / Plant Genie Connection Layer</div>
          <h3 className="panel-title">Centralized AI Binding</h3>
          <p className="billing-settings-lead">
            Bind Plant Genie AI to an existing Data Connector profile. This layer only references saved profiles and reads unified tag/state context from the shared store.
          </p>
        </div>
      </div>

      <div className="plant-genie-connectors-summary">
        <div className="plant-genie-summary-chip is-active">
          <Bot size={12} />
          <span>{binding?.configured ? `Bound to ${binding.data_source_connector_name ?? "saved profile"}` : "No AI binding configured"}</span>
        </div>
        <div className="plant-genie-summary-chip">
          <CheckCircle2 size={12} />
          <span>Updated {formatTimestamp(binding?.updated_at ?? null)}</span>
        </div>
      </div>

      {isLoading ? (
        <div className="plant-genie-connectors-empty data-connectors-empty-state">
          <LoaderCircle size={14} className="animate-spin" /> Loading AI binding...
        </div>
      ) : (
        <div className="plant-genie-form-grid data-connectors-form-grid">
          <label className="plant-genie-field plant-genie-field-full">
            <span>Select Data Source</span>
            <select
              value={form.dataSourceConnectorId}
              onChange={(event) => updateField("dataSourceConnectorId", event.target.value)}
              disabled={isConnectorsLoading || connectors.length === 0}
            >
              <option value="">Choose saved connector profile</option>
              {connectors.map((connector) => (
                <option key={connector.id} value={connector.id}>
                  {connector.name}
                </option>
              ))}
            </select>
          </label>

          <label className="plant-genie-field">
            <span>Tag Scope</span>
            <select value={form.tagScope} onChange={(event) => updateField("tagScope", event.target.value as PlantGenieAIBindingTagScope)}>
              {TAG_SCOPE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="plant-genie-field">
            <span>Context Mode</span>
            <select value={form.contextMode} onChange={(event) => updateField("contextMode", event.target.value as PlantGenieAIBindingContextMode)}>
              {CONTEXT_MODE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="plant-genie-field">
            <span>Sampling Rate</span>
            <select value={form.samplingMode} onChange={(event) => updateField("samplingMode", event.target.value as PlantGenieAIBindingSamplingMode)}>
              {SAMPLING_MODE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          {form.samplingMode === "interval" ? (
            <label className="plant-genie-field">
              <span>Interval (ms)</span>
              <input type="number" min={500} max={300000} value={form.samplingIntervalMs} onChange={(event) => updateField("samplingIntervalMs", event.target.value)} />
            </label>
          ) : null}

          <label className="plant-genie-field">
            <span>AI Access Mode</span>
            <select value={form.aiAccessMode} onChange={(event) => updateField("aiAccessMode", event.target.value as PlantGenieAIBindingAccessMode)}>
              {ACCESS_MODE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="plant-genie-field data-connectors-toggle-field">
            <span>System Structure</span>
            <label className="data-connectors-toggle">
              <input type="checkbox" checked={form.includeSystemStructure} onChange={(event) => updateField("includeSystemStructure", event.target.checked)} />
              <span>Include control loops and equipment context</span>
            </label>
          </label>

          <label className="plant-genie-field plant-genie-field-full">
            <span>AI API Input</span>
            <input type="text" value={form.aiApiInput} onChange={(event) => updateField("aiApiInput", event.target.value)} placeholder="Optional routing hint or API-specific input" />
          </label>

          {form.tagScope === "selected" ? (
            <div className="plant-genie-field plant-genie-field-full">
              <span>Selected Tags</span>
              {availableTags.length === 0 ? (
                <p className="data-connectors-file-name">The selected connector profile does not expose reusable tag mappings yet.</p>
              ) : (
                <div className="data-connectors-opcua-selection-list">
                  {availableTags.map((tag) => (
                    <label key={tag} className="data-connectors-toggle">
                      <input type="checkbox" checked={form.selectedTags.includes(tag)} onChange={() => toggleTag(tag)} />
                      <span>{tag}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>
          ) : null}

          {selectedConnector ? (
            <div className="plant-genie-field plant-genie-field-full">
              <span>Source Status</span>
              <div className="plant-genie-connector-status-row">
                <span>{selectedConnector.runtime.enabled ? "Profile active" : "Profile saved but not active"}</span>
                <span>{selectedConnector.health.healthy ? "Healthy" : "Health unknown or failing"}</span>
              </div>
            </div>
          ) : null}

          {error ? <div className="plant-genie-inline-alert error"><span>{error}</span></div> : null}

          <div className="plant-genie-field plant-genie-field-full data-connectors-inline-actions">
            <span>Binding Action</span>
            <div className="data-connectors-editor-actions">
              <button type="button" className="command-btn" onClick={() => void handleConnect()} disabled={isConnecting || isLoading || isConnectorsLoading || connectors.length === 0}>
                {isConnecting ? <LoaderCircle size={12} className="animate-spin" /> : <PlugZap size={12} />}
                <span>{isConnecting ? "Connecting..." : "Connect AI"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}