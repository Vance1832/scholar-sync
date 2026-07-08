from app.services.scholarship import filter_open_scholarships


class TestFilterOpenScholarships:
    def test_excludes_inactive_and_expired(self, make_scholarship, db):
        active = make_scholarship(title="Active", days=10)
        make_scholarship(title="Inactive", days=10, is_active=False)
        # Bypass validation to create an already-expired scholarship
        expired = make_scholarship(title="Expired", days=5)
        from datetime import date, timedelta
        expired.deadline = date.today() - timedelta(days=1)
        db.session.commit()

        results = filter_open_scholarships()
        titles = [s.title for s in results]
        assert titles == ["Active"]
        assert active in results

    def test_search_matches_title_and_description(self, make_scholarship, db):
        sch = make_scholarship(title="STEM Excellence")
        other = make_scholarship(title="Arts Award")
        other.description = "for stem-adjacent artists"
        db.session.commit()

        assert {s.id for s in filter_open_scholarships(q="stem")} == {sch.id, other.id}
        assert [s.id for s in filter_open_scholarships(q="excellence")] == [sch.id]

    def test_category_filter(self, make_scholarship):
        stem = make_scholarship(title="A", category="STEM")
        make_scholarship(title="B", category="Business")
        assert [s.id for s in filter_open_scholarships(category="STEM")] == [stem.id]

    def test_min_amount_filter(self, make_scholarship):
        make_scholarship(title="Small", amount=1000)
        big = make_scholarship(title="Big", amount=8000)
        assert [s.id for s in filter_open_scholarships(min_amount=5000)] == [big.id]

    def test_sort_by_amount_desc(self, make_scholarship):
        make_scholarship(title="Small", amount=1000)
        make_scholarship(title="Big", amount=9000)
        results = filter_open_scholarships(sort="amount")
        assert [s.title for s in results] == ["Big", "Small"]

    def test_sort_by_deadline_puts_no_deadline_last(self, make_scholarship):
        make_scholarship(title="NoDeadline", days=None)
        make_scholarship(title="Soon", days=3)
        results = filter_open_scholarships(sort="deadline")
        assert [s.title for s in results] == ["Soon", "NoDeadline"]
