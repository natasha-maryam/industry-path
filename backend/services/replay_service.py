from datetime import datetime, timedelta, timezone
import json

from services.project_service import project_service


class ReplayService:
    def _events_file(self, project_id: str):
        paths = project_service.workspace_paths(project_id)
        return paths.monitoring / "replay_events.json"

    def get_replay(self, project_id: str, start_minutes_ago: int = 5, points: int = 6) -> dict[str, object]:
        project_service.ensure_project(project_id)

        now = datetime.now(timezone.utc)
        start = now - timedelta(minutes=start_minutes_ago)
        timeline: list[dict[str, object]] = []
        events_file = self._events_file(project_id)
        if events_file.exists():
            all_events = json.loads(events_file.read_text())
            cutoff = start.timestamp()
            for event in all_events:
                raw_ts = event.get("timestamp")
                if not isinstance(raw_ts, str):
                    continue
                try:
                    parsed_ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                except ValueError:
                    continue
                if parsed_ts.timestamp() >= cutoff:
                    timeline.append(event)

        return {
            "project_id": project_id,
            "start": start.isoformat(),
            "end": now.isoformat(),
            "timeline": timeline[:points],
        }


replay_service = ReplayService()
