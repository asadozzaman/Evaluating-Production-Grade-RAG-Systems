"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { Project, TOKEN_STORAGE_KEY, authRequest } from "../../../lib/auth";

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
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
        token,
      );
      router.push(`/dashboard/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create project");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main>
      <section className="auth-panel">
        <p className="eyebrow">CLEAR-RAG</p>
        <h1>New project</h1>
        <p className="summary">Create the evaluation workspace before adding setup data.</p>

        <form className="form" onSubmit={handleSubmit}>
          <label>
            Name
            <input name="name" required />
          </label>
          <label>
            System type
            <input name="systemType" defaultValue="internal_knowledge_assistant" required />
          </label>
          <label>
            Target users
            <input name="targetUsers" defaultValue="Employees" required />
          </label>
          <label>
            Description
            <textarea name="description" rows={4} />
          </label>
          {error ? <p className="error">{error}</p> : null}
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Creating..." : "Create project"}
          </button>
        </form>

        <p className="auth-switch">
          <Link href="/dashboard/projects">Back to projects</Link>
        </p>
      </section>
    </main>
  );
}
