import Link from "next/link";
import { Loader2 } from "lucide-react";

type AsyncWorkflowBannerProps = {
  title: string;
  body: readonly string[];
  showSpinner?: boolean;
  dashboardHref?: string;
  className?: string;
};

export function AsyncWorkflowBanner({
  title,
  body,
  showSpinner = true,
  dashboardHref = "/dashboard",
  className = "",
}: AsyncWorkflowBannerProps) {
  return (
    <div
      className={`rounded-xl border border-ribet-green/30 bg-ribet-green/10 px-5 py-4 text-sm text-ribet-text ${className}`}
      role="status"
      aria-live="polite"
    >
      <div className="flex items-start gap-3">
        {showSpinner && (
          <Loader2
            className="mt-0.5 h-5 w-5 shrink-0 animate-spin text-ribet-green"
            aria-hidden
          />
        )}
        <div className="space-y-2">
          <p className="font-semibold text-ribet-text">{title}</p>
          {body.map((line) => (
            <p key={line} className="text-ribet-muted">
              {line}
            </p>
          ))}
          <Link
            href={dashboardHref}
            className="inline-block font-medium text-ribet-green hover:underline"
          >
            Open dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
