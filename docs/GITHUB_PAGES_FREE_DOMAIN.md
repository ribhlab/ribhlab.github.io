# RibhLab — Free GitHub Pages domain (account root)

**Chosen free address:** `https://univcours.github.io/`

This is a GitHub Pages **user-site address**, not a privately registered domain. It costs 0 USD with GitHub Pages public hosting. **It is not yet active for RibhLab** until the `univcours/univcours.github.io` repository is actually created and its Pages settings enabled. Existing project site is retained at `https://univcours.github.io/ribhlab-site/ar/`.

## Finish the account-root setup

1. In GitHub, signed in to the **univcours** account, open [Import repository](https://github.com/new/import).
2. Source repository: `https://github.com/univcours/ribhlab-site.git`.
3. Owner: `univcours`; repository name: **`univcours.github.io`**; visibility **Public**. Finish import. This creates a separate copy; do not rename or delete `ribhlab-site`.
4. New repo → **Settings → Pages → Build and deployment → Source: GitHub Actions**.
5. New repo → **Actions** → enable workflows if GitHub prompts. Run the **Publish RibhLab to GitHub Pages** workflow on branch `main`, or trigger a new push.
6. Open `https://univcours.github.io/ar/`, `/en/`, `/fr/`, `/sitemap.xml` and `/robots.txt`. Confirm links/assets point to **root** paths such as `/assets/` rather than `/ribhlab-site/assets/`.
7. GitHub Actions auto-detects `univcours/univcours.github.io` and builds for `https://univcours.github.io`. Do **not** configure `RIBHLAB_SITE_URL` to the old project path in the new repo.
8. Once verified, add `univcours.github.io` (without `https://` or `/ar/`) under **AdSense → Sites → New site**. GitHub.io is on the Public Suffix List; Google AdSense's 2023 site-management policy allows subdomains on Public Suffix List platforms to be submitted, **but Google approval and acceptance of any specific site are not guaranteed**.
9. For AdSense site ownership, use the authentic account's `ca-pub-...` ID in **Settings → Secrets and variables → Actions → Variables → RIBHLAB_ADSENSE_PUBLISHER_ID**. The build can output verification metadata and ads.txt. Keep `RIBHLAB_ENABLE_ADSENSE=false` until actual site approval, and implement a compliant consent platform before loading personalized ads where required.
10. For Search Console, choose URL-prefix `https://univcours.github.io/`; verify using a real Google verification meta token through `RIBHLAB_GOOGLE_SITE_VERIFICATION` as documented in `docs/DOMAIN_ADSENSE_ACTIVATION.md`. Submit `https://univcours.github.io/sitemap.xml`.

**Important:** The GitHub connector used here can edit the existing repository but cannot create a new repository or change its Pages account-level setting. The owner must finish steps 1–5 in their own GitHub session. Do not claim the new domain is live before a successful deploy.

## Official references
- https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site
- https://support.google.com/adsense/answer/12170421
- https://support.google.com/adsense/answer/9724
