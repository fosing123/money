# Adsterra setup for TIANA

TIANA renders the standard banner units only on the public **Money School** education page. The 320×50 mobile leaderboard appears just below the page introduction. The 300×250 rectangle appears after the educational guides. The scripts are never injected into account balances, transactions, budgets, savings goals, the AI Coach, Analyzer, Insights or other private finance screens. Premium members do not receive the Money School ad slots.

## Website ID vs ad-unit IDs

The value `6182605` is configured as `ADSTERRA_WEBSITE_ID`. It identifies the publisher website; it is not an ad-unit key. Each banner unit has its own generated code and its own placement statistics.

## Approved banner snippets

1. Sign in to Adsterra as a publisher.
2. Open **Websites** and confirm the TIANA domain is approved.
3. Open **Add Unit → Banner**, choose **320×50**, and copy the complete code from **Get Code**.
4. Create a separate **300×250** banner unit and copy its complete code too.
5. Use only the exact snippets shown as active in your own Adsterra dashboard or the approval email. Do not edit the script URLs or keys.

Adsterra's official guides explain that banner codes are generated per unit and can be placed in page content. They also recommend matching the ad size to the viewport and avoiding several crowded banners on the same area. See the [publisher dashboard guide](https://adsterra.com/blog/set-up-publishers-dashboard/) and [banner implementation guide](https://adsterra.com/blog/how-banner-ads-make-money/).

## Configure Cloudflare staging

In GitHub, open **Settings → Environments → tiana-django-staging** and configure:

- Variable `ADSTERRA_ENABLED`: `true`
- Variable `ADSTERRA_WEBSITE_ID`: `6182605`
- Secret `ADSTERRA_BANNER_320X50_CODE`: paste the complete 320×50 banner snippet
- Secret `ADSTERRA_BANNER_300X250_CODE`: paste the complete 300×250 banner snippet

The previous `ADSTERRA_NATIVE_BANNER_CODE` secret remains a backwards-compatible fallback for the 320×50 slot if the new dedicated secret is not set.

The **Deploy TIANA Django Worker** workflow transfers these values to Cloudflare Worker secrets before deployment. The generated JavaScript is intentionally not committed to Git. For local testing, put the values in your untracked `.env` file and keep `ADSTERRA_ENABLED=0` until the site and ad units are approved.

## Why some supplied scripts are not enabled

The additional scripts using the `/1/`, `/14/` and `/21/` paths do not identify their ad format from the snippet alone. They are not included in this banner-only integration. Confirm each unit's exact format in the Adsterra dashboard before enabling it. TIANA intentionally avoids Popunders, Smartlinks, Social Bar overlays and automatic redirects inside signed-in finance and AI workflows.

The Analyzer and AI Coach display sensitive personal spending context. Third-party JavaScript on those pages could inspect page content, so those pages remain ad-free rather than exposing financial records to advertising scripts.

## Pause ads

Set `ADSTERRA_ENABLED=false` in the GitHub environment and redeploy. Ad delivery and earnings still depend on Adsterra approval, active ad inventory, browser protections, and account settings; successful deployment does not guarantee impressions or payouts.
