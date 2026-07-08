from datetime import date, timedelta

from app.utils.validators import (
    validate_gpa, validate_amount, validate_deadline,
    validate_password, validate_username,
)


class TestValidateGpa:
    def test_empty_is_valid_none(self):
        assert validate_gpa("") == (True, None, "")

    def test_valid_gpa(self):
        ok, value, msg = validate_gpa("3.50")
        assert ok and value == 3.5 and msg == ""

    def test_non_numeric_rejected(self):
        ok, value, _ = validate_gpa("three")
        assert not ok and value is None

    def test_out_of_range_rejected(self):
        assert not validate_gpa("4.5")[0]
        assert not validate_gpa("-1")[0]

    def test_boundaries_accepted(self):
        assert validate_gpa("0.0")[0]
        assert validate_gpa("4.0")[0]


class TestValidateAmount:
    def test_empty_rejected(self):
        assert not validate_amount("")[0]

    def test_zero_and_negative_rejected(self):
        assert not validate_amount("0")[0]
        assert not validate_amount("-100")[0]

    def test_valid_amount(self):
        ok, value, _ = validate_amount("5000")
        assert ok and value == 5000.0


class TestValidateDeadline:
    def test_empty_is_valid_none(self):
        assert validate_deadline("") == (True, None, "")

    def test_past_date_rejected(self):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        assert not validate_deadline(yesterday)[0]

    def test_future_date_accepted(self):
        future = (date.today() + timedelta(days=30)).isoformat()
        ok, value, _ = validate_deadline(future)
        assert ok and value == date.today() + timedelta(days=30)

    def test_bad_format_rejected(self):
        assert not validate_deadline("30/12/2026")[0]


class TestValidateCredentials:
    def test_short_password_rejected(self):
        assert not validate_password("abc")[0]

    def test_mismatched_confirm_rejected(self):
        assert not validate_password("secret123", "secret124")[0]

    def test_matching_password_accepted(self):
        assert validate_password("secret123", "secret123")[0]

    def test_username_length_rules(self):
        assert not validate_username("ab")[0]
        assert not validate_username("x" * 65)[0]
        assert validate_username("devon_r")[0]
