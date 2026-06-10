import Link from "next/link";
import { MessageCircleQuestion } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { SourceTraceabilityChip } from "@/features/reports/SourceTraceabilityChip";
import {
  signalSeverityClass,
  signalSeverityPill,
} from "@/lib/dashboard/report-signals";
import type {
  AnalystOutput,
  TopRisk,
  TopSignal,
} from "@/lib/types/report";

function pillClass(pill: "High" | "Medium" | "Low"): string {
  if (pill === "High") return "bg-ribet-risk/15 text-ribet-risk border-ribet-risk/40";
  if (pill === "Medium") return "bg-amber-500/15 text-amber-700 border-amber-500/40";
  return "bg-ribet-card text-ribet-muted border-ribet-border";
}

function RiskCard({ risk }: { risk: TopRisk }) {
  return (
    <Card className="border-l-4 border-l-ribet-risk/60">
      <div className="flex items-start gap-3">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-ribet-risk/10 text-sm font-bold text-ribet-risk">
          {risk.rank}
        </span>
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-ribet-text">{risk.title}</p>
          <p className="mt-1 text-xs font-medium uppercase tracking-wide text-ribet-muted">
            {risk.impact}
          </p>
          {risk.narrative && (
            <p className="mt-3 text-sm leading-relaxed text-ribet-text">
              {risk.narrative}
            </p>
          )}
          {risk.recommended_action && (
            <p className="mt-3 text-sm font-medium text-ribet-green">
              → {risk.recommended_action}
            </p>
          )}
        </div>
      </div>
    </Card>
  );
}

function SignalCard({ signal, featured }: { signal: TopSignal; featured?: boolean }) {
  const pill = signalSeverityPill(signal.severity);
  return (
    <Card
      className={`border-2 ${signalSeverityClass(signal.severity)} ${
        featured ? "lg:col-span-2" : ""
      }`}
    >
      <span
        className={`inline-block rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${pillClass(pill)}`}
      >
        {pill}
      </span>
      <p
        className={`mt-3 font-semibold text-ribet-text ${
          featured ? "text-xl" : "text-base"
        }`}
      >
        {signal.title}
      </p>
      {(signal.why_it_matters || signal.body) && (
        <p className="mt-2 text-sm leading-relaxed text-ribet-muted">
          {signal.why_it_matters ?? signal.body}
        </p>
      )}
      {signal.suggested_action && (
        <p className="mt-3 text-sm font-medium text-ribet-green">
          → {signal.suggested_action}
        </p>
      )}
      <SourceTraceabilityChip
        trace={signal.source_trace}
        sourceLabel={signal.source}
        findingId={signal.finding_id}
        metricKey={signal.metric_label ?? undefined}
        className="mt-4"
      />
    </Card>
  );
}

export function NarrativeStory({
  analystOutput,
  topSignals,
  reportId,
}: {
  analystOutput?: AnalystOutput | null;
  topSignals?: TopSignal[];
  reportId?: string;
}) {
  const summary = analystOutput?.executive_summary ?? [];
  const risks = analystOutput?.top_risks ?? [];
  const questions = analystOutput?.management_questions ?? [];
  const signals = topSignals ?? [];

  if (!summary.length && !risks.length && !questions.length && !signals.length) {
    return null;
  }

  return (
    <section className="space-y-6">
      {summary.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-ribet-text">The story</h2>
          <p className="mt-1 text-sm text-ribet-muted">
            What Ribet sees in your business right now.
          </p>
          <div className="mt-4 space-y-4">
            {summary.map((beat, i) => (
              <div key={i} className="flex gap-4">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-ribet-green/15 text-xs font-bold text-ribet-green">
                  {i + 1}
                </span>
                <p className="pt-0.5 text-sm leading-relaxed text-ribet-text md:text-base">
                  {beat}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {risks.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-ribet-text">Top risks</h3>
          <div className="mt-3 grid gap-4 lg:grid-cols-2">
            {risks.slice(0, 4).map((risk) => (
              <RiskCard key={risk.rank} risk={risk} />
            ))}
          </div>
        </div>
      )}

      {signals.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-ribet-text">Key signals</h3>
          <div className="mt-3 grid gap-4 lg:grid-cols-2">
            {signals.slice(0, 3).map((signal, i) => (
              <SignalCard key={`${signal.title}-${i}`} signal={signal} featured={i === 0} />
            ))}
          </div>
        </div>
      )}

      {questions.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-ribet-text">
            Questions for leadership
          </h3>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {questions.slice(0, 4).map((q, i) => (
              <Card key={i} className="flex gap-3">
                <MessageCircleQuestion className="mt-0.5 h-4 w-4 shrink-0 text-ribet-green" />
                <div>
                  <p className="text-sm font-medium text-ribet-text">
                    {q.question}
                  </p>
                  {q.context && (
                    <p className="mt-1 text-xs leading-relaxed text-ribet-muted">
                      {q.context}
                    </p>
                  )}
                </div>
              </Card>
            ))}
          </div>
          {reportId && (
            <Link
              href={`/dashboard/reports/${reportId}#chat`}
              className="mt-3 inline-block text-sm font-medium text-ribet-green hover:underline"
            >
              Explore in operations chat →
            </Link>
          )}
        </div>
      )}
    </section>
  );
}
