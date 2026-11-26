import { ChatTurn, ComplianceReport, ControlDefinition, HealthStatus } from "./types";

export async function fetchHealth(): Promise<HealthStatus> {
  // Check backend health and Gemini configuration status.
  const res = await fetch("/api/health");
  if (!res.ok) throw new Error(`Health check failed (${res.status})`);
  return res.json();
}

export async function fetchPolicies(): Promise<ControlDefinition[]> {
  // Load active governance controls from the backend policy registry.
  const res = await fetch("/api/policies");
  if (!res.ok) throw new Error(`Policies fetch failed (${res.status})`);
  return res.json();
}

export async function assessRepository(
  repoUrl: string,
  question: string,
  history: ChatTurn[]
): Promise<ComplianceReport> {
  // Submit a repository URL and compliance question to the FastAPI agent.
  const res = await fetch("/api/assess", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_url: repoUrl, question, history }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Assessment failed (${res.status})`);
  }
  return res.json();
}

export async function exportMarkdown(report: ComplianceReport): Promise<string> {
  // Convert a structured report into Markdown via the backend formatter.
  const res = await fetch("/api/report/markdown", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(report),
  });
  if (!res.ok) throw new Error(`Markdown export failed (${res.status})`);
  return res.text();
}
