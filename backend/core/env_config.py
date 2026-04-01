from __future__ import annotations

import logging
import os
from pathlib import Path
from threading import Lock


logger = logging.getLogger(__name__)

_ENV_LOAD_LOCK = Lock()
_ENV_LOADED = False
_ENV_PATH: Path | None = None


def ensure_backend_env_loaded() -> Path | None:
    global _ENV_LOADED, _ENV_PATH

    if _ENV_LOADED:
        return _ENV_PATH

    with _ENV_LOAD_LOCK:
        if _ENV_LOADED:
            return _ENV_PATH

        env_path = Path(__file__).resolve().parents[1] / ".env"
        if env_path.exists() and env_path.is_file():
            for raw_line in env_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                normalized_key = key.strip()
                if not normalized_key:
                    continue
                normalized_value = value.strip().strip('"').strip("'")
                os.environ.setdefault(normalized_key, normalized_value)

            logger.info("Loaded backend environment from %s", env_path)
            _ENV_PATH = env_path
        else:
            logger.warning("Backend environment file not found at %s", env_path)

        _ENV_LOADED = True
        return _ENV_PATH