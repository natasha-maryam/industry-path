import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class InfluxConfig:
    url: str
    org: str
    bucket: str


class InfluxClient:
    def __init__(self) -> None:
        self.config = InfluxConfig(
            url=os.getenv("INFLUX_URL", "http://localhost:8086"),
            org=os.getenv("INFLUX_ORG", "crosslayerx"),
            bucket=os.getenv("INFLUX_BUCKET", "signals"),
        )

    def health(self) -> dict[str, str]:
        return {
            "backend": "influx",
            "url": self.config.url,
            "bucket": self.config.bucket,
            "status": "configured",
        }

    def get_signal_history(self, tags: list[str], *, points: int = 12) -> list[dict]:
        now = datetime.now(timezone.utc)
        history: list[dict] = []
        normalized = [tag for tag in tags if tag]
        for index, tag in enumerate(normalized):
            for point in range(points):
                timestamp = now - timedelta(minutes=(points - point))
                history.append(
                    {
                        "tag": tag,
                        "timestamp": timestamp.isoformat(),
                        "value": round(10 + index * 2 + point * 0.3, 3),
                        "source": "influx",
                    }
                )
        return history


influx_client = InfluxClient()
