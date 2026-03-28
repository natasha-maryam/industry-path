import type { ReactNode } from "react";

type MainWorkspaceView = "graph" | "table" | "logic" | "simulation" | "monitoring";

type MainWorkspaceRouterProps = {
  activeView: MainWorkspaceView;
  hasProject: boolean;
  graphView: ReactNode;
  tableView: ReactNode;
  logicView: ReactNode;
  simulationView: ReactNode;
  monitoringView: ReactNode;
};

export default function MainWorkspaceRouter({
  activeView,
  hasProject,
  graphView,
  tableView,
  logicView,
  simulationView,
  monitoringView,
}: MainWorkspaceRouterProps) {
  const renderView = (): ReactNode => {
    if (!hasProject) {
      return <div className="monitor-frame">No project selected. Choose or create a project to open workspace views.</div>;
    }

    if (activeView === "graph") {
      return graphView;
    }
    if (activeView === "table") {
      return tableView;
    }
    if (activeView === "logic") {
      return logicView;
    }
    if (activeView === "simulation") {
      return simulationView;
    }
    return monitoringView;
  };

  return (
    <section className="graph-shell">
      <div className="main-workspace-view">{renderView()}</div>
    </section>
  );
}
