import json
from types import SimpleNamespace
import httpx

from backend.agent import ComplianceAgent
from backend.github_client import GitHubClient
from backend.models import ChatTurn, ControlStatus


class FakeModels:
    # Deterministic stub for Gemini generate_content calls.

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        nxt = self._responses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt


def _fake_github() -> GitHubClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/repos/openai/whisper":
            return httpx.Response(200, json={"full_name": "openai/whisper", "default_branch": "main", "html_url": "https://github.com/openai/whisper", "license": {"spdx_id": "MIT", "name": "MIT License", "key": "mit"}})
        return httpx.Response(404)

    return GitHubClient(transport=httpx.MockTransport(handler))


def test_agent_tool_loop_and_structured_synthesis():
    fn_call = SimpleNamespace(name="get_repo_metadata", args={})
    step1 = SimpleNamespace(candidates=[SimpleNamespace(content={"role": "model", "parts": []})], function_calls=[fn_call], text=None)
    step2 = SimpleNamespace(candidates=[SimpleNamespace(content={"role": "model", "parts": []})], function_calls=[], text="Done")

    draft_json = json.dumps(
        {
            "answer": "Whisper uses the MIT license and includes documentation.",
            "overall_summary": "4 controls passed, 1 failed.",
            "controls": [
                {"control_name": "Documentation", "description": "Nonempty README", "status": "PASS", "evidence": ["README.md present"], "source_references": ["https://github.com/openai/whisper/blob/main/README.md"], "explanation": "Found README.md.", "remediation": ""},
                {"control_name": "Licensing", "description": "MIT or Apache 2.0", "status": "PASS", "evidence": ["SPDX: MIT"], "source_references": ["https://github.com/openai/whisper"], "explanation": "MIT license verified.", "remediation": ""},
                {"control_name": "Model Documentation", "description": "Model card", "status": "PASS", "evidence": ["model-card.md present"], "source_references": ["https://github.com/openai/whisper/blob/main/model-card.md"], "explanation": "Found model-card.md.", "remediation": ""},
                {"control_name": "AI Transparency", "description": "Intended use & limitations", "status": "PASS", "evidence": ["Model Use and Limitations sections"], "source_references": ["https://github.com/openai/whisper/blob/main/model-card.md"], "explanation": "Documented clearly.", "remediation": ""},
                {"control_name": "Security", "description": "Security policy", "status": "FAIL", "evidence": ["No SECURITY.md found"], "source_references": ["https://github.com/openai/whisper"], "explanation": "Missing SECURITY.md.", "remediation": "Add SECURITY.md."},
            ],
        }
    )
    step3 = SimpleNamespace(candidates=[], function_calls=[], text=draft_json)

    fake_genai = SimpleNamespace(models=FakeModels([step1, step2, step3]))
    gh = _fake_github()
    agent = ComplianceAgent(github_client=gh, genai_client=fake_genai)
    report = agent.assess("https://github.com/openai/whisper", "Does it use MIT?", history=[ChatTurn(role="user", content="Hi")])

    assert report.repository == "openai/whisper"
    assert len(report.tool_traces) == 1
    assert report.tool_traces[0].tool_name == "get_repo_metadata"
    assert report.tool_traces[0].ok is True
    assert len(report.controls) == 5
    assert report.controls[1].status == ControlStatus.PASS
    assert report.controls[4].status == ControlStatus.FAIL
    gh.close()


def test_agent_llm_failure_returns_unknown_fallback():
    fake_genai = SimpleNamespace(models=FakeModels([RuntimeError("Gemini timeout")]))
    gh = _fake_github()
    agent = ComplianceAgent(github_client=gh, genai_client=fake_genai)
    report = agent.assess("https://github.com/openai/whisper", "Check compliance")

    assert len(report.controls) == 5
    assert all(c.status == ControlStatus.UNKNOWN for c in report.controls)
    assert "Gemini timeout" in report.answer
    gh.close()
