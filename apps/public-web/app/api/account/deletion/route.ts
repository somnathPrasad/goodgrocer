import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  const contentLength = Number(request.headers.get("content-length") || "0");
  if (contentLength > 12000) {
    return NextResponse.json(
      { error: { message: "The deletion request is too large." } },
      { status: 413 },
    );
  }
  const body = (await request.json().catch(() => null)) as {
    id_token?: unknown;
  } | null;
  if (
    typeof body?.id_token !== "string" ||
    !body.id_token ||
    body.id_token.length > 10000
  ) {
    return NextResponse.json(
      { error: { message: "Verify your Google account before continuing." } },
      { status: 422 },
    );
  }
  try {
    const response = await fetch(
      `${process.env.API_URL || "http://127.0.0.1:8000"}/api/v1/account/deletion`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_token: body.id_token }),
        cache: "no-store",
      },
    );
    if (response.ok) return new NextResponse(null, { status: 204 });
    const upstream = (await response.json().catch(() => null)) as {
      error?: { message?: string };
    } | null;
    return NextResponse.json(
      {
        error: {
          message:
            upstream?.error?.message || "Deletion could not be completed.",
        },
      },
      { status: response.status },
    );
  } catch {
    return NextResponse.json(
      {
        error: {
          message: "Goodgrocer is unavailable. Please try again shortly.",
        },
      },
      { status: 503 },
    );
  }
}
