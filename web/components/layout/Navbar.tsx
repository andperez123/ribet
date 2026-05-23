import { getDemoUrl, getSignInUrl } from "@/lib/config/env";
import { nav } from "@/lib/content/landing";
import { Button } from "@/components/ui/Button";
import { Container } from "@/components/ui/Container";
import { Logo } from "@/components/ui/Logo";

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-rivet-border/60 bg-rivet-bg/90 backdrop-blur-md">
      <Container>
        <nav className="flex h-16 items-center justify-between md:h-20">
          <Logo />
          <div className="flex items-center gap-4 md:gap-8">
            <a
              href="/dashboard"
              className="hidden text-sm font-medium text-rivet-text hover:opacity-70 sm:block"
            >
              Dashboard
            </a>
            <a
              href={getSignInUrl()}
              className="hidden text-sm font-medium text-rivet-text hover:opacity-70 sm:block"
            >
              {nav.signIn}
            </a>
            <Button href={getDemoUrl()} className="!px-5 !py-2.5 text-sm">
              {nav.bookDemo}
            </Button>
          </div>
        </nav>
      </Container>
    </header>
  );
}
