import SettingsSidebar from "./SettingsSidebar";

type SettingsNavItemId =
  | "general"
  | "project_settings"
  | "ai_connectors"
  | "runtime_connections"
  | "export_integrations";

type SidebarModeSettingsProps = {
  activeItem: SettingsNavItemId;
  onSelectItem: (item: SettingsNavItemId) => void;
};

export default function SidebarModeSettings({ activeItem, onSelectItem }: SidebarModeSettingsProps) {
  return <SettingsSidebar activeItem={activeItem} onSelectItem={onSelectItem} />;
}
