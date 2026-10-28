# Nkem — Smart Money. Brighter You.

Nkem is a mobile-first student money-planning PWA designed around student life in Cameroon and FCFA/XAF. The current project is a **static frontend prototype** with local browser persistence.

## Nkem experience
- Branded welcome screen and illustrated onboarding for spending, savings goals and money guidance.
- Goal-based onboarding, optional life-stage/persona selection, income cadence, starting balance, weekly needs and editable starter budget.
- Dashboard, recorded income and expenses, transaction search, budget tracking, spending insights and manually tracked savings goals.
- Eight selectable colour themes: Nkem Violet, Mint Growth, Ocean Blue, Sunset Peach, Golden Hour, Midnight Pro, Rose Dream and Forest Wealth.
- Rule-based Money Coach with a clear disclosure that it is not connected to a live AI model.
- Campus Marketplace sample catalogue with category search, saved listings, listing details and local seller-draft functionality.
- Student-business opportunity discovery examples, risk education, saved opportunities and locally saved interest.
- Offline app-shell caching, JSON backup/restore and CSV transaction export.
- Terms and Privacy pages that describe this preview accurately.

## Prototype boundaries — please read
This repository does **not** currently include a backend service, database server, server-side accounts or a production authentication provider. Personal data remains in the current browser/device and is not cloud-synced or protected by server-side ownership controls. Google, email and phone account options are visual entry points that disclose they are not connected; the local preview can be continued without an account.

Marketplace listings and student-business profiles are clearly illustrative examples, not verified live offers. Seller drafts and interest registrations remain local and do not contact providers. Payments, bank/mobile-money connections, fund transfers, push notifications and regulated investment execution are not connected. The displayed balance is a manually maintained local record, not a bank balance. The Money Coach is a rule-based local helper, not a live AI model, and should not be treated as personalized professional financial advice.

Do not use the static preview to collect real customers' sensitive financial data or describe it as a production financial service. A production launch requires backend authentication and authorization, database persistence, server-authoritative and auditable financial state transitions, backups, monitoring, rate limits, marketplace moderation, verified providers, legal/privacy review and properly configured integrations. Live AI credentials must remain server-side. Investment execution requires separate legal/regulatory review and authorized providers.

## Run locally
Requires Python 3:
```bash
git clone https://github.com/fosing123/money.git
cd money
python -m http.server 8080
```
Open `http://127.0.0.1:8080`.

## Deploy on GitHub Pages
1. Merge the approved changes to `main`.
2. In GitHub, open **Settings → Pages** and choose **GitHub Actions** as the source.
3. Open **Actions** and verify that the **Deploy Nkem** workflow completes successfully.
4. Open the Pages URL shown in repository settings. Check the app on an Android phone and a desktop browser.

The current build is static; it does not run backend migrations. Keep the app honest about which services are still local-only.

## Smoke-test checklist
- Walk through the new welcome and three introduction screens.
- Open the account-options panel and confirm it explains that sign-in is not connected; continue without an account.
- Complete profile, goals, income, balance, savings, weekly needs and budget setup.
- Add income and an expense and check the dashboard, transaction list and weekly spend.
- Create a savings goal and add a goal contribution; ensure totals update as expected.
- Change all eight palettes and refresh.
- Search and save Marketplace examples, open detail views and create a private draft.
- Register interest in a business example and read the risk disclosure.
- Export a JSON backup before clearing browser data.
