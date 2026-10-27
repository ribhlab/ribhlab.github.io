# RibhLab — Real public visitor statistics by country

The RibhLab public audience page is published at:
- https://ribhlab.github.io/ar/audience/
- https://ribhlab.github.io/fr/audience/
- https://ribhlab.github.io/en/audience/

**Current status:** site structure is ready, but no tracking account/website ID or public share URL has been supplied. The page truthfully shows "not connected" rather than made-up visitor totals.

## Connect actual analytics (Umami Cloud Hobby, free plan)

1. Sign up at https://cloud.umami.is/ and choose **Hobby ($0)**. At the time of implementation it supports one website and up to 100,000 events a month (confirm live pricing at https://umami.is/pricing).
2. In Umami → Websites → Add website:
   - Name: RibhLab
   - Domain: ribhlab.github.io
3. Copy the actual **Website ID** (UUID) from Umami's tracking settings.
4. Under GitHub repository **ribhlab/ribhlab.github.io** → Settings → Secrets and variables → Actions → Variables, create:
   - `RIBHLAB_UMAMI_WEBSITE_ID` = real Umami website UUID
5. Umami → Websites → Edit → Share URL → Add Share URL → enable **Traffic**; or create a public board with the **world map/country** visualization. Copy the generated public URL.
6. Add second GitHub Actions variable:
   - `RIBHLAB_UMAMI_SHARE_URL` = full `https://cloud.umami.is/share/...` link.
7. Publish by **Actions → Publish RibhLab to GitHub Pages → Run workflow** (branch main). The build inserts the official cookieless Umami tracking snippet only when the real valid UUID is present, and embeds the public dashboard only when an actual well-formed HTTPS share URL is present.
8. Open the public audience page; verify it includes genuine visitors and country breakdown. Do not confuse pageviews with distinct visitors, and note privacy tools may block tracking.

No API key or personal login is embedded in the static site. Never place Umami account passwords/tokens in the repository, the frontend or a public share URL. The linked dashboard is intentionally read-only and public.

References:
- https://docs.umami.is/docs/add-a-website
- https://docs.umami.is/docs/collect-data
- https://docs.umami.is/docs/guides/create-a-public-dashboard
- https://umami.is/pricing

## Country privacy
RibhLab shares aggregate country statistics only, never raw visitor addresses or identities. The tracker respects Do Not Track, and the multilingual privacy policy updates automatically when real Umami tracking is activated.
