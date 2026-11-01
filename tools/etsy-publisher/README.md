# RibhLab Etsy Publisher · Seller API integration

**Purpose:** operate a single approved Etsy seller shop, create printable wall art / instant digital downloads, upload listing previews and up to five downloadable files, and optionally activate listings. Etsy API v3, PKCE OAuth2, draft-first safety, and basic duplicate protection.

**Current deployment:** source files only in GitHub under `ribhlab/ribhlab.github.io/tools/etsy-publisher/`. The repository is **PUBLIC**. Never commit product files (original artwork, saleable PDFs, images), OAuth callback URLs with `code`, API key/secret, or refresh tokens here. The workflow only runs manually and cannot publish until you move the assets to a private repository and configure the four Etsy secrets.

## Official docs
- https://developers.etsy.com/documentation/essentials/oauth2/
- https://developers.etsy.com/documentation/tutorials/listings/
- https://developers.etsy.com/documentation/reference

## Setup on your trusted computer / private repository

```bash
cd tools/etsy-publisher  # after checking out the RibhLab repository
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
# Edit .env locally — DO NOT publish it.
python -m etsy_publisher auth-start
# Open the Etsy approval link privately. Copy the complete callback URL back into your local terminal, never into ChatGPT.
python -m etsy_publisher auth-finish
```

Use the registered redirect `https://ribhlab.github.io/ar/etsy-oauth-callback.html` in `.env` as `ETSY_REDIRECT_URI`. On successful OAuth, `.state/oauth_tokens.json` contains a refresh token and usually your numeric shop ID. Keep that file private, not in GitHub. Add four secrets **inside a separate private GitHub repository**: `ETSY_KEYSTRING`, `ETSY_SHARED_SECRET`, `ETSY_SHOP_ID`, `ETSY_REFRESH_TOKEN`.

## Product folder and publishing

Create one folder per digital product under `products/<slug>/` with:

```text
products/my-wall-art/
  listing.json
  images/preview-1.jpg
  files/my-wall-art.pdf
```

`listing.json` must contain title, description, price (shop currency), verified Etsy `taxonomy_id`, 1–20 images (JPG/PNG/GIF) and 1–5 digital files (each under 20 MiB), optional tags (max 13, 20 chars each). `type` must be `download`. A sample manifest is in `examples/sample-planner/listing.json`; its taxonomy ID is placeholder, **not verified** and the demo has no actual digital files, so do not publish it as-is.

```bash
python -m etsy_publisher validate --product products/my-wall-art
python -m etsy_publisher publish --product products/my-wall-art
# after visually checking the draft in Etsy, and if you accept Etsy listing fees:
python -m etsy_publisher publish --product products/my-wall-art --activate
```

The first call creates a draft then uploads images/files. The second activates the same listing ID, tracked in `.state/registry.json`. Publishing creates normal Etsy listing fees (if applicable); this project does not remove Etsy fees. The registry is not a transactional guarantee: a crash between Etsy creating a draft and writing its ID can still require manual deduplication inside Etsy before retrying.

You can also run `python scripts/create_listing.py --help` to create validated metadata with the files you prepared.

## GitHub Actions (after moving to a private repository)

A template is at `.github/workflows/etsy-publish.yml`. Put it at the root `.github/workflows/` in the private repository; if the publisher is at repository root, adjust `tools/etsy-publisher` prefixes in that workflow. Run Actions → Etsy Publisher → Run workflow → slug → `publish_live=false`. Confirm draft first; set true only after reviewing. It is **not an automatic ChatGPT integration** until the repository is linked and can be operated through a tool with write/run permissions.

## Validation

```bash
python -m pytest -q
```

## Boundaries

This repository contains working code, but at this moment **Etsy OAuth is not yet granted** to the running publisher and it cannot upload/publish until you finish seller consent and configure credentials. The Etsy connector visible in ChatGPT is buyer-side, and cannot by itself manage seller listings. Etsy API policies, seller verification, listing restrictions and fees still apply.
