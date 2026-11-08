# Adsterra setup for TIANA

TIANA uses two standard Adsterra banner units across the public welcome experience and the free signed-in app:

- **320×50 mobile banner:** below the site header on standard app pages and below the welcome hero on the public landing page.
- **300×250 rectangle:** after page content on standard app pages, including Profile, Dashboard, Activity, Budgets, Goals, Insights, AI Coach and Analyzer.

Money School also displays both units. Active Premium members remain ad-free.

## Website ID vs ad-unit IDs

The value `6182605` is `ADSTERRA_WEBSITE_ID`, used for publisher website reporting. It is not an ad-unit key. Each banner unit has its own generated code and placement statistics.

## Create the two banner units

1. Sign in to Adsterra as a publisher.
2. Open **Websites** and confirm the TIANA domain is approved.
3. Open **Add Unit → Banner**, choose **320×50**, and copy the complete code from **Get Code**.
4. Create a separate **300×250** Banner unit and copy its complete code too.
5. Use the exact active snippets from your own Adsterra dashboard. Do not edit script URLs, keys, dimensions or tag content.

The official [publisher dashboard guide](https://adsterra.com/blog/set-up-publishers-dashboard/) explains adding a website and generating ad-unit code. The [publisher formats page](https://adsterra.com/publishers/) describes standard banners, Native Banners and Social Bar/interstitial formats.

## Configure Cloudflare staging

In GitHub, open **Settings → Environments → tiana-django-staging** and configure:

- Variable `ADSTERRA_ENABLED`: `true`
- Variable `ADSTERRA_WEBSITE_ID`: `6182605`
- Secret `ADSTERRA_BANNER_320X50_CODE`: the complete 320×50 banner snippet
- Secret `ADSTERRA_BANNER_300X250_CODE`: the complete 300×250 banner snippet

The previous `ADSTERRA_NATIVE_BANNER_CODE` remains a backwards-compatible fallback for the 320×50 unit.

The **Deploy TIANA Django Worker** workflow transfers these values to Cloudflare Worker secrets before deploying. Third-party JavaScript is not committed to Git. For local testing, use your untracked `.env` file and keep `ADSTERRA_ENABLED=0` until the site and units are approved.

## AI Coach and Analyzer

Both AI pages display the two standard banner placements while users use the AI features. The supplied standard banner snippets do not provide a verified rewarded-video completion callback, so TIANA does not claim that each Gemini request is paid for by a specific ad view.

Adsterra's current [Publisher Terms](https://adsterra.com/publishers-terms-managed/) require the provided tag to be used as supplied, prohibit placing the tag inside an iframe without prior written consent (clause 4.7), prohibit incentives that inflate impressions/clicks/actions (clause 6), and prohibit confusing or forcing visitors to act. TIANA therefore renders the banner snippets directly on the page and never requires users to click or watch an ad before receiving an AI response.

## Cover Gemini costs

Banner earnings depend on valid impressions, clicks or actions recognised by Adsterra and are not guaranteed per AI request. Ad blockers, unfilled inventory, audience location and advertiser demand affect revenue. Keep the existing daily free AI allowance and Premium request limits in place. For stronger unit economics, add paid AI credits or a Premium subscription rather than assuming each request generates a matching ad payment.

## Other supplied snippets not enabled

The additional scripts using the `/1/`, `/14/` and `/21/` paths are not enabled in this release. Confirm their exact formats and placement rules in your Adsterra dashboard or with Adsterra support before enabling them. Do not guess whether they are Popunder, Social Bar, Interstitial, Native Banner or another format.

## Pause ads

Set `ADSTERRA_ENABLED=false` in the GitHub environment and redeploy. Adding a banner does not guarantee impressions or earnings; Adsterra determines valid delivery and reporting.
