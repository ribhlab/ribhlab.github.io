# RibhLab — Commercial launch security & legal gates

Status: **NO PAID CHECKOUT / NO LIVE TRADING ENABLED**. This is an internal launch checklist, not legal certification. Morocco is the initial legal review jurisdiction; assess customer jurisdictions before cross-border sales.

## Mandatory go/no-go gates

- [ ] Identify actual merchant/legal entity, address, support email, commercial/tax registration details as applicable. Do not invent these details.
- [ ] Moroccan counsel reviews Law 31-08 distance selling disclosures, contractual terms, invoice obligations, withdrawal rights and exceptions for digital content. Never assert a blanket no-refunds rule.
- [ ] Publish accurate, localized Terms of Sale, refund/withdrawal policy, Privacy Policy, Cookie Policy, security contact, complaint channel, product limits, prices, taxes, currency, delivery and support SLAs before checkout.
- [ ] Document CNDP Law 09-08 compliance, including applicable declaration/authorization and cross-border transfer requirements BEFORE collecting customer data.
- [ ] Use a licensed/legitimate payment provider with hosted checkout. Do not collect or store card numbers, CVV, banking login or brokerage credentials in GitHub Pages, source code, forms or logs. Verify merchant eligibility and country availability.
- [ ] Set up server-side webhook signature verification, idempotency, payment reconciliation, fraud/rate limiting, chargeback handling and tested refunds before provisioning purchases. Never trust a client-side 'payment success' redirect.
- [ ] Conduct dependency audit, secret scanning, least-privilege access, MFA for admins, backups, vulnerability response and independent security review. Never commit tokens, API keys or customer uploads.
- [ ] For uploaded files: obtain explicit consent, enforce file size/type limits, malware scan, isolated processing, deletion/retention rules and secure access controls; do not process sensitive documents in public static GitHub Pages.
- [ ] Review intellectual property and commercial licenses for all code, AI models, fonts, assets, images, templates and datasets.
- [ ] Establish customer support, dispute process and truthful marketing. No fake reviews, invented performance, guaranteed earnings or artificial scarcity.

## Additional trading bot gates

- [ ] Get written Moroccan regulatory counsel review of whether software distribution, signals, personalized advice, broker referral, copy trading or account management triggers AMMC/other licensing or cross-border restrictions.
- [ ] Keep demos and backtests clearly separate from live trading and audited track records. Publish assumptions, data source, out-of-sample results, spread, commission, slippage, drawdown and failure modes.
- [ ] No guaranteed profits, unrealistic income claims, or implied regulator endorsement. Clear prominent loss-of-capital risk warnings.
- [ ] Default to paper trading. Live trading requires separate informed opt-in, broker compatibility tests, maximum loss limits, position limits, kill switch and fail-safe behavior.
- [ ] Never request customer broker passwords. Prefer scoped revocable API access where permitted; secrets must be securely managed server-side, not in static frontend.
- [ ] Define updates, uptime limitations, cancellation, refunds and incident response before offering subscriptions.

## Authoritative starting references

- Moroccan Ministry of Industry and Trade, consumer protection: https://www.mcinet.gov.ma/fr/content/protection-du-consommateur
- CNDP website compliance: https://www.cndp.ma/conformite-des-sites-web/
- CNDP processing notification: https://www.cndp.ma/notifier-un-traitement/
- AMMC warning about unauthorized investment advice/trading fraud (22 Dec 2025): https://www.ammc.ma/sites/default/files/Communiqu%C3%A9%20de%20presse%20-%20Mise%20en%20garde%20AMMC%20VFR_0.pdf

**Release rule:** No monetization or live trading until applicable gates are reviewed, verified and signed off by the project owner and qualified counsel/security reviewers. This checklist does not claim legal compliance.
