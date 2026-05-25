import Link from "next/link";
import { Container } from "@/components/ui/Container";

export default function TermsPage() {
  return (
    <Container className="py-16">
      <h1 className="text-3xl font-semibold text-ribet-text">Terms of Service</h1>
      <p className="mt-4 text-sm text-ribet-muted">Last updated: May 2026</p>
      <div className="prose prose-invert mt-8 max-w-3xl space-y-4 text-sm text-ribet-muted">
        <p>
          Ribet provides operational health analysis from ERP exports you upload.
          You retain ownership of your data. By using Ribet you confirm you have
          authority to upload files on behalf of your organization.
        </p>
        <p>
          Reports and narratives are informational only and do not constitute
          accounting, tax, or legal advice. Verify material decisions with your
          finance team and advisors.
        </p>
        <p>
          Trial access may be limited or revoked at any time. Contact us for
          production agreements before relying on Ribet for regulated workflows.
        </p>
      </div>
      <Link href="/" className="mt-8 inline-block text-sm text-ribet-green hover:underline">
        Back to home
      </Link>
    </Container>
  );
}
