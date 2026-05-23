import Link from "next/link";

type EmptyStateProps = {
  title: string;
  description?: string;
  actionLabel?: string;
  actionHref?: string;
};

export function EmptyState({
  title,
  description,
  actionLabel,
  actionHref,
}: EmptyStateProps) {
  return (
    <div className="rounded-2xl border border-dashed border-ribet-border bg-ribet-card px-6 py-12 text-center">
      <p className="text-lg font-medium text-ribet-text">{title}</p>
      {description && (
        <p className="mt-2 text-sm text-ribet-muted">{description}</p>
      )}
      {actionLabel && actionHref && (
        <Link
          href={actionHref}
          className="mt-6 inline-block rounded-full bg-ribet-green px-5 py-2.5 text-sm font-medium text-ribet-text hover:opacity-90"
        >
          {actionLabel}
        </Link>
      )}
    </div>
  );
}
