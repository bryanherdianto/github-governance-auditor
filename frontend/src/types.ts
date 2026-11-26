export type ControlStatus = "PASS" | "FAIL" | "UNKNOWN";

export interface ControlDefinition {
  id: string;
  name: string;
  description: string;
  criteria: string;
}

export interface ControlResult {
  control_name: string;
  description: string;
  status: ControlStatus;
  evidence: string[];
  source_references: string[];
  explanation: string;
  remediation: string;
}

export interface ToolTrace {
  tool_name: string;
  arguments: Record<string, unknown>;
  ok: boolean;
  summary: string;
  source_url?: string | null;
}

export interface ComplianceReport {
  repository: string;
  repository_url: string;
  question: string;
  answer: string;
  overall_summary: string;
  controls: ControlResult[];
  tool_traces: ToolTrace[];
}

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

export interface HealthStatus {
  status: string;
  gemini_configured: boolean;
  github_token_configured: boolean;
  model: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  repoUrl?: string;
  report?: ComplianceReport;
  error?: string;
  failedQuestion?: string;
}
