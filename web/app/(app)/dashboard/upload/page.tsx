import { SectorUploadFlow } from "@/features/upload/SectorUploadFlow";

export default function UploadPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-ribet-text md:text-3xl">
          Upload data
        </h1>
        <p className="mt-1 text-sm text-ribet-muted">
          Add ERP exports to refresh your operational health report.
        </p>
      </div>
      <SectorUploadFlow variant="in-app" />
    </div>
  );
}
