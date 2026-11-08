# Adsterra setup for TIANA

TIANA uses two standard Adsterra banner units across the public welcome experience and the free signed-in app:

- **320×50 mobile banner:** shared placement below the site header (and below the welcome hero on the public landing screen).
- **300×250 rectangle:** a second shared placement on ordinary pages, including Profile, Dashboard, Activity, Budgets, Goals and Insights. On AI pages, this same size is presented in a sponsored pause before the AI request is sent.

Money School also displays the two units. Premium members remain ad-free.

## Website ID vs ad-unit IDs

The value `6182605` is `ADSTERRA_WEBSITE_ID`, used for publisher website reporting. It is not an ad-unit key. Each banner unit has its own generated code and placement statistics.

## Create the two banner units

1. Sign in to Adsterra as a publisher.
2. Open **Websites** and confirm the TIANA domain is approved.
3. Open **Add Unit → Banner**, choose **320×50**, and copy the complete code from **Get Code**.
4. Create a separate **300×250** Banner unit and copy its complete code too.
5. Use the exact active snippets from your own Adsterra dashboard. Do not edit their script URLs or keys.

The official [publisher dashboard guide](https://adsterra.com/blog/set-up-publishers-dashboard/) explains adding a website and generating its ad-unit code. The [publisher formats page](https://adsterra.com/publishers/) describes banners and Social Bar/interstitial formats.

## Configure Cloudflare staging

In GitHub, open **Settings → Environments → tiana-django-staging** and configure:

- Variable `ADSTERRA_ENABLED`: `true`
- Variable `ADSTERRA_WEBSITE_ID`: `6182605`
- Secret `ADSTERRA_BANNER_320X50_CODE`: the complete 320×50 banner snippet
- Secret `ADSTERRA_BANNER_300X250_CODE`: the complete 300×250 banner snippet

The previous `ADSTERRA_NATIVE_BANNER_CODE` remains a backwards-compatible fallback for the 320×50 unit.

The **Deploy TIANA Django Worker** workflow transfers these values to Cloudflare Worker secrets before deploying. Third-party JavaScript is not committed to Git. For local testing, use your untracked `.env` file and keep `ADSTERRA_ENABLED=0` until the site and units are approved.

## AI Coach and Analyzer sponsored pause

Before the Coach submits a Gemini request or the Analyzer sends its AI-enhanced analysis request, TIANA opens a short sponsored pause containing the 300×250 banner. The user presses **Continue to TIANA AI** after the placement has had time to load. The user is never asked or incentivised to click an advertisement.

Important: a standard banner script does not provide a trusted video-completion/reward callback. This pause is an ad-supported presentation step, not a verified rewarded-video integration. Ad blockers, low inventory, or script failures can mean no impression or revenue even though a user can continue. Do not describe this as guaranteed payment per AI request.

## Privacy boundary

Each publisher snippet is rendered inside a sandboxed iframe with scripts and ad popups allowed, but without same-origin access or top-page navigation. This limits an ad script's ability to inspect TIANA's surrounding finance and AI page DOM. Test actual delivery after deployment because a publisher's code may not render or count impressions identically in a sandboxed frame.

## Other supplied snippets not enabled

The additional scripts using the `/1/`, `/14/` and `/21/` paths are not enabled in this release. Confirm their exact formats in the Adsterra dashboard before using them. TIANA intentionally does not activate popunders, automatic redirects or unclassified overlays across financial workflows.

## Pause ads

Set `ADSTERRA_ENABLED=false` in the GitHub environment and redeploy. A successful deployment does not guarantee impressions or payouts; delivery depends on approval, fill rate, browser protections and publisher-account settings.
