import { BFF } from "@/lib/api/endpoints";
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

/** Calls Next.js BFF → FastAPI */
export class ApiUploadClient implements UploadClient {
  async upload(files: File[], sector: UploadSector): Promise<UploadFileMeta[]> {
    const form = new FormData();
    form.append("sector", sector);
    files.forEach((f) => form.append("files", f));

    const res = await fetch(BFF.ingest.uploads, {
      method: "POST",
      body: form,
    });

    if (!res.ok) {
      throw new Error(`Upload failed: ${res.status}`);
    }

    const data = (await res.json()) as UploadJobsResponse;

    const results: UploadFileMeta[] = data.jobs.map((job) => ({
      id: job.id,
      name: job.file_name,
      size: 0,
      mimeType: "application/octet-stream",
      sector: (job.sector as UploadSector | undefined) ?? sector,
      status: job.status,
      error: job.errors?.[0],
      reportId: job.report_id ?? undefined,
    }));

    await Promise.all(
      results.map(async (meta) => {
        if (meta.status === "pending" || meta.status === "processing") {
          const final = await this.pollUntilDone(meta.id);
          meta.status = final.status;
          if (final.reportId) meta.reportId = final.reportId;
        }
      })
    );

    return results;
  }

  async pollJob(jobId: string): Promise<UploadJob> {
    const res = await fetch(BFF.ingest.job(jobId));
    if (!res.ok) throw new Error(`Poll failed: ${res.status}`);
    return res.json() as Promise<UploadJob>;
  }

  private async pollUntilDone(
    jobId: string,
    maxAttempts = 60
  ): Promise<{ status: UploadFileMeta["status"]; reportId?: string }> {
    for (let i = 0; i < maxAttempts; i++) {
      const job = await this.pollJob(jobId);
      if (job.status === "done" || job.status === "error") {
        return {
          status: job.status,
          reportId: job.report_id ?? undefined,
        };
      }
      await delay(2000);
    }
    return { status: "error" };
  }
}

export function createUploadClient(mode: "mock" | "api"): UploadClient {
  return mode === "api" ? new ApiUploadClient() : new MockUploadClient();
}
