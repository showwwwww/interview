from __future__ import annotations

import re
from pathlib import Path

from utils.logger import get_logger
from .base import BaseReader, Section

logger = get_logger(__name__)

_HEADING_PATTERN = re.compile(
    r"^(?:"
    r"(?:ARTICLE|SECTION|PART|CHAPTER)\s+[\dIVXLCDM]+"       # ARTICLE I, SECTION 2, etc.
    r"|(?:\d+\.(?:\d+\.?)*)\s+\S"                            # 1. Heading, 1.1 Heading
    r"|[A-Z][A-Z\s]{4,}$"                                    # ALL-CAPS lines (>=5 chars)
    r")",
    re.MULTILINE,
)


class TxtReader(BaseReader):
    def read(self, filepath: str) -> list[Section]:
        text = Path(filepath).read_text(encoding="utf-8")
        if not text.strip():
            logger.warning("Empty file: %s", filepath)
            return [Section(title=Path(filepath).stem, number="1", content="")]

        blocks = re.split(r"\n\s*\n", text)

        sections: list[Section] = []
        current_title = ""
        current_body: list[str] = []
        counter = 0

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            first_line = block.split("\n", 1)[0]
            if _HEADING_PATTERN.match(first_line):
                if current_body or current_title:
                    counter += 1
                    sections.append(Section(
                        title=current_title or f"Section {counter}",
                        number=str(counter),
                        content="\n".join(current_body).strip(),
                    ))
                current_title = first_line.strip()
                rest = block.split("\n", 1)
                current_body = [rest[1].strip()] if len(rest) > 1 and rest[1].strip() else []
            else:
                current_body.append(block)

        if current_body or current_title:
            counter += 1
            sections.append(Section(
                title=current_title or f"Section {counter}",
                number=str(counter),
                content="\n".join(current_body).strip(),
            ))

        if not sections:
            sections.append(Section(
                title=Path(filepath).stem,
                number="1",
                content=text.strip(),
            ))

        logger.info("TxtReader: extracted %d section(s) from %s", len(sections), filepath)
        return sections
