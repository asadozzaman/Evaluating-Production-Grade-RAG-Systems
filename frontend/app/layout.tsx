import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Inter } from "next/font/google";
import "./globals.css";

/* Inter loaded via next/font — zero layout shift, subset optimized */
const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "CLEAR-RAG",
    template: "%s · CLEAR-RAG",
  },
  description:
    "Production-grade RAG evaluation platform. Measure retrieval quality, faithfulness, and answer accuracy across every experiment.",
  icons: {
    icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='8' fill='%23059669'/><path d='M8 16l6 6 10-12' stroke='white' stroke-width='3' stroke-linecap='round' stroke-linejoin='round' fill='none'/></svg>",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" className={inter.variable}>
      <body>{children}</body>
    </html>
  );
}
