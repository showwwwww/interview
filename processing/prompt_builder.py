"""Build LLM prompts for plain-English conversion and bullet-point summarization."""

from readers.base import Section

_PLAIN_ENGLISH_SYSTEM = (
    "You are a legal document translator. Convert the following legal text "
    "into plain English, word for word. Do not remove any content or context. "
    "Make it understandable to a non-legal reader. Preserve the original "
    "section structure and numbering."
)

_SUMMARY_SYSTEM = (
    "You are a legal document summarizer. Convert the following legal text "
    "into a concise bullet-point summary, preserving all legal context and "
    "meaning. Each bullet should capture a key point from the text. "
    "Preserve the original section structure and numbering."
)


def build_plain_english_prompt(section: Section) -> tuple[str, str]:
    user = f"Section {section.number}: {section.title}\n\n{section.content}"
    return _PLAIN_ENGLISH_SYSTEM, user


def build_summary_prompt(section: Section) -> tuple[str, str]:
    user = f"Section {section.number}: {section.title}\n\n{section.content}"
    return _SUMMARY_SYSTEM, user
