import { ForbiddenContentError } from "../errors";

const EMAIL_RE = /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi;
const BEARER_RE = /Bearer\s+\S+/gi;
const AWS_KEY_RE = /\bAKIA[0-9A-Z]{16}\b/g;
const PRIVATE_KEY_RE =
  /-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/g;
const PPS_RE = /\b\d{7}[A-Z]{1,2}\b/g;
const NHS_RE = /\b\d{3}\s\d{3}\s\d{4}\b/g;
const IBAN_RE = /\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b/g;
const CLINICAL_RE = /\bPATIENT\b|MRN:|DOB:/i;

export function redactText(input: string): string {
  return input
    .replace(EMAIL_RE, "[REDACTED_EMAIL]")
    .replace(PRIVATE_KEY_RE, "[REDACTED_SECRET]")
    .replace(BEARER_RE, "[REDACTED_SECRET]")
    .replace(AWS_KEY_RE, "[REDACTED_SECRET]")
    .replace(IBAN_RE, "[REDACTED_IBAN]")
    .replace(PPS_RE, "[REDACTED_PPS]")
    .replace(NHS_RE, "[REDACTED_NHS]");
}

export function assertAllowedContent(input: string): void {
  const redacted = redactText(input);
  if (CLINICAL_RE.test(redacted)) {
    throw new ForbiddenContentError(
      "Refusing to persist special-category or patient identifiers",
    );
  }
}
