import argparse
from pathlib import Path
from dotenv import load_dotenv

from backend.agent import ComplianceAgent
from backend.models import ComplianceReport


def render_markdown(report: ComplianceReport) -> str:
    # Render a ComplianceReport into a clean, readable Markdown document.
    lines = [
        f"# Compliance Report: {report.repository}",
        "",
        f"- **Repository:** [{report.repository}]({report.repository_url})",
        f"- **Question:** {report.question}",
        "",
        "## Answer",
        "",
        report.answer,
        "",
        "## Executive Summary",
        "",
        report.overall_summary,
        "",
        "| Control | Status | Sources |",
        "| --- | --- | --- |",
    ]

    for c in report.controls:
        sources = ", ".join(f"[link]({url})" for url in c.source_references) or "N/A"
        lines.append(f"| {c.control_name} | **{c.status.value}** | {sources} |")

    lines.extend(["", "## Detailed Control Evaluations", ""])
    for c in report.controls:
        lines.extend(
            [
                f"### {c.control_name} — {c.status.value}",
                f"**Description:** {c.description}",
                "",
                f"**Explanation:** {c.explanation}",
                "",
                "**Supporting Evidence:**",
            ]
        )
        lines.extend(f"- {item}" for item in c.evidence) if c.evidence else lines.append("- None retrieved.")
        lines.append("")
        lines.append("**Source References:**")
        lines.extend(f"- {url}" for url in c.source_references) if c.source_references else lines.append("- None")
        if c.remediation:
            lines.extend(["", f"**Recommended Remediation:** {c.remediation}"])
        lines.append("")

    if report.tool_traces:
        lines.extend(["## Agent Evidence Collection Trace", ""])
        for t in report.tool_traces:
            status = "OK" if t.ok else "ERR"
            lines.append(f"- `{t.tool_name}({t.arguments})` [{status}]: {t.summary}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    # CLI entrypoint to run a compliance assessment and optionally write Markdown output.
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    parser = argparse.ArgumentParser(description="Run AI compliance assessment on a GitHub repository.")
    parser.add_argument("repo_url", help="GitHub repository URL or owner/repo shorthand")
    parser.add_argument("--question", default="Run a full compliance assessment across all governance controls.")
    parser.add_argument("--output", help="Optional path to write the Markdown report")
    args = parser.parse_args()

    report = ComplianceAgent().assess(args.repo_url, args.question)
    md = render_markdown(report)
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md, encoding="utf-8")
        print(f"Wrote compliance report to {out_path}")
    else:
        print(md)


if __name__ == "__main__":
    main()
