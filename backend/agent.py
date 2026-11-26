from pathlib import Path
from typing import Any
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import ValidationError

from backend.github_client import GitHubClient, parse_github_url
from backend.models import ChatTurn, ComplianceReport, ControlDefinition, ControlResult, ControlStatus, ReportDraft, ToolTrace
from backend.policies import DEFAULT_CONTROLS, format_policies_for_prompt

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

TOOL_DECLARATIONS = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="get_repo_metadata",
            description="Fetch GitHub repository metadata including default branch, description, and detected SPDX license.",
            parameters=types.Schema(type=types.Type.OBJECT, properties={}),
        ),
        types.FunctionDeclaration(
            name="list_repo_files",
            description="List file paths in the repository using the given branch (default 'main').",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"branch": types.Schema(type=types.Type.STRING, description="Branch name, usually from metadata.")},
            ),
        ),
        types.FunctionDeclaration(
            name="read_repo_file",
            description="Read and decode the text contents of a repository file by path.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"path": types.Schema(type=types.Type.STRING, description="Relative path, e.g. README.md or model-card.md.")},
                required=["path"],
            ),
        ),
        types.FunctionDeclaration(
            name="check_org_security_policy",
            description="Check whether the repository owner has an organization-level SECURITY.md in <owner>/.github.",
            parameters=types.Schema(type=types.Type.OBJECT, properties={}),
        ),
    ]
)


def _summarize_tool_result(result: dict[str, Any]) -> str:
    # Build a short human-readable summary of a tool call outcome.
    if not result.get("ok"):
        return result.get("error") or "Tool call failed."
    data = result.get("data")
    if isinstance(data, dict):
        if "files" in data:
            return f"Listed {len(data['files'])} paths (total {data.get('total_files', len(data['files']))})."
        if "content" in data:
            return f"Read {data.get('path', 'file')} ({len(data['content'])} chars)."
        if "found" in data:
            return "Found org-level security policy." if data["found"] else "No org-level security policy found."
        if "full_name" in data:
            lic = (data.get("license") or {}).get("spdx_id") or "None"
            return f"Metadata loaded (branch={data.get('default_branch')}, license={lic})."
    return "Success."


