import { redactText } from "../privacy/redact";
import { parseTags } from "../parser/tags";
import type { AnnexIvFile, GitEvent, RiskRow } from "../types";

const FIELD_RE = /\b(PURPOSE|METRIC|BIAS|OVERSIGHT|DATASET):(\S+)/g;

function fieldsFrom(message: string): Record<string, string> {
  const out: Record<string, string> = {};
  const re = new RegExp(FIELD_RE.source, "g");
  for (const match of message.matchAll(re)) {
    const key = match[1];
    let value = match[2] ?? "";
    if (key === "DATASET") value = value.slice(0, 200);
    out[key] = redactText(value);
  }
  return out;
}

function latestSha(events: GitEvent[]): string {
  return [...events].sort((a, b) => a.at.localeCompare(b.at)).at(-1)?.sha ?? "";
}

export function compileAnnexIv(input: {
  providerName: string;
  events: GitEvent[];
  risks: RiskRow[];
}): AnnexIvFile {
  const modelEvents = input.events.filter((event) =>
    parseTags(event.message).some((tag) => tag.kind === "MODEL"),
  );
  const merged: Record<string, string> = {};
  for (const event of modelEvents) Object.assign(merged, fieldsFrom(event.message));
  const version = latestSha(modelEvents.length > 0 ? modelEvents : input.events);
  const modelIds = [
    ...new Set(
      modelEvents.flatMap((event) =>
        parseTags(event.message)
          .filter((tag) => tag.kind === "MODEL")
          .map((tag) => `MODEL-${tag.id}`),
      ),
    ),
  ];
  const linkedRisks = input.risks.filter(
    (risk) =>
      risk.linkedItemIds.some((id) => modelIds.includes(id) || id.startsWith("AI-") || id.startsWith("MODEL-")) ||
      risk.id.startsWith("AI-"),
  );

  const sections: AnnexIvFile["sections"] = [
    {
      number: 1,
      title: "General description of the AI system",
      body: `Provider: ${input.providerName}. Intended purpose: ${merged.PURPOSE ?? "unspecified"}. Version (git SHA): ${version}. Models: ${modelIds.join(", ") || "none"}.`,
    },
    {
      number: 2,
      title: "Elements of the AI system and development process",
      body: `Methods and data (summary only): METRIC=${merged.METRIC ?? "n/a"}; BIAS=${merged.BIAS ?? "n/a"}; DATASET=${merged.DATASET ?? "n/a"}. Training-set files are not stored.`,
    },
    {
      number: 3,
      title: "Monitoring, functioning and control",
      body: `Accuracy/metrics: ${merged.METRIC ?? "n/a"}. Human oversight: ${merged.OVERSIGHT ?? "unspecified"}. Limitations: see residual risks.`,
    },
    {
      number: 4,
      title: "Appropriateness of performance metrics",
      body: `Declared metric: ${merged.METRIC ?? "unspecified"}. Manufacturer must justify appropriateness.`,
    },
    {
      number: 5,
      title: "Risk management system (Article 9)",
      body: linkedRisks.length
        ? linkedRisks.map((risk) => `${risk.id} RPN=${risk.rpn} verified=${risk.controlsVerified}`).join("; ")
        : "No AI-linked ISO 14971 rows yet.",
    },
    {
      number: 6,
      title: "Lifecycle changes",
      body: modelEvents.map((event) => `${event.at} ${event.sha} ${event.message.slice(0, 120)}`).join("\n") || "none",
    },
    {
      number: 7,
      title: "Harmonised standards applied",
      body: "IEC 62304:2006+AMD1:2015; ISO 14971:2019; ISO 13485:2016.",
    },
    {
      number: 8,
      title: "EU declaration of conformity (Article 47)",
      body: "DocuMDR never generates a signed EU declaration of conformity.",
      status: "not-signed",
    },
    {
      number: 9,
      title: "Post-market monitoring (Article 72)",
      body: "Placeholder post-market monitoring plan. Incident reporting is performed by the manufacturer, not DocuMDR.",
    },
  ];

  return { sections };
}
