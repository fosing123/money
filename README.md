# Student Money — student finance and discipline prototype

A colourful, mobile-first money management website concept for students in Cameroon. The final Cameroonian-language brand name is undecided; **Student Money** is a temporary working label.

## What's in the project

- `index.html`: the app shell and page metadata
- `app.css`: responsive layouts, full-screen photo-led onboarding, glass cards, charts and motion
- `app.js`: onboarding, transactions, weekly budget calculations, savings transfers, insights, habit tracking and the rule-based Money Coach
- `assets/`: local illustrations and student photography
- `sw.js`: offline app-shell cache
- `manifest.webmanifest`: installable web-app metadata

## Main experience

- Full-screen, photo-led onboarding with profile, goals, payday/income, available balance, money sources, weekly needs and debts
- Nine personalized goal paths across education/career, tech and creative work, business, wellbeing, independence, family, travel, emergency savings and personal dreams
- Six selectable colour palettes: Dreamy Violet, Ocean Calm, Sunset Glow, Forest Fresh, Rose Studio and Midnight Neon
- Custom savings goals with a category, target amount, saved amount and optional personal motivation
- An editable FCFA weekly budget and warning when actual needs exceed the plan or allocations exceed income
- Dashboard showing recorded balance, transactions, current-week spending and savings goals
- Weekly budgets use transactions recorded since Monday; lifetime recorded totals stay separate
- Savings-goal deposits move funds out of the recorded spendable balance and appear as savings transfers, not expenses
- Transaction search and filters for money in, money out and saved transfers
- Insights page with week-to-date trends, spending compared with the same elapsed period last week, category budget use, goal forecasts and a recommended next step
- Daily discipline checklist: record expenses, pause before impulse buys, and reconnect with a goal
- Streaks for completed daily routines, stored locally
- Goal-aware Money Coach using saved goals, current-week spending, budget limits, debt entered during setup and savings targets
- Money Coach understands common English and French expense descriptions and FCFA number formats
- Campus Marketplace and Invest “Coming Soon” pages

## Preview locally

No Node.js, npm or Android Studio is required to preview the website.

**Computer**
```bash
git clone https://github.com/fosing123/money.git
cd money
python -m http.server 8080
```

**Android + Termux**
```bash
pkg update && pkg install git python -y
git clone https://github.com/fosing123/money.git
cd money
python -m http.server 8080
```

Open **http://127.0.0.1:8080** and keep the server running. Pull updates using `git pull` from inside the repository.

To replay onboarding, use **More → Settings → Reset local data**. Export your records first if needed; reset deletes the current browser's demo data and habit streak.

## Quick manual test checklist

1. Complete onboarding with the default 10,000 FCFA weekly income, 2,000 FCFA weekly savings and 5,000 FCFA opening balance.
2. Check that the starter expense estimates trigger a realistic-budget warning if they exceed the plan.
3. Add a food expense in English and a transport expense in French; check the balance and Activity.
4. Add money to a savings goal; check that available balance goes down and the transfer appears under **Saved**, not **Money out**.
5. Mark each daily habit; refresh the page and confirm the checklist persists.
6. Open **More → Insights** and check the week-to-date chart, budget usage and coach recommendation.
7. Confirm Marketplace and Invest stay labelled Coming Soon.

## Prototype limits

- Records, profile, goals and habits are stored in this browser only; they do not sync across devices or have secure cloud backup.
- Money Coach uses personalized local rules, not a connected AI model or professional financial advice.
- Balance and transactions are manually entered. No bank, Orange Money, MTN MoMo, real receipt scanning, authentication, payments, advertising or push-notification service is connected.
- Marketplace and Invest are coming-soon pages. Invest does not accept money, offer actual investments or promise returns.

Before production, add secure accounts and cloud storage, automated browser tests, privacy/security controls, server-side AI with usage and privacy safeguards, and legal review before enabling financial or investment features.


## Deploy on GitHub Pages

This repository is a static web app, so it needs no server, database, build command or API key for the current prototype. A GitHub Actions workflow checks the JavaScript, validates the app shell and offline-cache assets, then publishes the site when code reaches `main`.

**One-time setup**
1. Open the repository on GitHub and go to **Settings → Pages**.
2. Under **Build and deployment**, set **Source** to **GitHub Actions**.
3. Open **Actions** and allow workflows if GitHub asks.
4. Merge or push the deployment workflow to `main`. Each later push to `main` will validate first and deploy automatically. You can also start the workflow from **Actions → Deploy Student Money → Run workflow**.

GitHub Pages creates the live URL after the first successful deployment; find it in **Settings → Pages** or the deployment job's environment link. This workflow does not need repository secrets.

## Back up your data

Open **More → Settings → Your privacy** and choose **Download full backup (JSON)** to save your profile, budget, goals, settings and transaction records. Keep that file somewhere private. On the new device, open the same app, choose **Restore a backup**, and select the JSON file. Restore replaces the data stored in that browser, so export the current device first if you need to keep both sets of records. Transaction-only CSV export remains available for spreadsheets.

## Before a public launch

This version is an offline-capable budgeting prototype, not a real wallet or bank. User data remains in the current browser unless they export a backup. There is no user login, secure cloud sync, bank or mobile-money integration, payment processing, connected AI service, or actual investment offering. Do not enter account PINs or payment credentials. Add authentication, server-side storage, recovery, privacy controls and a security/legal review before offering shared accounts or money-moving features.
