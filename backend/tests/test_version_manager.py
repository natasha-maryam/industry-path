from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from git import Repo

import services.version_manager as version_manager_module
from services.version_manager import VersionManager


class _FakePostgres:
    def __init__(self) -> None:
        self.version_records: list[dict[str, object]] = []

    def execute(self, sql: str, params: tuple | None = None) -> None:
        if params is None:
            return
        normalized = " ".join(sql.lower().split())
        if "insert into version_records" in normalized:
            self.version_records.append(
                {
                    "id": params[0],
                    "project_id": params[1],
                    "version_tag": params[2],
                    "commit_hash": params[3],
                    "trigger_source": params[4],
                    "summary": params[5],
                    "plant_graph_path": params[6],
                    "logic_path": params[7],
                    "io_mapping_path": params[8],
                    "simulation_results_path": params[9],
                    "runtime_state_path": params[10],
                    "created_at": params[11],
                    "created_by": params[12],
                    "deployment_tag": params[13],
                    "rollback_available": params[14],
                }
            )
            return

        if "update version_records" in normalized and "set deployment_tag" in normalized:
            deployment_tag, project_id, version_tag = params
            for row in self.version_records:
                if row["project_id"] == project_id and row["version_tag"] == version_tag:
                    row["deployment_tag"] = deployment_tag

    def fetch_all(self, sql: str, params: tuple | None = None) -> list[dict[str, object]]:
        normalized = " ".join(sql.lower().split())
        if "from version_records" not in normalized:
            return []

        project_id = str(params[0]) if params else ""
        records = [dict(item) for item in self.version_records if str(item["project_id"]) == project_id]
        records.sort(
            key=lambda item: item.get("created_at") or datetime.fromtimestamp(0, tz=timezone.utc),
            reverse=True,
        )
        return records


class _FakeProjectService:
    def __init__(self, root: Path) -> None:
        self.root = root

    def ensure_project(self, project_id: str) -> None:
        _ = project_id

    def workspace_paths(self, project_id: str):
        project_root = self.root / project_id
        paths = SimpleNamespace(
            root=project_root,
            uploads=project_root / "uploads",
            plant_graph=project_root / "plant_graph",
            control_logic=project_root / "control_logic",
            simulation_models=project_root / "simulation_models",
            io_mapping=project_root / "io_mapping",
            runtime=project_root / "runtime",
            monitoring=project_root / "monitoring",
            snapshots=project_root / "snapshots",
        )
        for directory in (
            paths.root,
            paths.uploads,
            paths.plant_graph,
            paths.control_logic,
            paths.simulation_models,
            paths.io_mapping,
            paths.runtime,
            paths.monitoring,
            paths.snapshots,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        return paths


class VersionManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = Path(self.temp_dir.name)
        self.project_id = "project-123"

        self.fake_postgres = _FakePostgres()
        self.fake_project_service = _FakeProjectService(self.workspace_root)

        self.postgres_patch = patch.object(version_manager_module, "postgres_client", self.fake_postgres)
        self.project_patch = patch.object(version_manager_module, "project_service", self.fake_project_service)
        self.postgres_patch.start()
        self.project_patch.start()

        self.manager = VersionManager()
        self.paths = self.fake_project_service.workspace_paths(self.project_id)
        (self.paths.plant_graph / "latest_graph.json").write_text(json.dumps({"nodes": [], "edges": []}))
        (self.paths.control_logic / "main.st").write_text("PROGRAM Main\nEND_PROGRAM\n")
        (self.paths.io_mapping / "io_mapping_latest.json").write_text(json.dumps({"rows": []}))
        (self.paths.simulation_models / "latest_run.json").write_text(json.dumps({"status": "completed"}))
        (self.paths.runtime / "runtime_state.json").write_text(json.dumps({"runtime": "ok"}))

    def tearDown(self) -> None:
        self.postgres_patch.stop()
        self.project_patch.stop()
        self.temp_dir.cleanup()

    def test_repo_initialization(self) -> None:
        repo_info = self.manager.ensure_repo(self.project_id)
        self.assertTrue((Path(repo_info["repo_path"]) / ".git").exists())

    def test_snapshot_creation(self) -> None:
        snapshot = self.manager.create_snapshot(self.project_id, trigger_source="Test", summary="snapshot")
        snapshot_dir = Path(snapshot["snapshot_path"])
        self.assertTrue((snapshot_dir / "plant_graph" / "plant_graph.json").exists())
        self.assertTrue((snapshot_dir / "control_logic" / "main.st").exists())

    def test_auto_commit(self) -> None:
        result = self.manager.auto_commit(self.project_id, trigger_source="Test Commit", summary="autocommit")
        self.assertEqual(result["status"], "committed")
        self.assertTrue(result["commit_hash"])
        repo = Repo(self.paths.root / "repo")
        self.assertIn(result["version_tag"], [tag.name for tag in repo.tags])

    def test_metadata_record_creation(self) -> None:
        result = self.manager.auto_commit(self.project_id, trigger_source="Metadata", summary="metadata")
        self.assertEqual(len(self.fake_postgres.version_records), 1)
        self.assertEqual(self.fake_postgres.version_records[0]["version_tag"], result["version_tag"])

    def test_rollback_flow(self) -> None:
        first = self.manager.auto_commit(self.project_id, trigger_source="Initial", summary="first")
        (self.paths.control_logic / "main.st").write_text("PROGRAM Main\nX := TRUE;\nEND_PROGRAM\n")
        _ = self.manager.auto_commit(self.project_id, trigger_source="Changed", summary="second")

        rollback = self.manager.rollback_to_version(self.project_id, first["version_tag"])
        restored = (self.paths.control_logic / "main.st").read_text()
        self.assertIn("END_PROGRAM", restored)
        self.assertEqual(rollback["rolled_back_to"], first["version_tag"])

    def test_missing_artifact_handling(self) -> None:
        (self.paths.simulation_models / "latest_run.json").unlink()
        (self.paths.runtime / "runtime_state.json").unlink()

        snapshot = self.manager.create_snapshot(self.project_id, trigger_source="Partial", summary="missing")
        self.assertEqual(snapshot["statuses"]["simulation"], "missing")
        self.assertEqual(snapshot["statuses"]["runtime"], "missing")

    def test_snapshot_tag_skips_existing_filesystem_versions(self) -> None:
        stale_v1 = self.paths.snapshots / "v1"
        stale_v1.mkdir(parents=True, exist_ok=True)

        snapshot = self.manager.create_snapshot(self.project_id, trigger_source="Manual", summary="collision-safe")
        self.assertEqual(snapshot["version_tag"], "v2")
        self.assertTrue((self.paths.snapshots / "v2").exists())

    def test_deployment_tag_creation(self) -> None:
        result = self.manager.auto_commit(self.project_id, trigger_source="Deploy", summary="ready")
        tag_info = self.manager.create_deployment_tag(self.project_id, result["version_tag"])
        repo = Repo(self.paths.root / "repo")
        self.assertIn(tag_info["deployment_tag"], [tag.name for tag in repo.tags])


if __name__ == "__main__":
    unittest.main()
