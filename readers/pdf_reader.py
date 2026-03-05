from __future__ import annotations

import re
from pathlib import Path

from utils.logger import get_logger
from .base import BaseReader, Section

logger = get_logger(__name__)

_HEADING_PATTERN = re.compile(
    r"^(?:"
    r"(?:ARTICLE|SECTION|PART|CHAPTER)\s+[\dIVXLCDM]+"
    r"|(?:\d+\.(?:\d+\.?)*)\s+\S"
    r"|[A-Z][A-Z\s]{4,}$"
    r")",
    re.MULTILINE,
)


class PdfReader(BaseReader):
    def read(self, filepath: str) -> list[Section]:
        text = self._extract_with_pdfplumber(filepath)
        if text is None:
            logger.warning("pdfplumber failed for %s, falling back to PyPDF2", filepath)
            text = self._extract_with_pypdf2(filepath)

        if not text.strip():
            logger.warning("No text extracted from %s", filepath)
            return [Section(title=Path(filepath).stem, number="1", content="")]

        sections = self._detect_sections(text, filepath)
        logger.info("PdfReader: extracted %d section(s) from %s", len(sections), filepath)
        return sections

    @staticmethod
    def _detect_sections(text: str, filepath: str) -> list[Section]:
        """Split extracted text into sections based on heading patterns."""
        lines = text.split("\n")
        segments: list[tuple[str, list[str]]] = []
        current_heading = ""
        body_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            if stripped and _HEADING_PATTERN.match(stripped):
                if body_lines or current_heading:
                    segments.append((current_heading, body_lines))
                current_heading = stripped
                body_lines = []
            else:
                body_lines.append(line)

        if body_lines or current_heading:
            segments.append((current_heading, body_lines))

        if len(segments) <= 1:
            return [Section(
                title=Path(filepath).stem,
                number="1",
                content=text,
            )]

        sections: list[Section] = []
        for idx, (heading, body) in enumerate(segments, 1):
            content = "\n".join(body).strip()
            if not content and not heading:
                continue
            sections.append(Section(
                title=heading or f"Section {idx}",
                number=str(idx),
                content=content,
            ))

        return sections or [Section(title=Path(filepath).stem, number="1", content=text)]

    @staticmethod
    def _extract_with_pdfplumber(filepath: str) -> str | None:
        try:
            import pdfplumber

            pages_text: list[str] = []
            with pdfplumber.open(filepath) as pdf:
                for i, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        pages_text.append(page_text)
                    else:
                        logger.warning("Page %d of %s yielded no text", i, filepath)
            return "\n\n".join(pages_text) if pages_text else None
        except Exception as exc:
            logger.debug("pdfplumber error: %s", exc)
            return None

    @staticmethod
    def _extract_with_pypdf2(filepath: str) -> str:
        from PyPDF2 import PdfReader as PyPDF2Reader

        reader = PyPDF2Reader(filepath)
        pages_text: list[str] = []
        for i, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                pages_text.append(page_text)
            else:
                logger.warning("PyPDF2: page %d of %s yielded no text", i, filepath)
        return "\n\n".join(pages_text)
