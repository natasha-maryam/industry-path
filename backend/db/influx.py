from __future__ import annotations

import logging
import os
import threading
from collections import deque
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

try:
    from influxdb_client import InfluxDBClient as _InfluxDBClient, Point, WritePrecision  # type: ignore
    from influxdb_client.client.write_api import SYNCHRONOUS  # type: ignore
except Exception:  # pragma: no cover
    _InfluxDBClient = None
    Point = None
    WritePrecision = None
    SYNCHRONOUS = None


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class InfluxConfig:
    url: str
    org: str
    bucket: str
    token: str | None


class InfluxClient:
    def __init__(self) -> None:
        self.config = InfluxConfig(
            url=os.getenv("INFLUX_URL", "http://localhost:8086"),
            org=os.getenv("INFLUX_ORG", "crosslayerx"),
            bucket=os.getenv("INFLUX_BUCKET", "signals"),
            token=os.getenv("INFLUX_TOKEN") or None,
        )
        self._lock = threading.RLock()
        self._client: Any | None = None
        self._write_api: Any | None = None
        self._memory_history: deque[dict[str, Any]] = deque(maxlen=5000)

    def health(self) -> dict[str, str]:
        status = "configured"
        if _InfluxDBClient is None:
            status = "fallback-memory"
        else:
            try:
                self._ensure_client()
                if self._client is not None and hasattr(self._client, "ping") and not self._client.ping():
                    status = "unreachable"
            except Exception:
                status = "unreachable"
        return {
            "backend": "influx",
            "url": self.config.url,
            "bucket": self.config.bucket,
            "status": status,
        }

    def write_signal_samples(self, samples: Iterable[Mapping[str, Any]]) -> None:
        normalized = [self._normalize_sample(sample) for sample in samples if str(sample.get("tag") or "").strip()]
        if not normalized:
            return

        with self._lock:
            for sample in normalized:
                self._memory_history.append(sample)

        if _InfluxDBClient is None or Point is None or WritePrecision is None or SYNCHRONOUS is None:
            return

        try:
            self._ensure_client()
            if self._write_api is None:
                return
            self._write_api.write(
                bucket=self.config.bucket,
                org=self.config.org,
                record=[self._to_point(sample) for sample in normalized],
            )
        except Exception:
            logger.debug("Failed to write signal samples to InfluxDB.", exc_info=True)

    def get_signal_history(self, tags: list[str], *, points: int = 12) -> list[dict[str, Any]]:
        normalized_tags = [str(tag).strip() for tag in tags if str(tag).strip()]
        if not normalized_tags:
            return []
        if _InfluxDBClient is not None:
            try:
                remote_rows = self._query_history(normalized_tags, points)
                if remote_rows:
                    return remote_rows
            except Exception:
                logger.debug("Failed to query signal history from InfluxDB.", exc_info=True)
        return self._memory_history_rows(normalized_tags, points)

    def _ensure_client(self) -> None:
        if _InfluxDBClient is None:
            return
        if self._client is not None and self._write_api is not None:
            return
        with self._lock:
            if self._client is not None and self._write_api is not None:
                return
            self._client = _InfluxDBClient(
                url=self.config.url,
                token=self.config.token or "",
                org=self.config.org,
                timeout=5000,
            )
            self._write_api = self._client.write_api(write_options=SYNCHRONOUS)

    def _to_point(self, sample: Mapping[str, Any]):
        point = Point("signals").tag("tag", str(sample["tag"]))
        connector_type = str(sample.get("connector_type") or "").strip()
        if connector_type:
            point = point.tag("connector_type", connector_type)
        quality = str(sample.get("quality") or "").strip()
        if quality:
            point = point.tag("quality", quality)
        point = point.field("value_text", str(sample.get("value_text") or ""))
        numeric_value = sample.get("value_num")
        if isinstance(numeric_value, (int, float)) and not isinstance(numeric_value, bool):
            point = point.field("value_num", float(numeric_value))
        point = point.time(sample["timestamp"], WritePrecision.NS)
        return point

    def _query_history(self, tags: list[str], points: int) -> list[dict[str, Any]]:
        self._ensure_client()
        if self._client is None:
            return []
        escaped_tag_filters = []
        for tag in tags:
            escaped_tag = str(tag).replace('"', '\\"')
            escaped_tag_filters.append(f'r.tag == "{escaped_tag}"')
        escaped_tags = " or ".join(escaped_tag_filters)
        query = f'''
from(bucket: "{self.config.bucket}")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "signals")
  |> filter(fn: (r) => {escaped_tags})
  |> filter(fn: (r) => r._field == "value_text" or r._field == "value_num")
  |> pivot(rowKey:["_time", "tag", "connector_type", "quality"], columnKey:["_field"], valueColumn:"_value")
  |> group(columns:["tag"])
  |> sort(columns:["_time"], desc:true)
  |> limit(n:{max(points, 1)})
  |> sort(columns:["_time"])
'''
        rows: list[dict[str, Any]] = []
        for table in self._client.query_api().query(query=query, org=self.config.org):
            for record in table.records:
                value_num = record.values.get("value_num")
                value_text = record.values.get("value_text")
                value: Any = value_num if value_num is not None else value_text
                rows.append(
                    {
                        "tag": str(record.values.get("tag") or ""),
                        "timestamp": record.get_time().isoformat(),
                        "value": value,
                        "source": "influx",
                    }
                )
        return rows

    def _memory_history_rows(self, tags: list[str], points: int) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = {tag: [] for tag in tags}
        with self._lock:
            for item in reversed(self._memory_history):
                tag = str(item.get("tag") or "")
                if tag in grouped:
                    grouped[tag].append(item)
        rows: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)
        for index, tag in enumerate(tags):
            tag_rows = grouped[tag]
            if not tag_rows:
                for point_index in range(points):
                    timestamp = now - timedelta(minutes=(points - point_index))
                    rows.append(
                        {
                            "tag": tag,
                            "timestamp": timestamp.isoformat(),
                            "value": round(10 + index * 2 + point_index * 0.3, 3),
                            "source": "influx-fallback",
                        }
                    )
                continue
            for item in tag_rows[-points:]:
                rows.append(
                    {
                        "tag": tag,
                        "timestamp": self._coerce_timestamp(item["timestamp"]).isoformat(),
                        "value": item.get("value_num") if item.get("value_num") is not None else item.get("value_text"),
                        "source": "influx-memory",
                    }
                )
        rows.sort(key=lambda row: (str(row["tag"]), str(row["timestamp"])))
        return rows

    @staticmethod
    def _normalize_sample(sample: Mapping[str, Any]) -> dict[str, Any]:
        timestamp = InfluxClient._coerce_timestamp(sample.get("timestamp"))
        value = sample.get("value")
        value_num = None
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            value_num = float(value)
        return {
            "tag": str(sample.get("tag") or "").strip(),
            "timestamp": timestamp,
            "value_num": value_num,
            "value_text": "" if value is None else str(value),
            "connector_type": str(sample.get("connector_type") or "").strip() or None,
            "quality": str(sample.get("quality") or "").strip() or None,
        }

    @staticmethod
    def _coerce_timestamp(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
            except Exception:
                pass
        return datetime.now(timezone.utc)


influx_client = InfluxClient()
