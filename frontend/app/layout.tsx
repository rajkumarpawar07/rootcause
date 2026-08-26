import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RootCause",
  description:
    "Shows a teacher what their class actually thinks — not just what they got wrong.",
};

/*
 * IMPECCABLE DIRECTION CONTRACT — seed 64617a38, "Midnight Slate"
 * THESIS: lecture blackboard at night rebuilt as a precision AI
 * instrument; refuses friendly pastel SaaS. OWN-WORLD: near-black
 * slate ground, chalk-white Bricolage/Hanken type, hairline rules,
 * registration crosses, JetBrains Mono readouts, one reserved amber
 * signal for action only. STORY: teacher pastes answers, instrument
 * prints the class's patterns; first viewport = centered invitation
 * on bare slate with amber primary action.
 */
const CONTRACT = `<!--
  IMPECCABLE DIRECTION CONTRACT seed=64617a38 world="Midnight Slate"
  THESIS: lecture blackboard at night as precision AI instrument; refuses pastel SaaS.
  OWN-WORLD: slate ground #0C120F, chalk type (Bricolage Grotesque / Hanken Grotesk / JetBrains Mono), hairline rules, registration crosses, reserved amber #F0A63C for action only.
  STORY: paste answers, instrument reads the class, prints patterns worth reteaching.
  FIRST VIEWPORT: wordmark top-left, centered chalk seedling, invitation heading, amber primary button on bare slate.
  FORM: assigned grounded candidate 4 of roll 64617a38; raises: registration grid (print annual), accent law (arcade), typed readouts (starship terminal), label rows (sneaker archive), growth draw-on (gravity garden).
  FINISH: unreviewed and undocumented is unfinished; ends with finish review, verdict, DESIGN.md, raster provenance.
-->`;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        {/* App Router renders this layout for every page; the pages-router
            rule below doesn't apply. Kept as a plain link so font behavior
            is deterministic across deployments. */}
        {/* eslint-disable-next-line @next/next/no-page-custom-font */}
        <link
          href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,600;12..96,700&family=Hanken+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap"
          rel="stylesheet"
        />
      </head>
      {/* suppressHydrationWarning: antivirus/browser extensions inject
          attributes into the served HTML before React hydrates; without
          this the dev console fills with false-positive hydration diffs.
          Real mismatches inside page components still surface. */}
      <body suppressHydrationWarning>
        <div hidden dangerouslySetInnerHTML={{ __html: CONTRACT }} />
        {children}
      </body>
    </html>
  );
}
