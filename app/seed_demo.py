"""
Demo data seeding — `flask seed-demo`.

Creates realistic donors, scholarships, students, applications, and awards
so the platform demos well (landing-page stats, populated browse pages,
review queues with real-looking content). Idempotent: skips if demo data
already exists.
"""
from datetime import date, timedelta
from .extensions import db
from .models.user import User
from .models.student import Student
from .models.donor import Donor
from .models.scholarship import Scholarship, EligibilityCriteria
from .models.application import Application
from .models.award import Award

DEMO_PASSWORD = "demo1234"

DONORS = [
    ("hartwell", "Hartwell Foundation", "Corporate Foundation", "grants@hartwell.org"),
    ("brightpath", "BrightPath Trust", "Non-Profit", "hello@brightpath.org"),
    ("nguyen_fund", "The Nguyen Family Fund", "Individual", "fund@nguyenfamily.com"),
    ("techforward", "TechForward Initiative", "Organization", "apply@techforward.io"),
]

# (donor_idx, title, amount, days_to_deadline, category, effort, slots,
#  min_gpa, required_major, need_based, criterion_text, description)
SCHOLARSHIPS = [
    (0, "Hartwell STEM Excellence Award", 10000, 45, "STEM", "essay", 2, "3.50", "Computer Science", False, None,
     "Awarded to outstanding students pursuing computer science who demonstrate exceptional academic performance and a passion for solving real-world problems with technology.\n\nWinners join the Hartwell alumni network with access to mentorship and internship pipelines."),
    (0, "Hartwell Women in Engineering Grant", 7500, 30, "STEM", "detailed", 1, "3.20", "Engineering", False, "Open to women and non-binary students",
     "Supporting the next generation of engineers. This grant covers tuition and provides a summer research stipend at a partner university lab."),
    (1, "BrightPath First-Generation Scholars", 5000, 21, "First-Generation", "essay", 3, "3.00", None, True, "Must be the first in your family to attend college",
     "BrightPath believes the first step is the hardest. This award supports first-generation college students with demonstrated financial need — funding plus a dedicated success coach for your first year."),
    (1, "BrightPath Community Impact Award", 2500, 14, "Community Service", "easy", 4, None, None, False, "100+ hours of documented community service",
     "A quick-apply award recognizing students who give back. Tell us where you volunteer and what it taught you — no essay required."),
    (1, "BrightPath Need-Based Completion Grant", 3000, 60, "Need-Based", "essay", 2, "2.50", None, True, None,
     "For students within two semesters of graduating who need a final push to cross the finish line. Priority given to applicants with unmet financial need."),
    (2, "Nguyen Family Healthcare Heroes Scholarship", 6000, 35, "Healthcare", "essay", 1, "3.30", "Nursing", False, None,
     "Established in honor of Dr. Linh Nguyen, this scholarship supports nursing students committed to serving underserved communities after graduation."),
    (2, "Nguyen Merit Award for the Arts", 4000, 50, "Arts & Humanities", "detailed", 1, "3.00", "Arts", False, "Portfolio submission required",
     "Celebrating creative excellence. Applicants submit a portfolio alongside a statement about how their work engages with their community."),
    (3, "TechForward Future Builders Scholarship", 8000, 28, "STEM", "essay", 2, "3.40", "Computer Science", False, None,
     "For builders who ship. Show us something you've made — an app, a research project, an open-source contribution — and tell us what you'd build next with fewer constraints."),
    (3, "TechForward Leadership in Tech Award", 5500, 40, "Leadership", "essay", 1, "3.25", None, False, "Must hold a leadership role in a student organization",
     "Technical skill matters, but so does bringing people along. This award recognizes students who lead teams, clubs, or communities in tech."),
    (3, "TechForward Quick Start Grant", 1500, 10, "Merit-Based", "easy", 5, "3.00", None, False, None,
     "A no-essay micro-grant for high-achieving students. Five winners selected each cycle — apply in under five minutes."),
    (2, "Nguyen Business Futures Scholarship", 4500, 55, "Business", "essay", 1, "3.10", "Business Administration", False, None,
     "Supporting aspiring entrepreneurs and business leaders who plan to build companies that matter."),
    (1, "BrightPath Student Athlete Award", 3500, 25, "Athletics", "easy", 2, "2.75", None, False, "Must be on a varsity or club athletic roster",
     "Balancing training and coursework is its own achievement. A quick-apply award for student athletes in good academic standing."),
]

STUDENTS = [
    ("maya_t", "Maya", "Torres", "Nursing", "3.72", "Junior", "maya.torres@example.edu"),
    ("devon_r", "Devon", "Reyes", "Computer Science", "3.85", "Senior", "devon.reyes@example.edu"),
    ("aisha_k", "Aisha", "Khan", "Engineering", "3.41", "Sophomore", "aisha.khan@example.edu"),
]


