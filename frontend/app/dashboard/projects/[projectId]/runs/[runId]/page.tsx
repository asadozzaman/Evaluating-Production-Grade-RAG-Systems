"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import {
  API_URL,
  AutoEvaluationResult,
  EvaluationRun,
  EvaluationRecord,
  GeneratedAnswer,
  Project,
  RagExecutionResult,
  RetrievedChunk,
  SourceDocument,
  TOKEN_STORAGE_KEY,
  RunSummary,
  TestQuestion,
  authRequest,
} from "../../../../../lib/auth";

const relevanceLabels = ["high", "medium", "low", "irrelevant"];
const scoreOptions = [1, 2, 3, 4, 5];
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
    const summaryData = await authRequest<RunSummary>(
      `/projects/${projectId}/runs/${runId}/summary`,
      { method: "GET" },
      token,
    );
    setSummary(summaryData);
  }, [getToken, projectId, runId]);

  const loadPage = useCallback(async () => {
    const token = getToken();
    if (!token) {
      return;
    }

    try {
      const [projectData, runData, documentData, questionData, summaryData] = await Promise.all([
        authRequest<Project>(`/projects/${projectId}`, { method: "GET" }, token),
        authRequest<EvaluationRun>(`/projects/${projectId}/runs/${runId}`, { method: "GET" }, token),
        authRequest<SourceDocument[]>(`/projects/${projectId}/documents`, { method: "GET" }, token),
        authRequest<TestQuestion[]>(`/projects/${projectId}/questions`, { method: "GET" }, token),
        authRequest<RunSummary>(`/projects/${projectId}/runs/${runId}/summary`, { method: "GET" }, token),
      ]);
      setProject(projectData);
      setRun(runData);
      setDocuments(documentData);
      setQuestions(questionData);
      setSummary(summaryData);
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
              onSubmit={submitEvaluation}
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
            {result.answer_text ? <p>{result.answer_text}</p> : <p>No generated answer yet.</p>}
          </div>
        ))}
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
  onSubmit,
}: Readonly<{
  answers: GeneratedAnswer[];
  evaluations: EvaluationRecord[];
  onSubmit: (answerId: number, event: FormEvent<HTMLFormElement>) => void;
}>) {
  if (answers.length === 0) {
    return null;
  }

  return (
    <div className="review-list">
      <h3>CLEAR-RAG Scoring</h3>
      {answers.map((answer) => {
        const answerEvaluations = evaluations.filter((evaluation) => evaluation.generated_answer_id === answer.id);
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
