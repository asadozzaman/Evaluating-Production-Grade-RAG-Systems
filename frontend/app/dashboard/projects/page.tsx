"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Project, TOKEN_STORAGE_KEY, authRequest } from "../../lib/auth";

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) {
      router.replace("/login");
      return;
    }

    authRequest<Project[]>("/projects", { method: "GET" }, token)
      .then(setProjects)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load projects"));
  }, [router]);

  return (
    <main>
      <section className="shell">
        <div className="dashboard-header">
          <div>
            <p className="eyebrow">CLEAR-RAG</p>
            <h1>Projects</h1>
          </div>
          <Link className="secondary-button" href="/dashboard">
            Dashboard
          </Link>
        </div>

        <p className="summary">
          Create and manage the evaluation setup layer. Scoring workflows come later.
        </p>

        <div className="actions">
          <Link href="/dashboard/projects/new">New project</Link>
        </div>

        {error ? <p className="error">{error}</p> : null}

        <div className="list">
          {projects.length === 0 && !error ? (
            <p className="muted">No projects yet.</p>
          ) : (
            projects.map((project) => (
              <Link className="list-item" href={`/dashboard/projects/${project.id}`} key={project.id}>
                <strong>{project.name}</strong>
                <span>{project.system_type}</span>
                <span>{project.target_users}</span>
              </Link>
            ))
          )}
        </div>
      </section>
    </main>
  );
}
