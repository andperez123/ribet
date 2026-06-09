"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Loader2, Send } from "lucide-react";
import { Card } from "@/components/ui/Card";

type ChatResponse = {
  answer: string;
  follow_up_questions?: string[];
  cited_finding_ids?: string[];
  confidence?: string;
  source?: string;
  narration_available?: boolean;
  report_id?: string | null;
};

type Props = {
  reportId?: string;
};

export function OperationsChatPanel({ reportId }: Props) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; text: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const suggestions = useMemo(
    () => [
      "Who should we call on collections this week?",
      "Which vendors are driving AP risk?",
      "What should we upload next to improve analysis?",
    ],
    []
  );

  const ask = useCallback(
    async (text: string) => {
      const q = text.trim();
      if (!q || loading) return;
      setError(null);
      setLoading(true);
      setMessages((prev) => [...prev, { role: "user", text: q }]);
      setQuestion("");
      try {
        const res = await fetch("/api/chat/query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: q, report_id: reportId ?? null }),
        });
        if (!res.ok) throw new Error(await res.text());
        const data = (await res.json()) as ChatResponse;
        setMessages((prev) => [...prev, { role: "assistant", text: data.answer }]);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not get an answer");
      } finally {
        setLoading(false);
      }
    },
    [loading, reportId]
  );

  return (
    <Card>
      <h2 className="text-lg font-semibold text-ribet-text">Ask your operations manager</h2>
      <p className="mt-1 text-sm text-ribet-muted">
        Questions are answered from your verified report data — not generic advice.
      </p>

      {messages.length > 0 && (
        <div className="mt-4 max-h-80 space-y-3 overflow-y-auto rounded-xl border border-ribet-border bg-ribet-bg/40 p-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`text-sm ${
                msg.role === "user" ? "text-ribet-muted" : "text-ribet-text"
              }`}
            >
              <span className="font-medium text-ribet-green">
                {msg.role === "user" ? "You" : "Ribet"}
              </span>
              {": "}
              {msg.text}
            </div>
          ))}
          {loading && (
            <div className="flex items-center gap-2 text-sm text-ribet-muted">
              <Loader2 className="h-4 w-4 animate-spin" />
              Analyzing your data…
            </div>
          )}
        </div>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        {suggestions.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => ask(s)}
            className="rounded-full border border-ribet-border px-3 py-1.5 text-xs text-ribet-muted hover:bg-ribet-card hover:text-ribet-text"
          >
            {s}
          </button>
        ))}
      </div>

      <form
        className="mt-4 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          ask(question);
        }}
      >
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. Why is cash flow at risk this month?"
          className="min-w-0 flex-1 rounded-xl border border-ribet-border bg-ribet-bg px-4 py-2.5 text-sm text-ribet-text placeholder:text-ribet-muted"
          aria-label="Ask a question about your operational data"
        />
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="inline-flex items-center gap-2 rounded-full bg-ribet-green px-4 py-2.5 text-sm font-medium text-ribet-text hover:opacity-90 disabled:opacity-50"
        >
          <Send className="h-4 w-4" />
          Ask
        </button>
      </form>

      {error && (
        <p className="mt-2 text-sm text-ribet-risk" role="alert">
          {error}
        </p>
      )}
    </Card>
  );
}
