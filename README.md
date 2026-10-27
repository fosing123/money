# Student Money — experience prototype

A colourful, mobile-first money-management website for students in Cameroon. The permanent brand name is still undecided; **Student Money** is a temporary working label.

## Included
- Illustrated welcome screen and short onboarding
- Profile choices, goal cards, FCFA balance and allowance setup
- Guided first-run tour
- Dashboard, income/expense tracking, budgets and savings goals
- White chat-style Money Coach preview
- Campus Marketplace and Invest “Coming Soon” pages
- Mobile bottom navigation, desktop sidebar, transitions and basic offline shell

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

Open **http://127.0.0.1:8080** in a browser. Keep the server running. For later updates, run `git pull` inside the repo before starting the server.

## Free hosting

You can enable GitHub Pages under **Settings → Pages → Deploy from a branch → main → /(root)**. Save and wait for GitHub to publish the site; hosting has not been enabled automatically.

## Prototype limits
- Entries and goals are stored in the current browser only; there is no account sync or secure cloud backup.
- Money Coach uses local rules, not a connected AI model.
- There is no payment processing, live bank/mobile-money connection, ad network, or push notification service.
- Marketplace and Invest are coming-soon pages. Invest does not accept money or offer returns.

Add a secure backend, privacy/security controls, tests, and legal review before production or any financial, advertising, payment, or investment integrations.
