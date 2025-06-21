🔒 **Important:** This project follows strict development rules.  
Please read [`project-rules.md`](./project-rules.md) before editing anything.

Put a short banner at the top of each file that should not be refactored or touched lightly — especially:

app.py

startup.py

core/app_factory.py (or similar)

.replit

replit.nix

# ⚠️ WARNING: This file is production-critical.
# Do not refactor, delete, or modularize without explicit approval.
# Read project-rules.md before making changes.

# ⚠️ DO NOT MODIFY THIS CONFIG unless you're 100% sure.
# See project-rules.md for instructions.


📜 Replit Development Rules & Instructions
(For AI agents, team members, or collaborators working inside Replit)

✅ 1. Respect the Existing File Structure
Do not restructure, rename, or flatten files (e.g., app.py, startup.py, core/) unless explicitly instructed.

If a file like app.py is long but working, it stays that way until we agree on modularizing it.

✅ 2. No Auto-Deletions or Mass Overwrites
Do not delete or "move" critical logic without:

Approval

Explanation

A rollback plan

If a feature requires multiple file changes — do it gradually, with commit points.

✅ 3. All Changes Must Be Gradual & Measured
No “big bang” refactors. Break changes into small, testable commits.

Add new features next to existing logic unless told to fully replace it.

Example:
Adding auth logic? Don’t move the entire login flow into 5 new modules. Start with one.

✅ 4. Every Change Must Be Reversible

Before major edits, create a backup:
git checkout -b backup-before-feature-x

If anything breaks, I must be able to:
git checkout main

Instant rollback — no guessing.


### ✅ 5. Dependency Management

- All dependencies must be added to `requirements.txt` **manually and explicitly**.
- Do **not** run inline `pip install` commands inside `.replit` or during runtime.
- If you add a new package:
  - Verify it installs cleanly via `pip install -r requirements.txt`
  - Lock its version if possible (`package==x.y.z`)
  - Add a comment in the file if it’s critical or tricky

Example:
```txt
fpdf2==2.8.3      # Required for PDF reports
fpdf              # [⚠️ Consider removing — likely a legacy/duplicate entry]


✅ 6. Replit-specific Config Must Be Protected
Only touch .replit or replit.nix if explicitly requested

Any change must:

Be commented

Not trigger Recovery Mode

Include a backup version

✅ 7. Every Feature or Refactor Must Be Justified
For each pull request, push, or AI update:

What did you change?

Why was it needed?

Where is the logic now?

What was removed (if anything)?

If that can’t be answered — don’t push it.

✅ 8. Ask Before Acting
If you're not sure whether to:

Rename a function

Move a file

Strip 3,000 lines from app.py...

Ask. First.

📌 Final Reminder
The goal is to make the app better — not different for the sake of difference.
Respect what's already working, and build like you're not the only one reading the code.

