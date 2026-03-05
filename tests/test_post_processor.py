"""Tests for post_processor."""

from processing.post_processor import clean_llm_output, _strip_markdown, _normalize_whitespace


class TestStripMarkdown:
    def test_removes_bold(self):
        assert _strip_markdown("This is **bold** text") == "This is bold text"

    def test_removes_italic(self):
        assert _strip_markdown("This is *italic* text") == "This is italic text"

    def test_removes_headings(self):
        result = _strip_markdown("### Heading\nBody text")
        assert "###" not in result
        assert "Body text" in result

    def test_removes_code_fences(self):
        text = "Before\n```python\ncode\n```\nAfter"
        result = _strip_markdown(text)
        assert "```" not in result
        assert "Before" in result
        assert "After" in result

    def test_removes_inline_code(self):
        assert _strip_markdown("Use `variable` here") == "Use variable here"

    def test_removes_horizontal_rules(self):
        result = _strip_markdown("Above\n---\nBelow")
        assert "---" not in result

    def test_removes_underline_bold(self):
        assert _strip_markdown("This is __bold__ text") == "This is bold text"


class TestNormalizeWhitespace:
    def test_collapses_multiple_blank_lines(self):
        text = "Line 1\n\n\n\n\nLine 2"
        result = _normalize_whitespace(text)
        assert result == "Line 1\n\nLine 2"

    def test_strips_trailing_spaces(self):
        text = "Line with trailing spaces   \nNext line"
        result = _normalize_whitespace(text)
        assert "   \n" not in result


class TestCleanLlmOutput:
    def test_full_pipeline(self):
        raw = "### Section 1: Overview\n\nThis is **important** text.\n\n\n\nEnd."
        result = clean_llm_output(raw, "1")
        assert "**" not in result
        assert "###" not in result
        assert "\n\n\n" not in result
        assert "important" in result

    def test_empty_input(self):
        assert clean_llm_output("", "1") == ""
