import SettingsSidebar, { type SettingsNavItemId } from "./SettingsSidebar";

type SidebarModeSettingsProps = {
  activeItem: SettingsNavItemId;
  onSelectItem: (item: SettingsNavItemId) => void;
  showBilling?: boolean;
};

export default function SidebarModeSettings({ activeItem, onSelectItem, showBilling = true }: SidebarModeSettingsProps) {
  return <SettingsSidebar activeItem={activeItem} onSelectItem={onSelectItem} showBilling={showBilling} />;
}
