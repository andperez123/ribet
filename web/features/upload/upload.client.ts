import { BFF } from "@/lib/api/endpoints";
import { firstJobError } from "@/lib/upload/job-errors";
import type {
  UploadClient,
  UploadFileMeta,
  UploadJob,
  UploadJobsResponse,
  UploadSector,
} from "@/lib/types/upload";

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function toMeta(
  file: File,
  status: UploadFileMeta["status"],
  sector: UploadSector,
  id?: string
): UploadFileMeta {
  return {
    id: id ?? crypto.randomUUID(),
    name: file.name,
    size: file.size,
    mimeType: file.type || "application/octet-stream",
    sector,
    status,
  };
}

/** Phase 1 — simulates upload + processing */
export class MockUploadClient implements UploadClient {
  async upload(files: File[], sector: UploadSector): Promise<UploadFileMeta[]> {
    const results: UploadFileMeta[] = files.map((f) =>
      toMeta(f, "uploading", sector)
    );

    await delay(600);
    for (const r of results) r.status = "processing";

    await delay(1400);
    for (const r of results) r.status = "done";

    return results;
  }
}

/** Calls Next.js BFF → FastAPI; returns after files are queued (async processing). */
export class ApiUploadClient implements UploadClient {
  async upload(
    files: File[],
    sector: UploadSector,
    consentAcknowledged = false,
    description?: string
  ): Promise<UploadFileMeta[]> {
    const form = new FormData();
    form.append("sector", sector);
    form.append("consent_acknowledged", consentAcknowledged ? "true" : "false");
    if (description?.trim()) {
      form.append("description", description.trim());
    }
    files.forEach((f) => form.append("files", f));

    const res = await fetch(BFF.ingest.uploads, {
      method: "POST",
      body: form,
    });

    if (!res.ok) {
      const detail = await res.text();
      throw new Error(
        detail ? `Upload failed: ${detail}` : `Upload failed: ${res.status}`
      );
    }

    const data = (await res.json()) as UploadJobsResponse;

    return data.jobs.map((job) => ({
      id: job.id,
      name: job.file_name,
      size: 0,
      mimeType: "application/octet-stream",
      sector: (job.sector as UploadSector | undefined) ?? sector,
      status: normalizeJobStatus(job.status),
      error: firstJobError(job.errors) ?? undefined,
      reportId: job.report_id ?? undefined,
      intakeMetadata: job.intake_metadata ?? undefined,
    }));
  }

  async pollJob(jobId: string): Promise<UploadJob> {
    const res = await fetch(BFF.ingest.job(jobId));
    if (!res.ok) throw new Error(`Poll failed: ${res.status}`);
    const job = (await res.json()) as UploadJob;
    return { ...job, status: normalizeJobStatus(job.status) };
  }
}

function normalizeJobStatus(
  status: string
): UploadFileMeta["status"] {
  if (status === "pending") return "processing";
  if (
    status === "processing" ||
    status === "done" ||
    status === "error" ||
    status === "uploading" ||
    status === "needs_review"
  ) {
    return status;
  }
  return "processing";
}

export function createUploadClient(mode: "mock" | "api"): UploadClient {
  return mode === "api" ? new ApiUploadClient() : new MockUploadClient();
}
