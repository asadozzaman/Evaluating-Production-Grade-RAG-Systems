"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import {
  EvaluationRun,
  GeneratedAnswer,
  Project,
  RetrievedChunk,
  SourceDocument,
  TOKEN_STORAGE_KEY,
  TestQuestion,
  authRequest,
} from "../../../../../lib/auth";

const relevanceLabels = ["high", "medium", "low", "irrelevant"];

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

      const [chunkData, answerData] = await Promise.all([
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
      ]);
      setChunks(chunkData);
      setAnswers(answerData);
    },
    [getToken, projectId, runId],
  );

  const loadPage = useCallback(async () => {
    const token = getToken();
    if (!token) {
      return;
    }

    try {
      const [projectData, runData, documentData, questionData] = await Promise.all([
        authRequest<Project>(`/projects/${projectId}`, { method: "GET" }, token),
        authRequest<EvaluationRun>(`/projects/${projectId}/runs/${runId}`, { method: "GET" }, token),
        authRequest<SourceDocument[]>(`/projects/${projectId}/documents`, { method: "GET" }, token),
        authRequest<TestQuestion[]>(`/projects/${projectId}/questions`, { method: "GET" }, token),
      ]);
      setProject(projectData);
      setRun(runData);
      setDocuments(documentData);
      setQuestions(questionData);
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
          Add retrieved chunks and generated answers for a selected test question. Keep API keys in backend environment files only.
        </p>
        {error ? <p className="error">{error}</p> : null}

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
