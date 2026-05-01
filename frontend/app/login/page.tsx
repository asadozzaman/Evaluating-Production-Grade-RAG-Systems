"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { AuthResponse, TOKEN_STORAGE_KEY, authRequest } from "../lib/auth";

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
    <main>
      <section className="auth-panel">
        <p className="eyebrow">CLEAR-RAG</p>
        <h1>Sign in</h1>
        <p className="summary">Access the evaluation workspace with your assigned role.</p>

        <form className="form" onSubmit={handleSubmit}>
          <label>
            Email
            <input name="email" type="email" autoComplete="email" required />
          </label>
          <label>
            Password
            <input name="password" type="password" autoComplete="current-password" required />
          </label>
          {error ? <p className="error">{error}</p> : null}
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="auth-switch">
          New workspace? <Link href="/register">Create the first account</Link>
        </p>
      </section>
    </main>
  );
}
