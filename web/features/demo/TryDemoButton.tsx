"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import type { UploadJob } from "@/lib/types/upload";

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
      if (!data.jobs?.length) {
        throw new Error("Demo created but no files were queued");
      }
      router.push("/dashboard?processing=demo");
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
        {loading ? "Creating demo workspace…" : children}
      </Button>
      {error && (
        <p className="mt-2 text-sm text-ribet-risk">{error}</p>
      )}
    </div>
  );
}
