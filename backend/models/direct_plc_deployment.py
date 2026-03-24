from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SupportedPLCProtocol = Literal["opc_ua", "modbus_tcp", "ethernet_ip", "profinet", "mqtt_industrial"]
TargetRuntime = Literal["openplc", "beremiz", "codesys", "siemens_s7", "beckhoff_twincat", "custom"]
DeploymentStatus = Literal["disabled", "blocked", "accepted", "failed"]


class DeviceConnectionConfig(BaseModel):
    plc_address: str = Field(min_length=1)
    protocol: SupportedPLCProtocol
    target_runtime: TargetRuntime
    io_configuration: str = Field(default="", description="Raw IO configuration payload (JSON/text)")


class DeploymentSafetyValidation(BaseModel):
    syntax_validation_passed: bool = False
    logic_verification_passed: bool = False
    io_validation_passed: bool = False
    simulation_test_passed: bool = False

    def all_passed(self) -> bool:
        return (
            self.syntax_validation_passed
            and self.logic_verification_passed
            and self.io_validation_passed
            and self.simulation_test_passed
        )


class RuntimeUploadResult(BaseModel):
    accepted: bool
    artifact_path: str | None = None
    uploaded_at: datetime | None = None
    message: str = ""


class DeploymentAuditRecord(BaseModel):
    id: str
    project_id: str
    requested_at: datetime
    feature_flag_enabled: bool
    status: DeploymentStatus
    connection: DeviceConnectionConfig
    safety: DeploymentSafetyValidation
    runtime_upload: RuntimeUploadResult
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class DirectPLCDeploymentRequest(BaseModel):
    project_id: str
    connection: DeviceConnectionConfig
    safety: DeploymentSafetyValidation


class DirectPLCDeploymentResponse(BaseModel):
    status: DeploymentStatus
    message: str
    audit: DeploymentAuditRecord
