"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import TopBar from "../components/TopBar";
import { TOKEN_STORAGE_KEY, User, authRequest } from "../lib/auth";

/* Quick-action card */
function ActionCard({
  href,
  title,
  desc,
  icon,
}: {
  href: string;
  title: string;
  desc: string;
  icon: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="card card-hover"
      style={{ padding: "var(--sp-5)", display: "grid", gap: "var(--sp-3)" }}
    >
      <div style={{
        width: 40, height: 40, borderRadius: "var(--radius-md)",
        background: "var(--brand-50)",
        border: "1px solid var(--border-brand)",
        display: "flex", alignItems: "center", justifyContent: "center",
        color: "var(--brand-600)",
      }}>
        {icon}
      </div>
      <div>
        <div style={{ fontWeight: 600, fontSize: 15, color: "var(--text-primary)", marginBottom: 4 }}>
          {title}
        </div>
        <div style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.5 }}>
          {desc}
        </div>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 13, fontWeight: 600, color: "var(--text-brand)" }}>
        Open
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
        </svg>
      </div>
    </Link>
  );
}

/* Skeleton row */
function SkeletonRow({ width = "60%" }: { width?: string }) {
  return <div className="skeleton skeleton-text" style={{ width }} />;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) {
      router.replace("/login");
      return;
    }

    authRequest<User>("/auth/me", { method: "GET" }, token)
      .then(setUser)
      .catch((err) => {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        setError(err instanceof Error ? err.message : "Session expired");
        router.replace("/login");
      });
  }, [router]);

  function handleLogout() {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    router.replace("/login");
  }

  /* Error state */
  if (error) {
    return (
      <div className="page-root">
        <TopBar />
        <main className="page-body">
          <div className="shell" style={{ paddingTop: "var(--sp-8)" }}>
            <p className="error" role="alert">{error}</p>
          </div>
        </main>
      </div>
    );
  }

  /* Loading skeleton */
  if (!user) {
    return (
      <div className="page-root">
        <TopBar />
        <main className="page-body">
          <div className="shell animate-in" style={{ paddingTop: "var(--sp-8)" }}>
            <SkeletonRow width="35%" />
            <div style={{ marginTop: 12 }}>
              <SkeletonRow width="55%" />
            </div>
            <div style={{ marginTop: 24, display: "grid", gap: 12 }}>
              <div className="skeleton skeleton-card" />
              <div className="skeleton skeleton-card" />
            </div>
          </div>
        </main>
      </div>
    );
  }

  const initials = user.full_name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <div className="page-root">
      <TopBar userName={user.full_name} onLogout={handleLogout} />

      <main className="page-body">
        <div className="shell animate-in">
          {/* ── Page header ── */}
          <div style={{ paddingBottom: "var(--sp-6)", borderBottom: "1px solid var(--border)", marginBottom: "var(--sp-6)" }}>
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "var(--sp-4)", flexWrap: "wrap" }}>
              <div>
                <p className="eyebrow">Dashboard</p>
                <h1 style={{ marginBottom: 8 }}>
                  Hello, {user.full_name.split(" ")[0]} 👋
                </h1>
                <p style={{ fontSize: 15, color: "var(--text-secondary)", maxWidth: "50ch" }}>
                  Manage evaluation workspaces, run batch experiments, and track your
                  RAG system&apos;s performance over time.
                </p>
              </div>
            </div>
          </div>

          {/* ── Quick actions ── */}
          <section style={{ marginBottom: "var(--sp-8)" }}>
            <h2 style={{ fontSize: 14, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.07em", color: "var(--text-muted)", marginBottom: "var(--sp-4)" }}>
              Quick actions
            </h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "var(--sp-3)" }}>
              <ActionCard
                href="/dashboard/projects"
                title="Browse Projects"
                desc="View all your RAG evaluation workspaces."
                icon={
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                    <polyline points="9 22 9 12 15 12 15 22"/>
                  </svg>
                }
              />
              <ActionCard
                href="/dashboard/projects/new"
                title="New Project"
                desc="Create an evaluation workspace for a new RAG system."
                icon={
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/>
                    <line x1="8" y1="12" x2="16" y2="12"/>
                  </svg>
                }
              />
            </div>
          </section>

          {/* ── User card ── */}
          <section>
            <h2 style={{ fontSize: 14, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.07em", color: "var(--text-muted)", marginBottom: "var(--sp-4)" }}>
              Your account
            </h2>
            <div className="card">
              <div style={{ padding: "var(--sp-5)", display: "flex", alignItems: "center", gap: "var(--sp-4)", borderBottom: "1px solid var(--border)" }}>
                <div style={{
                  width: 48, height: 48, borderRadius: "var(--radius-pill)",
                  background: "linear-gradient(135deg,var(--brand-400),var(--brand-600))",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 18, fontWeight: 700, color: "#fff", flexShrink: 0,
                }}>
                  {initials}
                </div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 16, color: "var(--text-primary)" }}>
                    {user.full_name}
                  </div>
                  <div style={{ fontSize: 13, color: "var(--text-muted)" }}>{user.email}</div>
                </div>
              </div>

              {/* Roles */}
              <div style={{ padding: "var(--sp-4) var(--sp-5)", display: "flex", alignItems: "center", justifyContent: "space-between", gap: "var(--sp-4)" }}>
                <span style={{ fontSize: 13, color: "var(--text-muted)" }}>Roles</span>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--sp-1)", justifyContent: "flex-end" }}>
                  {user.roles.map((role) => (
                    <span key={role.name} className="badge badge-green">
                      {role.name}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
