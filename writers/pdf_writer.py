"""Write sections to a formatted PDF file."""

from __future__ import annotations

from fpdf import FPDF

from readers.base import Section
from utils.logger import get_logger

logger = get_logger(__name__)

_FONT_FAMILY = "Helvetica"
_HEADING_SIZE = 14
_BODY_SIZE = 11
_LINE_HEIGHT = 6
_PAGE_MARGIN = 20


class _LegalPDF(FPDF):
    """Thin FPDF subclass with header/footer defaults."""

    def header(self):
        self.set_font(_FONT_FAMILY, "B", 9)
        self.set_text_color(140, 140, 140)
        self.cell(0, 8, "Legal Document Converter", align="R", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font(_FONT_FAMILY, "", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


def write_pdf(sections: list[Section], output_path: str) -> None:
    pdf = _LegalPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=_PAGE_MARGIN)
    pdf.add_page()

    for section in sections:
        _write_heading(pdf, f"Section {section.number}: {section.title}")
        _write_body(pdf, section.content)
        pdf.ln(_LINE_HEIGHT)

    pdf.output(output_path)
    logger.info("PDF written: %s", output_path)


def _write_heading(pdf: FPDF, text: str) -> None:
    pdf.set_font(_FONT_FAMILY, "B", _HEADING_SIZE)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, _LINE_HEIGHT + 2, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)


def _write_body(pdf: FPDF, text: str) -> None:
    pdf.set_font(_FONT_FAMILY, "", _BODY_SIZE)
    pdf.set_text_color(50, 50, 50)

    if _looks_like_bullets(text):
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            clean = line.lstrip("-•*").strip()
            pdf.cell(6)
            pdf.multi_cell(0, _LINE_HEIGHT, f"-  {clean}", new_x="LMARGIN", new_y="NEXT")
    else:
        for paragraph in text.split("\n\n"):
            paragraph = paragraph.strip()
            if paragraph:
                pdf.multi_cell(0, _LINE_HEIGHT, paragraph, new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)


def _looks_like_bullets(text: str) -> bool:
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    if not lines:
        return False
    bullet_count = sum(1 for line in lines if line.startswith(("-", "•", "*")))
    return bullet_count / len(lines) > 0.5
