# RibhLab — free branded GitHub Pages hostname

**Target:** `https://ribhlab.github.io/` (free GitHub Pages organization-site hostname).

**Status:** Preparations committed to `univcours/ribhlab-site`. The organization `ribhlab` and repository `ribhlab.github.io` have NOT been created/confirmed by this change. Its availability is NOT guaranteed. The current site remains at `https://univcours.github.io/ribhlab-site/ar/`.

## Best path: create a GitHub Free organization rather than rename univcours

1. Sign in as `univcours`, go to profile photo → Settings → Organizations → New organization: https://github.com/settings/organizations
2. Choose **GitHub Free**, set organization name to **ribhlab**, if GitHub confirms it is available, and complete requested verification.
3. Import repository at https://github.com/new/import. Source: `https://github.com/univcours/ribhlab-site.git`. Owner: newly created **ribhlab** organization. Destination repository name: **ribhlab.github.io**. Make repository **Public**. Keep original repo untouched. If GitHub does not offer the organization as an Owner at import time, create the repository under that organization and push/copy the existing project separately; do not put it under univcours expecting the branded domain.
4. In `ribhlab/ribhlab.github.io`, open Settings → Pages → Build and deployment → Source: **GitHub Actions**. Enable Actions if asked.
5. Trigger the `Publish RibhLab to GitHub Pages` workflow on branch main. The workflow in this repository automatically identifies a user/organization Pages repo when its name is `<owner>.github.io` and builds with `SITE_URL=https://<owner>.github.io`. It keeps the original `univcours/ribhlab-site` URL unchanged.
6. Confirm `https://ribhlab.github.io/ar/`, `/en/`, `/fr/`, `/assets/style.css`, `/sitemap.xml` and `/robots.txt`. Do not claim that URL is live before deployment succeeds.
7. Add the URL-prefix property `https://ribhlab.github.io/` to Google Search Console; verify with the genuine meta token using `RIBHLAB_GOOGLE_SITE_VERIFICATION` as an Actions variable or another supported method.
8. In AdSense, use **Sites → New site** with `ribhlab.github.io` (no /ar path). Acceptance depends on the real account, Google platform/domain support and site quality. Use only your real `RIBHLAB_ADSENSE_PUBLISHER_ID` for ownership proof; `RIBHLAB_ENABLE_ADSENSE` remains **false** until actual approval and appropriate consent implementation.

**If `ribhlab` is taken:** Do not claim ownership of `ribhlab.github.io` or invent a redirect. Select another available organization name (and corresponding matching hostname) or use a registered custom domain. Creating a repository `ribhlab.github.io` under `univcours` will **not** produce `ribhlab.github.io`.

Official docs:
- https://docs.github.com/en/organizations/collaborating-with-groups-in-organizations/creating-a-new-organization-from-scratch
- https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site
- https://support.google.com/adsense/answer/9724
