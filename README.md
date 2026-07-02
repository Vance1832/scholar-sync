# ScholarSync

A full-stack scholarship management platform that connects students with donors — built around the real-world workflow of applying, reviewing, and disbursing scholarship funds, not just a CRUD demo.

**Live app:** [scholar-sync-bext.onrender.com](https://scholar-sync-bext.onrender.com)

---

## Why this exists

Most scholarship-management tutorials stop at "student applies, admin approves." Real scholarship programs need more: proof that a student actually qualifies, a paper trail for *why* they were selected, and accountability for the money — donors shouldn't be able to mark an award "paid" without a transfer reference, and students shouldn't have funds sent without confirming their own payment details first.

ScholarSync models that full lifecycle.

## Features

**Public site (no account required)**
- Marketing landing page with live platform stats, featured scholarships, how-it-works, donor pitch, and FAQ
- Browse and search all open scholarships before signing up — filter by category, application effort, and minimum amount; sort by deadline, amount, or recency
- SEO-friendly public detail pages with a login-gated "Apply" that returns you to the application after sign-in

**For students**
- **Match score on every scholarship** — your profile (GPA, major) is checked against each scholarship's criteria and shown as a percentage, so you never waste an essay on an award you can't win. Sort by "Best match."
- **Saved scholarships** — bookmark awards with one click and come back to them from a dedicated Saved page
- Browse scholarships as cards (amount, deadline urgency, effort level, category, eligibility at a glance)
- Apply with a structured form — personal statement, financial need, and intended use of funds (not a single free-text box)
- Track every application through a visual pipeline: Submitted → Under Review → Shortlisted → Decision
- Accept an award and submit payment details before any money moves
- Dashboard shows total dollar amount still available to apply for

**For donors**
- Create scholarships with eligibility criteria (GPA, major, financial need), a category, and an application-effort level (quick apply / essay / detailed)
- Review applicants with a private 1–5 star rating and internal notes — never visible to students
- Shortlist top candidates before making a final decision
- Two-step disbursement: initiate transfer with recipient account details → confirm with a transaction reference and proof. No award can be marked "paid" without both steps.
- Dashboard shows total amount actually disbursed and to how many scholars

**For admins**
- System-wide oversight of students, donors, scholarships, and applications
- Audit log of every approval, rejection, shortlist, and payment action with actor and timestamp
- Suspend/reactivate user accounts
- Hidden, unlisted admin login — not exposed on the public-facing login page

**Platform-wide**
- Role-based access control (student / donor / admin) enforced at the route level, not just hidden in the UI
- Email notifications at every status change (application received, shortlisted, awarded, rejected, payment confirmed) via Flask-Mail
- Profile-completion gates — students/donors can't apply or post scholarships until their profile is complete
- Expired scholarships automatically filtered from student browse
- Custom 403/404/500 error pages

## Tech Stack

- **Backend:** Flask 3, SQLAlchemy 2 (PostgreSQL in production, SQLite in dev)
- **Auth:** Flask-Login, Flask-WTF (CSRF protection)
- **Email:** Flask-Mail (Gmail SMTP)
- **Frontend:** Server-rendered Jinja2 templates, hand-written CSS (no framework) — slate/neutral design system
- **Deployment:** Render, Gunicorn

## Architecture

```
app/
├── main/         # public marketing site: landing, browse, detail (no login)
├── auth/         # login, register (student/donor role tabs), unlisted admin login
├── student/      # browse with match scores & filters, save, apply, track, accept awards
├── donor/        # create scholarships, review applicants, disbursement
├── admin/        # oversight, audit log, user management
├── models/       # SQLAlchemy models
├── services/     # business logic (eligibility & match scoring, review, disbursement, email, audit)
├── seed_demo.py  # realistic demo data (flask seed-demo)
├── templates/    # Jinja2 templates, organized by role (+ public/)
└── static/       # CSS/JS — main.css (app shell) + public.css (marketing)
```

Business logic lives in `services/`, not in routes — application approval, disbursement state transitions, and eligibility checks are all testable, role-agnostic functions.

## Running locally

```bash
git clone https://github.com/Vance1832/scholar-sync.git
cd scholar-sync/scholarsync
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # then edit SECRET_KEY etc.

flask run --port 5001                # FLASK_APP is set via .flaskenv
```

Visit `http://localhost:5001` — SQLite database is created automatically on first run.

### Demo data

Populate the app with realistic donors, scholarships, students, and applications so every page has something to show:

```bash
flask seed-demo
```

This creates 4 donor organizations, 12 scholarships across categories, and 3 students with applications in every review state. All demo accounts use password `demo1234` (e.g. student `devon_r`, donor `hartwell`).

### Optional: enable email notifications

Add to `.env`:
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_DEFAULT_SENDER=ScholarSync <your@gmail.com>
```
Without these, the app runs normally and silently skips sending email.

## Try it out

Student and donor accounts are self-serve — visit the [live app](https://scholar-sync-bext.onrender.com), pick a role on the welcome screen, and register. The admin account is seeded automatically:

| Role | Username | Password |
|------|----------|----------|
| Admin | _(unlisted login at `/admin/login`)_ | `admin` / `admin123` |

## License

MIT
