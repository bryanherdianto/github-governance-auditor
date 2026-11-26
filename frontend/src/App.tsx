import { FormEvent, useEffect, useRef, useState } from "react";
import { assessRepository, fetchHealth, fetchPolicies } from "./api";
import ComplianceCard from "./components/ComplianceCard";
import { ChatMessage, ChatTurn, ControlDefinition, HealthStatus } from "./types";

const QUICK_PROMPTS = [
  "Run a full compliance assessment across all governance controls.",
  "Does this repository use an approved MIT or Apache 2.0 license?",
  "Are the model's intended use and limitations adequately documented?",
  "Does this repository have a security policy, and what should we fix?",
];

const FALLBACK_POLICIES: Pick<ControlDefinition, "id" | "name" | "description">[] = [
  { id: "documentation", name: "Documentation", description: "Does the repository contain a nonempty README file?" },
  { id: "licensing", name: "Licensing", description: "Does the repository use an approved license (MIT or Apache 2.0)?" },
  { id: "model_documentation", name: "Model Documentation", description: "Does the repository contain a model card?" },
  { id: "ai_transparency", name: "AI Transparency", description: "Are the model's intended use and limitations adequately documented?" },
  { id: "security", name: "Security", description: "Does the repository contain a security policy?" },
];

const PILL_INPUT_CLASS =
  "min-h-11 rounded-[24px] border-2 border-transparent bg-soft-cloud px-[18px] py-2.5 text-[15px] text-ink transition-colors focus:border-ink focus:bg-white focus:outline-none focus:shadow-[0_0_0_6px_#f5f5f5]";

