# Market Pulse — Real-Photo Source & Attribution Register

Reviewed 27 October 2026. This register documents actual Unsplash photographs used on **externally attributed headline topic cards**. These are NOT screenshots, live quotes, or photographs of the reported events. The original six Market Pulse digest stories already have one different real photograph per report (see `content/market-digests.json`).

## Why headlines are grouped

Google News search RSS currently supplies multiple headlines per topic but **no guaranteed article-image metadata**. Displaying the same category photo repeatedly under each story would look misleading and repetitive. Therefore RibhLab shows **one real, unique, clearly credited photograph per visible topic card** and lists all other headlines from that topic as original-publisher links within the same card. No external headline is presented as a fully authored RibhLab article.

| Topic | Licensed Unsplash image | Photographer | Editorial subject |
|---|---|---|---|
| `crypto` | [Photo](https://unsplash.com/photos/bitcoin-coin-isolated-on-a-black-background-cdV4BY5hTdU) | Valentin | Physical Bitcoin token on a black background; illustrative, not a live quote |
| `new_tokens` | [Photo](https://unsplash.com/photos/a-person-holding-a-coin-in-front-of-a-computer-qF1XTSiGpqM) | Art Rachen | Person holding an Ethereum token in front of a computer, illustrative crypto photo |
| `gold` | [Photo](https://unsplash.com/photos/several-gold-bars-stacked-on-a-dark-surface-tBTv7T9WFmM) | Scottsdale Mint | Real physical gold bars on a dark surface, illustrative gold-market photo |
| `us_macro` | [Photo](https://unsplash.com/photos/us-dollar-bills-and-a-calculator-on-blue-background-y1vS_aBALGc) | Sasun Bughdaryan | US dollar bills and a calculator illustrating economic and inflation news |
| `europe` | [Photo](https://unsplash.com/photos/a-close-up-of-assorted-euro-banknotes-ORy-C_iPZXo) | Maxim Hopman | Assorted euro banknotes illustrating the eurozone economy |
| `japan` | [Photo](https://unsplash.com/photos/tokyo-tower-in-tokyo-skyline-tIALnpOYB8g) | Farlley Gonçalves | Tokyo skyline with Tokyo Tower, general Japan context, not the Bank of Japan |
| `china` | [Photo](https://unsplash.com/photos/cargo-ships-and-cranes-at-a-busy-port-4VVkMCgtu70) | Abdalla Emiir | Cargo ships and cranes illustrating global trade, not a specifically identified Chinese port |
| `geopolitics` | [Photo](https://unsplash.com/photos/an-oil-refinery-is-silhouetted-against-a-hazy-sky-rg8gAwGFXE8) | Buddy AN | Oil refinery photographed in Japan, illustrative energy context rather than the reported event |
| `ai_future` | [Photo](https://unsplash.com/photos/server-racks-in-data-center-klWUhr-wPJ8) | imgix | Real data-centre server racks, illustrating AI infrastructure |
| `digital_income` | [Photo](https://unsplash.com/photos/man-working-on-a-laptop-at-a-desk-mj8TyyqVOCA) | Vitaly Gariev | Entrepreneur using a laptop at a home-office desk, illustrating online work |

## Editorial image policy

- All topic photos were located on an Unsplash page explicitly marked **Free to use under the Unsplash License**. Photographer and original source are displayed to readers; license reference: https://unsplash.com/license.
- `photoId` must be globally unique across the ten topic-card photos, all original Market Pulse digests, and all normal blog articles. CI fails on duplicates or missing alt text/credit.
- Illustrative photos do not depict an actual CPI release, ECB/FOMC decision, token listing or specific current geopolitical event. The images for China and geopolitics are intentionally generic world-trade and refinery scenes, not claims of actual event locations.
- Every outside headline retains its title, named publisher, date and source URL; it is grouped visually without copy-pasting copyrighted articles or inventing a summary.
- The source items may be stale if the RSS update fails. No real-time accuracy is claimed; keep the feed retrieval timestamp visible.
- Never silently replace photos with generated artwork or reuse the same photo in multiple cards. New topics require a newly licensed, documented photograph.
