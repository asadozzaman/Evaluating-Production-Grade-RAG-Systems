"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { FormEvent, useCallback, useEffect, useState } from "react";
import TopBar from "../../../components/TopBar";
import {
  BatchExperimentResult,
  DocumentIndexResult,
  EvaluationRun,
  ExperimentLeaderboard,
  Project,
  QuestionDataset,
  QuestionImportResult,
  RunComparison,
  SourceDocument,
  TOKEN_STORAGE_KEY,
  TestQuestion,
  authRequest,
  uploadRequest,
} from "../../../lib/auth";

const questionTypes = [
  "simple_factual",
  "conditional",
  "multi_document",
  "ambiguous",
  "edge_case",
];

/* ─────────────────────────────────────────
   Helper sub-components
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
}: Readonly<{ title: string; count: number; children: ReactNode }>) {
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

function SetupList({
  items,
}: Readonly<{
  items: Array<{
    title: string;
    meta: string;
    href?: string;
    actionLabel?: string;
    actionDisabled?: boolean;
    onAction?: () => void;
  }>;
}>) {
  if (items.length === 0) {
    return <p className="muted" style={{ fontStyle: "italic" }}>Nothing added yet.</p>;
  }

  return (
    <div className="mini-list">
      {items.map((item, index) => (
        <div className="mini-list-item" key={`${item.title}-${index}`}>
          <strong style={{ fontWeight: 600, fontSize: 13, color: "var(--text-primary)" }}>
            {item.title}
          </strong>
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{item.meta}</span>
          {item.onAction && (
            <button
              type="button"
              className="btn btn-outline btn-sm"
              onClick={item.onAction}
              disabled={item.actionDisabled}
              style={{ marginTop: 4, justifySelf: "start" }}
            >
              {item.actionLabel}
            </button>
          )}
          {item.href && (
            <Link href={item.href} className="btn btn-ghost btn-sm" style={{ marginTop: 4, justifySelf: "start", color: "var(--text-brand)" }}>
              Open run →
            </Link>
          )}
        </div>
      ))}
    </div>
  );
}

function RunComparisonView({ comparison }: Readonly<{ comparison: RunComparison }>) {
  return (
    <div className="comparison-results">
      <div className="metric-grid">
        {comparison.runs.map((run) => (
          <div className="metric-card" key={run.run_id}>
            <span>{run.run_name}</span>
            <strong>{run.average_overall_score ?? "Not scored"}</strong>
            <small style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
              {[run.retrieval_mode, run.generator_model_name, run.embedding_model_name, run.judge_model_name]
                .filter(Boolean)
                .join(" / ") || "No experiment metadata"}
            </small>
          </div>
        ))}
      </div>

      {comparison.runs.length > 0 && (
        <div className="dimension-list" style={{ marginTop: "var(--sp-3)" }}>
          {comparison.runs.map((run) => (
            <div className="mini-list-item" key={run.run_id}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: "var(--sp-4)" }}>
                <span style={{ fontWeight: 600, fontSize: 13 }}>{run.run_name}</span>
                <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                  Weakest: {run.weakest_dimension ?? "—"}
                </span>
              </div>
              <p style={{ margin: 0, fontSize: 12, color: "var(--text-muted)" }}>
                Generated {run.generated_answers}, reviewed {run.reviewed_answers}
              </p>
            </div>
          ))}
        </div>
      )}

      {Object.entries(comparison.metric_deltas).length > 0 && (
        <div className="mini-list">
          <h3 style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)", marginBottom: "var(--sp-2)" }}>
            Metric deltas vs. baseline
          </h3>
          {Object.entries(comparison.metric_deltas).map(([runId, deltas]) => (
            <div className="mini-list-item" key={runId}>
              <strong>Run {runId} vs baseline {comparison.baseline_run_id}</strong>
              <span>Overall delta: {formatDelta(deltas.overall_score_delta)}</span>
              <span>
                Citation {formatDelta(deltas.citation_quality_delta)} · Faithfulness{" "}
                {formatDelta(deltas.evidence_faithfulness_delta)} · Relevance{" "}
                {formatDelta(deltas.answer_relevance_delta)} · Retrieval{" "}
                {formatDelta(deltas.retrieval_quality_delta)}
              </span>
            </div>
          ))}
        </div>
      )}

      {comparison.question_results.length > 0 && (
        <div>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)", marginBottom: "var(--sp-2)" }}>
            Question-level comparison
          </h3>
          <div className="question-results">
            {comparison.question_results.map((question) => (
              <div className="mini-list-item" key={question.question_id}>
                <strong>{question.question_text}</strong>
                <span>Best run: {question.best_run_id ?? "Not enough scored answers"}</span>
                {question.run_results.map((result) => (
                  <p key={result.run_id}>
                    Run {result.run_id}: {result.overall_score ?? "Not scored"} /{" "}
                    {result.evaluation_mode ?? "not reviewed"} / {result.answer_text ?? "No answer"}
                  </p>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ExperimentLeaderboardView({
  leaderboard,
  projectId,
}: Readonly<{ leaderboard: ExperimentLeaderboard; projectId: string }>) {
  const bestRun = leaderboard.runs[0];

  return (
    <section className="status comparison-panel">
      <div className="section-heading">
        <h2>Experiment Leaderboard</h2>
        <span className="badge-count">{leaderboard.total_runs}</span>
      </div>

      <div style={{ padding: "var(--sp-5)" }}>
        <div className="metric-grid" style={{ marginBottom: "var(--sp-4)" }}>
          <MetricCard label="Best Run"          value={bestRun ? `#${bestRun.rank} Run ${bestRun.run_id}` : "None"} />
          <MetricCard label="Leaderboard Score" value={bestRun?.leaderboard_score ?? "n/a"} />
          <MetricCard label="Approved Average"  value={bestRun?.approved_average_overall_score ?? bestRun?.average_overall_score ?? "n/a"} />
        </div>

        {leaderboard.runs.length === 0 ? (
          <p className="muted" style={{ fontStyle: "italic" }}>
            Create and score runs to populate the leaderboard.
          </p>
        ) : (
          <div className="question-results">
            {leaderboard.runs.map((run) => (
              <div className="mini-list-item" key={run.run_id}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "var(--sp-4)" }}>
                  <strong>
                    #{run.rank} {run.run_name}
                  </strong>
                  <span style={{
                    fontSize: 14, fontWeight: 700,
                    color: run.rank === 1 ? "var(--brand-600)" : "var(--text-secondary)",
                  }}>
                    {run.leaderboard_score}
                  </span>
                </div>
                <span>
                  Score {run.approved_average_overall_score ?? run.average_overall_score ?? "not scored"} ·
                  Review {run.review_completion_percent}% ·
                  Hit rate {run.retrieval_hit_rate ?? "n/a"}
                </span>
                <span>
                  Judge agreement {run.judge_within_one_agreement_percent}% ({run.judge_paired_answer_count} pairs) ·
                  Errors {run.error_count} ·
                  Gate {formatQualityGate(run.quality_gate)}
                </span>
                <span>
                  {[run.retrieval_mode, run.generator_model_name, run.embedding_model_name, run.judge_model_name]
                    .filter(Boolean)
                    .join(" / ") || "No experiment metadata"}
                </span>
                <Link
                  href={`/dashboard/projects/${projectId}/runs/${run.run_id}`}
                  className="btn btn-outline btn-sm"
                  style={{ justifySelf: "start", marginTop: 4 }}
                >
                  Open run →
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────
   Main page component
───────────────────────────────────────── */

