import { useEffect, useMemo } from "react";

import type { PlantGeniePlantDataConnector } from "../services/api";
import {
  extractConnectorTags,
  normalizeSelectedTags,
  TAG_SCOPE_OPTIONS,
  type DataSourceSelectorValue,
} from "./dataSourceSelectorModel";

type DataSourceSelectorModeOption<Mode extends string = string> = {
  value: Mode;
  label: string;
  disabled?: boolean;
};

type DataSourceSelectorProps<Mode extends string = string> = {
  title: string;
  description?: string;
  subtext?: string;
  emptyStateMessage?: string;
  connectors: PlantGeniePlantDataConnector[];
  isLoading?: boolean;
  value: DataSourceSelectorValue<Mode>;
  onChange: (value: DataSourceSelectorValue<Mode>) => void;
  modeLabel?: string;
  modeOptions?: DataSourceSelectorModeOption<Mode>[];
  notice?: {
    tone?: "neutral" | "error";
    text: string;
  };
  layout?: "card" | "topbar";
};

const EMPTY_STATE_MESSAGE = "No data connected. Go to Data Connectors to add a source.";
const LOADING_STATE_MESSAGE = "Loading saved connection profiles...";

export default function DataSourceSelector<Mode extends string = string>({
  title,
  description,
  subtext,
  emptyStateMessage = EMPTY_STATE_MESSAGE,
  connectors,
  isLoading = false,
  value,
  onChange,
  modeLabel = "Mode",
  modeOptions = [],
  notice,
  layout = "card",
}: DataSourceSelectorProps<Mode>) {
  const selectedConnector = useMemo(
    () => connectors.find((connector) => connector.id === value.dataSourceConnectorId) ?? null,
    [connectors, value.dataSourceConnectorId]
  );
  const availableTags = useMemo(() => extractConnectorTags(selectedConnector), [selectedConnector]);
  const hasModeSelector = modeOptions.length > 0 && value.mode !== undefined;
  const hasConnectors = connectors.length > 0;

  useEffect(() => {
    if (value.dataSourceConnectorId) {
      return;
    }

    if (connectors.length !== 1) {
      return;
    }

    const onlyConnector = connectors[0];

    onChange({
      ...value,
      dataSourceConnectorId: onlyConnector.id,
      selectedTags: normalizeSelectedTags(value.selectedTags, extractConnectorTags(onlyConnector)),
    });
  }, [connectors, onChange, value]);

  useEffect(() => {
    if (!value.dataSourceConnectorId || selectedConnector) {
      return;
    }

    if (connectors.length === 1) {
      const onlyConnector = connectors[0];
      onChange({
        ...value,
        dataSourceConnectorId: onlyConnector.id,
        selectedTags: normalizeSelectedTags(value.selectedTags, extractConnectorTags(onlyConnector)),
      });
      return;
    }

    onChange({
      ...value,
      dataSourceConnectorId: "",
      selectedTags: [],
    });
  }, [connectors, onChange, selectedConnector, value]);

  useEffect(() => {
    if (value.tagScope !== "selected" || value.selectedTags.length === 0) {
      return;
    }

    const normalized = normalizeSelectedTags(value.selectedTags, availableTags);
    if (normalized.length === value.selectedTags.length) {
      return;
    }

    onChange({
      ...value,
      selectedTags: normalized,
    });
  }, [availableTags, onChange, value]);

  const handleConnectorChange = (nextConnectorId: string): void => {
    const nextConnector = connectors.find((connector) => connector.id === nextConnectorId) ?? null;
    const nextAvailableTags = extractConnectorTags(nextConnector);
    onChange({
      ...value,
      dataSourceConnectorId: nextConnectorId,
      selectedTags: normalizeSelectedTags(value.selectedTags, nextAvailableTags),
    });
  };

  const handleTagScopeChange = (nextTagScope: DataSourceSelectorValue<Mode>["tagScope"]): void => {
    onChange({
      ...value,
      tagScope: nextTagScope,
      selectedTags: nextTagScope === "selected" ? normalizeSelectedTags(value.selectedTags, availableTags) : value.selectedTags,
    });
  };

  const toggleTag = (tag: string): void => {
    onChange({
      ...value,
      selectedTags: value.selectedTags.includes(tag)
        ? value.selectedTags.filter((item) => item !== tag)
        : [...value.selectedTags, tag],
    });
  };

  return (
    <section className={`data-source-selector-panel ${layout === "topbar" ? "is-topbar" : "is-card"}`} aria-label={title}>
      <div className="data-source-selector-header">
        <div>
          <p className="data-source-selector-eyebrow">Saved Data Source</p>
          <h3>{title}</h3>
          {description ? <p className="data-source-selector-description">{description}</p> : null}
        </div>
        {selectedConnector ? (
          <div className="data-source-selector-status">
            <span className={`data-source-selector-pill ${selectedConnector.runtime.enabled ? "is-active" : "is-idle"}`}>
              {selectedConnector.runtime.enabled ? "Profile active" : "Profile saved"}
            </span>
            <span className={`data-source-selector-pill ${selectedConnector.health.healthy ? "is-active" : "is-idle"}`}>
              {selectedConnector.health.healthy ? "Healthy" : "Health unknown"}
            </span>
          </div>
        ) : null}
      </div>

      <div className="data-source-selector-grid">
        <label className="data-source-selector-field data-source-selector-field-full">
          <span>Data Source</span>
          <select value={value.dataSourceConnectorId} onChange={(event) => handleConnectorChange(event.target.value)} disabled={isLoading || !hasConnectors}>
            {!hasConnectors ? <option value="">{isLoading ? LOADING_STATE_MESSAGE : emptyStateMessage}</option> : <option value="">Choose saved connection profile</option>}
            {connectors.map((connector) => (
              <option key={connector.id} value={connector.id}>
                {connector.name}
              </option>
            ))}
          </select>
        </label>

        <label className="data-source-selector-field">
          <span>Tag Scope</span>
          <select
            value={value.tagScope}
            onChange={(event) => handleTagScopeChange(event.target.value as DataSourceSelectorValue<Mode>["tagScope"])}
            disabled={isLoading || !hasConnectors}
          >
            {TAG_SCOPE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        {hasModeSelector ? (
          <label className="data-source-selector-field">
            <span>{modeLabel}</span>
            <select value={value.mode} onChange={(event) => onChange({ ...value, mode: event.target.value as Mode })} disabled={isLoading || !hasConnectors}>
              {modeOptions.map((option) => (
                <option key={option.value} value={option.value} disabled={option.disabled}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        ) : null}

        {selectedConnector ? (
          <div className="data-source-selector-meta data-source-selector-field-full">
            <span>{selectedConnector.name}</span>
            <span>{availableTags.length > 0 ? `${availableTags.length} reusable tags available` : "No reusable tag mappings detected yet"}</span>
          </div>
        ) : null}

        {!hasConnectors ? <p className="data-source-selector-empty">{emptyStateMessage}</p> : null}

        {value.tagScope === "selected" ? (
          <div className="data-source-selector-field data-source-selector-field-full">
            <span>Selected Tags</span>
            {availableTags.length === 0 ? (
              <p className="data-source-selector-helper">The selected saved profile does not expose reusable tag mappings yet.</p>
            ) : (
              <div className="data-source-selector-tag-list">
                {availableTags.map((tag) => (
                  <label key={tag} className="data-source-selector-tag-option">
                    <input type="checkbox" checked={value.selectedTags.includes(tag)} onChange={() => toggleTag(tag)} />
                    <span>{tag}</span>
                  </label>
                ))}
              </div>
            )}
          </div>
        ) : null}
      </div>

      {subtext ? <p className="data-source-selector-subtext">{subtext}</p> : null}
      {notice ? <p className={`data-source-selector-notice ${notice.tone === "error" ? "is-error" : "is-neutral"}`}>{notice.text}</p> : null}
    </section>
  );
}