import { proxyGet } from "@/lib/api/proxy";

type Props = { params: Promise<{ id: string }> };

export async function GET(_request: Request, { params }: Props) {
  const { id } = await params;
  return proxyGet(`/v1/reports/${id}/setup`);
}