class ComplianceAgent:
    # Gemini-powered agent that gathers GitHub evidence via tools and synthesizes a compliance report.

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        github_client: GitHubClient | None = None,
        genai_client: Any | None = None,
        controls: list[ControlDefinition] | None = None,
        max_steps: int = 8,
    ) -> None:
        import os

        self.controls = controls or DEFAULT_CONTROLS
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        self.max_steps = max_steps
        self._owns_github = github_client is None
        self.github = github_client or GitHubClient(token=os.getenv("GITHUB_TOKEN") or None)

        if genai_client is not None:
            self.genai = genai_client
        else:
            key = api_key or os.getenv("GEMINI_API_KEY")
            if not key:
                raise RuntimeError("GEMINI_API_KEY is not configured. Set it in .env or environment variables.")
            self.genai = genai.Client(api_key=key)

    def _build_system_instruction(self, owner: str, repo: str) -> str:
        # Compose concise governance rules and evidence standards for Gemini.
        policies = format_policies_for_prompt(self.controls)
        return (
            f"You are an AI governance compliance auditor inspecting GitHub repository '{owner}/{repo}'.\n"
            "Evaluate ALL of the following controls using ONLY evidence retrieved from the provided GitHub tools:\n"
            f"{policies}\n\n"
            "Rules:\n"
            "- Start by calling get_repo_metadata and list_repo_files, then read relevant files (README, LICENSE, model card, SECURITY.md).\n"
            "- If no repo-level security policy exists, call check_org_security_policy.\n"
            "- PASS: Required artifact/content is directly verified in retrieved metadata or files.\n"
            "- FAIL: Repository was inspected successfully and the required artifact/content is confirmed absent or non-compliant.\n"
            "- UNKNOWN: Evidence could not be retrieved or verified due to API errors, rate limits, 404 repo, or unreadable files.\n"
            "- Cite exact quotes/facts and exact source_url values returned by tools. Never invent URLs or evidence.\n"
            "- Directly answer the user's question in `answer` while completing all 5 control evaluations."
        )

    def _execute_tool(self, owner: str, repo: str, name: str, args: dict[str, Any]) -> tuple[dict[str, Any], ToolTrace]:
        # Dispatch a Gemini tool call to GitHubClient and record a ToolTrace.
        if name == "get_repo_metadata":
            res = self.github.get_repo_metadata(owner, repo)
        elif name == "list_repo_files":
            res = self.github.list_repo_files(owner, repo, branch=str(args.get("branch") or "main"))
        elif name == "read_repo_file":
            res = self.github.read_repo_file(owner, repo, path=str(args.get("path") or ""))
        elif name == "check_org_security_policy":
            res = self.github.check_org_security_policy(owner)
        else:
            res = {"ok": False, "source_url": f"https://github.com/{owner}/{repo}", "data": None, "error": f"Unknown tool: {name}"}

        trace = ToolTrace(
            tool_name=name,
            arguments=args,
            ok=bool(res.get("ok")),
            summary=_summarize_tool_result(res),
            source_url=res.get("source_url"),
        )
        return res, trace

    def _fallback_report(self, owner: str, repo: str, question: str, reason: str, traces: list[ToolTrace]) -> ComplianceReport:
        # Return a safe UNKNOWN report when LLM or API orchestration fails.
        repo_url = f"https://github.com/{owner}/{repo}"
        controls = [
            ControlResult(
                control_name=c.name,
                description=c.description,
                status=ControlStatus.UNKNOWN,
                evidence=[],
                source_references=[repo_url],
                explanation=f"Unable to complete automated evaluation: {reason}",
                remediation="Verify network connectivity, API keys, and GitHub rate limits, then retry.",
            )
            for c in self.controls
        ]
        return ComplianceReport(
            repository=f"{owner}/{repo}",
            repository_url=repo_url,
            question=question,
            answer=f"Assessment could not be completed due to an error: {reason}",
            overall_summary=f"Compliance evaluation incomplete ({reason}). All controls marked UNKNOWN.",
            controls=controls,
            tool_traces=traces,
        )

    def assess(self, repo_url: str, question: str, history: list[ChatTurn] | None = None) -> ComplianceReport:
        # Run tool-assisted evidence collection followed by structured JSON synthesis.
        owner, repo = parse_github_url(repo_url)
        full_url = f"https://github.com/{owner}/{repo}"
        system_instruction = self._build_system_instruction(owner, repo)
        traces: list[ToolTrace] = []

        contents: list[types.Content] = []
        for turn in (history or [])[-6:]:
            role = "model" if turn.role == "assistant" else "user"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=turn.content)]))

        user_prompt = (
            f"Target Repository: {full_url}\n"
            f"User Question: {question}\n"
            "Gather the necessary repository evidence using your tools."
        )
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)]))

        try:
            # Phase 1: Iterative tool-calling loop to gather repository evidence.
            for _ in range(self.max_steps):
                response = self.genai.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        tools=[TOOL_DECLARATIONS],
                        temperature=0.1,
                    ),
                )
                if response.candidates and response.candidates[0].content:
                    contents.append(response.candidates[0].content)

                calls = getattr(response, "function_calls", None) or []
                if not calls:
                    break

                fn_parts: list[types.Part] = []
                for call in calls:
                    args = dict(call.args) if call.args else {}
                    res, trace = self._execute_tool(owner, repo, call.name, args)
                    traces.append(trace)
                    fn_parts.append(types.Part.from_function_response(name=call.name, response={"result": res}))
                contents.append(types.Content(role="user", parts=fn_parts))

            # Phase 2: Synthesize validated structured report from collected evidence.
            synthesis_prompt = (
                "Now synthesize the final compliance report JSON matching the required schema. "
                "Include all 5 controls in order (Documentation, Licensing, Model Documentation, AI Transparency, Security), "
                "cite exact retrieved source_url links, and directly answer the user's question."
            )
            contents.append(types.Content(role="user", parts=[types.Part.from_text(text=synthesis_prompt)]))

            final_resp = self.genai.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=ReportDraft,
                    temperature=0.0,
                ),
            )
            draft = ReportDraft.model_validate_json(final_resp.text)
            return ComplianceReport(
                repository=f"{owner}/{repo}",
                repository_url=full_url,
                question=question,
                answer=draft.answer,
                overall_summary=draft.overall_summary,
                controls=draft.controls,
                tool_traces=traces,
            )
        except (ValidationError, ValueError, RuntimeError, Exception) as exc:
            return self._fallback_report(owner, repo, question, str(exc), traces)
        finally:
            if self._owns_github:
                self.github.close()
