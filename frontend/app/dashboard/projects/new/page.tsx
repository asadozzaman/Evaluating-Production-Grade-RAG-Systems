"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import TopBar from "../../../components/TopBar";
import { Project, TOKEN_STORAGE_KEY, authRequest } from "../../../lib/auth";

const systemTypes = [
  { value: "internal_knowledge_assistant", label: "Internal Knowledge Assistant" },
  { value: "customer_support_bot", label: "Customer Support Bot" },
  { value: "document_qa", label: "Document Q&A" },
  { value: "code_assistant", label: "Code Assistant" },
  { value: "research_tool", label: "Research Tool" },
  { value: "other", label: "Other" },
];

export default function NewProjectPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) {
      router.replace("/login");
      return;
    }

    const formData = new FormData(event.currentTarget);
    const payload = {
      name: String(formData.get("name") ?? ""),
      description: String(formData.get("description") ?? "") || null,
      system_type: String(formData.get("systemType") ?? ""),
      target_users: String(formData.get("targetUsers") ?? ""),
    };

    try {
      const project = await authRequest<Project>(
        "/projects",
        { method: "POST", body: JSON.stringify(payload) },
        token,
      );
      router.push(`/dashboard/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create project");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleLogout() {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    router.replace("/login");
  }

  return (
    <div className="page-root">
      <TopBar onLogout={handleLogout}>
        <Link href="/dashboard/projects" className="topbar-link">Projects</Link>
      </TopBar>

      <main className="page-body">
        <div className="shell animate-in" style={{ maxWidth: 560 }}>
          {/* Breadcrumb */}
          <nav className="breadcrumb" aria-label="Breadcrumb">
            <Link href="/dashboard">Dashboard</Link>
            <span className="breadcrumb-sep" aria-hidden="true">›</span>
            <Link href="/dashboard/projects">Projects</Link>
            <span className="breadcrumb-sep" aria-hidden="true">›</span>
            <span className="breadcrumb-current">New project</span>
          </nav>

          {/* Header */}
          <div style={{ marginBottom: "var(--sp-6)" }}>
            <h1 style={{ marginBottom: 8 }}>New project</h1>
            <p style={{ fontSize: 15, color: "var(--text-secondary)" }}>
              Create an evaluation workspace. Add documents, questions, and runs
              after creation.
            </p>
          </div>

          {/* Form card */}
          <div className="card card-padded">
            <form onSubmit={handleSubmit} noValidate style={{ display: "grid", gap: "var(--sp-4)" }}>
              <label>
                Project name <span style={{ color: "var(--color-danger)", fontWeight: 400 }}>*</span>
                <input
                  name="name"
                  type="text"
                  placeholder="e.g., HR Knowledge Base v2"
                  required
                  autoFocus
                />
              </label>

              <label>
                System type <span style={{ color: "var(--color-danger)", fontWeight: 400 }}>*</span>
                <select name="systemType" defaultValue="internal_knowledge_assistant" required>
                  {systemTypes.map(({ value, label }) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </label>

              <label>
                Target users <span style={{ color: "var(--color-danger)", fontWeight: 400 }}>*</span>
                <input
                  name="targetUsers"
                  type="text"
                  defaultValue="Employees"
                  placeholder="e.g., Employees, Customers, Developers"
                  required
                />
              </label>

              <label>
                Description
                <textarea
                  name="description"
                  rows={3}
                  placeholder="Optional: what does this RAG system do?"
                />
              </label>

              {error && <p className="error" role="alert">{error}</p>}

              <div style={{ display: "flex", gap: "var(--sp-3)", justifyContent: "flex-end", paddingTop: "var(--sp-2)", borderTop: "1px solid var(--border)" }}>
                <Link href="/dashboard/projects" className="btn btn-secondary">
                  Cancel
                </Link>
                <button
                  type="submit"
                  className={`btn btn-primary${isSubmitting ? " btn-loading" : ""}`}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? "" : "Create project"}
                </button>
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}
