from backend.models import ComplianceReport, ControlResult, ControlStatus, ToolTrace
from backend.policies import DEFAULT_CONTROLS
from backend.report import render_markdown


def test_default_controls_count_and_names():
    names = [c.name for c in DEFAULT_CONTROLS]
    assert names == ["Documentation", "Licensing", "Model Documentation", "AI Transparency", "Security"]


def test_render_markdown_includes_controls_and_traces():
    report = ComplianceReport(
        repository="openai/whisper",
        repository_url="https://github.com/openai/whisper",
        question="Audit repo",
        answer="4 passed, 1 failed.",
        overall_summary="Summary text.",
        controls=[
            ControlResult(
                control_name="Security",
                description="Does the repository contain a security policy?",
                status=ControlStatus.FAIL,
                evidence=["No SECURITY.md found."],
                source_references=["https://github.com/openai/whisper"],
                explanation="Missing policy.",
                remediation="Add SECURITY.md.",
            )
        ],
        tool_traces=[ToolTrace(tool_name="get_repo_metadata", arguments={}, ok=True, summary="Metadata loaded.")],
    )
    md = render_markdown(report)
    assert "# Compliance Report: openai/whisper" in md
    assert "**FAIL**" in md
    assert "Add SECURITY.md." in md
    assert "get_repo_metadata" in md
