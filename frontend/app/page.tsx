const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  return (
    <main>
      <section className="shell">
        <p className="eyebrow">CLEAR-RAG</p>
        <h1>Project foundation is ready.</h1>
        <p className="summary">
          FastAPI, Next.js, and PostgreSQL are wired for local development.
          Business features will be added in later iterations.
        </p>
        <div className="status" aria-label="Project foundation status">
          <div className="status-row">
            <span>Frontend</span>
            <span>Next.js</span>
          </div>
          <div className="status-row">
            <span>Backend health endpoint</span>
            <span>{apiUrl}/health</span>
          </div>
          <div className="status-row">
            <span>Database</span>
            <span>PostgreSQL via Docker Compose</span>
          </div>
        </div>
      </section>
    </main>
  );
}
