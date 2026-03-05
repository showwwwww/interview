"""Tests for prompt_builder."""

from readers.base import Section
from processing.prompt_builder import build_plain_english_prompt, build_summary_prompt


class TestBuildPlainEnglishPrompt:
    def test_returns_system_and_user(self):
        section = Section(title="Obligations", number="2", content="The party shall...")
        system, user = build_plain_english_prompt(section)
        assert "plain english" in system.lower()
        assert "Section 2: Obligations" in user
        assert "The party shall..." in user

    def test_includes_section_number_in_prompt(self):
        section = Section(title="Termination", number="5", content="Upon termination...")
        _, user = build_plain_english_prompt(section)
        assert "Section 5" in user


class TestBuildSummaryPrompt:
    def test_returns_system_and_user(self):
        section = Section(title="Scope", number="1", content="The scope includes...")
        system, user = build_summary_prompt(section)
        assert "bullet" in system.lower()
        assert "Section 1: Scope" in user

    def test_includes_content(self):
        section = Section(title="Liability", number="3", content="Limited liability clause.")
        _, user = build_summary_prompt(section)
        assert "Limited liability clause." in user
