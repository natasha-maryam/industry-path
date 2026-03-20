from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ControlLoopDetectRequest(BaseModel):
    project_id: str


class ControlLoopRecord(BaseModel):
    id: str
    project_id: str
    loop_tag: str
    sensor_tag: str
    actuator_tag: str
    process_unit: str | None = None
    controller_tag: str | None = None
    loop_type: str = "feedback"
    control_strategy: str = "PID"
    setpoint_tag: str | None = None
    output_tag: str | None = None
    status: str = "inferred"
    confidence: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
