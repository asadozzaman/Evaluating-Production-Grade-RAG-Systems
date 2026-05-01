"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { TOKEN_STORAGE_KEY, User, authRequest } from "../lib/auth";

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

  if (error) {
    return (
      <main>
        <section className="shell">
          <p className="error">{error}</p>
        </section>
      </main>
    );
  }

  if (!user) {
    return (
      <main>
        <section className="shell">
          <p className="summary">Loading dashboard...</p>
        </section>
      </main>
    );
  }

  return (
    <main>
      <section className="shell">
        <div className="dashboard-header">
          <div>
            <p className="eyebrow">CLEAR-RAG</p>
            <h1>Dashboard</h1>
          </div>
          <button className="secondary-button" type="button" onClick={handleLogout}>
            Sign out
          </button>
        </div>

        <p className="summary">
          Project setup APIs are active. Prepare evaluation workspaces, source document
          metadata, test questions, and evaluation runs before scoring begins.
        </p>

        <div className="actions">
          <Link href="/dashboard/projects">Open projects</Link>
          <Link href="/dashboard/projects/new">New project</Link>
        </div>

        <div className="status" aria-label="Current user">
          <div className="status-row">
            <span>User</span>
            <span>{user.full_name}</span>
          </div>
          <div className="status-row">
            <span>Email</span>
            <span>{user.email}</span>
          </div>
          <div className="status-row">
            <span>Roles</span>
            <span>{user.roles.map((role) => role.name).join(", ")}</span>
          </div>
        </div>
      </section>
    </main>
  );
}
