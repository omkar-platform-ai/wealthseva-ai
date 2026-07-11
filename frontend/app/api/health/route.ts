// Health-poll carve-out. The catch-all proxy maps `/api/<x>` → `${FURL}/api/<x>`,
// but the backend health probe lives at the FURL ROOT `/health`, so it needs a
// dedicated handler. A static segment wins over the `[...path]` catch-all in the
// same directory. No secret needed — `/health` is exempt on the backend.
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const FURL = process.env.BACKEND_FURL_URL;

export async function GET() {
  if (!FURL) {
    return new Response(JSON.stringify({ status: 'error', code: 'NO_BACKEND' }), {
      status: 500,
      headers: { 'content-type': 'application/json' },
    });
  }
  const upstream = await fetch(`${FURL}/health`);
  return new Response(upstream.body, {
    status: upstream.status,
    headers: { 'content-type': upstream.headers.get('content-type') ?? 'application/json' },
  });
}
