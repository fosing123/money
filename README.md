# Student Money — student finance and discipline prototype

A colourful, mobile-first money management website concept for students in Cameroon. The final Cameroonian-language brand name is undecided; **Student Money** is a temporary working label.

## Core experience

- Full-screen, photo-led onboarding with personalized profile, money goals, payday/income, current balance and money sources
- Editable FCFA weekly needs and budget plan, including a warning if needs exceed money available after the savings target
- Dashboard with current-week spending, transactions, savings goals and personalized advice
- Weekly budget limits use transactions recorded since Monday; all-time recorded totals remain visible separately
- Savings-goal deposits move funds out of the recorded spendable balance and appear as a transfer in activity (not an expense)
- Activity search and filters for money in, money out and savings transfers
- Insights page with week-to-date trends, comparable last-week spend, category budget use, goal forecasts and a recommended next step
- Daily discipline checklist: record expenses, pause before impulse buys, and reconnect with a goal
- Streaks for completed daily routines, stored locally
- Goal-based Money Coach preview using saved goals, current-week spending, budget limits, entered debts and savings targets
- Campus Marketplace and Invest “Coming Soon” pages

## Preview locally

No Node.js, npm or Android Studio is required.

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

To replay onboarding, use **More → Settings → Reset local data**. Export your records first if you need them; reset deletes the current browser's demo data and streak.

## Prototype limits

- Records, profile, goals and habits are stored in this browser only; they do not sync across devices or have secure cloud backup.
- Money Coach uses personalized local rules, not a connected AI model or professional financial advice.
- Balance and transactions are manually entered. No bank, Orange Money, MTN MoMo, real receipt scanning, authentication, payments, advertising or push-notification service is connected.
- Marketplace and Invest are coming-soon pages. Invest does not accept money, offer actual investments or promise returns.

Before production, add secure accounts and cloud storage, automated tests, privacy/security controls, server-side AI with usage and privacy safeguards, and legal review before enabling financial or investment features.
