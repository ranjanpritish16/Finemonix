import { NextResponse } from "next/server";

export async function GET() {
  try {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const res = await fetch(`${backendUrl}/health`, {
      cache: "no-store",
    });

    if (!res.ok) {
      return NextResponse.json(
        { status: "error", message: `Backend returned status ${res.status}` },
        { status: 502 }
      );
    }

    const data = await res.json();
    return NextResponse.json({
      status: "ok",
      backend: data,
    });
  } catch (error: any) {
    return NextResponse.json(
      { status: "error", message: error.message || "Failed to reach backend" },
      { status: 500 }
    );
  }
}
