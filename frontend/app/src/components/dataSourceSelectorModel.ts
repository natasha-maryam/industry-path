import type { PlantGenieAIBindingTagScope, PlantGeniePlantDataConnector } from "../services/api";

export type DataSourceSelectorValue<Mode extends string = string> = {
  dataSourceConnectorId: string;
  tagScope: PlantGenieAIBindingTagScope;
  selectedTags: string[];
  mode?: Mode;
};

export const TAG_SCOPE_OPTIONS: Array<{ value: PlantGenieAIBindingTagScope; label: string }> = [
  { value: "all", label: "All Tags" },
  { value: "selected", label: "Select Tags" },
];

export const extractConnectorTags = (connector: PlantGeniePlantDataConnector | null): string[] => {
  if (!connector) {
    return [];
  }

  const config = connector.config ?? {};
  const tags = new Set<string>();

  const addTag = (value: unknown): void => {
    const normalized = String(value ?? "").trim();
    if (normalized) {
      tags.add(normalized);
    }
  };

  const addFromMappings = (items: unknown, key: string): void => {
    if (!Array.isArray(items)) {
      return;
    }
    items.forEach((item) => {
      if (item && typeof item === "object") {
        addTag((item as Record<string, unknown>)[key]);
      }
    });
  };

  addFromMappings(config.tag_mappings, "internal_tag");
  addFromMappings(config.tag_mappings, "target_tag");

  const subscriptionConfig = config.subscription_config;
  if (subscriptionConfig && typeof subscriptionConfig === "object") {
    addFromMappings((subscriptionConfig as Record<string, unknown>).nodes, "tag");
  }

  if (Array.isArray(config.node_ids)) {
    config.node_ids.forEach(addTag);
  }

  return Array.from(tags).sort((left, right) => left.localeCompare(right));
};

export const normalizeSelectedTags = (selectedTags: string[], availableTags: string[]): string[] =>
  selectedTags.filter((tag) => availableTags.includes(tag));