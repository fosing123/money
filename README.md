# Student Money — student finance and discipline prototype

A colourful, mobile-first money management website concept for students in Cameroon. The permanent brand name is undecided; **Student Money** is a temporary working label.

## New onboarding and discipline coach

- Full-screen, edge-to-edge photo backgrounds on the welcome and setup steps
- Personalized profile, goals, payday/income, available balance, money sources, weekly needs and debt questions
- Editable budget that checks spending allocation against expected weekly income
- Goal-aware Money Coach: suggestions based on saved goals, the selected savings target, entered debt and recent recorded spending
- Daily discipline routine: track spending, pause before impulse buys, and review the top goal
- A daily streak counts completed routines stored in this browser
- Dashboard advice card and a goal-focused coach view
- Campus Marketplace and Invest remain Coming Soon pages

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

Open **http://127.0.0.1:8080** and leave the server running. Pull updates with `git pull` from inside the repository.

To replay the onboarding, use **More → Settings → Reset local data**. This clears the current browser's demo records and streak.

## Important prototype limits

- Money, habits and progress are saved in this browser only. They do not sync across devices or have secure cloud backup.
- Advice is personalized using local rules and the information entered by the user. This is **not a connected AI model**, financial adviser, bank or wallet.
- The balance and transactions are manually entered. No Orange Money, MTN MoMo, bank, payment, receipt scanning, advertising or notifications service is connected.
- Marketplace and Invest are Coming Soon. Invest does not collect funds, make investments or promise returns.

Before production, add secure accounts and cloud storage, tests, privacy/security controls, server-side AI with cost/privacy safeguards, and legal review for financial and investment features.
