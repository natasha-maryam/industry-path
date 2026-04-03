from __future__ import annotations

import json
import re
import threading
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from queue import Empty, LifoQueue
from typing import Any

try:
    import psycopg2  # type: ignore
except Exception:  # pragma: no cover
    psycopg2 = None

try:
    import pymysql  # type: ignore
except Exception:  # pragma: no cover
    pymysql = None

try:
    import pytds  # type: ignore
except Exception:  # pragma: no cover
    pytds = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class SQLConnectorSample:
    tag: str
    value: Any
    observed_at: datetime
    quality: str | None = None


class SQLConnectionPool:
    def __init__(self, create_connection, max_size: int) -> None:  # type: ignore[no-untyped-def]
        self._create_connection = create_connection
        self._max_size = max(max_size, 1)
        self._available: LifoQueue[Any] = LifoQueue(maxsize=self._max_size)
        self._created = 0
        self._lock = threading.Lock()

    def _new_connection(self):  # type: ignore[no-untyped-def]
        connection = self._create_connection()
        try:
            connection.autocommit = True
        except Exception:
            pass
        return connection

    def acquire(self):  # type: ignore[no-untyped-def]
        try:
            return self._available.get_nowait()
        except Empty:
            with self._lock:
                if self._created < self._max_size:
                    self._created += 1
                    return self._new_connection()
        return self._available.get()

    def release(self, connection) -> None:  # type: ignore[no-untyped-def]
        try:
            self._available.put_nowait(connection)
        except Exception:
            try:
                connection.close()
            except Exception:
                pass
            with self._lock:
                self._created = max(self._created - 1, 0)

    def discard(self, connection) -> None:  # type: ignore[no-untyped-def]
        try:
            connection.close()
        except Exception:
            pass
        with self._lock:
            self._created = max(self._created - 1, 0)

    def close(self) -> None:
        while True:
            try:
                connection = self._available.get_nowait()
            except Empty:
                break
            try:
                connection.close()
            except Exception:
                pass
        with self._lock:
            self._created = 0


