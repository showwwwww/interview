#!/usr/bin/env python3
"""Legal Document Converter — CLI entry point.

Converts legal documents into plain English and bullet-point summaries
using an LLM.
"""

import argparse
import os
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from config import OUTPUT_DIR, validate_config
from processing.llm_client import LLMClient
from processing.post_processor import clean_llm_output
from processing.prompt_builder import build_plain_english_prompt, build_summary_prompt
from processing.quality_checker import (
    check_quality,
    check_section_counts,
    reset_warnings,
    write_quality_report,
)
from processing.section_splitter import split_sections
from readers import get_reader
from readers.base import Section
from utils.logger import get_logger
from writers.docx_writer import write_docx
from writers.pdf_writer import write_pdf
from writers.txt_writer import write_txt

logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
_DEFAULT_PARALLEL_WORKERS = 4


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Convert legal documents into plain English and bullet-point summaries.",
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to an input folder or a single file.",
    )
    parser.add_argument(
        "--output", "-o",
        default=str(OUTPUT_DIR),
        help="Path to the output folder (default: ./output).",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["txt", "docx", "pdf", "both", "all"],
        default="docx",
        help="Output format: txt, docx, pdf, both (txt+docx), or all (default: docx).",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        default=False,
        help=f"Enable parallel file processing (uses {_DEFAULT_PARALLEL_WORKERS} workers by default).",
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=None,
        help=f"Number of parallel workers (default: {_DEFAULT_PARALLEL_WORKERS}). Implies --parallel.",
    )
    return parser.parse_args(argv)


def discover_files(input_path: str) -> list[Path]:
    p = Path(input_path)
    if p.is_file():
        if p.suffix.lower() in SUPPORTED_EXTENSIONS:
            return [p]
        raise ValueError(f"Unsupported file type: {p.suffix}")
    if p.is_dir():
        files = sorted(
            f for f in p.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        )
        if not files:
            raise FileNotFoundError(f"No supported files found in {p}")
        return files
    raise FileNotFoundError(f"Input path does not exist: {p}")


def _output_path(output_dir: Path, input_file: Path, suffix: str, ext: str) -> Path:
    """Build an output file path, handling filename collisions."""
    stem = input_file.stem
    candidate = output_dir / f"{stem}_{suffix}.{ext}"
    counter = 1
    while candidate.exists():
        counter += 1
        candidate = output_dir / f"{stem}_{suffix}_{counter}.{ext}"
    return candidate


def process_file(
    filepath: Path,
    output_dir: Path,
    output_format: str,
    client: LLMClient,
) -> None:
    logger.info("Reading: %s", filepath)
    reader = get_reader(str(filepath))
    raw_sections = reader.read(str(filepath))
    logger.info("Extracted %d raw section(s)", len(raw_sections))

    sections = split_sections(raw_sections)
    logger.info("Split into %d section(s) within token limits", len(sections))

    plain_sections = []
    summary_sections = []

    for idx, section in enumerate(sections, 1):
        logger.info(
            "Processing section %d/%d: '%s'",
            idx, len(sections), section.title,
        )

        sys_pe, usr_pe = build_plain_english_prompt(section)
        pe_text = clean_llm_output(client.convert(sys_pe, usr_pe), section.number)
        check_quality(section, pe_text, "plain_english")

        sys_sm, usr_sm = build_summary_prompt(section)
        sm_text = clean_llm_output(client.convert(sys_sm, usr_sm), section.number)
        check_quality(section, sm_text, "summary")

        plain_sections.append(Section(
            title=section.title,
            number=section.number,
            content=pe_text,
        ))
        summary_sections.append(Section(
            title=section.title,
            number=section.number,
            content=sm_text,
        ))

    check_section_counts(
        len(sections), len(plain_sections), len(summary_sections), filepath.name,
    )

    os.makedirs(output_dir, exist_ok=True)

    def _write(sections, suffix, fmt):
        if fmt in ("docx", "both", "all"):
            p = _output_path(output_dir, filepath, suffix, "docx")
            write_docx(sections, str(p))
            logger.info("Written: %s", p)
        if fmt in ("txt", "both", "all"):
            p = _output_path(output_dir, filepath, suffix, "txt")
            write_txt(sections, str(p))
            logger.info("Written: %s", p)
        if fmt in ("pdf", "all"):
            p = _output_path(output_dir, filepath, suffix, "pdf")
            write_pdf(sections, str(p))
            logger.info("Written: %s", p)

    _write(plain_sections, "plainEnglish", output_format)
    _write(summary_sections, "summary", output_format)


def main(argv=None):
    args = parse_args(argv)
    validate_config()

    files = discover_files(args.input)
    output_dir = Path(args.output)
    total = len(files)
    succeeded = 0
    failed = 0
    start = time.time()

    client = LLMClient()
    reset_warnings()

    use_parallel = args.parallel or args.workers is not None
    workers = args.workers if args.workers is not None else _DEFAULT_PARALLEL_WORKERS
    workers = max(1, workers)

    if not use_parallel or workers == 1:
        for file_idx, filepath in enumerate(files, 1):
            logger.info("[%d/%d] Processing: %s", file_idx, total, filepath.name)
            try:
                process_file(filepath, output_dir, args.format, client)
                succeeded += 1
            except RuntimeError as exc:
                msg = str(exc)
                if "Invalid OpenAI API key" in msg or "quota exceeded" in msg:
                    logger.error(msg)
                    failed += total - file_idx + 1
                    break
                failed += 1
                logger.error(
                    "Failed to process %s:\n%s",
                    filepath.name, traceback.format_exc(),
                )
            except Exception:
                failed += 1
                logger.error(
                    "Failed to process %s:\n%s",
                    filepath.name, traceback.format_exc(),
                )
    else:
        logger.info("Parallel mode: processing %d files with %d workers", total, workers)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            future_to_file = {
                pool.submit(process_file, fp, output_dir, args.format, client): fp
                for fp in files
            }
            for future in as_completed(future_to_file):
                fp = future_to_file[future]
                try:
                    future.result()
                    succeeded += 1
                    logger.info("Completed: %s", fp.name)
                except Exception:
                    failed += 1
                    logger.error(
                        "Failed to process %s:\n%s",
                        fp.name, traceback.format_exc(),
                    )

    write_quality_report(output_dir)

    elapsed = time.time() - start
    logger.info(
        "Done. %d/%d files succeeded, %d failed (%.1fs elapsed). See converter.log for details.",
        succeeded, total, failed, elapsed,
    )
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
