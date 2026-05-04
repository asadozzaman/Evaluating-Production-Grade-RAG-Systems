/* Landing page — dark hero + feature grid */
import Link from "next/link";

function CheckIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

const features = [
  {
    title: "Retrieval Quality Metrics",
    desc: "Hit rate, Precision@K, Recall@K, MRR, and chunk coverage measured automatically across every run.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        <line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/>
      </svg>
    ),
  },
  {
    title: "Multi-Dimension Scoring",
    desc: "Five structured evaluation axes: Citation Quality, Faithfulness, Relevance, Retrieval, and Latency/Cost.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
      </svg>
    ),
  },
  {
    title: "Batch Experiment Runs",
    desc: "Fire Gemini RAG over entire question datasets with one click. Keyword or vector retrieval — your choice.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
      </svg>
    ),
  },
  {
    title: "Experiment Leaderboard",
    desc: "Compare every run on a ranked leaderboard. Instantly see which configuration wins on every dimension.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/>
        <line x1="6" y1="20" x2="6" y2="14"/>
      </svg>
    ),
  },
  {
    title: "Production Readiness Gates",
    desc: "Automated pass/warn/fail gates validate your RAG system against configurable quality thresholds before release.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      </svg>
    ),
  },
  {
    title: "Human-in-the-Loop Review",
    desc: "Judge calibration, bias detection, and structured human review workflows to catch what automation misses.",
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
        <circle cx="9" cy="7" r="4"/>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
      </svg>
    ),
  },
];

export default function Home() {
  return (
    <div className="landing-root">
      {/* ── Navigation ── */}
      <nav className="landing-nav" aria-label="Main navigation">
        <Link href="/" className="landing-nav-brand" aria-label="CLEAR-RAG home">
          <div className="landing-nav-logo" aria-hidden="true">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <span className="landing-nav-name">CLEAR-RAG</span>
        </Link>
        <div className="landing-nav-links">
          <Link
            href="/login"
            className="btn btn-ghost btn-sm"
            style={{ color: "var(--slate-400)", borderColor: "transparent" }}
          >
            Sign in
          </Link>
          <Link href="/register" className="btn btn-primary btn-sm">
            Get started
          </Link>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="landing-hero animate-in" aria-label="Hero">
        <div className="landing-badge" aria-label="Product category">
          <CheckIcon />
          Production-Grade RAG Evaluation
        </div>

        <h1>
          Know exactly how good<br />
          your <span className="landing-accent">RAG system</span> is.
        </h1>

        <p>
          CLEAR-RAG gives your team a structured workflow to measure retrieval
          quality, answer faithfulness, and model accuracy — across every
          experiment, every dataset, every release.
        </p>

        <div className="landing-actions">
          <Link href="/register" className="btn btn-primary btn-lg">
            Create workspace
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
            </svg>
          </Link>
          <Link href="/login" className="btn btn-outline btn-lg" style={{ color: "var(--slate-300)", borderColor: "rgba(255,255,255,.15)", background: "rgba(255,255,255,.05)" }}>
            Sign in to existing workspace
          </Link>
        </div>
      </section>

      {/* ── Feature grid ── */}
      <section className="landing-features" aria-label="Features">
        <p className="landing-features-eyebrow">Everything you need</p>
        <h2>A complete RAG evaluation framework</h2>

        <div className="landing-features-grid">
          {features.map((feature) => (
            <div className="landing-feature-card" key={feature.title}>
              <div className="landing-feature-icon" aria-hidden="true">
                {feature.icon}
              </div>
              <div className="landing-feature-title">{feature.title}</div>
              <p className="landing-feature-desc">{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
