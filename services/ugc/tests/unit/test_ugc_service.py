from datetime import datetime, timezone


from src.services.ugc import _parse_ts


class TestParseTs:
    def test_valid_iso_with_timezone(self):
        result = _parse_ts('2026-01-15T10:30:00+00:00')
        assert result == datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    def test_valid_iso_without_timezone(self):
        result = _parse_ts('2026-07-01T08:00:00')
        assert result.year == 2026
        assert result.month == 7
        assert result.day == 1

    def test_invalid_string_returns_now(self):
        before = datetime.now(timezone.utc)
        result = _parse_ts('not-a-date')
        after = datetime.now(timezone.utc)
        # Should fall back to current time, not raise
        assert before <= result.replace(tzinfo=timezone.utc) <= after

    def test_empty_string_returns_now(self):
        result = _parse_ts('')
        assert isinstance(result, datetime)

    def test_none_returns_now(self):
        result = _parse_ts(None)
        assert isinstance(result, datetime)
