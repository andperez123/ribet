export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-ribet-bg">
      <header className="border-b border-ribet-border bg-ribet-card">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <span className="text-sm font-semibold text-ribet-text">Ribet Admin</span>
          <a href="/dashboard" className="text-sm text-ribet-muted hover:text-ribet-text">
            Back to app
          </a>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
    </div>
  );
}
