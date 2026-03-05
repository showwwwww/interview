"""Tests for section_splitter."""

from readers.base import Section
from processing.section_splitter import split_sections, _detect_sub_sections


class TestDetectSubSections:
    def test_finds_article_headings(self):
        text = "ARTICLE I\nFirst article body.\nARTICLE II\nSecond article body."
        result = _detect_sub_sections(text)
        assert len(result) == 2
        assert result[0][0] == "ARTICLE I"
        assert result[1][0] == "ARTICLE II"

    def test_no_headings_returns_single_segment(self):
        text = "This is plain text without any headings at all."
        result = _detect_sub_sections(text)
        assert len(result) == 1

    def test_numbered_headings(self):
        text = "1. Introduction\nSome content.\n2. Background\nMore content."
        result = _detect_sub_sections(text)
        assert len(result) == 2


class TestSplitSections:
    def test_preserves_small_sections(self):
        sections = [
            Section(title="Test", number="1", content="Short content."),
        ]
        result = split_sections(sections)
        assert len(result) >= 1
        assert result[0].content == "Short content."

    def test_empty_input_produces_fallback(self):
        result = split_sections([])
        assert len(result) == 1
        assert result[0].title == "Section 1"

    def test_refines_sub_headings(self):
        raw = [Section(
            title="Full Doc",
            number="1",
            content="ARTICLE I\nFirst.\nARTICLE II\nSecond.",
        )]
        result = split_sections(raw)
        assert len(result) >= 2
