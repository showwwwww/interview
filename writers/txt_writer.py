"""Write sections to a plain-text file."""

from __future__ import annotations

from readers.base import Section
from utils.logger import get_logger

logger = get_logger(__name__)


def write_txt(sections: list[Section], output_path: str) -> None:
    lines: list[str] = []
    for section in sections:
        lines.append(f"{'=' * 60}")
        lines.append(f"Section {section.number}: {section.title}")
        lines.append(f"{'=' * 60}")
        lines.append("")
        lines.append(section.content)
        lines.append("")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info("TXT written: %s", output_path)
