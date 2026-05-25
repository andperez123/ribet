"use client";

import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import type { UploadJob } from "@/lib/types/upload";

async function pollJob(jobId: string, maxAttempts = 90): Promise<UploadJob> {
  for (let i = 0; i < maxAttempts; i++) {
    const res = await fetch(`/api/ingest/jobs/${jobId}`);
    if (!res.ok) throw new Error(`Poll failed: ${res.status}`);
    const job = (await res.json()) as UploadJob;
    if (job.status === "done" || job.status === "error") return job;
    await new Promise((r) => setTimeout(r, 2000));
  }
  throw new Error("Demo data processing timed out");
}

export function TryDemoButton({
  className,
  children = "Try demo data",
}: {
  className?: string;
  children?: string;
}) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/org/demo", { method: "POST" });
      if (!res.ok) {
        throw new Error(await res.text());
      }
      const data = (await res.json()) as {
        org_id: string;
        jobs: UploadJob[];
      };
      const jobs = data.jobs ?? [];
      await Promise.all(jobs.map((j) => pollJob(j.id)));
      router.push("/dashboard");
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Demo failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={className}>
      <Button type="button" onClick={handleClick} disabled={loading}>
        {loading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Building demo…
          </>
        ) : (
          children
        )}
      </Button>
      {error && (
        <p className="mt-2 text-sm text-ribet-risk">{error}</p>
      )}
    </div>
  );
}
