"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { ClusterCard } from "@/lib/api";

const CATEGORY_COLOR: Record<string, string> = {
  misconception: "var(--ember)",
  solid_understanding: "var(--mint)",
  unclear: "var(--drift)",
};

const CATEGORY_TEXT: Record<string, string> = {
  misconception: "var(--ember)",
  solid_understanding: "var(--mint)",
  unclear: "var(--chalk-mid)",
};

const W = 800;
const H = 280;
const TRUNK_Y = 140;
const TRUNK_X0 = 20;
const TRUNK_X1 = 780;
const MAX_BRANCHES = 6;
const MAX_LINES = 3;
const NAME_FONT = 12.5;
const CHAR_PX = 6.6;

function wrapLabel(text: string, maxChars: number): string[] {
  const words = text.split(/\s+/).filter(Boolean);
  const lines: string[] = [];
  let cur = "";
  for (const word of words) {
    const cand = cur ? `${cur} ${word}` : word;
    if (cand.length <= maxChars || !cur) {
      cur = cand;
    } else {
      lines.push(cur);
      cur = word;
      if (lines.length === MAX_LINES) break;
    }
  }
  if (cur && lines.length < MAX_LINES) lines.push(cur);
  const consumed = lines.join(" ").length;
  const total = words.join(" ").length;
  if (consumed < total && lines.length === MAX_LINES) {
    let last = lines[MAX_LINES - 1];
    while (last.length + 1 > maxChars) {
      last = last.replace(/\s*\S*$/, "");
    }
    lines[MAX_LINES - 1] = `${last}…`;
  }
  return lines;
}

/** Subtle chalk-dust particles rising from the branch growth */
function BranchDust({ active }: { active: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [particles, setParticles] = useState<Array<{ x: number; y: number; vx: number; vy: number; life: number; color: string }>>([]);
  const raf = useRef<number | null>(null);

  useEffect(() => {
    if (!active) return;
    const canvas = canvasRef.current!;
    const ctx = canvas.getContext("2d")!;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;

    let lastTime = 0;
    function tick(time: number) {
      const dt = (time - lastTime) / 1000;
      lastTime = time;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      setParticles(prev => {
        const next = prev.map(p => {
          p.x += p.vx * dt;
          p.y += p.vy * dt;
          p.vy -= 8 * dt; // gentle upward drift
          p.life -= dt;
          return p;
        }).filter(p => p.life > 0);

        // spawn new particles near branch endpoints
        if (Math.random() < 0.15 * dt * 60) {
          const branchX = 0.15 + Math.random() * 0.7;
          const branchY = 0.35 + Math.random() * 0.45;
          next.push({
            x: branchX * canvas.width,
            y: branchY * canvas.height,
            vx: (Math.random() - 0.5) * 12,
            vy: -20 - Math.random() * 30,
            life: 1.5 + Math.random() * 1.5,
            color: Math.random() < 0.5 ? "rgba(232,146,98,0.4)" : "rgba(143,216,172,0.35)"
          });
        }
        return next;
      });

      particles.forEach(p => {
        const alpha = Math.min(1, p.life) * 0.35;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 1.5, 0, Math.PI * 2);
        ctx.fillStyle = p.color.replace(/[\d.]+\)$/, `${alpha})`);
        ctx.fill();
      });

      raf.current = requestAnimationFrame(tick);
    }
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current!);
  }, [active]);

  return <canvas ref={canvasRef} style={{ position: "absolute", inset: 0, pointerEvents: "none", zIndex: 1 }} />;
}

/**
 * The signature element (brand commitment): a chalk-drawn root system —
 * one trunk, one branch per pattern, branch thickness mapped to the share
 * of the class sharing that reasoning. Each branch owns its own column so
 * labels never collide. On arrival the roots grow out of the trunk (the one
 * authored motion moment on this screen); honors prefers-reduced-motion via
 * the global animation kill switch.
 */
