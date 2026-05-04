"use client";

import Link from "next/link";
import type { ReactNode } from "react";

interface TopBarProps {
  userName?: string;
  /** Called when the user clicks Sign out */
  onLogout?: () => void;
  /** Extra nav links/actions rendered between the logo and the user chip */
  children?: ReactNode;
}

/* Inline SVG logo mark — no external dependency */
function LogoMark() {
  return (
    <div className="topbar-logo" aria-hidden="true">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path
          d="M2.5 8.5L6 12L13.5 4"
          stroke="white"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}

export default function TopBar({ userName, onLogout, children }: TopBarProps) {
  const initials = userName
    ? userName
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "?";

  return (
    <header className="topbar" role="banner">
      {/* Brand */}
      <Link href="/dashboard" className="topbar-brand" aria-label="CLEAR-RAG dashboard">
        <LogoMark />
        <span className="topbar-name">CLEAR-RAG</span>
      </Link>

      {/* Flexible spacer */}
      <div className="topbar-sep" />

      {/* Nav slots (breadcrumb links, page-specific actions) */}
      {children && <nav className="topbar-nav">{children}</nav>}

      {/* User chip */}
      {userName && (
        <div className="topbar-user" aria-label={`Signed in as ${userName}`}>
          <div className="topbar-avatar" aria-hidden="true">
            {initials}
          </div>
          <span className="topbar-username">{userName}</span>
        </div>
      )}

      {/* Logout */}
      {onLogout && (
        <button
          type="button"
          className="topbar-link"
          onClick={onLogout}
          aria-label="Sign out"
        >
          {/* Exit icon */}
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
          Sign out
        </button>
      )}
    </header>
  );
}
