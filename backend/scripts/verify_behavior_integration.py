from __future__ import annotations

import argparse
import asyncio
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def http_get_json(url: str) -> tuple[int, dict[str, Any] | list[Any] | None, str | None]:
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            status = int(response.getcode() or 0)
            payload = response.read().decode("utf-8")
            parsed = json.loads(payload) if payload else None
            return status, parsed, None
    except urllib.error.HTTPError as exc:
        return int(exc.code), None, f"HTTPError: {exc}"
    except Exception as exc:
        return 0, None, f"Error: {exc}"


def http_post_json(url: str, data: dict[str, Any]) -> tuple[int, dict[str, Any] | list[Any] | None, str | None]:
    body = json.dumps(data).encode("utf-8")
    request = urllib.request.Request(
        url,
        method="POST",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            status = int(response.getcode() or 0)
            payload = response.read().decode("utf-8")
            parsed = json.loads(payload) if payload else None
            return status, parsed, None
    except urllib.error.HTTPError as exc:
        return int(exc.code), None, f"HTTPError: {exc}"
    except Exception as exc:
        return 0, None, f"Error: {exc}"


async def verify_websocket_initial_snapshot(ws_url: str) -> tuple[bool, str]:
    try:
        import websockets  # type: ignore
    except Exception:
        return False, "websockets package missing. Install with: pip install websockets"

    try:
        async with websockets.connect(ws_url, open_timeout=8, close_timeout=4) as socket:
            raw = await asyncio.wait_for(socket.recv(), timeout=8)
            payload = json.loads(raw)
            event_name = str(payload.get("event") or "")
            if event_name != "behavior_snapshot_full":
                return False, f"Unexpected websocket event: {event_name or 'none'}"
            return True, "Received initial behavior_snapshot_full event"
    except Exception as exc:
        return False, f"WebSocket failed: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify CrossLayerX behavior API/websocket integration.")
    parser.add_argument("--base", default="http://127.0.0.1:8000", help="Backend base URL (default: http://127.0.0.1:8000)")
    args = parser.parse_args()

    base = args.base.rstrip("/")
    api_base = f"{base}/api"
    ws_base = base.replace("https://", "wss://").replace("http://", "ws://")

    print(f"[verify] Base: {base}")

    rows_status, rows_payload, rows_err = http_get_json(f"{api_base}/behavior/rows")
    print(f"[verify] GET /api/behavior/rows -> {rows_status}")
    if rows_err:
        print(f"  error: {rows_err}")

    rows = []
    if isinstance(rows_payload, dict):
        data = rows_payload.get("data")
        if isinstance(data, dict):
            maybe_rows = data.get("rows")
            if isinstance(maybe_rows, list):
                rows = [item for item in maybe_rows if isinstance(item, dict)]

    test_tag = str(rows[0].get("tag") or "") if rows else ""

    why_ok = True
    if test_tag:
        why_status, _why_payload, why_err = http_get_json(f"{api_base}/behavior/why/{urllib.parse.quote(test_tag)}")
        print(f"[verify] GET /api/behavior/why/{{tag}} ({test_tag}) -> {why_status}")
        if why_err:
            print(f"  error: {why_err}")
        why_ok = why_status == 200
    else:
        print("[verify] Skipped WHY check: no rows available yet")

    runtime_status, _runtime_payload, runtime_err = http_post_json(f"{api_base}/behavior/runtime-update", {"updates": {}})
    print(f"[verify] POST /api/behavior/runtime-update -> {runtime_status}")
    if runtime_err:
        print(f"  error: {runtime_err}")

    ws_ok, ws_message = asyncio.run(verify_websocket_initial_snapshot(f"{ws_base}/api/ws/behavior"))
    print(f"[verify] WS /api/ws/behavior -> {'ok' if ws_ok else 'failed'}")
    print(f"  detail: {ws_message}")

    checks = [
        rows_status == 200,
        runtime_status == 200,
        why_ok,
        ws_ok,
    ]
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
