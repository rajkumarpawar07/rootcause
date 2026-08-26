"use client";

import Badge from "./Badge";
import BranchChart, { BranchRankedList } from "./BranchChart";
import { ClusterCard, DiagnoseResult } from "@/lib/api";

const BADGE_BY_CATEGORY: Record<
  string,
  { text: string; kind: "ember" | "mint" | "slate" }
> = {
  misconception: { text: "Misconception", kind: "ember" },
  solid_understanding: { text: "Solid understanding", kind: "mint" },
  unclear: { text: "Unclear", kind: "slate" },
};

export function cardSortKey(c: ClusterCard): number {
  if (c.category === "unclear") return 2;
  if (c.category === "solid_understanding") return 1;
  return 0;
}

export default function Screen03Dashboard({
  result,
  onNewDiagnostic,
  onViewCluster,
}: {
  result: DiagnoseResult;
  onNewDiagnostic: () => void;
  onViewCluster: (clusterId: number) => void;
}) {
  const cards = [...result.clusters].sort(
    (a, b) => cardSortKey(a) - cardSortKey(b) || b.size - a.size
  );
  const misconceptionCount = cards.filter(
    (c) => c.category === "misconception"
  ).length;
  const solidPct =
    cards.find((c) => c.category === "solid_understanding")?.percentage ?? 0;

  return (
    <div>
      <div className="dash-head">
        <h3>{result.question}</h3>
        <button className="btn btn-secondary" onClick={onNewDiagnostic}>
          New diagnostic
        </button>
      </div>

      <div className="stat-band">
        <div className="stat-cell">
          <div className="label">Responses analyzed</div>
          <div className="num">{result.responses_analyzed}</div>
        </div>
        <div className="stat-cell">
          <div className="label">Misconceptions found</div>
          <div className="num">{misconceptionCount}</div>
        </div>
        <div className="stat-cell">
          <div className="label">Solid understanding</div>
          <div className="num">{solidPct}%</div>
        </div>
      </div>

      <BranchChart cards={cards} />
      <BranchRankedList cards={cards} />

      <div className="cluster-list">
        {cards.map((card) => {
          const badge = BADGE_BY_CATEGORY[card.category];
          return (
            <div key={card.cluster_id} className="cluster-card">
              <div className="cluster-top">
                <div className="left">
                  <Badge text={badge.text} kind={badge.kind} />
                  <span className="title">{card.label}</span>
                </div>
                <span className="share">
                  <b>{card.size}</b> · {card.percentage}%
                </span>
              </div>
              <div className="cluster-meta-row">
                <span className="meta-key">Example</span>
                <p className="cluster-example">&ldquo;{card.example_response}&rdquo;</p>
              </div>
              <div className="cluster-meta-row">
                <span className="meta-key">Reteach</span>
                <p className="cluster-suggest">{card.reteach_suggestion}</p>
              </div>
              <button
                className="cluster-link"
                onClick={() => onViewCluster(card.cluster_id)}
              >
                View all {card.size} student{card.size === 1 ? "" : "s"} &rarr;
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
