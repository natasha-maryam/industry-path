import os
from dataclasses import dataclass


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
