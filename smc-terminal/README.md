# RibhLab SMC Terminal

Free, browser-based, real-time **cryptocurrency technical analysis and Smart Money Concepts (SMC)** terminal.

**Live site:** deployment on Vercel, with this directory as the source of truth.
**Repository directory:** `smc-terminal/` in `ribhlab/ribhlab.github.io`.

## What works

- Candlestick chart with pan, zoom, crosshair and a mobile responsive workspace, powered by **TradingView Lightweight Charts™ v5** (the open-source charting library, not TradingView Advanced Charts).
- Binance Spot **public market data**: 18 USDT pairs; historical OHLCV (REST) and live WebSocket candle updates with 60-second REST polling fallback.
- 5m, 15m, 1h, 4h, and 1d charts, plus a higher-timeframe read.
- **Smart Money heuristics** computed locally from *closed candles*:
  - Confirmed swing high/low pivots, with three candles on either side.
  - BOS vs CHoCH on closing-price breaks of the last confirmed structure pivot.
  - Three-candle Fair Value Gaps (FVG) and untouched / partially mitigated gaps.
  - Candidate order blocks (last opposite candle before structure breaks, invalidated by closes beyond far boundary).
  - Liquidity sweeps (wick-through / close back inside), equal swing highs/lows.
  - Premium/discount relative to the most recent 110 closed candles.
  - Higher-timeframe market structure, EMA alignment and an **explanatory confluence count**, not a probability forecast.
- EMA 20/50/200, RSI 14, ATR 14, volume, colored overlays and structure markers.
- Horizontal levels, trend lines, Fibonacci price levels and clear drawings.
- Dark/light theme, starred market pairs and deep links; persistent preferences stored in browser localStorage.
- Export current OHLCV to CSV. No login, no wallet, no secrets, no trade execution or subscriptions.

## Deploy

This is plain HTML/CSS/JavaScript. Serve the **contents** of this directory at the site root:

- `index.html`
- `styles.css`
- `analysis.js`
- `app.js`

On Vercel, set framework to **Other**, project root directory to `smc-terminal` if connecting the GitHub monorepo, and deploy as static files.

You can test locally with `python -m http.server 8000` from within this directory and navigate to `http://localhost:8000`.

No secret or API key is required. Browser network access to the Binance public market-data REST / WebSocket endpoints is required; the app reports unavailability rather than fabricating market prices. Chart library loads over jsDelivr, and fonts over Google Fonts.

## SMC engine — important limitations

SMC labels are **defined algorithmically**, not a unique or consensus definition of Smart Money Concepts, and do **not** measure real institutional order flow. Their meaning depends on swing radius, candle close confirmation, lookback, liquidity and venue. They are educational patterns only and do not predict price direction. The platform does not provide buy/sell execution or guaranteed signals.

- Swing pivots are **non-repainting after right-side confirmation**, not immediately available at the swing candle.
- Only the latest fully closed candles feed the SMC calculation (incoming open candles update price/candles but are excluded from event analysis).
- The order-block heuristic is deliberately simple and should not be treated as validated institutional block detection.
- Confluence values are counts of conditions, not a calibrated success probability.
- Markets are **Binance Spot USDT**, not forex, gold, futures or broker CFD feeds. Those require additional data licensing / source integration.

## Legal / licenses

TradingView Lightweight Charts™ is used with mandatory creator credit and link: https://www.tradingview.com/
Repository: https://github.com/tradingview/lightweight-charts

Binance public endpoints: https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md

The app is independent, not affiliated with TradingView or Binance. Read the applicable market-data redistribution terms before using commercially.

© RibhLab 2026. For research and education. Not financial advice.
