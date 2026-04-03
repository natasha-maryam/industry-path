from __future__ import annotations

import base64
import json
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import requests

from services.plant_genie_sql_service import plant_genie_sql_service


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class HistorianSample:
    timestamp: datetime
    tag: str
    value: Any
    quality: str | None = None


@dataclass(frozen=True)
class PIBrowseItem:
    web_id: str
    label: str
    path: str
    item_type: str


class PlantGenieHistorianService:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._cache: dict[str, tuple[datetime, Any]] = {}

    def test_connection(self, config: Mapping[str, Any], secrets: Mapping[str, Any]) -> tuple[bool, str]:
        normalized = self._normalize_config(config)
        try:
            if normalized["historian_subtype"] == "osisoft_pi":
                self._browse_pi_assets(normalized, secrets, query=None, limit=1)
                return True, "OSIsoft PI connection succeeded."
            if normalized["generic_mode"] == "sql":
                sql_config, sql_secrets = self._build_sql_request(normalized, secrets)
                return plant_genie_sql_service.test_connection(sql_config, sql_secrets)
            self._fetch_generic_rest_rows(normalized, secrets)
            return True, "Generic time-series REST connection succeeded."
        except Exception as exc:
            return False, str(exc)

    def browse_pi_assets(self, config: Mapping[str, Any], secrets: Mapping[str, Any], *, query: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        normalized = self._normalize_config(config)
        return [item.__dict__ for item in self._browse_pi_assets(normalized, secrets, query=query, limit=limit)]

    def preview_data(self, config: Mapping[str, Any], secrets: Mapping[str, Any]) -> dict[str, Any]:
        samples = self.fetch_runtime_samples(config, secrets)
        rows = [
            {
                "timestamp": sample.timestamp.isoformat(),
                "tag": sample.tag,
                "value": sample.value,
                "quality": sample.quality,
            }
            for sample in samples
        ]
        return {
            "columns": ["timestamp", "tag", "value", "quality"],
            "rows": rows,
            "row_count": len(rows),
        }

    def fetch_runtime_samples(self, config: Mapping[str, Any], secrets: Mapping[str, Any]) -> list[HistorianSample]:
        normalized = self._normalize_config(config)
        if normalized["historian_subtype"] == "osisoft_pi":
            return self._fetch_pi_samples(normalized, secrets)
        if normalized["generic_mode"] == "sql":
            return self._fetch_generic_sql_samples(normalized, secrets)
        return self._fetch_generic_rest_samples(normalized, secrets)

    def _fetch_pi_samples(self, config: Mapping[str, Any], secrets: Mapping[str, Any]) -> list[HistorianSample]:
        start_time, end_time = self._resolve_time_window(config)
        interval = str(config.get("sampling_interval") or "").strip() or None
        max_points = int(config.get("max_data_points") or 500)
        samples: list[HistorianSample] = []
        for mapping in config["tag_mappings"]:
            web_id = str(mapping.get("web_id") or "").strip()
            if not web_id:
                web_id = self._resolve_pi_mapping_webid(config, secrets, mapping)
            endpoint = self._pi_stream_endpoint(str(config["retrieval_mode"]), web_id)
            params = self._pi_retrieval_params(
                retrieval_mode=str(config["retrieval_mode"]),
                start_time=start_time,
                end_time=end_time,
                interval=interval,
                max_points=max_points,
            )
            payload = self._cached_get(
                cache_key=self._cache_key("pi", json.dumps({"endpoint": endpoint, "params": params}, sort_keys=True)),
                enabled=bool(config.get("cache_enabled")),
                loader=lambda: self._pi_request(config, secrets, endpoint, params=params),
            )
            samples.extend(self._parse_pi_payload(payload, internal_tag=str(mapping["internal_tag"])))
        return self._sort_and_trim_samples(samples, max_points)

    def _fetch_generic_sql_samples(self, config: Mapping[str, Any], secrets: Mapping[str, Any]) -> list[HistorianSample]:
        sql_config, sql_secrets = self._build_sql_request(config, secrets)
        preview = plant_genie_sql_service.preview_data(sql_config, sql_secrets, limit=int(config.get("max_data_points") or 500))
        return self._rows_to_samples(
            preview.get("rows", []),
            timestamp_field=str(config["timestamp_field"]),
            tag_field=str(config["tag_field"]),
            value_field=str(config["value_field"]),
        )

    def _fetch_generic_rest_samples(self, config: Mapping[str, Any], secrets: Mapping[str, Any]) -> list[HistorianSample]:
        rows = self._fetch_generic_rest_rows(config, secrets)
        return self._rows_to_samples(
            rows,
            timestamp_field=str(config["timestamp_field"]),
            tag_field=str(config["tag_field"]),
            value_field=str(config["value_field"]),
        )

    def _fetch_generic_rest_rows(self, config: Mapping[str, Any], secrets: Mapping[str, Any]) -> list[dict[str, Any]]:
        start_time, end_time = self._resolve_time_window(config)
        params = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "interval": str(config.get("sampling_interval") or "").strip(),
            "max_points": int(config.get("max_data_points") or 500),
        }
        payload = self._cached_get(
            cache_key=self._cache_key("rest", json.dumps({"url": config["endpoint_url"], "params": params}, sort_keys=True)),
            enabled=bool(config.get("cache_enabled")),
            loader=lambda: self._rest_request(config, secrets, params),
        )
        rows = self._extract_array_path(payload, str(config.get("array_path") or "").strip())
        if not isinstance(rows, list):
            raise ValueError("REST historian response did not resolve to a list of records.")
        return [row for row in rows if isinstance(row, dict)]

    def _build_sql_request(self, config: Mapping[str, Any], secrets: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        return (
            {
                "db_type": config["db_type"],
                "host": config["host"],
                "port": config["port"],
                "database": config["database"],
                "username": config["username"],
                "ssl_enabled": bool(config.get("ssl_enabled")),
                "pool_size": 2,
                "query_mode": "custom_query",
                "refresh_mode": "full_snapshot",
                "custom_query": config["query"],
                "tag_mappings": [{"source_column": config["value_field"], "target_tag": "historian.preview"}],
                "timestamp_column": config["timestamp_field"],
+                "state_column": None,
+                "quality_column": None,
            },
            {"password": str(secrets.get("password") or "")},
        )

    def _rows_to_samples(self, rows: list[dict[str, Any]], *, timestamp_field: str, tag_field: str, value_field: str) -> list[HistorianSample]:
        samples: list[HistorianSample] = []
        for row in rows:
            tag = str(row.get(tag_field) or "").strip()
            if not tag:
                continue
            samples.append(
                HistorianSample(
                    timestamp=self._coerce_datetime(row.get(timestamp_field)),
                    tag=tag,
                    value=row.get(value_field),
                    quality=str(row.get("quality") or "").strip() or None,
                )
            )
        return self._sort_and_trim_samples(samples, len(samples) or 1)

    def _browse_pi_assets(self, config: Mapping[str, Any], secrets: Mapping[str, Any], *, query: str | None, limit: int) -> list[PIBrowseItem]:
        database = self._resolve_pi_database(config, secrets)
        if query:
            payload = self._pi_request(
                config,
                secrets,
                "/search/query",
                params={"q": query, "maxCount": max(limit, 1)},
            )
            items = payload.get("Items") if isinstance(payload, dict) else []
            results: list[PIBrowseItem] = []
            for item in items if isinstance(items, list) else []:
                if not isinstance(item, dict):
                    continue
                web_id = str(item.get("WebId") or "").strip()
                label = str(item.get("Name") or item.get("Path") or web_id).strip()
                path = str(item.get("Path") or label).strip()
                if web_id and label and str(config["af_database"]).lower() in path.lower():
                    results.append(PIBrowseItem(web_id=web_id, label=label, path=path, item_type=str(item.get("ObjectType") or "attribute")))
                if len(results) >= limit:
                    break
            if results:
                return results

        links = database.get("Links") if isinstance(database, dict) else None
        elements_link = str((links or {}).get("Elements") or "")
        if not elements_link:
            return []
        payload = self._pi_request(config, secrets, elements_link, params={"maxCount": max(limit, 1)})
        items = payload.get("Items") if isinstance(payload, dict) else []
        results: list[PIBrowseItem] = []
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict):
                continue
            web_id = str(item.get("WebId") or "").strip()
            label = str(item.get("Name") or web_id).strip()
            path = str(item.get("Path") or label).strip()
            if web_id and label:
                results.append(PIBrowseItem(web_id=web_id, label=label, path=path, item_type="element"))
        return results[:limit]

    def _resolve_pi_mapping_webid(self, config: Mapping[str, Any], secrets: Mapping[str, Any], mapping: Mapping[str, Any]) -> str:
        manual_path = str(mapping.get("manual_path") or "").strip()
        if not manual_path:
            raise ValueError("PI mapping requires either a browsed attribute or a manual path.")
        payload = self._pi_request(config, secrets, "/attributes", params={"path": self._normalize_pi_attribute_path(config, manual_path)})
        web_id = str(payload.get("WebId") or "").strip() if isinstance(payload, dict) else ""
        if not web_id:
            raise ValueError(f"Unable to resolve PI attribute path: {manual_path}")
        return web_id

    def _resolve_pi_database(self, config: Mapping[str, Any], secrets: Mapping[str, Any]) -> dict[str, Any]:
        servers = self._pi_request(config, secrets, "/assetservers")
        items = servers.get("Items") if isinstance(servers, dict) else []
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict):
                continue
            if str(item.get("Name") or "").strip().lower() != str(config["af_server"]).lower():
                continue
            databases_link = str((item.get("Links") or {}).get("AssetDatabases") or "")
            payload = self._pi_request(config, secrets, databases_link)
            databases = payload.get("Items") if isinstance(payload, dict) else []
            for database in databases if isinstance(databases, list) else []:
                if isinstance(database, dict) and str(database.get("Name") or "").strip().lower() == str(config["af_database"]).lower():
                    return database
        raise ValueError("Unable to resolve the configured AF server/database in PI Web API.")

    def _pi_request(self, config: Mapping[str, Any], secrets: Mapping[str, Any], endpoint: str, *, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        session = self._build_pi_session(config, secrets)
        url = self._join_pi_url(str(config["pi_server_url"]), endpoint)
        response = session.get(url, params={key: value for key, value in (params or {}).items() if value not in {None, ""}}, timeout=20)
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {"Items": payload}

    def _rest_request(self, config: Mapping[str, Any], secrets: Mapping[str, Any], params: Mapping[str, Any]) -> Any:
        headers: dict[str, str] = {"Accept": "application/json"}
        auth_mode = str(config.get("authentication_mode") or "anonymous")
        auth = None
        if auth_mode == "basic":
            auth = (str(config.get("username") or ""), str(secrets.get("password") or ""))
        elif auth_mode == "bearer":
            token = str(secrets.get("token") or "").strip()
            if token:
                headers["Authorization"] = f"Bearer {token}"
        response = requests.get(
            str(config["endpoint_url"]),
            params={key: value for key, value in params.items() if value not in {None, ""}},
            headers=headers,
            auth=auth,
            timeout=int(config.get("timeout_ms") or 15000) / 1000.0,
        )
        response.raise_for_status()
        return response.json()

    def _build_pi_session(self, config: Mapping[str, Any], secrets: Mapping[str, Any]) -> requests.Session:
        session = requests.Session()
        session.headers.update({"Accept": "application/json"})
        auth_mode = str(config.get("authentication_mode") or "anonymous")
        if auth_mode == "basic":
            session.auth = (str(config.get("username") or ""), str(secrets.get("password") or ""))
        elif auth_mode == "bearer":
            token = str(secrets.get("token") or "").strip()
            if token:
                session.headers["Authorization"] = f"Bearer {token}"
        elif auth_mode == "basic_header":
            credentials = f"{str(config.get('username') or '')}:{str(secrets.get('password') or '')}"
            session.headers["Authorization"] = f"Basic {base64.b64encode(credentials.encode('utf-8')).decode('ascii')}"
        return session

    def _pi_stream_endpoint(self, retrieval_mode: str, web_id: str) -> str:
        if retrieval_mode == "snapshot":
            return f"/streams/{web_id}/value"
        if retrieval_mode == "recorded":
            return f"/streams/{web_id}/recorded"
        if retrieval_mode == "interpolated":
            return f"/streams/{web_id}/interpolated"
        return f"/streams/{web_id}/summary"

    def _pi_retrieval_params(
        self,
        *,
        retrieval_mode: str,
        start_time: datetime,
        end_time: datetime,
        interval: str | None,
        max_points: int,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "startTime": start_time.isoformat(),
            "endTime": end_time.isoformat(),
            "maxCount": max_points,
        }
        if retrieval_mode == "interpolated" and interval:
            params["interval"] = interval
        if retrieval_mode == "summary":
            params["summaryType"] = "Average"
            params["summaryDuration"] = interval or "1h"
        return params

    def _parse_pi_payload(self, payload: Mapping[str, Any], *, internal_tag: str) -> list[HistorianSample]:
        def flatten_items(value: Any) -> list[dict[str, Any]]:
            if isinstance(value, dict):
                if "Timestamp" in value and "Value" in value:
                    return [value]
                nested = value.get("Items")
                if isinstance(nested, list):
                    rows: list[dict[str, Any]] = []
                    for item in nested:
                        rows.extend(flatten_items(item))
                    return rows
                return []
            if isinstance(value, list):
                rows: list[dict[str, Any]] = []
                for item in value:
                    rows.extend(flatten_items(item))
                return rows
            return []

        rows = flatten_items(payload)
        samples = [
            HistorianSample(
                timestamp=self._coerce_datetime(row.get("Timestamp")),
                tag=internal_tag,
                value=self._unwrap_pi_value(row.get("Value")),
                quality=str(row.get("Good") if row.get("Good") is not None else row.get("Questionable") or "").strip() or None,
            )
            for row in rows
        ]
        return self._sort_and_trim_samples(samples, len(samples) or 1)

    @staticmethod
    def _unwrap_pi_value(value: Any) -> Any:
        if isinstance(value, dict) and "Value" in value:
            return value.get("Value")
        return value

    @staticmethod
    def _extract_array_path(payload: Any, array_path: str) -> Any:
        if not array_path:
            return payload
        current = payload
        for segment in [item for item in array_path.split(".") if item.strip()]:
            if not isinstance(current, dict):
                return []
            current = current.get(segment)
        return current

    def _cached_get(self, *, cache_key: str, enabled: bool, loader) -> Any:  # type: ignore[no-untyped-def]
        if not enabled:
            return loader()
        now = _utc_now()
        with self._lock:
            cached = self._cache.get(cache_key)
            if cached is not None and (now - cached[0]).total_seconds() < 30:
                return cached[1]
        result = loader()
        with self._lock:
            self._cache[cache_key] = (now, result)
        return result

    @staticmethod
    def _cache_key(prefix: str, value: str) -> str:
        return f"{prefix}:{value}"

    @staticmethod
    def _normalize_pi_attribute_path(config: Mapping[str, Any], manual_path: str) -> str:
        if manual_path.startswith("\\"):
            return manual_path
        return f"\\\\{str(config['af_server'])}\\{str(config['af_database'])}\\{manual_path}"

    @staticmethod
    def _join_pi_url(base_url: str, endpoint: str) -> str:
        base = base_url.rstrip("/")
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        return f"{base}/{endpoint.lstrip('/')}"

    @staticmethod
    def _resolve_time_window(config: Mapping[str, Any]) -> tuple[datetime, datetime]:
        now = _utc_now()
        value = int(config.get("time_range_value") or 1)
        unit = str(config.get("time_range_unit") or "hours")
        if unit == "days":
            delta = timedelta(days=value)
        elif unit == "minutes":
            delta = timedelta(minutes=value)
        else:
            delta = timedelta(hours=value)
        return now - delta, now

    @staticmethod
    def _coerce_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
            except Exception:
                pass
        return _utc_now()

    @staticmethod
    def _sort_and_trim_samples(samples: list[HistorianSample], max_points: int) -> list[HistorianSample]:
        ordered = sorted(samples, key=lambda sample: (sample.timestamp, sample.tag))
        if len(ordered) <= max_points:
            return ordered
        return ordered[-max_points:]

    def _normalize_config(self, config: Mapping[str, Any]) -> dict[str, Any]:
        historian_subtype = str(config.get("historian_subtype") or config.get("subtype") or "osisoft_pi").strip().lower()
        if historian_subtype not in {"osisoft_pi", "generic_timeseries"}:
            raise ValueError("config.historian_subtype must be osisoft_pi or generic_timeseries")
        retrieval_mode = str(config.get("retrieval_mode") or "snapshot").strip().lower()
        if retrieval_mode not in {"snapshot", "recorded", "interpolated", "summary"}:
            raise ValueError("config.retrieval_mode must be snapshot, recorded, interpolated, or summary")
        time_range_unit = str(config.get("time_range_unit") or "hours").strip().lower()
        if time_range_unit not in {"minutes", "hours", "days"}:
            raise ValueError("config.time_range_unit must be minutes, hours, or days")
        time_range_value = int(config.get("time_range_value") or 1)
        max_data_points = int(config.get("max_data_points") or 500)
        if time_range_value < 1 or time_range_value > 10000:
            raise ValueError("config.time_range_value must be between 1 and 10000")
        if max_data_points < 1 or max_data_points > 5000:
            raise ValueError("config.max_data_points must be between 1 and 5000")
        normalized: dict[str, Any] = {
            "historian_subtype": historian_subtype,
            "retrieval_mode": retrieval_mode,
            "time_range_value": time_range_value,
            "time_range_unit": time_range_unit,
            "sampling_interval": str(config.get("sampling_interval") or "").strip() or None,
            "poll_interval_ms": int(config.get("poll_interval_ms") or 5000),
            "cache_enabled": bool(config.get("cache_enabled")),
            "max_data_points": max_data_points,
            "authentication_mode": str(config.get("authentication_mode") or "anonymous").strip().lower() or "anonymous",
+            "username": str(config.get("username") or "").strip() or None,
        }
        if historian_subtype == "osisoft_pi":
            pi_server_url = str(config.get("pi_server_url") or config.get("server_url") or "").strip()
            af_server = str(config.get("af_server") or "").strip()
            af_database = str(config.get("af_database") or "").strip()
            if not pi_server_url or not af_server or not af_database:
                raise ValueError("PI server URL, AF Server, and AF Database are required.")
            tag_mappings = self._normalize_pi_tag_mappings(config.get("tag_mappings") or [])
            normalized.update(
                {
                    "pi_server_url": pi_server_url,
                    "af_server": af_server,
                    "af_database": af_database,
                    "tag_mappings": tag_mappings,
                }
            )
            return normalized

        generic_mode = str(config.get("generic_mode") or "sql").strip().lower()
        if generic_mode not in {"sql", "rest"}:
            raise ValueError("config.generic_mode must be sql or rest")
        timestamp_field = str(config.get("timestamp_field") or "timestamp").strip()
        tag_field = str(config.get("tag_field") or "tag").strip()
        value_field = str(config.get("value_field") or "value").strip()
        if not timestamp_field or not tag_field or not value_field:
            raise ValueError("timestamp, tag, and value mappings are required.")
        normalized.update(
            {
                "generic_mode": generic_mode,
                "timestamp_field": timestamp_field,
                "tag_field": tag_field,
                "value_field": value_field,
            }
        )
        if generic_mode == "sql":
            db_type = str(config.get("db_type") or "postgresql").strip().lower()
            if db_type not in {"postgresql", "mysql", "sqlserver"}:
                raise ValueError("config.db_type must be postgresql, mysql, or sqlserver")
            query = str(config.get("query") or "").strip()
            if not query:
                raise ValueError("SQL query is required for generic SQL historian mode.")
            normalized.update(
                {
                    "db_type": db_type,
                    "host": str(config.get("host") or "").strip(),
                    "port": int(config.get("port") or (3306 if db_type == "mysql" else 1433 if db_type == "sqlserver" else 5432)),
                    "database": str(config.get("database") or "").strip(),
                    "username": str(config.get("username") or "").strip(),
                    "ssl_enabled": bool(config.get("ssl_enabled")),
                    "query": query,
                }
            )
            if not normalized["host"] or not normalized["database"] or not normalized["username"]:
                raise ValueError("Host, database, and username are required for generic SQL historian mode.")
            return normalized

        endpoint_url = str(config.get("endpoint_url") or "").strip()
        if not endpoint_url:
            raise ValueError("Endpoint URL is required for generic REST historian mode.")
        normalized.update(
            {
                "endpoint_url": endpoint_url,
                "array_path": str(config.get("array_path") or "").strip() or None,
                "timeout_ms": int(config.get("timeout_ms") or 15000),
            }
        )
        return normalized

    @staticmethod
    def _normalize_pi_tag_mappings(value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list) or not value:
            raise ValueError("At least one PI tag mapping is required.")
        normalized: list[dict[str, Any]] = []
        for item in value:
            if not isinstance(item, Mapping):
                raise ValueError("PI tag mappings must be objects.")
            internal_tag = str(item.get("internal_tag") or item.get("internalTag") or "").strip()
            web_id = str(item.get("web_id") or item.get("webId") or "").strip() or None
            manual_path = str(item.get("manual_path") or item.get("manualPath") or "").strip() or None
            display_path = str(item.get("display_path") or item.get("displayPath") or manual_path or web_id or "").strip() or None
            if not internal_tag:
                raise ValueError("Each PI tag mapping requires an internal tag.")
            if not web_id and not manual_path:
                raise ValueError("Each PI tag mapping requires a browsed attribute or manual path.")
            normalized.append(
                {
                    "internal_tag": internal_tag,
                    "web_id": web_id,
                    "manual_path": manual_path,
                    "display_path": display_path,
                }
            )
        return normalized


plant_genie_historian_service = PlantGenieHistorianService()
