from __future__ import annotations

import difflib
import json
import logging
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from git import InvalidGitRepositoryError, Repo

from db.postgres import postgres_client
from models.logic import VersionSnapshotResult
from services.project_service import project_service


class VersionManager:
    """Engineering artifact versioning manager with Git + Dolt backed audit trail."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._dolt_checked = False
        self._dolt_available = False

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _project_paths(self, project_id: str):
        project_service.ensure_project(project_id)
        return project_service.workspace_paths(project_id)

    @staticmethod
    def _safe_copy_file(source: Path, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.exists() and source.is_file():
            shutil.copy2(source, destination)

    @staticmethod
    def _safe_copy_tree(source: Path, destination: Path) -> bool:
        if not source.exists() or not source.is_dir():
            return False
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
        return True

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text()) if path.exists() else {}

    @staticmethod
    def _status_payload(status: str, message: str, source_path: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": status,
            "message": message,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        if source_path:
            payload["source_path"] = source_path
        return payload

    @staticmethod
    def _next_tag_from_history(history: list[dict[str, Any]]) -> str:
        max_version = 0
        for row in history:
            version_tag = str(row.get("version_tag") or "")
            match = re.fullmatch(r"v(\d+)", version_tag)
            if not match:
                continue
            max_version = max(max_version, int(match.group(1)))
        return f"v{max_version + 1}"

    @staticmethod
    def _max_snapshot_version_from_filesystem(snapshots_dir: Path) -> int:
        if not snapshots_dir.exists() or not snapshots_dir.is_dir():
            return 0

        max_version = 0
        for child in snapshots_dir.iterdir():
            if not child.is_dir():
                continue
            match = re.fullmatch(r"v(\d+)", child.name)
            if not match:
                continue
            max_version = max(max_version, int(match.group(1)))
        return max_version

    def _next_version_tag(self, project_id: str) -> str:
        paths = self._project_paths(project_id)
        history = self.get_history(project_id)
        history_tag = self._next_tag_from_history(history)
        history_match = re.fullmatch(r"v(\d+)", history_tag)
        history_next = int(history_match.group(1)) if history_match else 1
        filesystem_max = self._max_snapshot_version_from_filesystem(paths.snapshots)
        return f"v{max(history_next, filesystem_max + 1)}"

    @staticmethod
    def _runtime_state_source(paths) -> Path | None:
        candidates = [
            paths.runtime / "runtime_validation.json",
            paths.runtime / "runtime_state.json",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    @staticmethod
    def _simulation_source(paths) -> Path | None:
        candidates = [
            paths.simulation_models / "virtual_commissioning.json",
            paths.simulation_models / "latest_run.json",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    @staticmethod
    def _io_mapping_source(paths) -> Path | None:
        candidate = paths.io_mapping / "io_mapping_latest.json"
        return candidate if candidate.exists() else None

    def _ensure_dolt_available(self) -> bool:
        if self._dolt_checked:
            return self._dolt_available
        self._dolt_checked = True
        try:
            subprocess.run(["dolt", "--version"], check=True, capture_output=True, text=True)
            self._dolt_available = True
        except Exception:
            self._dolt_available = False
        return self._dolt_available

    def ensure_repo(self, project_id: str) -> dict[str, str]:
        paths = self._project_paths(project_id)
        repo_dir = paths.root / "repo"
        repo_dir.mkdir(parents=True, exist_ok=True)
        try:
            repo = Repo(repo_dir)
        except InvalidGitRepositoryError:
            repo = Repo.init(repo_dir)
            (repo_dir / ".gitignore").write_text(".DS_Store\n")
            repo.git.add(A=True)
            repo.index.commit("Initialize engineering repository")

        with repo.config_writer() as writer:
            writer.set_value("user", "name", "CrossLayerX Bot")
            writer.set_value("user", "email", "crosslayerx-bot@local")

        return {
            "project_id": project_id,
            "repo_path": str(repo_dir),
            "git_dir": str(repo.git_dir),
        }

    def export_plant_graph(self, project_id: str) -> dict[str, Any]:
        paths = self._project_paths(project_id)
        source = paths.plant_graph / "latest_graph.json"
        if source.exists():
            return {
                "exists": True,
                "path": str(source),
                "status": "exported",
            }
        return {
            "exists": False,
            "path": str(source),
            "status": "missing",
            "message": "Validated plant graph export not found.",
        }

    def collect_logic_files(self, project_id: str) -> dict[str, Any]:
        paths = self._project_paths(project_id)
        files = sorted(
            [
                str(file.relative_to(paths.control_logic))
                for file in paths.control_logic.rglob("*")
                if file.is_file()
            ]
        )
        return {
            "exists": len(files) > 0,
            "root": str(paths.control_logic),
            "files": files,
        }

    def collect_io_mapping(self, project_id: str) -> dict[str, Any]:
        paths = self._project_paths(project_id)
        source = self._io_mapping_source(paths)
        return {
            "exists": source is not None,
            "path": str(source) if source else str(paths.io_mapping / "io_mapping_latest.json"),
        }

    def collect_simulation_results(self, project_id: str) -> dict[str, Any]:
        paths = self._project_paths(project_id)
        source = self._simulation_source(paths)
        return {
            "exists": source is not None,
            "path": str(source) if source else str(paths.simulation_models / "latest_run.json"),
        }

    def collect_runtime_state(self, project_id: str) -> dict[str, Any]:
        paths = self._project_paths(project_id)
        source = self._runtime_state_source(paths)
        return {
            "exists": source is not None,
            "path": str(source) if source else str(paths.runtime / "runtime_state.json"),
        }

    def _build_snapshot_directories(self, snapshot_dir: Path) -> dict[str, Path]:
        directories = {
            "plant_graph": snapshot_dir / "plant_graph",
            "control_logic": snapshot_dir / "control_logic",
            "io_mapping": snapshot_dir / "io_mapping",
            "simulation": snapshot_dir / "simulation",
            "runtime": snapshot_dir / "runtime",
            "metadata": snapshot_dir / "metadata",
        }
        for directory in directories.values():
            directory.mkdir(parents=True, exist_ok=True)
        return directories

    def _snapshot_artifacts(self, project_id: str, snapshot_dir: Path) -> dict[str, Any]:
        paths = self._project_paths(project_id)
        directories = self._build_snapshot_directories(snapshot_dir)

        plant_graph_info = self.export_plant_graph(project_id)
        plant_graph_target = directories["plant_graph"] / "plant_graph.json"
        if plant_graph_info["exists"]:
            self._safe_copy_file(Path(str(plant_graph_info["path"])), plant_graph_target)
        else:
            self._write_json(
                directories["plant_graph"] / "status.json",
                self._status_payload("missing", "Plant graph export is not available.", plant_graph_info.get("path")),
            )

        logic_info = self.collect_logic_files(project_id)
        logic_root = Path(str(logic_info["root"]))
        logic_target = directories["control_logic"]
        if logic_info["exists"]:
            self._safe_copy_tree(logic_root, logic_target)
        else:
            self._write_json(
                logic_target / "status.json",
                self._status_payload("missing", "Generated control logic files not found.", str(logic_root)),
            )

        io_info = self.collect_io_mapping(project_id)
        io_target = directories["io_mapping"] / "io_mapping.json"
        io_source = Path(str(io_info["path"]))
        if io_info["exists"] and io_source.exists():
            self._safe_copy_file(io_source, io_target)
        else:
            self._write_json(
                directories["io_mapping"] / "status.json",
                self._status_payload("missing", "IO mapping artifact not found.", str(io_source)),
            )

        simulation_info = self.collect_simulation_results(project_id)
        simulation_target = directories["simulation"] / "simulation_results.json"
        simulation_source = Path(str(simulation_info["path"]))
        if simulation_info["exists"] and simulation_source.exists():
            self._safe_copy_file(simulation_source, simulation_target)
        else:
            self._write_json(
                directories["simulation"] / "status.json",
                self._status_payload(
                    "missing",
                    "Simulation results not available yet. Partial snapshot captured.",
                    str(simulation_source),
                ),
            )

        runtime_info = self.collect_runtime_state(project_id)
        runtime_target = directories["runtime"] / "runtime_state.json"
        runtime_source = Path(str(runtime_info["path"]))
        if runtime_info["exists"] and runtime_source.exists():
            self._safe_copy_file(runtime_source, runtime_target)
        else:
            self._write_json(
                directories["runtime"] / "status.json",
                self._status_payload(
                    "missing",
                    "Runtime state artifact not available yet. Partial snapshot captured.",
                    str(runtime_source),
                ),
            )

        return {
            "plant_graph": str(plant_graph_target) if plant_graph_target.exists() else None,
            "logic_root": str(logic_target),
            "io_mapping": str(io_target) if io_target.exists() else None,
            "simulation": str(simulation_target) if simulation_target.exists() else None,
            "runtime": str(runtime_target) if runtime_target.exists() else None,
            "statuses": {
                "plant_graph": "available" if plant_graph_target.exists() else "missing",
                "control_logic": "available" if logic_info["exists"] else "missing",
                "io_mapping": "available" if io_target.exists() else "missing",
                "simulation": "available" if simulation_target.exists() else "missing",
                "runtime": "available" if runtime_target.exists() else "missing",
            },
        }

    def create_snapshot(self, project_id: str, trigger_source: str, summary: str | None = None) -> dict[str, Any]:
        paths = self._project_paths(project_id)
        version_tag = self._next_version_tag(project_id)
        snapshot_dir = paths.snapshots / version_tag
        while snapshot_dir.exists():
            match = re.fullmatch(r"v(\d+)", version_tag)
            next_number = (int(match.group(1)) if match else 0) + 1
            version_tag = f"v{next_number}"
            snapshot_dir = paths.snapshots / version_tag

        artifacts = self._snapshot_artifacts(project_id, snapshot_dir)
        metadata = {
            "project_id": project_id,
            "version_tag": version_tag,
            "trigger_source": trigger_source,
            "summary": summary or "",
            "created_at": self._now().isoformat(),
            "created_by": "system",
            "snapshot_path": str(snapshot_dir),
            "artifacts": artifacts,
        }
        metadata_path = snapshot_dir / "metadata" / "version_record.json"
        self._write_json(metadata_path, metadata)

        repo_info = self.ensure_repo(project_id)
        repo_snapshot_dir = Path(repo_info["repo_path"]) / "snapshots" / version_tag
        self._safe_copy_tree(snapshot_dir, repo_snapshot_dir)

        return {
            "project_id": project_id,
            "version_tag": version_tag,
            "snapshot_path": str(snapshot_dir),
            "repo_snapshot_path": str(repo_snapshot_dir),
            "trigger_source": trigger_source,
            "summary": summary,
            "statuses": artifacts["statuses"],
        }

    @staticmethod
    def _build_commit_message(trigger_source: str, version_tag: str, summary: str | None = None, simulation_status: str | None = None) -> str:
        lines = [
            "Auto Commit",
            f"Trigger: {trigger_source}",
            f"Plant Model Version: {version_tag}",
            f"Simulation Status: {simulation_status or 'Unknown'}",
            f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
        ]
        if summary:
            lines.append(f"Summary: {summary}")
        return "\n".join(lines)

    @staticmethod
    def _extract_commit_hash(repo: Repo) -> str:
        return repo.head.commit.hexsha

    def write_version_metadata(self, **payload: Any) -> dict[str, Any]:
        record_id = str(uuid4())
        postgres_client.execute(
            """
            INSERT INTO version_records (
                id,
                project_id,
                version_tag,
                commit_hash,
                trigger_source,
                summary,
                plant_graph_path,
                logic_path,
                io_mapping_path,
                simulation_results_path,
                runtime_state_path,
                created_at,
                created_by,
                deployment_tag,
                rollback_available
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                record_id,
                payload["project_id"],
                payload["version_tag"],
                payload["commit_hash"],
                payload["trigger_source"],
                payload.get("summary") or "",
                payload.get("plant_graph_path"),
                payload.get("logic_path"),
                payload.get("io_mapping_path"),
                payload.get("simulation_results_path"),
                payload.get("runtime_state_path"),
                payload.get("created_at") or self._now(),
                payload.get("created_by") or "system",
                payload.get("deployment_tag"),
                bool(payload.get("rollback_available", True)),
            ),
        )
        return {
            "id": record_id,
            **payload,
        }

    def dolt_commit_metadata(self, project_id: str, metadata: dict[str, Any]) -> dict[str, Any]:
        paths = self._project_paths(project_id)
        dolt_root = paths.root / "metadata_dolt"
        dolt_root.mkdir(parents=True, exist_ok=True)

        metadata_file = dolt_root / "version_records" / f"{metadata['version_tag']}.json"
        self._write_json(metadata_file, metadata)

        if not self._ensure_dolt_available():
            return {
                "status": "skipped",
                "reason": "dolt_cli_not_available",
                "path": str(metadata_file),
            }

        try:
            if not (dolt_root / ".dolt").exists():
                subprocess.run(["dolt", "init"], check=True, cwd=dolt_root, capture_output=True, text=True)
            subprocess.run(["dolt", "add", "."], check=True, cwd=dolt_root, capture_output=True, text=True)
            subprocess.run(
                ["dolt", "commit", "-m", f"Version metadata snapshot {metadata['version_tag']}"] ,
                check=True,
                cwd=dolt_root,
                capture_output=True,
                text=True,
            )
            return {
                "status": "committed",
                "path": str(metadata_file),
            }
        except Exception as exc:
            self.logger.warning("Dolt metadata commit failed: project=%s error=%s", project_id, exc)
            return {
                "status": "error",
                "reason": str(exc),
                "path": str(metadata_file),
            }

    def auto_commit(self, project_id: str, trigger_source: str, summary: str | None = None) -> dict[str, Any]:
        snapshot = self.create_snapshot(project_id, trigger_source=trigger_source, summary=summary)
        repo_info = self.ensure_repo(project_id)
        repo_instance = Repo(repo_info["repo_path"])

        repo_instance.git.add(A=True)
        commit_message = self._build_commit_message(
            trigger_source=trigger_source,
            version_tag=snapshot["version_tag"],
            summary=summary,
            simulation_status=snapshot["statuses"].get("simulation", "unknown"),
        )
        commit = repo_instance.index.commit(commit_message)

        try:
            repo_instance.create_tag(snapshot["version_tag"], ref=commit)
        except Exception:
            self.logger.warning("Version tag already exists or could not be created: %s", snapshot["version_tag"])

        metadata_payload = {
            "project_id": project_id,
            "version_tag": snapshot["version_tag"],
            "commit_hash": self._extract_commit_hash(repo_instance),
            "trigger_source": trigger_source,
            "summary": summary or "",
            "plant_graph_path": snapshot["repo_snapshot_path"] + "/plant_graph/plant_graph.json",
            "logic_path": snapshot["repo_snapshot_path"] + "/control_logic",
            "io_mapping_path": snapshot["repo_snapshot_path"] + "/io_mapping/io_mapping.json",
            "simulation_results_path": snapshot["repo_snapshot_path"] + "/simulation/simulation_results.json",
            "runtime_state_path": snapshot["repo_snapshot_path"] + "/runtime/runtime_state.json",
            "created_at": self._now(),
            "created_by": "system",
            "deployment_tag": None,
            "rollback_available": True,
        }
        metadata_record = self.write_version_metadata(**metadata_payload)
        dolt_result = self.dolt_commit_metadata(project_id, metadata_record)

        return {
            "status": "committed",
            "project_id": project_id,
            "version_tag": snapshot["version_tag"],
            "commit_hash": metadata_payload["commit_hash"],
            "snapshot_path": snapshot["snapshot_path"],
            "trigger_source": trigger_source,
            "summary": summary,
            "artifact_status": snapshot["statuses"],
            "metadata_id": metadata_record["id"],
            "dolt": dolt_result,
        }

    def create_deployment_tag(self, project_id: str, version_tag: str) -> dict[str, Any]:
        repo_info = self.ensure_repo(project_id)
        repo = Repo(repo_info["repo_path"])
        deployment_tag = f"deployed_{version_tag}"
        try:
            repo.create_tag(deployment_tag)
        except Exception:
            self.logger.warning("Deployment tag already exists or could not be created: %s", deployment_tag)

        postgres_client.execute(
            """
            UPDATE version_records
            SET deployment_tag = %s
            WHERE project_id = %s
              AND version_tag = %s
            """,
            (deployment_tag, project_id, version_tag),
        )

        return {
            "project_id": project_id,
            "version_tag": version_tag,
            "deployment_tag": deployment_tag,
        }

    def get_history(self, project_id: str) -> list[dict[str, Any]]:
        rows = postgres_client.fetch_all(
            """
            SELECT id::text AS id,
                   project_id::text AS project_id,
                   version_tag,
                   commit_hash,
                   trigger_source,
                   summary,
                   plant_graph_path,
                   logic_path,
                   io_mapping_path,
                   simulation_results_path,
                   runtime_state_path,
                   created_at,
                   created_by,
                   deployment_tag,
                   rollback_available
            FROM version_records
            WHERE project_id = %s
            ORDER BY created_at DESC
            """,
            (project_id,),
        )
        return [dict(row) for row in rows]

    def rollback_to_version(self, project_id: str, version_tag: str) -> dict[str, Any]:
        paths = self._project_paths(project_id)
        snapshot_dir = paths.snapshots / version_tag
        if not snapshot_dir.exists():
            raise ValueError(f"Snapshot version not found: {version_tag}")

        source_map = {
            snapshot_dir / "plant_graph" / "plant_graph.json": paths.plant_graph / "latest_graph.json",
            snapshot_dir / "io_mapping" / "io_mapping.json": paths.io_mapping / "io_mapping_latest.json",
            snapshot_dir / "simulation" / "simulation_results.json": paths.simulation_models / "latest_run.json",
            snapshot_dir / "runtime" / "runtime_state.json": paths.runtime / "runtime_state.json",
        }

        restored_files: list[str] = []
        for source, destination in source_map.items():
            if source.exists():
                self._safe_copy_file(source, destination)
                restored_files.append(str(destination))

        source_logic_dir = snapshot_dir / "control_logic"
        if source_logic_dir.exists():
            if paths.control_logic.exists():
                shutil.rmtree(paths.control_logic)
            shutil.copytree(source_logic_dir, paths.control_logic)

        rollback_commit = self.auto_commit(
            project_id,
            trigger_source="Rollback",
            summary=f"Rollback restored from {version_tag}",
        )

        return {
            "project_id": project_id,
            "rolled_back_to": version_tag,
            "restored_files": restored_files,
            "rollback_commit": rollback_commit,
        }

    def _collect_logic_file_texts(self, snapshot_dir: Path) -> dict[str, str]:
        root = snapshot_dir / "control_logic"
        if not root.exists():
            return {}
        payload: dict[str, str] = {}
        for file in root.rglob("*.st"):
            payload[str(file.relative_to(root))] = file.read_text()
        return payload

    def _metadata_diff(self, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
        keys = sorted(set(left.keys()) | set(right.keys()))
        changes: dict[str, Any] = {}
        for key in keys:
            if left.get(key) == right.get(key):
                continue
            changes[key] = {
                "from": left.get(key),
                "to": right.get(key),
            }
        return changes

    def diff_versions(self, project_id: str, version_a: str, version_b: str) -> dict[str, Any]:
        paths = self._project_paths(project_id)
        dir_a = paths.snapshots / version_a
        dir_b = paths.snapshots / version_b
        if not dir_a.exists() or not dir_b.exists():
            raise ValueError("One or both snapshot versions were not found.")

        meta_a = self._read_json(dir_a / "metadata" / "version_record.json")
        meta_b = self._read_json(dir_b / "metadata" / "version_record.json")
        metadata_diff = self._metadata_diff(meta_a, meta_b)

        logic_a = self._collect_logic_file_texts(dir_a)
        logic_b = self._collect_logic_file_texts(dir_b)

        changed_files = sorted(set(logic_a.keys()) | set(logic_b.keys()))
        logic_diff: dict[str, str] = {}
        for file_name in changed_files:
            if logic_a.get(file_name) == logic_b.get(file_name):
                continue
            lines = difflib.unified_diff(
                (logic_a.get(file_name) or "").splitlines(),
                (logic_b.get(file_name) or "").splitlines(),
                fromfile=f"{version_a}:{file_name}",
                tofile=f"{version_b}:{file_name}",
                lineterm="",
            )
            logic_diff[file_name] = "\n".join(lines)

        return {
            "project_id": project_id,
            "version_a": version_a,
            "version_b": version_b,
            "logic_diff": logic_diff,
            "metadata_diff": metadata_diff,
        }

    def snapshot(self, project_id: str, artifact_paths: list[str]) -> VersionSnapshotResult:
        result = self.auto_commit(
            project_id=project_id,
            trigger_source="Manual Snapshot",
            summary=f"Artifacts: {', '.join(sorted(artifact_paths)) if artifact_paths else 'none'}",
        )

        self.logger.info("Version snapshot created: project=%s snapshot_id=%s", project_id, result["version_tag"])
        return VersionSnapshotResult(
            project_id=project_id,
            snapshot_id=result["version_tag"],
            artifacts=artifact_paths,
            backend="git+dolt",
        )

    def get_version(self, project_id: str, version_tag: str) -> dict[str, Any] | None:
        rows = postgres_client.fetch_all(
            """
            SELECT id::text AS id,
                   project_id::text AS project_id,
                   version_tag,
                   commit_hash,
                   trigger_source,
                   summary,
                   created_at,
                   created_by,
                   deployment_tag,
                   rollback_available
            FROM version_records
            WHERE project_id = %s
              AND version_tag = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (project_id, version_tag),
        )
        return dict(rows[0]) if rows else None


version_manager = VersionManager()
