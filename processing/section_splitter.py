"""Split raw sections from readers into well-structured, token-bounded sections."""

from __future__ import annotations

import re

import tiktoken

from config import MAX_TOKENS, MODEL_NAME
from readers.base import Section
from utils.logger import get_logger

logger = get_logger(__name__)

_HEADING_RE = re.compile(
    r"^(?:"
    r"(?:ARTICLE|SECTION|PART|CHAPTER)\s+[\dIVXLCDM]+"
    r"|(?:\d+\.(?:\d+\.?)*)\s+\S"
    r"|[A-Z][A-Z\s]{4,}$"
    r")",
    re.MULTILINE,
)


def _get_encoder():
    try:
        return tiktoken.encoding_for_model(MODEL_NAME)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def _count_tokens(text: str) -> int:
    return len(_get_encoder().encode(text))


def _split_into_sub_sections(section: Section) -> list[Section]:
    """Split a section that exceeds MAX_TOKENS at paragraph or sentence boundaries."""
    paragraphs = re.split(r"\n\s*\n", section.content)
    chunks: list[str] = []
    current_chunk: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = _count_tokens(para)
        if current_tokens + para_tokens > MAX_TOKENS and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = []
            current_tokens = 0

        if para_tokens > MAX_TOKENS:
            # paragraph itself is too large — split at sentence boundaries
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sentence in sentences:
                s_tokens = _count_tokens(sentence)
                if current_tokens + s_tokens > MAX_TOKENS and current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_tokens = 0
                current_chunk.append(sentence)
                current_tokens += s_tokens
        else:
            current_chunk.append(para)
            current_tokens += para_tokens

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    if len(chunks) <= 1:
        return [section]

    total = len(chunks)
    return [
        Section(
            title=f"{section.title} (Part {i} of {total})",
            number=section.number,
            content=chunk,
        )
        for i, chunk in enumerate(chunks, 1)
    ]


def _detect_sub_sections(text: str) -> list[tuple[str, str]]:
    """Detect heading-like lines and split text into (heading, body) pairs."""
    lines = text.split("\n")
    segments: list[tuple[str, str]] = []
    current_heading = ""
    body_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped and _HEADING_RE.match(stripped):
            if body_lines or current_heading:
                segments.append((current_heading, "\n".join(body_lines).strip()))
            current_heading = stripped
            body_lines = []
        else:
            body_lines.append(line)

    if body_lines or current_heading:
        segments.append((current_heading, "\n".join(body_lines).strip()))

    return segments


def split_sections(raw_sections: list[Section]) -> list[Section]:
    """
    Take raw sections from a reader, refine them with heading detection,
    and enforce token limits.
    """
    refined: list[Section] = []
    counter = 0

    for section in raw_sections:
        sub_headings = _detect_sub_sections(section.content)

        if len(sub_headings) > 1:
            for heading, body in sub_headings:
                if not body.strip():
                    continue
                counter += 1
                refined.append(Section(
                    title=heading or f"Section {counter}",
                    number=str(counter),
                    content=body,
                ))
        else:
            counter += 1
            refined.append(Section(
                title=section.title,
                number=str(counter),
                content=section.content,
            ))

    token_bounded: list[Section] = []
    for section in refined:
        if _count_tokens(section.content) > MAX_TOKENS:
            logger.info(
                "Section '%s' exceeds %d tokens — splitting into sub-chunks",
                section.title, MAX_TOKENS,
            )
            token_bounded.extend(_split_into_sub_sections(section))
        else:
            token_bounded.append(section)

    if not token_bounded:
        token_bounded.append(Section(title="Section 1", number="1", content=""))

    logger.info("Section splitter produced %d section(s)", len(token_bounded))
    return token_bounded
