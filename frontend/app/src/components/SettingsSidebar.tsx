import { Bot, Cog, FolderCog, PlugZap, Router } from "lucide-react";

type SettingsNavItemId =
  | "general"
  | "project_settings"
  | "ai_connectors"
  | "runtime_connections"
  | "export_integrations";

type SettingsSidebarProps = {
  activeItem: SettingsNavItemId;
  onSelectItem: (item: SettingsNavItemId) => void;
};

const SETTINGS_ITEMS: Array<{ id: SettingsNavItemId; label: string; Icon: typeof Cog }> = [
  { id: "general", label: "General", Icon: Cog },
  { id: "project_settings", label: "Project Settings", Icon: FolderCog },
  { id: "ai_connectors", label: "AI Connectors", Icon: Bot },
  { id: "runtime_connections", label: "Runtime / Connection Settings", Icon: Router },
  { id: "export_integrations", label: "Export / Integration Settings", Icon: PlugZap },
];

export default function SettingsSidebar({ activeItem, onSelectItem }: SettingsSidebarProps) {
  return (
    <div className="settings-sidebar-nav">
      <h3 className="panel-title">Settings</h3>
      <ul className="settings-nav-list">
        {SETTINGS_ITEMS.map(({ id, label, Icon }) => (
          <li key={id}>
            <button className={`settings-nav-item ${activeItem === id ? "active" : ""}`} type="button" onClick={() => onSelectItem(id)}>
              <Icon size={12} className="tree-node-icon" />
              {label}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
