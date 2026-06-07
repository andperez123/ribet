import { proxyDelete, proxyGet } from "@/lib/api/proxy";

type Params = { params: Promise<{ id: string }> };

export async function GET(_req: Request, { params }: Params) {
  const { id } = await params;
  return proxyGet(`/v1/reports/${id}`);
}

export async function DELETE(_req: Request, { params }: Params) {
  const { id } = await params;
  return proxyDelete(`/v1/reports/${id}`);
}
