export const TAG_KINDS = [
  "REQ",
  "RISK",
  "TEST",
  "ARCH",
  "UNIT",
  "GSPR",
  "AI",
  "SOUP",
  "CAPA",
  "MODEL",
] as const;

export type TagKind = (typeof TAG_KINDS)[number];

export type ParsedTag = {
  kind: TagKind;
  id: string;
  raw: string;
};

export const TAG_RE =
  /#(?<kind>REQ|RISK|TEST|ARCH|UNIT|GSPR|AI|SOUP|CAPA|MODEL)-(?<id>[A-Z0-9][A-Z0-9._-]{0,31})/g;

export function parseTags(text: string): ParsedTag[] {
  const tags: ParsedTag[] = [];
  const re = new RegExp(TAG_RE.source, "g");
  for (const match of text.matchAll(re)) {
    const kind = match.groups?.kind as TagKind | undefined;
    const id = match.groups?.id;
    if (!kind || !id) continue;
    tags.push({ kind, id, raw: match[0] });
  }
  return tags;
}
