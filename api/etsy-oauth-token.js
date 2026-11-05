const ALLOWED_ORIGIN = "https://ribhlab.github.io";
const REDIRECT_URI = "https://ribhlab.github.io/ar/etsy-oauth-callback.html";
const TOKEN_ENDPOINT = "https://api.etsy.com/v3/public/oauth/token";

function respond(res, status, payload) {
  return res.status(status).json(payload);
}

export function validateExchange(input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) return false;
  const { client_id, code, code_verifier } = input;
  return typeof client_id === "string" && /^[a-zA-Z0-9_-]{12,128}$/.test(client_id)
    && typeof code === "string" && code.length >= 4 && code.length <= 2048
    && !/[\s\x00-\x1F]/.test(code)
    && typeof code_verifier === "string"
    && /^[A-Za-z0-9._~-]{43,128}$/.test(code_verifier);
}

export default async function handler(req, res) {
  // This intentionally has NO listings endpoints and NO access to Etsy shared secret.
  res.setHeader("Cache-Control", "no-store, private");
  res.setHeader("Pragma", "no-cache");
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.setHeader("Referrer-Policy", "no-referrer");
  res.setHeader("Vary", "Origin");
  const origin = req.headers.origin;
  if (origin !== ALLOWED_ORIGIN) return respond(res, 403, { error: "origin_not_allowed" });
  res.setHeader("Access-Control-Allow-Origin", ALLOWED_ORIGIN);
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "POST") return respond(res, 405, { error: "method_not_allowed" });
  if (Number(req.headers["content-length"] || 0) > 4096) {
    return respond(res, 413, { error: "payload_too_large" });
  }
  const configuredId = process.env.ETSY_ALLOWED_KEYSTRING;
  let body = req.body;
  if (typeof body === "string") {
    try { body = JSON.parse(body); } catch { return respond(res, 400, { error: "invalid_json" }); }
  }
  if (!validateExchange(body)) return respond(res, 400, { error: "invalid_parameters" });
  if (configuredId && body.client_id !== configuredId) {
    return respond(res, 403, { error: "unrecognized_app" });
  }

  const params = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: body.client_id,
    redirect_uri: REDIRECT_URI,
    code: body.code,
    code_verifier: body.code_verifier,
  });
  try {
    const response = await fetch(TOKEN_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: params.toString(),
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(15000),
    });
    if (!response.ok) return respond(res, 400, { error: "etsy_rejected_or_expired_authorization" });
    const data = await response.json();
    if (typeof data.refresh_token !== "string" || !data.refresh_token) {
      return respond(res, 502, { error: "missing_refresh_token" });
    }
    // Return the minimum data to the user's browser, never log or persist tokens.
    const granted_scopes = typeof data.scope === "string"
      ? data.scope.split(/\s+/).filter(scope =>
          ["listings_r","listings_w","shops_r","shops_w"].includes(scope))
      : [];
    return respond(res, 200, {
      refresh_token: data.refresh_token,
      granted_scopes,
      shops_write_granted: granted_scopes.includes("shops_w")
    });
  } catch {
    return respond(res, 502, { error: "etsy_unreachable" });
  }
}
