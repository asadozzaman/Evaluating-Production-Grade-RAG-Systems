"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import {
  API_URL,
  AutoEvaluationResult,
  EvaluationRun,
  EvaluationRecord,
  ErrorAnnotation,
  ErrorCategory,
  ErrorSeverity,
  ErrorTaxonomyReport,
  GeneratedAnswer,
  JudgeCalibrationReport,
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

const relevanceLabels = ["high", "medium", "low", "irrelevant"];
const scoreOptions = [1, 2, 3, 4, 5];
const errorCategories: Array<{ value: ErrorCategory; label: string }> = [
  { value: "retrieval_miss", label: "Retrieval Miss" },
  { value: "citation_error", label: "Citation Error" },
  { value: "hallucination", label: "Hallucination" },
  { value: "incomplete_answer", label: "Incomplete Answer" },
  { value: "irrelevant_answer", label: "Irrelevant Answer" },
  { value: "contradiction", label: "Contradiction" },
  { value: "latency_cost", label: "Latency or Cost" },
  { value: "format_error", label: "Format Error" },
  { value: "policy_ambiguity", label: "Policy Ambiguity" },
  { value: "other", label: "Other" },
];
const errorSeverities: Array<{ value: ErrorSeverity; label: string }> = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
  { value: "critical", label: "Critical" },
];
const retrievalModes = [
  { value: "keyword", label: "Keyword matching" },
  { value: "vector", label: "Vector embeddings" },
] as const;
const dimensionLabels: Array<[keyof RunSummary["dimension_averages"], string]> = [
  ["citation_quality_score", "Citation Quality"],
  ["latency_cost_score", "Latency and Cost"],
  ["evidence_faithfulness_score", "Evidence Faithfulness"],
  ["answer_relevance_score", "Answer Relevance"],
  ["retrieval_quality_score", "Retrieval Quality"],
];

