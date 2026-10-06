export type SafetyClass = "A" | "B" | "C";
export type TagKind =
  | "REQ"
  | "RISK"
  | "TEST"
  | "ARCH"
  | "UNIT"
  | "GSPR"
  | "AI"
  | "SOUP"
  | "CAPA"
  | "MODEL";

export type GitEvent = {
  id: string;
  organizationId: string;
  repository: string;
  sha: string;
  at: string;
  authorLogin: string;
  message: string;
  paths: string[];
  testSummary?: { passed: number; failed: number; skipped: number };
};

export type SoftwareItem = {
  id: string;
  kind: "REQ" | "ARCH" | "UNIT" | "TEST" | "SOUP";
  title: string;
  safetyClass: SafetyClass;
  shas: string[];
  linkedIds: string[];
  paths: string[];
};

export type MatrixRow = {
  reqId: string;
  archIds: string[];
  unitIds: string[];
  testIds: string[];
  status: "covered" | "partial" | "gap";
};

export type RiskRow = {
  id: string;
  hazard: string;
  sequence: string;
  harm: string;
  severity: 1 | 2 | 3 | 4 | 5;
  probability: 1 | 2 | 3 | 4 | 5;
  detectability: 1 | 2 | 3 | 4 | 5;
  rpn: number;
  linkedItemIds: string[];
  controls: string[];
  controlsVerified: boolean;
  changePrompt: boolean;
  probabilityBumpShas: string[];
  paths: string[];
};

export type GsprRow = {
  id: string;
  title: string;
  status: "met" | "unmet";
};

export type AnnexIvFile = {
  sections: Array<{ number: number; title: string; body: string; status?: string }>;
};

export type Role = "engineer" | "quality";
export type Tier = "free" | "team" | "ai";

export type User = {
  id: string;
  organizationId: string;
  email: string;
  role: Role;
  displayName: string;
};

export type Organization = {
  id: string;
  name: string;
  tier: Tier;
  iec62304Class: SafetyClass;
  mdrClass: "IIa";
  rule: "11";
  modules: { aiAct: boolean };
  invitedUserIds: string[];
};

export type Signature = {
  id: string;
  organizationId: string;
  artefact: "technical-file";
  meaning: string;
  signerUserId: string;
  signerRole: "quality";
  at: string;
  shaScope: string;
  userAgent: string;
};

export const DISCLAIMER =
  "DocuMDR compiles draft technical documentation from software-development metadata. It is not a notified body, does not issue CE marking, does not provide legal or regulatory advice, and is not itself a medical device. A qualified person must review and electronically sign artefacts before use. The manufacturer remains solely responsible for conformity with EU MDR 2017/745, IEC 62304, ISO 14971, ISO 13485, and Regulation (EU) 2024/1689.";

export const SIGNATURE_MEANING =
  "I have reviewed this compiled technical file. I am authorised to approve it for internal use. DocuMDR is not a Notified Body.";

export type TechnicalFile = {
  disclaimer: string;
  organizationId: string;
  headSha: string | null;
  matrix: MatrixRow[];
  fmea: RiskRow[];
  gspr: GsprRow[];
  annexIv?: AnnexIvFile;
  signatures: Signature[];
};
