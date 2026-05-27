import Link from "next/link";
import { SignIn } from "@clerk/nextjs";
import { Logo } from "@/components/ui/Logo";

const hasClerk = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

export default function SignInPage() {
  if (!hasClerk) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center px-6">
        <Logo />
        <p className="mt-8 max-w-sm text-center text-lg text-ribet-muted">
          Sign in is not configured yet. Add Clerk keys on the Railway{" "}
          <strong>web</strong> service, then redeploy. Until then, use demo data
          or continue to the dashboard without an account.
        </p>
        <Link
          href="/#upload"
          className="mt-8 rounded-full bg-ribet-green px-6 py-3 text-sm font-medium text-ribet-text hover:opacity-90"
        >
          Try demo data
        </Link>
        <Link
          href="/dashboard"
          className="mt-4 text-sm font-medium text-ribet-muted hover:text-ribet-text"
        >
          Continue to dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6">
      <SignIn
        routing="path"
        path="/sign-in"
        signUpUrl="/sign-up"
        forceRedirectUrl="/dashboard"
      />
    </div>
  );
}
