import Link from "next/link";
import { Logo } from "@/components/ui/Logo";

const nav = [
  { href: "/dashboard", label: "Overview" },
  { href: "/#upload", label: "Upload files" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-rivet-bg">
      <header className="sticky top-0 z-50 border-b border-rivet-border/60 bg-rivet-bg/90 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 md:h-20 md:px-10">
          <Logo href="/dashboard" />
          <nav className="hidden items-center gap-6 sm:flex">
            {nav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="text-sm font-medium text-rivet-muted hover:text-rivet-text"
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <Link
            href="/"
            className="text-sm font-medium text-rivet-muted hover:text-rivet-text"
          >
            Back to site
          </Link>
        </div>
      </header>

      <div className="mx-auto flex max-w-7xl gap-8 px-6 py-8 md:px-10">
        <aside className="hidden w-48 shrink-0 md:block">
          <nav className="sticky top-28 space-y-1">
            {nav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="block rounded-lg px-3 py-2 text-sm font-medium text-rivet-muted hover:bg-rivet-card hover:text-rivet-text"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </aside>
        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
