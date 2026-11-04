# TIANA Learn and AdSense readiness

This note describes the public editorial section added to the Django application. It is served by the same Django project and is not a separate blog or Pages project.

## Public routes

| Route | Purpose |
|---|---|
| `/learn/` | TIANA Learn index with search and topic filters |
| `/learn/<slug>/` | Individual original learning article |
| `/about/` | About TIANA |
| `/contact/` | Public support contact |
| `/privacy/` | Privacy policy |
| `/terms/` | Terms of use |
| `/disclaimer/` | Financial education disclaimer |
| `/ads.txt` | Google publisher declaration when a valid publisher ID is configured |

The old `/money-school/` route permanently redirects to `/learn/` to preserve existing bookmarks.

The article content is currently held in `core/learning_content.py` as editorial data, with no new database tables or migrations. This keeps the first release simple and lets the team review content in Git. If TIANA later needs an editorial CMS, it should be introduced as a separately tested feature with draft/review/publish controls.

## Editorial launch checklist

- Review every article for accuracy, clarity and local relevance before publication.
- Keep article titles, examples, and explanations original; do not copy other publishers.
- Add an author/editor contact and a real public support email.
- Check all public links on mobile and desktop.
- Keep the privacy policy aligned with the real services used by the production app (Cloudflare, database host, Firebase, AI provider, email and any analytics/advertising tools).
- Update the policy whenever the data flows or service providers change.
- Make sure public article pages are crawlable and that private finance pages remain behind sign-in.
- Do not place ads on login, registration, dashboards, transaction forms, private member content, or other non-content views.

There is no fixed number of posts or word count that guarantees AdSense approval. Google reviews the site and its content, navigation, ownership and policy compliance. The six initial guides are a starting library, not a promise of approval.

## AdSense configuration lifecycle

Ad serving is deliberately disabled by default.

1. Create an AdSense account using the site's legal owner/publisher details and the correct payment country.
2. Add `tiana.lol` in AdSense.
3. When Google provides the publisher ID (`ca-pub-...`), add it as the Cloudflare Worker variable `ADSENSE_CLIENT_ID`. This enables Google's site-connection script on the public homepage, TIANA Learn pages and public policy pages.
4. Follow the verification/review steps shown by AdSense. The publisher declaration is available from `https://tiana.lol/ads.txt` once the publisher ID is configured.
5. Wait until AdSense reports the site as approved/ready before serving ad units.
6. Create an ad unit in AdSense and set the numeric slot ID as `ADSENSE_SLOT_ID`.
7. Only then set `ADSENSE_ENABLED=1` in the Cloudflare Worker environment. Keep this off until the site is approved and the slot is real.
8. Deploy the configuration and verify ads only on the public learning pages.

### Worker variables

| Name | Type | When needed |
|---|---|---|
| `PUBLIC_CONTACT_EMAIL` | Variable | Before public launch/review; must be a real monitored address |
| `ADSENSE_CLIENT_ID` | Variable | When AdSense asks to connect/verify the site |
| `ADSENSE_SLOT_ID` | Variable | After an ad unit exists |
| `ADSENSE_ENABLED` | Variable | Set to `1` only after site approval and slot configuration |

Never commit real account credentials or secret values. Publisher IDs and ad slot IDs are identifiers, not secrets, but configure them through the Worker environment so staging and production can be controlled independently.

## Domain and deployment boundary

A Django route does not automatically move the live domain. The existing Cloudflare deployment notes identify `tiana-django-staging` as a separate staging Worker and the prior `tiana-money` Pages project as the current production site. Therefore this feature branch does not change DNS, Pages production, Worker routes or custom-domain bindings.

The `/learn/` route will be served on `tiana.lol` only when the production hostname is deliberately attached to the validated Django Worker (or when the same Django app is deployed behind that hostname). Before that cutover, test the route on the Django staging hostname and complete the application's existing authentication, ledger, backup/restore, media, notifications and load checks. Do not switch the live hostname as part of this content-only change.

## Verification

Run the project checks from the repository root:

```bash
uv run python manage.py check
uv run python manage.py test core
uv run python manage.py test
uv run python manage.py collectstatic --noinput
```

A passing unit test suite does not by itself prove a live Cloudflare hostname, database, R2 bucket or AdSense account is configured. Verify those separately in the deployment environment.
