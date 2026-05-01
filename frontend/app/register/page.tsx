"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { AuthResponse, TOKEN_STORAGE_KEY, authRequest } from "../lib/auth";

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
    <main>
      <section className="auth-panel">
        <p className="eyebrow">CLEAR-RAG</p>
        <h1>Create account</h1>
        <p className="summary">
          The first registered account becomes admin. Later accounts start as viewers.
        </p>

        <form className="form" onSubmit={handleSubmit}>
          <label>
            Full name
            <input name="fullName" type="text" autoComplete="name" required />
          </label>
          <label>
            Email
            <input name="email" type="email" autoComplete="email" required />
          </label>
          <label>
            Password
            <input
              name="password"
              type="password"
              autoComplete="new-password"
              minLength={8}
              required
            />
          </label>
          {error ? <p className="error">{error}</p> : null}
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Creating..." : "Create account"}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account? <Link href="/login">Sign in</Link>
        </p>
      </section>
    </main>
  );
}
