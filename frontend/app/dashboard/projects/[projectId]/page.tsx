"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  EvaluationRun,
  Project,
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
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [error, setError] = useState("");
  const [documentSourceMode, setDocumentSourceMode] = useState<"uri" | "file">("uri");

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
      const [projectData, documentData, questionData, runData] = await Promise.all([
        authRequest<Project>(`/projects/${projectId}`, { method: "GET" }, token),
        authRequest<SourceDocument[]>(`/projects/${projectId}/documents`, { method: "GET" }, token),
        authRequest<TestQuestion[]>(`/projects/${projectId}/questions`, { method: "GET" }, token),
        authRequest<EvaluationRun[]>(`/projects/${projectId}/runs`, { method: "GET" }, token),
      ]);
      setProject(projectData);
      setDocuments(documentData);
      setQuestions(questionData);
      setRuns(runData);
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

  if (error) {
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
              }))}
            />
          </SetupSection>

          <SetupSection title="Questions" count={questions.length}>
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
      </section>
    </main>
  );
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
  items: Array<{ title: string; meta: string; href?: string }>;
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
          {item.href ? <Link href={item.href}>Open run</Link> : null}
        </div>
      ))}
    </div>
  );
}
