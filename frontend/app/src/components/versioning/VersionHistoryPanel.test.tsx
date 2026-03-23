import { fireEvent, render, screen } from "@testing-library/react";
import VersionHistoryPanel from "./VersionHistoryPanel";
import type { VersionRecord } from "../../types/versioning";

const sampleVersion = (tag: string): VersionRecord => ({
  id: tag,
  project_id: "p1",
  version_tag: tag,
  commit_hash: "abcdef0123456789",
  trigger_source: "Control Logic Generated",
  summary: "Generated logic",
  created_at: "2026-03-20T10:00:00Z",
  created_by: "system",
  deployment_tag: null,
  rollback_available: true,
  plant_graph_path: "/tmp/plant.json",
  logic_path: "/tmp/logic",
  io_mapping_path: "/tmp/io",
  simulation_results_path: null,
  runtime_state_path: null,
  artifact_status: {
    plant_graph: "available",
    control_logic: "available",
    io_mapping: "available",
    simulation: "missing",
    runtime: "missing",
  },
});

describe("VersionHistoryPanel", () => {
  test("shows empty history message", () => {
    render(
      <VersionHistoryPanel
        versions={[]}
        selectedVersionTag={null}
        loading={false}
        errorMessage={null}
        onSelectVersion={() => {}}
      />
    );

    expect(
      screen.getByText(/No versions created yet\. Versions will appear after logic generation/i)
    ).toBeInTheDocument();
  });

  test("selecting a version row calls onSelectVersion", () => {
    const onSelectVersion = vi.fn();
    const versions = [sampleVersion("v1"), sampleVersion("v2")];
    render(
      <VersionHistoryPanel
        versions={versions}
        selectedVersionTag={null}
        loading={false}
        errorMessage={null}
        onSelectVersion={onSelectVersion}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: /v2/i }));
    expect(onSelectVersion).toHaveBeenCalledWith(expect.objectContaining({ version_tag: "v2" }));
  });
});
