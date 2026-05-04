"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import TopBar from "../../components/TopBar";
import { Project, TOKEN_STORAGE_KEY, authRequest } from "../../lib/auth";

/* System type → readable label */
function humanize(str: string) {
  return str.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

/* Icon for project card */
function ProjectIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
    </svg>
  );
}

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) {
      router.replace("/login");
      return;
    }

    authRequest<Project[]>("/projects", { method: "GET" }, token)
      .then((data) => {
        setProjects(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Unable to load projects");
        setLoading(false);
      });
  }, [router]);

  function handleLogout() {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    router.replace("/login");
  }

  return (
    <div className="page-root">
      <TopBar onLogout={handleLogout}>
        <Link href="/dashboard" className="topbar-link">Dashboard</Link>
      </TopBar>

      <main className="page-body">
        <div className="shell animate-in">
          {/* Header */}
          <div style={{ paddingBottom: "var(--sp-6)", borderBottom: "1px solid var(--border)", marginBottom: "var(--sp-6)" }}>
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "var(--sp-4)", flexWrap: "wrap" }}>
              <div>
                <nav className="breadcrumb" aria-label="Breadcrumb">
                  <Link href="/dashboard">Dashboard</Link>
                  <span className="breadcrumb-sep" aria-hidden="true">›</span>
                  <span className="breadcrumb-current">Projects</span>
                </nav>
                <h1 style={{ marginBottom: 8 }}>Projects</h1>
                <p style={{ fontSize: 15, color: "var(--text-secondary)" }}>
                  Each project is an isolated RAG evaluation workspace.
                </p>
              </div>
              <Link href="/dashboard/projects/new" className="btn btn-primary" style={{ flexShrink: 0, marginTop: "var(--sp-6)" }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
                New project
              </Link>
            </div>
          </div>

          {/* Error */}
          {error && <p className="error" role="alert" style={{ marginBottom: "var(--sp-4)" }}>{error}</p>}

          {/* Loading skeleton */}
          {loading && !error && (
            <div style={{ display: "grid", gap: "var(--sp-3)" }}>
              {[1, 2, 3].map((i) => (
                <div key={i} className="skeleton skeleton-card" />
              ))}
            </div>
          )}

          {/* Projects list */}
          {!loading && projects.length === 0 && !error && (
            <div className="empty-state">
              <div style={{
                width: 48, height: 48, borderRadius: "var(--radius-lg)",
                background: "var(--brand-50)", border: "1px solid var(--border-brand)",
                display: "flex", alignItems: "center", justifyContent: "center",
                color: "var(--brand-600)", margin: "0 auto var(--sp-4)",
              }}>
                <ProjectIcon />
              </div>
              <p className="muted" style={{ textAlign: "center", marginBottom: "var(--sp-5)" }}>
                No projects yet. Create your first RAG evaluation workspace.
              </p>
              <Link href="/dashboard/projects/new" className="btn btn-primary">
                Create first project
              </Link>
            </div>
          )}

          {!loading && projects.length > 0 && (
            <div className="list">
              {projects.map((project) => (
                <Link
                  className="list-item"
                  href={`/dashboard/projects/${project.id}`}
                  key={project.id}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "var(--sp-3)" }}>
                    <div style={{
                      width: 36, height: 36, borderRadius: "var(--radius-md)", flexShrink: 0,
                      background: "var(--brand-50)", border: "1px solid var(--border-brand)",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      color: "var(--brand-600)",
                    }}>
                      <ProjectIcon />
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <strong style={{ display: "block", fontSize: 15, fontWeight: 600, color: "var(--text-primary)", marginBottom: 3 }}>
                        {project.name}
                      </strong>
                      <div style={{ display: "flex", gap: "var(--sp-2)", flexWrap: "wrap" }}>
                        <span className="badge badge-green">{humanize(project.system_type)}</span>
                        <span className="badge badge-slate">{project.target_users}</span>
                      </div>
                    </div>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ flexShrink: 0 }}>
                      <polyline points="9 18 15 12 9 6"/>
                    </svg>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
