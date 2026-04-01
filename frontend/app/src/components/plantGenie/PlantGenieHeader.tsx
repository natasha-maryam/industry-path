import PlantGenieIcon from "../icons/PlantGenieIcon";

type PlantGenieHeaderStatus = {
  label: string;
  connected: boolean;
};

type PlantGenieHeaderAction = {
  label: string;
  onClick: () => void;
};

type PlantGenieHeaderProps = {
  description?: string;
  projectName?: string | null;
  selectedTag?: string | null;
  statuses?: PlantGenieHeaderStatus[];
  actions?: PlantGenieHeaderAction[];
};

export default function PlantGenieHeader({ description, projectName, selectedTag, statuses = [], actions = [] }: PlantGenieHeaderProps) {
  return (
    <header className="plant-genie-topbar">
      <div className="plant-genie-topbar-brand">
        <div className="plant-genie-topbar-icon" aria-hidden="true">
          <PlantGenieIcon size={31} />
        </div>
        <div className="plant-genie-topbar-copy">
          <div className="plant-genie-topbar-title-row">
            <h1>Plant Genie</h1>
            <span className="plant-genie-topbar-badge">NEW</span>
          </div>
          {(projectName || selectedTag) ? (
            <div className="plant-genie-topbar-context">
              {projectName ? <span>{projectName}</span> : null}
              {selectedTag ? <span>{selectedTag}</span> : null}
            </div>
          ) : null}
        </div>
      </div>

      <div className="plant-genie-topbar-aside">
        {statuses.length > 0 ? (
          <div className="plant-genie-status-list">
            {statuses.map((status) => (
              <span
                key={status.label}
                className={`plant-genie-status-badge ${status.connected ? "is-connected" : "is-disconnected"}`}
              >
                {status.label}
              </span>
            ))}
          </div>
        ) : null}
        {actions.length > 0 ? (
          <div className="plant-genie-header-actions">
            {actions.map((action) => (
              <button key={action.label} type="button" className="plant-genie-header-action" onClick={action.onClick}>
                {action.label}
              </button>
            ))}
          </div>
        ) : null}
        {description ? <p className="plant-genie-topbar-description">{description}</p> : null}
      </div>
    </header>
  );
}