class PlantGenieSQLService:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._pools: dict[str, SQLConnectionPool] = {}

    @contextmanager
    def connection(self, config: Mapping[str, Any], secrets: Mapping[str, Any]) -> Iterator[Any]:
        normalized = self._normalize_connection_config(config, secrets)
        pool = self._get_pool(normalized, secrets)
        connection = pool.acquire()
        try:
            self._ping(connection)
        except Exception:
            pool.discard(connection)
            connection = pool.acquire()
            self._ping(connection)

        try:
            yield connection
            pool.release(connection)
        except Exception:
            pool.discard(connection)
            raise

    def close_pool(self, config: Mapping[str, Any], secrets: Mapping[str, Any]) -> None:
        pool_key = self._pool_key(self._normalize_connection_config(config, secrets), secrets)
        with self._lock:
            pool = self._pools.pop(pool_key, None)
        if pool is not None:
            pool.close()

    def test_connection(self, config: Mapping[str, Any], secrets: Mapping[str, Any]) -> tuple[bool, str]:
        try:
            with self.connection(config, secrets) as connection:
                self._execute(connection, "SELECT 1")
            return True, "SQL connection succeeded."
        except Exception as exc:
            return False, str(exc)

    def list_tables(self, config: Mapping[str, Any], secrets: Mapping[str, Any]) -> list[dict[str, Any]]:
        normalized = self._normalize_connection_config(config, secrets)
        query = self._tables_query(normalized["db_type"])
        with self.connection(normalized, secrets) as connection:
            rows = self._fetch_all(connection, query, tuple(self._system_schemas(normalized["db_type"])))
        return [
            {
                "schema": str(row.get("table_schema") or ""),
                "name": str(row.get("table_name") or ""),
                "label": f"{row.get('table_schema')}.{row.get('table_name')}" if row.get("table_schema") else str(row.get("table_name") or ""),
            }
            for row in rows
            if str(row.get("table_name") or "").strip()
        ]

    def list_columns(self, config: Mapping[str, Any], secrets: Mapping[str, Any], *, table_name: str, table_schema: str | None = None) -> list[dict[str, Any]]:
        normalized = self._normalize_connection_config(config, secrets)
        schema = self._resolve_table_schema(normalized, table_schema)
        with self.connection(normalized, secrets) as connection:
            rows = self._fetch_all(
                connection,
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
                """,
                (schema, table_name),
            )
        return [
            {
                "name": str(row.get("column_name") or ""),
                "data_type": str(row.get("data_type") or "unknown"),
            }
            for row in rows
            if str(row.get("column_name") or "").strip()
        ]

    def preview_data(self, config: Mapping[str, Any], secrets: Mapping[str, Any], *, limit: int = 25) -> dict[str, Any]:
        normalized = self._normalize_sql_connector_config(config, require_query=True, require_mappings=False)
        query = self._build_preview_query(normalized, limit=max(min(limit, 100), 1))
        with self.connection(normalized, secrets) as connection:
            rows = self._fetch_all(connection, query)
        return self._preview_payload(rows)

    def fetch_runtime_samples(self, config: Mapping[str, Any], secrets: Mapping[str, Any]) -> list[SQLConnectorSample]:
        normalized = self._normalize_sql_connector_config(config, require_query=True, require_mappings=False)
        query = self._build_runtime_query(normalized)
        with self.connection(normalized, secrets) as connection:
            rows = self._fetch_all(connection, query)
        return self._normalize_samples(normalized, rows)

    def _get_pool(self, config: Mapping[str, Any], secrets: Mapping[str, Any]) -> SQLConnectionPool:
        pool_key = self._pool_key(config, secrets)
        with self._lock:
            pool = self._pools.get(pool_key)
            if pool is not None:
                return pool
            pool = SQLConnectionPool(lambda: self._create_connection(config, secrets), int(config.get("pool_size") or 5))
            self._pools[pool_key] = pool
            return pool

    @staticmethod
    def _pool_key(config: Mapping[str, Any], secrets: Mapping[str, Any]) -> str:
        payload = {
            "config": dict(config),
            "secrets": {key: "***" if value else "" for key, value in secrets.items()},
        }
        return json.dumps(payload, sort_keys=True, default=str)

    def _create_connection(self, config: Mapping[str, Any], secrets: Mapping[str, Any]):  # type: ignore[no-untyped-def]
        db_type = str(config.get("db_type") or "postgresql")
        host = str(config.get("host") or "").strip()
        port = int(config.get("port") or self._default_port(db_type))
        database = str(config.get("database") or "").strip()
        username = str(config.get("username") or "").strip()
        password = str(secrets.get("password") or "")
        ssl_enabled = bool(config.get("ssl_enabled"))

        if db_type == "postgresql":
            if psycopg2 is None:
                raise RuntimeError("PostgreSQL support is unavailable on the server (missing psycopg2).")
            return psycopg2.connect(
                host=host,
                port=port,
                dbname=database,
                user=username,
                password=password,
                connect_timeout=10,
                sslmode="require" if ssl_enabled else "prefer",
            )

        if db_type == "mysql":
            if pymysql is None:
                raise RuntimeError("MySQL support is unavailable on the server (missing PyMySQL).")
            connect_kwargs: dict[str, Any] = {
                "host": host,
                "port": port,
                "database": database,
                "user": username,
                "password": password,
                "connect_timeout": 10,
                "cursorclass": pymysql.cursors.Cursor,
            }
            if ssl_enabled:
                connect_kwargs["ssl"] = {}
            return pymysql.connect(**connect_kwargs)

        if pytds is None:
            raise RuntimeError("SQL Server support is unavailable on the server (missing python-tds).")
        return pytds.connect(
            server=host,
            port=port,
            database=database,
            user=username,
            password=password,
            login_timeout=10,
            timeout=10,
            pooling=False,
            autocommit=True,
            enc_login_only=not ssl_enabled,
        )

    @staticmethod
    def _execute(connection, query: str, params: tuple[Any, ...] = ()) -> Any:  # type: ignore[no-untyped-def]
        cursor = connection.cursor()
        try:
            cursor.execute(query, params)
            return cursor
        except Exception:
            cursor.close()
            raise

    def _fetch_all(self, connection, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:  # type: ignore[no-untyped-def]
        cursor = self._execute(connection, query, params)
        try:
            rows = cursor.fetchall()
            columns = [str(item[0]) for item in cursor.description or []]
            return [dict(zip(columns, row)) for row in rows]
        finally:
            cursor.close()

    def _ping(self, connection) -> None:  # type: ignore[no-untyped-def]
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        finally:
            cursor.close()

    @staticmethod
    def _default_port(db_type: str) -> int:
        if db_type == "mysql":
            return 3306
        if db_type == "sqlserver":
            return 1433
        return 5432

    @staticmethod
    def _default_schema(db_type: str) -> str:
        if db_type == "sqlserver":
            return "dbo"
        return "public"

    @staticmethod
    def _system_schemas(db_type: str) -> list[str]:
        if db_type == "postgresql":
            return ["pg_catalog", "information_schema"]
        if db_type == "mysql":
            return ["information_schema", "mysql", "performance_schema", "sys"]
        return ["INFORMATION_SCHEMA", "sys"]

    @staticmethod
    def _tables_query(db_type: str) -> str:
        if db_type == "sqlserver":
            return """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE' AND table_schema NOT IN (%s, %s)
            ORDER BY table_schema, table_name
            """
        if db_type == "mysql":
            return """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE' AND table_schema NOT IN (%s, %s, %s, %s)
            ORDER BY table_schema, table_name
            """
        return """
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_type = 'BASE TABLE' AND table_schema NOT IN (%s, %s)
        ORDER BY table_schema, table_name
        """

    def _normalize_connection_config(self, config: Mapping[str, Any], secrets: Mapping[str, Any]) -> dict[str, Any]:
        db_type = str(config.get("db_type") or "postgresql").strip().lower()
        if db_type not in {"postgresql", "mysql", "sqlserver"}:
            raise ValueError("config.db_type must be one of: postgresql, mysql, sqlserver")
        host = str(config.get("host") or "").strip()
        database = str(config.get("database") or "").strip()
        username = str(config.get("username") or "").strip()
        password = str(secrets.get("password") or "").strip()
        if not host or not database or not username or not password:
            raise ValueError("SQL connector requires host, database, username, and password")
        port = int(config.get("port") or self._default_port(db_type))
        pool_size = int(config.get("pool_size") or 5)
        if port <= 0 or port > 65535:
            raise ValueError("config.port must be between 1 and 65535")
        if pool_size < 1 or pool_size > 50:
            raise ValueError("config.pool_size must be between 1 and 50")
        return {
            **dict(config),
            "db_type": db_type,
            "host": host,
            "database": database,
            "username": username,
            "port": port,
            "pool_size": pool_size,
            "ssl_enabled": bool(config.get("ssl_enabled")),
        }

    def _normalize_sql_connector_config(self, config: Mapping[str, Any], require_query: bool, require_mappings: bool) -> dict[str, Any]:
        normalized = self._normalize_connection_config(config, {"password": "placeholder"})
        query_mode = str(config.get("query_mode") or ("custom_query" if config.get("query") else "table")).strip().lower()
        if query_mode not in {"table", "custom_query"}:
            raise ValueError("config.query_mode must be one of: table, custom_query")
        refresh_mode = str(config.get("refresh_mode") or "latest_row").strip().lower()
        if refresh_mode not in {"latest_row", "full_snapshot"}:
            raise ValueError("config.refresh_mode must be one of: latest_row, full_snapshot")
        table_name = str(config.get("table_name") or "").strip() or None
        table_schema = str(config.get("table_schema") or "").strip() or None
        custom_query = str(config.get("custom_query") or config.get("query") or "").strip() or None
        if query_mode == "table" and require_query and not table_name:
            raise ValueError("config.table_name is required when query_mode is table")
        if query_mode == "custom_query" and require_query:
            if not custom_query:
                raise ValueError("config.custom_query is required when query_mode is custom_query")
            if not re.match(r"^select\b", custom_query, re.IGNORECASE):
                raise ValueError("config.custom_query must start with SELECT")
        tag_mappings: list[dict[str, str]] = []
        raw_mappings = config.get("tag_mappings") or []
        if isinstance(raw_mappings, list):
            for item in raw_mappings:
                if not isinstance(item, Mapping):
                    continue
                source_column = str(item.get("source_column") or item.get("sourceColumn") or "").strip()
                target_tag = str(item.get("target_tag") or item.get("targetTag") or "").strip()
                if source_column and target_tag:
                    tag_mappings.append({"source_column": source_column, "target_tag": target_tag})
        if require_mappings and not tag_mappings and not (config.get("tag_column") and config.get("value_column")):
            raise ValueError("config.tag_mappings must include at least one source column to target tag mapping")
        return {
            **normalized,
            "query_mode": query_mode,
            "refresh_mode": refresh_mode,
            "table_name": table_name,
            "table_schema": table_schema,
            "custom_query": custom_query,
            "timestamp_column": str(config.get("timestamp_column") or "").strip() or None,
            "state_column": str(config.get("state_column") or "").strip() or None,
            "quality_column": str(config.get("quality_column") or "").strip() or None,
            "tag_mappings": tag_mappings,
            "tag_column": str(config.get("tag_column") or "").strip() or None,
            "value_column": str(config.get("value_column") or "").strip() or None,
        }

    def _build_preview_query(self, config: Mapping[str, Any], limit: int) -> str:
        if config["query_mode"] == "table":
            return self._build_table_query(config, limit=limit)
        return self._build_custom_query(config, limit=limit)

    def _build_runtime_query(self, config: Mapping[str, Any]) -> str:
        if config["query_mode"] == "table":
            limit = 1 if config["refresh_mode"] == "latest_row" else None
            return self._build_table_query(config, limit=limit)
        limit = 1 if config["refresh_mode"] == "latest_row" else None
        return self._build_custom_query(config, limit=limit)

    def _build_table_query(self, config: Mapping[str, Any], limit: int | None) -> str:
        db_type = str(config["db_type"])
        schema = self._resolve_table_schema(config, str(config.get("table_schema") or "").strip() or None)
        table_name = str(config.get("table_name") or "").strip()
        if not table_name:
            raise ValueError("config.table_name is required")
        quoted_table = self._qualified_table_name(db_type, schema, table_name)
        select_clause = "SELECT *"
        if db_type == "sqlserver" and limit is not None:
            select_clause = f"SELECT TOP {int(limit)} *"
        query = f"{select_clause} FROM {quoted_table}"
        timestamp_column = str(config.get("timestamp_column") or "").strip()
        if timestamp_column:
            query += f" ORDER BY {self._quote_identifier(db_type, timestamp_column)} DESC"
        if db_type != "sqlserver" and limit is not None:
            query += f" LIMIT {int(limit)}"
        return query

    def _build_custom_query(self, config: Mapping[str, Any], limit: int | None) -> str:
        db_type = str(config["db_type"])
        base_query = str(config.get("custom_query") or "").strip()
        if not base_query:
            raise ValueError("config.custom_query is required")
        if limit is None:
            return base_query
        if db_type == "sqlserver":
            return f"SELECT TOP {int(limit)} * FROM ({base_query}) AS preview_rows"
        return f"SELECT * FROM ({base_query}) AS preview_rows LIMIT {int(limit)}"

    def _normalize_samples(self, config: Mapping[str, Any], rows: list[dict[str, Any]]) -> list[SQLConnectorSample]:
        timestamp_column = str(config.get("timestamp_column") or "").strip() or None
        quality_column = str(config.get("quality_column") or "").strip() or None
        state_column = str(config.get("state_column") or "").strip() or None
        tag_mappings = list(config.get("tag_mappings") or [])
        samples: list[SQLConnectorSample] = []

        if tag_mappings:
            for row in rows:
                observed_at = self._coerce_observed_at(row.get(timestamp_column)) if timestamp_column else _utc_now()
                quality_value = row.get(quality_column) if quality_column else row.get(state_column) if state_column else None
                quality = None if quality_value is None else str(quality_value)
                for mapping in tag_mappings:
                    source_column = str(mapping.get("source_column") or "").strip()
                    target_tag = str(mapping.get("target_tag") or "").strip()
                    if not source_column or not target_tag or source_column not in row:
                        continue
                    samples.append(
                        SQLConnectorSample(
                            tag=target_tag,
                            value=row.get(source_column),
                            observed_at=observed_at,
                            quality=quality,
                        )
                    )
            return samples

        tag_column = str(config.get("tag_column") or "").strip()
        value_column = str(config.get("value_column") or "").strip()
        if not tag_column or not value_column:
            return samples
        for row in rows:
            tag = str(row.get(tag_column) or "").strip()
            if not tag:
                continue
            observed_at = self._coerce_observed_at(row.get(timestamp_column)) if timestamp_column else _utc_now()
            quality_value = row.get(quality_column) if quality_column else row.get(state_column) if state_column else None
            quality = None if quality_value is None else str(quality_value)
            samples.append(
                SQLConnectorSample(
                    tag=tag,
                    value=row.get(value_column),
                    observed_at=observed_at,
                    quality=quality,
                )
            )
        return samples

    @staticmethod
    def _coerce_observed_at(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
            except Exception:
                pass
        return _utc_now()

    def _preview_payload(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        columns = list(rows[0].keys()) if rows else []
        return {
            "columns": columns,
            "rows": [self._serialize_row(row) for row in rows],
            "row_count": len(rows),
        }

    def _serialize_row(self, row: Mapping[str, Any]) -> dict[str, Any]:
        return {str(key): self._serialize_value(value) for key, value in row.items()}

    def _serialize_value(self, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return value

    def _resolve_table_schema(self, config: Mapping[str, Any], table_schema: str | None) -> str:
        return str(table_schema or self._default_schema(str(config.get("db_type") or "postgresql")))

    @staticmethod
    def _quote_identifier(db_type: str, name: str) -> str:
        if db_type == "mysql":
            return f"`{name.replace('`', '``')}`"
        if db_type == "sqlserver":
            return f"[{name.replace(']', ']]')}]"
        return f'"{name.replace(chr(34), chr(34) * 2)}"'

    def _qualified_table_name(self, db_type: str, schema: str, table_name: str) -> str:
        return f"{self._quote_identifier(db_type, schema)}.{self._quote_identifier(db_type, table_name)}"


plant_genie_sql_service = PlantGenieSQLService()