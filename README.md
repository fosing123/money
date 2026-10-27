# Student Money — prototype

A mobile-first, installable web prototype for student money management in Cameroon. The permanent Cameroonian-language brand name is intentionally undecided; “Student Money” is a temporary working label, not the final brand.

## MVP
- Friendly first-run onboarding
- FCFA balance and spending overview
- Log income and expenses
- Local budget and savings goals
- Rule-based money helper (not a connected AI model)
- Campus Marketplace and Invest coming-soon pages
- Responsive, browser-based experience with a basic cached app shell for repeat/offline opening

## Preview locally
This repository is a no-build static website. Download or clone it, then open `index.html` in a browser. For a local server, run `python -m http.server 8000` in the repository directory and open `http://localhost:8000`.

## Deploy
GitHub Pages can host the static prototype for free: open **Settings → Pages**, choose **Deploy from a branch**, select `main` and `/ (root)`, then save. The site will be available at the URL GitHub provides after deployment. Alternatively, drag the repository into Netlify or import it into Vercel.

## Data and safety
All prototype data stays in the current browser using local storage. There is no account sync, server, bank/mobile-money connection, real AI API, advertising network or payment processing. The Invest page does not accept funds or offer investments. Do not store secrets in browser code. Add a secure backend, privacy disclosures, accessibility checks and legal review before a public launch.

## Next steps
1. Test the onboarding and expense logging with 5–10 students.
2. Validate which features students use repeatedly.
3. Choose the permanent brand name.
4. Add authentication and secure cloud sync only after the core experience is validated.
5. Connect a real AI provider through a backend, with privacy and cost controls.
6. Review advertising, payment and investment regulations before integrating those products.