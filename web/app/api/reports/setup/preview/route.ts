import { proxyGet } from "@/lib/api/proxy";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const params = new URLSearchParams();
  for (const id of searchParams.getAll("job_ids")) {
    params.append("job_ids", id);
  }
  return proxyGet("/v1/reports/setup/preview", params);
}
