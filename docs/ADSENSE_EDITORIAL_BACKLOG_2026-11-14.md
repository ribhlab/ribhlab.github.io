# RibhLab — article review backlog (14 November 2026)

**Source:** the actual GitHub Actions source-and-build quality run [43586885921](https://github.com/ribhlab/ribhlab.github.io/actions/runs/43586885921), not a claim about the private Google AdSense rejection decision.

- Total source article records: 95, each localized to AR, EN and FR.
- Currently meeting the internal editorial index gate: 61.
- Held for editorial review: **34** records. Their public pages still load for readers, but use `noindex,follow`, are excluded from `sitemap.xml` and do not load AdSense JS.
- Criteria: 2 distinct attributed HTTPS sources, at least 4 explanatory sections in each language, no empty short placeholder sections, and at least 300 words of substantive explanation in each language. These thresholds are **RibhLab editorial triage rules, not Google AdSense numeric requirements**.
- **Do not fabricate references, word-count filler, first-person testing, or independently-checked translation claims to clear the gate.** Revise articles using real source evidence and unique details before publication.
- One article record represents three localized pages. A translation missing details holds all three locales until they are independently reviewed, preventing inconsistent claims across languages.
- The recipe backlog is separate: **120 × 3 recipe detail pages** using templated cooking-method steps, noindexed pending individually reviewed instructions.

## Items to rewrite and source-check

| Article slug | Current automated reason |
|---|---|
| `adsense-ready-original-site-2026-checklist` | ar: thin explanation (298 words); en: thin explanation (246 words); fr: thin explanation (235 words) |
| `affiliate-marketing-ethically` | fewer than two traceable HTTPS references; ar: thin explanation (184 words); en: thin explanation (158 words); fr: thin explanation (158 words) |
| `ai-agents-business-security-human-checklist` | fewer than two traceable HTTPS references; ar: thin explanation (197 words); en: thin explanation (201 words); fr: thin explanation (213 words) |
| `ai-assistant-apps-2026-iphone-android-comparison` | fewer than two traceable HTTPS references; ar: thin explanation (258 words); en: thin explanation (205 words); fr: thin explanation (201 words) |
| `ai-finance-automation-with-human-controls` | fewer than two traceable HTTPS references; ar: thin explanation (129 words); en: thin explanation (131 words); fr: thin explanation (125 words) |
| `ai-platforms-comparison-practical-2026` | en: thin explanation (280 words); fr: thin explanation (268 words) |
| `ai-prompts-at-work` | fewer than two traceable HTTPS references; ar: thin explanation (163 words); en: thin explanation (153 words); fr: thin explanation (168 words) |
| `ai-video-filmmaking-automation-unity-2026` | en: thin explanation (263 words); fr: thin explanation (245 words) |
| `ai-video-workflow` | fewer than two traceable HTTPS references; ar: thin explanation (161 words); en: thin explanation (146 words); fr: thin explanation (147 words) |
| `automate-excel-ai` | fewer than two traceable HTTPS references; ar: thin explanation (154 words); en: thin explanation (156 words); fr: thin explanation (146 words) |
| `backtest-trading-bots` | fewer than two traceable HTTPS references; ar: thin explanation (168 words); en: thin explanation (158 words); fr: thin explanation (169 words) |
| `best-android-iphone-apps-productivity-2026` | en: thin explanation (290 words); fr: thin explanation (264 words) |
| `best-mobile-budget-expense-apps-2026` | fewer than two traceable HTTPS references; en: thin explanation (201 words); fr: thin explanation (194 words) |
| `classic-italian-tiramisu-without-raw-eggs` | fewer than two traceable HTTPS references |
| `classic-roman-spaghetti-carbonara-recipe` | fewer than two traceable HTTPS references |
| `crypto-new-token-due-diligence` | fewer than two traceable HTTPS references; ar: thin explanation (174 words); en: thin explanation (159 words); fr: thin explanation (154 words) |
| `crypto-perpetual-futures-funding-and-liquidation` | fewer than two traceable HTTPS references; ar: thin explanation (135 words); en: thin explanation (157 words); fr: thin explanation (148 words) |
| `elliott-wave-technical-analysis-course` | fewer than two traceable HTTPS references; ar: thin explanation (257 words); en: thin explanation (219 words); fr: thin explanation (233 words) |
| `football-results-sports-apps-2026-guide` | ar: thin explanation (200 words); en: thin explanation (210 words); fr: thin explanation (175 words) |
| `geopolitics-energy-gold-risk-framework` | fewer than two traceable HTTPS references; ar: thin explanation (160 words); en: thin explanation (145 words); fr: thin explanation (140 words) |
| `gold-october-2026-market-drivers` | ar: thin explanation (213 words); en: thin explanation (201 words); fr: thin explanation (202 words) |
| `grain-and-vegetable-bowl-easy-recipe` | fewer than two traceable HTTPS references; ar: thin explanation (204 words); en: thin explanation (251 words); fr: thin explanation (240 words) |
| `iphone-18-pixel-11-galaxy-s26-buying-guide-2026` | ar: thin explanation (223 words); en: thin explanation (192 words); fr: thin explanation (194 words) |
| `iphone-android-productivity-apps-2026-comparison` | fewer than two traceable HTTPS references; en: thin explanation (232 words); fr: thin explanation (221 words) |
| `macro-calendar-us-europe-japan-china` | ar: thin explanation (165 words); en: thin explanation (170 words); fr: thin explanation (145 words) |
| `mobile-photo-video-editing-apps-2026-guide` | ar: thin explanation (222 words); en: thin explanation (228 words); fr: thin explanation (197 words) |
| `morocco-public-job-application-checklist-2026` | en: thin explanation (203 words); fr: thin explanation (202 words) |
| `online-income-real-business-models` | fewer than two traceable HTTPS references; ar: thin explanation (136 words); en: thin explanation (132 words); fr: thin explanation (129 words) |
| `reverse-engineering-legally-tools-ghidra` | fr: thin explanation (255 words) |
| `sell-digital-products` | fewer than two traceable HTTPS references; ar: thin explanation (159 words); en: thin explanation (153 words); fr: thin explanation (147 words) |
| `start-freelancing` | fewer than two traceable HTTPS references; ar: thin explanation (252 words); en: thin explanation (200 words); fr: thin explanation (201 words) |
| `trading-bot-backtest-spread-slippage-reality-check` | fewer than two traceable HTTPS references; ar: thin explanation (192 words); en: thin explanation (206 words); fr: thin explanation (225 words) |
| `trading-risk-management` | fewer than two traceable HTTPS references; ar: thin explanation (189 words); en: thin explanation (179 words); fr: thin explanation (188 words) |
| `understand-price-charts` | fewer than two traceable HTTPS references; ar: thin explanation (158 words); en: thin explanation (144 words); fr: thin explanation (154 words) |

## Review and reactivation steps

1. Open the relevant `content/articles/<slug>.json` file in a trusted editor.
2. Review actual primary sources and quote them sparingly; verify all figures and dates against the latest official information.
3. Write original AR, EN and FR explanations; avoid translations that change the meaning.
4. Update genuine `sources`, `date` and `updated` values; retain image licensing and proper attribution.
5. Run `npm run build && npm run check`; when ready, `articleIndexReady` automatically re-enables indexing and eligible AdSense loader on the three article pages. Inspect the live result before requesting a new AdSense review.
6. Google Search Console and AdSense dashboards still require separate verification, and no automated quality score proves an AdSense site will be approved.

The actual Google AdSense rejection reason is **not confirmed** by the generic email. The owner must read the site-specific explanation shown in AdSense > Sites and any Policy Center details before claiming the case is resolved.
