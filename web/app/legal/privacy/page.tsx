import Link from "next/link";
import { Container } from "@/components/ui/Container";

export default function PrivacyPage() {
  return (
    <Container className="py-16">
      <h1 className="text-3xl font-semibold text-ribet-text">Privacy Policy</h1>
      <p className="mt-4 text-sm text-ribet-muted">Last updated: May 2026</p>
      <div className="prose prose-invert mt-8 max-w-3xl space-y-4 text-sm text-ribet-muted">
        <p>
          Ribet processes ERP export files you upload to generate operational
          reports. We store uploads, derived metrics, and report outputs for your
          organization only.
        </p>
        <p>
          We do not sell your data. Third-party processors (hosting, email
          delivery, optional AI narration when enabled) receive only what is
          required to operate the service.
        </p>
        <p>
          Demo organizations are purged automatically after 24 hours. Contact us
          to request deletion of production trial data.
        </p>
      </div>
      <Link href="/" className="mt-8 inline-block text-sm text-ribet-green hover:underline">
        Back to home
      </Link>
    </Container>
  );
}
