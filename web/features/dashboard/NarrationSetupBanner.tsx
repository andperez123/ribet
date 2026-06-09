"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";

type Features = {
  narration_enabled: boolean;
  openai_configured: boolean;
  narration_env: string;
};

export function NarrationSetupBanner() {
  const [features, setFeatures] = useState<Features | null>(null);

  useEffect(() => {
    fetch("/api/org/features")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => setFeatures(data))
      .catch(() => setFeatures(null));
  }, []);

  if (!features || features.narration_enabled) return null;

  return (
    <Card className="border-amber-500/30 bg-amber-500/5">
      <p className="text-sm font-semibold text-ribet-text">AI analysis is not fully enabled</p>
      <p className="mt-2 text-sm text-ribet-muted">
        Ribet Narration defaults to on, but the API needs an OpenAI key to generate
        management-grade narrative and chat answers. Set{" "}
        <code className="text-xs">OPENAI_API_KEY</code> on the API service and ensure{" "}
        <code className="text-xs">RIBET_NARRATION=on</code> (now the default).
      </p>
      {!features.openai_configured && (
        <p className="mt-2 text-xs text-ribet-muted">
          Until then, reports use verified deterministic insights only.
        </p>
      )}
    </Card>
  );
}