def seed_demo() -> None:
    if Donor.query.filter(Donor.name.in_([d[1] for d in DONORS])).first():
        print("Demo data already present — nothing to do.")
        return

    donors = []
    for username, name, dtype, email in DONORS:
        user = User(username=username, role="donor")
        user.set_password(DEMO_PASSWORD)
        db.session.add(user)
        db.session.flush()
        profile = Donor(
            user_id=user.id,
            donor_code=f"DONOR-{user.id:04d}",
            name=name,
            donor_type=dtype,
            contact_email=email,
            profile_completed=True,
        )
        db.session.add(profile)
        db.session.flush()
        donors.append(profile)

    scholarships = []
    for (d_idx, title, amount, days, category, effort, slots,
         min_gpa, major, need_based, criterion, desc) in SCHOLARSHIPS:
        sch = Scholarship(
            donor_id=donors[d_idx].id,
            title=title,
            description=desc,
            amount=amount,
            deadline=date.today() + timedelta(days=days),
            is_active=True,
            slots=slots,
            category=category,
            effort_level=effort,
        )
        db.session.add(sch)
        db.session.flush()
        if min_gpa or major or need_based or criterion:
            db.session.add(EligibilityCriteria(
                scholarship_id=sch.id,
                min_gpa=min_gpa,
                required_major=major,
                need_based=need_based,
                criterion_text=criterion,
            ))
        scholarships.append(sch)

    students = []
    for username, first, last, major, gpa, year, email in STUDENTS:
        user = User(username=username, role="student")
        user.set_password(DEMO_PASSWORD)
        db.session.add(user)
        db.session.flush()
        profile = Student(
            user_id=user.id,
            student_code=f"STUD-{user.id:04d}",
            first_name=first,
            last_name=last,
            email=email,
            major=major,
            gpa=gpa,
            academic_year=year,
            profile_completed=True,
        )
        db.session.add(profile)
        db.session.flush()
        students.append(profile)

    # Applications in every review state, so donor queues and student
    # dashboards have something to show.
    maya, devon, aisha = students
    healthcare = scholarships[5]
    stem = scholarships[0]
    builders = scholarships[7]
    quick = scholarships[9]
    firstgen = scholarships[2]

    apps = [
        Application(student_id=maya.id, scholarship_id=healthcare.id, status="approved",
                    personal_statement="I grew up translating hospital paperwork for my grandmother. Nursing is how I turn that experience into a career of advocacy for patients who feel unheard.",
                    financial_need="I work 20 hours a week to cover rent while carrying a full course load.",
                    intended_use="Tuition for my final two semesters and NCLEX preparation."),
        Application(student_id=devon.id, scholarship_id=stem.id, status="shortlisted", star_rating=5,
                    personal_statement="I maintain an open-source scheduling library used by three student-run clinics. I want to spend my career building infrastructure for care, not ads.",
                    financial_need="Partial — my aid package covers tuition but not materials.",
                    intended_use="A development laptop and conference travel."),
        Application(student_id=devon.id, scholarship_id=builders.id, status="pending",
                    personal_statement="Last summer I built an SMS-based flood alert system for my hometown. Next: making it work without cell coverage.",
                    financial_need="Moderate.",
                    intended_use="Hardware for a mesh-network prototype."),
        Application(student_id=aisha.id, scholarship_id=quick.id, status="pending",
                    personal_statement="Sophomore engineering student, 3.41 GPA, robotics team lead.",
                    financial_need="Books and lab fees.",
                    intended_use="Lab fees for the spring semester."),
        Application(student_id=aisha.id, scholarship_id=firstgen.id, status="rejected",
                    rejection_reason="Strong application, but this cycle prioritized applicants within one year of graduation.",
                    personal_statement="First in my family to attend university. My parents run a small grocery store and I intend to make their sacrifice count.",
                    financial_need="High — I receive no family support for tuition.",
                    intended_use="Next semester's tuition balance."),
    ]
    db.session.add_all(apps)
    db.session.flush()

    # A completed award so "total awarded" on the landing page is non-zero.
    db.session.add(Award(
        application_id=apps[0].id,
        amount=healthcare.amount,
        payment_status="completed",
        payment_method="Bank Transfer",
        payment_reference="TXN-2026-0142",
        student_accepted=True,
        disbursement_date=date.today() - timedelta(days=7),
    ))

    db.session.commit()
    print(f"Seeded {len(donors)} donors, {len(scholarships)} scholarships, "
          f"{len(students)} students, {len(apps)} applications, 1 award.")
    print(f"Demo logins — donors: {', '.join(d[0] for d in DONORS)}; "
          f"students: {', '.join(s[0] for s in STUDENTS)} (password: {DEMO_PASSWORD})")
