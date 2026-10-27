# Student Money — experience prototype

A mobile-first, colourful money-management website concept for students in Cameroon. The permanent brand name is intentionally undecided; **Student Money** is only a working label.

## What's in this version

- Four-stage onboarding flow with persona choices, pre-made goal cards, FCFA allowance/balance estimates, and a savings target.
- Welcome illustration and matching local SVG illustrations for the money coach, marketplace, and future business-funding section.
- Guided first-run tour to help people understand the dashboard.
- Responsive dashboard with income/expense totals, quick actions, budget categories, recent activity, and savings goals.
- Add income and expense records, edit budget limits, add and update goals, filter/search activity, and export transactions to CSV.
- White chat-style Money Coach interface with starter prompts and a simple local rule-based helper.
- Marketplace and Invest sections are clearly marked **Coming Soon**.
- Responsive desktop sidebar plus mobile bottom navigation, animated screen/card transitions, onboarding swipe gesture, and a basic cached offline shell.

## Preview locally

This is a no-build static website. No Node.js, npm, or Android Studio is required.

### On a computer

```bash
git clone https://github.com/fosing123/money.git
cd money
python -m http.server 8080
```

Open http://127.0.0.1:8080 in your browser.

### On Android with Termux

```bash
pkg update && pkg install git python -y
git clone https://github.com/fosing123/money.git
cd money
python -m http.server 8080
```

Then open http://127.0.0.1:8080 in Chrome. Keep Termux running while previewing the site. To re-download future changes, enter the repository folder and run `git pull`.

## Free hosting option

GitHub Pages can host the static version: repository **Settings → Pages → Deploy from a branch → main → /(root)**. Save and wait for GitHub to provide the published address. Pages has not been enabled by this repository change.

## Important prototype limits

- Transactions, budgets, onboarding details and savings goals are stored locally in the current browser. They do not sync across devices and should not be treated as a secure financial record system.
- Money Coach is a **local rule-based preview**, not a connected AI model.
- There is no user authentication, real-time bank/Orange Money/MTN MoMo integration, transaction processing, live advertising network, or push-notification service.
- Marketplace and Invest are non-functional coming-soon screens. The Invest section does not collect funds, offer investments, or promise returns.
- Before public production use, add a secure backend, privacy disclosures, automated tests, appropriate security controls, and legal review for any payment, advertising, financial or investment features.

## Next steps

1. Test the onboarding and navigation on small Android screens.
2. Ask a few students to complete common flows without help.
3. Choose the permanent Cameroonian-language name and visual identity.
4. Add authenticated cloud storage and backup only after validating the prototype.
5. Connect a real AI provider through a server-side API with privacy and usage-cost controls.
6. Review local requirements before enabling advertising, payments or business-investment functionality.
