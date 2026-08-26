"use client";

export default function Badge({
  text,
  kind,
}: {
  text: string;
  kind: "ember" | "mint" | "slate";
}) {
  // Every badge carries a text label so meaning survives without color
  // (accessibility floor).
  return <span className={`badge badge-${kind}`}>{text}</span>;
}
