from app.services.eligibility import check_eligibility, eligibility_summary, match_score


class TestMatchScore:
    def test_no_profile_returns_none(self, make_scholarship):
        sch = make_scholarship(min_gpa="3.00")
        assert match_score(None, sch) is None

    def test_no_criteria_is_full_match(self, student, make_scholarship):
        sch = make_scholarship()
        assert match_score(student, sch) == 100

    def test_all_criteria_met(self, student, make_scholarship):
        sch = make_scholarship(min_gpa="3.50", required_major="Computer Science")
        assert match_score(student, sch) == 100

    def test_half_criteria_met(self, student, make_scholarship):
        # GPA 3.60 passes, major fails
        sch = make_scholarship(min_gpa="3.00", required_major="Nursing")
        assert match_score(student, sch) == 50

    def test_no_criteria_met(self, student, make_scholarship):
        sch = make_scholarship(min_gpa="3.90", required_major="Nursing")
        assert match_score(student, sch) == 0

    def test_any_major_ignored(self, student, make_scholarship):
        sch = make_scholarship(min_gpa="3.00", required_major="Any Major")
        assert match_score(student, sch) == 100


class TestCheckEligibility:
    def test_eligible_when_criteria_met(self, student, make_scholarship):
        sch = make_scholarship(min_gpa="3.50", required_major="Computer Science")
        eligible, reasons = check_eligibility(student, sch)
        assert eligible and reasons == []

    def test_gpa_failure_gives_reason(self, student, make_scholarship):
        sch = make_scholarship(min_gpa="3.90")
        eligible, reasons = check_eligibility(student, sch)
        assert not eligible
        assert any("GPA" in r for r in reasons)

    def test_major_comparison_case_insensitive(self, student, make_scholarship):
        sch = make_scholarship(required_major="computer science")
        eligible, _ = check_eligibility(student, sch)
        assert eligible


class TestEligibilitySummary:
    def test_incomplete_profile(self, make_scholarship):
        sch = make_scholarship()
        summary = eligibility_summary(None, sch)
        assert summary["eligible"] is None
        assert summary["match_pct"] is None

    def test_summary_includes_match_pct(self, student, make_scholarship):
        sch = make_scholarship(min_gpa="3.00")
        summary = eligibility_summary(student, sch)
        assert summary["eligible"] is True
        assert summary["match_pct"] == 100
