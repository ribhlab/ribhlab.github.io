# RibhLab Etsy Browser OAuth Bridge

Why: GitHub Pages is static. Browser POST to `api.etsy.com/v3/public/oauth/token` can fail due to Etsy's CORS policy. A real server-side token exchange fixes that. Never use a public third-party CORS proxy for OAuth.

## Architecture

- Authorization page: `https://ribhlab.github.io/ar/etsy-connect.html`.
- Exact registered callback URL: `https://ribhlab.github.io/ar/etsy-oauth-callback.html`.
- Backend serverless function: `api/etsy-oauth-token.js` (Vercel Node.js endpoint).
- PKCE `verifier` and `state` are generated in-browser and kept in `sessionStorage` for the same browser tab.
- On callback, verify state, remove authorization code from browser address bar, and exchange through the serverless endpoint.
- The server verifies Origin, validates PKCE arguments, POSTs to Etsy over HTTPS, and returns only the refresh token.
- The user copies the refresh token into **GitHub Actions repository secret** `ETSY_REFRESH_TOKEN` (not into ChatGPT).
- Etsy Keystring and Shared Secret remain in existing GitHub Actions secrets; this bridge does NOT read them.
- No Etsy token is added to GitHub commits or frontend assets.

## Deployment requirement

This file on GitHub **is not a running server**. Deploy this repository to a supported serverless host such as Vercel. The deployment provides `https://YOUR-PROJECT.vercel.app/api/etsy-oauth-token`. Optionally set deployment env variable `ETSY_ALLOWED_KEYSTRING` to restrict use to one Etsy app.

Once deployed, configure the trusted endpoint in `public/ar/etsy-connect.html` and `public/ar/etsy-oauth-callback.html` via the constant `BRIDGE_ORIGIN` (or use its hostname setup field when appropriate). Never enter a random third-party URL that could receive your Etsy authorization code.

**Do not attempt another Etsy approval** until the backend endpoint is live and confirmed. Earlier codes are typically single-use/short-lived.

After exchanging the code, the Etsy publisher still needs `ETSY_SHOP_ID` in GitHub Actions secrets. The product assets must be in a private repository before upload; the RibhLab repository is public.

## Tests

`node --test tools/etsy-web-bridge/tests/oauth.test.mjs`

These are mocked tests. They do not demonstrate that the production OAuth grant works until a live serverless deployment and Etsy account consent complete.
