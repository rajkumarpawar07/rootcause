import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RootCause",
  description:
    "Shows a teacher what their class actually thinks — not just what they got wrong.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        {/* App Router renders this layout for every page; the pages-router
            rule below doesn't apply. Kept as a plain link so font behavior
            matches the design document exactly. */}
        {/* eslint-disable-next-line @next/next/no-page-custom-font */}
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Karla:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap"
          rel="stylesheet"
        />
      </head>
      {/* suppressHydrationWarning: antivirus/browser extensions (e.g. Bitdefender's
          bis_skin_checked) inject attributes into the served HTML before React
          hydrates; without this the dev console fills with false-positive
          hydration diffs. Scoped to the shell only — real mismatches inside
          page components still surface. */}
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
