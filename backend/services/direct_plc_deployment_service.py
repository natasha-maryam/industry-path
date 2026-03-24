from __future__ import annotations

import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from models.direct_plc_deployment import (
    DeploymentAuditRecord,
    DeploymentSafetyValidation,
    DeviceConnectionConfig,
    DirectPLCDeploymentRequest,
    DirectPLCDeploymentResponse,
    RuntimeUploadResult,
    SupportedPLCProtocol,
)
from services.project_service import project_service


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProtocolDriver(ABC):
    protocol: SupportedPLCProtocol

    @abstractmethod
    def validate_connection(self, connection: DeviceConnectionConfig) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def upload_runtime(self, project_id: str, connection: DeviceConnectionConfig) -> RuntimeUploadResult:
        raise NotImplementedError


class StubProtocolDriver(ProtocolDriver):
    def __init__(self, protocol: SupportedPLCProtocol) -> None:
        self.protocol = protocol

    def validate_connection(self, connection: DeviceConnectionConfig) -> list[str]:
        warnings: list[str] = []
        if not connection.plc_address.strip():
            warnings.append("PLC address is empty")
        return warnings

    def upload_runtime(self, project_id: str, connection: DeviceConnectionConfig) -> RuntimeUploadResult:
        return RuntimeUploadResult(
            accepted=False,
            artifact_path=None,
            uploaded_at=_utcnow(),
            message=(
                f"Scaffold mode: protocol '{self.protocol}' deployment transport is not implemented yet "
                f"for target runtime '{connection.target_runtime}' (project={project_id})."
            ),
        )


class DirectPLCDeploymentService:
    def __init__(self) -> None:
        self._drivers: dict[SupportedPLCProtocol, ProtocolDriver] = {
            "opc_ua": StubProtocolDriver("opc_ua"),
            "modbus_tcp": StubProtocolDriver("modbus_tcp"),
            "ethernet_ip": StubProtocolDriver("ethernet_ip"),
            "profinet": StubProtocolDriver("profinet"),
            "mqtt_industrial": StubProtocolDriver("mqtt_industrial"),
        }

    @staticmethod
    def is_enabled() -> bool:
        return os.getenv("DIRECT_PLC_DEPLOYMENT_ENABLED", "false").lower() in {"1", "true", "yes", "on"}

    def _audit_dir(self, project_id: str) -> Path:
        paths = project_service.workspace_paths(project_id)
        root = paths.monitoring / "direct_plc_deployment"
        root.mkdir(parents=True, exist_ok=True)
        return root

    def _write_audit(self, record: DeploymentAuditRecord) -> None:
        root = self._audit_dir(record.project_id)
        file_path = root / f"{record.id}.json"
        file_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        latest = root / "latest.json"
        latest.write_text(record.model_dump_json(indent=2), encoding="utf-8")

    @staticmethod
    def _safety_errors(safety: DeploymentSafetyValidation) -> list[str]:
        errors: list[str] = []
        if not safety.syntax_validation_passed:
            errors.append("Syntax validation has not passed")
        if not safety.logic_verification_passed:
            errors.append("Logic verification has not passed")
        if not safety.io_validation_passed:
            errors.append("IO validation has not passed")
        if not safety.simulation_test_passed:
            errors.append("Simulation test has not passed")
        return errors

    def deploy(self, payload: DirectPLCDeploymentRequest) -> DirectPLCDeploymentResponse:
        project_service.ensure_project(payload.project_id)
        feature_enabled = self.is_enabled()
        driver = self._drivers[payload.connection.protocol]

        warnings = driver.validate_connection(payload.connection)
        safety_errors = self._safety_errors(payload.safety)

        status = "accepted"
        message = "Direct PLC deployment scaffold accepted."
        runtime_upload = RuntimeUploadResult(accepted=False, message="Not attempted")
        errors: list[str] = []

        if not feature_enabled:
            status = "disabled"
            message = "Direct PLC deployment feature flag is disabled by default."
            errors.append("Enable DIRECT_PLC_DEPLOYMENT_ENABLED=true to allow scaffold execution.")
        elif safety_errors:
            status = "blocked"
            message = "Deployment blocked by required safety gates."
            errors.extend(safety_errors)
        else:
            runtime_upload = driver.upload_runtime(payload.project_id, payload.connection)
            status = "accepted"
            message = runtime_upload.message

        audit = DeploymentAuditRecord(
            id=str(uuid4()),
            project_id=payload.project_id,
            requested_at=_utcnow(),
            feature_flag_enabled=feature_enabled,
            status=status,
            connection=payload.connection,
            safety=payload.safety,
            runtime_upload=runtime_upload,
            warnings=warnings,
            errors=errors,
        )
        self._write_audit(audit)

        return DirectPLCDeploymentResponse(status=status, message=message, audit=audit)


direct_plc_deployment_service = DirectPLCDeploymentService()
