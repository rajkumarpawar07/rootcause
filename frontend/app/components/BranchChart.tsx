"use client";

import { useMemo } from "react";

import { ClusterCard } from "@/lib/api";

const CATEGORY_COLOR: Record<string, string> = {
  misconception: "var(--gold)",
  solid_understanding: "var(--moss)",
  unclear: "var(--ink-faint)",
};

const CATEGORY_TEXT: Record<string, string> = {
  misconception: "var(--ink)",
  solid_understanding: "var(--moss-text)",
  unclear: "var(--ink-muted)",
};

/**
 * The one deliberately bold visual element (design doc, screen 03):
 * a root trunk with one branch per pattern; branch thickness maps to the
 * share of the class sharing that reasoning.
 */
export default function BranchChart({ cards }: { cards: ClusterCard[] }) {
  const W = 800;
  const H = 210;
  const TRUNK_Y = 105;
  const TRUNK_X0 = 20;
  const TRUNK_X1 = 770;

  const branches = useMemo(() => {
    const n = Math.min(cards.length, 6);
    if (n === 0) return [];
    // Spread anchor points along the trunk between x=160 and x=620.
    const x0 = 160;
    const x1 = 620;
    return cards.slice(0, n).map((card, i) => {
      const ax = n === 1 ? (x0 + x1) / 2 : x0 + ((x1 - x0) * i) / (n - 1);
      const dir = i % 2 === 0 ? "down" : "up";
      const endY = TRUNK_Y + (dir === "down" ? 67 : -63);
      const cx = ax + 25;
      const cy = TRUNK_Y + (dir === "down" ? 40 : -36);
      const strokeWidth = Math.max(5, Math.round((card.percentage / 100) * 24) + 4);
      const dotR = Math.max(5, Math.min(9, 4 + card.size * 0.35));
      const color = CATEGORY_COLOR[card.category] ?? "var(--ink-faint)";
      return { card, ax, dir, endY, cx, cy, strokeWidth, dotR, color };
    });
  }, [cards]);

  const summary = cards
    .map((c) => `${c.percentage}% ${c.label}`)
    .join(", ");

  return (
    <div className="branch-wrap">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={`Branch diagram: ${summary}, branching off a shared trunk line.`}
      >
        <line
          x1={TRUNK_X0}
          y1={TRUNK_Y}
          x2={TRUNK_X1}
          y2={TRUNK_Y}
          stroke="var(--ink)"
          strokeWidth="3"
          strokeLinecap="round"
        />
        <circle cx={TRUNK_X0} cy={TRUNK_Y} r="5" fill="var(--ink)" />
        {branches.map(({ card, ax, endY, cx, cy, strokeWidth, dotR, color }) => {
          const labelX = Math.min(ax + 13, W - 170);
          const nameY = endY + (endY > TRUNK_Y ? -6 : -8);
          const pctY = endY + (endY > TRUNK_Y ? 12 : 10);
          return (
            <g key={card.cluster_id}>
              <path
                d={`M${ax},${TRUNK_Y} Q${cx},${cy} ${ax + 15},${endY}`}
                stroke={color}
                strokeWidth={strokeWidth}
                fill="none"
                strokeLinecap="round"
              />
              <circle cx={ax + 15} cy={endY} r={dotR} fill={color} />
              <text
                x={labelX}
                y={nameY}
                fontFamily="Karla, sans-serif"
                fontSize="14"
                fontWeight="600"
                fill={CATEGORY_TEXT[card.category] ?? "var(--ink)"}
              >
                {card.label}
              </text>
              <text
                x={labelX}
                y={pctY}
                fontFamily="IBM Plex Mono, monospace"
                fontSize="12"
                fill={CATEGORY_TEXT[card.category] ?? "var(--ink-muted)"}
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
    <div className="branch-rank" aria-hidden="false">
      {sorted.map((c) => (
        <div key={c.cluster_id} className="rank-row">
          <span>{c.label}</span>
          <span className="rank-pct">{c.percentage}%</span>
        </div>
      ))}
    </div>
  );
}
