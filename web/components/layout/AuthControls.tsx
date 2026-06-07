import Link from "next/link";
import { UserMenu } from "@/components/layout/UserMenu";

const clerkEnabled = Boolean(
  process.env.CLERK_SECRET_KEY && process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
);

export function AuthControls() {
  if (clerkEnabled) {
    return <UserMenu />;
  }

  return (
    <Link
      href="/sign-in"
      className="text-sm font-medium text-ribet-muted hover:text-ribet-text"
    >
      Sign in
    </Link>
  );
}
