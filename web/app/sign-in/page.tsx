import Link from "next/link";
import { Logo } from "@/components/ui/Logo";

export default function SignInPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6">
      <Logo />
      <p className="mt-8 max-w-sm text-center text-lg text-rivet-muted">
        Sign in is coming soon. For development, continue to the dashboard with
        your demo organization.
      </p>
      <Link
        href="/dashboard"
        className="mt-8 rounded-full bg-rivet-green px-6 py-3 text-sm font-medium text-rivet-text hover:opacity-90"
      >
        Continue to dashboard
      </Link>
      <Link
        href="/"
        className="mt-4 text-sm font-medium text-rivet-muted hover:text-rivet-text"
      >
        Back to home
      </Link>
    </div>
  );
}
