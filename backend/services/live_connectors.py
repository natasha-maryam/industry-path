from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from services.uns_core import uns_core

try:
    from asyncua import Client as AsyncUAClient  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    AsyncUAClient = None

try:
    import paho.mqtt.client as mqtt  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    mqtt = None


@dataclass
class ConnectorValidationResult:
    ok: bool
    message: str


class LiveConnectorManager:
    def __init__(self) -> None:
        self._timeouts = {
            "opcua_seconds": 4.0,
            "mqtt_seconds": 4.0,
        }

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    async def _validate_opcua_async(self, endpoint: str) -> ConnectorValidationResult:
        if AsyncUAClient is None:
            return ConnectorValidationResult(ok=False, message="asyncua is not installed in this environment.")

        client = AsyncUAClient(url=endpoint)
        try:
            await asyncio.wait_for(client.connect(), timeout=self._timeouts["opcua_seconds"])
            return ConnectorValidationResult(ok=True, message="OPC UA endpoint reachable.")
        except Exception as exc:
            return ConnectorValidationResult(ok=False, message=f"OPC UA connect failed: {exc}")
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass

    def configure_opcua(
        self,
        *,
        endpoint: str,
        security_policy: str | None = None,
        auth_mode: str | None = None,
        username: str | None = None,
    ) -> dict[str, Any]:
        endpoint_value = endpoint.strip()
        if not endpoint_value:
            raise ValueError("OPC UA endpoint is required.")

        validation = asyncio.run(self._validate_opcua_async(endpoint_value))
        payload = {
            "endpoint": endpoint_value,
            "security_policy": security_policy,
            "auth_mode": auth_mode,
            "username": username,
            "validated": validation.ok,
            "validation_message": validation.message,
            "updated_at": self._now(),
        }
        stored = uns_core.set_connector("opcua", payload)
        return {
            "connector": stored,
            "validated": validation.ok,
            "message": validation.message,
        }

    def configure_mqtt(
        self,
        *,
        host: str,
        port: int = 1883,
        client_id: str | None = None,
        topic: str | None = None,
    ) -> dict[str, Any]:
        host_value = host.strip()
        if not host_value:
            raise ValueError("MQTT host is required.")

        if mqtt is None:
            validation = ConnectorValidationResult(ok=False, message="paho-mqtt is not installed in this environment.")
        else:
            client = mqtt.Client(client_id=client_id or "crosslayerx-uns-probe")
            try:
                result = client.connect(host_value, int(port), int(self._timeouts["mqtt_seconds"]))
                if result == 0:
                    validation = ConnectorValidationResult(ok=True, message="MQTT broker reachable.")
                else:
                    validation = ConnectorValidationResult(ok=False, message=f"MQTT connect failed with code {result}.")
            except Exception as exc:
                validation = ConnectorValidationResult(ok=False, message=f"MQTT connect failed: {exc}")
            finally:
                try:
                    client.disconnect()
                except Exception:
                    pass

        payload = {
            "host": host_value,
            "port": int(port),
            "client_id": client_id,
            "topic": topic,
            "validated": validation.ok,
            "validation_message": validation.message,
            "updated_at": self._now(),
        }
        stored = uns_core.set_connector("mqtt", payload)
        return {
            "connector": stored,
            "validated": validation.ok,
            "message": validation.message,
        }

    def configure_api(self, *, endpoint: str, method: str = "GET", headers: dict[str, str] | None = None) -> dict[str, Any]:
        endpoint_value = endpoint.strip()
        if not endpoint_value:
            raise ValueError("API endpoint is required.")

        payload = {
            "endpoint": endpoint_value,
            "method": method.upper() if method else "GET",
            "headers": headers or {},
            "validated": True,
            "validation_message": "API connector metadata stored.",
            "updated_at": self._now(),
        }
        stored = uns_core.set_connector("api", payload)
        return {
            "connector": stored,
            "validated": True,
            "message": "API connector metadata stored.",
        }


live_connector_manager = LiveConnectorManager()
