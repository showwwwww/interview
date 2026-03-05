"""Tests for quality_checker."""

from readers.base import Section
from processing.quality_checker import (
    check_quality,
    check_section_counts,
    get_warnings,
    reset_warnings,
    write_quality_report,
)


class TestCheckQuality:
    def _section(self, content="A" * 200):
        return Section(title="Test", number="1", content=content)

    def setup_method(self):
        reset_warnings()

    def test_empty_output_warns(self):
        warnings = check_quality(self._section(), "", "plain_english")
        assert len(warnings) == 1
        assert "empty" in warnings[0].lower()

    def test_short_output_warns(self):
        warnings = check_quality(self._section(), "tiny", "plain_english")
        assert any("short" in w.lower() for w in warnings)

    def test_truncated_output_warns(self):
        warnings = check_quality(self._section(), "Some text that ends with...", "summary")
        assert any("truncated" in w.lower() for w in warnings)

    def test_good_output_no_warnings(self):
        long_output = "Test " + "This is a reasonably long converted text. " * 10
        warnings = check_quality(self._section(), long_output, "plain_english")
        assert warnings == []

    def test_whitespace_only_is_empty(self):
        warnings = check_quality(self._section(), "   \n\n  ", "summary")
        assert any("empty" in w.lower() for w in warnings)

    def test_missing_title_warns(self):
        section = Section(title="Liability Clause", number="3", content="Some legal text here.")
        warnings = check_quality(section, "output without the title", "plain_english")
        assert any("title" in w.lower() for w in warnings)

    def test_title_present_no_warning(self):
        section = Section(title="Liability", number="3", content="Some text.")
        output = "This Liability section explains something. " * 5
        warnings = check_quality(section, output, "plain_english")
        title_warnings = [w for w in warnings if "title" in w.lower()]
        assert title_warnings == []

    def test_20_percent_threshold(self):
        section = self._section("A" * 100)
        output_19 = "B" * 19
        output_21 = "B" * 21
        reset_warnings()
        w1 = check_quality(section, output_19, "plain_english")
        assert any("short" in w.lower() for w in w1)
        reset_warnings()
        w2 = check_quality(section, output_21, "plain_english")
        short_warnings = [w for w in w2 if "short" in w.lower()]
        assert short_warnings == []


class TestCheckSectionCounts:
    def setup_method(self):
        reset_warnings()

    def test_matching_counts_no_warnings(self):
        warnings = check_section_counts(5, 5, 5, "test.pdf")
        assert warnings == []

    def test_mismatched_plain_warns(self):
        warnings = check_section_counts(5, 3, 5, "test.pdf")
        assert len(warnings) == 1
        assert "plain" in warnings[0].lower()

    def test_mismatched_summary_warns(self):
        warnings = check_section_counts(5, 5, 3, "test.pdf")
        assert len(warnings) == 1
        assert "summary" in warnings[0].lower()


class TestWarningAccumulation:
    def setup_method(self):
        reset_warnings()

    def test_accumulates_across_calls(self):
        section = Section(title="Test", number="1", content="A" * 200)
        check_quality(section, "", "plain_english")
        check_quality(section, "", "summary")
        assert len(get_warnings()) == 2

    def test_reset_clears(self):
        section = Section(title="Test", number="1", content="A" * 200)
        check_quality(section, "", "plain_english")
        reset_warnings()
        assert get_warnings() == []


class TestWriteQualityReport:
    def setup_method(self):
        reset_warnings()

    def test_no_warnings_returns_none(self, tmp_path):
        result = write_quality_report(tmp_path)
        assert result is None

    def test_writes_report_file(self, tmp_path):
        section = Section(title="Test", number="1", content="A" * 200)
        check_quality(section, "", "plain_english")
        path = write_quality_report(tmp_path)
        assert path is not None
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "Quality Report" in text
        assert "1." in text
