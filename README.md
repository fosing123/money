# Nkem — Smart Money. Brighter You.

Nkem is a mobile-first student money planner prototype for Cameroon, using FCFA/XAF. It currently runs as a static Progressive Web App with browser-local persistence.

## Included today
- Personal onboarding, career/life-path preferences and configurable weekly budget.
- Income and expense entries, transaction history, budget tracking and expense insights.
- Savings goals with local contribution tracking.
- Six dynamic colour palettes and a responsive layout.
- A rule-based Money Coach with clear disclosure that it is not a connected AI service.
- Campus marketplace discovery with search, categories, saved sample listings, listing details and locally saved private seller drafts.
- Student-business discovery, educational risk information, locally saved interest and privately saved business suggestions.
- Offline app-shell caching and JSON/CSV export.

## Important prototype boundaries
This repository currently contains a **static frontend, not a backend service**. Personal data is saved in the current browser/device and is not cloud-synced or protected by server-side accounts. Marketplace entries are illustrative examples, not verified live offers; seller drafts and interest are saved locally and do not contact anyone. No payment, transfer, investment, OAuth, SMS, push notification, server-side AI or regulated investment execution is connected. The balance is a manually maintained local record and must not be treated as a bank balance. Do not collect real customers' sensitive financial data or represent this prototype as a production financial service.

## Run locally
Requires Python 3 or another static HTTP server:
```bash
git clone https://github.com/fosing123/money.git
cd money
python -m http.server 8080
```
Open `http://127.0.0.1:8080`.

## Deploy on GitHub Pages
1. Push changes to `main`.
2. In GitHub, open **Settings → Pages** and select **GitHub Actions** as the source if the repository workflow expects it.
3. Check the **Actions** tab for the Pages deployment workflow and wait for a successful run.
4. Open the Pages URL shown in repository settings. Test on a phone and desktop.

There is no backend build or database migration for the current static prototype. Before a public production launch, implement server-side authentication, database persistence and ownership permissions, validated authoritative financial transactions, audit logging, backups, rate limits, marketplace moderation, seller verification, privacy/legal pages, and a proper deployment environment. A server-side AI provider requires credentials stored only in server environment variables. Investment/funding execution requires separate legal and regulatory review and an authorized provider.

## Smoke-test checklist
- Complete onboarding; add income and expense records; verify balance, transaction list and weekly spending update.
- Create a savings goal and add a contribution.
- Switch colour palettes and refresh.
- Search/filter marketplace examples; save a listing; create a private seller draft.
- Register interest in a business example; save a business suggestion.
- Export a JSON backup before clearing local browser data.
