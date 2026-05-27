import { NextRequest, NextResponse } from "next/server";
import { getFastApiBase, getProxyHeaders } from "@/lib/api/bff";

function isUploadFile(
  value: FormDataEntryValue
): value is File & { name: string } {
  return (
    typeof value === "object" &&
    value !== null &&
    "arrayBuffer" in value &&
    "name" in value &&
    typeof (value as File).name === "string"
  );
}

export async function POST(req: NextRequest) {
  const formData = await req.formData();
  const upstream = new FormData();

  for (const [key, value] of formData.entries()) {
    if (isUploadFile(value)) {
      upstream.append("files", value, value.name);
    } else {
      upstream.append(key, value);
    }
  }

  try {
    const headers = await getProxyHeaders();
    const res = await fetch(`${getFastApiBase()}/v1/ingest/uploads`, {
      method: "POST",
      headers,
      body: upstream,
    });

    const body = await res.text();
    return new NextResponse(body || "{}", {
      status: res.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    const message =
      err instanceof Error ? err.message : "Upload proxy failed";
    console.error("[ingest/uploads] upstream fetch failed:", message);
    return NextResponse.json(
      {
        detail:
          "Could not reach the API. Check FASTAPI_URL on the web service " +
          "(use https://api.ribetlab.com if private networking fails) and " +
          "that FASTAPI_API_KEY matches API_KEY.",
        error: message,
      },
      { status: 502 }
    );
  }
}
