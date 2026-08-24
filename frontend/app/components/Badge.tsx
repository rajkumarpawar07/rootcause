"use client";

export default function Badge({
  text,
  kind,
}: {
  text: string;
  kind: "gold" | "moss" | "muted";
}) {
  // Every badge carries a text label so meaning survives without color
  // (design doc: responsive & accessibility).
  return <span className={`badge badge-${kind}`}>{text}</span>;
}
