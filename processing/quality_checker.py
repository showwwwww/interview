"""Quality checks on LLM output — flag suspicious responses and write reports."""

from __future__ import annotations

import os
from pathlib import Path

from readers.base import Section
from utils.logger import get_logger

logger = get_logger(__name__)

_MIN_OUTPUT_RATIO = 0.2
_TRUNCATION_MARKERS = ("...", "[truncated]", "[continued]", "[cut off]")

# Module-level accumulator so process_file can collect warnings per run.
_all_warnings: list[str] = []


def reset_warnings() -> None:
    """Clear accumulated warnings for a new run."""
    _all_warnings.clear()


def get_warnings() -> list[str]:
    """Return a copy of all accumulated warnings."""
    return list(_all_warnings)


def check_quality(
    original: Section,
    llm_output: str,
    conversion_type: str,
) -> list[str]:
    """Run quality checks and return a list of warning messages (empty if clean)."""
    warnings: list[str] = []
    label = f"[{conversion_type}] Section {original.number} '{original.title}'"

    if not llm_output.strip():
        msg = f"{label}: LLM returned empty output"
        logger.warning(msg)
        warnings.append(msg)
        _all_warnings.extend(warnings)
        return warnings

    input_len = len(original.content)
    output_len = len(llm_output)

    if input_len > 0 and output_len / input_len < _MIN_OUTPUT_RATIO:
        msg = (
            f"{label}: output is suspiciously short "
            f"({output_len} chars vs {input_len} input chars, "
            f"ratio {output_len / input_len:.2f})"
        )
        logger.warning(msg)
        warnings.append(msg)

    if original.title and original.title.lower() not in llm_output.lower():
        msg = f"{label}: section title '{original.title}' not found in LLM output"
        logger.warning(msg)
        warnings.append(msg)

    lowered = llm_output.rstrip().lower()
    for marker in _TRUNCATION_MARKERS:
        if lowered.endswith(marker):
            msg = f"{label}: output appears truncated (ends with '{marker}')"
            logger.warning(msg)
            warnings.append(msg)
            break

    _all_warnings.extend(warnings)
    return warnings


def check_section_counts(
    input_count: int,
    plain_count: int,
    summary_count: int,
    filename: str,
) -> list[str]:
    """Compare input vs output section counts and flag mismatches."""
    warnings: list[str] = []
    if plain_count != input_count:
        msg = (
            f"[{filename}] Section count mismatch — "
            f"input has {input_count} sections, plain English output has {plain_count}"
        )
        logger.warning(msg)
        warnings.append(msg)
    if summary_count != input_count:
        msg = (
            f"[{filename}] Section count mismatch — "
            f"input has {input_count} sections, summary output has {summary_count}"
        )
        logger.warning(msg)
        warnings.append(msg)
    _all_warnings.extend(warnings)
    return warnings


def write_quality_report(output_dir: str | Path) -> Path | None:
    """Write accumulated warnings to quality_report.txt. Returns the path, or None if clean."""
    warnings = get_warnings()
    if not warnings:
        logger.info("Quality report: no issues found")
        return None

    os.makedirs(output_dir, exist_ok=True)
    report_path = Path(output_dir) / "quality_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("Quality Report — Legal Document Converter\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total issues found: {len(warnings)}\n\n")
        for i, warning in enumerate(warnings, 1):
            f.write(f"{i}. {warning}\n")
        f.write("\n")

    logger.info("Quality report written: %s (%d issue(s))", report_path, len(warnings))
    return report_path
