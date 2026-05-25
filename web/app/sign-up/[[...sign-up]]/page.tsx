import Link from "next/link";
import { SignUp } from "@clerk/nextjs";
import { Logo } from "@/components/ui/Logo";

const hasClerk = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

export default function SignUpPage() {
  if (!hasClerk) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center px-6">
        <Logo />
        <p className="mt-8 max-w-sm text-center text-lg text-ribet-muted">
          Sign up is not configured yet. Try demo data to explore Ribet.
        </p>
        <Link
          href="/#upload"
          className="mt-8 rounded-full bg-ribet-green px-6 py-3 text-sm font-medium text-ribet-text hover:opacity-90"
        >
          Try demo data
        </Link>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6">
      <SignUp
        routing="path"
        path="/sign-up"
        signInUrl="/sign-in"
        forceRedirectUrl="/dashboard"
      />
    </div>
  );
}
