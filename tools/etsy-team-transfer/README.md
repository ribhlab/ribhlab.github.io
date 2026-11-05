# ProfitLens Team Server 3.6 — Publication state (2026-11-05)

- Seller shop: RibhLabDigital.
- Etsy listing: **4610734598**, **Draft**, **11/11 images uploaded and verified**, price 39.95 USD.
- Buyer file **not yet uploaded**; do **not** activate the listing without it.
- Buyer asset: `ProfitLens_v3_6_Team_With_Server.zip` (SHA256 `5575e7567ba0cf4ffc8755fb76fe3963768914f50c7a0a17f00a86aa573f31eb`).
- Encrypted source: WordPress media ID 69, `profitlens-team-v36-encrypted-transfer.pdf`. **Do not publish plaintext buyer ZIP** in this public repository.
- Encrypted transport SHA256: `728b376379f5bfa33e8633966da2c735047dbfa0bd2cd5c6a175cf638af98b4c`.
- Full original package SHA256: `c19d9e8eee24b2a0640ef8b45d73404796df7062524cd650651497d7d0a38f54`.
- Vercel temporary project `ribhlab-profitlens-team-v36-transfer`, project ID `prj_0ea3OzO0wSHqMiIG35f5o6fGIYLx`, stores encrypted `TEAM_ZIP_KEY_HEX` in production env.
- Current Vercel endpoint rejects authorized GitHub Actions with **403** because it checks the wrong OIDC `sub` claim. Repo's custom GitHub subject is:
  `repo:ribhlab@349031564/ribhlab.github.io@1436299009:ref:refs/heads/main`.
- Corrected secure endpoint source exists at `tools/etsy-team-transfer/api/package.py` and its `requirements.txt`.
- Vercel's Git deployment needs a **GitHub Login Connection** to user account. `create_git_project` failed without it. After authorization, deploy this folder as a protected backend and set `TEAM_ZIP_KEY_HEX` as an encrypted env var on the project. Set `PACKAGE_URL` in `tools/etsy-publisher/scripts/publish_profitlens_team_v36.py` to the confirmed endpoint.
- Rerun workflow `.github/workflows/etsy-profitlens-team-v36-publish.yml` (id-token: write); it reuses the existing draft and only activates after buyer ZIP checksum, attachment, and all 11 images have been verified.
- Last workflow run: `https://github.com/ribhlab/ribhlab.github.io/actions/runs/42097392940` (expected failure 403 at buyer ZIP download).
- All 11 temporary WordPress preview media items 70–80 have been permanently removed after Etsy copied them. They are **already in the Etsy draft**, so repeat runs will not download the temporary preview images.
- On completion: remove temporary WordPress media ID 69 and deactivate/retire temporary Vercel transfer endpoint. Do not log access/refresh tokens or decryption keys.

**Never claim the Team product is Active until Etsy itself confirms state=active and at least one digital ZIP attachment.**
