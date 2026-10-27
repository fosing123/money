# Student Money — experience prototype

A colourful, mobile-first money-management website concept for students in Cameroon. The final Cameroonian-language brand name is still undecided; **Student Money** is a temporary working label.

## Personalized onboarding

The first-run experience now asks students about:
1. Profile and student/work situation
2. Up to three personal money goals
3. Income amount, frequency and usual payday
4. Current available balance and where they keep money
5. A weekly savings target
6. Weekly expenses, school/personal estimates and debts owed
7. An editable starter budget, with a warning when allocations exceed expected income

The starting values are examples based on the user's current tracker setup (5,000 FCFA starting balance, 10,000 FCFA weekly income, Tuesday payday and 2,000 FCFA weekly savings goal). All are editable.

## Included

- Large photo-style student welcome visual and matching setup artwork
- Responsive 7-step onboarding, live savings math and weekly expense gap feedback
- FCFA dashboard, income/expense logging, category budgets and savings goals
- Searchable activity and CSV export
- White chat-style Money Coach preview
- Campus Marketplace and Invest “Coming Soon” sections
- Mobile bottom navigation, desktop sidebar, transitions and basic offline shell

## Preview locally

No Node.js, npm or Android Studio is required for this static prototype.

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

Open **http://127.0.0.1:8080** and keep the server running. For later updates, run `git pull` inside the repository first.

To see onboarding again after finishing it, use **More → Settings → Reset local data**. This deletes locally stored demo entries.

## Free hosting

Enable GitHub Pages under **Settings → Pages → Deploy from a branch → main → /(root)**. Save and wait for GitHub to publish the site; hosting has not been enabled automatically.

## Prototype limits

- Data is stored in the current browser only. There is no account sync or secure cloud backup.
- Money Coach uses local rules, not a connected AI model.
- Receipt scanning, user authentication, real bank/mobile-money connection, payment processing, ads and notifications are not connected.
- Marketplace and Invest are coming-soon pages. Invest does not accept money or offer investments.
- The product is a budgeting prototype, not a bank, wallet, investment service or financial adviser.

Before production, add secure backend storage, privacy/security controls, automated tests, and legal review for advertising, payments or financial products.
