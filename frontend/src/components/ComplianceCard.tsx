import { useState } from "react";
import { exportMarkdown } from "../api";
import { ComplianceReport, ControlStatus } from "../types";

const STATUS_STYLES: Record<ControlStatus, string> = {
  PASS: "bg-pass-bg text-pass-fg",
  FAIL: "bg-fail-bg text-fail-fg",
  UNKNOWN: "bg-unknown-bg text-unknown-fg",
};

function downloadBlob(content: string, filename: string, mime: string) {
  // Trigger a browser file download for generated report artifacts.
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function countByStatus(report: ComplianceReport, status: ControlStatus): number {
  return report.controls.filter((c) => c.status === status).length;
}

export default function ComplianceCard({ report }: { report: ComplianceReport }) {
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const slug = report.repository.replace("/", "_");

  const handleMarkdownDownload = async () => {
    setExporting(true);
    setExportError(null);
    try {
      const md = await exportMarkdown(report);
      downloadBlob(md, `${slug}_compliance_report.md`, "text/markdown");
    } catch (err) {
      setExportError(err instanceof Error ? err.message : "Markdown export failed.");
    } finally {
      setExporting(false);
    }
  };

  const handleJsonDownload = () => {
    downloadBlob(JSON.stringify(report, null, 2), `${slug}_compliance_report.json`, "application/json");
  };

  return (
    <section
      className="w-full border-t-2 border-ink pt-5 [overflow-wrap:anywhere]"
      aria-label={`Compliance report for ${report.repository}`}
    >
      <div className="mb-5 flex flex-wrap items-start justify-between gap-5">
        <div className="min-w-0 flex-1 basis-[480px]">
          <div className="mb-2 text-[13px] font-semibold">
            <a href={report.repository_url} target="_blank" rel="noreferrer" className="text-ink underline">
              {report.repository}
            </a>
          </div>
          <h2 className="m-0 mb-2 text-[22px] font-semibold leading-[1.3]">{report.answer}</h2>
          <p className="m-0 text-[15px] leading-normal text-charcoal">{report.overall_summary}</p>
        </div>

        <div className="flex flex-col items-start gap-3 lg:items-end">
          <div className="flex flex-wrap gap-2" aria-label="Control status totals">
            <span className={`inline-block rounded-[30px] px-3 py-1 text-xs font-bold leading-snug ${STATUS_STYLES.PASS}`}>
              PASS: {countByStatus(report, "PASS")}
            </span>
            <span className={`inline-block rounded-[30px] px-3 py-1 text-xs font-bold leading-snug ${STATUS_STYLES.FAIL}`}>
              FAIL: {countByStatus(report, "FAIL")}
            </span>
            <span className={`inline-block rounded-[30px] px-3 py-1 text-xs font-bold leading-snug ${STATUS_STYLES.UNKNOWN}`}>
              UNKNOWN: {countByStatus(report, "UNKNOWN")}
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="min-h-11 rounded-[30px] bg-soft-cloud px-5 py-2.5 text-sm font-semibold text-ink transition hover:bg-hairline-soft active:scale-[0.97]"
              onClick={handleMarkdownDownload}
              disabled={exporting}
            >
              {exporting ? "Exporting..." : "Download Markdown"}
            </button>
            <button
              type="button"
              className="min-h-11 rounded-[30px] bg-soft-cloud px-5 py-2.5 text-sm font-semibold text-ink transition hover:bg-hairline-soft active:scale-[0.97]"
              onClick={handleJsonDownload}
            >
              Download JSON
            </button>
          </div>
        </div>
      </div>

      {exportError && (
        <p className="mb-2 text-[13px] font-semibold text-fail-fg" role="alert">
          {exportError}
        </p>
      )}

      <div className="flex flex-col">
        {report.controls.map((ctrl) => (
          <article
            key={ctrl.control_name}
            className="grid grid-cols-1 gap-5 border-t border-hairline py-5 lg:grid-cols-[minmax(220px,1fr)_2fr] lg:gap-6"
          >
            <div>
              <div className="mb-1.5 flex items-center justify-between gap-2.5">
                <h3 className="m-0 text-base font-bold">{ctrl.control_name}</h3>
                <span
                  className={`inline-block rounded-[30px] px-3 py-1 text-xs font-bold leading-snug ${STATUS_STYLES[ctrl.status]}`}
                >
                  {ctrl.status}
                </span>
              </div>
              <p className="m-0 text-sm leading-snug text-mute">{ctrl.description}</p>
            </div>

            <div className="min-w-0">
              <p className="m-0 mb-3 text-[15px] leading-normal text-charcoal">{ctrl.explanation}</p>

              {ctrl.evidence.length > 0 && (
                <div className="mt-2.5 text-sm">
                  <span className="mb-1 block text-xs font-bold uppercase text-mute">Evidence</span>
                  <ul className="m-0 list-disc pl-5 leading-normal">
                    {ctrl.evidence.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {ctrl.source_references.length > 0 && (
                <div className="mt-2.5 text-sm">
                  <span className="mb-1 block text-xs font-bold uppercase text-mute">Sources</span>
                  <div className="flex flex-wrap gap-3.5">
                    {ctrl.source_references.map((url, idx) => (
                      <a key={idx} href={url} target="_blank" rel="noreferrer" className="font-medium text-ink underline">
                        {url.replace("https://github.com/", "")}
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {ctrl.remediation && (
                <div className="mt-3 border-l-2 border-ink bg-soft-cloud px-3.5 py-3 text-sm">
                  <span className="mb-1 block text-xs font-bold uppercase text-mute">Remediation</span>
                  <p className="m-0 leading-snug">{ctrl.remediation}</p>
                </div>
              )}
            </div>
          </article>
        ))}
      </div>

      {report.tool_traces.length > 0 && (
        <details className="mt-4 border-t border-hairline py-3.5 text-[13px] text-charcoal">
          <summary className="font-semibold">Agent Tool Calls ({report.tool_traces.length})</summary>
          <ul className="mt-2.5 list-disc pl-5 leading-relaxed">
            {report.tool_traces.map((trace, idx) => (
              <li key={idx}>
                <code>
                  {trace.tool_name}({JSON.stringify(trace.arguments)})
                </code>{" "}
                <span className={trace.ok ? "font-bold text-pass-fg" : "font-bold text-fail-fg"}>
                  {trace.ok ? "OK" : "ERR"}
                </span>
                : {trace.summary}
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
