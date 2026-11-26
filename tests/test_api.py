from fastapi.testclient import TestClient

from backend import main as api_main
from backend.models import ComplianceReport, ControlResult, ControlStatus


def test_health_and_policies(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    client = TestClient(api_main.app)

    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["gemini_configured"] is True

    policies = client.get("/api/policies")
    assert policies.status_code == 200
    assert len(policies.json()) == 5


def test_assess_endpoint_and_markdown_export(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    sample = ComplianceReport(
        repository="openai/whisper",
        repository_url="https://github.com/openai/whisper",
        question="Check license",
        answer="MIT license found.",
        overall_summary="All good.",
        controls=[
            ControlResult(
                control_name="Licensing",
                description="Approved license",
                status=ControlStatus.PASS,
                evidence=["MIT"],
                source_references=["https://github.com/openai/whisper"],
                explanation="MIT is approved.",
                remediation="",
            )
        ],
    )

    class StubAgent:
        def assess(self, repo_url, question, history=None):
            if "invalid" in repo_url:
                raise ValueError("Invalid GitHub repository format.")
            return sample

    monkeypatch.setattr(api_main, "ComplianceAgent", StubAgent)
    client = TestClient(api_main.app)

    ok_res = client.post("/api/assess", json={"repo_url": "https://github.com/openai/whisper", "question": "Check license"})
    assert ok_res.status_code == 200
    assert ok_res.json()["repository"] == "openai/whisper"

    bad_res = client.post("/api/assess", json={"repo_url": "invalid", "question": "Check"})
    assert bad_res.status_code == 400

    md_res = client.post("/api/report/markdown", json=sample.model_dump())
    assert md_res.status_code == 200
    assert "# Compliance Report: openai/whisper" in md_res.text
