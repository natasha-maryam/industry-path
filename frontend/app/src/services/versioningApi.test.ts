import type { VersionRecord } from "../types/versioning";

const { getMock, postMock } = vi.hoisted(() => ({
  getMock: vi.fn(),
  postMock: vi.fn(),
}));

vi.mock("axios", () => ({
  default: {
    create: () => ({
      get: getMock,
      post: postMock,
    }),
  },
}));

import { diffVersions, getVersionHistory, rollbackVersion } from "./versioningApi";

describe("versioningApi", () => {
  beforeEach(() => {
    getMock.mockReset();
    postMock.mockReset();
  });

  test("maps version history response", async () => {
    getMock.mockResolvedValueOnce({
      data: {
        project_id: "p1",
        records: [
          {
            id: "1",
            project_id: "p1",
            version_tag: "v1",
            commit_hash: "abcdef",
            trigger_source: "Control Logic Generated",
            summary: "ok",
            plant_graph_path: "/a",
            logic_path: "/b",
            io_mapping_path: "",
            simulation_results_path: null,
            runtime_state_path: "/c",
            created_at: "2026-03-20T10:00:00Z",
            created_by: "system",
            deployment_tag: null,
            rollback_available: true,
          },
        ],
      },
    });

    const result = await getVersionHistory("p1");
    const first = result[0] as VersionRecord;
    expect(first.version_tag).toBe("v1");
    expect(first.artifact_status.plant_graph).toBe("available");
    expect(first.artifact_status.io_mapping).toBe("missing");
  });

  test("calls diff endpoint with compare params", async () => {
    getMock.mockResolvedValueOnce({
      data: {
        project_id: "p1",
        version_a: "v1",
        version_b: "v2",
        logic_diff: {},
        metadata_diff: {},
      },
    });

    await diffVersions("p1", "v1", "v2");

    expect(getMock).toHaveBeenCalledWith("/versions/v2", {
      params: {
        project_id: "p1",
        compare_to: "v1",
      },
    });
  });

  test("calls rollback endpoint", async () => {
    postMock.mockResolvedValueOnce({ data: { project_id: "p1", rolled_back_to: "v2", restored_files: [], rollback_commit: { status: "committed", project_id: "p1", version_tag: "v3", commit_hash: "abc", snapshot_path: "/tmp", trigger_source: "Rollback" } } });
    await rollbackVersion({ project_id: "p1", version_tag: "v2" });
    expect(postMock).toHaveBeenCalledWith("/versions/rollback", { project_id: "p1", version_tag: "v2" });
  });
});
