export class DocuMdrError extends Error {
  readonly code: string;

  constructor(message: string, code: string) {
    super(message);
    this.name = new.target.name;
    this.code = code;
  }
}

export class ForbiddenContentError extends DocuMdrError {
  constructor(message: string) {
    super(message, "FORBIDDEN_CONTENT");
  }
}

export class ExportBlockedError extends DocuMdrError {
  constructor(message: string) {
    super(message, "EXPORT_BLOCKED");
  }
}

export class UpgradeRequiredError extends DocuMdrError {
  constructor(message: string) {
    super(message, "UPGRADE_REQUIRED");
  }
}

export class SeatLimitError extends DocuMdrError {
  constructor(message: string) {
    super(message, "SEAT_LIMIT");
  }
}

export class NotFoundError extends DocuMdrError {
  constructor(message: string) {
    super(message, "NOT_FOUND");
  }
}
