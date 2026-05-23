import Link from "next/link";
import { notFound } from "next/navigation";
import { Badge } from "@/components/ui/Badge";
import { HealthScoreHero } from "@/features/dashboard/HealthScoreHero";
import { ReportSections } from "@/features/dashboard/ReportSections";
import { WeeklyBriefPanel } from "@/features/dashboard/WeeklyBriefPanel";
import { formatDate, healthStatusColor } from "@/lib/dashboard/utils";
import { serverData } from "@/lib/api/server-data";

type Props = { params: Promise<{ id: string }> };

export default async function ReportPage({ params }: Props) {
  const { id } = await params;
  const [report, brief, healthScore] = await Promise.all([
    serverData.report(id),
    serverData.weeklyBrief(),
    serverData.healthScore(),
  ]);

  if (!report) notFound();

  return (
    <div className="space-y-8">
      <div>
        <Link
          href="/dashboard"
          className="text-sm font-medium text-ribet-muted hover:text-ribet-text"
        >
          ← Dashboard
        </Link>
        <h1 className="mt-4 text-2xl font-semibold tracking-tight text-ribet-text md:text-3xl">
          Operational Health Report
        </h1>
        <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-ribet-muted">
          <span>Generated {formatDate(report.generated_at)}</span>
          <Badge variant="default">{report.health_score} / 100</Badge>
          <span className={healthStatusColor(report.health_status)}>
            {report.health_status}
          </span>
        </div>
      </div>

      {healthScore && <HealthScoreHero score={healthScore} />}

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <ReportSections report={report} />
        </div>
        <div>{brief && <WeeklyBriefPanel brief={brief} />}</div>
      </div>
    </div>
  );
}
