import { parseTags } from "../parser/tags";
import type { GitEvent, RiskRow } from "../types";

export type ParsedRiskFields = {
  severity?: 1 | 2 | 3 | 4 | 5;
  probability?: 1 | 2 | 3 | 4 | 5;
  detectability?: 1 | 2 | 3 | 4 | 5;
  hazard?: string;
  harm?: string;
  control?: string;
};

function rating(value: string | undefined): 1 | 2 | 3 | 4 | 5 | undefined {
  if (!value) return undefined;
  const n = Number(value);
  if (n === 1 || n === 2 || n === 3 || n === 4 || n === 5) return n;
  return undefined;
}

export function parseRiskFields(message: string): ParsedRiskFields {
  const s = message.match(/\bS:([1-5])\b/);
  const p = message.match(/\bP:([1-5])\b/);
  const d = message.match(/\bD:([1-5])\b/);
  const hazard = message.match(/\bHAZARD:(\S+)/);
  const harm = message.match(/\bHARM:(\S+)/);
  const control = message.match(/\bCONTROL:(\S+)/);
  return {
    severity: rating(s?.[1]),
    probability: rating(p?.[1]),
    detectability: rating(d?.[1]),
    hazard: hazard?.[1],
    harm: harm?.[1],
    control: control?.[1],
  };
}

export function rpn(row: Pick<RiskRow, "severity" | "probability" | "detectability">): number {
  return row.severity * row.probability * row.detectability;
}

export function isUnacceptable(row: RiskRow): boolean {
  return rpn(row) >= 40 && !row.controlsVerified;
}

function tagFullId(kind: string, id: string): string {
  return `${kind}-${id}`;
}

function cloneRow(row: RiskRow): RiskRow {
  return {
    ...row,
    linkedItemIds: [...row.linkedItemIds],
    controls: [...row.controls],
    probabilityBumpShas: [...row.probabilityBumpShas],
    paths: [...row.paths],
  };
}

export function upsertRisks(rows: RiskRow[], event: GitEvent): RiskRow[] {
  const tags = parseTags(event.message);
  const riskTags = tags.filter((tag) => tag.kind === "RISK");
  if (riskTags.length === 0) return rows.map(cloneRow);

  const fields = parseRiskFields(event.message);
  const explicitP = fields.probability !== undefined;
  const next = rows.map(cloneRow);

  for (const tag of riskTags) {
    const id = tagFullId("RISK", tag.id);
    const linkedItemIds = tags
      .filter((other) => !(other.kind === "RISK" && other.id === tag.id))
      .map((other) => tagFullId(other.kind, other.id));
    let row = next.find((r) => r.id === id);
    const creating = !row;
    if (!row) {
      row = {
        id,
        hazard: fields.hazard ?? firstLine(event.message),
        sequence: "",
        harm: fields.harm ?? "",
        severity: fields.severity ?? 3,
        probability: fields.probability ?? 3,
        detectability: fields.detectability ?? 3,
        rpn: 0,
        linkedItemIds: [],
        controls: fields.control ? [fields.control] : [],
        controlsVerified: false,
        changePrompt: false,
        probabilityBumpShas: [],
        paths: [],
      };
      next.push(row);
    }

    const overlapPath = event.paths.some((p) => row.paths.includes(p));
    const overlapItem = linkedItemIds.some((itemId) => row.linkedItemIds.includes(itemId));

    if (!creating && (overlapItem || overlapPath)) {
      row.changePrompt = true;
      row.controlsVerified = false;
      if (!explicitP && !row.probabilityBumpShas.includes(event.sha)) {
        row.probability = Math.min(5, (row.probability + 1) as 1 | 2 | 3 | 4 | 5) as 1 | 2 | 3 | 4 | 5;
        row.probabilityBumpShas.push(event.sha);
      }
    }

    if (fields.severity) row.severity = fields.severity;
    if (fields.probability) row.probability = fields.probability;
    if (fields.detectability) row.detectability = fields.detectability;
    if (fields.hazard) row.hazard = fields.hazard;
    if (fields.harm) row.harm = fields.harm;
    if (fields.control && !row.controls.includes(fields.control)) row.controls.push(fields.control);
    row.linkedItemIds = [...new Set([...row.linkedItemIds, ...linkedItemIds])];
    row.paths = [...new Set([...row.paths, ...event.paths])];
    row.rpn = rpn(row);
  }

  return next;
}

function firstLine(message: string): string {
  return message.split("\n")[0]?.trim() ?? "";
}

export function verifyRiskControl(rows: RiskRow[], riskId: string): RiskRow[] {
  return rows.map((row) => {
    if (row.id !== riskId) return cloneRow(row);
    const next = cloneRow(row);
    next.controlsVerified = true;
    next.changePrompt = false;
    next.rpn = rpn(next);
    return next;
  });
}
