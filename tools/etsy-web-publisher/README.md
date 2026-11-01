# RibhLab Etsy Web Publisher

Browser uploader deployed to `https://ribhlab-etsy-oauth-bridge.vercel.app/` via Vercel serverless functions. Admin login and Etsy OAuth are protected by HttpOnly, AES-GCM encrypted cookies. Uploads store 3 MiB chunks in private Vercel Blob storage, never public GitHub. Draft-first Etsy publishing with tracked listing IDs; live publishing happens only after explicit confirmation.

## Important

Code is public, secrets are NOT. Set Vercel encrypted environment variables `RP_PASSWORD`, `RP_SECRET` and connect a PRIVATE Blob store (`BLOB_READ_WRITE_TOKEN`). Etsy Keystring and Shared Secret are entered only into the HTTPS account connection interface and exchanged server-side; never committed. Registered Etsy redirect URI: `https://ribhlab.github.io/ar/etsy-oauth-callback.html`, which relays `rvp_` state to this web app.

Vercel deployment currently uses inline source rather than Git integration. Updates to this repo **do not automatically redeploy Vercel** until Git integration is configured. Test in preview before production upgrades.

Listing activation can cause Etsy fees. Etsy product content must be original/licensed. Serverless file size limit per file: 20 MiB; private chunk upload: 3 MiB per request.
