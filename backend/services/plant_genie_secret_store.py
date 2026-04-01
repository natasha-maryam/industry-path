from __future__ import annotations

from base64 import urlsafe_b64encode
from hashlib import sha256
import logging
import os

from cryptography.fernet import Fernet, InvalidToken

from core.env_config import ensure_backend_env_loaded
from services.plant_genie_config_errors import SecretConfigurationError
from services.plant_genie_config import ensure_plant_genie_secret_storage_ready


logger = logging.getLogger(__name__)


class PlantGenieSecretStore:
    def __init__(self) -> None:
        self._fernet: Fernet | None = None

    def encrypt(self, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("api_key is required")
        return self._get_fernet().encrypt(normalized.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str) -> str:
        try:
            return self._get_fernet().decrypt(str(value or "").encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise SecretConfigurationError("Stored Plant Genie connector secret could not be decrypted.") from exc

    def _get_fernet(self) -> Fernet:
        if self._fernet is None:
            self._fernet = Fernet(self._derive_key())
        return self._fernet

    @staticmethod
    def _derive_key() -> bytes:
        ensure_backend_env_loaded()
        ensure_plant_genie_secret_storage_ready(logger=logger, context="runtime")
        seed = (
            os.getenv("PLANT_GENIE_CONNECTOR_SECRET", "").strip()
            or os.getenv("JWT_SECRET", "").strip()
            or os.getenv("POSTGRES_PASSWORD", "").strip()
        )
        return urlsafe_b64encode(sha256(seed.encode("utf-8")).digest())


plant_genie_secret_store = PlantGenieSecretStore()