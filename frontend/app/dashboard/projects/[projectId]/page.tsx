"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  DocumentIndexResult,
  EvaluationRun,
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

export default function ProjectDetailPage() {
  const params = useParams<{ projectId: string }>();
  const router = useRouter();
  const projectId = params.projectId;
  const [project, setProject] = useState<Project | null>(null);
  const [documents, setDocuments] = useState<SourceDocument[]>([]);
  const [questions, setQuestions] = useState<TestQuestion[]>([]);
  const [questionDatasets, setQuestionDatasets] = useState<QuestionDataset[]>([]);
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [documentSourceMode, setDocumentSourceMode] = useState<"uri" | "file">("uri");
  const [indexingDocumentId, setIndexingDocumentId] = useState<number | null>(null);
  const [selectedRunIds, setSelectedRunIds] = useState<number[]>([]);
  const [comparison, setComparison] = useState<RunComparison | null>(null);
  const [isComparing, setIsComparing] = useState(false);
  const [isImportingQuestions, setIsImportingQuestions] = useState(false);

  const getToken = useCallback(() => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) {
      router.replace("/login");
      return null;
    }
    return token;
  }, [router]);

  const loadProject = useCallback(async () => {
    const token = getToken();
    if (!token) {
      return;
    }

    try {
      const [projectData, documentData, questionData, datasetData, runData] = await Promise.all([
        authRequest<Project>(`/projects/${projectId}`, { method: "GET" }, token),
        authRequest<SourceDocument[]>(`/projects/${projectId}/documents`, { method: "GET" }, token),
        authRequest<TestQuestion[]>(`/projects/${projectId}/questions`, { method: "GET" }, token),
        authRequest<QuestionDataset[]>(`/projects/${projectId}/question-datasets`, { method: "GET" }, token),
        authRequest<EvaluationRun[]>(`/projects/${projectId}/runs`, { method: "GET" }, token),
      ]);
      setProject(projectData);
      setDocuments(documentData);
      setQuestions(questionData);
      setQuestionDatasets(datasetData);
      setRuns(runData);
      setSelectedRunIds((current) => {
        if (current.length > 0) {
          return current.filter((runId) => runData.some((run) => run.id === runId));
        }
        return runData.slice(0, 2).map((run) => run.id);
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load project");
    }
  }, [getToken, projectId]);

  useEffect(() => {
    loadProject();
  }, [loadProject]);

  async function submitDocument(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    const token = getToken();
    if (!token) {
      return;
    }
    const form = event.currentTarget;
    const formData = new FormData(form);

    try {
      if (documentSourceMode === "file") {
        const uploadData = new FormData();
        uploadData.set("title", String(formData.get("title") ?? ""));
        uploadData.set("document_type", String(formData.get("documentType") ?? ""));
        const version = String(formData.get("version") ?? "");
        if (version) {
          uploadData.set("version", version);
        }
        const file = formData.get("file");
        if (file instanceof File) {
          uploadData.set("file", file);
        }
        await uploadRequest(`/projects/${projectId}/documents/upload`, uploadData, token);
      } else {
        await authRequest(
          `/projects/${projectId}/documents`,
          {
            method: "POST",
            body: JSON.stringify({
              title: String(formData.get("title") ?? ""),
              document_type: String(formData.get("documentType") ?? ""),
              source_kind: "uri",
              source_uri: String(formData.get("sourceUri") ?? ""),
              version: String(formData.get("version") ?? "") || null,
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
    setError("");
    setNotice("");
    const token = getToken();
    if (!token) {
      return;
    }

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
    if (!token) {
      return;
    }
    const form = event.currentTarget;
    const formData = new FormData(form);
    try {
      await authRequest(
        `/projects/${projectId}/questions`,
        {
          method: "POST",
          body: JSON.stringify({
            question_text: String(formData.get("questionText") ?? ""),
            question_type: String(formData.get("questionType") ?? ""),
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
    setError("");
    setNotice("");
    const token = getToken();
    if (!token) {
      return;
    }

    const form = event.currentTarget;
    const formData = new FormData(form);
    const uploadData = new FormData();
    uploadData.set("dataset_name", String(formData.get("datasetName") ?? ""));
    const datasetVersion = String(formData.get("datasetVersion") ?? "");
    if (datasetVersion) {
      uploadData.set("dataset_version", datasetVersion);
    }
    const file = formData.get("questionFile");
    if (file instanceof File) {
      uploadData.set("file", file);
    }

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
    if (!token) {
      return;
    }
    const form = event.currentTarget;
    const formData = new FormData(form);
    try {
      await authRequest(
        `/projects/${projectId}/runs`,
        {
          method: "POST",
          body: JSON.stringify({
            name: String(formData.get("name") ?? ""),
            system_version: String(formData.get("systemVersion") ?? "") || null,
            notes: String(formData.get("notes") ?? "") || null,
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
    setError("");
    setNotice("");
    setComparison(null);
    const token = getToken();
    if (!token) {
      return;
    }
    if (selectedRunIds.length < 2) {
      setError("Select at least two runs to compare.");
      return;
    }

    const params = new URLSearchParams();
    selectedRunIds.forEach((runId) => params.append("run_ids", String(runId)));
    setIsComparing(true);
    try {
      const result = await authRequest<RunComparison>(
        `/projects/${projectId}/runs/compare?${params.toString()}`,
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

  function toggleRunSelection(runId: number) {
    setSelectedRunIds((current) => {
      if (current.includes(runId)) {
        return current.filter((selectedRunId) => selectedRunId !== runId);
      }
      return [...current, runId];
    });
  }

  if (error && !project) {
    return (
      <main>
        <section className="shell">
          <p className="error">{error}</p>
          <p className="auth-switch">
            <Link href="/dashboard/projects">Back to projects</Link>
          </p>
        </section>
      </main>
    );
  }

  if (!project) {
    return (
      <main>
        <section className="shell">
          <p className="summary">Loading project...</p>
        </section>
      </main>
    );
  }

  return (
    <main>
      <section className="wide-shell">
        <div className="dashboard-header">
          <div>
            <p className="eyebrow">CLEAR-RAG</p>
            <h1>{project.name}</h1>
          </div>
          <Link className="secondary-button" href="/dashboard/projects">
            Projects
          </Link>
        </div>

        <p className="summary">
          {project.system_type} for {project.target_users}
        </p>
        {error ? <p className="error">{error}</p> : null}
        {notice ? <p className="success">{notice}</p> : null}

        <div className="setup-grid">
          <SetupSection title="Documents" count={documents.length}>
            <form className="compact-form" onSubmit={submitDocument}>
              <div className="segmented-control" aria-label="Document source type">
                <button
                  className={documentSourceMode === "uri" ? "active-segment" : ""}
                  type="button"
                  onClick={() => setDocumentSourceMode("uri")}
                >
                  Use URI
                </button>
                <button
                  className={documentSourceMode === "file" ? "active-segment" : ""}
                  type="button"
                  onClick={() => setDocumentSourceMode("file")}
                >
                  Upload file
                </button>
              </div>
              <input name="title" placeholder="Document title" required />
              <input name="documentType" placeholder="Document type" required />
              {documentSourceMode === "uri" ? (
                <input name="sourceUri" placeholder="Source URI" required />
              ) : (
                <input
                  name="file"
                  type="file"
                  accept=".pdf,.docx,.txt,.csv,.md"
                  required
                />
              )}
              <input name="version" placeholder="Version" />
              <button type="submit">
                {documentSourceMode === "file" ? "Upload document" : "Add document"}
              </button>
            </form>
            <SetupList
              items={documents.map((document) => ({
                title: document.title,
                meta: [
                  document.source_kind,
                  document.document_type,
                  document.version,
                  document.source_kind === "file" ? document.original_file_name : document.source_uri,
                ]
                  .filter(Boolean)
                  .join(" · "),
                actionLabel: indexingDocumentId === document.id ? "Indexing..." : "Index for vector search",
                actionDisabled: indexingDocumentId !== null || document.source_kind !== "file",
                onAction: () => indexDocument(document.id),
              }))}
            />
          </SetupSection>

          <SetupSection title="Questions" count={questions.length}>
            <form className="compact-form" onSubmit={importQuestions}>
              <input name="datasetName" placeholder="Dataset name" required />
              <input name="datasetVersion" placeholder="Dataset version" />
              <input name="questionFile" type="file" accept=".csv,.json" required />
              <button type="submit" disabled={isImportingQuestions}>
                {isImportingQuestions ? "Importing questions..." : "Import question set"}
              </button>
            </form>
            <SetupList
              items={questionDatasets.map((dataset) => ({
                title: dataset.dataset_name,
                meta: [
                  dataset.dataset_version,
                  `${dataset.question_count} questions`,
                  dataset.imported_file_name,
                ]
                  .filter(Boolean)
                  .join(" / "),
              }))}
            />
            <form className="compact-form" onSubmit={submitQuestion}>
              <textarea name="questionText" placeholder="Question text" rows={3} required />
              <select name="questionType" required defaultValue="simple_factual">
                {questionTypes.map((questionType) => (
                  <option key={questionType} value={questionType}>
                    {questionType}
                  </option>
                ))}
              </select>
              <input name="expectedSource" placeholder="Expected source" />
              <button type="submit">Add question</button>
            </form>
            <SetupList
              items={questions.map((question) => ({
                title: question.question_text,
                meta: question.question_type,
              }))}
            />
          </SetupSection>

          <SetupSection title="Runs" count={runs.length}>
            <form className="compact-form" onSubmit={submitRun}>
              <input name="name" placeholder="Run name" required />
              <input name="systemVersion" placeholder="System version" />
              <textarea name="notes" placeholder="Notes" rows={3} />
              <button type="submit">Add run</button>
            </form>
            <SetupList
              items={runs.map((run) => ({
                title: run.name,
                meta: run.system_version ?? "No version",
                href: `/dashboard/projects/${projectId}/runs/${run.id}`,
              }))}
            />
          </SetupSection>
        </div>

        <section className="status comparison-panel">
          <div className="section-heading">
            <h2>Run Comparison</h2>
            <span>{selectedRunIds.length}</span>
          </div>
          <div className="comparison-selector">
            {runs.length === 0 ? (
              <p className="muted">Create at least two runs to compare experiments.</p>
            ) : (
              runs.map((run) => (
                <label className="checkbox-row" key={run.id}>
                  <input
                    type="checkbox"
                    checked={selectedRunIds.includes(run.id)}
                    onChange={() => toggleRunSelection(run.id)}
                  />
                  <span>
                    {run.name}
                    {run.retrieval_mode ? ` / ${run.retrieval_mode}` : ""}
                  </span>
                </label>
              ))
            )}
          </div>
          <div className="actions compact-actions">
            <button type="button" onClick={compareSelectedRuns} disabled={isComparing || selectedRunIds.length < 2}>
              {isComparing ? "Comparing..." : "Compare selected runs"}
            </button>
          </div>
          {comparison ? <RunComparisonView comparison={comparison} /> : null}
        </section>
      </section>
    </main>
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
            <small>
              {[
                run.retrieval_mode,
                run.generator_model_name,
                run.embedding_model_name,
                run.judge_model_name,
              ]
                .filter(Boolean)
                .join(" / ") || "No experiment metadata"}
            </small>
          </div>
        ))}
      </div>
      <div className="dimension-list">
        {comparison.runs.map((run) => (
          <div className="dimension-row" key={run.run_id}>
            <div className="status-row">
              <span>{run.run_name}</span>
              <span>{run.weakest_dimension ?? "No weakest dimension"}</span>
            </div>
            <p className="muted">
              Generated {run.generated_answers}, reviewed {run.reviewed_answers}
            </p>
          </div>
        ))}
      </div>
      {Object.entries(comparison.metric_deltas).length > 0 ? (
        <div className="mini-list">
          {Object.entries(comparison.metric_deltas).map(([runId, deltas]) => (
            <div className="mini-list-item" key={runId}>
              <strong>Run {runId} vs baseline {comparison.baseline_run_id}</strong>
              <span>Overall delta: {formatDelta(deltas.overall_score_delta)}</span>
              <span>
                Citation {formatDelta(deltas.citation_quality_delta)} / Faithfulness{" "}
                {formatDelta(deltas.evidence_faithfulness_delta)} / Relevance{" "}
                {formatDelta(deltas.answer_relevance_delta)} / Retrieval{" "}
                {formatDelta(deltas.retrieval_quality_delta)}
              </span>
            </div>
          ))}
        </div>
      ) : null}
      <div className="question-results">
        <h3>Question-Level Comparison</h3>
        {comparison.question_results.map((question) => (
          <div className="mini-list-item" key={question.question_id}>
            <strong>{question.question_text}</strong>
            <span>
              Best run: {question.best_run_id ? question.best_run_id : "Not enough scored answers"}
            </span>
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
  );
}

function formatDelta(value: string | null): string {
  if (value === null) {
    return "n/a";
  }
  const numericValue = Number(value);
  if (numericValue > 0) {
    return `+${value}`;
  }
  return value;
}

function SetupSection({
  title,
  count,
  children,
}: Readonly<{
  title: string;
  count: number;
  children: ReactNode;
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
    return <p className="muted">Nothing added yet.</p>;
  }

  return (
    <div className="mini-list">
      {items.map((item, index) => (
        <div className="mini-list-item" key={`${item.title}-${index}`}>
          <strong>{item.title}</strong>
          <span>{item.meta}</span>
          {item.onAction ? (
            <button type="button" onClick={item.onAction} disabled={item.actionDisabled}>
              {item.actionLabel}
            </button>
          ) : null}
          {item.href ? <Link href={item.href}>Open run</Link> : null}
        </div>
      ))}
    </div>
  );
}
