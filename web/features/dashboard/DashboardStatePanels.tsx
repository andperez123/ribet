import Link from "next/link";
import {
  DollarSign,
  Factory,
  ClipboardList,
  TrendingUp,
  Loader2,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { RegenerateReportButton } from "@/features/dashboard/RegenerateReportButton";
import { SECTORS } from "@/lib/sectors";
import type { OrgCoverage } from "@/lib/types/coverage";
import type { IngestJobRecord } from "@/lib/types/report";

const SECTOR_ICONS = {
  financials: DollarSign,
  manufacturing: Factory,
  orders: ClipboardList,
  sales: TrendingUp,
} as const;

export function DashboardEmptyHero() {
  return (
    <section className="relative overflow-hidden rounded-3xl border border-ribet-border bg-ribet-card p-8 md:p-12">
      <div className="pointer-events-none absolute inset-0 opacity-30">
        <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-ribet-green/20 blur-3xl" />
        <div className="absolute -bottom-16 -left-16 h-48 w-48 rounded-full bg-ribet-border blur-2xl" />
      </div>
      <div className="relative max-w-2xl">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-ribet-green">
          Your business story starts here
        </p>
        <h2 className="mt-4 text-3xl font-semibold tracking-tight text-ribet-text md:text-4xl">
          Upload ERP exports to see operational health, risks, and what to do next.
        </h2>
        <p className="mt-4 text-sm leading-relaxed text-ribet-muted">
          Ribet turns AR aging, payables, GL detail, and inventory into a living
          dashboard — with charts, narrative, and confidence that grows with every
          upload.
        </p>
        <Link
          href="/dashboard/upload"
          className="mt-6 inline-block rounded-full bg-ribet-green px-6 py-3 text-sm font-medium text-ribet-text hover:opacity-90"
        >
          Upload your first files
        </Link>
      </div>

      <div className="relative mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {SECTORS.map((sector) => {
          const Icon = SECTOR_ICONS[sector.id as keyof typeof SECTOR_ICONS];
          return (
            <Link
              key={sector.id}
              href="/dashboard/upload"
              className="rounded-xl border border-ribet-border/60 bg-ribet-bg/80 p-4 transition hover:border-ribet-green/40 hover:bg-ribet-green/5"
            >
              <Icon className="h-5 w-5 text-ribet-green" />
              <p className="mt-2 text-sm font-medium text-ribet-text">
                {sector.label}
              </p>
              <p className="mt-1 text-xs text-ribet-muted">{sector.description}</p>
            </Link>
          );
        })}
      </div>
    </section>
  );
}

export function DashboardProcessingState({
  jobs,
}: {
  jobs: IngestJobRecord[];
}) {
  const active = jobs.filter(
    (j) => j.status === "pending" || j.status === "processing"
  );

  return (
    <Card className="border-ribet-green/30 bg-ribet-green/5">
      <div className="flex items-start gap-3">
        <Loader2 className="mt-0.5 h-5 w-5 animate-spin text-ribet-green" />
        <div>
          <p className="font-semibold text-ribet-text">Building your story</p>
          <p className="mt-1 text-sm text-ribet-muted">
            {active.length} file{active.length !== 1 ? "s" : ""} processing.
            Charts and narrative will appear when analysis completes.
          </p>
          <ul className="mt-3 space-y-1">
            {active.slice(0, 3).map((j) => (
              <li key={j.id} className="text-sm text-ribet-muted">
                {j.file_name}
                {j.pipeline_stage && (
                  <span className="ml-2 text-xs text-ribet-green">
                    {j.pipeline_stage.replace(/_/g, " ")}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </Card>
  );
}

export function DataNoReportState({
  orgCoverage,
  hasDoneJobs,
}: {
  orgCoverage: OrgCoverage | null;
  hasDoneJobs: boolean;
}) {
  const understood = orgCoverage?.understood ?? [];

  return (
    <Card className="border-ribet-amber/30 bg-amber-500/5">
      <p className="font-semibold text-ribet-text">Data imported — report not active</p>
      <p className="mt-2 text-sm text-ribet-muted">
        Ribet has ingested your exports
        {understood.length > 0 && (
          <> ({understood.map((u) => u.label).join(", ")})</>
        )}
        but there is no current operational report to power the full dashboard.
      </p>
      {hasDoneJobs && (
        <div className="mt-4">
          <RegenerateReportButton label="Generate report from uploaded data" />
        </div>
      )}
      {!hasDoneJobs && (
        <Link
          href="/dashboard/upload"
          className="mt-4 inline-block text-sm font-medium text-ribet-green hover:underline"
        >
          Upload data →
        </Link>
      )}
    </Card>
  );
}
