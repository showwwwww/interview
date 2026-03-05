"""Post-process LLM output: strip markdown artifacts, normalize whitespace."""

from __future__ import annotations

import re

from utils.logger import get_logger

logger = get_logger(__name__)


def clean_llm_output(text: str, expected_section_number: str = "") -> str:
    """Apply all cleaning steps to raw LLM output."""
    text = _strip_markdown(text)
    text = _normalize_whitespace(text)
    if expected_section_number:
        text = _fix_section_reference(text, expected_section_number)
    return text.strip()


def _strip_markdown(text: str) -> str:
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*---+\s*$", "", text, flags=re.MULTILINE)
    return text


def _normalize_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _fix_section_reference(text: str, expected: str) -> str:
    """Warn if the LLM changed the section reference."""
    pattern = re.compile(r"^Section\s+(\S+):", re.MULTILINE)
    match = pattern.search(text)
    if match and match.group(1) != expected:
        logger.warning(
            "Section reference mismatch: LLM wrote '%s', expected '%s'",
            match.group(1), expected,
        )
    return text
