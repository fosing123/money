# Student Money — experience prototype

A colourful, mobile-first money-management website for students in Cameroon. The permanent brand name is undecided; **Student Money** is a temporary working label.

## Included
- Illustrated welcome screen and 3 short intro slides
- Profile setup, selectable savings goals and FCFA allowance setup
- Guided tour that can be replayed from the dashboard or More
- Dashboard with a colour-gradient balance card, quick actions, spending donut, recent entries and savings goals
- Income/expense logging, searchable transactions, budget limits and savings progress
- White chat-style Money Coach preview with starter prompts
- Marketplace and Invest “Coming Soon” screens in the footer and More section
- Local 3D student hero asset, matching illustrations, mobile navigation, transitions and basic offline shell

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

Open **http://127.0.0.1:8080** in a browser and keep the server running. For later updates, run `git pull` inside the repository first.

To see onboarding again after you have completed it, use **More → Settings → Reset local data**. This deletes locally stored demo entries.

## Free hosting

You can enable GitHub Pages under **Settings → Pages → Deploy from a branch → main → /(root)**. Save and wait for GitHub to publish the site; hosting has not been enabled automatically.

## Prototype limits
- Entries, goals and profile are saved in the current browser only; there is no account sync or secure cloud backup.
- Money Coach uses local rules, not a connected AI model.
- There is no real receipt scanning, user authentication, payment processing, live bank/mobile-money connection, ad network or push notification service.
- Marketplace and Invest are coming-soon pages. Invest does not accept money, offer investments or promise returns.

Add a secure backend, privacy/security controls, tests, and legal review before production or any financial, advertising, payment or investment integrations.
