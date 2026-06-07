export type JobError = {
  code: string;
  message: string;
  hint?: string | null;
  detail?: string | null;
};

export type IntakeMetadata = {
  encoding?: string;
  delimiter?: string;
  header_row_index?: number;
  skipped_rows?: number;
  sheet_name?: string | null;
  warnings?: string[];
};

/** Normalize API errors — supports legacy plain strings and structured objects. */
export function parseJobError(raw: unknown): JobError | null {
  if (raw == null) return null;

  if (typeof raw === "string") {
    const text = raw.trim();
    if (!text) return null;
    return {
      code: "legacy",
      message: text.split("\n", 1)[0],
      hint: text.toLowerCase().includes("could not detect")
        ? "Try exporting as CSV (.csv) from your ERP with column headers intact."
        : undefined,
      detail: text,
    };
  }

  if (typeof raw === "object") {
    const obj = raw as Record<string, unknown>;
    const message = String(obj.message ?? obj.detail ?? "").trim();
    if (!message) return null;
    return {
      code: String(obj.code ?? "processing_failed"),
      message,
      hint: obj.hint != null ? String(obj.hint) : undefined,
      detail: obj.detail != null ? String(obj.detail) : undefined,
    };
  }

  return null;
}

export function firstJobError(errors?: unknown[]): JobError | null {
  if (!errors?.length) return null;
  return parseJobError(errors[0]);
}
