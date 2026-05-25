"use client";

import { useCallback, useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";

export default function SettingsPage() {
  const [recipients, setRecipients] = useState<string[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/org/settings")
      .then((r) => r.json())
      .then((data: { email_recipients?: string[] }) => {
        setRecipients(data.email_recipients ?? []);
      })
      .finally(() => setLoading(false));
  }, []);

  const save = useCallback(async () => {
    setSaving(true);
    setMessage(null);
    const res = await fetch("/api/org/settings", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email_recipients: recipients }),
    });
    setSaving(false);
    if (res.ok) {
      setMessage("Saved.");
    } else {
      setMessage("Could not save settings.");
    }
  }, [recipients]);

  const addEmail = () => {
    const email = input.trim();
    if (!email || !email.includes("@")) return;
    if (!recipients.includes(email)) {
      setRecipients((prev) => [...prev, email]);
    }
    setInput("");
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-ribet-text">Settings</h1>
        <p className="mt-1 text-sm text-ribet-muted">
          Configure who receives weekly operational briefs.
        </p>
      </div>

      <Card>
        {loading ? (
          <p className="text-sm text-ribet-muted">Loading…</p>
        ) : (
          <>
            <label className="text-sm font-medium text-ribet-text">
              Email recipients
            </label>
            <div className="mt-3 flex flex-wrap gap-2">
              {recipients.map((email) => (
                <span
                  key={email}
                  className="inline-flex items-center gap-2 rounded-full border border-ribet-border bg-ribet-card px-3 py-1 text-sm"
                >
                  {email}
                  <button
                    type="button"
                    className="text-ribet-muted hover:text-ribet-text"
                    onClick={() =>
                      setRecipients((prev) => prev.filter((e) => e !== email))
                    }
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <input
                type="email"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="controller@company.com"
                className="min-w-[240px] flex-1 rounded-lg border border-ribet-border bg-ribet-bg px-3 py-2 text-sm text-ribet-text"
              />
              <button
                type="button"
                onClick={addEmail}
                className="rounded-full border border-ribet-border px-4 py-2 text-sm font-medium text-ribet-text hover:bg-ribet-card"
              >
                Add
              </button>
            </div>
            <button
              type="button"
              disabled={saving}
              onClick={save}
              className="mt-6 rounded-full bg-ribet-green px-5 py-2.5 text-sm font-medium text-ribet-text hover:opacity-90 disabled:opacity-50"
            >
              {saving ? "Saving…" : "Save settings"}
            </button>
            {message && (
              <p className="mt-3 text-sm text-ribet-muted">{message}</p>
            )}
          </>
        )}
      </Card>
    </div>
  );
}
