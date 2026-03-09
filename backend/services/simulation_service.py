from datetime import datetime, timezone
import json

from services.project_service import project_service


class SimulationService:
    def _latest_file(self, project_id: str):
        paths = project_service.workspace_paths(project_id)
        return paths.simulation_models / "latest_run.json"

    def run(self, project_id: str) -> dict[str, object]:
        project_service.ensure_project(project_id)
        payload = {
            "project_id": project_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "started",
            "metrics": {},
        }
        self._latest_file(project_id).write_text(json.dumps(payload, indent=2))
        return payload

    def latest(self, project_id: str) -> dict[str, object]:
        project_service.ensure_project(project_id)
        latest_file = self._latest_file(project_id)
        if not latest_file.exists():
            return {"project_id": project_id, "status": "not-run", "metrics": {}}
        return json.loads(latest_file.read_text())


simulation_service = SimulationService()
