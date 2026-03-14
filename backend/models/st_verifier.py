from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


VerificationStatus = Literal["passed", "passed_with_warnings", "failed"]
FileStatus = Literal["passed", "warnings", "failed"]


class STVerifyRequest(BaseModel):
    workspace_path: str


class STVerifierIssue(BaseModel):
    line: int = 0
    column: int = 0
    code: str
    message: str


class STVerifierFileResult(BaseModel):
    file: str
    status: FileStatus
    errors: list[STVerifierIssue] = Field(default_factory=list)
    warnings: list[STVerifierIssue] = Field(default_factory=list)


class STVerifierSummary(BaseModel):
    files_checked: int = 0
    error_count: int = 0
    warning_count: int = 0


class STVerifyResponse(BaseModel):
    status: VerificationStatus
    summary: STVerifierSummary
    files: list[STVerifierFileResult] = Field(default_factory=list)
