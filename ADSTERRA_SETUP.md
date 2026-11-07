# Adsterra setup for TIANA

TIANA keeps Adsterra ads inside the public **Money School** education page. It does not inject third-party ad scripts into account balances, transactions, budgets, savings goals, the AI Coach, or Analyzer pages. Active Premium members do not receive the Money School ad slot.

## What the supplied ID means

The supplied value `6182605` is configured as `ADSTERRA_WEBSITE_ID`. Adsterra distinguishes a website/domain ID from an ad-unit placement and its generated JavaScript code. The website ID alone cannot render an ad.

## Get the placement code

1. Sign in to Adsterra as a publisher.
2. Open **Websites** and confirm the website corresponding to the live TIANA domain is listed and approved.
3. Add a **Native Banner** or a standard **Banner** placement for that website. For TIANA, prefer a static in-content banner; do not enable Popunder, forced redirects, or Social Bar overlays across financial screens.
4. Wait until the website and ad unit are active.
5. Select **Get code** for that exact ad unit and copy the complete generated script unchanged.

Adsterra's current publisher instructions say the website must be added, the ad unit requested/approved, and the generated code copied from the publisher dashboard or approval email. See the official [publisher dashboard guide](https://adsterra.com/blog/set-up-publishers-dashboard/) and [banner implementation guide](https://adsterra.com/blog/how-banner-ads-make-money/).

## Configure the Cloudflare staging deployment

In GitHub, open **Settings → Environments → tiana-django-staging** for this repository and configure:

- Variable `ADSTERRA_ENABLED`: `true`
- Variable `ADSTERRA_WEBSITE_ID`: `6182605` (replace only if your Websites table shows a different site ID)
- Secret `ADSTERRA_NATIVE_BANNER_CODE`: paste the complete ad-unit script copied from Adsterra.

Then run the **Deploy TIANA Django Worker** workflow on `main`. The workflow transfers the code as a Cloudflare Worker secret before deploying. The code is intentionally not committed to Git.

For local testing, put the same values in your untracked `.env` file. Keep `ADSTERRA_ENABLED=0` until you have the approved ad-unit script.

## Safety and placement rules

- Do not paste the numeric website ID into a JavaScript zone/key field.
- Do not use a Smartlink as a fake banner; Smartlinks are user-click destinations and need a deliberate link placement.
- Do not put popunders, automatic redirects, or full-screen overlays on the authenticated finance and AI flows.
- Use only the exact code from the approved Adsterra dashboard. The server renders that trusted configuration as HTML on Money School only.
- If you need to pause ads, set `ADSTERRA_ENABLED=false` and redeploy.
- Ad delivery and earnings still depend on Adsterra approval, their ad inventory, browser protections, and your account settings; a successful deploy does not guarantee an impression or payout.
