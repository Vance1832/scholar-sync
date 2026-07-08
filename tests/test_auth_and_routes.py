from app.services.auth import register_user, authenticate


class TestAuthService:
    def test_register_creates_role_profile(self, db):
        ok, msg = register_user("newstudent", "secret123", "secret123", "student")
        assert ok, msg
        from app.models.user import User
        user = User.query.filter_by(username="newstudent").one()
        assert user.role == "student"
        assert user.student_profile is not None
        assert user.student_profile.student_code.startswith("STUD-")

    def test_duplicate_username_rejected(self, db):
        register_user("dupe", "secret123", "secret123", "student")
        ok, msg = register_user("dupe", "secret123", "secret123", "donor")
        assert not ok and "taken" in msg.lower()

    def test_password_is_hashed(self, db):
        register_user("hashcheck", "secret123", "secret123", "student")
        from app.models.user import User
        user = User.query.filter_by(username="hashcheck").one()
        assert user.password_hash != "secret123"
        assert user.check_password("secret123")

    def test_authenticate_enforces_role(self, db):
        register_user("roled", "secret123", "secret123", "student")
        assert authenticate("roled", "secret123", "student") is not None
        assert authenticate("roled", "secret123", "donor") is None

    def test_suspended_user_blocked(self, db):
        register_user("banned", "secret123", "secret123", "student")
        from app.models.user import User
        user = User.query.filter_by(username="banned").one()
        user.is_active = False
        db.session.commit()
        assert authenticate("banned", "secret123", "student") == "suspended"


class TestPublicRoutes:
    def test_landing_page(self, client, make_scholarship):
        make_scholarship(title="Visible Award")
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Fund your future" in resp.data

    def test_public_browse_lists_scholarships(self, client, make_scholarship):
        make_scholarship(title="Public Browse Award")
        resp = client.get("/scholarships")
        assert resp.status_code == 200
        assert b"Public Browse Award" in resp.data

    def test_public_detail_page(self, client, make_scholarship):
        sch = make_scholarship(title="Detail Award")
        resp = client.get(f"/scholarships/{sch.id}")
        assert resp.status_code == 200
        assert b"Detail Award" in resp.data
        assert b"Sign in to apply" in resp.data

    def test_student_area_requires_login(self, client):
        resp = client.get("/student/dashboard")
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_old_welcome_redirects_home(self, client):
        resp = client.get("/welcome")
        assert resp.status_code == 302

    def test_login_rejects_external_next_redirect(self, client, db):
        register_user("redir", "secret123", "secret123", "student")
        resp = client.post(
            "/login?role=student&next=https://evil.example.com",
            data={"username": "redir", "password": "secret123", "role": "student"},
        )
        assert resp.status_code == 302
        assert "evil.example.com" not in resp.headers["Location"]
