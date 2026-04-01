import { CheckCircle2, Pencil, PlugZap, Plus, Shield, TestTube2, Trash2, XCircle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { toast } from "react-hot-toast";

import {
  activatePlantGenieAIConnector,
  createPlantGenieAIConnector,
  deletePlantGenieAIConnector,
  getPlantGenieAIConnectors,
  testPlantGenieAIConnector,
  type PlantGenieAIConnector,
  type PlantGenieAIProvider,
  updatePlantGenieAIConnector,
} from "../services/api";

type PlantGenieConnectorSettingsProps = {
  modalOnly?: boolean;
  openCreateModalKey?: number;
  onConnectorsChange?: (connectors: PlantGenieAIConnector[]) => void;
};

type ConnectorFormState = {
  name: string;
  apiKey: string;
  model: string;
  providerLabel: string;
  notes: string;
};

const EMPTY_FORM: ConnectorFormState = {
  name: "",
  apiKey: "",
  model: "",
  providerLabel: "",
  notes: "",
};

const FRIENDLY_SECRET_STORAGE_MESSAGE =
  "Backend configuration is incomplete. Please configure Plant Genie secret storage and restart the server.";
const AI_PROVIDER_LABELS: Record<PlantGenieAIProvider, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  azure_openai: "Azure OpenAI",
  openrouter: "OpenRouter",
};

const normalizeConnectorModalError = (error: unknown): string => {
  const fallback = "Connector save failed.";
  const message = error instanceof Error && error.message ? error.message : fallback;
  const normalized = message.toLowerCase();

  if (
    normalized.includes("plant_genie_connector_secret") ||
    normalized.includes("jwt_secret") ||
    normalized.includes("postgres_password") ||
    normalized.includes("store plant genie connector secrets") ||
    normalized.includes("secret storage")
  ) {
    return FRIENDLY_SECRET_STORAGE_MESSAGE;
  }

  if (normalized.includes("network error") || normalized.includes("failed to fetch")) {
    return "The backend could not be reached. Confirm the server is running and try again.";
  }

  return message;
};

const formatProviderLabel = (provider: PlantGenieAIConnector["provider"], providerLabel: string | null): string => {
  const customLabel = providerLabel?.trim();
  if (customLabel) {
    return customLabel;
  }
  if (provider === "openai" || provider === "anthropic" || provider === "azure_openai" || provider === "openrouter") {
    return AI_PROVIDER_LABELS[provider];
  }
  return "Unsupported legacy provider";
};

const formatLastTested = (value: string | null): string => {
  if (!value) {
    return "Never tested";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "Never tested";
  }

  return parsed.toLocaleString();
};

const healthBadgeLabel = (connector: PlantGenieAIConnector): string => {
  if (connector.health_status === "healthy") {
    return "Healthy";
  }
  if (connector.health_status === "unhealthy") {
    return "Unhealthy";
  }
  return "Unknown";
};

