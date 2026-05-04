"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import TopBar from "../../../../../components/TopBar";
import {
  API_URL,
  AutoEvaluationResult,
  BuiltReport,
  EvaluationRun,
  EvaluationRecord,
  ErrorAnnotation,
  ErrorCategory,
  ErrorSeverity,
  ErrorTaxonomyReport,
  GeneratedAnswer,
  JudgeCalibrationReport,
  ProductionReadinessReport,
  ReportAudience,
  ReportSectionKey,
  Project,
  RagExecutionResult,
  RetrievedChunk,
  SourceDocument,
  TOKEN_STORAGE_KEY,
  RunReviewDashboard,
  RunSummary,
  TestQuestion,
  authRequest,
} from "../../../../../lib/auth";

/* ── Constants ── */
const relevanceLabels = ["high", "medium", "low", "irrelevant"];
const scoreOptions    = [1, 2, 3, 4, 5];
const reportSections: Array<{ value: ReportSectionKey; label: string }> = [
  { value: "overview", label: "Overview" },
  { value: "readiness", label: "Production readiness" },
  { value: "scores", label: "CLEAR-RAG scores" },
  { value: "retrieval", label: "Retrieval evaluation" },
  { value: "calibration", label: "Judge calibration" },
  { value: "errors", label: "Error taxonomy" },
  { value: "questions", label: "Question results" },
];

const errorCategories: Array<{ value: ErrorCategory; label: string }> = [
  { value: "retrieval_miss",   label: "Retrieval Miss" },
  { value: "citation_error",   label: "Citation Error" },
  { value: "hallucination",    label: "Hallucination" },
  { value: "incomplete_answer",label: "Incomplete Answer" },
  { value: "irrelevant_answer",label: "Irrelevant Answer" },
  { value: "contradiction",    label: "Contradiction" },
  { value: "latency_cost",     label: "Latency or Cost" },
  { value: "format_error",     label: "Format Error" },
  { value: "policy_ambiguity", label: "Policy Ambiguity" },
  { value: "other",            label: "Other" },
];

const errorSeverities: Array<{ value: ErrorSeverity; label: string }> = [
  { value: "low",      label: "Low" },
  { value: "medium",   label: "Medium" },
  { value: "high",     label: "High" },
  { value: "critical", label: "Critical" },
];

const retrievalModes = [
  { value: "keyword", label: "Keyword matching" },
  { value: "vector",  label: "Vector embeddings" },
] as const;

const dimensionLabels: Array<[keyof RunSummary["dimension_averages"], string]> = [
  ["citation_quality_score",      "Citation Quality"],
  ["latency_cost_score",          "Latency and Cost"],
  ["evidence_faithfulness_score", "Evidence Faithfulness"],
  ["answer_relevance_score",      "Answer Relevance"],
  ["retrieval_quality_score",     "Retrieval Quality"],
];

/* ─────────────────────────────────────────
   Helper components
───────────────────────────────────────── */

function MetricCard({ label, value }: Readonly<{ label: string; value: string | number }>) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function SetupSection({
  title,
  count,
  children,
}: Readonly<{ title: string; count: number; children: React.ReactNode }>) {
  return (
    <section className="setup-section">
      <div className="section-heading">
        <h2>{title}</h2>
        <span className="badge-count">{count}</span>
      </div>
      <div style={{ padding: "var(--sp-4) var(--sp-5)", display: "grid", gap: "var(--sp-4)" }}>
        {children}
      </div>
    </section>
  );
}

function ScoreSelect({ name, label }: Readonly<{ name: string; label: string }>) {
  return (
    <label>
      {label}
      <select name={name} defaultValue="5" required>
        {scoreOptions.map((s) => (
          <option key={s} value={s}>{s}</option>
        ))}
      </select>
    </label>
  );
}

function ScoreInput({ name, label, value }: Readonly<{ name: string; label: string; value: number | null }>) {
  return (
    <label>
      {label}
      <input name={name} type="number" min={1} max={5} defaultValue={value ?? ""} placeholder="1–5" />
    </label>
  );
}

function OutputList({ items }: Readonly<{ items: Array<{ title: string; body: string; meta: string }> }>) {
  if (items.length === 0) {
    return <p className="muted" style={{ fontStyle: "italic" }}>Nothing recorded yet.</p>;
  }
  return (
    <div className="mini-list">
      {items.map((item, index) => (
        <div className="mini-list-item" key={`${item.title}-${index}`}>
          <strong>{item.title}</strong>
          <p style={{ fontSize: 13, lineHeight: 1.6 }}>{item.body}</p>
          {item.meta && <span style={{ fontSize: 12 }}>{item.meta}</span>}
        </div>
      ))}
    </div>
  );
}

function GateBadge({ status }: { status: string }) {
  const cls =
    status === "pass"    ? "badge badge-green"  :
    status === "warning" ? "badge badge-yellow" :
    "badge badge-red";
  return (
    <span className={cls}>
      {status === "pass" ? "Pass" : status === "warning" ? "Warning" : "Fail"}
    </span>
  );
}