export default function BranchChart({ cards }: { cards: ClusterCard[] }) {
  const branches = useMemo(() => {
    const n = Math.min(cards.length, MAX_BRANCHES);
    if (n === 0) return [];
    const margin = 24;
    const colW = (W - margin * 2) / n;
    return cards.slice(0, n).map((card, i) => {
      const ax = margin + colW * (i + 0.5);
      const dir = i % 2 === 0 ? "down" : "up";
      const endY = TRUNK_Y + (dir === "down" ? 52 : -52);
      const cx = ax + 16;
      const cy = TRUNK_Y + (dir === "down" ? 30 : -30);
      const strokeWidth = Math.max(4.5, Math.round((card.percentage / 100) * 24) + 3.5);
      const dotR = Math.max(4.5, Math.min(8.5, 3.5 + card.size * 0.32));
      const color = CATEGORY_COLOR[card.category] ?? "var(--drift)";
      const textMaxW = Math.min(colW - 8, 230);
      const maxChars = Math.max(10, Math.floor(textMaxW / CHAR_PX));
      const lines = wrapLabel(card.label, maxChars);
      // staggered draw-on; trunk draws first
      const delay = 0.25 + i * 0.12;
      return { card, ax, endY, cx, cy, strokeWidth, dotR, color, lines, delay };
    });
  }, [cards]);

  const summary = cards.map((c) => `${c.percentage}% ${c.label}`).join(", ");
  const [dustActive, setDustActive] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setDustActive(true), 1500);
    return () => clearTimeout(t);
  }, [cards.length]);

  if (cards.length === 0) return null;

  return (
    <div className="branch-wrap" style={{ position: "relative" }}>
      <BranchDust active={dustActive} />
      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={`Branch diagram: ${summary}, branching off a shared root.`}
      >
        {/* construction line — faint full-width rule the roots sit on */}
        <line
          x1={TRUNK_X0}
          y1={TRUNK_Y}
          x2={TRUNK_X1}
          y2={TRUNK_Y}
          stroke="var(--hairline)"
          strokeWidth="1"
        />
        {/* trunk */}
        <line
          x1={TRUNK_X0}
          y1={TRUNK_Y}
          x2={TRUNK_X1}
          y2={TRUNK_Y}
          stroke="var(--chalk)"
          strokeWidth="2.5"
          strokeLinecap="round"
          pathLength={1}
          className="branch-path"
          style={{ animationDelay: "0.05s", animationDuration: "0.7s" }}
        />
        <circle cx={TRUNK_X0} cy={TRUNK_Y} r="4" fill="var(--chalk)" />
        {branches.map(({ card, ax, endY, cx, cy, strokeWidth, dotR, color, lines, delay }) => {
          const down = endY > TRUNK_Y;
          const lineH = 16;
          // Down branches: name reads away from the dot, pct last.
          // Up branches: mirrored — pct on top, name reads toward the dot.
          const nameTop = down
            ? endY + dotR + 17
            : endY - dotR - 17 - (lines.length - 1) * lineH;
          const pctY = down
            ? nameTop + lines.length * lineH + 4
            : nameTop - 16;
          return (
            <g key={card.cluster_id}>
              <path
                d={`M${ax},${TRUNK_Y} Q${cx},${cy} ${ax},${endY}`}
                stroke={color}
                strokeWidth={strokeWidth}
                fill="none"
                strokeLinecap="round"
                pathLength={1}
                className="branch-path"
                style={{ animationDelay: `${delay}s` }}
              />
              <circle
                cx={ax}
                cy={endY}
                r={dotR}
                fill={color}
                className="branch-node"
                style={{ animationDelay: `${delay + 0.55}s` }}
              />
              {lines.map((line, li) => (
                <text
                  key={li}
                  x={ax}
                  y={nameTop + li * lineH}
                  textAnchor="middle"
                  fontFamily="'Hanken Grotesk', sans-serif"
                  fontSize={NAME_FONT}
                  fontWeight="600"
                  fill="var(--chalk)"
                  className="branch-text"
                  style={{ animationDelay: `${delay + 0.65 + li * 0.05}s` }}
                >
                  {line}
                </text>
              ))}
              <text
                x={ax}
                y={pctY}
                textAnchor="middle"
                fontFamily="'JetBrains Mono', monospace"
                fontSize="11.5"
                fill={CATEGORY_TEXT[card.category] ?? "var(--chalk-mid)"}
                className="branch-text"
                style={{ animationDelay: `${delay + 0.85}s` }}
              >
                {card.percentage}%
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

export function BranchRankedList({ cards }: { cards: ClusterCard[] }) {
  const sorted = [...cards].sort((a, b) => b.percentage - a.percentage);
  return (
    <div className="branch-rank">
      {sorted.map((c) => (
        <div key={c.cluster_id} className="rank-row">
          <span>{c.label}</span>
          <span className="rank-pct">{c.percentage}%</span>
        </div>
      ))}
    </div>
  );
}