export default function PlantGenieConnectorSettings({
  modalOnly = false,
  openCreateModalKey = 0,
  onConnectorsChange,
}: PlantGenieConnectorSettingsProps) {
  const [connectors, setConnectors] = useState<PlantGenieAIConnector[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedConnectorId, setSelectedConnectorId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [connectorPendingDelete, setConnectorPendingDelete] = useState<PlantGenieAIConnector | null>(null);
  const [form, setForm] = useState<ConnectorFormState>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [testingConnectorId, setTestingConnectorId] = useState<string | null>(null);
  const [activatingConnectorId, setActivatingConnectorId] = useState<string | null>(null);
  const [deletingConnectorId, setDeletingConnectorId] = useState<string | null>(null);

  const selectedConnector = useMemo(
    () => connectors.find((connector) => connector.id === selectedConnectorId) ?? null,
    [connectors, selectedConnectorId]
  );

  const isEditing = selectedConnector !== null;
  const activeConnector = useMemo(
    () => connectors.find((connector) => connector.is_active) ?? null,
    [connectors]
  );

  const loadConnectors = async (): Promise<void> => {
    setIsLoading(true);
    try {
      const nextConnectors = await getPlantGenieAIConnectors();
      setConnectors(nextConnectors);
      setSelectedConnectorId((current) => {
        if (current && nextConnectors.some((connector) => connector.id === current)) {
          return current;
        }
        return null;
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load Plant Genie connectors.";
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadConnectors();
  }, []);

  useEffect(() => {
    onConnectorsChange?.(connectors);
  }, [connectors, onConnectorsChange]);

  useEffect(() => {
    if (!modalOnly || openCreateModalKey <= 0) {
      return;
    }
    resetToCreateMode();
    setIsModalOpen(true);
  }, [modalOnly, openCreateModalKey]);

  useEffect(() => {
    if (!selectedConnector) {
      setForm(EMPTY_FORM);
      setFormError(null);
      return;
    }

    setForm({
      name: selectedConnector.name,
      apiKey: "",
      model: selectedConnector.model ?? "",
      providerLabel: selectedConnector.provider_label ?? "",
      notes: selectedConnector.notes ?? "",
    });
    setFormError(null);
  }, [selectedConnector]);

  const resetToCreateMode = (): void => {
    setSelectedConnectorId(null);
    setForm(EMPTY_FORM);
    setFormError(null);
  };

  const openCreateModal = (): void => {
    resetToCreateMode();
    setIsModalOpen(true);
  };

  const openEditModal = (connectorId: string): void => {
    setSelectedConnectorId(connectorId);
    setIsModalOpen(true);
  };

  const closeModal = (): void => {
    if (isSaving) {
      return;
    }
    setIsModalOpen(false);
    setFormError(null);
    if (!selectedConnectorId) {
      setForm(EMPTY_FORM);
    }
  };

  const closeDeleteDialog = (): void => {
    if (connectorPendingDelete && deletingConnectorId === connectorPendingDelete.id) {
      return;
    }
    setConnectorPendingDelete(null);
  };

  const validateForm = (): string | null => {
    if (!form.name.trim()) {
      return "Connector name is required.";
    }
    if ((!isEditing || !selectedConnector?.has_api_key) && !form.apiKey.trim()) {
      return "API key is required.";
    }
    return null;
  };

  const upsertConnector = (connector: PlantGenieAIConnector): void => {
    setConnectors((current) => {
      const withoutTarget = current.filter((item) => item.id !== connector.id);
      const next = [connector, ...withoutTarget];
      return next.sort((left, right) => {
        if (left.is_active !== right.is_active) {
          return left.is_active ? -1 : 1;
        }
        return right.updated_at.localeCompare(left.updated_at);
      });
    });
  };

  const handleSubmit = async (): Promise<void> => {
    const validationMessage = validateForm();
    if (validationMessage) {
      setFormError(validationMessage);
      return;
    }

    setFormError(null);
    setIsSaving(true);

    try {
      if (isEditing && selectedConnector) {
        const updated = await updatePlantGenieAIConnector(selectedConnector.id, {
          name: form.name.trim(),
          apiKey: form.apiKey,
          model: form.model.trim(),
          providerLabel: form.providerLabel.trim(),
          notes: form.notes.trim(),
        });
        upsertConnector(updated);
        setSelectedConnectorId(updated.id);
        setIsModalOpen(false);
        toast.success(`Updated ${updated.name}`, { className: "industrial-toast" });
      } else {
        const created = await createPlantGenieAIConnector({
          name: form.name.trim(),
          apiKey: form.apiKey.trim(),
          model: form.model.trim(),
          providerLabel: form.providerLabel.trim(),
          notes: form.notes.trim(),
        });
        upsertConnector(created);
        setSelectedConnectorId(created.id);
        setIsModalOpen(false);
        toast.success(`Added ${created.name}`, { className: "industrial-toast" });
      }
      setForm((current) => ({ ...current, apiKey: "" }));
    } catch (error) {
      const message = normalizeConnectorModalError(error);
      setFormError(message);
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (connector: PlantGenieAIConnector): Promise<void> => {
    setDeletingConnectorId(connector.id);
    try {
      const response = await deletePlantGenieAIConnector(connector.id);
      setConnectors((current) => current.filter((item) => item.id !== connector.id));
      if (selectedConnectorId === connector.id) {
        resetToCreateMode();
      }
      setConnectorPendingDelete(null);
      await loadConnectors();
      toast.success(response.message, { className: "industrial-toast" });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Connector deletion failed.";
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setDeletingConnectorId(null);
    }
  };

  const handleTest = async (connector: PlantGenieAIConnector): Promise<void> => {
    setTestingConnectorId(connector.id);
    try {
      const response = await testPlantGenieAIConnector(connector.id);
      upsertConnector(response.connector);
      if (response.success) {
        toast.success(response.message, { className: "industrial-toast" });
      } else {
        toast.error(response.message, { className: "industrial-toast industrial-toast-error" });
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Connector test failed.";
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setTestingConnectorId(null);
    }
  };

  const handleActivate = async (connector: PlantGenieAIConnector): Promise<void> => {
    setActivatingConnectorId(connector.id);
    try {
      const active = await activatePlantGenieAIConnector(connector.id);
      setConnectors((current) =>
        current
          .map((item) => (item.id === active.id ? active : { ...item, is_active: false }))
          .sort((left, right) => {
            if (left.is_active !== right.is_active) {
              return left.is_active ? -1 : 1;
            }
            return right.updated_at.localeCompare(left.updated_at);
          })
      );
      toast.success(`${active.name} is now active`, { className: "industrial-toast" });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Connector activation failed.";
      toast.error(message, { className: "industrial-toast industrial-toast-error" });
    } finally {
      setActivatingConnectorId(null);
    }
  };

  const modalContent = (
    <>
      {isModalOpen ? (
        <div className="modal-backdrop" onClick={closeModal}>
          <div className="modal-card plant-genie-connector-modal" onClick={(event) => event.stopPropagation()}>
            <div className="plant-genie-form-header">
              <div>
                <h3>{isEditing ? "Edit AI Connector" : "Add AI Connector"}</h3>
                <p>
                  {isEditing
                    ? "Update the connector details. Leave API key blank to keep the existing stored secret."
                    : "Enter your own AI API key and optional model details. Provider routing is managed on the server."}
                </p>
              </div>
              <button type="button" className="command-btn" onClick={closeModal} disabled={isSaving}>
                Close
              </button>
            </div>

            <div className="plant-genie-form-grid">
              <label className="plant-genie-field">
                <span>Name</span>
                <input
                  type="text"
                  value={form.name}
                  onChange={(event) => {
                    setForm((current) => ({ ...current, name: event.target.value }));
                    if (formError) {
                      setFormError(null);
                    }
                  }}
                  placeholder="Production AI Connector"
                />
              </label>

              <label className="plant-genie-field">
                <span>API Key</span>
                <input
                  type="password"
                  value={form.apiKey}
                  onChange={(event) => {
                    setForm((current) => ({ ...current, apiKey: event.target.value }));
                    if (formError) {
                      setFormError(null);
                    }
                  }}
                  placeholder={isEditing ? "Leave blank to keep current secret" : "Enter API key"}
                />
              </label>

              <label className="plant-genie-field">
                <span>Model</span>
                <input
                  type="text"
                  value={form.model}
                  onChange={(event) => {
                    setForm((current) => ({ ...current, model: event.target.value }));
                    if (formError) {
                      setFormError(null);
                    }
                  }}
                  placeholder="Optional model identifier"
                />
              </label>

              <label className="plant-genie-field">
                <span>Label</span>
                <input
                  type="text"
                  value={form.providerLabel}
                  onChange={(event) => {
                    setForm((current) => ({ ...current, providerLabel: event.target.value }));
                    if (formError) {
                      setFormError(null);
                    }
                  }}
                  placeholder="Optional label"
                />
              </label>

              <label className="plant-genie-field plant-genie-field-full">
                <span>Notes</span>
                <textarea
                  value={form.notes}
                  onChange={(event) => {
                    setForm((current) => ({ ...current, notes: event.target.value }));
                    if (formError) {
                      setFormError(null);
                    }
                  }}
                  placeholder="Optional notes about this connector"
                  rows={5}
                />
              </label>
            </div>

            <div className="plant-genie-form-help">
              <Shield size={13} />
              <span>Plant Genie uses your own AI connector and API key. API keys are encrypted on the backend and never returned to the browser after save.</span>
            </div>

            {formError ? (
              <div className="plant-genie-inline-alert error">
                <XCircle size={13} />
                <span>{formError}</span>
              </div>
            ) : null}

            <div className="modal-actions plant-genie-modal-actions">
              <button type="button" className="command-btn" onClick={closeModal} disabled={isSaving}>
                Cancel
              </button>
              <button type="button" className="command-btn primary" onClick={() => void handleSubmit()} disabled={isSaving}>
                <CheckCircle2 size={12} />
                <span>{isSaving ? "Saving..." : isEditing ? "Save Changes" : "Create Connector"}</span>
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {connectorPendingDelete ? (
        <div className="modal-backdrop" onClick={closeDeleteDialog}>
          <div className="modal-card plant-genie-confirmation-modal" onClick={(event) => event.stopPropagation()}>
            <h3>Delete AI Connector</h3>
            <p className="plant-genie-confirmation-copy">
              Delete <strong>{connectorPendingDelete.name}</strong>? Plant Genie will stop using this connector until another one is configured and activated.
            </p>
            <div className="modal-actions">
              <button type="button" className="command-btn" onClick={closeDeleteDialog} disabled={deletingConnectorId === connectorPendingDelete.id}>
                Cancel
              </button>
              <button
                type="button"
                className="command-btn danger"
                onClick={() => void handleDelete(connectorPendingDelete)}
                disabled={deletingConnectorId === connectorPendingDelete.id}
              >
                <Trash2 size={12} />
                <span>{deletingConnectorId === connectorPendingDelete.id ? "Deleting..." : "Delete Connector"}</span>
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );

  if (modalOnly) {
    return modalContent;
  }

  return (
    <section className="graph-shell">
      <div className="main-workspace-view billing-settings-view plant-genie-connectors-view">
        <div className="plant-genie-connectors-layout">
          <div className="plant-genie-connectors-card">
            <div className="plant-genie-connectors-header">
              <div>
                <div className="plant-genie-settings-kicker">Settings / AI Connectors</div>
                <h2 className="panel-title">AI Connectors</h2>
                <p className="billing-settings-lead">
                  Configure Plant Genie to use your own AI connector and API key. Add, edit, test, delete, and activate the connector Plant Genie should use.
                </p>
              </div>
              <button type="button" className="command-btn" onClick={openCreateModal}>
                <Plus size={12} />
                <span>Add Connector</span>
              </button>
            </div>

            <div className="plant-genie-connectors-summary">
              <div className="plant-genie-summary-chip is-active">
                <Shield size={12} />
                <span>{activeConnector ? `Plant Genie active connector: ${activeConnector.name}` : "No active Plant Genie connector"}</span>
              </div>
              <div className="plant-genie-summary-chip">
                <PlugZap size={12} />
                <span>{connectors.length} configured</span>
              </div>
            </div>

            {isLoading ? (
              <div className="plant-genie-connectors-empty">Loading connectors...</div>
            ) : connectors.length === 0 ? (
              <div className="plant-genie-connectors-empty">
                No connectors configured yet. Add your own AI connector and API key to enable Plant Genie.
              </div>
            ) : (
              <div className="plant-genie-connector-list">
                {connectors.map((connector) => (
                  <article
                    key={connector.id}
                    className={`plant-genie-connector-item ${selectedConnectorId === connector.id ? "selected" : ""}`}
                  >
                    <button type="button" className="plant-genie-connector-main" onClick={() => setSelectedConnectorId(connector.id)}>
                      <div className="plant-genie-connector-title-row">
                        <strong>{connector.name}</strong>
                        <div className="plant-genie-connector-badges">
                          {connector.is_active ? <span className="plant-genie-badge active">Active</span> : null}
                          <span className={`plant-genie-badge ${connector.health_status}`}>{healthBadgeLabel(connector)}</span>
                        </div>
                      </div>
                      <div className="plant-genie-connector-meta">{formatProviderLabel(connector.provider, connector.provider_label)}</div>
                      {connector.model ? <div className="plant-genie-connector-meta">Model: {connector.model}</div> : null}
                      <div className="plant-genie-connector-status-row">
                        <span>Last tested: {formatLastTested(connector.last_tested_at)}</span>
                        <span>{connector.has_api_key ? "API key stored" : "No API key"}</span>
                      </div>
                      {connector.health_message ? <p className="plant-genie-connector-message">{connector.health_message}</p> : null}
                    </button>

                    <div className="plant-genie-connector-actions">
                      <button type="button" className="command-btn" onClick={() => openEditModal(connector.id)}>
                        <Pencil size={12} />
                        <span>Edit</span>
                      </button>
                      <button
                        type="button"
                        className="command-btn"
                        onClick={() => void handleTest(connector)}
                        disabled={testingConnectorId === connector.id}
                      >
                        <TestTube2 size={12} />
                        <span>{testingConnectorId === connector.id ? "Testing..." : "Test"}</span>
                      </button>
                      <button
                        type="button"
                        className="command-btn"
                        onClick={() => void handleActivate(connector)}
                        disabled={connector.is_active || activatingConnectorId === connector.id}
                      >
                        <CheckCircle2 size={12} />
                        <span>{connector.is_active ? "Active" : activatingConnectorId === connector.id ? "Activating..." : "Activate"}</span>
                      </button>
                      <button
                        type="button"
                        className="command-btn danger"
                        onClick={() => setConnectorPendingDelete(connector)}
                        disabled={deletingConnectorId === connector.id}
                      >
                        <Trash2 size={12} />
                        <span>{deletingConnectorId === connector.id ? "Deleting..." : "Delete"}</span>
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </div>

        </div>

        {modalContent}
      </div>
    </section>
  );
}