/* ── Analytics panel ── */
function RunAnalytics({
  summary,
  onDownload,
}: Readonly<{ summary: RunSummary; onDownload: (format: "csv" | "json") => void }>) {
  return (
    <section className="status analytics-panel">
      <div className="section-heading">
        <h2>Evaluation Summary</h2>
        <div style={{ display: "flex", gap: "var(--sp-2)" }}>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => onDownload("csv")}>
            Export CSV
          </button>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => onDownload("json")}>
            Export JSON
          </button>
        </div>
      </div>

      <div style={{ padding: "var(--sp-5)", display: "grid", gap: "var(--sp-5)" }}>
        {/* KPI grid */}
        <div className="metric-grid">
          <MetricCard label="Questions"        value={summary.total_questions} />
          <MetricCard label="Generated answers" value={summary.generated_answers} />
          <MetricCard label="Reviewed"          value={summary.reviewed_answers} />
          <MetricCard label="Completion"        value={`${summary.review_completion_percent}%`} />
          <MetricCard label="Avg overall"       value={summary.average_overall_score ?? "Not scored"} />
          <MetricCard label="Weakest dimension" value={summary.weakest_dimension ?? "Not scored"} />
        </div>

        {/* Dimension score bars */}
        <div>
          <h3 style={{ fontSize: 13, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: "var(--sp-3)" }}>
            Dimension averages
          </h3>
          <div className="dimension-list">
            {dimensionLabels.map(([key, label]) => {
              const value       = summary.dimension_averages[key];
              const numericVal  = value ? Number(value) : 0;
              const pct         = Math.min(100, (numericVal / 5) * 100);
              return (
                <div className="dimension-row" key={key}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
                    <span style={{ color: "var(--text-secondary)" }}>{label}</span>
                    <strong style={{ color: "var(--text-primary)" }}>{value ?? "—"} / 5</strong>
                  </div>
                  <div className="score-bar" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
                    <span style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Retrieval metrics */}
        <div>
          <h3 style={{ fontSize: 13, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: "var(--sp-3)" }}>
            Retrieval metrics
          </h3>
          <div className="metric-grid">
            <MetricCard label="Hit Rate"        value={formatMetric(summary.retrieval_metrics.hit_rate)} />
            <MetricCard label="Precision@3"     value={formatMetric(summary.retrieval_metrics.precision_at_k)} />
            <MetricCard label="Recall@3"        value={formatMetric(summary.retrieval_metrics.recall_at_k)} />
            <MetricCard label="MRR"             value={formatMetric(summary.retrieval_metrics.mean_reciprocal_rank)} />
            <MetricCard label="Chunk coverage"  value={formatMetric(summary.retrieval_metrics.chunk_coverage)} />
            <MetricCard label="Missing evidence" value={summary.retrieval_metrics.missing_evidence_count} />
          </div>
        </div>

        {/* Question results */}
        <div>
          <h3 style={{ fontSize: 13, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: "var(--sp-3)" }}>
            Question results
          </h3>
          <div className="question-results">
            {summary.question_results.map((result) => (
              <div className="mini-list-item" key={result.question_id}>
                <strong>{result.question_text}</strong>
                <span>
                  {result.reviewed
                    ? `Reviewed · Overall ${result.overall_score}`
                    : "Not reviewed"}
                </span>
                {result.evaluation_mode && (
                  <span>
                    {result.evaluation_mode === "automated" ? "Automated judge" : "Human review"}
                    {result.judge_model_name ? ` / ${result.judge_model_name}` : ""}
                  </span>
                )}
                <span>
                  Retrieval: {formatExpectedSourceMatch(result.expected_source_match)} · chunks {result.retrieved_chunk_count}
                  {result.first_relevant_rank ? ` · first match rank ${result.first_relevant_rank}` : ""}
                  {result.missing_evidence ? " · missing evidence" : ""}
                </span>
                {result.answer_text
                  ? <p style={{ fontSize: 13, margin: 0 }}>{result.answer_text}</p>
                  : <p style={{ fontSize: 13, margin: 0, fontStyle: "italic", color: "var(--text-muted)" }}>No generated answer yet.</p>}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function ReportBuilderPanel({
  report,
  isBuilding,
  onBuild,
}: Readonly<{
  report: BuiltReport | null;
  isBuilding: boolean;
  onBuild: (event: FormEvent<HTMLFormElement>) => void;
}>) {
  return (
    <section className="status analytics-panel">
      <div className="section-heading">
        <h2>Report Builder</h2>
        <span>{report ? "Generated" : "Draft"}</span>
      </div>
      <form className="compact-form" onSubmit={onBuild}>
        <label>
          Report title
          <input name="title" placeholder="Evaluation report title" />
        </label>
        <label>
          Audience
          <select name="audience" defaultValue="technical">
            <option value="executive">Executive</option>
            <option value="technical">Technical</option>
            <option value="audit">Audit</option>
          </select>
        </label>
        <div className="comparison-selector">
          {reportSections.map((section) => (
            <label className="checkbox-row" key={section.value}>
              <input name="sections" type="checkbox" value={section.value} defaultChecked />
              <span>{section.label}</span>
            </label>
          ))}
        </div>
        <button type="submit" className={`btn btn-primary${isBuilding ? " btn-loading" : ""}`} disabled={isBuilding}>
          {isBuilding ? "" : "Build report"}
        </button>
      </form>
      {report ? (
        <div className="question-results">
          <div className="mini-list-item">
            <strong>{report.title}</strong>
            <span>
              {report.audience} / {new Date(report.generated_at).toLocaleString()}
            </span>
            <textarea readOnly rows={12} value={report.markdown} />
          </div>
        </div>
      ) : (
        <p className="muted" style={{ padding: "0 var(--sp-5) var(--sp-5)" }}>
          Build a Markdown report from the current run metrics, readiness gates, calibration, and errors.
        </p>
      )}
    </section>
  );
}

/* ── Production readiness ── */
function ProductionReadinessPanel({ report }: Readonly<{ report: ProductionReadinessReport }>) {
  return (
    <section className="status analytics-panel">
      <div className="section-heading">
        <h2>Production Readiness</h2>
        <span className={report.ready_for_production ? "badge badge-green" : "badge badge-red"}>
          {report.ready_for_production ? "Ready" : "Blocked"}
        </span>
      </div>

      <div style={{ padding: "var(--sp-5)", display: "grid", gap: "var(--sp-5)" }}>
        <div className="metric-grid">
          <MetricCard label="Passed gates"      value={report.passed_count} />
          <MetricCard label="Warnings"          value={report.warning_count} />
          <MetricCard label="Blocking failures" value={report.blocking_failure_count} />
          <MetricCard label="Release decision"  value={report.ready_for_production ? "Ready" : "Not ready"} />
        </div>

        <div className="question-results">
          {report.gates.map((gate) => (
            <div className="mini-list-item" key={gate.key}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "var(--sp-3)" }}>
                <strong>{gate.label}</strong>
                <GateBadge status={gate.status} />
              </div>
              <span>
                Observed {gate.observed_value ?? "n/a"} · threshold {gate.threshold ?? "n/a"}
                {gate.required ? " · required" : " · advisory"}
              </span>
              <p style={{ fontSize: 13, margin: 0, color: "var(--text-secondary)" }}>{gate.message}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ── Review dashboard ── */
function ReviewDashboard({
  dashboard,
  onSubmitReview,
}: Readonly<{
  dashboard: RunReviewDashboard;
  onSubmitReview: (evaluationId: number, event: FormEvent<HTMLFormElement>) => void;
}>) {
  return (
    <section className="status analytics-panel">
      <div className="section-heading">
        <h2>Evaluation Review</h2>
        <span className={dashboard.ready_for_release ? "badge badge-green" : "badge badge-slate"}>
          {dashboard.ready_for_release ? "Ready" : "In review"}
        </span>
      </div>

      <div style={{ padding: "var(--sp-5)", display: "grid", gap: "var(--sp-5)" }}>
        <div className="metric-grid">
          <MetricCard label="Total answers"    value={dashboard.total_answers} />
          <MetricCard label="Pending"          value={dashboard.pending_review_count} />
          <MetricCard label="Approved"         value={dashboard.approved_count} />
          <MetricCard label="Needs revision"   value={dashboard.needs_revision_count} />
          <MetricCard label="Completion"       value={`${dashboard.review_completion_percent}%`} />
          <MetricCard label="Approved average" value={dashboard.approved_average_overall_score ?? "Not approved"} />
        </div>

        {dashboard.items.length === 0 ? (
          <p className="muted" style={{ fontStyle: "italic" }}>
            Run Gemini RAG and automated CLEAR-RAG evaluation before reviewing answers.
          </p>
        ) : (
          <div className="question-results">
            {dashboard.items.map((item) => (
              <div className="review-card" key={item.answer_id}>
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "var(--sp-3)" }}>
                  <strong style={{ fontSize: 14 }}>{item.question_text}</strong>
                  <span className={
                    item.review_status === "approved"       ? "badge badge-green" :
                    item.review_status === "needs_revision" ? "badge badge-red"   :
                    "badge badge-slate"
                  }>
                    {formatReviewStatus(item.review_status)}
                  </span>
                </div>

                <p style={{ fontSize: 13, margin: 0, lineHeight: 1.65 }}>{item.answer_text}</p>

                <div style={{ fontSize: 12, color: "var(--text-muted)", display: "grid", gap: 3 }}>
                  <span>
                    {item.evaluation_mode ? `${item.evaluation_mode} score` : "No score"} · Overall{" "}
                    {item.overall_score ?? "not scored"}
                    {item.judge_model_name ? ` · ${item.judge_model_name}` : ""}
                  </span>
                  <span>
                    Citation {item.citation_quality_score ?? "n/a"} · Latency {item.latency_cost_score ?? "n/a"} ·
                    Faithfulness {item.evidence_faithfulness_score ?? "n/a"} · Relevance {item.answer_relevance_score ?? "n/a"} ·
                    Retrieval {item.retrieval_quality_score ?? "n/a"}
                  </span>
                </div>

                {item.judge_reasoning   && <p style={{ fontSize: 13, margin: 0, color: "var(--text-secondary)" }}>{item.judge_reasoning}</p>}
                {item.reviewer_notes    && <p style={{ fontSize: 13, margin: 0, color: "var(--text-secondary)" }}>{item.reviewer_notes}</p>}
                {item.review_notes      && <span style={{ fontSize: 12 }}>Reviewer decision: {item.review_notes}</span>}
                {item.score_change_reason && <span style={{ fontSize: 12 }}>Score change: {item.score_change_reason}</span>}

                {item.retrieved_chunks.length > 0 && (
                  <div className="mini-list">
                    {item.retrieved_chunks.map((chunk) => (
                      <div className="mini-list-item" key={chunk.id}>
                        <strong>Evidence {chunk.rank}: {chunk.section_reference ?? "No section"}</strong>
                        <p style={{ fontSize: 12, margin: 0 }}>{chunk.chunk_text}</p>
                      </div>
                    ))}
                  </div>
                )}

                {item.evaluation_id ? (
                  <form className="compact-form" onSubmit={(e) => onSubmitReview(item.evaluation_id as number, e)}>
                    <label>
                      Review status
                      <select name="reviewStatus" defaultValue={item.review_status ?? "pending_review"}>
                        <option value="pending_review">Pending review</option>
                        <option value="approved">Approved</option>
                        <option value="needs_revision">Needs revision</option>
                      </select>
                    </label>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--sp-2)" }}>
                      <ScoreInput name="citationQualityScore"      label="Citation quality"      value={item.citation_quality_score} />
                      <ScoreInput name="latencyCostScore"           label="Latency and cost"      value={item.latency_cost_score} />
                      <ScoreInput name="evidenceFaithfulnessScore"  label="Evidence faithfulness" value={item.evidence_faithfulness_score} />
                      <ScoreInput name="answerRelevanceScore"       label="Answer relevance"      value={item.answer_relevance_score} />
                      <ScoreInput name="retrievalQualityScore"      label="Retrieval quality"     value={item.retrieval_quality_score} />
                    </div>
                    <textarea name="reviewNotes"        placeholder="Review notes"                     rows={2} defaultValue={item.review_notes ?? ""} />
                    <textarea name="scoreChangeReason"  placeholder="Reason if scores changed"         rows={2} defaultValue={item.score_change_reason ?? ""} />
                    <textarea name="reviewerNotes"      placeholder="Final evaluator notes"            rows={2} defaultValue={item.reviewer_notes ?? ""} />
                    <textarea name="suggestedImprovement" placeholder="Suggested improvement"         rows={2} defaultValue={item.suggested_improvement ?? ""} />
                    <button type="submit" className="btn btn-primary btn-sm">Save review decision</button>
                  </form>
                ) : (
                  <p className="muted" style={{ fontStyle: "italic" }}>No evaluation record exists for this answer yet.</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

/* ── Judge calibration ── */
function JudgeCalibrationPanel({ report }: Readonly<{ report: JudgeCalibrationReport }>) {
  return (
    <section className="status analytics-panel">
      <div className="section-heading">
        <h2>Judge Calibration</h2>
        <span className={report.paired_answer_count > 0 ? "badge badge-green" : "badge badge-slate"}>
          {report.paired_answer_count > 0 ? "Paired" : "Needs human scores"}
        </span>
      </div>

      <div style={{ padding: "var(--sp-5)", display: "grid", gap: "var(--sp-5)" }}>
        <div className="metric-grid">
          <MetricCard label="Paired answers"  value={report.paired_answer_count} />
          <MetricCard label="Exact agreement" value={`${report.overall_exact_agreement_percent}%`} />
          <MetricCard label="Within 1 point"  value={`${report.overall_within_one_agreement_percent}%`} />
          <MetricCard label="Avg delta"       value={formatSignedMetric(report.average_overall_delta)} />
          <MetricCard label="Automated only"  value={report.automated_only_count} />
          <MetricCard label="Human only"      value={report.human_only_count} />
        </div>

        <div>
          <h3 style={{ fontSize: 13, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: "var(--sp-3)" }}>
            Dimension agreement
          </h3>
          <div className="dimension-list">
            {report.dimension_calibration.map((dim) => (
              <div className="dimension-row" key={dim.field}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
                  <span style={{ color: "var(--text-secondary)" }}>{dim.label}</span>
                  <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{formatBiasDirection(dim.bias_direction)}</span>
                </div>
                <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                  Delta {formatSignedMetric(dim.average_delta)} · exact {dim.exact_agreement_percent}% · within 1 {dim.within_one_agreement_percent}%
                </span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 style={{ fontSize: 13, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: "var(--sp-3)" }}>
            Paired answer comparisons
          </h3>
          {report.answer_comparisons.length === 0 ? (
            <p className="muted" style={{ fontStyle: "italic" }}>
              Add a human CLEAR-RAG score to an answer that already has an automated judge score.
            </p>
          ) : (
            <div className="question-results">
              {report.answer_comparisons.map((comparison) => (
                <div className="mini-list-item" key={comparison.answer_id}>
                  <strong>{comparison.question_text}</strong>
                  <span>
                    Automated {comparison.automated_overall_score} · human {comparison.human_overall_score} · delta{" "}
                    {formatSignedMetric(comparison.overall_delta)}
                  </span>
                  <span>
                    {dimensionLabels
                      .map(([key, label]) => `${label}: ${formatSignedMetric(comparison.dimension_deltas[key])}`)
                      .join(" / ")}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

/* ── Error taxonomy ── */
function ErrorTaxonomyPanel({ report }: Readonly<{ report: ErrorTaxonomyReport }>) {
  const activeCategoryCounts = report.category_counts.filter((i) => i.count > 0);
  const activeSeverityCounts = report.severity_counts.filter((i) => i.count > 0);

  return (
    <section className="status analytics-panel">
      <div className="section-heading">
        <h2>Error Taxonomy</h2>
        <span className={report.total_errors > 0 ? "badge badge-red" : "badge badge-slate"}>
          {report.total_errors > 0 ? "Classified" : "No errors tagged"}
        </span>
      </div>

      <div style={{ padding: "var(--sp-5)", display: "grid", gap: "var(--sp-5)" }}>
        <div className="metric-grid">
          <MetricCard label="Total errors"     value={report.total_errors} />
          <MetricCard label="Affected answers" value={report.affected_answers} />
          <MetricCard label="Top category"     value={activeCategoryCounts[0]?.label ?? "None"} />
          <MetricCard label="Highest severity" value={highestSeverityLabel(activeSeverityCounts)} />
        </div>

        {activeCategoryCounts.length > 0 && (
          <div>
            <h3 style={{ fontSize: 13, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: "var(--sp-3)" }}>
              Category breakdown
            </h3>
            <div className="dimension-list">
              {activeCategoryCounts.map((item) => (
                <div className="dimension-row" key={item.key}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
                    <span style={{ color: "var(--text-secondary)" }}>{item.label}</span>
                    <strong style={{ color: "var(--text-primary)" }}>{item.count} ({item.percent}%)</strong>
                  </div>
                  <div className="score-bar">
                    <span style={{ width: `${item.percent}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div>
          <h3 style={{ fontSize: 13, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: "var(--sp-3)" }}>
            Recent error tags
          </h3>
          {report.items.length === 0 ? (
            <p className="muted" style={{ fontStyle: "italic" }}>
              No error annotations have been added for this run.
            </p>
          ) : (
            <div className="question-results">
              {report.items.slice(0, 6).map((item) => (
                <div className="mini-list-item" key={item.id}>
                  <div style={{ display: "flex", alignItems: "center", gap: "var(--sp-2)" }}>
                    <strong>{item.category_label}</strong>
                    <span className={
                      item.severity === "critical" ? "badge badge-red"   :
                      item.severity === "high"     ? "badge badge-yellow" :
                      "badge badge-slate"
                    }>
                      {formatSeverity(item.severity)}
                    </span>
                  </div>
                  <span style={{ fontSize: 12 }}>{item.question_text}</span>
                  {item.notes && <p style={{ fontSize: 12, margin: 0 }}>{item.notes}</p>}
                  {item.evidence_reference && <span style={{ fontSize: 12 }}>{item.evidence_reference}</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

/* ── CLEAR-RAG Scoring list (per answer) ── */
function EvaluationReviewList({
  answers,
  evaluations,
  errorItems,
  onSubmit,
  onSubmitError,
}: Readonly<{
  answers: GeneratedAnswer[];
  evaluations: EvaluationRecord[];
  errorItems: ErrorTaxonomyReport["items"];
  onSubmit: (answerId: number, event: FormEvent<HTMLFormElement>) => void;
  onSubmitError: (answerId: number, event: FormEvent<HTMLFormElement>) => void;
}>) {
  if (answers.length === 0) return null;

  return (
    <div className="review-list">
      <h3>CLEAR-RAG Scoring</h3>
      {answers.map((answer) => {
        const answerEvaluations  = evaluations.filter((e) => e.generated_answer_id === answer.id);
        const answerErrors       = errorItems.filter((i) => i.answer_id === answer.id);
        const latestEvaluation   = answerEvaluations[0];

        return (
          <div className="review-card" key={answer.id}>
            <strong style={{ fontSize: 14 }}>{answer.model_name ?? "Generated answer"}</strong>

            {answerEvaluations.length > 0 ? (
              <div className="mini-list">
                {answerEvaluations.map((evaluation) => (
                  <div className="mini-list-item" key={evaluation.id}>
                    <div style={{ display: "flex", alignItems: "center", gap: "var(--sp-2)" }}>
                      <strong>Overall: {evaluation.overall_score}</strong>
                      <span className={evaluation.evaluation_mode === "automated" ? "badge badge-indigo" : "badge badge-green"}>
                        {evaluation.evaluation_mode === "automated" ? "Automated" : "Human"}
                      </span>
                    </div>
                    <span style={{ fontSize: 12 }}>
                      Citation {evaluation.citation_quality_score} · Latency {evaluation.latency_cost_score} ·
                      Faithfulness {evaluation.evidence_faithfulness_score} · Relevance {evaluation.answer_relevance_score} ·
                      Retrieval {evaluation.retrieval_quality_score}
                    </span>
                    <span style={{ fontSize: 12 }}>Status: {formatReviewStatus(evaluation.review_status)}</span>
                    {evaluation.reviewer_notes    && <p style={{ fontSize: 12, margin: 0 }}>{evaluation.reviewer_notes}</p>}
                    {evaluation.judge_reasoning   && <p style={{ fontSize: 12, margin: 0 }}>{evaluation.judge_reasoning}</p>}
                    {evaluation.suggested_improvement && <span style={{ fontSize: 12 }}>{evaluation.suggested_improvement}</span>}
                  </div>
                ))}
              </div>
            ) : (
              <p className="muted" style={{ fontStyle: "italic" }}>Not reviewed yet.</p>
            )}

            {/* Score form */}
            <form className="compact-form" onSubmit={(e) => onSubmit(answer.id, e)}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--sp-2)" }}>
                <ScoreSelect name="citationQualityScore"      label="Citation quality" />
                <ScoreSelect name="latencyCostScore"          label="Latency and cost" />
                <ScoreSelect name="evidenceFaithfulnessScore" label="Evidence faithfulness" />
                <ScoreSelect name="answerRelevanceScore"      label="Answer relevance" />
                <ScoreSelect name="retrievalQualityScore"     label="Retrieval quality" />
              </div>
              <textarea name="reviewerNotes"      placeholder="Reviewer notes"      rows={2} />
              <textarea name="suggestedImprovement" placeholder="Suggested improvement" rows={2} />
              <button type="submit" className="btn btn-primary btn-sm">Save CLEAR-RAG score</button>
            </form>

            {/* Existing error tags */}
            {answerErrors.length > 0 && (
              <div className="mini-list">
                {answerErrors.map((item) => (
                  <div className="mini-list-item" key={item.id}>
                    <div style={{ display: "flex", alignItems: "center", gap: "var(--sp-2)" }}>
                      <strong>{item.category_label}</strong>
                      <span className="badge badge-yellow">{formatSeverity(item.severity)}</span>
                    </div>
                    {item.notes && <p style={{ fontSize: 12, margin: 0 }}>{item.notes}</p>}
                  </div>
                ))}
              </div>
            )}

            {/* Error annotation form */}
            <form className="compact-form" onSubmit={(e) => onSubmitError(answer.id, e)}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--sp-2)" }}>
                <label>
                  Category
                  <select name="category" defaultValue="retrieval_miss" required>
                    {errorCategories.map((c) => (
                      <option key={c.value} value={c.value}>{c.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Severity
                  <select name="severity" defaultValue="medium" required>
                    {errorSeverities.map((s) => (
                      <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                  </select>
                </label>
              </div>
              <input name="evaluationRecordId" type="hidden" value={latestEvaluation?.id ?? ""} />
              <textarea name="notes"             placeholder="Error notes"                             rows={2} />
              <textarea name="evidenceReference" placeholder="Evidence reference or expected behavior" rows={2} />
              <button type="submit" className="btn btn-danger btn-sm">Add error tag</button>
            </form>
          </div>
        );
      })}
    </div>
  );
}

/* ─────────────────────────────────────────
   Main page
───────────────────────────────────────── */
export default function RunOutputPage() {
  const params    = useParams<{ projectId: string; runId: string }>();
  const router    = useRouter();
  const projectId = params.projectId;
  const runId     = params.runId;

  const [project,              setProject]              = useState<Project | null>(null);
  const [run,                  setRun]                  = useState<EvaluationRun | null>(null);
  const [documents,            setDocuments]            = useState<SourceDocument[]>([]);
  const [questions,            setQuestions]            = useState<TestQuestion[]>([]);
  const [selectedQuestionId,   setSelectedQuestionId]   = useState("");
  const [chunks,               setChunks]               = useState<RetrievedChunk[]>([]);
  const [answers,              setAnswers]              = useState<GeneratedAnswer[]>([]);
  const [evaluations,          setEvaluations]          = useState<EvaluationRecord[]>([]);
  const [summary,              setSummary]              = useState<RunSummary | null>(null);
  const [reviewDashboard,      setReviewDashboard]      = useState<RunReviewDashboard | null>(null);
  const [judgeCalibration,     setJudgeCalibration]     = useState<JudgeCalibrationReport | null>(null);
  const [errorTaxonomy,        setErrorTaxonomy]        = useState<ErrorTaxonomyReport | null>(null);
  const [productionReadiness,  setProductionReadiness]  = useState<ProductionReadinessReport | null>(null);
  const [builtReport,          setBuiltReport]          = useState<BuiltReport | null>(null);
  const [executionResult,      setExecutionResult]      = useState<RagExecutionResult | null>(null);
  const [autoEvaluationResult, setAutoEvaluationResult] = useState<AutoEvaluationResult | null>(null);
  const [retrievalMode,        setRetrievalMode]        = useState<"keyword" | "vector">("keyword");
  const [isExecuting,          setIsExecuting]          = useState(false);
  const [isAutoEvaluating,     setIsAutoEvaluating]     = useState(false);
  const [isBuildingReport,     setIsBuildingReport]     = useState(false);
  const [error,                setError]                = useState("");

  const selectedQuestion = useMemo(
    () => questions.find((q) => String(q.id) === selectedQuestionId),
    [questions, selectedQuestionId],
  );

  const getToken = useCallback(() => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) { router.replace("/login"); return null; }
    return token;
  }, [router]);

  const loadOutputs = useCallback(
    async (questionId: string) => {
      const token = getToken();
      if (!token || !questionId) { setChunks([]); setAnswers([]); return; }

      const [chunkData, answerData, evaluationData] = await Promise.all([
        authRequest<RetrievedChunk[]>(`/projects/${projectId}/runs/${runId}/questions/${questionId}/retrieved-chunks`, { method: "GET" }, token),
        authRequest<GeneratedAnswer[]>(`/projects/${projectId}/runs/${runId}/questions/${questionId}/generated-answers`, { method: "GET" }, token),
        authRequest<EvaluationRecord[]>(`/projects/${projectId}/runs/${runId}/evaluations`, { method: "GET" }, token),
      ]);
      setChunks(chunkData);
      setAnswers(answerData);
      setEvaluations(evaluationData);
    },
    [getToken, projectId, runId],
  );

  const loadSummary = useCallback(async () => {
    const token = getToken();
    if (!token) return;
    const [summaryData, reviewData, judgeData, errorData, readinessData] = await Promise.all([
      authRequest<RunSummary>(`/projects/${projectId}/runs/${runId}/summary`, { method: "GET" }, token),
      authRequest<RunReviewDashboard>(`/projects/${projectId}/runs/${runId}/review-dashboard`, { method: "GET" }, token),
      authRequest<JudgeCalibrationReport>(`/projects/${projectId}/runs/${runId}/judge-calibration`, { method: "GET" }, token),
      authRequest<ErrorTaxonomyReport>(`/projects/${projectId}/runs/${runId}/error-taxonomy`, { method: "GET" }, token),
      authRequest<ProductionReadinessReport>(`/projects/${projectId}/runs/${runId}/production-readiness`, { method: "GET" }, token),
    ]);
    setSummary(summaryData);
    setReviewDashboard(reviewData);
    setJudgeCalibration(judgeData);
    setErrorTaxonomy(errorData);
    setProductionReadiness(readinessData);
  }, [getToken, projectId, runId]);

  const loadPage = useCallback(async () => {
    const token = getToken();
    if (!token) return;

    try {
      const [
        projectData, runData, documentData, questionData,
        summaryData, reviewData, judgeData, errorData, readinessData,
      ] = await Promise.all([
        authRequest<Project>(`/projects/${projectId}`, { method: "GET" }, token),
        authRequest<EvaluationRun>(`/projects/${projectId}/runs/${runId}`, { method: "GET" }, token),
        authRequest<SourceDocument[]>(`/projects/${projectId}/documents`, { method: "GET" }, token),
        authRequest<TestQuestion[]>(`/projects/${projectId}/questions`, { method: "GET" }, token),
        authRequest<RunSummary>(`/projects/${projectId}/runs/${runId}/summary`, { method: "GET" }, token),
        authRequest<RunReviewDashboard>(`/projects/${projectId}/runs/${runId}/review-dashboard`, { method: "GET" }, token),
        authRequest<JudgeCalibrationReport>(`/projects/${projectId}/runs/${runId}/judge-calibration`, { method: "GET" }, token),
        authRequest<ErrorTaxonomyReport>(`/projects/${projectId}/runs/${runId}/error-taxonomy`, { method: "GET" }, token),
        authRequest<ProductionReadinessReport>(`/projects/${projectId}/runs/${runId}/production-readiness`, { method: "GET" }, token),
      ]);
      setProject(projectData);
      setRun(runData);
      setDocuments(documentData);
      setQuestions(questionData);
      setSummary(summaryData);
      setReviewDashboard(reviewData);
      setJudgeCalibration(judgeData);
      setErrorTaxonomy(errorData);
      setProductionReadiness(readinessData);
      const firstId = questionData[0] ? String(questionData[0].id) : "";
      setSelectedQuestionId((current) => current || firstId);
      if (firstId) await loadOutputs(firstId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load run");
    }
  }, [getToken, loadOutputs, projectId, runId]);

  useEffect(() => { loadPage(); }, [loadPage]);

  async function handleQuestionChange(questionId: string) {
    setSelectedQuestionId(questionId);
    setError("");
    try { await loadOutputs(questionId); }
    catch (err) { setError(err instanceof Error ? err.message : "Unable to load outputs"); }
  }

  async function submitChunk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError("");
    const token = getToken();
    if (!token || !selectedQuestionId) return;
    const form = event.currentTarget;
    const formData = new FormData(form);
    try {
      await authRequest(
        `/projects/${projectId}/runs/${runId}/questions/${selectedQuestionId}/retrieved-chunks`,
        {
          method: "POST",
          body: JSON.stringify({
            source_document_id: Number(formData.get("sourceDocumentId")),
            rank:               Number(formData.get("rank")),
            chunk_text:         String(formData.get("chunkText") ?? ""),
            section_reference:  String(formData.get("sectionReference") ?? "") || null,
            relevance_label:    String(formData.get("relevanceLabel") ?? "") || null,
            retrieval_time_ms:  optionalNumber(formData.get("retrievalTimeMs")),
          }),
        },
        token,
      );
      form.reset();
      await loadOutputs(selectedQuestionId);
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to save retrieved chunk"); }
  }

  async function submitAnswer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError("");
    const token = getToken();
    if (!token || !selectedQuestionId) return;
    const form = event.currentTarget;
    const formData = new FormData(form);
    try {
      await authRequest(
        `/projects/${projectId}/runs/${runId}/questions/${selectedQuestionId}/generated-answers`,
        {
          method: "POST",
          body: JSON.stringify({
            answer_text:      String(formData.get("answerText") ?? ""),
            model_name:       String(formData.get("modelName") ?? "") || null,
            input_tokens:     optionalNumber(formData.get("inputTokens")),
            output_tokens:    optionalNumber(formData.get("outputTokens")),
            generation_time_ms: optionalNumber(formData.get("generationTimeMs")),
            estimated_cost:   optionalString(formData.get("estimatedCost")),
          }),
        },
        token,
      );
      form.reset();
      await loadOutputs(selectedQuestionId);
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to save generated answer"); }
  }

  async function executeGeminiRag() {
    setError(""); setExecutionResult(null);
    const token = getToken();
    if (!token) return;
    setIsExecuting(true);
    try {
      const result = await authRequest<RagExecutionResult>(
        `/projects/${projectId}/runs/${runId}/execute`,
        { method: "POST", body: JSON.stringify({ retrieval_mode: retrievalMode }) },
        token,
      );
      setExecutionResult(result);
      const refreshed = await authRequest<EvaluationRun>(`/projects/${projectId}/runs/${runId}`, { method: "GET" }, token);
      setRun(refreshed);
      if (selectedQuestionId) await loadOutputs(selectedQuestionId);
      await loadSummary();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to run Gemini RAG");
      const refreshed = await authRequest<EvaluationRun>(`/projects/${projectId}/runs/${runId}`, { method: "GET" }, token).catch(() => null);
      if (refreshed) setRun(refreshed);
      await loadSummary().catch(() => undefined);
    } finally { setIsExecuting(false); }
  }

  async function runAutomatedEvaluation() {
    setError(""); setAutoEvaluationResult(null);
    const token = getToken();
    if (!token) return;
    setIsAutoEvaluating(true);
    try {
      const result = await authRequest<AutoEvaluationResult>(
        `/projects/${projectId}/runs/${runId}/auto-evaluate`,
        { method: "POST" },
        token,
      );
      setAutoEvaluationResult(result);
      if (selectedQuestionId) await loadOutputs(selectedQuestionId);
      await loadSummary();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to run automated CLEAR-RAG evaluation");
    } finally { setIsAutoEvaluating(false); }
  }

  async function submitEvaluation(answerId: number, event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError("");
    const token = getToken();
    if (!token || !selectedQuestionId) return;
    const form = event.currentTarget;
    const formData = new FormData(form);
    try {
      await authRequest(
        `/projects/${projectId}/runs/${runId}/questions/${selectedQuestionId}/answers/${answerId}/evaluations`,
        {
          method: "POST",
          body: JSON.stringify({
            citation_quality_score:     Number(formData.get("citationQualityScore")),
            latency_cost_score:         Number(formData.get("latencyCostScore")),
            evidence_faithfulness_score: Number(formData.get("evidenceFaithfulnessScore")),
            answer_relevance_score:     Number(formData.get("answerRelevanceScore")),
            retrieval_quality_score:    Number(formData.get("retrievalQualityScore")),
            reviewer_notes:             optionalString(formData.get("reviewerNotes")),
            suggested_improvement:      optionalString(formData.get("suggestedImprovement")),
          }),
        },
        token,
      );
      form.reset();
      await loadOutputs(selectedQuestionId);
      await loadSummary();
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to save evaluation"); }
  }

  async function submitErrorAnnotation(answerId: number, event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError("");
    const token = getToken();
    if (!token || !selectedQuestionId) return;
    const form = event.currentTarget;
    const formData = new FormData(form);
    try {
      await authRequest<ErrorAnnotation>(
        `/projects/${projectId}/runs/${runId}/questions/${selectedQuestionId}/answers/${answerId}/errors`,
        {
          method: "POST",
          body: JSON.stringify({
            category:             String(formData.get("category") ?? "other"),
            severity:             String(formData.get("severity") ?? "medium"),
            evaluation_record_id: optionalNumber(formData.get("evaluationRecordId")),
            notes:                optionalString(formData.get("notes")),
            evidence_reference:   optionalString(formData.get("evidenceReference")),
          }),
        },
        token,
      );
      form.reset();
      await loadSummary();
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to save error annotation"); }
  }

  async function submitReview(evaluationId: number, event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError("");
    const token = getToken();
    if (!token) return;
    const form = event.currentTarget;
    const formData = new FormData(form);
    try {
      await authRequest<EvaluationRecord>(
        `/projects/${projectId}/runs/${runId}/evaluations/${evaluationId}/review`,
        {
          method: "PATCH",
          body: JSON.stringify({
            review_status:              String(formData.get("reviewStatus") ?? "approved"),
            citation_quality_score:     optionalNumber(formData.get("citationQualityScore")),
            latency_cost_score:         optionalNumber(formData.get("latencyCostScore")),
            evidence_faithfulness_score: optionalNumber(formData.get("evidenceFaithfulnessScore")),
            answer_relevance_score:     optionalNumber(formData.get("answerRelevanceScore")),
            retrieval_quality_score:    optionalNumber(formData.get("retrievalQualityScore")),
            review_notes:               optionalString(formData.get("reviewNotes")),
            score_change_reason:        optionalString(formData.get("scoreChangeReason")),
            reviewer_notes:             optionalString(formData.get("reviewerNotes")),
            suggested_improvement:      optionalString(formData.get("suggestedImprovement")),
          }),
        },
        token,
      );
      form.reset();
      if (selectedQuestionId) await loadOutputs(selectedQuestionId);
      await loadSummary();
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to save review decision"); }
  }

  async function buildReport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const token = getToken();
    if (!token) return;
    const form = event.currentTarget;
    const formData = new FormData(form);
    const selectedSections = formData.getAll("sections").map(String) as ReportSectionKey[];
    setIsBuildingReport(true);
    try {
      const report = await authRequest<BuiltReport>(
        `/projects/${projectId}/runs/${runId}/report`,
        {
          method: "POST",
          body: JSON.stringify({
            title: optionalString(formData.get("title")),
            audience: String(formData.get("audience") ?? "technical") as ReportAudience,
            sections: selectedSections.length > 0 ? selectedSections : reportSections.map((section) => section.value),
          }),
        },
        token,
      );
      setBuiltReport(report);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to build report");
    } finally {
      setIsBuildingReport(false);
    }
  }

  async function downloadExport(format: "csv" | "json") {
    const token = getToken();
    if (!token) return;
    try {
      const response = await fetch(`${API_URL}/projects/${projectId}/runs/${runId}/export.${format}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail ?? "Unable to download export");
      }
      const blob = await response.blob();
      const url  = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href     = url;
      link.download = `clear-rag-run-${runId}.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to download export"); }
  }

  function handleLogout() {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    router.replace("/login");
  }

  /* ── Error / Loading ── */
  if (error && (!project || !run)) {
    return (
      <div className="page-root">
        <TopBar onLogout={handleLogout} />
        <main className="page-body">
          <div className="shell">
            <p className="error" role="alert" style={{ marginBottom: "var(--sp-4)" }}>{error}</p>
            <Link href={`/dashboard/projects/${projectId}`} className="btn btn-secondary">← Back to project</Link>
          </div>
        </main>
      </div>
    );
  }

  if (!project || !run) {
    return (
      <div className="page-root">
        <TopBar onLogout={handleLogout} />
        <main className="page-body">
          <div className="wide-shell animate-in">
            <div className="skeleton skeleton-heading" style={{ width: "25%", marginBottom: "var(--sp-4)" }} />
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--sp-4)" }}>
              <div className="skeleton" style={{ height: 200 }} />
              <div className="skeleton" style={{ height: 200 }} />
            </div>
          </div>
        </main>
      </div>
    );
  }

  /* ── Main render ── */
  return (
    <div className="page-root">
      <TopBar onLogout={handleLogout}>
        <Link href="/dashboard/projects" className="topbar-link">Projects</Link>
        <Link href={`/dashboard/projects/${projectId}`} className="topbar-link">
          {project.name}
        </Link>
      </TopBar>

      <main className="page-body">
        <div className="wide-shell animate-in">
          {/* Breadcrumb */}
          <nav className="breadcrumb" aria-label="Breadcrumb">
            <Link href="/dashboard">Dashboard</Link>
            <span className="breadcrumb-sep" aria-hidden="true">›</span>
            <Link href="/dashboard/projects">Projects</Link>
            <span className="breadcrumb-sep" aria-hidden="true">›</span>
            <Link href={`/dashboard/projects/${projectId}`}>{project.name}</Link>
            <span className="breadcrumb-sep" aria-hidden="true">›</span>
            <span className="breadcrumb-current">{run.name}</span>
          </nav>

          {/* Header */}
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "var(--sp-4)", flexWrap: "wrap", paddingBottom: "var(--sp-5)", borderBottom: "1px solid var(--border)", marginBottom: "var(--sp-6)" }}>
            <div>
              <p className="eyebrow">{project.name}</p>
              <h1 style={{ marginBottom: 6 }}>{run.name}</h1>
              <p style={{ fontSize: 14, color: "var(--text-muted)" }}>
                Run Gemini RAG automatically, or manually add retrieved chunks and generated answers for inspection.
              </p>
            </div>
            <Link href={`/dashboard/projects/${projectId}`} className="btn btn-secondary" style={{ flexShrink: 0, marginTop: "var(--sp-6)" }}>
              ← Project setup
            </Link>
          </div>

          {/* Feedback */}
          {error          && <p className="error"   role="alert"   style={{ marginBottom: "var(--sp-4)" }}>{error}</p>}
          {run.last_error && <p className="error"   role="alert"   style={{ marginBottom: "var(--sp-4)" }}>{run.last_error}</p>}

          {/* ── Run status panel ── */}
          <div className="status run-status-panel">
            <div className="section-heading">
              <h2>Run controls</h2>
              <span className={
                run.status === "completed" ? "badge badge-green" :
                run.status === "failed"    ? "badge badge-red"   :
                "badge badge-slate"
              }>
                {run.status}
              </span>
            </div>

            <div style={{ padding: "var(--sp-5)", display: "grid", gap: "var(--sp-4)" }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--sp-4)" }}>
                <div style={{ display: "grid", gap: 6 }}>
                  <span style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)" }}>
                    Processed questions
                  </span>
                  <strong style={{ fontSize: 22, fontWeight: 700, color: "var(--text-primary)" }}>
                    {run.processed_question_count}
                  </strong>
                </div>

                <label>
                  Retrieval mode
                  <select
                    value={retrievalMode}
                    onChange={(e) => setRetrievalMode(e.target.value as "keyword" | "vector")}
                  >
                    {retrievalModes.map((m) => (
                      <option key={m.value} value={m.value}>{m.label}</option>
                    ))}
                  </select>
                </label>
              </div>

              <div style={{ display: "flex", gap: "var(--sp-3)", flexWrap: "wrap" }}>
                <button
                  type="button"
                  className={`btn btn-primary${isExecuting ? " btn-loading" : ""}`}
                  onClick={executeGeminiRag}
                  disabled={isExecuting || documents.length === 0 || questions.length === 0}
                >
                  {isExecuting ? "" : "Run Gemini RAG"}
                </button>
                <button
                  type="button"
                  className={`btn btn-secondary${isAutoEvaluating ? " btn-loading" : ""}`}
                  onClick={runAutomatedEvaluation}
                  disabled={isAutoEvaluating || answers.length === 0}
                >
                  {isAutoEvaluating ? "" : "Run automated CLEAR-RAG evaluation"}
                </button>
              </div>

              {executionResult && (
                <p className="muted">
                  {executionResult.message} {executionResult.retrieved_chunks_created} chunks and{" "}
                  {executionResult.generated_answers_created} answers saved with {executionResult.model_name}.
                </p>
              )}
              {autoEvaluationResult && (
                <p className="muted">
                  {autoEvaluationResult.message} {autoEvaluationResult.evaluated_answers} answers scored with{" "}
                  {autoEvaluationResult.judge_model_name}.
                </p>
              )}
            </div>
          </div>

          {/* ── Analytics, readiness, review, calibration, errors ── */}
          {summary            && <RunAnalytics summary={summary} onDownload={downloadExport} />}
          {productionReadiness && <ProductionReadinessPanel report={productionReadiness} />}
          <ReportBuilderPanel report={builtReport} isBuilding={isBuildingReport} onBuild={buildReport} />
          {reviewDashboard    && <ReviewDashboard dashboard={reviewDashboard} onSubmitReview={submitReview} />}
          {judgeCalibration   && <JudgeCalibrationPanel report={judgeCalibration} />}
          {errorTaxonomy      && <ErrorTaxonomyPanel report={errorTaxonomy} />}

          {/* ── Question selector ── */}
          <div className="status run-selector">
            <div className="section-heading">
              <h2>Question inspector</h2>
            </div>
            <div style={{ padding: "var(--sp-5)", display: "grid", gap: "var(--sp-2)" }}>
              <label>
                Select test question
                <select
                  value={selectedQuestionId}
                  onChange={(e) => handleQuestionChange(e.target.value)}
                >
                  {questions.map((q) => (
                    <option key={q.id} value={q.id}>{q.question_text}</option>
                  ))}
                </select>
              </label>
              {selectedQuestion && (
                <span className="badge badge-slate" style={{ justifySelf: "start" }}>
                  {selectedQuestion.question_type.replace(/_/g, " ")}
                </span>
              )}
            </div>
          </div>

          {/* ── Two-column: Chunks + Answers ── */}
          <div className="setup-grid two-column-grid">
            <SetupSection title="Retrieved Chunks" count={chunks.length}>
              <form className="compact-form" onSubmit={submitChunk}>
                <label>
                  Source document
                  <select name="sourceDocumentId" required>
                    <option value="">Select document</option>
                    {documents.map((doc) => (
                      <option key={doc.id} value={doc.id}>{doc.title}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Rank
                  <input name="rank" type="number" min={1} placeholder="1" required />
                </label>
                <label>
                  Chunk text
                  <textarea name="chunkText" placeholder="Retrieved chunk text" rows={4} required />
                </label>
                <label>
                  Section reference
                  <input name="sectionReference" placeholder="Section or page reference" />
                </label>
                <label>
                  Relevance label
                  <select name="relevanceLabel" defaultValue="">
                    <option value="">No label</option>
                    {relevanceLabels.map((l) => (
                      <option key={l} value={l}>{l}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Retrieval time (ms)
                  <input name="retrievalTimeMs" type="number" min={0} placeholder="e.g. 120" />
                </label>
                <button
                  type="submit"
                  className="btn btn-primary btn-sm"
                  disabled={!selectedQuestionId || documents.length === 0}
                >
                  Add chunk
                </button>
              </form>

              <OutputList
                items={chunks.map((c) => ({
                  title: `Rank ${c.rank}: ${c.section_reference ?? "No section"}`,
                  body:  c.chunk_text,
                  meta:  [c.relevance_label, c.retrieval_time_ms ? `${c.retrieval_time_ms}ms` : null]
                    .filter(Boolean).join(" · "),
                }))}
              />
            </SetupSection>

            <SetupSection title="Generated Answers" count={answers.length}>
              <form className="compact-form" onSubmit={submitAnswer}>
                <label>
                  Answer text
                  <textarea name="answerText" placeholder="Generated answer" rows={5} required />
                </label>
                <label>
                  Model name
                  <input name="modelName" placeholder="e.g. gemini-1.5-pro" />
                </label>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--sp-2)" }}>
                  <label>
                    Input tokens
                    <input name="inputTokens" type="number" min={0} placeholder="0" />
                  </label>
                  <label>
                    Output tokens
                    <input name="outputTokens" type="number" min={0} placeholder="0" />
                  </label>
                  <label>
                    Generation time (ms)
                    <input name="generationTimeMs" type="number" min={0} placeholder="0" />
                  </label>
                  <label>
                    Estimated cost ($)
                    <input name="estimatedCost" type="number" min={0} step="0.000001" placeholder="0.00" />
                  </label>
                </div>
                <button type="submit" className="btn btn-primary btn-sm" disabled={!selectedQuestionId}>
                  Add answer
                </button>
              </form>

              <OutputList
                items={answers.map((a) => ({
                  title: a.model_name ?? "Generated answer",
                  body:  a.answer_text,
                  meta:  [
                    a.input_tokens      ? `${a.input_tokens} in`    : null,
                    a.output_tokens     ? `${a.output_tokens} out`  : null,
                    a.generation_time_ms ? `${a.generation_time_ms}ms` : null,
                    a.estimated_cost    ? `$${a.estimated_cost}`    : null,
                  ].filter(Boolean).join(" · "),
                }))}
              />

              <EvaluationReviewList
                answers={answers}
                evaluations={evaluations}
                errorItems={errorTaxonomy?.items ?? []}
                onSubmit={submitEvaluation}
                onSubmitError={submitErrorAnnotation}
              />
            </SetupSection>
          </div>
        </div>
      </main>
    </div>
  );
}

/* ── Utility functions ── */
function optionalNumber(value: FormDataEntryValue | null): number | null {
  if (typeof value !== "string" || value.trim() === "") return null;
  return Number(value);
}

function optionalString(value: FormDataEntryValue | null): string | null {
  if (typeof value !== "string" || value.trim() === "") return null;
  return value;
}

function formatMetric(value: string | null): string { return value ?? "n/a"; }

function formatSignedMetric(value: string | null): string {
  if (value === null) return "n/a";
  const n = Number(value);
  if (Number.isNaN(n) || n === 0) return value;
  return n > 0 ? `+${value}` : value;
}

function formatBiasDirection(value: string): string {
  if (value === "automated_under_scores") return "Automated under-scores";
  if (value === "automated_over_scores")  return "Automated over-scores";
  return "Aligned";
}

function formatSeverity(value: ErrorSeverity): string {
  return errorSeverities.find((s) => s.value === value)?.label ?? value;
}

function highestSeverityLabel(items: Array<{ key: string; label: string; count: number }>): string {
  const order = ["critical", "high", "medium", "low"];
  return order
    .map((s) => items.find((i) => i.key === s && i.count > 0))
    .find(Boolean)?.label ?? "None";
}

function formatExpectedSourceMatch(value: boolean | null): string {
  if (value === null) return "No expected source";
  return value ? "Source matched" : "Source missed";
}

function formatReviewStatus(value: "pending_review" | "approved" | "needs_revision" | null): string {
  if (value === "approved")       return "Approved";
  if (value === "needs_revision") return "Needs revision";
  return "Pending review";
}
