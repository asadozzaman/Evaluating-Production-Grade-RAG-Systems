"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { AuthResponse, TOKEN_STORAGE_KEY, authRequest } from "../lib/auth";

/* ── Brand panel illustration ── */
function BrandPanel() {
  return (
    <aside className="auth-brand-panel" aria-hidden="true">
      {/* Logo */}
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

      {/* Headline */}
      <h2 style={{ color: "#fff", fontSize: "clamp(24px,3.5vw,36px)", fontWeight: 800, letterSpacing: "-0.02em", lineHeight: 1.1, marginBottom: 20 }}>
        Evaluate your RAG<br />system with precision.
      </h2>
      <p style={{ color: "var(--slate-400)", fontSize: 16, lineHeight: 1.65, maxWidth: "40ch", marginBottom: 48 }}>
        Structured workflows for retrieval quality, faithfulness scoring,
        and production readiness — across every run.
      </p>

      {/* Metrics callout cards */}
      <div style={{ display: "grid", gap: 12 }}>
        {[
          ["Hit Rate", "94.2%", "Retrieval coverage"],
          ["Avg Faithfulness", "4.3 / 5", "Evidence grounding"],
          ["Production Gate", "Passed", "Ready to ship"],
        ].map(([label, value, sub]) => (
          <div key={label} style={{
            background: "rgba(255,255,255,.06)",
            border: "1px solid rgba(255,255,255,.1)",
            borderRadius: 10,
            padding: "14px 18px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 16,
            backdropFilter: "blur(8px)",
          }}>
            <div>
              <div style={{ fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--slate-400)", marginBottom: 2 }}>{label}</div>
              <div style={{ fontSize: 12, color: "var(--slate-500)" }}>{sub}</div>
            </div>
            <span style={{ fontSize: 18, fontWeight: 700, color: "var(--brand-300)", letterSpacing: "-0.02em" }}>{value}</span>
          </div>
        ))}
      </div>
    </aside>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    const formData = new FormData(event.currentTarget);
    const payload = {
      email: String(formData.get("email") ?? ""),
      password: String(formData.get("password") ?? ""),
    };

    try {
      const response = await authRequest<AuthResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to log in");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="auth-root">
      <BrandPanel />

      {/* ── Form panel ── */}
      <main className="auth-form-panel">
        <div className="auth-form-inner animate-in">
          {/* Logo (mobile — brand panel hidden on small screens) */}
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
            Welcome back
          </h1>
          <p style={{ fontSize: 15, color: "var(--text-muted)", marginBottom: 28 }}>
            Sign in to access the evaluation workspace.
          </p>

          <form className="form" onSubmit={handleSubmit} noValidate>
            <label>
              Email address
              <input
                name="email"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                required
              />
            </label>
            <label>
              Password
              <input
                name="password"
                type="password"
                autoComplete="current-password"
                placeholder="Your password"
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
              {isSubmitting ? "" : "Sign in"}
            </button>
          </form>

          <p className="auth-switch">
            No workspace yet?{" "}
            <Link href="/register">Create the first account</Link>
          </p>
        </div>
      </main>
    </div>
  );
}