export default function App() {
  const [repoUrl, setRepoUrl] = useState("https://github.com/openai/whisper");
  const [input, setInput] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [policies, setPolicies] = useState<Pick<ControlDefinition, "id" | "name" | "description">[]>(FALLBACK_POLICIES);
  const feedEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => setHealth(null));
    fetchPolicies().then(setPolicies).catch(() => setPolicies(FALLBACK_POLICIES));
  }, []);

  useEffect(() => {
    feedEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendQuestion = async (questionText: string) => {
    const question = questionText.trim();
    const targetRepo = repoUrl.trim();
    if (loading) return;

    if (!targetRepo) {
      setValidationError("Enter a GitHub repository URL before running an audit.");
      return;
    }
    if (!question) {
      setValidationError("Enter a compliance question or select a quick prompt.");
      return;
    }
    setValidationError(null);

    const history: ChatTurn[] = messages
      .filter((m) => !m.error)
      .slice(-6)
      .map((m) => ({ role: m.role, content: m.report ? m.report.answer : m.text }));

    const userMsg: ChatMessage = {
      id: `${Date.now()}-u`,
      role: "user",
      text: question,
      repoUrl: targetRepo,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const report = await assessRepository(targetRepo, question, history);
      setMessages((prev) => [
        ...prev,
        { id: `${Date.now()}-a`, role: "assistant", text: report.answer, repoUrl: report.repository_url, report },
      ]);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unexpected request error.";
      setMessages((prev) => [
        ...prev,
        { id: `${Date.now()}-e`, role: "assistant", text: msg, error: msg, failedQuestion: question },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    void sendQuestion(input);
  };

  const clearSession = () => {
    setMessages([]);
    setValidationError(null);
  };

  const healthLabel = health
    ? health.gemini_configured
      ? `Gemini Ready (${health.model})`
      : "Missing GEMINI_API_KEY"
    : "Backend Offline";

  return (
    <div className="flex min-h-screen w-full flex-col bg-white text-ink">
      <div className="flex min-h-9 w-full items-center justify-between gap-3 bg-soft-cloud px-4 py-1.5 text-xs font-medium sm:px-6 lg:px-10">
        <span className={health?.gemini_configured ? "text-pass-fg" : "text-fail-fg"}>{healthLabel}</span>
        {messages.length > 0 && (
          <button
            type="button"
            className="border-none bg-transparent py-1 text-xs font-medium text-ink underline"
            onClick={clearSession}
            disabled={loading}
          >
            Clear Session
          </button>
        )}
      </div>

      <header className="flex w-full flex-wrap items-center justify-between gap-4 bg-white px-4 py-4 shadow-[inset_0_-1px_0_#e5e5e5] sm:px-6 lg:px-10">
        <div>
          <h1 className="m-0 text-xl font-bold tracking-[-0.01em]">GitHub Compliance Auditor</h1>
          <span className="mt-0.5 block text-xs font-medium text-mute">Governance Policy Evidence Review</span>
        </div>

        <div className="flex flex-1 basis-[360px] flex-col items-stretch gap-2 sm:flex-row sm:items-center sm:justify-end sm:gap-3">
          <label htmlFor="repo-url" className="whitespace-nowrap text-[13px] font-medium">
            Repository URL
          </label>
          <input
            id="repo-url"
            type="text"
            className={`w-full sm:max-w-[520px] ${PILL_INPUT_CLASS}`}
            value={repoUrl}
            onChange={(e) => {
              setRepoUrl(e.target.value);
              if (validationError) setValidationError(null);
            }}
            placeholder="https://github.com/owner/repo"
          />
        </div>
      </header>

      <main className="w-full flex-1 px-4 pt-8 pb-12 sm:px-6 lg:px-10">
        {messages.length === 0 ? (
          <section
            className="grid grid-cols-1 items-start gap-8 lg:grid-cols-[1.35fr_1fr] lg:gap-12"
            aria-label="Audit workspace overview"
          >
            <div>
              <h2 className="m-0 mb-[18px] text-[clamp(2.1rem,4.2vw,3.6rem)] font-extrabold uppercase leading-[0.95] tracking-[-0.03em] text-ink">
                AUDIT REPOSITORIES AGAINST GOVERNANCE CONTROLS
              </h2>
              <p className="m-0 mb-6 max-w-[66ch] text-base leading-normal text-charcoal">
                Enter any public GitHub repository URL above and ask a compliance question below. The auditor inspects
                repository metadata, README, license files, model cards, and security policies through the GitHub REST
                API.
              </p>
              <div className="flex flex-wrap gap-2.5" aria-label="Suggested compliance questions">
                {QUICK_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    className="min-h-11 rounded-[30px] border border-hairline bg-white px-[18px] py-2.5 text-left text-sm font-medium text-ink transition hover:border-ink hover:bg-ink hover:text-white active:scale-[0.98]"
                    onClick={() => void sendQuestion(prompt)}
                    disabled={loading}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>

            <div className="border-t-2 border-ink pt-4" aria-label="Evaluated governance controls">
              <h2 className="m-0 mb-3 text-base font-bold">Active Governance Controls</h2>
              <ul className="m-0 list-none p-0">
                {policies.map((policy) => (
                  <li key={policy.id} className="flex flex-col gap-1 border-t border-hairline py-3.5">
                    <strong className="text-[15px] font-semibold">{policy.name}</strong>
                    <span className="text-sm leading-snug text-mute">{policy.description}</span>
                  </li>
                ))}
              </ul>
            </div>
          </section>
        ) : (
          <div className="flex flex-col gap-7">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                {msg.role === "user" ? (
                  <div className="max-w-full bg-ink px-5 py-4 text-white [overflow-wrap:anywhere] sm:max-w-[720px]">
                    <div className="mb-1 text-xs text-hairline">{msg.repoUrl}</div>
                    <div className="text-[15px] leading-normal">{msg.text}</div>
                  </div>
                ) : msg.report ? (
                  <ComplianceCard report={msg.report} />
                ) : (
                  <div
                    className="flex w-full flex-wrap items-center justify-between gap-3 border-l-[3px] border-fail-fg bg-fail-bg px-5 py-4 text-fail-fg"
                    role="alert"
                  >
                    <div>
                      <strong>Audit Error</strong>
                      <p className="mt-1 mb-0 text-ink">{msg.text}</p>
                    </div>
                    {msg.failedQuestion && (
                      <button
                        type="button"
                        className="min-h-11 rounded-[30px] bg-soft-cloud px-5 py-2.5 text-sm font-semibold text-ink transition hover:bg-hairline-soft active:scale-[0.97]"
                        onClick={() => void sendQuestion(msg.failedQuestion!)}
                        disabled={loading}
                      >
                        Retry
                      </button>
                    )}
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="border-t border-hairline py-4 text-[15px] font-medium text-charcoal" role="status" aria-live="polite">
                Inspecting {repoUrl.trim()} via GitHub REST API and evaluating controls...
              </div>
            )}
            <div ref={feedEndRef} />
          </div>
        )}
      </main>

      <footer className="sticky bottom-0 w-full border-t border-hairline bg-white px-4 py-3.5 sm:px-6 lg:px-10">
        {validationError && (
          <p className="m-0 mb-2 text-[13px] font-semibold text-fail-fg" role="alert">
            {validationError}
          </p>
        )}
        <form className="flex w-full flex-wrap items-center gap-3 sm:flex-nowrap" onSubmit={handleSubmit}>
          <label htmlFor="question-input" className="w-full whitespace-nowrap text-[13px] font-semibold sm:w-auto">
            Compliance Question
          </label>
          <input
            id="question-input"
            type="text"
            className={`min-h-12 w-full flex-1 ${PILL_INPUT_CLASS}`}
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              if (validationError) setValidationError(null);
            }}
            placeholder="Ask about documentation, license, model card, transparency, or security..."
            disabled={loading}
          />
          <button
            type="submit"
            className="min-h-12 w-full rounded-[30px] bg-ink px-7 py-3 text-sm font-semibold text-white transition hover:opacity-85 active:scale-[0.96] sm:w-auto"
            disabled={loading}
          >
            {loading ? "Auditing..." : "Run Audit"}
          </button>
        </form>
      </footer>
    </div>
  );
}
