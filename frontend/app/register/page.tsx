"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { AuthResponse, TOKEN_STORAGE_KEY, authRequest } from "../lib/auth";

function BrandPanel() {
  return (
    <aside className="auth-brand-panel" aria-hidden="true">
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 48 }}>
        <div style={{
          width: 40, height: 40, borderRadius: 10,
          background: "linear-gradient(135deg,var(--brand-500),var(--brand-700))",
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </div>
        <span style={{ fontWeight: 700, fontSize: 20, color: "#fff", letterSpacing: "-0.02em" }}>
          CLEAR-RAG
        </span>
      </div>

      <h2 style={{ color: "#fff", fontSize: "clamp(22px,3.5vw,34px)", fontWeight: 800, letterSpacing: "-0.02em", lineHeight: 1.1, marginBottom: 18 }}>
        Your first step toward<br />reliable RAG systems.
      </h2>
      <p style={{ color: "var(--slate-400)", fontSize: 15, lineHeight: 1.65, maxWidth: "42ch", marginBottom: 44 }}>
        The first account you create becomes admin. Subsequent accounts join as
        viewers until promoted.
      </p>

      {/* Steps */}
      <ol style={{ display: "grid", gap: 20, listStyle: "none" }}>
        {[
          ["Create workspace", "Register your admin account to get started."],
          ["Import documents", "Upload or link your knowledge-base documents."],
          ["Run evaluation", "Fire batch experiments and inspect every score."],
        ].map(([title, desc], i) => (
          <li key={title} style={{ display: "flex", gap: 14 }}>
            <span style={{
              width: 28, height: 28, borderRadius: "50%", flexShrink: 0,
              background: "rgba(16,185,129,.15)",
              border: "1px solid rgba(16,185,129,.3)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 13, fontWeight: 700, color: "var(--brand-400)",
            }}>
              {i + 1}
            </span>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600, color: "#fff", marginBottom: 2 }}>{title}</div>
              <div style={{ fontSize: 13, color: "var(--slate-500)", lineHeight: 1.5 }}>{desc}</div>
            </div>
          </li>
        ))}
      </ol>
    </aside>
  );
}

export default function RegisterPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    const formData = new FormData(event.currentTarget);
    const payload = {
      full_name: String(formData.get("fullName") ?? ""),
      email: String(formData.get("email") ?? ""),
      password: String(formData.get("password") ?? ""),
    };

    try {
      const response = await authRequest<AuthResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to register");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="auth-root">
      <BrandPanel />

      <main className="auth-form-panel">
        <div className="auth-form-inner animate-in">
          {/* Mobile logo */}
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 40 }}>
            <div style={{
              width: 34, height: 34, borderRadius: 8,
              background: "linear-gradient(135deg,var(--brand-500),var(--brand-700))",
              display: "flex", alignItems: "center", justifyContent: "center",
              flexShrink: 0,
            }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <span style={{ fontWeight: 700, fontSize: 17, color: "var(--text-primary)", letterSpacing: "-0.02em" }}>
              CLEAR-RAG
            </span>
          </div>

          <h1 style={{ fontSize: 26, fontWeight: 800, letterSpacing: "-0.02em", marginBottom: 6 }}>
            Create your workspace
          </h1>
          <p style={{ fontSize: 15, color: "var(--text-muted)", marginBottom: 28 }}>
            The first registered account becomes admin.
          </p>

          <form className="form" onSubmit={handleSubmit} noValidate>
            <label>
              Full name
              <input
                name="fullName"
                type="text"
                autoComplete="name"
                placeholder="Jane Smith"
                required
              />
            </label>
            <label>
              Email address
              <input
                name="email"
                type="email"
                autoComplete="email"
                placeholder="jane@company.com"
                required
              />
            </label>
            <label>
              Password
              <input
                name="password"
                type="password"
                autoComplete="new-password"
                placeholder="At least 8 characters"
                minLength={8}
                required
              />
            </label>

            {error && <p className="error" role="alert">{error}</p>}

            <button
              type="submit"
              className={`btn btn-primary${isSubmitting ? " btn-loading" : ""}`}
              style={{ width: "100%", height: 44, fontSize: 15 }}
              disabled={isSubmitting}
            >
              {isSubmitting ? "" : "Create account"}
            </button>
          </form>

          <p className="auth-switch">
            Already have an account? <Link href="/login">Sign in</Link>
          </p>
        </div>
      </main>
    </div>
  );
}