export default function ProjectDetailPage() {
  const params = useParams<{ projectId: string }>();
  const router = useRouter();
  const projectId = params.projectId;

  const [project, setProject]                       = useState<Project | null>(null);
  const [documents, setDocuments]                   = useState<SourceDocument[]>([]);
  const [questions, setQuestions]                   = useState<TestQuestion[]>([]);
  const [questionDatasets, setQuestionDatasets]     = useState<QuestionDataset[]>([]);
  const [runs, setRuns]                             = useState<EvaluationRun[]>([]);
  const [error, setError]                           = useState("");
  const [notice, setNotice]                         = useState("");
  const [documentSourceMode, setDocumentSourceMode] = useState<"uri" | "file">("uri");
  const [indexingDocumentId, setIndexingDocumentId] = useState<number | null>(null);
  const [selectedRunIds, setSelectedRunIds]         = useState<number[]>([]);
  const [comparison, setComparison]                 = useState<RunComparison | null>(null);
  const [leaderboard, setLeaderboard]               = useState<ExperimentLeaderboard | null>(null);
  const [isComparing, setIsComparing]               = useState(false);
  const [isImportingQuestions, setIsImportingQuestions] = useState(false);
  const [batchRunName, setBatchRunName]             = useState("Batch Gemini Evaluation");
  const [batchDatasetId, setBatchDatasetId]         = useState("");
  const [batchDocumentIds, setBatchDocumentIds]     = useState<number[]>([]);
  const [batchRetrievalMode, setBatchRetrievalMode] = useState<"keyword" | "vector">("keyword");
  const [shouldIndexDocuments, setShouldIndexDocuments] = useState(false);
  const [shouldAutoEvaluate, setShouldAutoEvaluate]     = useState(true);
  const [batchResult, setBatchResult]               = useState<BatchExperimentResult | null>(null);
  const [isBatchRunning, setIsBatchRunning]         = useState(false);

  const getToken = useCallback(() => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) { router.replace("/login"); return null; }
    return token;
  }, [router]);

  const loadProject = useCallback(async () => {
    const token = getToken();
    if (!token) return;

    try {
      const [projectData, documentData, questionData, datasetData, runData, leaderboardData] =
        await Promise.all([
          authRequest<Project>(`/projects/${projectId}`, { method: "GET" }, token),
          authRequest<SourceDocument[]>(`/projects/${projectId}/documents`, { method: "GET" }, token),
          authRequest<TestQuestion[]>(`/projects/${projectId}/questions`, { method: "GET" }, token),
          authRequest<QuestionDataset[]>(`/projects/${projectId}/question-datasets`, { method: "GET" }, token),
          authRequest<EvaluationRun[]>(`/projects/${projectId}/runs`, { method: "GET" }, token),
          authRequest<ExperimentLeaderboard>(`/projects/${projectId}/leaderboard`, { method: "GET" }, token),
        ]);
      setProject(projectData);
      setDocuments(documentData);
      setQuestions(questionData);
      setQuestionDatasets(datasetData);
      setRuns(runData);
      setLeaderboard(leaderboardData);
      setSelectedRunIds((current) => {
        if (current.length > 0) return current.filter((id) => runData.some((r) => r.id === id));
        return runData.slice(0, 2).map((r) => r.id);
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load project");
    }
  }, [getToken, projectId]);

  useEffect(() => { loadProject(); }, [loadProject]);

  useEffect(() => {
    if (!batchDatasetId && questionDatasets.length > 0) {
      setBatchDatasetId(String(questionDatasets[0].id));
    }
  }, [batchDatasetId, questionDatasets]);

  useEffect(() => {
    setBatchDocumentIds((current) => {
      const availableIds = documents.map((d) => d.id);
      const retainedIds  = current.filter((id) => availableIds.includes(id));
      if (retainedIds.length > 0 || availableIds.length === 0) return retainedIds;
      return availableIds;
    });
  }, [documents]);

  async function submitDocument(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(""); setNotice("");
    const token = getToken();
    if (!token) return;
    const form     = event.currentTarget;
    const formData = new FormData(form);

    try {
      if (documentSourceMode === "file") {
        const uploadData = new FormData();
        uploadData.set("title",         String(formData.get("title") ?? ""));
        uploadData.set("document_type", String(formData.get("documentType") ?? ""));
        const version = String(formData.get("version") ?? "");
        if (version) uploadData.set("version", version);
        const file = formData.get("file");
        if (file instanceof File) uploadData.set("file", file);
        await uploadRequest(`/projects/${projectId}/documents/upload`, uploadData, token);
      } else {
        await authRequest(
          `/projects/${projectId}/documents`,
          {
            method: "POST",
            body: JSON.stringify({
              title:         String(formData.get("title") ?? ""),
              document_type: String(formData.get("documentType") ?? ""),
              source_kind:   "uri",
              source_uri:    String(formData.get("sourceUri") ?? ""),
              version:       String(formData.get("version") ?? "") || null,
            }),
          },
          token,
        );
      }
      form.reset();
      loadProject();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save document");
    }
  }

  async function indexDocument(documentId: number) {
    setError(""); setNotice("");
    const token = getToken();
    if (!token) return;
    setIndexingDocumentId(documentId);
    try {
      const result = await authRequest<DocumentIndexResult>(
        `/projects/${projectId}/documents/${documentId}/index`,
        { method: "POST" },
        token,
      );
      setNotice(`${result.message} ${result.chunks_indexed} chunks saved with ${result.embedding_model}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to index document");
    } finally {
      setIndexingDocumentId(null);
    }
  }

  async function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const token = getToken();
    if (!token) return;
    const form     = event.currentTarget;
    const formData = new FormData(form);
    try {
      await authRequest(
        `/projects/${projectId}/questions`,
        {
          method: "POST",
          body: JSON.stringify({
            question_text:   String(formData.get("questionText") ?? ""),
            question_type:   String(formData.get("questionType") ?? ""),
            expected_source: String(formData.get("expectedSource") ?? "") || null,
          }),
        },
        token,
      );
      form.reset();
      loadProject();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save question");
    }
  }

  async function importQuestions(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(""); setNotice("");
    const token = getToken();
    if (!token) return;
    const form       = event.currentTarget;
    const formData   = new FormData(form);
    const uploadData = new FormData();
    uploadData.set("dataset_name", String(formData.get("datasetName") ?? ""));
    const datasetVersion = String(formData.get("datasetVersion") ?? "");
    if (datasetVersion) uploadData.set("dataset_version", datasetVersion);
    const file = formData.get("questionFile");
    if (file instanceof File) uploadData.set("file", file);

    setIsImportingQuestions(true);
    try {
      const result = await uploadRequest<QuestionImportResult>(
        `/projects/${projectId}/question-datasets/import`,
        uploadData,
        token,
      );
      setNotice(
        `Imported ${result.questions_imported} questions. Duplicates: ${result.duplicate_questions}. Invalid rows: ${result.invalid_rows}.`,
      );
      form.reset();
      await loadProject();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to import questions");
    } finally {
      setIsImportingQuestions(false);
    }
  }

  async function submitRun(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const token = getToken();
    if (!token) return;
    const form     = event.currentTarget;
    const formData = new FormData(form);
    try {
      await authRequest(
        `/projects/${projectId}/runs`,
        {
          method: "POST",
          body: JSON.stringify({
            name:           String(formData.get("name") ?? ""),
            system_version: String(formData.get("systemVersion") ?? "") || null,
            notes:          String(formData.get("notes") ?? "")          || null,
          }),
        },
        token,
      );
      form.reset();
      loadProject();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save run");
    }
  }

  async function compareSelectedRuns() {
    setError(""); setNotice(""); setComparison(null);
    const token = getToken();
    if (!token) return;
    if (selectedRunIds.length < 2) { setError("Select at least two runs to compare."); return; }

    const searchParams = new URLSearchParams();
    selectedRunIds.forEach((id) => searchParams.append("run_ids", String(id)));
    setIsComparing(true);
    try {
      const result = await authRequest<RunComparison>(
        `/projects/${projectId}/runs/compare?${searchParams.toString()}`,
        { method: "GET" },
        token,
      );
      setComparison(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to compare runs");
    } finally {
      setIsComparing(false);
    }
  }

  async function submitBatchExperiment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(""); setNotice(""); setBatchResult(null);
    const token = getToken();
    if (!token) return;
    if (!batchDatasetId)              { setError("Select a question dataset first.");      return; }
    if (batchDocumentIds.length === 0){ setError("Select at least one source document."); return; }

    const form     = event.currentTarget;
    const formData = new FormData(form);
    setIsBatchRunning(true);
    try {
      const result = await authRequest<BatchExperimentResult>(
        `/projects/${projectId}/batch-experiments`,
        {
          method: "POST",
          body: JSON.stringify({
            run_name:         batchRunName,
            dataset_id:       Number(batchDatasetId),
            document_ids:     batchDocumentIds,
            retrieval_mode:   batchRetrievalMode,
            system_version:   String(formData.get("systemVersion") ?? "") || null,
            notes:            String(formData.get("notes") ?? "")         || null,
            index_documents:  shouldIndexDocuments,
            auto_evaluate:    shouldAutoEvaluate,
          }),
        },
        token,
      );
      setBatchResult(result);
      setNotice(
        `${result.message} Run ${result.run.id}: ${result.rag_execution.generated_answers_created} answers generated.`,
      );
      await loadProject();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to run batch experiment");
    } finally {
      setIsBatchRunning(false);
    }
  }

  function toggleRunSelection(runId: number) {
    setSelectedRunIds((current) =>
      current.includes(runId) ? current.filter((id) => id !== runId) : [...current, runId],
    );
  }

  function toggleBatchDocument(documentId: number) {
    setBatchDocumentIds((current) =>
      current.includes(documentId)
        ? current.filter((id) => id !== documentId)
        : [...current, documentId],
    );
  }

  function handleLogout() {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    router.replace("/login");
  }

  /* ── Error / loading states ── */
  if (error && !project) {
    return (
      <div className="page-root">
        <TopBar onLogout={handleLogout} />
        <main className="page-body">
          <div className="shell">
            <p className="error" role="alert" style={{ marginBottom: "var(--sp-4)" }}>{error}</p>
            <Link href="/dashboard/projects" className="btn btn-secondary">← Back to projects</Link>
          </div>
        </main>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="page-root">
        <TopBar onLogout={handleLogout} />
        <main className="page-body">
          <div className="wide-shell animate-in" style={{ paddingTop: "var(--sp-4)" }}>
            <div className="skeleton skeleton-heading" style={{ width: "30%", marginBottom: "var(--sp-4)" }} />
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: "var(--sp-4)" }}>
              {[1,2,3].map((i) => <div key={i} className="skeleton" style={{ height: 280 }} />)}
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
      </TopBar>

      <main className="page-body">
        <div className="wide-shell animate-in">
          {/* Breadcrumb */}
          <nav className="breadcrumb" aria-label="Breadcrumb">
            <Link href="/dashboard">Dashboard</Link>
            <span className="breadcrumb-sep" aria-hidden="true">›</span>
            <Link href="/dashboard/projects">Projects</Link>
            <span className="breadcrumb-sep" aria-hidden="true">›</span>
            <span className="breadcrumb-current">{project.name}</span>
          </nav>

          {/* Header */}
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "var(--sp-4)", flexWrap: "wrap", paddingBottom: "var(--sp-5)", borderBottom: "1px solid var(--border)", marginBottom: "var(--sp-6)" }}>
            <div>
              <h1 style={{ marginBottom: 6 }}>{project.name}</h1>
              <p style={{ fontSize: 14, color: "var(--text-muted)" }}>
                {project.system_type.replace(/_/g, " ")} · {project.target_users}
              </p>
            </div>
            <div style={{ display: "flex", gap: "var(--sp-2)", flexWrap: "wrap" }}>
              <Link href={`/dashboard/projects/${projectId}/runs/${runs[0]?.id ?? ""}`} className="btn btn-primary" style={{ display: runs.length === 0 ? "none" : undefined }}>
                Open latest run →
              </Link>
            </div>
          </div>

          {/* Feedback */}
          {error  && <p className="error"   role="alert"   style={{ marginBottom: "var(--sp-4)" }}>{error}</p>}
          {notice && <p className="success" role="status" style={{ marginBottom: "var(--sp-4)" }}>{notice}</p>}

          {/* ── Setup grid: Documents · Questions · Runs ── */}
          <div className="setup-grid">
            {/* Documents */}
            <SetupSection title="Source Documents" count={documents.length}>
              <div className="segmented-control" aria-label="Document source">
                <button
                  type="button"
                  className={`seg-btn${documentSourceMode === "uri" ? " seg-btn-active" : ""}`}
                  onClick={() => setDocumentSourceMode("uri")}
                  aria-pressed={documentSourceMode === "uri"}
                >
                  URI
                </button>
                <button
                  type="button"
                  className={`seg-btn${documentSourceMode === "file" ? " seg-btn-active" : ""}`}
                  onClick={() => setDocumentSourceMode("file")}
                  aria-pressed={documentSourceMode === "file"}
                >
                  Upload
                </button>
              </div>

              <form className="compact-form" onSubmit={submitDocument}>
                <input name="title"        placeholder="Document title"  required />
                <input name="documentType" placeholder="Document type"   required />
                {documentSourceMode === "uri" ? (
                  <input name="sourceUri" placeholder="https://..." required />
                ) : (
                  <input name="file" type="file" accept=".pdf,.docx,.txt,.csv,.md" required />
                )}
                <input name="version" placeholder="Version (optional)" />
                <button type="submit" className="btn btn-primary btn-sm">
                  {documentSourceMode === "file" ? "Upload document" : "Add document"}
                </button>
              </form>

              <SetupList
                items={documents.map((doc) => ({
                  title: doc.title,
                  meta: [doc.source_kind, doc.document_type, doc.version,
                         doc.source_kind === "file" ? doc.original_file_name : doc.source_uri]
                    .filter(Boolean).join(" · "),
                  actionLabel:    indexingDocumentId === doc.id ? "Indexing…" : "Index for vector search",
                  actionDisabled: indexingDocumentId !== null || doc.source_kind !== "file",
                  onAction:       () => indexDocument(doc.id),
                }))}
              />
            </SetupSection>

            {/* Questions */}
            <SetupSection title="Test Questions" count={questions.length}>
              <form className="compact-form" onSubmit={importQuestions}>
                <input name="datasetName"    placeholder="Dataset name"    required />
                <input name="datasetVersion" placeholder="Dataset version (optional)" />
                <input name="questionFile"   type="file" accept=".csv,.json" required />
                <button type="submit" className="btn btn-primary btn-sm" disabled={isImportingQuestions}>
                  {isImportingQuestions ? "Importing…" : "Import question set"}
                </button>
              </form>

              <SetupList
                items={questionDatasets.map((ds) => ({
                  title: ds.dataset_name,
                  meta: [ds.dataset_version, `${ds.question_count} questions`, ds.imported_file_name]
                    .filter(Boolean).join(" / "),
                }))}
              />

              <div style={{ borderTop: "1px solid var(--border)", paddingTop: "var(--sp-4)" }}>
                <p style={{ fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: "var(--sp-2)" }}>
                  Add single question
                </p>
                <form className="compact-form" onSubmit={submitQuestion}>
                  <textarea name="questionText" placeholder="Question text" rows={3} required />
                  <select name="questionType" defaultValue="simple_factual" required>
                    {questionTypes.map((qt) => (
                      <option key={qt} value={qt}>{qt.replace(/_/g, " ")}</option>
                    ))}
                  </select>
                  <input name="expectedSource" placeholder="Expected source (optional)" />
                  <button type="submit" className="btn btn-outline btn-sm">Add question</button>
                </form>
              </div>

              <SetupList
                items={questions.map((q) => ({
                  title: q.question_text,
                  meta:  q.question_type.replace(/_/g, " "),
                }))}
              />
            </SetupSection>

            {/* Runs */}
            <SetupSection title="Evaluation Runs" count={runs.length}>
              <form className="compact-form" onSubmit={submitRun}>
                <input name="name"          placeholder="Run name"           required />
                <input name="systemVersion" placeholder="System version" />
                <textarea name="notes" placeholder="Notes (optional)" rows={2} />
                <button type="submit" className="btn btn-primary btn-sm">Create run</button>
              </form>

              <SetupList
                items={runs.map((run) => ({
                  title: run.name,
                  meta:  run.system_version ?? "No version",
                  href:  `/dashboard/projects/${projectId}/runs/${run.id}`,
                }))}
              />
            </SetupSection>
          </div>

          {/* ── Batch Experiment ── */}
          <section className="status comparison-panel">
            <div className="section-heading">
              <h2>Batch Experiment</h2>
              <span className="badge-count">{batchResult ? `Run ${batchResult.run.id}` : "New"}</span>
            </div>

            <form className="compact-form" style={{ padding: "var(--sp-5)" }} onSubmit={submitBatchExperiment}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--sp-3)" }}>
                <label>
                  Run name
                  <input
                    name="runName"
                    placeholder="Run name"
                    required
                    value={batchRunName}
                    onChange={(e) => setBatchRunName(e.target.value)}
                  />
                </label>
                <label>
                  System version
                  <input name="systemVersion" placeholder="v1.0" />
                </label>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--sp-3)" }}>
                <label>
                  Question dataset
                  <select
                    name="datasetId"
                    required
                    value={batchDatasetId}
                    onChange={(e) => setBatchDatasetId(e.target.value)}
                  >
                    <option value="">Select dataset</option>
                    {questionDatasets.map((ds) => (
                      <option key={ds.id} value={ds.id}>
                        {ds.dataset_name} ({ds.question_count} questions)
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Retrieval mode
                  <select
                    name="retrievalMode"
                    value={batchRetrievalMode}
                    onChange={(e) => setBatchRetrievalMode(e.target.value as "keyword" | "vector")}
                  >
                    <option value="keyword">Keyword retrieval</option>
                    <option value="vector">Vector retrieval</option>
                  </select>
                </label>
              </div>

              <textarea name="notes" placeholder="Notes (optional)" rows={2} />

              {/* Document checkboxes */}
              <div>
                <p style={{ fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: "var(--sp-2)" }}>
                  Source documents
                </p>
                {documents.length === 0 ? (
                  <p className="muted" style={{ fontStyle: "italic" }}>Upload at least one document first.</p>
                ) : (
                  <div className="comparison-selector" style={{ padding: 0 }}>
                    {documents.map((doc) => (
                      <label key={doc.id} className="checkbox-row">
                        <input
                          type="checkbox"
                          checked={batchDocumentIds.includes(doc.id)}
                          onChange={() => toggleBatchDocument(doc.id)}
                        />
                        <span>
                          {doc.title}
                          {doc.source_kind === "file"
                            ? ` — ${doc.original_file_name}`
                            : ` — ${doc.source_uri}`}
                        </span>
                      </label>
                    ))}
                  </div>
                )}
              </div>

              <div style={{ display: "grid", gap: "var(--sp-2)" }}>
                <label className="checkbox-row">
                  <input
                    type="checkbox"
                    checked={shouldIndexDocuments}
                    onChange={(e) => setShouldIndexDocuments(e.target.checked)}
                  />
                  <span>Index selected documents before vector retrieval</span>
                </label>
                <label className="checkbox-row">
                  <input
                    type="checkbox"
                    checked={shouldAutoEvaluate}
                    onChange={(e) => setShouldAutoEvaluate(e.target.checked)}
                  />
                  <span>Run automated CLEAR-RAG evaluation after Gemini answers</span>
                </label>
              </div>

              <div>
                <button
                  type="submit"
                  className={`btn btn-primary${isBatchRunning ? " btn-loading" : ""}`}
                  disabled={isBatchRunning || !batchDatasetId || batchDocumentIds.length === 0}
                >
                  {isBatchRunning ? "" : "Run batch experiment"}
                </button>
              </div>
            </form>

            {batchResult && (
              <div style={{ padding: "0 var(--sp-5) var(--sp-5)" }}>
                <div className="metric-grid">
                  <MetricCard label="Run ID"             value={batchResult.run.id} />
                  <MetricCard label="Questions"          value={batchResult.rag_execution.processed_questions} />
                  <MetricCard label="Answers generated"  value={batchResult.rag_execution.generated_answers_created} />
                  <MetricCard label="Reviewed answers"   value={batchResult.summary.reviewed_answers} />
                  <MetricCard label="Average overall"    value={batchResult.summary.average_overall_score ?? "Not scored"} />
                  <MetricCard label="Weakest dimension"  value={batchResult.summary.weakest_dimension ?? "Not scored"} />
                </div>
              </div>
            )}
          </section>

          {/* ── Leaderboard ── */}
          {leaderboard && (
            <ExperimentLeaderboardView leaderboard={leaderboard} projectId={projectId} />
          )}

          {/* ── Run Comparison ── */}
          <section className="status comparison-panel">
            <div className="section-heading">
              <h2>Run Comparison</h2>
              <span className="badge-count">{selectedRunIds.length} selected</span>
            </div>

            <div style={{ padding: "var(--sp-5)" }}>
              {runs.length === 0 ? (
                <p className="muted" style={{ fontStyle: "italic" }}>
                  Create at least two runs to compare experiments.
                </p>
              ) : (
                <div className="comparison-selector" style={{ padding: 0, marginBottom: "var(--sp-4)" }}>
                  {runs.map((run) => (
                    <label key={run.id} className="checkbox-row">
                      <input
                        type="checkbox"
                        checked={selectedRunIds.includes(run.id)}
                        onChange={() => toggleRunSelection(run.id)}
                      />
                      <span>
                        {run.name}{run.retrieval_mode ? ` — ${run.retrieval_mode}` : ""}
                      </span>
                    </label>
                  ))}
                </div>
              )}

              <button
                type="button"
                className={`btn btn-secondary${isComparing ? " btn-loading" : ""}`}
                onClick={compareSelectedRuns}
                disabled={isComparing || selectedRunIds.length < 2}
              >
                {isComparing ? "" : "Compare selected runs"}
              </button>
            </div>

            {comparison && <RunComparisonView comparison={comparison} />}
          </section>
        </div>
      </main>
    </div>
  );
}

/* ── Utility formatters ── */
function formatDelta(value: string | null): string {
  if (value === null) return "n/a";
  const n = Number(value);
  return n > 0 ? `+${value}` : value;
}

function formatQualityGate(value: string): string {
  return value.split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
}