export default function RunOutputPage() {
  const params = useParams<{ projectId: string; runId: string }>();
  const router = useRouter();
  const projectId = params.projectId;
  const runId = params.runId;
  const [project, setProject] = useState<Project | null>(null);
  const [run, setRun] = useState<EvaluationRun | null>(null);
  const [documents, setDocuments] = useState<SourceDocument[]>([]);
  const [questions, setQuestions] = useState<TestQuestion[]>([]);
  const [selectedQuestionId, setSelectedQuestionId] = useState("");
  const [chunks, setChunks] = useState<RetrievedChunk[]>([]);
  const [answers, setAnswers] = useState<GeneratedAnswer[]>([]);
  const [evaluations, setEvaluations] = useState<EvaluationRecord[]>([]);
  const [summary, setSummary] = useState<RunSummary | null>(null);
  const [reviewDashboard, setReviewDashboard] = useState<RunReviewDashboard | null>(null);
  const [judgeCalibration, setJudgeCalibration] = useState<JudgeCalibrationReport | null>(null);
  const [errorTaxonomy, setErrorTaxonomy] = useState<ErrorTaxonomyReport | null>(null);
  const [executionResult, setExecutionResult] = useState<RagExecutionResult | null>(null);
  const [autoEvaluationResult, setAutoEvaluationResult] = useState<AutoEvaluationResult | null>(null);
  const [retrievalMode, setRetrievalMode] = useState<"keyword" | "vector">("keyword");
  const [isExecuting, setIsExecuting] = useState(false);
  const [isAutoEvaluating, setIsAutoEvaluating] = useState(false);
  const [error, setError] = useState("");

  const selectedQuestion = useMemo(
    () => questions.find((question) => String(question.id) === selectedQuestionId),
    [questions, selectedQuestionId],
  );

  const getToken = useCallback(() => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) {
      router.replace("/login");
      return null;
    }
    return token;
  }, [router]);

  const loadOutputs = useCallback(
    async (questionId: string) => {
      const token = getToken();
      if (!token || !questionId) {
        setChunks([]);
        setAnswers([]);
        return;
      }

      const [chunkData, answerData, evaluationData] = await Promise.all([
        authRequest<RetrievedChunk[]>(
          `/projects/${projectId}/runs/${runId}/questions/${questionId}/retrieved-chunks`,
          { method: "GET" },
          token,
        ),
        authRequest<GeneratedAnswer[]>(
          `/projects/${projectId}/runs/${runId}/questions/${questionId}/generated-answers`,
          { method: "GET" },
          token,
        ),
        authRequest<EvaluationRecord[]>(
          `/projects/${projectId}/runs/${runId}/evaluations`,
          { method: "GET" },
          token,
        ),
      ]);
      setChunks(chunkData);
      setAnswers(answerData);
      setEvaluations(evaluationData);
    },
    [getToken, projectId, runId],
  );

  const loadSummary = useCallback(async () => {
    const token = getToken();
    if (!token) {
      return;
    }
    const [summaryData, reviewDashboardData, judgeCalibrationData, errorTaxonomyData] = await Promise.all([
      authRequest<RunSummary>(
        `/projects/${projectId}/runs/${runId}/summary`,
        { method: "GET" },
        token,
      ),
      authRequest<RunReviewDashboard>(
        `/projects/${projectId}/runs/${runId}/review-dashboard`,
        { method: "GET" },
        token,
      ),
      authRequest<JudgeCalibrationReport>(
        `/projects/${projectId}/runs/${runId}/judge-calibration`,
        { method: "GET" },
        token,
      ),
      authRequest<ErrorTaxonomyReport>(
        `/projects/${projectId}/runs/${runId}/error-taxonomy`,
        { method: "GET" },
        token,
      ),
    ]);
    setSummary(summaryData);
    setReviewDashboard(reviewDashboardData);
    setJudgeCalibration(judgeCalibrationData);
    setErrorTaxonomy(errorTaxonomyData);
  }, [getToken, projectId, runId]);

  const loadPage = useCallback(async () => {
    const token = getToken();
    if (!token) {
      return;
    }

    try {
      const [projectData, runData, documentData, questionData, summaryData, reviewDashboardData, judgeCalibrationData, errorTaxonomyData] = await Promise.all([
        authRequest<Project>(`/projects/${projectId}`, { method: "GET" }, token),
        authRequest<EvaluationRun>(`/projects/${projectId}/runs/${runId}`, { method: "GET" }, token),
        authRequest<SourceDocument[]>(`/projects/${projectId}/documents`, { method: "GET" }, token),
        authRequest<TestQuestion[]>(`/projects/${projectId}/questions`, { method: "GET" }, token),
        authRequest<RunSummary>(`/projects/${projectId}/runs/${runId}/summary`, { method: "GET" }, token),
        authRequest<RunReviewDashboard>(`/projects/${projectId}/runs/${runId}/review-dashboard`, { method: "GET" }, token),
        authRequest<JudgeCalibrationReport>(`/projects/${projectId}/runs/${runId}/judge-calibration`, { method: "GET" }, token),
        authRequest<ErrorTaxonomyReport>(`/projects/${projectId}/runs/${runId}/error-taxonomy`, { method: "GET" }, token),
      ]);
      setProject(projectData);
      setRun(runData);
      setDocuments(documentData);
      setQuestions(questionData);
      setSummary(summaryData);
      setReviewDashboard(reviewDashboardData);
      setJudgeCalibration(judgeCalibrationData);
      setErrorTaxonomy(errorTaxonomyData);
      const firstQuestionId = questionData[0] ? String(questionData[0].id) : "";
      setSelectedQuestionId((current) => current || firstQuestionId);
      if (firstQuestionId) {
        await loadOutputs(firstQuestionId);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load run");
    }
  }, [getToken, loadOutputs, projectId, runId]);

  useEffect(() => {
    loadPage();
  }, [loadPage]);

  async function handleQuestionChange(questionId: string) {
    setSelectedQuestionId(questionId);
    setError("");
    try {
      await loadOutputs(questionId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load outputs");
    }
  }

  async function submitChunk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const token = getToken();
    if (!token || !selectedQuestionId) {
      return;
    }

    const form = event.currentTarget;
    const formData = new FormData(form);
    try {
      await authRequest(
        `/projects/${projectId}/runs/${runId}/questions/${selectedQuestionId}/retrieved-chunks`,
        {
          method: "POST",
          body: JSON.stringify({
            source_document_id: Number(formData.get("sourceDocumentId")),
            rank: Number(formData.get("rank")),
            chunk_text: String(formData.get("chunkText") ?? ""),
            section_reference: String(formData.get("sectionReference") ?? "") || null,
            relevance_label: String(formData.get("relevanceLabel") ?? "") || null,
            retrieval_time_ms: optionalNumber(formData.get("retrievalTimeMs")),
          }),
        },
        token,
      );
      form.reset();
      await loadOutputs(selectedQuestionId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save retrieved chunk");
    }
  }

  async function submitAnswer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const token = getToken();
    if (!token || !selectedQuestionId) {
      return;
    }

    const form = event.currentTarget;
    const formData = new FormData(form);
    try {
      await authRequest(
        `/projects/${projectId}/runs/${runId}/questions/${selectedQuestionId}/generated-answers`,
        {
          method: "POST",
          body: JSON.stringify({
            answer_text: String(formData.get("answerText") ?? ""),
            model_name: String(formData.get("modelName") ?? "") || null,
            input_tokens: optionalNumber(formData.get("inputTokens")),
            output_tokens: optionalNumber(formData.get("outputTokens")),
            generation_time_ms: optionalNumber(formData.get("generationTimeMs")),
            estimated_cost: optionalString(formData.get("estimatedCost")),
          }),
        },
        token,
      );
      form.reset();
      await loadOutputs(selectedQuestionId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save generated answer");
    }
  }

  async function executeGeminiRag() {
    setError("");
    setExecutionResult(null);
    const token = getToken();
    if (!token) {
      return;
    }

    setIsExecuting(true);
    try {
      const result = await authRequest<RagExecutionResult>(
        `/projects/${projectId}/runs/${runId}/execute`,
        {
          method: "POST",
          body: JSON.stringify({ retrieval_mode: retrievalMode }),
        },
        token,
      );
      setExecutionResult(result);
      const refreshedRun = await authRequest<EvaluationRun>(`/projects/${projectId}/runs/${runId}`, { method: "GET" }, token);
      setRun(refreshedRun);
      if (selectedQuestionId) {
        await loadOutputs(selectedQuestionId);
      }
      await loadSummary();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to run Gemini RAG");
      const refreshedRun = await authRequest<EvaluationRun>(`/projects/${projectId}/runs/${runId}`, { method: "GET" }, token).catch(() => null);
      if (refreshedRun) {
        setRun(refreshedRun);
      }
      await loadSummary().catch(() => undefined);
    } finally {
      setIsExecuting(false);
    }
  }

  async function runAutomatedEvaluation() {
    setError("");
    setAutoEvaluationResult(null);
    const token = getToken();
    if (!token) {
      return;
    }

    setIsAutoEvaluating(true);
    try {
      const result = await authRequest<AutoEvaluationResult>(
        `/projects/${projectId}/runs/${runId}/auto-evaluate`,
        { method: "POST" },
        token,
      );
      setAutoEvaluationResult(result);
      if (selectedQuestionId) {
        await loadOutputs(selectedQuestionId);
      }
      await loadSummary();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to run automated CLEAR-RAG evaluation");
    } finally {
      setIsAutoEvaluating(false);
    }
  }

  async function submitEvaluation(answerId: number, event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const token = getToken();
    if (!token || !selectedQuestionId) {
      return;
    }

    const form = event.currentTarget;
    const formData = new FormData(form);
    try {
      await authRequest(
        `/projects/${projectId}/runs/${runId}/questions/${selectedQuestionId}/answers/${answerId}/evaluations`,
        {
          method: "POST",
          body: JSON.stringify({
            citation_quality_score: Number(formData.get("citationQualityScore")),
            latency_cost_score: Number(formData.get("latencyCostScore")),
            evidence_faithfulness_score: Number(formData.get("evidenceFaithfulnessScore")),
            answer_relevance_score: Number(formData.get("answerRelevanceScore")),
            retrieval_quality_score: Number(formData.get("retrievalQualityScore")),
            reviewer_notes: optionalString(formData.get("reviewerNotes")),
            suggested_improvement: optionalString(formData.get("suggestedImprovement")),
          }),
        },
        token,
      );
      form.reset();
      await loadOutputs(selectedQuestionId);
      await loadSummary();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save evaluation");
    }
  }

  async function submitErrorAnnotation(answerId: number, event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const token = getToken();
    if (!token || !selectedQuestionId) {
      return;
    }

    const form = event.currentTarget;
    const formData = new FormData(form);
    try {
      await authRequest<ErrorAnnotation>(
        `/projects/${projectId}/runs/${runId}/questions/${selectedQuestionId}/answers/${answerId}/errors`,
        {
          method: "POST",
          body: JSON.stringify({
            category: String(formData.get("category") ?? "other"),
            severity: String(formData.get("severity") ?? "medium"),
            evaluation_record_id: optionalNumber(formData.get("evaluationRecordId")),
            notes: optionalString(formData.get("notes")),
            evidence_reference: optionalString(formData.get("evidenceReference")),
          }),
        },
        token,
      );
      form.reset();
      await loadSummary();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save error annotation");
    }
  }

  async function submitReview(evaluationId: number, event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const token = getToken();
    if (!token) {
      return;
    }

    const form = event.currentTarget;
    const formData = new FormData(form);
    try {
      await authRequest<EvaluationRecord>(
        `/projects/${projectId}/runs/${runId}/evaluations/${evaluationId}/review`,
        {
          method: "PATCH",
          body: JSON.stringify({
            review_status: String(formData.get("reviewStatus") ?? "approved"),
            citation_quality_score: optionalNumber(formData.get("citationQualityScore")),
            latency_cost_score: optionalNumber(formData.get("latencyCostScore")),
            evidence_faithfulness_score: optionalNumber(formData.get("evidenceFaithfulnessScore")),
            answer_relevance_score: optionalNumber(formData.get("answerRelevanceScore")),
            retrieval_quality_score: optionalNumber(formData.get("retrievalQualityScore")),
            review_notes: optionalString(formData.get("reviewNotes")),
            score_change_reason: optionalString(formData.get("scoreChangeReason")),
            reviewer_notes: optionalString(formData.get("reviewerNotes")),
            suggested_improvement: optionalString(formData.get("suggestedImprovement")),
          }),
        },
        token,
      );
      form.reset();
      if (selectedQuestionId) {
        await loadOutputs(selectedQuestionId);
      }
      await loadSummary();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save review decision");
    }
  }

  async function downloadExport(format: "csv" | "json") {
    const token = getToken();
    if (!token) {
      return;
    }
    try {
      const response = await fetch(`${API_URL}/projects/${projectId}/runs/${runId}/export.${format}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail ?? "Unable to download export");
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `clear-rag-run-${runId}.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to download export");
    }
  }

  if (error && (!project || !run)) {
    return (
      <main>
        <section className="shell">
          <p className="error">{error}</p>
          <p className="auth-switch">
            <Link href={`/dashboard/projects/${projectId}`}>Back to project</Link>
          </p>
        </section>
      </main>
    );
  }

  if (!project || !run) {
    return (
      <main>
        <section className="shell">
          <p className="summary">Loading run...</p>
        </section>
      </main>
    );
  }

  return (
    <main>
      <section className="wide-shell">
        <div className="dashboard-header">
          <div>
            <p className="eyebrow">{project.name}</p>
            <h1>{run.name}</h1>
          </div>
          <Link className="secondary-button" href={`/dashboard/projects/${projectId}`}>
            Project setup
          </Link>
        </div>

        <p className="summary">
          Run Gemini RAG automatically, or manually add retrieved chunks and generated answers for inspection.
        </p>
        {error ? <p className="error">{error}</p> : null}
        {run.last_error ? <p className="error">{run.last_error}</p> : null}

        <div className="status run-status-panel">
          <div className="status-row">
            <span>Run status</span>
            <span>{run.status}</span>
          </div>
          <div className="status-row">
            <span>Processed questions</span>
            <span>{run.processed_question_count}</span>
          </div>
          <label>
            Retrieval mode
            <select
              value={retrievalMode}
              onChange={(event) => setRetrievalMode(event.target.value as "keyword" | "vector")}
            >
              {retrievalModes.map((mode) => (
                <option key={mode.value} value={mode.value}>
                  {mode.label}
                </option>
              ))}
            </select>
          </label>
          <div className="actions compact-actions">
            <button type="button" onClick={executeGeminiRag} disabled={isExecuting || documents.length === 0 || questions.length === 0}>
              {isExecuting ? "Running Gemini RAG..." : "Run Gemini RAG"}
            </button>
            <button type="button" onClick={runAutomatedEvaluation} disabled={isAutoEvaluating || answers.length === 0}>
              {isAutoEvaluating ? "Evaluating..." : "Run Automated CLEAR-RAG Evaluation"}
            </button>
          </div>
          {executionResult ? (
            <p className="muted">
              {executionResult.message} {executionResult.retrieved_chunks_created} chunks and {executionResult.generated_answers_created} answers saved with {executionResult.model_name}.
            </p>
          ) : null}
          {autoEvaluationResult ? (
            <p className="muted">
              {autoEvaluationResult.message} {autoEvaluationResult.evaluated_answers} answers scored with {autoEvaluationResult.judge_model_name}.
            </p>
          ) : null}
        </div>

        {summary ? <RunAnalytics summary={summary} onDownload={downloadExport} /> : null}
        {reviewDashboard ? (
          <ReviewDashboard dashboard={reviewDashboard} onSubmitReview={submitReview} />
        ) : null}
        {judgeCalibration ? <JudgeCalibrationPanel report={judgeCalibration} /> : null}
        {errorTaxonomy ? <ErrorTaxonomyPanel report={errorTaxonomy} /> : null}

        <div className="status run-selector">
          <label>
            Test question
            <select
              value={selectedQuestionId}
              onChange={(event) => handleQuestionChange(event.target.value)}
            >
              {questions.map((question) => (
                <option key={question.id} value={question.id}>
                  {question.question_text}
                </option>
              ))}
            </select>
          </label>
          {selectedQuestion ? <p className="muted">{selectedQuestion.question_type}</p> : null}
        </div>

        <div className="setup-grid two-column-grid">
          <SetupSection title="Retrieved Chunks" count={chunks.length}>
            <form className="compact-form" onSubmit={submitChunk}>
              <select name="sourceDocumentId" required>
                <option value="">Source document</option>
                {documents.map((document) => (
                  <option key={document.id} value={document.id}>
                    {document.title}
                  </option>
                ))}
              </select>
              <input name="rank" type="number" min={1} placeholder="Rank" required />
              <textarea name="chunkText" placeholder="Retrieved chunk text" rows={5} required />
              <input name="sectionReference" placeholder="Section reference" />
              <select name="relevanceLabel" defaultValue="">
                <option value="">Relevance label</option>
                {relevanceLabels.map((label) => (
                  <option key={label} value={label}>
                    {label}
                  </option>
                ))}
              </select>
              <input name="retrievalTimeMs" type="number" min={0} placeholder="Retrieval time ms" />
              <button type="submit" disabled={!selectedQuestionId || documents.length === 0}>
                Add chunk
              </button>
            </form>
            <OutputList
              items={chunks.map((chunk) => ({
                title: `Rank ${chunk.rank}: ${chunk.section_reference ?? "No section"}`,
                body: chunk.chunk_text,
                meta: [chunk.relevance_label, chunk.retrieval_time_ms ? `${chunk.retrieval_time_ms}ms` : null]
                  .filter(Boolean)
                  .join(" · "),
              }))}
            />
          </SetupSection>

          <SetupSection title="Generated Answers" count={answers.length}>
            <form className="compact-form" onSubmit={submitAnswer}>
              <textarea name="answerText" placeholder="Generated answer" rows={6} required />
              <input name="modelName" placeholder="Gemini model name, not API key" />
              <input name="inputTokens" type="number" min={0} placeholder="Input tokens" />
              <input name="outputTokens" type="number" min={0} placeholder="Output tokens" />
              <input name="generationTimeMs" type="number" min={0} placeholder="Generation time ms" />
              <input name="estimatedCost" type="number" min={0} step="0.000001" placeholder="Estimated cost" />
              <button type="submit" disabled={!selectedQuestionId}>
                Add answer
              </button>
            </form>
            <OutputList
              items={answers.map((answer) => ({
                title: answer.model_name ?? "Generated answer",
                body: answer.answer_text,
                meta: [
                  answer.input_tokens ? `${answer.input_tokens} input` : null,
                  answer.output_tokens ? `${answer.output_tokens} output` : null,
                  answer.generation_time_ms ? `${answer.generation_time_ms}ms` : null,
                  answer.estimated_cost ? `$${answer.estimated_cost}` : null,
                ]
                  .filter(Boolean)
                  .join(" · "),
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
      </section>
    </main>
  );
}

function optionalNumber(value: FormDataEntryValue | null): number | null {
  if (typeof value !== "string" || value.trim() === "") {
    return null;
  }
  return Number(value);
}

function optionalString(value: FormDataEntryValue | null): string | null {
  if (typeof value !== "string" || value.trim() === "") {
    return null;
  }
  return value;
}

function RunAnalytics({
  summary,
  onDownload,
}: Readonly<{
  summary: RunSummary;
  onDownload: (format: "csv" | "json") => void;
}>) {
  return (
    <section className="status analytics-panel">
      <div className="section-heading">
        <h2>Evaluation Summary</h2>
        <div className="actions compact-actions">
          <button type="button" onClick={() => onDownload("csv")}>
            Export CSV
          </button>
          <button type="button" onClick={() => onDownload("json")}>
            Export JSON
          </button>
        </div>
      </div>
      <div className="metric-grid">
        <MetricCard label="Questions" value={summary.total_questions} />
        <MetricCard label="Generated Answers" value={summary.generated_answers} />
        <MetricCard label="Reviewed Answers" value={summary.reviewed_answers} />
        <MetricCard label="Completion" value={`${summary.review_completion_percent}%`} />
        <MetricCard label="Average Overall" value={summary.average_overall_score ?? "Not scored"} />
        <MetricCard label="Weakest Dimension" value={summary.weakest_dimension ?? "Not scored"} />
      </div>
      <div className="dimension-list">
        {dimensionLabels.map(([key, label]) => {
          const value = summary.dimension_averages[key];
          const numericValue = value ? Number(value) : 0;
          return (
            <div className="dimension-row" key={key}>
              <div className="status-row">
                <span>{label}</span>
                <span>{value ?? "Not scored"}</span>
              </div>
              <div className="score-bar">
                <span style={{ width: `${Math.min(100, (numericValue / 5) * 100)}%` }} />
              </div>
            </div>
          );
        })}
      </div>
      <div className="dimension-list">
        <h3>Retrieval Metrics</h3>
        <div className="metric-grid">
          <MetricCard label="Hit Rate" value={formatMetric(summary.retrieval_metrics.hit_rate)} />
          <MetricCard label="Precision@3" value={formatMetric(summary.retrieval_metrics.precision_at_k)} />
          <MetricCard label="Recall@3" value={formatMetric(summary.retrieval_metrics.recall_at_k)} />
          <MetricCard label="MRR" value={formatMetric(summary.retrieval_metrics.mean_reciprocal_rank)} />
          <MetricCard label="Chunk Coverage" value={formatMetric(summary.retrieval_metrics.chunk_coverage)} />
          <MetricCard label="Missing Evidence" value={summary.retrieval_metrics.missing_evidence_count} />
        </div>
      </div>
      <div className="question-results">
        <h3>Question Results</h3>
        {summary.question_results.map((result) => (
          <div className="mini-list-item" key={result.question_id}>
            <strong>{result.question_text}</strong>
            <span>{result.reviewed ? `Reviewed / Overall ${result.overall_score}` : "Not reviewed"}</span>
            {result.evaluation_mode ? (
              <span>
                {result.evaluation_mode === "automated" ? "Automated judge" : "Human review"}
                {result.judge_model_name ? ` / ${result.judge_model_name}` : ""}
              </span>
            ) : null}
            <span>
              Retrieval: {formatExpectedSourceMatch(result.expected_source_match)} / chunks {result.retrieved_chunk_count}
              {result.first_relevant_rank ? ` / first match rank ${result.first_relevant_rank}` : ""}
              {result.missing_evidence ? " / missing evidence" : ""}
            </span>
            {result.answer_text ? <p>{result.answer_text}</p> : <p>No generated answer yet.</p>}
          </div>
        ))}
      </div>
    </section>
  );
}

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
        <span>{dashboard.ready_for_release ? "Ready" : "In review"}</span>
      </div>
      <div className="metric-grid">
        <MetricCard label="Answers" value={dashboard.total_answers} />
        <MetricCard label="Pending" value={dashboard.pending_review_count} />
        <MetricCard label="Approved" value={dashboard.approved_count} />
        <MetricCard label="Needs Revision" value={dashboard.needs_revision_count} />
        <MetricCard label="Approved Completion" value={`${dashboard.review_completion_percent}%`} />
        <MetricCard label="Approved Average" value={dashboard.approved_average_overall_score ?? "Not approved"} />
      </div>
      <div className="question-results">
        {dashboard.items.length === 0 ? (
          <p className="muted">Run Gemini RAG and automated CLEAR-RAG evaluation before reviewing answers.</p>
        ) : (
          dashboard.items.map((item) => (
            <div className="review-card" key={item.answer_id}>
              <div className="status-row">
                <strong>{item.question_text}</strong>
                <span>{formatReviewStatus(item.review_status)}</span>
              </div>
              <p>{item.answer_text}</p>
              <span>
                {item.evaluation_mode ? `${item.evaluation_mode} score` : "No score"} / Overall{" "}
                {item.overall_score ?? "not scored"}
                {item.judge_model_name ? ` / ${item.judge_model_name}` : ""}
              </span>
              <span>
                Citation {item.citation_quality_score ?? "n/a"} / Latency {item.latency_cost_score ?? "n/a"} / Faithfulness{" "}
                {item.evidence_faithfulness_score ?? "n/a"} / Relevance {item.answer_relevance_score ?? "n/a"} / Retrieval{" "}
                {item.retrieval_quality_score ?? "n/a"}
              </span>
              {item.judge_reasoning ? <p>{item.judge_reasoning}</p> : null}
              {item.reviewer_notes ? <p>{item.reviewer_notes}</p> : null}
              {item.review_notes ? <span>Reviewer decision: {item.review_notes}</span> : null}
              {item.score_change_reason ? <span>Score change: {item.score_change_reason}</span> : null}
              {item.retrieved_chunks.length > 0 ? (
                <div className="mini-list">
                  {item.retrieved_chunks.map((chunk) => (
                    <div className="mini-list-item" key={chunk.id}>
                      <strong>
                        Evidence {chunk.rank}: {chunk.section_reference ?? "No section"}
                      </strong>
                      <p>{chunk.chunk_text}</p>
                    </div>
                  ))}
                </div>
              ) : null}
              {item.evaluation_id ? (
                <form className="compact-form" onSubmit={(event) => onSubmitReview(item.evaluation_id as number, event)}>
                  <select name="reviewStatus" defaultValue={item.review_status}>
                    <option value="pending_review">Pending review</option>
                    <option value="approved">Approved</option>
                    <option value="needs_revision">Needs revision</option>
                  </select>
                  <ScoreInput name="citationQualityScore" label="Citation quality" value={item.citation_quality_score} />
                  <ScoreInput name="latencyCostScore" label="Latency and cost" value={item.latency_cost_score} />
                  <ScoreInput name="evidenceFaithfulnessScore" label="Evidence faithfulness" value={item.evidence_faithfulness_score} />
                  <ScoreInput name="answerRelevanceScore" label="Answer relevance" value={item.answer_relevance_score} />
                  <ScoreInput name="retrievalQualityScore" label="Retrieval quality" value={item.retrieval_quality_score} />
                  <textarea name="reviewNotes" placeholder="Review notes" rows={3} defaultValue={item.review_notes ?? ""} />
                  <textarea name="scoreChangeReason" placeholder="Reason if scores changed" rows={3} defaultValue={item.score_change_reason ?? ""} />
                  <textarea name="reviewerNotes" placeholder="Final evaluator notes" rows={3} defaultValue={item.reviewer_notes ?? ""} />
                  <textarea name="suggestedImprovement" placeholder="Suggested improvement" rows={3} defaultValue={item.suggested_improvement ?? ""} />
                  <button type="submit">Save review decision</button>
                </form>
              ) : (
                <p className="muted">No evaluation record exists for this answer yet.</p>
              )}
            </div>
          ))
        )}
      </div>
    </section>
  );
}

function JudgeCalibrationPanel({
  report,
}: Readonly<{
  report: JudgeCalibrationReport;
}>) {
  return (
    <section className="status analytics-panel">
      <div className="section-heading">
        <h2>Judge Calibration</h2>
        <span>{report.paired_answer_count > 0 ? "Paired" : "Needs human scores"}</span>
      </div>
      <div className="metric-grid">
        <MetricCard label="Paired Answers" value={report.paired_answer_count} />
        <MetricCard label="Exact Agreement" value={`${report.overall_exact_agreement_percent}%`} />
        <MetricCard label="Within 1 Point" value={`${report.overall_within_one_agreement_percent}%`} />
        <MetricCard label="Average Delta" value={formatSignedMetric(report.average_overall_delta)} />
        <MetricCard label="Automated Only" value={report.automated_only_count} />
        <MetricCard label="Human Only" value={report.human_only_count} />
      </div>
      <div className="dimension-list">
        <h3>Dimension Agreement</h3>
        {report.dimension_calibration.map((dimension) => (
          <div className="dimension-row" key={dimension.field}>
            <div className="status-row">
              <span>{dimension.label}</span>
              <span>{formatBiasDirection(dimension.bias_direction)}</span>
            </div>
            <span>
              Delta {formatSignedMetric(dimension.average_delta)} / exact {dimension.exact_agreement_percent}% / within 1{" "}
              {dimension.within_one_agreement_percent}%
            </span>
          </div>
        ))}
      </div>
      <div className="question-results">
        <h3>Paired Answer Comparisons</h3>
        {report.answer_comparisons.length === 0 ? (
          <p className="muted">Add a human CLEAR-RAG score to an answer that already has an automated judge score.</p>
        ) : (
          report.answer_comparisons.map((comparison) => (
            <div className="mini-list-item" key={comparison.answer_id}>
              <strong>{comparison.question_text}</strong>
              <span>
                Automated {comparison.automated_overall_score} / human {comparison.human_overall_score} / delta{" "}
                {formatSignedMetric(comparison.overall_delta)}
              </span>
              <span>
                {dimensionLabels
                  .map(([key, label]) => `${label}: ${formatSignedMetric(comparison.dimension_deltas[key])}`)
                  .join(" / ")}
              </span>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

function ErrorTaxonomyPanel({
  report,
}: Readonly<{
  report: ErrorTaxonomyReport;
}>) {
  const activeCategoryCounts = report.category_counts.filter((item) => item.count > 0);
  const activeSeverityCounts = report.severity_counts.filter((item) => item.count > 0);

  return (
    <section className="status analytics-panel">
      <div className="section-heading">
        <h2>Error Taxonomy</h2>
        <span>{report.total_errors > 0 ? "Classified" : "No errors tagged"}</span>
      </div>
      <div className="metric-grid">
        <MetricCard label="Total Errors" value={report.total_errors} />
        <MetricCard label="Affected Answers" value={report.affected_answers} />
        <MetricCard label="Top Category" value={activeCategoryCounts[0]?.label ?? "None"} />
        <MetricCard label="Highest Severity" value={highestSeverityLabel(activeSeverityCounts)} />
      </div>
      <div className="dimension-list">
        <h3>Category Counts</h3>
        {activeCategoryCounts.length === 0 ? (
          <p className="muted">Use the error tagging form under CLEAR-RAG Scoring to classify observed failures.</p>
        ) : (
          activeCategoryCounts.map((item) => (
            <div className="dimension-row" key={item.key}>
              <div className="status-row">
                <span>{item.label}</span>
                <span>
                  {item.count} / {item.percent}%
                </span>
              </div>
            </div>
          ))
        )}
      </div>
      <div className="question-results">
        <h3>Recent Error Tags</h3>
        {report.items.length === 0 ? (
          <p className="muted">No error annotations have been added for this run.</p>
        ) : (
          report.items.slice(0, 6).map((item) => (
            <div className="mini-list-item" key={item.id}>
              <strong>{item.category_label}</strong>
              <span>
                {formatSeverity(item.severity)} / {item.question_text}
              </span>
              {item.notes ? <p>{item.notes}</p> : null}
              {item.evidence_reference ? <span>{item.evidence_reference}</span> : null}
            </div>
          ))
        )}
      </div>
    </section>
  );
}

function MetricCard({ label, value }: Readonly<{ label: string; value: string | number }>) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatMetric(value: string | null): string {
  return value ?? "n/a";
}

function formatSignedMetric(value: string | null): string {
  if (value === null) {
    return "n/a";
  }
  const numericValue = Number(value);
  if (Number.isNaN(numericValue) || numericValue === 0) {
    return value;
  }
  return numericValue > 0 ? `+${value}` : value;
}

function formatBiasDirection(value: string): string {
  if (value === "automated_under_scores") {
    return "Automated under-scores";
  }
  if (value === "automated_over_scores") {
    return "Automated over-scores";
  }
  return "Aligned";
}

function formatSeverity(value: ErrorSeverity): string {
  return errorSeverities.find((item) => item.value === value)?.label ?? value;
}

function highestSeverityLabel(items: Array<{ key: string; label: string; count: number }>): string {
  const severityOrder = ["critical", "high", "medium", "low"];
  return severityOrder
    .map((severity) => items.find((item) => item.key === severity && item.count > 0))
    .find(Boolean)?.label ?? "None";
}

function formatExpectedSourceMatch(value: boolean | null): string {
  if (value === null) {
    return "No expected source";
  }
  return value ? "Expected source matched" : "Expected source missed";
}

function ScoreInput({ name, label, value }: Readonly<{ name: string; label: string; value: number | null }>) {
  return (
    <label>
      {label}
      <input name={name} type="number" min={1} max={5} defaultValue={value ?? ""} placeholder="1-5" />
    </label>
  );
}

function formatReviewStatus(value: "pending_review" | "approved" | "needs_revision" | null): string {
  if (value === "approved") {
    return "Approved";
  }
  if (value === "needs_revision") {
    return "Needs revision";
  }
  return "Pending review";
}

function SetupSection({
  title,
  count,
  children,
}: Readonly<{
  title: string;
  count: number;
  children: React.ReactNode;
}>) {
  return (
    <section className="setup-section">
      <div className="section-heading">
        <h2>{title}</h2>
        <span>{count}</span>
      </div>
      {children}
    </section>
  );
}

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
  if (answers.length === 0) {
    return null;
  }

  return (
    <div className="review-list">
      <h3>CLEAR-RAG Scoring</h3>
      {answers.map((answer) => {
        const answerEvaluations = evaluations.filter((evaluation) => evaluation.generated_answer_id === answer.id);
        const answerErrors = errorItems.filter((item) => item.answer_id === answer.id);
        const latestEvaluation = answerEvaluations[0];
        return (
          <div className="review-card" key={answer.id}>
            <strong>{answer.model_name ?? "Generated answer"}</strong>
            {answerEvaluations.length > 0 ? (
              <div className="mini-list">
                {answerEvaluations.map((evaluation) => (
                  <div className="mini-list-item" key={evaluation.id}>
                    <strong>Overall score: {evaluation.overall_score}</strong>
                    <span>
                      {evaluation.evaluation_mode === "automated" ? "Automated judge" : "Human review"}
                      {evaluation.judge_model_name ? ` / ${evaluation.judge_model_name}` : ""}
                    </span>
                    <span>Review status: {formatReviewStatus(evaluation.review_status)}</span>
                    <span>
                      Citation {evaluation.citation_quality_score} / Latency {evaluation.latency_cost_score} / Faithfulness {evaluation.evidence_faithfulness_score} / Relevance {evaluation.answer_relevance_score} / Retrieval {evaluation.retrieval_quality_score}
                    </span>
                    {evaluation.reviewer_notes ? <p>{evaluation.reviewer_notes}</p> : null}
                    {evaluation.judge_reasoning ? <p>{evaluation.judge_reasoning}</p> : null}
                    {evaluation.suggested_improvement ? <span>{evaluation.suggested_improvement}</span> : null}
                  </div>
                ))}
              </div>
            ) : (
              <p className="muted">Not reviewed yet.</p>
            )}
            <form className="compact-form" onSubmit={(event) => onSubmit(answer.id, event)}>
              <ScoreSelect name="citationQualityScore" label="Citation quality" />
              <ScoreSelect name="latencyCostScore" label="Latency and cost" />
              <ScoreSelect name="evidenceFaithfulnessScore" label="Evidence faithfulness" />
              <ScoreSelect name="answerRelevanceScore" label="Answer relevance" />
              <ScoreSelect name="retrievalQualityScore" label="Retrieval quality" />
              <textarea name="reviewerNotes" placeholder="Reviewer notes" rows={3} />
              <textarea name="suggestedImprovement" placeholder="Suggested improvement" rows={3} />
              <button type="submit">Save CLEAR-RAG score</button>
            </form>
            <div className="mini-list">
              {answerErrors.map((item) => (
                <div className="mini-list-item" key={item.id}>
                  <strong>{item.category_label}</strong>
                  <span>{formatSeverity(item.severity)}</span>
                  {item.notes ? <p>{item.notes}</p> : null}
                </div>
              ))}
            </div>
            <form className="compact-form" onSubmit={(event) => onSubmitError(answer.id, event)}>
              <select name="category" defaultValue="retrieval_miss" required>
                {errorCategories.map((category) => (
                  <option key={category.value} value={category.value}>
                    {category.label}
                  </option>
                ))}
              </select>
              <select name="severity" defaultValue="medium" required>
                {errorSeverities.map((severity) => (
                  <option key={severity.value} value={severity.value}>
                    {severity.label}
                  </option>
                ))}
              </select>
              <input name="evaluationRecordId" type="hidden" value={latestEvaluation?.id ?? ""} />
              <textarea name="notes" placeholder="Error notes" rows={3} />
              <textarea name="evidenceReference" placeholder="Evidence reference or expected behavior" rows={2} />
              <button type="submit">Add error tag</button>
            </form>
          </div>
        );
      })}
    </div>
  );
}

function ScoreSelect({ name, label }: Readonly<{ name: string; label: string }>) {
  return (
    <label>
      {label}
      <select name={name} defaultValue="5" required>
        {scoreOptions.map((score) => (
          <option key={score} value={score}>
            {score}
          </option>
        ))}
      </select>
    </label>
  );
}

function OutputList({
  items,
}: Readonly<{
  items: Array<{ title: string; body: string; meta: string }>;
}>) {
  if (items.length === 0) {
    return <p className="muted">Nothing recorded yet.</p>;
  }

  return (
    <div className="mini-list">
      {items.map((item, index) => (
        <div className="mini-list-item" key={`${item.title}-${index}`}>
          <strong>{item.title}</strong>
          <p>{item.body}</p>
          {item.meta ? <span>{item.meta}</span> : null}
        </div>
      ))}
    </div>
  );
}
