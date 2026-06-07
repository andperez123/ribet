import Link from "next/link";

const NAV = [
  { href: "/admin/metrics", label: "Metrics" },
  { href: "/admin/failures", label: "Job failures" },
];

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-ribet-bg">
      <header className="border-b border-ribet-border bg-ribet-card">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div className="flex flex-wrap items-center gap-6">
            <span className="text-sm font-semibold text-ribet-text">
              Ribet Admin
            </span>
            <nav className="flex flex-wrap gap-1">
              {NAV.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="rounded-lg px-3 py-1.5 text-sm text-ribet-muted hover:bg-ribet-border/40 hover:text-ribet-text"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
          <Link
            href="/dashboard"
            className="text-sm text-ribet-muted hover:text-ribet-text"
          >
            Back to app
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
    </div>
  );
}
