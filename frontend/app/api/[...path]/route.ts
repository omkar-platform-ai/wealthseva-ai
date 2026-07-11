import { NextRequest } from 'next/server';

// Amplify SSR catch-all proxy for the 9 non-streaming backend endpoints. The
// browser calls same-origin `/api/...`; this handler injects the server-only
// `x-origin-verify` secret and forwards to the Lambda Function URL. Chat is NOT
// routed here — it hits the FURL directly to preserve token streaming (Amplify
// SSR buffers responses).
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const FURL = process.env.BACKEND_FURL_URL;
const SECRET = process.env.ORIGIN_VERIFY_SECRET;

async function proxy(req: NextRequest, path: string[]) {
  if (!FURL) {
    return new Response(
      JSON.stringify({ error: 'proxy not configured', code: 'NO_BACKEND' }),
      { status: 500, headers: { 'content-type': 'application/json' } },
    );
  }

  const target = `${FURL}/api/${path.join('/')}${req.nextUrl.search}`;

  const headers = new Headers();
  const ct = req.headers.get('content-type');
  if (ct) headers.set('content-type', ct);
  if (SECRET) headers.set('x-origin-verify', SECRET);

  const hasBody = req.method !== 'GET' && req.method !== 'HEAD';

  const upstream = await fetch(target, {
    method: req.method,
    headers,
    body: hasBody ? req.body : undefined,
    // `duplex` is required by undici when streaming a request body through.
    ...(hasBody ? { duplex: 'half' } : {}),
    redirect: 'manual',
  } as RequestInit);

  // Pass through the headers that matter for TTS audio blobs and the CAS PDF.
  const respHeaders = new Headers();
  for (const h of ['content-type', 'content-disposition', 'cache-control']) {
    const v = upstream.headers.get(h);
    if (v) respHeaders.set(h, v);
  }

  return new Response(upstream.body, { status: upstream.status, headers: respHeaders });
}

export async function GET(req: NextRequest, { params }: { params: { path: string[] } }) {
  return proxy(req, params.path);
}

export async function POST(req: NextRequest, { params }: { params: { path: string[] } }) {
  return proxy(req, params.path);
}
