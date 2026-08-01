import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { query, max_depth = 3, branching_factor = 3 } = body;

    // Connect to Python backend MAS-8ENGINE
    const backendRes = await fetch('http://localhost:8000/api/v1/solve', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, max_depth, branching_factor }),
    });

    if (!backendRes.ok) {
      throw new Error(`Backend error: ${backendRes.statusText}`);
    }

    const data = await backendRes.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('API proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to communicate with MAS-8ENGINE backend' },
      { status: 500 }
    );
  }
}
