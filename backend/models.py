from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field


class ControlStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class ControlDefinition(BaseModel):
    # Static governance policy definition evaluated by the agent.
    id: str
    name: str
    description: str
    criteria: str


class ControlResult(BaseModel):
    # Evaluation outcome for a single compliance control.
    control_name: str
    description: str
    status: ControlStatus
    evidence: list[str] = Field(default_factory=list)
    source_references: list[str] = Field(default_factory=list)
    explanation: str
    remediation: str = ""


class ToolTrace(BaseModel):
    # Audit record of a single GitHub tool invocation.
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    ok: bool
    summary: str
    source_url: str | None = None


class ChatTurn(BaseModel):
    # Prior conversation turn passed for natural follow-up Q&A.
    role: Literal["user", "assistant"]
    content: str


class AssessRequest(BaseModel):
    # Request body for repository compliance assessment.
    repo_url: str
    question: str = "Run a full compliance assessment across all governance controls."
    history: list[ChatTurn] = Field(default_factory=list)


class ReportDraft(BaseModel):
    # Structured payload synthesized directly by the LLM.
    answer: str
    overall_summary: str
    controls: list[ControlResult]


class ComplianceReport(BaseModel):
    # Complete compliance assessment response returned to clients.
    repository: str
    repository_url: str
    question: str
    answer: str
    overall_summary: str
    controls: list[ControlResult]
    tool_traces: list[ToolTrace] = Field(default_factory=list)
