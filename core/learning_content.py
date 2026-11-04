"""Original editorial content for the public TIANA Learn library.

Keep this content practical, locally relevant and educational. It is deliberately
separate from private member finance data and does not require database migrations.
"""

EDITORIAL_UPDATED = "4 November 2026"
EDITORIAL_BYLINE = "TIANA Learn Editorial Team"

ARTICLES = [
    {
        "slug": "student-budget-that-works",
        "category": "Budgeting",
        "category_slug": "budgeting",
        "title": "Build a student budget that works with real life",
        "summary": "A flexible weekly plan for allowances, school costs, food, transport, data and the unexpected.",
        "reading_time": "7 min read",
        "featured": True,
        "intro": (
            "A useful student budget is not a perfect spreadsheet. It is a simple plan for the money "
            "you can reasonably expect, the expenses you cannot ignore and the choices you can still control. "
            "The best plan is one you can update when a week does not go as expected."
        ),
        "sections": [
            {
                "heading": "Start with money you can count on",
                "paragraphs": [
                    "Write down the amount you reliably receive and when it normally arrives. Separate confirmed income from money that might arrive later, such as a promised gift, an occasional job or a transfer that has not yet been sent. Build the first version of your budget around the reliable amount.",
                    "If your allowance changes from week to week, use a conservative estimate rather than your best week. When extra money arrives, decide deliberately whether it should cover an upcoming cost, strengthen savings or remain as a buffer."
                ],
                "bullets": [
                    "Record the amount and expected date of each reliable source.",
                    "Do not count a loan, an unconfirmed promise or money that has not arrived as available cash.",
                    "Keep a note of one-off income so it does not become an assumed weekly allowance."
                ]
            },
            {
                "heading": "Separate needs, commitments and flexible spending",
                "paragraphs": [
                    "List the costs that keep your school week functioning: meals, transport, mobile data or airtime, learning materials and any agreed household or school contribution. Add regular commitments next. Only then decide how much can go toward entertainment, snacks or other optional purchases.",
                    "The categories will look different for every student. A student who walks to campus may spend less on transport but more on data or printing. Your own records should guide the amounts; a budget copied from somebody else may not fit your life."
                ],
                "bullets": [
                    "Essentials: costs you need to meet to study and live safely.",
                    "Commitments: bills or contributions you have already agreed to pay.",
                    "Flexible spending: purchases you can reduce, delay or replace.",
                    "Savings and buffer: money assigned to a goal or kept for a surprise."
                ]
            },
            {
                "heading": "Give every franc a job without budgeting twice",
                "paragraphs": [
                    "Once the categories are listed, assign amounts that add up to the money available. Check the total before you start spending. If the plan is larger than your income, adjust it now: reduce a flexible category, change the savings amount temporarily or revisit a cost that can be planned for over several weeks.",
                    "Avoid treating the same money as both savings and spending money. When you set aside an amount for a goal, record it as committed. Your remaining balance should reflect what is genuinely available."
                ],
                "bullets": [
                    "Write down the starting balance.",
                    "Assign amounts to essentials and commitments first.",
                    "Choose a realistic savings contribution.",
                    "Leave a small unassigned buffer when possible.",
                    "Confirm that the planned categories do not exceed the money available."
                ]
            },
            {
                "heading": "Review the plan once a week",
                "paragraphs": [
                    "A budget is a working document, not a punishment. At the end of the week, compare what you planned with what happened. Look for patterns rather than blaming yourself for one unusual day. Did transport cost more because of rain? Did a school activity require extra printing? Is a category consistently underestimated?",
                    "Make one or two changes for the next week. Small corrections are easier to maintain than a complete redesign every few days."
                ],
                "bullets": [
                    "What went as expected?",
                    "Which cost surprised me, and is it likely to happen again?",
                    "What can I change next week?",
                    "Did I protect the money I had already assigned to a goal?"
                ]
            }
        ],
        "takeaway": "A strong student budget starts with reliable income, protects essentials, gives savings a realistic place and gets reviewed regularly.",
        "related": ["save-on-a-small-income", "track-cash-and-mobile-money", "plan-for-unexpected-costs"]
    },
    {
        "slug": "save-on-a-small-income",
        "category": "Saving",
        "category_slug": "saving",
        "title": "How to save when your income is small or irregular",
        "summary": "Make saving repeatable with a clear target, a flexible contribution and a plan for uneven weeks.",
        "reading_time": "6 min read",
        "featured": False,
        "intro": (
            "Saving is not reserved for people with large salaries. For a student, the useful first step is "
            "to protect a small amount consistently when it is genuinely affordable. A realistic plan can "
            "be adjusted; an unrealistic one is often abandoned."
        ),
        "sections": [
            {
                "heading": "Give the goal a name and a date",
                "paragraphs": [
                    "A goal such as 'save more' is difficult to measure. Give the money a purpose: exam materials, a laptop repair, transport for a school activity or a personal emergency reserve. Write down the amount you need and the date you hope to reach it.",
                    "A deadline helps you decide whether the goal is realistic. It is also useful to separate an essential upcoming expense from a long-term wish. The two goals may need different timelines."
                ]
            },
            {
                "heading": "Calculate a contribution you can maintain",
                "paragraphs": [
                    "Use a simple calculation: amount still needed divided by the number of contribution periods remaining. If you need 24,000 FCFA over 12 weeks, the starting plan is 2,000 FCFA per week. This is an illustration, not a recommended amount for every student.",
                    "Compare the result with your real budget. If it would leave too little for food, transport, school or other essentials, extend the deadline or lower the target. Do not borrow or skip a necessary expense just to make a savings chart look good."
                ],
                "bullets": [
                    "Target amount minus money already saved equals the amount remaining.",
                    "Amount remaining divided by weeks remaining gives a possible weekly contribution.",
                    "Recheck the plan whenever your income or essential costs change."
                ]
            },
            {
                "heading": "Use a flexible rule for uneven income",
                "paragraphs": [
                    "When income is irregular, a fixed weekly amount may not work. You can set a small baseline for normal weeks and a percentage or optional top-up for weeks when more money arrives. Protect essential costs before making the extra contribution.",
                    "If a week is difficult, pause or reduce the contribution instead of using money needed for an immediate necessity. Record the change and update the target date so your plan stays honest."
                ]
            },
            {
                "heading": "Keep goal money separate in your records",
                "paragraphs": [
                    "You do not always need a separate bank account to make progress visible. A clear record can show the amount assigned to a goal, the date of each contribution and the remaining amount. If you keep money physically or digitally separate, check the provider's fees, access rules and safety features before relying on it.",
                    "Never share a Mobile Money PIN, password or one-time code with someone who says they need it to help you save. A genuine savings plan should not require you to disclose your secret credentials."
                ]
            },
            {
                "heading": "Celebrate progress without spending it twice",
                "paragraphs": [
                    "Track each contribution, even when it is small. A progress bar or written record can help you see that the habit is developing. When you reach the target, use the money for the purpose you chose and then decide what the next goal should be.",
                    "If you withdraw from the goal for a genuine emergency, record it and make a new plan. The purpose of saving is to give yourself options, not to create guilt."
                ]
            }
        ],
        "takeaway": "Choose a goal you can explain, calculate a contribution that leaves essentials covered, and adjust the deadline when life changes.",
        "related": ["student-budget-that-works", "plan-for-unexpected-costs", "track-cash-and-mobile-money"]
    },
    {
        "slug": "track-cash-and-mobile-money",
        "category": "Money habits",
        "category_slug": "money-habits",
        "title": "Track cash and Mobile Money without losing the full picture",
        "summary": "A simple routine for recording payments, transfers, fees and cash so your balance makes sense.",
        "reading_time": "7 min read",
        "featured": False,
        "intro": (
            "Money can move through cash, bank accounts and Mobile Money during the same day. If you only "
            "check one balance, it is easy to forget a transfer, fee or cash purchase. A consistent record "
            "helps you understand what you have without sharing private account details."
        ),
        "sections": [
            {
                "heading": "Record the movement, not just the final balance",
                "paragraphs": [
                    "When money comes in or goes out, record the date, amount, direction and a short description. Add a category such as food, transport, data, school materials or savings. You do not need a long story for every purchase; the purpose is to recognise the transaction later.",
                    "For a transfer between two accounts you control, record it as money moving from one place to another, not as new income. Otherwise your records may count the same money twice."
                ],
                "bullets": [
                    "Date and amount.",
                    "Whether it was income, an expense or a transfer.",
                    "Which cash or digital account was involved.",
                    "A short description and a useful category.",
                    "Any fee charged by the provider."
                ]
            },
            {
                "heading": "Keep cash and digital balances distinct",
                "paragraphs": [
                    "A wallet balance is not the same thing as cash in your pocket. Keep each location separate in your notes or finance app. When you withdraw cash, record the transfer from the digital wallet to cash. When you spend that cash later, record the expense from the cash balance.",
                    "This makes it easier to check whether a balance is missing because of an unrecorded purchase or because money is sitting in a different place."
                ]
            },
            {
                "heading": "Check receipts and fees",
                "paragraphs": [
                    "After a digital transaction, check the confirmation message or transaction history in the official application. Compare the amount sent, the amount received and any fee shown. If a message looks unusual, do not follow a link in it automatically; open the official app or contact the provider through a support channel you already trust.",
                    "Keep only the details you need for your records. Never copy a PIN, password, full one-time code or recovery code into a budget note."
                ]
            },
            {
                "heading": "Reconcile once a week",
                "paragraphs": [
                    "Choose a regular time to compare your recorded balances with the balances shown by your providers and the cash you can count. If something does not match, review the most recent transactions first. Look for a forgotten snack, a fee, a delayed transfer or a duplicated entry.",
                    "Correct the record with a note rather than silently changing an old transaction. A short explanation makes future reviews easier."
                ]
            },
            {
                "heading": "Protect the record itself",
                "paragraphs": [
                    "Use a screen lock on your phone and avoid leaving financial records open on a shared device. Sign out when using a public or borrowed device. If you export a file for your own backup, store it somewhere private and delete copies from devices you no longer control.",
                    "A finance tracker should help you understand your habits. It should not require you to publish screenshots of balances or transaction messages to prove that you have money."
                ]
            }
        ],
        "takeaway": "Record cash and digital activity separately, treat your own-account transfers as transfers, and reconcile your balances every week.",
        "related": ["student-budget-that-works", "mobile-money-safety-checklist", "save-on-a-small-income"]
    },
    {
        "slug": "mobile-money-safety-checklist",
        "category": "Digital safety",
        "category_slug": "digital-safety",
        "title": "A practical safety checklist for Mobile Money",
        "summary": "Recognise pressure tactics, protect secret codes and verify transactions through official channels.",
        "reading_time": "8 min read",
        "featured": False,
        "intro": (
            "Digital payments are convenient, but a convincing message or urgent phone call can still trick "
            "someone into revealing a secret code or approving the wrong transaction. Slow down, verify the "
            "request and keep control of your account credentials."
        ),
        "sections": [
            {
                "heading": "Treat secret codes as private",
                "paragraphs": [
                    "Your PIN, password, one-time password and account recovery codes are secrets. Do not share them with a caller, a person claiming to be support, a buyer, a seller or someone offering to reverse a payment. A person who asks for your secret code is asking for access that should remain yours.",
                    "A legitimate support process should not require you to tell another person your PIN. If you are unsure, end the conversation and contact your provider using the support details in its official app or on its verified website."
                ]
            },
            {
                "heading": "Be careful with urgent stories and unexpected links",
                "paragraphs": [
                    "Scammers often create pressure: an account will supposedly be blocked in minutes, a prize will disappear, a transfer must be reversed immediately or a relative is in trouble. Urgency makes it harder to check the facts. Pause before acting.",
                    "Do not open unexpected links to 'unlock' an account or confirm a prize. Open the provider's official app yourself or type the known website address into the browser. Check the sender carefully; a familiar display name does not prove that a message is genuine."
                ],
                "bullets": [
                    "Unexpected prize or giveaway messages.",
                    "Requests to pay a fee before receiving a reward.",
                    "A caller asking you to read out a one-time code.",
                    "A stranger asking you to install a screen-sharing or remote-control app.",
                    "A screenshot presented as proof while the actual transaction is missing from your history."
                ]
            },
            {
                "heading": "Verify before confirming a payment",
                "paragraphs": [
                    "Before entering your PIN, check the amount, recipient name or number and any fee displayed by the official payment flow. A single wrong digit can send money to the wrong person. Do not rely only on a screenshot sent by someone else.",
                    "After you complete a transfer, check your own transaction history or confirmation from the provider. Save the transaction reference privately if you may need it for a dispute."
                ]
            },
            {
                "heading": "Secure the phone and accounts around the wallet",
                "paragraphs": [
                    "Use a device screen lock, keep the operating system and official payment apps updated, and avoid installing applications from unknown links. Do not lend an unlocked phone to someone who wants to 'help' with a payment. Use a different strong password for important accounts where possible.",
                    "If your SIM or phone is lost, contact the mobile operator through its official channel as soon as possible and ask how to secure the line and wallet. Change credentials for accounts that may have been exposed."
                ]
            },
            {
                "heading": "What to do when something seems wrong",
                "paragraphs": [
                    "Stop sending money and do not share additional codes. Contact the provider immediately through its official support channel, explain what happened and provide the transaction reference if one exists. Ask whether the account or SIM can be secured and what dispute process is available.",
                    "Keep relevant messages and records, but do not post private screenshots publicly. If you believe a crime occurred, consider reporting it to the appropriate local authority. Fast reporting may help the provider investigate, but no reversal can be guaranteed."
                ]
            }
        ],
        "takeaway": "Never disclose your secret codes, ignore pressure to act instantly, and verify every payment in your own official transaction history.",
        "related": ["track-cash-and-mobile-money", "student-budget-that-works", "plan-for-unexpected-costs"]
    },
    {
        "slug": "plan-for-unexpected-costs",
        "category": "Planning",
        "category_slug": "planning",
        "title": "Build a small emergency buffer on a student budget",
        "summary": "Prepare for phone repairs, unexpected travel or school expenses without confusing a buffer with everyday spending.",
        "reading_time": "6 min read",
        "featured": False,
        "intro": (
            "An emergency buffer is money reserved for an expense you did not plan for but may need to handle. "
            "It does not have to start large. The first purpose is to create a little breathing room so one "
            "surprise does not immediately disrupt food, transport or school needs."
        ),
        "sections": [
            {
                "heading": "Choose what counts as an emergency",
                "paragraphs": [
                    "Examples might include an urgent phone repair needed for school communication, unexpected transport for a family situation or an essential learning material that cannot wait. A planned outing or a regular data bundle is not an emergency simply because it was forgotten in the budget.",
                    "Writing down a few examples helps you protect the buffer for genuine surprises. If you repeatedly use it for the same predictable cost, that cost probably belongs in your normal budget."
                ]
            },
            {
                "heading": "Start with a milestone you can reach",
                "paragraphs": [
                    "Pick a first milestone that is small enough to build without missing essentials. It could be the cost of one necessary journey, a basic replacement item or another realistic local expense. The right amount depends on your situation; there is no universal number.",
                    "Once you reach the first milestone, you can decide whether to build toward a larger reserve. Do not compare your starting point with someone else's savings balance."
                ]
            },
            {
                "heading": "Make the contribution flexible",
                "paragraphs": [
                    "If your income is reliable, a small regular contribution may work. If it changes, use a minimum you can normally maintain and add more only when essentials are already covered. It is fine to contribute less or pause during a difficult week.",
                    "Keep the buffer visible in your records. Label it clearly so you do not accidentally treat it as money available for everyday purchases."
                ]
            },
            {
                "heading": "Decide where the money should sit",
                "paragraphs": [
                    "Think about how quickly you may need access, what fees apply, what happens if your phone is lost and what security controls the provider offers. The best place is one you can access safely and understand. Do not put emergency money into an investment or product whose value can fall or whose withdrawal is restricted unless you fully understand those risks.",
                    "Avoid keeping secret credentials with another person. If you use a digital wallet, protect the SIM, device and account access."
                ]
            },
            {
                "heading": "Use the buffer, then rebuild it",
                "paragraphs": [
                    "When an eligible surprise happens, record the amount and what it covered. Afterward, return to your normal budget and choose a contribution to rebuild the reserve when you can. Do not create debt or skip necessary costs just to restore it immediately.",
                    "Review the target when your circumstances change. A new school term, new transport route or different allowance may change what a useful buffer looks like."
                ]
            }
        ],
        "takeaway": "Start with a reachable milestone, keep the reserve distinct from spending money, and rebuild it gradually after a real emergency.",
        "related": ["student-budget-that-works", "save-on-a-small-income", "track-cash-and-mobile-money"]
    },
    {
        "slug": "plan-school-week-costs",
        "category": "Student life",
        "category_slug": "student-life",
        "title": "Plan for the real cost of a school week",
        "summary": "Bring meals, transport, data, printing and small campus purchases into one clear weekly plan.",
        "reading_time": "6 min read",
        "featured": False,
        "intro": (
            "Small purchases can quietly use up a student allowance. The solution is not to remove every "
            "pleasure from the week; it is to understand the costs that repeat, prepare for the ones that "
            "change and make trade-offs before the money is gone."
        ),
        "sections": [
            {
                "heading": "Map a normal school week",
                "paragraphs": [
                    "Write down the days you attend classes and the journeys you normally make. Add meals or snacks you usually buy, expected data or airtime, printing, stationery and any regular group contribution. Use your own recent spending records rather than guessing from memory.",
                    "Separate daily expenses from weekly or monthly purchases. A notebook bought once should not be treated like a daily snack, but its cost still needs a place in the plan."
                ]
            },
            {
                "heading": "Prepare for costs that change",
                "paragraphs": [
                    "Some weeks are different: an assignment may need printing, a class may finish later than expected or transport may cost more because your route changes. Look at the school calendar and upcoming deadlines before the week begins.",
                    "Where possible, keep a small buffer for these variations. If there is no room for a buffer, identify which flexible purchase you would reduce first rather than borrowing automatically."
                ]
            },
            {
                "heading": "Compare the full cost, not only the headline price",
                "paragraphs": [
                    "A cheaper option is not always cheaper overall. Consider travel required to reach it, data used to access it, service fees, durability and the time it takes. When comparing data bundles or transport choices, use the details shown by the provider and avoid assuming that a promotion is always available.",
                    "For recurring purchases, note what you actually use. Buying more than you can use before expiry may waste money even when the advertised unit price looks lower."
                ]
            },
            {
                "heading": "Choose a weekly check-in",
                "paragraphs": [
                    "At the end of the week, total your spending by category. Find one pattern worth changing, such as buying data in several small top-ups or making an unplanned journey. Choose a practical adjustment for the next week.",
                    "Do not make a plan that depends on being perfect. A good routine lets you record a missed expense, correct the numbers and continue."
                ]
            }
        ],
        "takeaway": "Use your own school timetable and spending history to plan recurring costs, prepare for deadline weeks and adjust one habit at a time.",
        "related": ["student-budget-that-works", "track-cash-and-mobile-money", "save-on-a-small-income"]
    }
]

ARTICLES_BY_SLUG = {article["slug"]: article for article in ARTICLES}


def get_article(slug):
    """Return a published article by its stable URL slug."""
    return ARTICLES_BY_SLUG.get(slug)


def get_related_articles(article, limit=3):
    """Return related published articles while preserving editorial order."""
    related = []
    for slug in article.get("related", []):
        candidate = get_article(slug)
        if candidate and candidate["slug"] != article["slug"]:
            related.append(candidate)
        if len(related) >= limit:
            break
    return related
