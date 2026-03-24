import { fireEvent, render, screen } from "@testing-library/react";
import SnapshotManager from "./SnapshotManager";
import type { VersionRecord } from "../../types/versioning";

const makeVersion = (tag: string, rollback = true): VersionRecord => ({
  id: tag,
  project_id: "p1",
  version_tag: tag,
  commit_hash: "abcdef0123456789",
  trigger_source: "Simulation Validation Passed",
  summary: "Validation run",
  created_at: "2026-03-20T10:00:00Z",
  created_by: "system",
  deployment_tag: null,
  rollback_available: rollback,
  plant_graph_path: "/tmp/plant.json",
  logic_path: "/tmp/logic",
  io_mapping_path: "/tmp/io",
  simulation_results_path: "/tmp/sim.json",
  runtime_state_path: null,
  artifact_status: {
    plant_graph: "available",
    control_logic: "available",
    io_mapping: "available",
    simulation: "available",
    runtime: "missing",
  },
});

describe("SnapshotManager", () => {
  test("compare button disabled until exactly two versions selected", () => {
    render(
      <SnapshotManager
        versions={[makeVersion("v1"), makeVersion("v2"), makeVersion("v3")]}
        selectedVersionTags={["v1"]}
        busyAction={null}
        onCreateSnapshot={() => {}}
        onToggleCompareSelection={() => {}}
        onLoadSnapshot={() => {}}
        onRollback={() => {}}
        onCompare={() => {}}
        onExport={() => {}}
      />
    );

    expect(screen.getByRole("button", { name: /Compare Selected Versions/i })).toBeDisabled();
  });

  test("compare button enabled with two selected versions", () => {
    render(
      <SnapshotManager
        versions={[makeVersion("v1"), makeVersion("v2")]}
        selectedVersionTags={["v1", "v2"]}
        busyAction={null}
        onCreateSnapshot={() => {}}
        onToggleCompareSelection={() => {}}
        onLoadSnapshot={() => {}}
        onRollback={() => {}}
        onCompare={() => {}}
        onExport={() => {}}
      />
    );

    expect(screen.getByRole("button", { name: /Compare Selected Versions/i })).toBeEnabled();
  });

  test("rollback action is disabled when rollback unavailable", () => {
    render(
      <SnapshotManager
        versions={[makeVersion("v1", false)]}
        selectedVersionTags={[]}
        busyAction={null}
        onCreateSnapshot={() => {}}
        onToggleCompareSelection={() => {}}
        onLoadSnapshot={() => {}}
        onRollback={() => {}}
        onCompare={() => {}}
        onExport={() => {}}
      />
    );

    expect(screen.getByRole("button", { name: /Rollback/i })).toBeDisabled();
  });

  test("rollback flow dispatches callback", () => {
    const onRollback = vi.fn();
    render(
      <SnapshotManager
        versions={[makeVersion("v1")]}
        selectedVersionTags={[]}
        busyAction={null}
        onCreateSnapshot={() => {}}
        onToggleCompareSelection={() => {}}
        onLoadSnapshot={() => {}}
        onRollback={onRollback}
        onCompare={() => {}}
        onExport={() => {}}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: /Rollback/i }));
    expect(onRollback).toHaveBeenCalledWith(expect.objectContaining({ version_tag: "v1" }));
  });
});
