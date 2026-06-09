import Link from "next/link";
import { AuthControls } from "@/components/layout/AuthControls";
import { DemoBanner } from "@/components/layout/DemoBanner";
import { MobileNav } from "@/components/layout/MobileNav";
import { Logo } from "@/components/ui/Logo";

const nav = [
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/reports", label: "Reports" },
  { href: "/dashboard/upload", label: "Upload" },
  { href: "/dashboard/settings", label: "Settings" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-ribet-bg">
      <DemoBanner />
      <header className="sticky top-0 z-50 border-b border-ribet-border/60 bg-ribet-bg/90 backdrop-blur-md">
        <div className="relative mx-auto flex h-16 max-w-7xl items-center justify-between px-6 md:h-20 md:px-10">
          <div className="flex items-center gap-3">
            <MobileNav />
            <Logo href="/dashboard" />
          </div>
          <nav className="hidden items-center gap-6 sm:flex">
            {nav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="text-sm font-medium text-ribet-muted hover:text-ribet-text"
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="flex items-center gap-4">
            <AuthControls />
            <Link
              href="/"
              className="hidden text-sm font-medium text-ribet-muted hover:text-ribet-text sm:inline"
            >
              Back to site
            </Link>
          </div>
        </div>
      </header>

      <div className="mx-auto flex max-w-7xl gap-8 px-6 py-8 md:px-10">
        <aside className="hidden w-48 shrink-0 md:block">
          <nav className="sticky top-28 space-y-1">
            {nav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="block rounded-lg px-3 py-2 text-sm font-medium text-ribet-muted hover:bg-ribet-card hover:text-ribet-text"
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
