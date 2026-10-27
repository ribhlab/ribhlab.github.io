# RibhLab — Free domain, Google AdSense and GitHub Pages

**PREPARATION ONLY. No domain has been registered and NO live DNS, GitHub Pages custom-domain setting, or AdSense account was changed.** Keep https://univcours.github.io/ribhlab-site/ working until the user owns the new domain and the DNS/HTTPS checks pass.

## Truly free option: ribhlab.pp.ua (proposed, availability unconfirmed)

- At https://nic.ua/en/domains/.pp.ua the registrar NIC.UA advertises .PP.UA registration for 0 UAH and annual renewal for 0 UAH. The domain can be registered by users outside Ukraine.
- The name **ribhlab.pp.ua is not yet verified as available**. Check https://dig.ua/ or NIC.UA's domain lookup. If taken, alternatives to check include ribhlabmedia.pp.ua and ribhlabmag.pp.ua. Never claim registration before it is completed.
- The registry requires an activation SMS sent to the registrant's **own** mobile telephone. Only the owner should enter the activation code.
- **Important privacy warning:** the registrar publishes domain owner's WHOIS details. Read its privacy and public-data policy before registering. Do not disclose the registrant's details or SMS code in GitHub issues or to third parties.
- Verify that the checkout total really is zero and there are no unwanted extras. Check renewal terms.
- The official Public Suffix List https://publicsuffix.org/list/public_suffix_list.dat contains pp.ua. This is a possible AdSense site URL structure; it is **not** advance Google approval.

## After the owner registers the proposed name

1. Activate the domain via the registrar's SMS step and confirm the registrar shows ownership/active delegation. Do NOT change the current public RibhLab site yet.
2. Configure the owner’s registered custom domain at GitHub repository univcours/ribhlab-site → Settings → Pages → Custom domain. Verify domain ownership first when available.
3. Configure DNS at the registrar. Four apex/root A records for @:
   - 185.199.108.153
   - 185.199.109.153
   - 185.199.110.153
   - 185.199.111.153
   Optional www CNAME to univcours.github.io. Do not create wildcard records, or leave DNS parking records that conflict.
4. Confirm HTTPS and DNS before changing canonical/site URL. Enable GitHub Pages Enforce HTTPS when available.
5. After domain ownership, DNS and HTTPS are confirmed, update:
   - site.config.json domain to https://ribhlab.pp.ua
   - .github/workflows/deploy-pages.yml SITE_URL to https://ribhlab.pp.ua
   - GitHub Pages custom domain settings as above, plus Google Search Console after launch.
6. Confirm all three locales (ar/en/fr), Market Pulse, Document Studio, 11 tool routes, article imagery, mobile navigation, redirects, sitemap.xml and robots.txt. The site should be served at the root of the custom domain, **without /ribhlab-site**.
7. Only with an actual publisher account and after verification/eligibility can the real AdSense publisher ID be configured; do not enable code or invent an ID before authorized AdSense setup.

## Google AdSense facts

Google official help:
- https://support.google.com/adsense/answer/9724 (eligibility)
- https://support.google.com/adsense/answer/2784438 (valid site URL format)
- https://support.google.com/adsense/answer/12170421 (domain/site types)

A registered domain is not a guarantee of AdSense acceptance. Google assesses original value, policies, ownership and site experience. External RSS titles must be attributed, not misrepresented as RibhLab’s original reporting. Editorial contact, privacy and necessary disclosures should be accurate.

The project-style GitHub URL https://univcours.github.io/ribhlab-site/ includes a path, which Google's site entry form doesn't accept as the domain itself.

## Google-hosted free alternative

Blogger allows free *.blogspot.com blog addresses and provides direct AdSense integration: https://support.google.com/adsense/answer/1269077 . Blogger cannot simply become the DNS alias of a GitHub Pages project containing all its interactive tools. A Blogger move would be a migration needing separate validation and the user's article-review hold must be respected.

## Release and rollback guard

This pull request only PREPARES CI for a root-domain build and documents the free domain path. **It must not switch production or declare any domain registered.** Keep the old GitHub URL available until the fully owned, verified custom domain is working. Do not enable payments, recurring fees or scheduled publication tasks.

Official GitHub Pages DNS and custom domain guide:
https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site
