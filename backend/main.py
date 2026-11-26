import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from backend.agent import ComplianceAgent
from backend.models import AssessRequest, ComplianceReport, ControlDefinition
from backend.policies import DEFAULT_CONTROLS
from backend.report import render_markdown

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

app = FastAPI(title="GitHub Compliance Agent API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    # Report backend and API key configuration status without exposing secrets.
    return {
        "status": "ok",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "github_token_configured": bool(os.getenv("GITHUB_TOKEN")),
        "model": os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
    }


@app.get("/api/policies", response_model=list[ControlDefinition])
def get_policies() -> list[ControlDefinition]:
    # Return the active governance controls evaluated by the agent.
    return DEFAULT_CONTROLS


@app.post("/api/assess", response_model=ComplianceReport)
def assess_repository(req: AssessRequest) -> ComplianceReport:
    # Evaluate a GitHub repository and answer the user's compliance question.
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY is not configured in .env.")
    try:
        return ComplianceAgent().assess(req.repo_url, req.question, req.history)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/report/markdown")
def export_markdown(report: ComplianceReport) -> PlainTextResponse:
    # Render a ComplianceReport payload as downloadable Markdown text.
    return PlainTextResponse(render_markdown(report), media_type="text/markdown")
